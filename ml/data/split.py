"""Train/validation/test split for the SafePost AI dataset.

Stratified 70 / 15 / 15 split with a pinned seed, deterministic and
idempotent. Output lands in ``data/processed/`` as three CSV files:

- ``train.csv`` (~17,338 rows, ~70%)
- ``val.csv``   ( ~3,717 rows, ~15%)
- ``test.csv``  ( ~3,717 rows, ~15%)

Run as a script:

    uv run python ml/data/split.py

Import from a notebook:

    from ml.data.split import split_dataset
    splits = split_dataset()
    splits["train"], splits["val"], splits["test"]
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# Configuration constants (frozen; do not change without re-issuing splits).
RANDOM_SEED: int = 42
TEST_SIZE: float = 0.15  # 15% goes to test
VAL_SIZE: float = 0.15   # 15% goes to validation (taken from the 85% train pool)

RAW_DATA_PATH: Path = Path("data/raw/hate_speech.csv")
OUTPUT_DIR: Path = Path("data/processed")


def _load_raw(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw labeled CSV.

    Accepts either the user-facing ``hate_speech.csv`` filename or the
    fetch-script default ``hatespeech-dataset.csv`` so the splitter works
    regardless of which one is in the raw folder.
    """
    candidates = [path, path.with_name("hatespeech-dataset.csv")]
    for candidate in candidates:
        if candidate.exists():
            df = pd.read_csv(candidate)
            break
    else:
        raise FileNotFoundError(
            f"Raw dataset not found at {RAW_DATA_PATH} "
            f"(or data/raw/hatespeech-dataset.csv). "
            "Run scripts/fetch_dataset.py first."
        )

    if "class" not in df.columns or "tweet" not in df.columns:
        raise ValueError(
            f"Expected 'class' and 'tweet' columns, got {list(df.columns)}"
        )
    return df


def split_dataset(
    raw_path: Path = RAW_DATA_PATH,
    output_dir: Path = OUTPUT_DIR,
    *,
    seed: int = RANDOM_SEED,
) -> dict[str, pd.DataFrame]:
    """Stratified 70 / 15 / 15 train/val/test split.

    Two-step split: first carve off the test set (15%), then split the
    remaining 85% into train (70%) and val (15%) using
    ``val_size / (1 - test_size) = 0.15 / 0.85 ~ 0.1765`` as the val
    fraction of the train pool.

    Returns a dict of DataFrames keyed by ``"train"``, ``"val"``,
    ``"test"``. The same three CSVs are written to ``output_dir``.
    """
    df = _load_raw(raw_path)

    # Step 1: train_pool (85%) / test (15%)
    train_pool, test = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=seed,
        stratify=df["class"],
    )

    # Step 2: train (~70%) / val (~15%) from the 85% pool
    val_fraction_of_pool = VAL_SIZE / (1 - TEST_SIZE)
    train, val = train_test_split(
        train_pool,
        test_size=val_fraction_of_pool,
        random_state=seed,
        stratify=train_pool["class"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    splits: dict[str, pd.DataFrame] = {"train": train, "val": val, "test": test}
    for name, split_df in splits.items():
        split_df.to_csv(output_dir / f"{name}.csv", index=False)

    return splits


def main() -> None:
    splits = split_dataset()
    total = sum(len(df) for df in splits.values())
    print(f"Wrote {len(splits)} splits to {OUTPUT_DIR} ({total:,} rows total)")
    for name, df in splits.items():
        cls = df["class"].value_counts(normalize=True).round(4).to_dict()
        print(f"  {name:<5}  {len(df):>6,} rows  class_pct={cls}")


if __name__ == "__main__":
    main()
