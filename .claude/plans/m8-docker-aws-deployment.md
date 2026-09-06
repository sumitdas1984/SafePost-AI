# Plan: M8 — Docker + AWS App Deployment (#17)

## Context

Issue #17 covers the path from a working FastAPI service (M5) to a real
public endpoint on AWS. The user has a real AWS account, so this is the
first milestone where every artifact becomes a real running piece of
infrastructure: an ECR image, an ECS Fargate task, and an ALB-fronted
public URL. That makes it the highest-value hands-on AWS learning block
in the 2-day plan (after SageMaker / Terraform).

Current state on disk:
- `docker/api/Dockerfile` — placeholder, uses `pip install .` instead of `uv sync`.
- `docker/streamlit/Dockerfile` — placeholder, same issue.
- `docker/docker-compose.yml` — minimal (builds, exposes ports; no env, no
  healthchecks, no model mount, no API URL wiring).
- No `docker/.dockerignore`.
- `app/streamlit/app.py` — placeholder text-area + button; doesn't call the API.
- `models/m3-transformer/final/` — saved DistilBERT weights + tokenizer
  (gitignored; needs to be baked into the API image).

## Recommended approach

### Phase 1 — Local Dockerfiles (foundation, ~1 h)

**Status:** `app/streamlit/app.py` wiring is done (commit `7010f35`).
Remaining: the two Dockerfiles, `.dockerignore`, and the rewired
`docker-compose.yml`.

**`docker/api/Dockerfile`** — multi-stage, uv-based, non-root:
- Base: `python:3.11-slim-bookworm` (pinned tag).
- Install `uv` via the official `pip install uv` (or `COPY --from=...`).
- Copy `pyproject.toml` + `uv.lock` first (cache layer).
- `uv sync --frozen --no-dev` for reproducibility.
- Copy `app/` source.
- Copy `models/m3-transformer/final/` (model baked in).
- Non-root `appuser` (uid 1000).
- `HEALTHCHECK` via `curl -fsS http://localhost:8000/health`.
- `EXPOSE 8000`.
- `CMD ["uv", "run", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]`.

