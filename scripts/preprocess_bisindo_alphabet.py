"""
scripts/preprocess_bisindo_alphabet.py
Full Preprocessing and Stratified Data Splitting (70% Train / 15% Val / 15% Test)
for Mendeley BISINDO Alphabet Dataset (4,466 images -> 4,462 valid, 4 excluded cross-class duplicates).
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE
from signbridge.image.crop import _bilinear_resize_rgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bisindo_preprocessor")

RAW_DIR = ROOT / "data" / "raw" / "image" / "bisindo_alphabet"
PROCESSED_DIR = ROOT / "data" / "processed" / "bisindo_alphabet"
SEED = 42

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def run_preprocessing() -> Dict[str, Any]:
    logger.info("=== TAHAP 4 & 5: Preprocessing & Stratified Splitting ===")
    logger.info("Sumber mentah   : %s", RAW_DIR)
    logger.info("Tujuan processed: %s", PROCESSED_DIR)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Pindai seluruh 26 kelas
    class_dirs = sorted([d for d in RAW_DIR.iterdir() if d.is_dir() and d.name in FINGERSPELL_26_LABELS])
    if len(class_dirs) != 26:
        raise ValueError(f"Ditemukan {len(class_dirs)} kelas, diharapkan 26 kelas A-Z di {RAW_DIR}")

    raw_files_by_class: Dict[str, List[Path]] = {}
    file_to_sha: Dict[Path, str] = {}
    sha_to_files: Dict[str, List[Tuple[str, Path]]] = defaultdict(list)
    total_raw = 0

    for cdir in class_dirs:
        letter = cdir.name
        files = sorted([f for f in cdir.iterdir() if f.is_file() and not f.name.startswith("._")])
        raw_files_by_class[letter] = files
        total_raw += len(files)
        for f in files:
            sha = compute_sha256(f)
            file_to_sha[f] = sha
            sha_to_files[sha].append((letter, f))

    logger.info("Total gambar mentah dipindai: %d gambar dari 26 kelas", total_raw)

    # 2. Identifikasi duplikat lintas kelas
    cross_class_duplicate_shas: Set[str] = set()
    excluded_files: Dict[Path, str] = {}

    for sha, occurrences in sha_to_files.items():
        unique_classes = set(occ[0] for occ in occurrences)
        if len(unique_classes) > 1:
            cross_class_duplicate_shas.add(sha)
            cls_str = " vs ".join(sorted(unique_classes))
            for letter, path in occurrences:
                reason = f"CROSS_CLASS_DUPLICATE ({cls_str}): sha256={sha[:16]}"
                excluded_files[path] = reason
                logger.warning("Pengecualian Berkas Ambigu: %s -> %s", path.name, reason)

    logger.info(
        "Ditemukan %d grup SHA-256 duplikat lintas-kelas (%d berkas dikecualikan)",
        len(cross_class_duplicate_shas),
        len(excluded_files)
    )

    # 3. Kumpulkan berkas valid per kelas
    valid_records: List[Dict[str, Any]] = []
    all_audit_records: List[Dict[str, Any]] = []

    for letter in FINGERSPELL_26_LABELS:
        files = raw_files_by_class[letter]
        for f in files:
            sha = file_to_sha[f]
            if f in excluded_files:
                all_audit_records.append({
                    "original_path": str(f.as_posix()),
                    "processed_path": "",
                    "class_name": letter,
                    "letter": letter,
                    "label": FINGERSPELL_26_LABELS.index(letter),
                    "original_sha256": sha,
                    "sha256": sha,
                    "split": "excluded",
                    "crop_status": "EXCLUDED",
                    "preprocessing_status": "EXCLUDED",
                    "exclusion_reason": excluded_files[f]
                })
            else:
                valid_records.append({
                    "raw_path": f,
                    "letter": letter,
                    "label": FINGERSPELL_26_LABELS.index(letter),
                    "sha256": sha
                })

    logger.info("Jumlah berkas valid untuk training/evaluasi: %d berkas", len(valid_records))

    # 4. Stratified Split 70% Train, 15% Val, 15% Test (Seed 42)
    # Langkah 4a: Pisahkan 70% train dan 30% temp (val+test)
    labels = [r["label"] for r in valid_records]
    train_idx, temp_idx = train_test_split(
        range(len(valid_records)),
        test_size=0.30,
        random_state=SEED,
        stratify=labels
    )

    # Langkah 4b: Pisahkan 30% temp menjadi 15% val dan 15% test (rasio 50:50)
    temp_labels = [labels[i] for i in temp_idx]
    val_sub_idx, test_sub_idx = train_test_split(
        range(len(temp_idx)),
        test_size=0.50,
        random_state=SEED,
        stratify=temp_labels
    )

    val_idx = [temp_idx[i] for i in val_sub_idx]
    test_idx = [temp_idx[i] for i in test_sub_idx]

    split_map: Dict[int, str] = {}
    for i in train_idx:
        split_map[i] = "train"
    for i in val_idx:
        split_map[i] = "val"
    for i in test_idx:
        split_map[i] = "test"

    logger.info(
        "Hasil Pembagian Stratified: Train=%d (%.1f%%), Val=%d (%.1f%%), Test=%d (%.1f%%)",
        len(train_idx), len(train_idx) / len(valid_records) * 100,
        len(val_idx), len(val_idx) / len(valid_records) * 100,
        len(test_idx), len(test_idx) / len(valid_records) * 100,
    )

    # 5. Preprocessing fisik dan penyimpanan
    processed_manifest_rows: List[Dict[str, Any]] = []
    class_sample_counters: Dict[str, int] = defaultdict(int)

    for i, rec in enumerate(valid_records):
        raw_p: Path = rec["raw_path"]
        letter: str = rec["letter"]
        lbl: int = rec["label"]
        sha: str = rec["sha256"]
        split: str = split_map[i]

        out_class_dir = PROCESSED_DIR / letter
        out_class_dir.mkdir(parents=True, exist_ok=True)

        sample_num = class_sample_counters[letter]
        class_sample_counters[letter] += 1

        # Nama file output
        npy_name = f"{letter}_{sample_num:04d}.npy"
        jpg_name = f"{letter}_{sample_num:04d}.jpg"
        npy_path = out_class_dir / npy_name
        jpg_path = out_class_dir / jpg_name

        # Baca dan crop / resize
        with Image.open(raw_p) as im:
            rgb_im = im.convert("RGB")
            arr = np.asarray(rgb_im, dtype=np.uint8)

        H, W, _ = arr.shape
        side = min(H, W)
        x0 = (W - side) // 2
        y0 = (H - side) // 2
        patch = arr[y0 : y0 + side, x0 : x0 + side]

        if patch.shape[0] != IMAGE_SIZE or patch.shape[1] != IMAGE_SIZE:
            resized = _bilinear_resize_rgb(patch, out_h=IMAGE_SIZE, out_w=IMAGE_SIZE)
        else:
            resized = patch.copy()

        # Simpan .npy uint8 [224, 224, 3] untuk kecepatan I/O DataLoader
        np.save(npy_path, resized)

        # Simpan .jpg untuk visualisasi
        Image.fromarray(resized).save(jpg_path, quality=95)

        row_dict = {
            "path": str(npy_path.as_posix()),
            "image_path": str(jpg_path.as_posix()),
            "processed_path": str(npy_path.as_posix()),
            "source_path": str(raw_p.as_posix()),
            "original_path": str(raw_p.as_posix()),
            "letter": letter,
            "class_name": letter,
            "label": lbl,
            "split": split,
            "sha256": sha,
            "original_sha256": sha,
            "crop_status": "SUCCESS_PRECENTERED_224",
            "preprocessing_status": "SUCCESS",
            "hand_found": "1",
            "exclusion_reason": ""
        }
        processed_manifest_rows.append(row_dict)
        all_audit_records.append(row_dict)

    # 6. Tulis Manifest Pelatihan: data/processed/bisindo_alphabet/manifest.csv
    manifest_csv = PROCESSED_DIR / "manifest.csv"
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "path", "image_path", "processed_path", "source_path", "original_path",
            "letter", "class_name", "label", "split",
            "sha256", "original_sha256", "crop_status", "preprocessing_status",
            "hand_found", "exclusion_reason"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(processed_manifest_rows)

    logger.info("Manifest pelatihan ditulis ke: %s (%d baris)", manifest_csv, len(processed_manifest_rows))

    # 7. Tulis Manifest Audit Penuh: data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv
    audit_csv = PROCESSED_DIR / "preprocessing_audit_manifest.csv"
    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_audit_records)

    logger.info("Manifest audit penuh ditulis ke: %s (%d baris)", audit_csv, len(all_audit_records))

    # 8. Hitung statistik distribusi per kelas per split
    class_split_stats: Dict[str, Dict[str, int]] = {c: {"train": 0, "val": 0, "test": 0, "total": 0} for c in FINGERSPELL_26_LABELS}
    for r in processed_manifest_rows:
        c = r["letter"]
        sp = r["split"]
        class_split_stats[c][sp] += 1
        class_split_stats[c]["total"] += 1

    summary_json = {
        "total_raw": total_raw,
        "total_excluded": len(excluded_files),
        "total_processed": len(processed_manifest_rows),
        "train_count": len(train_idx),
        "val_count": len(val_idx),
        "test_count": len(test_idx),
        "train_pct": round(len(train_idx) / len(valid_records) * 100, 2),
        "val_pct": round(len(val_idx) / len(valid_records) * 100, 2),
        "test_pct": round(len(test_idx) / len(valid_records) * 100, 2),
        "seed": SEED,
        "excluded_files_detail": [
            {"path": str(p.as_posix()), "reason": r} for p, r in excluded_files.items()
        ],
        "class_split_stats": class_split_stats
    }

    summary_file = PROCESSED_DIR / "preprocessing_summary.json"
    with summary_file.open("w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    logger.info("Ringkasan preprocessing disimpan ke: %s", summary_file)
    return summary_json

if __name__ == "__main__":
    run_preprocessing()

