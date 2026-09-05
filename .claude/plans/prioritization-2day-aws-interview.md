# Plan: 2-day reprioritization to learn advanced AWS services by doing

## Context

The user is preparing for a Principal AI Engineering interview in ~2 days
with an AWS-cloud-deployment focus. **The project is not being showcased
in the interview** — it's being used as a learning vehicle for advanced
AWS services. They know the basics (IAM, S3, Lambda, ECR, ECS) but have
limited or no hands-on experience with **SageMaker** and **Terraform**
(plus CI/CD with OIDC, MLOps/monitoring). Doing the work in this repo is
how they'll learn those services deeply enough to answer interview
questions on them.

**The user has a real AWS account.** This changes the calculus significantly
vs. local-mode / LocalStack — they can deploy a real SageMaker endpoint,
push to a real ECR, run real Terraform applies, and observe real CloudWatch
metrics. The learning value per hour goes up because every artifact is real.

Current model state:
- **M2 (BiLSTM)** is done — val 0.89, test 0.89 on the `data/processed/`
  splits. See `docs/experiments/M2-bilstm-baseline.md`.
- **M3 (Transformer, DistilBERT)** is in progress. The 1-epoch finetune
  produced a model with **better test accuracy than BiLSTM** but the
  notebook outputs were lost (training cell ran, eval cells didn't get
  committed with the metrics). The finetuned model + tokenizer are
  saved to `models/m3-transformer/final/` — that artifact is preserved.
  The notebook is being re-run end-to-end to repopulate the metrics.
- **M4 (Evaluation + Model Selection)** is not started.

Decision: cap M3 (already done), capture the re-run metrics, run a
minimal M4 comparison, then pivot hard to the deployment milestones.
**SageMaker and Terraform are the primary learning goals** — everything
else is supporting infrastructure. With the AWS account, every
deployment artifact is real and reusable in the interview.

## Recommended approach

The priorities are driven by **learning value per hour**, not just
interview relevance. Services the user has never touched (SageMaker,
Terraform, OIDC-based CI/CD) deserve the most time because that's where
the interview's unknowns are.

### M3 (#12) — Transformer: cap aggressively

- Limit to **1 epoch** of fine-tuning, batch size 16. On CPU with 17,347
  rows, expect ~45–60 min.
- Save the partial model + tokenizer to `models/m3-transformer/final/`
  even if it's underfit.
- Eval cells in the notebook (cells 22, 24, 26) still produce numbers —
  that's all M4 needs.
- Capture the result in `docs/experiments/M3-transformer.md` with
  whatever macro F1 / accuracy you have.

### M4 (#13) — Evaluation + Model Selection: keep light

- Single comparison notebook (e.g. `notebooks/03_evaluation.ipynb`) that
  loads both models' predictions on `data/processed/test.csv`.
- Side-by-side classification report + confusion matrix.
- Pick a winner; record the rationale. Move on.

### Priority ordering for the deployment milestones

