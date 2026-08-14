# SafePost AI

Production-oriented social-media text moderation platform.

SafePost AI classifies text into:

- `HATE_SPEECH`
- `OFFENSIVE_LANGUAGE`
- `NEUTRAL`

The project is intentionally structured as an end-to-end learning journey:

**ML → API → SageMaker → Streamlit → Docker → AWS → CI/CD → Terraform → MLOps**

## Project Status

**Current milestone:** M1 — Product & Dataset

See [`docs/roadmap.md`](docs/roadmap.md) for the current milestone and progress.

## Repository Structure

```text
app/                 Application code
ml/                  Data, training, evaluation and inference
tests/               Unit/API/integration tests
configs/              Configuration
notebooks/            Exploration notebooks
data/                 Dataset artifacts (not committed)
models/               Local model artifacts (not committed)
docker/               Container definitions
infrastructure/      Terraform / AWS infrastructure
scripts/              Utility scripts
docs/                 PRD, architecture, decisions, experiments
.github/              CI/CD and GitHub templates
```

## Quick Start

This project uses [uv](https://docs.astral.sh/uv/) as the Python package and project manager.

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
# or on Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create the virtualenv and install all dependencies (runtime + dev)
uv sync --all-extras

# Run the test suite
uv run pytest

# Run the API locally
uv run uvicorn app.api.main:app --reload

# Run the Streamlit console
uv run streamlit run app/streamlit/app.py
```

The Python version is pinned in `.python-version` (currently `3.11`). `uv` will
automatically download and use the correct interpreter — no manual `python -m venv`
or `pip install` calls required.

The initial implementation will be added milestone by milestone. Empty directories contain `.gitkeep` files so the repository structure is preserved.

## Source of Truth

- Product requirements: [`docs/PRD.md`](docs/PRD.md)
- Progress / milestones: [`docs/roadmap.md`](docs/roadmap.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Decisions: [`docs/decisions/`](docs/decisions/)
- Experiments: [`docs/experiments/`](docs/experiments/)

## GitHub Project

Use a GitHub Project to track:

- Milestones
- Features
- Tasks
- Bugs
- Technical debt
- Experiments

Keep implementation details in the repository and execution status in GitHub Project.
