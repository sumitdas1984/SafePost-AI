"""Download the SafePost AI raw dataset.

Pulls the labeled hate-speech CSV from a pinned source URL into
``data/raw/hatespeech-dataset.csv`` and prints its SHA-256 and row
count so the download is verifiable.

Idempotent: if the file already exists, the script skips the download
and only re-reports the hash and row count. Use ``--force`` to override.

Run from the repo root:

    uv run python scripts/fetch_dataset.py
    uv run python scripts/fetch_dataset.py --force
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

import httpx

DEFAULT_URL = (
    "https://media.geeksforgeeks.org/wp-content/uploads/"
    "20250321123144355200/Dataset---Hate-Speech-Detection-using-Deep-Learning.csv"
)
DEFAULT_OUT = Path("data/raw/hatespeech-dataset.csv")
CHUNK_SIZE = 1 << 20  # 1 MiB


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(path: Path) -> int:
    """Return the number of data rows, excluding the header line.

    Counts logical CSV rows via the :mod:`csv` module so that rows
    containing embedded newlines inside quoted fields are not
    double-counted.
    """
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return sum(1 for _ in reader)


def fetch(url: str, out: Path, *, force: bool = False) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not force:
        print(f"[skip] {out} already exists; not re-downloading (use --force to override)")
    else:
        print(f"[get ] {url}")
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as r:
            r.raise_for_status()
            with out.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        print(f"[ok  ] wrote {out} ({out.stat().st_size:,} bytes)")

    digest = sha256_of(out)
    rows = count_rows(out)
    print(f"[hash] sha256={digest}")
    print(f"[rows] {rows:,} data rows (excluding header)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Source URL of the CSV")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Destination path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the destination file already exists",
    )
    args = parser.parse_args(argv)
    fetch(args.url, args.out, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
