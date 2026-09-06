# syntax=docker/dockerfile:1.6
#
# SafePost AI — FastAPI image.
# Bakes the trained DistilBERT model (M3) into the image so the
# container is self-contained and doesn't need a model mount at
# runtime. Use `docker/api/Dockerfile` from the repo root:
#
#   docker build -f docker/api/Dockerfile -t safepost-ai-api:latest .
#
# The .dockerignore at the docker/ level keeps most of `models/`
# out of the build context; only `models/m3-transformer/final/` is
# re-included (via the !models/m3-transformer/final/ pattern).

FROM python:3.11-slim-bookworm

# Install uv. The slim base doesn't ship it; this is the standard
# pattern from https://docs.astral.sh/uv/guides/integration/docker/.
ENV PATH="/root/.local/bin:${PATH}"
RUN pip install --no-cache-dir uv

WORKDIR /app

# Layer 1 — Python deps. Cached as long as pyproject.toml + uv.lock
# don't change, so source-only edits don't re-run uv sync.
# README.md is required by hatchling (pyproject.toml -> readme).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Layer 2 — Application source.
COPY app ./app

# Layer 3 — Trained model + tokenizer. ~260 MB on disk; baked in so
# the API has no runtime model dependency. See docker/.dockerignore
# for the include/exclude pattern.
COPY models ./models

# Non-root user. Created after the heavy layers so the useradd layer
# stays small in the case of source-only changes.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# .venv/bin must be on PATH so the CMD resolves `uvicorn`. Set the
# usual Python hygiene envs too.
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# `python -c` healthcheck so we don't have to install curl in the
# slim image. start-period gives the model load ~30 s on first boot.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3).read()" \
    || exit 1

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
