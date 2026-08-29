# EXP-003 — Train / Validation / Test Split Strategy

## Objective

Define a deterministic, stratified three-way split for the SafePost AI
dataset so M2 (BiLSTM), M3 (Transformer), and M4 (Evaluation + Model
Selection) can train, tune, and score against a reproducible benchmark
— and so the test set never leaks into training or model selection.

## Dataset version

- Source: `data/raw/hate_speech.csv` (or `data/raw/hatespeech-dataset.csv`
  if the fetch script's default name is in use).
- Provenance: `docs/experiments/M1-product-and-dataset.md`.
- Class distribution (raw): `0 = hate_speech` 5.77%, `1 = offensive_language` 77.43%, `2 = neither` 16.80%.

## Configuration

- **Method:** two-step stratified `train_test_split`.
- **Ratios:** 70 / 15 / 15 (train / val / test).
- **Seed:** `RANDOM_SEED = 42` (pinned constant at the top of `ml/data/split.py`).
- **Output:** `data/processed/{train,val,test}.csv` (gitignored).
- **Code:** `ml/data/split.py` — runnable as a script (`uv run python ml/data/split.py`) or importable from a notebook (`from ml.data.split import split_dataset`).

The two-step procedure:
1. First split: `test_size=0.15`, `stratify=df['class']` → `train_pool` (85%) / `test` (15%).
2. Second split: `test_size = 0.15 / 0.85 ≈ 0.1765`, `stratify=train_pool['class']` → `train` (70%) / `val` (15%).

## Result

| Split | Rows | % of total | Class 0 | Class 1 | Class 2 |
|---|---|---|---|---|---|
| train | 17,347 | 70.0% | 5.77% | 77.43% | 16.80% |
| val   |  3,718 | 15.0% | 5.78% | 77.43% | 16.78% |
| test  |  3,718 | 15.0% | 5.76% | 77.43% | 16.81% |
| **total** | **24,783** | **100%** | **5.77%** | **77.43%** | **16.80%** |

Class proportions match the raw distribution within ±0.02% across all three splits.

## Verification

- All three CSVs are written to `data/processed/`.
- Re-running the splitter produces byte-identical files (SHA-256 matches across runs).
- Tweet strings are disjoint across splits (no leakage).
- `data/processed/*.csv` is gitignored; `data/processed/.gitkeep` is tracked.
- Splitter also accepts `hatespeech-dataset.csv` (the fetch-script default) so it works regardless of which filename is in `data/raw/`.

## Learning

- A single `train_test_split` call can't produce three sets directly; two passes are needed to keep the train/val/test ratios exactly 70/15/15.
- Stratification matters here — the dataset is 78% `offensive_language`, so an unstratified split risks producing a val/test set with a meaningfully different class balance than the train set.
- A held-out test set is essential: the M2 / M3 notebooks have been scoring on the same val set they tuned on, which leaks information. M4 (Evaluation + Model Selection) should score both models on the new `data/processed/test.csv` so the comparison is honest.

## Next action

- M2 / M3 notebooks should be updated to load `data/processed/{train,val,test}.csv` instead of calling `train_test_split` ad hoc.
- M4 should report macro F1 + per-class precision/recall on `data/processed/test.csv` for both models.
- If a future experiment needs a different split ratio or seed, parameterize `split_dataset()` and write a new strategy note next to this one — never overwrite the existing CSVs in place without a deliberate, documented change.
