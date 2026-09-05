"""Hate-speech inference service.

Loads the DistilBERT model + tokenizer produced by M3 from
``models/m3-transformer/final/`` and exposes a single ``predict``
function that takes a raw tweet string and returns the moderation
decision.

The bundle is loaded once via ``get_model()`` and cached for the
process lifetime. Callers should fetch the bundle inside a FastAPI
``lifespan`` handler so the model is ready before the first request
and isn't re-loaded per call.

Label / action mapping
----------------------

The M3 fine-tune emits three labels (per the dataset's ``class``
column):

- ``0`` -> ``hate_speech``     -> ``block``
- ``1`` -> ``offensive_language`` -> ``flag``
- ``2`` -> ``neutral``         -> ``allow``
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_MODEL_DIR: Path = Path("models/m3-transformer/final")
LABEL_NAMES: list[str] = ["hate_speech", "offensive_language", "neutral"]
ACTION_MAP: dict[str, str] = {
    "hate_speech": "block",
    "offensive_language": "flag",
    "neutral": "allow",
}
MAX_LENGTH: int = 128


class ModelBundle:
    """Loaded tokenizer + model + metadata for inference."""

    def __init__(self, model_dir: Path = DEFAULT_MODEL_DIR) -> None:
        self.model_dir = model_dir
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        # Friendly version = parent directory name (e.g. "m3-transformer").
        self.model_version = model_dir.parent.name

    def predict(self, text: str) -> dict:
        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=MAX_LENGTH,
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with torch.no_grad():
            logits = self.model(**encoded).logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()
        pred_id = int(np.argmax(probs))
        label = LABEL_NAMES[pred_id]
        return {
            "label": label,
            "confidence": float(probs[pred_id]),
            "action": ACTION_MAP[label],
            "model_version": self.model_version,
        }


@lru_cache
def get_model() -> ModelBundle:
    """Return the cached model bundle (loads on first call)."""
    return ModelBundle()
