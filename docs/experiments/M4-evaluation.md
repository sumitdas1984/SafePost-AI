# EXP-004 — M4: Evaluation + Model Selection

## Objective

Pick the candidate model for M5+ deployment (FastAPI, SageMaker, ECS)
based on the M2 / M3 experiments, and document the rationale so the
decision is discoverable without re-running the notebooks.

## Decision

**DistilBERT (M3) is the model for deployment.** BiLSTM (M2) is
documented for reference but not promoted to production.

## Comparison summary

Numbers come from `docs/experiments/M2-bilstm-baseline.md` (BiLSTM)
and `docs/experiments/m3_metrics.json` + `notebooks/02_experiment_transformer.ipynb`
cell 33 (DistilBERT). Both models were trained on the same
`data/processed/{train,val,test}.csv` splits from `ml/data/split.py`.

| Metric | BiLSTM (M2) | DistilBERT (M3, 1 epoch) | Winner |
|---|---:|---:|---|
| Val accuracy | 0.8876 | **0.9110** | DistilBERT (+0.023) |
| Test accuracy | 0.8892 | **0.9190** | DistilBERT (+0.030) |
| Macro F1 (test) | not computed | 0.7510 | n/a |
| Hate-speech F1 (test) | not computed | **0.4025** | n/a |
| Training time | ~50 s (5 epochs) | ~45–60 min (1 epoch) | BiLSTM (~70× faster) |
| Model size | 346,755 params | ~66M params | BiLSTM (~190× smaller) |
| Inference CPU | fast, no tokenizer | slower, BERT tokenizer required | BiLSTM |

## Rationale

### Why DistilBERT wins for deployment
1. **+3 pp test accuracy.** 0.92 vs 0.89 on the held-out test set; the
   same data the BiLSTM scored on.
2. **No preprocessing pipeline required.** DistilBERT feeds raw tweets
   into its tokenizer. The BiLSTM notebook applies lowercase +
   punctuation stripping + stopword removal + WordNet lemmatization. That's
   four steps to maintain, test, and version. DistilBERT's win on
   accuracy is *despite* not having that pipeline, which makes the win
   robust.
3. **Standard HuggingFace packaging.** `transformers.AutoTokenizer` +
   `transformers.AutoModelForSequenceClassification` give us a model +
   tokenizer pair that drops into SageMaker / ECS without bespoke glue.
4. **1-epoch cap leaves headroom.** Even at 1 epoch DistilBERT beats the
   BiLSTM; the 5-epoch BiLSTM already overfit (best epoch = 2).
   DistilBERT's longer training runway means production retraining has
   room to grow into the 0.85 macro-F1 target.

### Why BiLSTM is not the choice
- ~3 pp lower test accuracy.
- Lower margin for production retraining (overfits past epoch 2).
- Custom preprocessing pipeline = more code to maintain.

### Known gap: Macro F1
The PRD's success metric is `Macro F1 >= 0.85`. DistilBERT hits 0.7510 on
test — short of target by 10 pp. The deficit is entirely from
`hate_speech` recall (0.3037): the model misses ~70% of hate-speech
posts. With only ~1,001 hate-speech training rows out of 17,347, the
class is starved for signal.

**Production caveats to flag in any demo or interview:**
- Accuracy numbers (0.92) overstate real-world performance on hate
  speech specifically. Macro F1 (0.75) is the honest number.
- Closing the gap needs class-weighted loss, focal loss, or more
  hate-speech data — none of which are in scope for the MVP but
  should be tracked before any real deployment.

## Trade-offs accepted

| Trade-off | Decision | Why |
|---|---|---|
| 70× slower training | Accept | Production retraining is rare; training happens in CI/CD jobs. |
| 190× larger model | Accept | Model still fits in <300 MB on disk; SageMaker endpoints handle it. |
| Macro F1 10 pp below PRD target | Accept with caveat | Above the bar for a 1-epoch, no-preprocessing baseline; document the gap. |
| Different preprocessing from M2 | Accept | BiLSTM's pipeline isn't portable; DistilBERT doesn't need it. |

## Artifacts

- **Decision source:** this note (`docs/experiments/M4-evaluation.md`).
- **DistilBERT metrics:** `docs/experiments/m3_metrics.json` (durable artifact).
- **DistilBERT notebook:** `notebooks/02_experiment_transformer.ipynb` (cells 22, 24, 26, 33).
- **BiLSTM metrics:** `docs/experiments/M2-bilstm-baseline.md` (val/test accuracy; no macro F1).
- **BiLSTM notebook:** `notebooks/01_experiment_bilstm.ipynb`.
- **Saved model + tokenizer:** `models/m3-transformer/final/` (gitignored).
- **Splits used by both:** `data/processed/{train.csv, val.csv, test.csv}` from `ml/data/split.py`.

## Next action

Promote DistilBERT to deployment:
- **#14 FastAPI** — load the saved model + tokenizer, expose `/predict`.
- **#17 Docker** — package the FastAPI app as an ECS-ready image.
- **#15 SageMaker** — real endpoint from the image.

The macro-F1 gap is a known M4-follow-up; out of scope for the 2-day plan.
