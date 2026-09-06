# Plan: Three-branch deployment architecture (FastAPI-only / SageMaker-only / Gateway)

## Context

SafePost AI's `docs/architecture.md` currently shows a single "target
architecture" that puts FastAPI in front of SageMaker (Option C — the
gateway pattern). For learning purposes, the user wants to build and
deploy **all three** serving patterns in parallel branches so they can
compare approaches and learn the trade-offs:

- **Branch A — `feature/fastapi-only`** — FastAPI serves the model directly (Option A).
- **Branch B — `feature/sagemaker-only`** — SageMaker Endpoint serves the model; Streamlit calls SageMaker directly (Option B).
- **Branch C — `feature/fastapi-gateway-sagemaker`** — FastAPI acts as a gateway to SageMaker (Option C).

Each branch:
- Is deployed to **real AWS**, not just local.
- Updates **`docs/architecture.md`** so the diagrams match that branch's chosen approach.
- Has its own deployment workflow and Terraform stack (or a shared stack with conditional modules).

The same ML logic (`app/inference.predict`) is shared across all three branches — only the HTTP wrapper changes.

## Branch layout

| Branch | Approach | When to ship | Stack |
|---|---|---|---|
| `feature/fastapi-only` | FastAPI serves the model directly | First | ECS Fargate + ALB + Docker + ECR + Terraform + CI/CD + CloudWatch |
| `feature/sagemaker-only` | SageMaker Endpoint serves the model; Streamlit calls SageMaker directly | Second | SageMaker Endpoint + custom inference container + ECR + Terraform + CI/CD + CloudWatch |
| `feature/fastapi-gateway-sagemaker` | FastAPI as a thin proxy → SageMaker Endpoint | Third | Both of the above + IAM SigV4 request signing + Cognito/ALB auth |

### Suggested order

1. **`feature/fastapi-only`** first — FastAPI already runs locally; the work is "deploy that same image to ECS". Lowest-effort big-learning chunk. ~1 day.
2. **`feature/sagemaker-only`** second — new territory (SageMaker SDK, custom inference container, endpoint lifecycle). ~1–2 days.
3. **`feature/fastapi-gateway-sagemaker`** last — combines both + adds IAM SigV4 signing. ~1 day.

## Mapping to existing GitHub issues

The current open issues already cover the work; no new issues needed.

| Issue | Closes in branch |
|---|---|
| **#14** FastAPI inference endpoint | `feature/fastapi-only` (locally done; AWS deploy is in #17) |
| **#15** SageMaker endpoint | `feature/sagemaker-only` |
| **#17** Docker + AWS app deployment | `feature/fastapi-only` + `feature/fastapi-gateway-sagemaker` |
| **#18** GitHub Actions CI/CD | All three branches (each has its own pipeline) |
| **#19** Terraform infrastructure | All three branches (each has its own stack) |
| **#20** Production monitoring (MLOps) | All three branches (CloudWatch dashboards differ per branch) |

## How `app/inference.py` stays the same across all three

The ML logic lives in `app/inference.py` and is intentionally HTTP-agnostic:

```
                    ┌─────────────────────────────┐
                    │  app/inference.predict(text) │   ← unchanged across branches
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
   ┌─────────┐              ┌─────────────┐             ┌────────────┐
   │ FastAPI │              │  SageMaker  │             │ FastAPI →  │
   │ route   │              │  endpoint   │             │ SageMaker  │
   │ /predict│              │ /invocations│             │ (gateway)  │
   └─────────┘              └─────────────┘             └────────────┘
      Branch A                 Branch B                    Branch C
```

The branch-specific code is just the HTTP wrapper:
- Branch A: `app/api/main.py` (already written)
- Branch B: `app/inference_sagemaker.py` + a SageMaker SDK deploy script
- Branch C: `app/api/main.py` calls SageMaker Runtime instead of `app.inference.predict` directly

## `docs/architecture.md` shape per branch

For `feature/fastapi-only`:

