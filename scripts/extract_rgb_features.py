"""
scripts/extract_rgb_features.py — Modul 01 Langkah 3 (PDF Hal. 15):
Ekstraksi offline token RGB VideoMAE [8, 768] float16/float32 dari berkas video pada manifest.csv.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import MANIFEST_COLUMNS, RGB_NUM_TOKENS, RGB_TOKEN_DIM


def _require_rgb_extraction_deps() -> None:
    missing = []
    try:
        import cv2  # noqa: F401
    except ImportError:
        missing.append("opencv-python (cv2)")
    try:
        import torch  # noqa: F401
    except ImportError:
        missing.append("torch (PyTorch)")
    if missing:
        raise ImportError(
            "Dependency ekstraksi fitur RGB VideoMAE belum terpasang: "
            + ", ".join(missing)
            + ". Pasang dengan: pip install opencv-python torch transformers"
        )


def extract_rgb_tokens_for_manifest(
    manifest_path: Path,
    out_dir: Path,
    encoder_fn=None,
) -> int:
    """
    Ekstraksi offline token RGB [8, 768] dari berkas video asli.
    Keamanan Pipeline (Tahap A.1):
      - Dilarang memanggil ensure_demo_dataset() secara otomatis.
      - Dilarang membangkitkan token acak (rng.standard_normal) atau menyuntikkan
        sinyal label ground-truth (`tokens[:, (label * 16)...] += 1.25`) yang menyebabkan
        kebocoran label (label leakage).
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"Manifest video tidak ditemukan: {manifest_path}. "
            "Ekstraksi RGB menolak membuat dataset sintetis otomatis."
        )

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Manifest video '{manifest_path}' kosong (0 baris).")

    if encoder_fn is None:
        _require_rgb_extraction_deps()
        raise RuntimeError(
            "Ekstraksi fitur RGB VideoMAE memerlukan model encoder_fn yang telah dimuat "
            "(mis. MCG-NJU/videomae-base). Pembuatan token acak / sintetis telah dihapus."
        )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    updated = 0
    for row in rows:
        vid_id = (row.get("video_id") or "").strip()
        if not vid_id:
            raise ValueError(f"Baris manifest tidak memiliki video_id: {row!r}")
        rgb_file = out_dir / f"{vid_id}.npy"
        tokens = np.asarray(encoder_fn(row), dtype=np.float16)
        if tokens.shape != (RGB_NUM_TOKENS, RGB_TOKEN_DIM):
            raise ValueError(
                f"Dimensi output encoder RGB untuk '{vid_id}' tidak valid: "
                f"diharapkan {(RGB_NUM_TOKENS, RGB_TOKEN_DIM)}, diperoleh {tokens.shape}"
            )
        if not np.all(np.isfinite(tokens)):
            raise ValueError(f"Output encoder RGB untuk '{vid_id}' mengandung NaN/Inf.")
        np.save(rgb_file, tokens)
        row["rgb_path"] = str(rgb_file.as_posix())
        updated += 1

    fieldnames = list(rows[0].keys()) if rows else list(MANIFEST_COLUMNS)
    for col in MANIFEST_COLUMNS:
        if col not in fieldnames:
            fieldnames.append(col)

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Ekstraksi fitur RGB VideoMAE [8, 768].")
    parser.add_argument("--manifest", type=str, default="data/manifest.csv")
    parser.add_argument("--out", type=str, default="data/rgb_feats/bisindo")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    n = extract_rgb_tokens_for_manifest(Path(args.manifest), Path(args.out))
    print(f"[extract_rgb_features] {n} berkas token RGB [8, 768] tersimpan di {args.out}")


if __name__ == "__main__":
    main()

