"""Hate-speech inference service backed by the BiLSTM model.

Wraps :func:`app.inference.predict` with a thin ``ModelBundle`` that
holds the artifact directory + the resolved ``model_version`` string for
the ``/version`` endpoint. The actual model + tokenizer + NLTK corpora
are loaded lazily by ``app.inference.predict`` (and cached there via
``functools.lru_cache``), so this layer is essentially metadata.

Why BiLSTM and not the Transformer (M3)? The Transformer fine-tune hit
higher validation accuracy, but the BiLSTM is what we ship:

- Smaller image (~350K params vs ~66M) → faster ECR push, faster ECS
  task startup, cheaper Fargate compute (CPU-only, no GPU driver).
- Lower inference latency on CPU (~10–50 ms vs ~200–800 ms).
- Smaller operational surface (no TensorRT, no GPU AMI).

Label / action mapping (per the PRD MVP contract):
- ``0`` → ``hate_speech``       → ``block``
- ``1`` → ``offensive_language`` → ``flag``
- ``2`` → ``neutral``            → ``allow``
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.inference import DEFAULT_ARTIFACT_DIR, predict as _infer_predict

# Default artifact dir mirrors `app.inference.DEFAULT_ARTIFACT_DIR` so the
# FastAPI side and the SageMaker side stay aligned. Override with
# SAFEPOST_MODEL_DIR (read inside app.inference) or by passing
# `model_dir=` to ModelBundle.
DEFAULT_MODEL_DIR: Path = DEFAULT_ARTIFACT_DIR


class ModelBundle:
    """Wraps `app.inference.predict` with a model_version string for /version."""

    def __init__(self, model_dir: Path = DEFAULT_MODEL_DIR) -> None:
        self.model_dir = Path(model_dir)
        # Probe the artifact dir to resolve the version string at startup.
        # _load_artifacts is private to app.inference but cheap to call
        # once; its lru_cache keeps subsequent calls (predict, etc.)
        # from re-loading the model.
        from app.inference import _load_artifacts

        _, _, meta = _load_artifacts(str(self.model_dir))
        self.model_version = meta.get("model_version", "unknown")

    def predict(self, text: str) -> dict:
        """Run inference and return the PRD-shaped response."""
        return _infer_predict(text, artifact_dir=str(self.model_dir))


@lru_cache
def get_model() -> ModelBundle:
    """Return the cached ModelBundle (constructed on first call).

    The underlying Keras model + tokenizer + NLTK data are loaded by
    ``app.inference._load_artifacts`` on the first ``predict`` call;
    subsequent calls hit the same lru_cache and skip the load.
    """
    return ModelBundle()