Effort estimates assume **real AWS** — the user has an account and IAM
permissions. **Set a billing alarm before starting** (see "Cost
control" below) so a runaway endpoint or ECR repo doesn't surprise you.

| Order | Issue | Effort | Learning value | What's new vs what you already know |
|---|---|---|---|---|
| 1 | #14 FastAPI | 1–2 h | Low | Probably familiar. Wrap BiLSTM in `/predict`; Pydantic request/response. |
| 2 | #17 Docker (API image) | 2–3 h | Medium | ECR-ready image. `uv sync --all-extras` inside the build. Push to real ECR. |
| 3 | **#15 SageMaker** | 4–6 h | **Very high** | **Real endpoint.** Inference containers, models, endpoint configs, real-time endpoints, **optionally** local mode for iteration, batch transform, data capture. |
| 4 | **#19 Terraform** | 3–4 h | **Very high** | **Real apply.** HCL, AWS provider, resources, modules, variables/outputs, state, remote backend (S3 + DynamoDB), lifecycle rules. |
| 5 | #18 GitHub Actions CI/CD | 2–3 h | High | Static AWS keys + ECR push + (optional) deploy-to-SageMaker job. |
| 6 | #20 MLOps / monitoring | 1–2 h | High | CloudWatch custom metrics from FastAPI, model monitoring, basic drift detection. |
| 7 | #16 Streamlit | 1 h | None | "Hello world" UI. Skip unless time. |

**Total: ~15–23 hours** across 2 days. SageMaker + Terraform together
are ~7–10 hours — that's the bulk of the learning.

## Concepts you'll absorb by doing

By the time the 2 days are done, the user will have hands-on exposure to:

**SageMaker**
- Inference containers (custom vs prebuilt)
- Models, endpoint configurations, real-time endpoints
- Local mode (full SDK workflow on the laptop, no AWS account)
- Batch transform jobs
- Data capture for monitoring
- IAM execution roles for SageMaker
- Auto-scaling policies

**Terraform**
- HCL syntax (resources, data sources, variables, outputs, locals)
- AWS provider configuration
- Module pattern for reusable infrastructure
- Remote state backend (S3 + DynamoDB lock)
- `terraform plan` / `terraform apply` workflow
- Importing existing resources
- Lifecycle rules (create_before_destroy, ignore_changes)

**CI/CD + MLOps**
- GitHub Actions with **static AWS keys** in repo secrets (simpler than OIDC
  for a learning project; OIDC is the production best practice but adds setup
  steps — defer until you need it).
- ECR push workflow
- CloudWatch custom metrics from a FastAPI endpoint
- SageMaker Model Monitor basics
- Drift detection (data drift vs concept drift)

## Trade-offs to flag

1. **Real AWS is now on the table.** SageMaker real-time endpoints, ECR
   push, Terraform applies, CloudWatch custom metrics — every artifact
   becomes real and demonstrable. Learning value per hour goes up.
2. **Cost control.** Real endpoints cost money per hour. Before starting
   any deployment work, set a **billing alarm** in the AWS console:
   - CloudWatch → Alarms → Billing → Create alarm → set threshold at $20
     (or whatever your comfort is) → SNS topic that emails you
   - Tag every resource with `Project=SafePostAI` so you can find stragglers
   - Tear down endpoints and stop notebooks when not in use; SageMaker
     endpoints accrue cost while `InService`
3. **Local mode is still useful for iteration.** Even with real AWS
   available, SageMaker local mode lets you iterate on the inference
   container without round-tripping to AWS. Use local mode for the
   first end-to-end loop; deploy to real AWS once it works.
4. **Terraform scope creep is real.** Restrict #19 to S3 + ECR + ECS
   Fargate. That's enough to learn the full Terraform workflow without
   burning the day on resource sprawl.
5. **Time budget is the constraint.** SageMaker + Terraform are 7–10
   hours together. Don't let supporting infrastructure (FastAPI, Docker,
   Streamlit) eat into that. If #14 takes longer than 2 hours, ask why.

## M3 rerun — saving the metrics this time

The previous M3 run lost its eval outputs (only the training cell was
captured; cells 22 / 24 / 26 / 28 had no outputs). The finetuned model
+ tokenizer are preserved in `models/m3-transformer/final/` — that
artifact is safe.

When the rerun finishes, capture the metrics durably:
1. **Commit the notebook with all outputs** (`git add notebooks/02_experiment_transformer.ipynb`)
   immediately after the eval cells finish — don't wait.
2. **Update `docs/experiments/M3-transformer.md`** with the val/test
   numbers, per-class report, and a "Comparison with BiLSTM" section.
3. **Save the model metrics to a JSON file** for M4 to load:
   `models/m3-transformer/metrics.json` — accuracy, macro precision,
   recall, F1 for val and test, plus the per-class dict. Make this
   commit a separate step so the notebook commit doesn't accidentally
   regress if cells are re-run.
4. **Write a "rerun discipline" note** in the M3 doc: "If you re-run
   the notebook, save before re-running — outputs aren't reliably
   preserved otherwise."

## Concrete next steps

1. **Tonight:** finish M3 with the 1-epoch cap. Save outputs.
2. **Tomorrow morning:** M4 evaluation + comparison notebook + decision.
3. **Tomorrow afternoon:** #14 FastAPI + #17 Docker.
4. **Day 2 morning:** #15 SageMaker local mode + #19 Terraform.
5. **Day 2 afternoon:** #18 CI/CD + #20 MLOps if time permits.

## Out of scope for this 2-day window

- **#16 Streamlit** — low learning value, skip unless there's a free hour.
- **Real AWS deployment beyond local mode** — depends on AWS account
  availability and credit budget. Worth attempting only after #15 and #19
  are solid.
- **Production-grade model performance** — BiLSTM at 0.89 is good enough.

## Critical files (created/touched in this 2-day window)

- `app/api/main.py` — replace placeholder with real `/predict` (#14).
- `docker/api/Dockerfile` — API image (#17).
- `notebooks/03_evaluation.ipynb` — comparison notebook (#13).
- `docs/experiments/M3-transformer.md` — M3 wrap-up note.
- `docs/experiments/M4-evaluation.md` — M4 wrap-up note.
- `infrastructure/terraform/` — S3 + ECR + ECS modules (#19).
- `.github/workflows/ci.yml` — static AWS keys + ECR push (#18).
- `app/streamlit/app.py` — minimal UI (#16, optional).
- AWS: real SageMaker endpoint, ECR repo, ECS Fargate service, CloudWatch
  metrics + billing alarm — all tagged `Project=SafePostAI`.
