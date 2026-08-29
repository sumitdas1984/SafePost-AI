# EXP-002 — M2: BiLSTM Baseline (TensorFlow)

## Objective

Establish a Bidirectional LSTM as the project's first non-trivial baseline
for 3-class hate-speech classification, ahead of any Transformer comparison.

## Dataset version

- Pre-split CSVs at `data/processed/{train,val,test}.csv` produced by
  `ml/data/split.py` (stratified 70 / 15 / 15, seed 42).
- Sizes: train 17,347 / val 3,718 / test 3,718 rows (24,783 total).
- Class distribution preserved across all splits (5.77 / 77.43 / 16.80).
- Provenance and SHA-256: see `docs/experiments/M1-product-and-dataset.md`.

## Configuration

- **Framework:** TensorFlow / Keras (`tensorflow.keras.Sequential`).
- **Vocabulary / sequence:** `max_words = 5000` (Tokenizer), `max_len = 100`,
  Keras `Tokenizer(num_words=5000, lower=True, split=' ')`,
  `pad_sequences(... padding='post', truncating='post')`.
- **Architecture (346,755 params):**
  ```
  Embedding(10000, 32, input_length=100)
    → Bidirectional(LSTM(16))
    → Dense(512, activation='relu', kernel_regularizer='l1')
    → BatchNormalization()
    → Dropout(0.3)
    → Dense(3, activation='softmax')
  ```
  Note: `Tokenizer` is capped at 5000 but `Embedding` input_dim is 10000.
  The mismatch is carried forward from the original notebook; the actual
  vocab in use is the smaller 5000.
- **Loss / optimizer:** `categorical_crossentropy`, `adam`.
- **Callbacks:** `EarlyStopping(patience=3, monitor='val_accuracy', restore_best_weights=True)`, `ReduceLROnPlateau(patience=2, monitor='val_loss', factor=0.5)`.
- **Training:** `batch_size=32`, `epochs=50` (EarlyStopping fired at epoch 5), `~8–10s` per epoch on CPU.

## Result

Per-epoch log (visible in `notebooks/01_experiment_tf.ipynb`, cell 19):

| Epoch | Train Acc | Val Acc | Val Loss | LR |
|---|---|---|---|---|
| 1 | 0.8613 | 0.7867 | 0.5497 | 1.0e-3 |
| 2 | 0.9020 | **0.8876** | **0.3901** | 1.0e-3 |
| 3 | 0.9119 | 0.8857 | 0.4190 | 1.0e-3 |
| 4 | 0.9223 | 0.8857 | 0.4342 | 1.0e-3 |
| 5 | 0.9383 | 0.8854 | 0.4533 | 5.0e-4 |

**Final evaluation (best weights restored by EarlyStopping):**
- `model.evaluate(X_val_padded, Y_val)` → accuracy **0.8876**, loss **0.3901**. Reported as "Validation Accuracy: 0.89".
- `model.evaluate(X_test_padded, Y_test)` → accuracy **0.8892**, loss **0.3870**. Reported as "Test Accuracy: 0.89".

The notebook does **not** currently emit macro F1, per-class precision/recall, or a confusion matrix. M4 (Evaluation + Model Selection) will be the place to add those — both models need to be on the same metric set for the comparison to be fair.

## Comparison vs. the first M2 run

The notebook was first run with an ad-hoc balanced subset (class 1 subsampled
to 3500, class 0 repeated 3×) and a single 80 / 20 split. That run reached
val_accuracy 0.8766 / "Validation Accuracy: 0.88" with no held-out test
evaluation.

After switching to `data/processed/`:
- The training set is now 17,347 rows (vs ~13,553 before) with the natural
  5.77 / 77.43 / 16.80 distribution (vs the old manually-balanced subset).
- Val accuracy improved slightly (0.8876 vs 0.8766).
- A held-out test set is now actually held out — test 0.8892 ≈ val 0.8876
  means the val-set selection wasn't leaking.

## Learning

- **Best epoch is epoch 2.** From epoch 3 onward val accuracy plateaus near 0.886 while train accuracy climbs past 0.93. The L1 regularizer + 0.3 dropout helps but isn't enough — the architecture is overparameterized for 17k training rows.
- **ReduceLROnPlateau fires after epoch 3** (LR drops from 1e-3 to 5e-4). It does not move val accuracy; the model is already in its plateau.
- **The held-out test set matches val accuracy (within 0.002).** That's the good case for the new splits — the val set was genuinely held out from training, and the test set confirms it.
- **Macro F1 is missing.** The success metric from issue #1 is `Macro F1 ≥ 0.85`. We have accuracy = 0.89 but no F1. The class distribution (5.77% hate_speech) means macro F1 will likely be lower than accuracy — needs to be measured in M4.

## Next action

- Open **M3 — Transformer Fine-tuning** (issue #12) and run a comparable fine-tune
  against the same splits + preprocessing so M4 can compare apples to apples.
- In M4, add macro F1 + per-class precision/recall + confusion matrix to both notebooks
  before picking a winner.
- Defer #8 (preprocessing skeleton) — in-notebook preprocessing is sufficient for the M2/M3/M4 comparison round.

## Artifacts

- `notebooks/01_experiment_tf.ipynb` — full notebook (load → preprocess → tokenize → model → train → evaluate).
- `ml/data/split.py` — splitter that produced the train/val/test CSVs.
- `docs/experiments/M2-bilstm-baseline.md` — this note.
