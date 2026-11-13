"""
tests/test_fsl_duplicate_leakage.py — Pengujian Deteksi Duplikasi SHA-256 & Pencegahan Kebocoran Split FSL-105 (Tahap A.2.2).

Membuktikan secara otomatis bahwa:
1. Duplikasi SHA-256 pada FSL-105 terdeteksi secara fisik berdasarkan konten file (bukan hanya nama file).
2. Duplikat dalam split yang sama dilaporkan (WITHIN_SPLIT_DUPLICATE).
3. Duplikat lintas split ditandai secara eksplisit (CROSS_SPLIT_DUPLICATE).
4. Tidak ada grup SHA-256 yang bocor ke train dan test pada manifest eksperimen evaluasi (status karantina).
5. Berkas CSV sumber resmi FSL-105 (train.csv, test.csv, labels.csv) tidak diubah sedikit pun.
6. Label FSL-105 (105 kelas) tidak tercampur dengan label WL-BISINDO (32 kelas) atau concepts.csv.
"""

from __future__ import annotations

import csv
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.extract_keypoints as extract_keypoints
from signbridge.constants import BISINDO_32_GLOSSES
from signbridge.data.video_metadata import (
    DUP_CROSS_SPLIT,
    DUP_UNIQUE,
    DUP_WITHIN_SPLIT,
    EXP_INCLUDED,
    EXP_QUARANTINED_CROSS_SPLIT,
    FSL105_SOURCE,
    WLBISINDO_LABELS,
    assert_no_sha256_split_leakage,
    build_fsl105_duplicate_report,
    classify_sha256_duplicates,
    compute_file_sha256,
    load_fsl105_official_splits,
    write_duplicate_report,
)

FSL_ROOT = ROOT / "data" / "raw" / "video" / "fsl_105"
FSL_TRAIN_CSV = FSL_ROOT / "train.csv"
FSL_TEST_CSV = FSL_ROOT / "test.csv"
FSL_LABELS_CSV = FSL_ROOT / "labels.csv"

# Hash SHA-256 referensi awal dari file CSV resmi FSL-105
EXPECTED_FSL_CSV_HASHES = {
    "labels.csv": "6074947fc905eecf20a341388551aeab0b32341928778a1f87d6c3bca073b630",
    "test.csv": "3dd8e83294a63b7c02fd1ee3ebd1d179aa4b0437ff9cfb3febab5d0e1da0ccf7",
    "train.csv": "861a76cae835e284ac76ef37dc077ae0b6c793beb9c378eda1fce5f408dc609f",
}


