"""Smoke tests for the /predict endpoint.

Validates the response contract (label, confidence, action, model_version)
without asserting specific predictions — the DistilBERT fine-tune is at
1 epoch and per-class behavior will shift with retraining.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app

ALLOWED_LABELS = {"hate_speech", "offensive_language", "neutral"}
ALLOWED_ACTIONS = {"allow", "flag", "block"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def test_predict_response_shape(client):
    r = client.post("/predict", json={"text": "I had a great day today!"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"label", "confidence", "action", "model_version"}
    assert body["label"] in ALLOWED_LABELS
    assert body["action"] in ALLOWED_ACTIONS
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_version"] == "m3-transformer"


def test_predict_rejects_empty_text(client):
    bad = client.post("/predict", json={"text": ""})
    assert bad.status_code == 422
