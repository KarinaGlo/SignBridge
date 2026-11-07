"""
scripts/web_dataset_to_multimodal.py — Modul 02 Langkah 10 (PDF Hal. 18):
Mengekstrak arsip .zip dari Perekam Dataset Multimodal Web ke 4 folder modalitas
(video, image, audio, text) + manifest_selfrec.csv.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def unpack_multimodal_zips(in_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    if not in_dir.exists():
        return 0
    for zf in sorted(in_dir.glob("*.zip")):
        with zipfile.ZipFile(zf, "r") as z:
            z.extractall(out_dir / zf.stem)
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Bongkar ZIP dataset multimodal dari perekam web.")
    parser.add_argument("--in", dest="in_dir", type=str, default="data/raw/web_zips")
    parser.add_argument("--out", type=str, default="data/selfrec_multimodal")
    args = parser.parse_args()

    n = unpack_multimodal_zips(Path(args.in_dir), Path(args.out))
    print(f"[web_dataset_to_multimodal] {n} arsip ZIP diekstrak ke {args.out}")


if __name__ == "__main__":
    main()

