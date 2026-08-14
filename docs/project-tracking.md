# GitHub Project Tracking Guide

Use the GitHub Project as the execution board.

## Suggested fields

- Status: Backlog / Ready / In Progress / Blocked / Done
- Priority: P0 / P1 / P2
- Milestone
- Type: Feature / Task / Bug / Experiment / Tech Debt
- Area: ML / API / UI / AWS / DevOps / MLOps / Docs

## Issue pattern

Prefer small issues that can normally be completed in one focused session.

Example:

```text
[M2][ML] Implement TF-IDF baseline

Acceptance criteria:
- Training script runs
- Validation metrics are produced
- Test metrics are saved
- Model artifact is generated
- Experiment note is created
```

## Repository vs GitHub Project

Repository:
- Code
- Documentation
- Experiment results
- Architecture decisions
- Configuration

GitHub Project:
- What to do
- What is in progress
- What is blocked
- What is complete
