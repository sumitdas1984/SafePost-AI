# EXP-002 — M2: BiLSTM Baseline (TensorFlow)

## Objective

Establish a Bidirectional LSTM as the project's first non-trivial baseline
for 3-class hate-speech classification, ahead of any Transformer comparison.

## Dataset version

- `data/raw/hatespeech-dataset.csv` — 24,783 rows × 2 columns.
- Class-balanced training set: class 1 subsampled to 3500, class 0
  repeated 3×, class 2 kept as-is. Split: `train_test_split(... test_size=0.2, random_state=42)`.
- Provenance and SHA-256: see `docs/experiments/M1-product-and-dataset.md`.

## Configuration

- **Framework:** TensorFlow / Keras (`tensorflow.keras.Sequential`).
- **Vocabulary / sequence:** `max_words = 10000`, `max_len = 100`, Keras
  `Tokenizer(num_words=10000, lower=True, split=' ')`, `pad_sequences(... padding='post', truncating='post')`.
- **Architecture (346,755 params):**
  ```
  Embedding(10000, 32, input_length=100)
    → Bidirectional(LSTM(16))
    → Dense(512, activation='relu', kernel_regularizer='l1')
    → BatchNormalization()
    → Dropout(0.3)
    → Dense(3, activation='softmax')
  ```
- **Loss / optimizer:** `categorical_crossentropy`, `adam`.
- **Callbacks:** `EarlyStopping(patience=3, monitor='val_accuracy', restore_best_weights=True)`, `ReduceLROnPlateau(patience=2, monitor='val_loss', factor=0.5)`.
- **Training:** `batch_size=32`, `epochs=50` (EarlyStopping fired at epoch 5), `~7–10s` per epoch on CPU.

## Result

Per-epoch log (visible in `notebooks/01_experiment_tf.ipynb`, cell 19):

| Epoch | Train Acc | Val Acc | Val Loss | LR |
|---|---|---|---|---|
| 1 | 0.7531 | 0.7900 | 0.9334 | 1.0e-3 |
| 2 | 0.9016 | **0.8766** | **0.4560** | 1.0e-3 |
| 3 | 0.9368 | 0.6412 | 1.9503 | 1.0e-3 |
| 4 | 0.9531 | 0.8248 | 0.6939 | 5.0e-4 |
| 5 | 0.9726 | 0.8185 | 0.6807 | 5.0e-4 |

**Final evaluation (best weights restored by EarlyStopping):**
- `model.evaluate(X_val_padded, Y_val)` → accuracy **0.8766**, loss **0.4560**.
- Reported as "Validation Accuracy: 0.88" in cell 22.

The notebook does **not** currently emit macro F1, per-class precision/recall, or a confusion matrix. M4 (Evaluation + Model Selection) will be the place to add those — both models need to be on the same metric set for the comparison to be fair.

## Learning

- **Best epoch is epoch 2.** From epoch 3 onward the model overfits the training set (train accuracy climbs past 0.93 while val accuracy oscillates 0.64–0.83). The L1 regularizer + dropout helps but isn't enough — the architecture is overparameterized for 24k tweets.
- **ReduceLROnPlateau fires after epoch 3** (LR drops from 1e-3 to 5e-4). It does not recover the epoch-2 peak; the train loss continues to drop.
- **The current val set doubles as the test set** — `train_test_split(... test_size=0.2, random_state=42)` is the only split. There is no held-out test set. M4 should treat the val split as the comparison set and document the limitation.
- **Class imbalance is partially addressed.** The notebook balances via subsampling/repetition, but class weights are not set on the loss. If M3 (Transformer) doesn't beat this number, the next experiment should try `class_weight` instead.
- **Macro F1 is missing.** The success metric from issue #1 is `Macro F1 ≥ 0.85`. We have accuracy = 0.88 but no F1. The class distribution (5.77% hate_speech) means macro F1 will likely be lower than accuracy — needs to be measured in M4.

## Next action

- Open **M3 — Transformer Fine-tuning** (issue #12) and run a comparable fine-tune
  against the same split + preprocessing so M4 can compare apples to apples.
- In M4, add macro F1 + per-class precision/recall + confusion matrix to both notebooks
  before picking a winner.
- Defer #7 (split strategy) and #8 (preprocessing skeleton) — M2's ad-hoc split and
  in-notebook preprocessing are sufficient for the M2/M3/M4 comparison round.

## Artifacts

- `notebooks/01_experiment_tf.ipynb` — full notebook (data → preprocess → tokenize → model → train → evaluate).
- `docs/experiments/M2-bilstm-baseline.md` — this note.
