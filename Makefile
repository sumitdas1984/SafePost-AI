.PHONY: help install sync test lint format api streamlit clean

help:
	@echo "SafePost AI — available targets:"
	@echo "  install   Create the local uv virtualenv and install all dependencies"
	@echo "  sync      Sync dependencies with the lockfile"
	@echo "  test      Run the test suite"
	@echo "  lint      Run ruff lint"
	@echo "  format    Run ruff format"
	@echo "  api       Run the FastAPI service with hot reload"
	@echo "  streamlit Run the Streamlit moderation console"
	@echo "  clean     Remove the .venv and build artifacts"

install:
	uv venv
	uv sync --all-extras

sync:
	uv sync --all-extras

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

api:
	uv run uvicorn app.api.main:app --reload

streamlit:
	uv run streamlit run app/streamlit/app.py

clean:
	rm -rf .venv
	rm -rf dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
