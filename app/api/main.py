"""SafePost AI FastAPI service.

Loads the M3 DistilBERT model at startup via a lifespan handler and
exposes three endpoints:

- ``GET  /health``   liveness probe
- ``GET  /version``  API + model version
- ``POST /predict``  text -> {label, confidence, action, model_version}
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from app.api.services.predict import get_model

API_VERSION = "0.1.0"


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw social-media post text")


class PredictResponse(BaseModel):
    label: str
    confidence: float
    action: str
    model_version: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Load the model bundle once at startup. ``get_model`` is cached, so
    # any caller that grabs it during request handling sees the same instance.
    app.state.model = get_model()
    yield


app = FastAPI(
    title="SafePost AI API",
    version=API_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version(request: Request) -> dict:
    return {
        "api_version": API_VERSION,
        "model_version": request.app.state.model.model_version,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request) -> dict:
    return request.app.state.model.predict(payload.text)
