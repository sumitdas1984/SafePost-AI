# EXP-001 — M1: Product and Dataset

## Objective

Define SafePost AI's product scope (problem, target users, label taxonomy,
success criteria) and lock in the dataset that downstream modeling
(M2+) will train on.

## Dataset

- **Source URL:** <https://media.geeksforgeeks.org/wp-content/uploads/20250321123144355200/Dataset---Hate-Speech-Detection-using-Deep-Learning.csv>
- **Local copy:** `data/raw/hatespeech-dataset.csv` (gitignored)
- **Reproducibility:** `scripts/fetch_dataset.py` (idempotent, prints SHA-256 + logical row count)
- **SHA-256:** `3a9e3dc0fc80f3bfea1b590a0a4b5d481b1cdc1916a27716f7d87b03f0a9811d`
- **Size:** 24,783 data rows × 2 columns (`class`, `tweet`); 2.21 MB
- **License:** not formally documented (issue #3 closed as `not_planned`); treat as research-use-only until provenance is established
- **Class mapping:** `0 = hate_speech`, `1 = offensive_language`, `2 = neither`

## Decisions made during M1

| Decision | Outcome | Issue |
|---|---|---|
| Target users + use cases | Trust & Safety moderators (primary), platform engineers (secondary), console reviewers (tertiary). Pre-publish moderation is the primary use case. | #1 |
| Label taxonomy | 3-class (`HATE_SPEECH` / `OFFENSIVE_LANGUAGE` / `NEUTRAL`) confirmed — maps 1:1 onto the dataset's 0/1/2 labels | #1 |
| Out-of-scope for MVP | English-only, text-only, no real-time chat, no reputation scoring, no appeals, no mobile, no multi-tenant | #1 |
| Success metric (MVP) | Macro F1 ≥ 0.85 on the held-out test set | #1 |
| Dataset selection | GeeksforGeeks hate-speech CSV (informally chosen by the user; no formal comparison matrix) | #2 (skipped) |
| Dataset license / source doc | Skipped — URL is locked in `scripts/fetch_dataset.py` | #3 (skipped) |
| Modeling baseline | **BiLSTM is the baseline.** TF-IDF (originally planned for M2) is skipped. The TensorFlow BiLSTM in `notebooks/01_experiment_tf.ipynb` is the working baseline. | this note |

## Configuration

- **EDA notebook:** `notebooks/01_eda.ipynb` (PyTorch exploration of the dataset).
- **Baseline model notebook:** `notebooks/01_experiment_bilstm.ipynb` (TensorFlow BiLSTM — see `docs/experiments/M2-bilstm-baseline.md` for results).
- **Fetch script:** `scripts/fetch_dataset.py`.
- **Imbalance mitigation (informal, in the EDA notebook):** class 1 is subsampled to 3500 and class 0 repeated 3× to form a balanced training set. Not yet promoted to a reusable pipeline (issue #8).

## Results

- **Reproducible fetch:** `scripts/fetch_dataset.py --force` re-downloads to the same hash.
- **Dataset shape:** 24,783 rows × 2 columns, no missing values, no duplicates.
- **Class distribution (raw):** 0 = 5.77%, 1 = 77.43%, 2 = 16.80% — heavy skew toward `offensive_language`.
- **Tweet length:** median 13 words, p95 26, p99 29. `max_len = 100` is comfortable headroom.
- **Baseline signal:** the TF BiLSTM reached ~0.88 validation accuracy on the same preprocessing, confirming the dataset + cleaning pipeline is viable for downstream milestones.

## Learning

- The dataset is severely imbalanced (~78% `offensive_language`). The notebook's ad-hoc balancing works for a prototype but is not a reusable pipeline yet — needs issue #8.
- The dataset's exact license and citation are not formally documented. We can keep using it for local development but should not redistribute artifacts without resolving #3.
- The user chose to skip the formal dataset-selection ADR (issue #2) and skip the TF-IDF baseline. Documenting both decisions here keeps them out of the issue board — M2 picks up at BiLSTM, M3 likely picks up at Transformer or evaluation.

## Outstanding M1 follow-ups

These remain as open issues; M1 should not be marked closed until they move:

- **#6 — Analyze label distribution and class imbalance.** Partially covered by the EDA notebook; needs a written mitigation rationale.
- **#7 — Define train/validation/test split strategy.** No deterministic three-way split yet; the notebooks use `train_test_split(... test_size=0.2, random_state=42)` ad hoc.
- **#8 — Scaffold the data preprocessing pipeline.** Currently lives inside the notebooks. Needs to move into `ml/preprocessing/` with a unit test.
- **#21 — Set up the GitHub Project board.** Project board with Status / Priority / Milestone / Type / Area fields is not created yet.

## Next action

After M1 closes: open **M2 — BiLSTM Baseline (TensorFlow)** (the existing epic at issue #11, retitled) and promote the TensorFlow prototype into a reusable training script + serialized model artifact.