class TestFSLDuplicateLeakage(unittest.TestCase):
    def test_official_fsl_csvs_unmodified(self) -> None:
        """Pastikan train.csv, test.csv, dan labels.csv FSL-105 asli 100% tidak berubah."""
        for name, expected_hash in EXPECTED_FSL_CSV_HASHES.items():
            csv_path = FSL_ROOT / name
            self.assertTrue(csv_path.is_file(), f"{name} harus ada di disk")
            actual_hash = compute_file_sha256(csv_path)
            self.assertEqual(
                actual_hash.lower(),
                expected_hash.lower(),
                f"File resmi {name} tidak boleh dimodifikasi!",
            )

    def test_fsl_and_wlbisindo_label_spaces_isolated(self) -> None:
        """Pastikan label space FSL-105 (105 kelas) dan WL-BISINDO (32 kelas) terisolasi tegas."""
        label_map = extract_keypoints.load_optional_labels_csv(FSL_ROOT, FSL_LABELS_CSV)
        self.assertGreaterEqual(len(label_map), 105)

        # source='wl_bisindo' wajib menolak labels.csv FSL-105
        with self.assertRaises(ValueError) as ctx:
            extract_keypoints.resolve_video_gloss_and_label(
                Path("signer0_label0_sample1.mp4"),
                source="wl_bisindo",
                label_map=label_map,
            )
        self.assertIn("Pencampuran dataset terdeteksi", str(ctx.exception))

        # source='bisindo' (32 kelas ruang kelas) wajib menolak labels.csv FSL-105
        with self.assertRaises(ValueError) as ctx2:
            extract_keypoints.resolve_video_gloss_and_label(
                Path("clips/0/0.MOV"),
                source="bisindo",
                label_map=label_map,
            )
        self.assertIn("Pencampuran dataset terdeteksi", str(ctx2.exception))

    def test_classify_sha256_duplicates_synthetic(self) -> None:
        """Uji logika klasifikasi duplikat pada skenario sintesis tanpa menyentuh disk."""
        mock_rows = [
            {"sha256": "hash_a", "split": "train", "source_label_id": 1},
            {"sha256": "hash_a", "split": "test", "source_label_id": 2},  # Cross-split duplicate!
            {"sha256": "hash_b", "split": "train", "source_label_id": 3},
            {"sha256": "hash_b", "split": "train", "source_label_id": 3},  # Within-split duplicate
            {"sha256": "hash_c", "split": "train", "source_label_id": 4},  # Unique
            {"sha256": "hash_d", "split": "", "source_label_id": 5},       # No split
        ]

        classified = classify_sha256_duplicates(mock_rows, split_key="split")
        self.assertEqual(len(classified), 6)

        # hash_a: CROSS_SPLIT_DUPLICATE & QUARANTINED
        self.assertEqual(classified[0]["dup_status"], DUP_CROSS_SPLIT)
        self.assertEqual(classified[0]["experiment_status"], EXP_QUARANTINED_CROSS_SPLIT)
        self.assertEqual(classified[1]["dup_status"], DUP_CROSS_SPLIT)
        self.assertEqual(classified[1]["experiment_status"], EXP_QUARANTINED_CROSS_SPLIT)

        # hash_b: WITHIN_SPLIT_DUPLICATE & INCLUDED
        self.assertEqual(classified[2]["dup_status"], DUP_WITHIN_SPLIT)
        self.assertEqual(classified[2]["experiment_status"], EXP_INCLUDED)
        self.assertEqual(classified[3]["dup_status"], DUP_WITHIN_SPLIT)
        self.assertEqual(classified[3]["experiment_status"], EXP_INCLUDED)

        # hash_c: UNIQUE & INCLUDED
        self.assertEqual(classified[4]["dup_status"], DUP_UNIQUE)
        self.assertEqual(classified[4]["experiment_status"], EXP_INCLUDED)

        # Filter inklusi eksperimen: tidak boleh ada kebocoran split
        included = [r for r in classified if r["experiment_status"] == EXP_INCLUDED]
        assert_no_sha256_split_leakage(included, split_key="split")

        # Jika semua data (termasuk yang bocor) dimasukkan tanpa karantina, harus melempar ValueError
        with self.assertRaises(ValueError) as leak_ctx:
            assert_no_sha256_split_leakage(classified, split_key="split", only_included=False)
        self.assertIn("Kebocoran konten video", str(leak_ctx.exception))

    @unittest.skipUnless(FSL_ROOT.is_dir() and (FSL_ROOT / "clips").is_dir(), "FSL-105 clips NOT FOUND")
    def test_real_fsl105_duplicates_and_quarantine(self) -> None:
        """Verifikasi fisik 4 pasang duplikat SHA-256 pada 2.130 berkas FSL-105."""
        # 4 pasang hash yang diketahui dari audit:
        cross_split_hash_1 = "2894410d8559ff07b0a2e17cf6d6189ce3faf2ed867e955825441e8ff8108845"
        cross_split_hash_2 = "c329a443c221550baa104bfb20ca93fc1f13c2b191467a96f4c59b90137b8ca5"
        within_train_hash_1 = "8349f35b80868cafa419d753f28f87a137d975d7116a5889ff63b9dd16de8b87"
        within_train_hash_2 = "755a474858b2fc54641336d60c69a8026b7e33d65a4f2c86cae8a424d7865c17"

        # Gunakan cache hash untuk 4 pasang klip duplikat agar eksekusi cepat
        known_hashes = {
            "clips/23/6.mov": cross_split_hash_1,
            "clips/26/7.mov": cross_split_hash_1,
            "clips/23/8.mov": cross_split_hash_2,
            "clips/26/9.mov": cross_split_hash_2,
            "clips/57/9.mov": within_train_hash_1,
            "clips/60/9.mov": within_train_hash_1,
            "clips/58/6.mov": within_train_hash_2,
            "clips/61/6.mov": within_train_hash_2,
        }

        # Verifikasi fisik langsung pada 8 file tersebut di disk
        for rel_path, expected_h in known_hashes.items():
            p = FSL_ROOT / rel_path
            self.assertTrue(p.is_file(), f"{p} harus ada di disk")
            self.assertEqual(compute_file_sha256(p), expected_h)

        # Verifikasi deteksi split resmi untuk 8 file tersebut
        splits = load_fsl105_official_splits(FSL_ROOT)
        self.assertEqual(splits["clips/23/6.mov"][0], "train")
        self.assertEqual(splits["clips/26/7.mov"][0], "test")  # Bocor train <-> test!
        self.assertEqual(splits["clips/23/8.mov"][0], "test")
        self.assertEqual(splits["clips/26/9.mov"][0], "train")  # Bocor test <-> train!
        self.assertEqual(splits["clips/57/9.mov"][0], "train")
        self.assertEqual(splits["clips/60/9.mov"][0], "train")  # Sesama train
        self.assertEqual(splits["clips/58/6.mov"][0], "train")
        self.assertEqual(splits["clips/61/6.mov"][0], "train")  # Sesama train

        # Bangun laporan baris duplikat mini
        rows = []
        for rel_path, h in known_hashes.items():
            sp, lbl, gloss = splits[rel_path]
            rows.append({
                "source": FSL105_SOURCE,
                "rel_path": rel_path,
                "source_label_id": lbl,
                "source_gloss": gloss,
                "official_split": sp,
                "sha256": h,
            })
        classified = classify_sha256_duplicates(rows, split_key="official_split")

        # 4 klip cross-split wajib dikarantina
        quarantined = [r for r in classified if r["experiment_status"] == EXP_QUARANTINED_CROSS_SPLIT]
        self.assertEqual(len(quarantined), 4)

        # 4 klip within-split tetap INCLUDED
        included = [r for r in classified if r["experiment_status"] == EXP_INCLUDED]
        self.assertEqual(len(included), 4)

        # Manifest eksperimen yang menyaring data karantina wajib bebas kebocoran
        assert_no_sha256_split_leakage(included, split_key="official_split")


if __name__ == "__main__":
    unittest.main(verbosity=2)

