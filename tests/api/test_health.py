"""Smoke tests for /health and /version."""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version_includes_model(client):
    v = client.get("/version")
    assert v.status_code == 200
    body = v.json()
    assert body["api_version"] == "0.1.0"
    assert body["model_version"] == "m3-transformer"
