"""
scripts/verify_preprocessing_and_loaders.py
Comprehensive Verification for Preprocessed Dataset, Zero Leakage,
and FingerspellDataset DataLoader Compatibility.
"""

import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from torch.utils.data import DataLoader
from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE
from signbridge.image.train_image import FingerspellDataset

MANIFEST_CSV = ROOT / "data" / "processed" / "bisindo_alphabet" / "manifest.csv"
AUDIT_CSV = ROOT / "data" / "processed" / "bisindo_alphabet" / "preprocessing_audit_manifest.csv"

def run_verification():
    print("=== MEMULAI VERIFIKASI PREPROCESSING & DATA LOADER ===")
    assert MANIFEST_CSV.exists(), f"Manifest tidak ditemukan: {MANIFEST_CSV}"
    assert AUDIT_CSV.exists(), f"Audit manifest tidak ditemukan: {AUDIT_CSV}"

    with open(MANIFEST_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Total baris manifest pelatihan: {len(rows)} (Diharapkan: 4.462)")
    assert len(rows) == 4462, f"Jumlah baris {len(rows)} != 4462"

    with open(AUDIT_CSV, "r", encoding="utf-8") as f:
        audit_rows = list(csv.DictReader(f))
    print(f"Total baris audit penuh: {len(audit_rows)} (Diharapkan: 4.466)")
    assert len(audit_rows) == 4466, f"Jumlah baris audit {len(audit_rows)} != 4466"

    # 1. Verifikasi File Fisik & Array
    split_paths = defaultdict(set)
    split_sources = defaultdict(set)
    split_shas = defaultdict(set)
    class_split_counts = {c: {"train": 0, "val": 0, "test": 0} for c in FINGERSPELL_26_LABELS}

    for idx, r in enumerate(rows):
        if idx % 1000 == 0:
            print(f"Memeriksa file {idx}/{len(rows)}...", flush=True)
        p = Path(r["path"])
        if not p.is_absolute():
            p = ROOT / p
        assert p.exists(), f"Berkas tidak ada di disk: {p}"
        arr = np.load(str(p))
        assert arr.shape == (224, 224, 3), f"Bentuk array salah: {arr.shape} pada {p}"
        assert arr.dtype == np.uint8, f"Tipe data array salah: {arr.dtype} pada {p}"

        sp = r["split"]
        c = r["letter"]
        lbl = int(r["label"])
        sha = r["sha256"]
        src = r["source_path"]

        assert c in FINGERSPELL_26_LABELS, f"Label huruf tidak valid: {c}"
        assert 0 <= lbl < 26, f"Label index tidak valid: {lbl}"
        assert FINGERSPELL_26_LABELS[lbl] == c, f"Inkonsistensi label {lbl} vs huruf {c}"

        split_paths[sp].add(str(p.as_posix()))
        split_sources[sp].add(src)
        split_shas[sp].add(sha)
        class_split_counts[c][sp] += 1

    print("Verifikasi 4.462 berkas .npy fisik (224x224x3 uint8): 100% SUKSES")

    # 2. Verifikasi Data Leakage (Strict Zero Leakage Check)
    splits = ["train", "val", "test"]
    for i in range(len(splits)):
        for j in range(i + 1, len(splits)):
            s1, s2 = splits[i], splits[j]
            leak_path = split_paths[s1] & split_paths[s2]
            leak_src = split_sources[s1] & split_sources[s2]
            leak_sha = split_shas[s1] & split_shas[s2]
            assert len(leak_path) == 0, f"LEAKAGE PATH antara {s1} dan {s2}: {leak_path}"
            assert len(leak_src) == 0, f"LEAKAGE SOURCE PATH antara {s1} dan {s2}: {leak_src}"
            assert len(leak_sha) == 0, f"LEAKAGE SHA-256 antara {s1} dan {s2}: {leak_sha}"

    print("Pemeriksaan Data Leakage (Zero Path/Source/SHA-256 Leakage): 100% LOLOS")

    # 3. Verifikasi FingerspellDataset DataLoader Compatibility
    print("\n--- Menguji FingerspellDataset Compatibility ---")
    train_ds = FingerspellDataset(manifest_path=MANIFEST_CSV, split="train", seed=42)
    val_ds = FingerspellDataset(manifest_path=MANIFEST_CSV, split="val", seed=43)
    test_ds = FingerspellDataset(manifest_path=MANIFEST_CSV, split="test", seed=44)

    print(f"train_ds length: {len(train_ds)} (Diharapkan: 3.123)")
    print(f"val_ds length  : {len(val_ds)} (Diharapkan: 669)")
    print(f"test_ds length : {len(test_ds)} (Diharapkan: 670)")

    assert len(train_ds) == 3123
    assert len(val_ds) == 669
    assert len(test_ds) == 670

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

    # Uji ambil 1 batch dari masing-masing loader
    imgs_tr, lbls_tr = next(iter(train_loader))
    imgs_va, lbls_va = next(iter(val_loader))
    imgs_te, lbls_te = next(iter(test_loader))

    assert imgs_tr.shape == (32, 3, 224, 224) and imgs_tr.dtype == torch.float32
    assert lbls_tr.shape == (32,) and lbls_tr.dtype == torch.int64
    assert imgs_va.shape == (32, 3, 224, 224)
    assert imgs_te.shape == (32, 3, 224, 224)

    print(f"Batch Train shape: {imgs_tr.shape}, dtype: {imgs_tr.dtype}, labels: [{lbls_tr.min().item()}..{lbls_tr.max().item()}]")
    print(f"Batch Val shape  : {imgs_va.shape}, dtype: {imgs_va.dtype}")
    print(f"Batch Test shape : {imgs_te.shape}, dtype: {imgs_te.dtype}")
    print("DataLoader PyTorch Compatibility: 100% SUKSES")

    print("\n=== SELURUH VERIFIKASI TAHAP 4 & 5 BERHASIL (PASSED) ===")

if __name__ == "__main__":
    run_verification()

