# SafePost AI — Architecture

## Target Architecture

```text
                         ┌───────────────┐
                         │     User      │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │   Streamlit   │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │    FastAPI    │
                         └───────┬───────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ SageMaker Runtime │
                       └─────────┬─────────┘
                                 │
                                 ▼
                       ┌───────────────────┐
                       │ SageMaker Endpoint│
                       │   NLP Classifier  │
                       └───────────────────┘
```

## Supporting AWS Services

```text
S3 → data/model artifacts
ECR → container images
ECS/Fargate → application
IAM → permissions
CloudWatch → logs/metrics
Terraform → infrastructure
```

## Architecture Evolution

### Stage 1 — Local

```text
Streamlit → FastAPI → Local Model
```

### Stage 2 — Cloud Model

```text
Streamlit → FastAPI → SageMaker Endpoint
```

### Stage 3 — Production-oriented

```text
GitHub
  ↓
GitHub Actions
  ↓
ECR
  ↓
ECS/Fargate
  ↓
FastAPI
  ↓
SageMaker
```
