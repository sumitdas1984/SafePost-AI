# EXP-005 — M5: FastAPI Inference Endpoint

## Objective

Expose the M3 DistilBERT model behind a FastAPI service so downstream
milestones (SageMaker, Streamlit, ECS) can call it over HTTP instead of
loading the model themselves.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/version` | API version + model version |
| POST | `/predict` | Text → `{label, confidence, action, model_version}` |

### `POST /predict` request / response

```json
// Request
{"text": "you are a stupid idiot"}

// Response (200)
{
  "label": "offensive_language",
  "confidence": 0.7310,
  "action": "flag",
  "model_version": "m3-transformer"
}
```

`label` ∈ {`hate_speech`, `offensive_language`, `neutral`}.
`action` is mapped from `label`:

| Label | Action |
|---|---|
| `hate_speech` | `block` |
| `offensive_language` | `flag` |
| `neutral` | `allow` |

## Configuration

- **Framework:** FastAPI + Pydantic v2.
- **Model:** `distilbert-base-uncased` fine-tuned for 1 epoch on
  `data/processed/{train,val,test}.csv` (see `docs/experiments/m3_metrics.json`).
- **Inference device:** CPU (no GPU; ~250 MB model weight, ~50–200 ms
  per single-text call on a modern laptop CPU).
- **Tokenizer:** HuggingFace `AutoTokenizer`, `max_length=128`,
  truncation on, padding to max length.
- **Model loading:** once at startup, via FastAPI lifespan. Cached via
  `functools.lru_cache` so subsequent `get_model()` calls return the
  same instance.

## Result

Smoke tests via `uv run pytest tests/api/ -v` pass:

```
tests/api/test_health.py::test_health PASSED                       [ 25%]
tests/api/test_health.py::test_version_includes_model PASSED       [ 50%]
tests/api/test_predict.py::test_predict_response_shape PASSED      [ 75%]
tests/api/test_predict.py::test_predict_rejects_empty_text PASSED  [100%]
======================== 4 passed, 1 warning in 7.85s =========================
```

End-to-end smoke check against the running app:

| Input | Output |
|---|---|
| `I love this product` | `neutral` (conf 0.95) → `allow` |
| `you are a stupid idiot` | `offensive_language` (conf 0.73) → `flag` |
| `Lets discuss politics calmly` | `neutral` (conf 0.94) → `allow` |

## Architecture

```
app/
  api/
    main.py            FastAPI app, lifespan, endpoints, Pydantic models
    services/
      __init__.py
      predict.py       ModelBundle (load + predict), get_model() cache
tests/api/
  test_health.py       /health + /version smoke tests
  test_predict.py      /predict shape + validation smoke tests
```

The model + tokenizer stay in `models/m3-transformer/final/` (gitignored).
`get_model()` is the only entry point; the FastAPI lifespan pulls it once
and stashes it on `app.state.model`.

## Run

```bash
uv sync
uv run uvicorn app.api.main:app --reload      # local dev
# OR
uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000  # container
```

## Known caveats

- **Macro F1 0.751** is below the PRD's ≥0.85 target. `hate_speech`
  recall is 0.30 (see `docs/experiments/m3_metrics.json`). The endpoint
  surfaces this without mitigation; production should add a confidence
  threshold or a `flag` override for `hate_speech` to be safe.
- **Single-text inference only.** No batch endpoint. For bulk
  inference, wrap multiple calls client-side or extend with a
  `/predict/batch` route.
- **No auth.** The endpoint is unauthenticated. Production deployment
  needs IAM / API Gateway auth in front.
- **No structured logging / metrics.** `print()`-only. M11 (#20) adds
  CloudWatch custom metrics; this milestone doesn't.

## Artifacts

- `app/api/main.py` — FastAPI app, lifespan, endpoints.
- `app/api/services/predict.py` — inference service.
- `tests/api/test_health.py`, `tests/api/test_predict.py` — smoke tests.
- `models/m3-transformer/final/` — saved model + tokenizer (gitignored).
- `docs/experiments/m5-fastapi.md` — this note.

## Next action

Wrap the FastAPI service as a Docker image (M8 / #17) and push it to
ECR. The Dockerfile is the next step; SageMaker and ECS Fargate both
consume from ECR.
