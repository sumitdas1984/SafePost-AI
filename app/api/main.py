from fastapi import FastAPI

app = FastAPI(title="SafePost AI API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": app.version}


@app.post("/predict")
def predict(payload: dict):
    # Placeholder. Model integration will be implemented in M6.
    return {
        "label": "not_implemented",
        "confidence": 0.0,
        "action": "review",
        "model_version": "local-placeholder",
    }
