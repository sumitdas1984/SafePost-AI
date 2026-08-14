# SafePost AI — Compact PRD

**Status:** Planned  
**Goal:** End-to-end ML → AWS → production learning project

## Product

SafePost AI is a social-media text moderation platform that classifies posts into:

- `HATE_SPEECH`
- `OFFENSIVE_LANGUAGE`
- `NEUTRAL`

It returns a **label, confidence, model version, and recommended moderation action**.

## Goals

- Build and evaluate a deep-learning NLP classifier.
- Compare baseline → BiLSTM → Transformer.
- Expose inference through FastAPI.
- Deploy model inference using Amazon SageMaker.
- Build a Streamlit moderation UI.
- Containerize and deploy the application on AWS.
- Implement GitHub Actions CI/CD.
- Learn model versioning, monitoring, and IaC.

## Target Architecture

```text
User
 ↓
Streamlit
 ↓
FastAPI
 ↓
SageMaker Runtime
 ↓
SageMaker Endpoint
 ↓
NLP Model
 ↓
Prediction
```

AWS:

```text
S3          → datasets + model artifacts
ECR         → Docker images
ECS/Fargate → Streamlit + FastAPI
SageMaker   → model inference
CloudWatch  → logs + metrics
IAM         → access control
Terraform   → infrastructure
GitHub Actions → CI/CD
```

## ML Lifecycle

```text
Dataset → Validation → TF-IDF Baseline → BiLSTM → Transformer
        → Evaluation → Model Selection → Registry/S3 → SageMaker
```

## API

`POST /predict`

```json
{"text": "some social media post"}
```

```json
{
  "label": "hate_speech",
  "confidence": 0.94,
  "action": "flag",
  "model_version": "transformer-v1"
}
```

Also:

```text
GET /health
GET /version
```

## Milestones

| # | Milestone | Outcome |
|---|---|---|
| 1 | Product + Dataset | Problem and data defined |
| 2 | Baseline | TF-IDF classifier |
| 3 | Deep Learning | BiLSTM classifier |
| 4 | Transformer | Fine-tuned transformer |
| 5 | Evaluation | Model comparison + selection |
| 6 | API | Local FastAPI inference |
| 7 | SageMaker | Cloud model endpoint |
| 8 | UI | Streamlit moderation console |
| 9 | Docker + AWS | Containerized application |
| 10 | CI/CD | Automated deployment |
| 11 | Terraform | Reproducible infrastructure |
| 12 | MLOps | Monitoring + model lifecycle |

## MVP

```text
Dataset → Model → Evaluation → FastAPI → SageMaker → Streamlit
```

Do not start with the complete AWS infrastructure.

Recommended sequence:

**ML → API → SageMaker → UI → Docker → AWS App → CI/CD → Terraform → MLOps**
