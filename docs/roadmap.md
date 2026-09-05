# SafePost AI — Roadmap & Progress

This is the repository-level execution tracker. Detailed task status should be maintained in the GitHub Project.

## Current Milestone

**M1 — Product + Dataset**

### Definition of Done
- [x] Product scope confirmed
- [x] Dataset selected
- [ ] Dataset license/source documented (skipped — see issue #3, `not_planned`)
- [x] Dataset downloaded
- [x] Dataset exploratory analysis completed
- [ ] Label distribution understood — covered informally in EDA, formal write-up tracked in #6
- [ ] Train/validation/test strategy defined — tracked in #7
- [ ] Data preprocessing pipeline skeleton created — tracked in #8
- [x] M1 notes captured in `docs/experiments/`

## Milestones

- [x] M1 — Product + Dataset
- [x] M2 — BiLSTM Baseline (TensorFlow) — replaces the original TF-IDF baseline
- [x] M3 — Transformer
- [x] M4 — Evaluation + Model Selection
- [x] M5 — FastAPI
- [ ] M6 — SageMaker
- [ ] M7 — Streamlit
- [ ] M8 — Docker + AWS Application
- [ ] M9 — GitHub Actions CI/CD
- [ ] M10 — Terraform
- [ ] M11 — MLOps + Monitoring

## Milestone Rule

Only one milestone should be actively built at a time.

When a milestone is complete:
1. Record what was learned.
2. Record important decisions.
3. Update this roadmap.
4. Create/close the corresponding GitHub Project items.
5. Move to the next milestone.