```text
User
  ↓
ALB
  ↓
ECS Fargate (FastAPI tasks, autoscaled)
  ↓
app/inference.predict  →  BiLSTM (in-process)
```

No SageMaker in the diagram. Stage 1 = local FastAPI; Stage 2 = ECS-hosted FastAPI.

For `feature/sagemaker-only`:

```text
User
  ↓
ALB + Cognito (optional)
  ↓
ECS Fargate (Streamlit tasks)
  ↓ HTTPS + IAM SigV4
SageMaker Endpoint
  ↓
Custom inference container → app/inference.predict → BiLSTM
```

For `feature/fastapi-gateway-sagemaker`:

```text
User
  ↓
ALB
  ↓
ECS Fargate (FastAPI tasks — gateway)
  ↓ HTTPS + IAM SigV4
SageMaker Runtime → SageMaker Endpoint
  ↓
Custom inference container → app/inference.predict → BiLSTM
```

Each branch's `docs/architecture.md` removes the lines that don't apply and adds the supporting AWS services that branch actually uses (Cognito for the gateway branch, etc.).

## Per-branch deliverables

For each of the three branches, the Definition of Done is:

- [ ] Inference path actually works end-to-end on AWS (not just local)
- [ ] `docs/architecture.md` updated to reflect that branch's chosen approach
- [ ] `docs/experiments/M{N}-{topic}.md` wrap-up note captures what was learned
- [ ] Terraform stack deployed via `terraform apply` (or LocalStack where applicable)
- [ ] CI/CD pipeline pushes images and applies infrastructure
- [ ] CloudWatch dashboard shows the relevant metrics
- [ ] Branch merged into `main` only after end-to-end verification

## Concrete first-step plan for `feature/fastapi-only`

Since FastAPI already runs locally, the only thing missing is the AWS side.

1. **Create the branch**
   ```bash
   git checkout main && git pull
   git checkout -b feature/fastapi-only
   ```

2. **Bring the FastAPI image up to ECS-ready shape**
   - `docker/api/Dockerfile` already exists; verify `uv sync --all-extras` runs inside.
   - Container binds to `0.0.0.0:8000` and respects `$PORT`.
   - Health endpoint responds inside the container.

3. **Push to ECR**
   - Create ECR repo `safepost-api` (via Terraform in step 5).
   - `docker build + docker tag + docker push`.

4. **ECS Fargate task definition + service**
   - Task: 0.5 vCPU / 1 GB RAM, single container from ECR image, port 8000.
   - Service: desired count 2, behind ALB.
   - ALB: HTTPS listener (ACM cert), target group on port 8000, health check `/health`.

5. **Terraform stack** (in `infrastructure/terraform/feature/fastapi-only/` or a shared path with conditional locals)
   - Resources: ECR repo, ECS cluster, ECS service + task def, ALB + target group + listener, security groups, IAM execution role, CloudWatch log group.
   - State backend: S3 + DynamoDB lock.
   - Outputs: ALB DNS name, ECR repo URL.

6. **GitHub Actions** (`#18`)
   - On push to branch: `uv sync + ruff + pytest`, build Docker image, push to ECR, `terraform apply`.

7. **CloudWatch** (`#20`)
   - Log group for the FastAPI task.
   - Metrics: request count, latency p50/p95/p99, 5xx count, target group healthy host count.
   - Alarms: 5xx > threshold, latency p95 > threshold.

8. **`docs/architecture.md`** + **`docs/experiments/M5-fastapi-only-aws.md`**
   - Update the diagram to show ECS-hosted FastAPI (no SageMaker).
   - Capture the deployment, what was learned, and any cost numbers.

## Out of scope

- **Real Cognito user pool** — the gateway branch (C) can use Cognito for end-user auth; fastapi-only and sagemaker-only branches don't need it for the learning scope.
- **Multi-region deployment** — single region only.
- **Production-grade autoscaling** — basic ECS Service auto-scaling is enough.
- **SageMaker-specific MLOps** — covered in the sagemaker-only branch.
