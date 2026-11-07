"""
scripts/merge_manifests.py — Gabungkan beberapa berkas manifest CSV menjadi data/manifest.csv.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import MANIFEST_COLUMNS
from signbridge.data.dataset import ensure_demo_dataset


def merge_manifests(inputs: list[Path], out_path: Path) -> int:
    rows = []
    seen_ids = set()

    for p in inputs:
        if not p.exists():
            continue
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vid = row.get("video_id", "")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    rows.append({col: row.get(col, "") for col in MANIFEST_COLUMNS})

    if not rows:
        ensure_demo_dataset(manifest_path=out_path)
        with out_path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in csv.DictReader(f))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(MANIFEST_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gabungkan manifest CSV.")
    parser.add_argument("--inputs", nargs="+", default=["data/manifest_bisindo.csv", "data/manifest_selfrec.csv"])
    parser.add_argument("--out", type=str, default="data/manifest.csv")
    args = parser.parse_args()

    total = merge_manifests([Path(x) for x in args.inputs], Path(args.out))
    print(f"[merge_manifests] Total {total} baris ditulis ke {args.out}")


if __name__ == "__main__":
    main()