**`docker/streamlit/Dockerfile`** — same pattern, simpler:
- No model bake-in.
- `EXPOSE 8501`.
- `HEALTHCHECK` against `http://localhost:8501/_stcore/health` (Streamlit's built-in).
- `CMD ["uv", "run", "streamlit", "run", "app/streamlit/app.py", "--server.address=0.0.0.0"]`.

**`docker/.dockerignore`** — exclude build noise:
```
.venv/
.git/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.ipynb_checkpoints/
data/
notebooks/
docs/
tests/
.claude/
infrastructure/
models/
!models/m3-transformer/
!models/m3-transformer/final/
!models/m3-transformer/final/**
```

The negated lines re-include exactly the model directory the API image needs.

**`docker/docker-compose.yml`** — proper local wiring:
- `api` service: build from `docker/api/Dockerfile`, mount `models/` as a read-only
  volume so devs can iterate without rebuilding, port 8000, `PYTHONUNBUFFERED=1`.
- `streamlit` service: build from `docker/streamlit/Dockerfile`, port 8501,
  env `API_URL=http://api:8000`.
- Both services get healthchecks and `depends_on` with
  `condition: service_healthy`.

**`app/streamlit/app.py`** — wire to API: ✅ **done**
- Read `API_URL` from env (default `http://localhost:8000`).
- On "Analyze Post", POST to `${API_URL}/predict` with `{"text": ...}`.
- Display label / confidence / action in Streamlit components, with a
  color-coded action badge (`allow`=green, `flag`=orange, `block`=red).
- Surfaces backend errors inline so a failed API call doesn't crash the UI.
- `httpx>=0.27` was added to runtime deps for the call.

Verified locally with `uv run uvicorn ...` + `uv run streamlit run ...`.

### Phase 2 — ECR push (~30 min)

1. Create ECR repos in the AWS console (or via CLI):
   - `safepost-ai-api`
   - `safepost-ai-streamlit`
2. Log in to ECR and push:
   ```bash
   aws ecr get-login-password --region <r> \
     | docker login --username AWS --password-stdin <acct>.dkr.ecr.<r>.amazonaws.com
   docker build -f docker/api/Dockerfile -t safepost-ai-api:latest .
   docker tag  safepost-ai-api:latest <acct>.dkr.ecr.<r>.amazonaws.com/safepost-ai-api:latest
   docker push <acct>.dkr.ecr.<r>.amazonaws.com/safepost-ai-api:latest
   ```
3. Codify in `scripts/build_and_push.sh` — single script that builds both
   images, tags with a timestamp, and pushes to ECR. Tag every resource
   with `Project=SafePostAI`.

### Phase 3 — ECS Fargate + ALB (~2 h)

1. **Cluster:** `safepost-ai-cluster` (AWS Fargate, no EC2).
2. **IAM task execution role:** `safepost-ai-exec-role` with the
   `AmazonECSTaskExecutionRolePolicy` attached (pulls from ECR, writes
   CloudWatch logs).
3. **CloudWatch log group:** `/ecs/safepost-ai-api` (and
   `/ecs/safepost-ai-streamlit` if Phase 4 happens).
4. **Task definition** for the API:
   - Image: `safepost-ai-api:latest` from ECR.
   - CPU: 1024, Memory: 2048 (CPU torch needs RAM; start higher than the
     Fargate minimums).
   - Container port: 8000.
   - Log driver: `awslogs` → the log group above.
5. **Target group:** `safepost-ai-api-tg`, port 8000, health check
   `/health`, deregistration delay 30 s.
6. **ALB:** `safepost-ai-alb`, internet-facing, scheme `ipv4`, listener
   on port 80 → forward to the target group.
7. **Security groups:**
   - ALB SG: inbound `0.0.0.0/0:80`, all egress.
   - Service SG: inbound from ALB SG only on port 8000, all egress.
8. **Fargate service:**
   - Desired tasks: 1 (start at 1; auto-scaling is a later exercise).
   - Network mode `awsvpc`, two subnets from the default VPC.
   - `assignPublicIp: ENABLED` (simplest path; NAT gateway not needed).
   - Load balancer: attach to the target group.
9. **Smoke test the public endpoint:**
   `curl http://<alb-dns>/health` → `{"status":"ok"}`.

### Phase 4 — Streamlit on ECS (optional, ~1 h)

Same pattern as the API service. Env `API_URL` points at the API's ALB
DNS. Skip this phase if running short on time — the API alone is the
deployable deliverable; Streamlit can stay on `docker compose`.

## Critical files

**Create / overwrite:**
- `docker/api/Dockerfile` — multi-stage, uv, non-root, healthcheck.
- `docker/streamlit/Dockerfile` — same pattern, simpler.
- `docker/.dockerignore`
- `docker/docker-compose.yml` — proper local wiring.
- `app/streamlit/app.py` — wire to API via env `API_URL`.
- `scripts/build_and_push.sh` — ECR push helper.
- `docs/experiments/M8-docker.md` — wrap-up note.

**No change:**
- `app/api/main.py` — already serves the contract M5 ships.
- `pyproject.toml` — runtime deps already include FastAPI, transformers, torch.
- AWS CLI config — user-managed.

## Verification

1. **Local:** `docker compose up --build` →
   - `curl localhost:8000/health` returns `{"status":"ok"}`.
   - `curl localhost:8000/predict -d '{"text":"I love this"}' -H 'content-type: application/json'` returns a real prediction.
   - `localhost:8501` shows the Streamlit UI; "Analyze Post" returns a real label.
2. **Image size:** `docker images safepost-ai-api` — expect ~1.5–2.5 GB
   (CPU torch + transformers stack). Streamlit image should be ~1.2 GB.
3. **ECR:** `aws ecr describe-images --repository-name safepost-ai-api`
   lists the pushed image with the expected tag.
4. **ECS:** AWS console → ECS → `safepost-ai-cluster` → service
   `safepost-ai-api-svc` → 1 task in `RUNNING`.
5. **Public endpoint:** `curl http://<alb-dns>/health` returns
   `{"status":"ok"}` from outside the VPC.
6. **End-to-end from anywhere:** `curl http://<alb-dns>/predict ...`
   returns a real prediction; latency 200–500 ms cold, 50–150 ms warm.

## Out of scope (deliberate)

- **Terraform codification** — that's #19. Phase 3 creates resources via
  the console or CLI; Terraform can re-encode the same shape later.
- **HTTPS / custom domain** — ALB HTTP only. ACM cert + Route 53 +
  HTTPS listener come later.
- **Auto-scaling** — service fixed at 1 task. Min/max/desired can be
  set; start at 1.
- **CI/CD-driven builds** — that's #18. Phase 2 is a manual
  `bash scripts/build_and_push.sh`.
- **Streamlit polish** — basic UI is enough; that's #16. ECS-Streamlit
  is a Phase 4 optional.
- **SageMaker endpoint** — that's #15. The ECS deployment in this
  milestone uses the same ECR image but a different service shape.

## Time estimate

- Phase 1 (local Dockerfiles + compose + Streamlit wiring): ~1 h
- Phase 2 (ECR push, manual): ~30 min
- Phase 3 (ECS Fargate + ALB): ~2 h
- Phase 4 (Streamlit on ECS, optional): ~1 h

Total: ~3.5–4.5 h for the full milestone. Phase 4 is the first thing to
skip if running short on time.

## Cost control reminder

ECS Fargate + ALB accrues per-hour cost. From the prior
`.claude/plans/prioritization-2day-aws-interview.md`:

- **Billing alarm at $20** in CloudWatch before starting.
- Tag every resource with `Project=SafePostAI`.
- Tear down the service (`update-service desired-count=0`) when not in
  use; ALB has a fixed hourly cost regardless.
