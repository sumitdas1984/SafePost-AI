# syntax=docker/dockerfile:1.6
#
# SafePost AI — Streamlit UI image.
# No model is baked in; the UI is a thin client that POSTs to the
# FastAPI service. Build from the repo root:
#
#   docker build -f docker/streamlit/Dockerfile -t safepost-ai-streamlit:latest .
#
# The `API_URL` env var should be set in docker-compose.yml or the
# ECS task definition so the UI talks to the right backend.

FROM python:3.11-slim-bookworm

ENV PATH="/root/.local/bin:${PATH}"
RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY app ./app

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_URL="http://localhost:8000"

EXPOSE 8501

# Streamlit exposes /_stcore/health out of the box; that's the
# documented health endpoint for Streamlit apps in containers.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3).read()" \
    || exit 1

CMD ["streamlit", "run", "app/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
