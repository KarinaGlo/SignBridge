"""
scripts/build_multimodal_manifest.py — Bangun manifest dataset multimodal M6.

Sumber data:
  1. ZIP dari menu "Perekam Dataset" di aplikasi web (setiap klip berisi 4 modalitas berpasangan:
     keypoint JSON, foto crop tangan JPG, audio WAV 16 kHz, dan kalimat teks di meta JSON).
  2. (Opsional) WL-BISINDO: hanya modalitas video/pose -> dipakai sebagai sampel "modalitas parsial"
     agar cabang video ikut belajar dari 1.600 klip publik. Citra/audio/teks ditandai hilang.

Contoh:
    python scripts/build_multimodal_manifest.py --zips data/raw/web_zips --out data/multimodal
    python scripts/build_multimodal_manifest.py --zips data/raw/web_zips --out data/multimodal \
        --include-wlbisindo data/manifest_wl_bisindo.csv
    python scripts/build_multimodal_manifest.py ... --protocol si --test-signer S03
"""

from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import GLOSS_TO_ID  # noqa: E402
from signbridge.multimodal.dataset import (  # noqa: E402
    MultimodalRecord,
    assign_splits,
    write_manifest,
)


def unpack_zips(zip_dir: Path, out_dir: Path) -> List[Path]:
    """Ekstrak setiap ZIP perekam ke out_dir/raw/<nama_zip>/ ; kembalikan daftar folder."""
    folders: List[Path] = []
    if not zip_dir.exists():
        return folders
    for zf in sorted(zip_dir.glob("*.zip")):
        dest = out_dir / "raw" / zf.stem
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zf, "r") as z:
            for name in z.namelist():
                target = (dest / name).resolve()
                if not str(target).startswith(str(dest.resolve())):
                    raise ValueError(f"Path tidak aman di dalam ZIP: {name}")
            z.extractall(dest)
        folders.append(dest)
    return folders


def records_from_selfrec(folder: Path) -> List[MultimodalRecord]:
    manifest = folder / "manifest_selfrec.csv"
    if not manifest.exists():
        return []
    out: List[MultimodalRecord] = []
    with manifest.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            category = (row.get("category") or "gloss").strip()
            gloss = (row.get("target") or "").strip().upper()
            if category != "gloss" or gloss not in GLOSS_TO_ID:
                continue  # M6 memprediksi 32 konsep gloss; huruf A–Z ditangani model ejaan jari

            def path_of(key: str) -> str:
                v = (row.get(key) or "").strip()
                return str(folder / v) if v and (folder / v).exists() else ""

            out.append(
                MultimodalRecord(
                    clip_id=f"{folder.name}:{row['clip_id']}",
                    signer=(row.get("signer") or "").strip(),
                    category=category,
                    gloss=gloss,
                    label=GLOSS_TO_ID[gloss],
                    kp_path=path_of("kp_path"),
                    image_path=path_of("handcrop_path"),
                    audio_path=path_of("audio_path"),
                    text=(row.get("text") or "").strip(),
                )
            )
    return out


def records_from_wlbisindo(manifest_csv: Path) -> List[MultimodalRecord]:
    """Baris WL-BISINDO: hanya pose (.npz). Split asli (split_sd) dipertahankan."""
    out: List[MultimodalRecord] = []
    base = manifest_csv.parent.parent  # path di manifest relatif terhadap root repo
    with manifest_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            kp = base / row["kp_path"]
            out.append(
                MultimodalRecord(
                    clip_id=row["video_id"],
                    signer=row["signer"],
                    category="gloss",
                    gloss=row["gloss"],
                    label=int(row["label"]),
                    kp_path=str(kp) if kp.exists() else "",
                    split=row.get("split_sd", "train") or "train",
                )
            )
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Bangun manifest dataset multimodal M6")
    ap.add_argument("--zips", type=str, default="data/raw/web_zips", help="Folder berisi ZIP Perekam Dataset")
    ap.add_argument("--out", type=str, default="data/multimodal", help="Folder keluaran (manifest + file)")
    ap.add_argument("--include-wlbisindo", type=str, default=None, help="Path manifest_wl_bisindo.csv (opsional)")
    ap.add_argument("--protocol", choices=["sd", "si"], default="sd")
    ap.add_argument("--test-signer", type=str, default=None)
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    folders = unpack_zips(Path(args.zips), out_dir)
    selfrec: List[MultimodalRecord] = []
    for folder in folders:
        selfrec.extend(records_from_selfrec(folder))
    assign_splits(selfrec, protocol=args.protocol, test_signer=args.test_signer)

    records = list(selfrec)
    if args.include_wlbisindo:
        records.extend(records_from_wlbisindo(Path(args.include_wlbisindo)))

    manifest_path = out_dir / "manifest_multimodal.csv"
    write_manifest(records, manifest_path)

    split_count = Counter(r.split for r in records)
    full = sum(1 for r in selfrec if r.kp_path and r.image_path and r.audio_path and r.text)
    print(f"[build_multimodal_manifest] {len(folders)} ZIP diekstrak")
    print(f"  klip perekam (gloss)      : {len(selfrec)}  (lengkap 4 modalitas: {full})")
    print(f"  baris WL-BISINDO (pose)   : {len(records) - len(selfrec)}")
    print(f"  split                     : {dict(split_count)}")
    print(f"  manifest                  : {manifest_path}")
    if len(selfrec) == 0:
        print("  PERINGATAN: belum ada klip multimodal berpasangan. Rekam data lewat menu Perekam Dataset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
