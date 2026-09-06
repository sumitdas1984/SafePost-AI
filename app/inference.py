"""Inference entry point for the SafePost BiLSTM model.

Loads the trained Keras model + tokenizer + metadata from disk, applies
the same preprocessing used during training, and returns a label +
confidence + recommended action for any input text.

Used by:
  - FastAPI route handler (``app/api/main.py`` calls ``predict(...)``)
  - SageMaker inference container (the container's ``/opt/ml/code/``
    ships a thin wrapper that imports this module)

Run as a script for a quick sanity check::

    uv run python -m app.inference --text "some social media post"
    uv run python -m app.inference --text "..." --artifact-dir /opt/ml/model
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import string
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import tensorflow as tf  # noqa: E402  — used lazily below; module-level so predict() can see it

logger = logging.getLogger(__name__)

# Default artifact location. SageMaker containers place the model at
# /opt/ml/model; FastAPI runs from the repo root with models/bilstm/.
DEFAULT_ARTIFACT_DIR = Path(os.environ.get("SAFEPOST_MODEL_DIR", "models/bilstm"))

# Action mapping per the PRD MVP contract. Module-of-truth is here so the
# meta.json sidecar doesn't have to change when product policy does.
ACTION_MAP: dict[str, str] = {
    "hate_speech": "block",
    "offensive_language": "flag",
    "neither": "allow",
}


@lru_cache(maxsize=1)
def _load_artifacts(artifact_dir_str: str) -> tuple:
    """Lazy-load the model, tokenizer, and metadata. Cached after first call.

    Returns ``(model, tokenizer, meta)``. ``artifact_dir_str`` is a string
    (not a Path) because ``lru_cache`` requires hashable args.
    """
    # Lazy imports: TF and the rest of the model stack only need to be
    # importable when inference actually happens, not at app startup.
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing.text import tokenizer_from_json

    artifact_dir = Path(artifact_dir_str)
    model_path = artifact_dir / "bilstm.keras"
    tokenizer_path = artifact_dir / "tokenizer.json"
    meta_path = artifact_dir / "meta.json"

    for p in (model_path, tokenizer_path, meta_path):
        if not p.exists():
            raise FileNotFoundError(
                f"Required artifact missing: {p}. "
                "Run notebooks/01_experiment_bilstm.ipynb Step 9 to generate."
            )

    logger.info("Loading BiLSTM model from %s", model_path)
    model = load_model(model_path)

    logger.info("Loading tokenizer from %s", tokenizer_path)
    with tokenizer_path.open(encoding="utf-8") as f:
        tokenizer = tokenizer_from_json(f.read())

    with meta_path.open(encoding="utf-8") as f:
        meta = json.load(f)

    logger.info(
        "Model loaded: version=%s, max_len=%d, labels=%s",
        meta.get("model_version"),
        meta.get("max_len"),
        meta.get("label_names"),
    )
    return model, tokenizer, meta


@lru_cache(maxsize=1)
def _get_nltk():
    """Lazy-import NLTK + ensure the corpora used by preprocessing are present.

    Downloads on first call (dev convenience). Production images should
    bake the corpora into the Docker layer instead — see Dockerfile.
    """
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    for resource in ("stopwords", "omw-1.4", "wordnet"):
        try:
            nltk.data.find(f"corpora/{resource}")
        except LookupError:
            logger.info("Downloading NLTK resource: %s", resource)
            nltk.download(resource, quiet=True)

    return set(stopwords.words("english")), WordNetLemmatizer()


def _preprocess(text: str, stop_words: set, lemmatizer) -> str:
    """Lowercase, strip punctuation, drop stopwords, lemmatize.

    Mirrors the preprocessing applied during training in
    ``notebooks/01_experiment_bilstm.ipynb`` (cells 11 + 12).
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = [lemmatizer.lemmatize(w) for w in text.split() if w not in stop_words]
    return " ".join(words)


def predict(text: str, artifact_dir: str | os.PathLike | None = None) -> dict:
    """Classify a single piece of text. Returns the PRD-shaped response.

    Output::

        {
            "label": "hate_speech",
            "confidence": 0.94,
            "action": "block",
            "model_version": "bilstm-v1",
        }

    ``artifact_dir`` defaults to ``$SAFEPOST_MODEL_DIR`` or
    ``models/bilstm/``. Pass an explicit path to override (useful for
    tests and for SageMaker's ``/opt/ml/model``).
    """
    if artifact_dir is None:
        artifact_dir = DEFAULT_ARTIFACT_DIR
    model, tokenizer, meta = _load_artifacts(str(artifact_dir))
    stop_words, lemmatizer = _get_nltk()

    clean_text = _preprocess(text, stop_words, lemmatizer)
    if not clean_text.strip():
        # Empty after preprocessing (e.g. all-stopwords input). Return
        # the safest default rather than crashing.
        label_name = "neither"
        return {
            "label": label_name,
            "confidence": 0.0,
            "action": ACTION_MAP[label_name],
            "model_version": meta.get("model_version", "unknown"),
        }

    max_len = int(meta["max_len"])
    seq = tokenizer.texts_to_sequences([clean_text])
    if not seq or not seq[0]:
        # No token in the trained vocab maps to this text. Treat as
        # "neither" with low confidence rather than crashing.
        label_name = "neither"
        return {
            "label": label_name,
            "confidence": 0.0,
            "action": ACTION_MAP[label_name],
            "model_version": meta.get("model_version", "unknown"),
        }

    # pad_sequences lives in tf.keras.utils in TF 2.x.
    padded = tf.keras.utils.pad_sequences(
        seq, maxlen=max_len, padding="post", truncating="post",
    )

    probs = model.predict(padded, verbose=0)[0]
    label_id = int(np.argmax(probs))
    label_name = meta["label_names"][label_id]
    confidence = float(probs[label_id])

    return {
        "label": label_name,
        "confidence": round(confidence, 4),
        "action": ACTION_MAP.get(label_name, "review"),
        "model_version": meta.get("model_version", "unknown"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Text to classify")
    parser.add_argument(
        "--artifact-dir",
        default=str(DEFAULT_ARTIFACT_DIR),
        help="Path to the directory containing bilstm.keras / tokenizer.json / meta.json",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = predict(args.text, artifact_dir=args.artifact_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
