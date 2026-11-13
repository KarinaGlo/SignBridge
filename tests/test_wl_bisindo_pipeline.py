"""
tests/test_wl_bisindo_pipeline.py — Tahap A.2.2: parser signer/label WL-BISINDO, label space terpisah,
dan pembentukan split SD/SI dengan validasi cakupan kelas.

Tidak mengekstrak archive.zip (hanya membaca central directory ZIP), tidak menjalankan ekstraksi keypoint
maupun training.
"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.extract_keypoints as extract_keypoints  # noqa: E402
from signbridge.constants import BISINDO_32_GLOSSES, NUM_COORDS, NUM_KEYPOINTS  # noqa: E402
from signbridge.data.dataset import SignDataset  # noqa: E402
from signbridge.data.video_metadata import (  # noqa: E402
    UNANNOTATED_SIGNER,
    WLBISINDO_CONCEPT_OVERLAP,
    WLBISINDO_LABELS,
    WLBISINDO_LICENSE,
    assign_wlbisindo_sd_splits,
    build_wlbisindo_records,
    build_wlbisindo_si_split,
    extract_signer_id_from_text,
    list_wlbisindo_zip_members,
    parse_wlbisindo_filename,
    signer_class_coverage,
    validate_split_class_coverage,
)

WL_ZIP = ROOT / "data" / "raw" / "video" / "wl_bisindo" / "archive.zip"
CONCEPTS_CSV = ROOT / "data" / "bridge" / "concepts.csv"


def _synthetic_wlbisindo_names() -> list:
    """Daftar NAMA berkas (bukan data video) yang meniru struktur sumber WL-BISINDO yang diaudit."""
    names = []
    for label in range(32):
        if label <= 11:
            per_signer = {0: 10, 1: 10, 2: 10, 3: 10, 4: 10}
        else:
            per_signer = {1: 15, 2: 15, 3: 10, 4: 10}
        for s, n in per_signer.items():
            for k in range(1, n + 1):
                names.append(f"signer{s}_label{label}_sample{k}.mp4")
    return names


class TestSignerRegex(unittest.TestCase):
    def test_wlbisindo_signers_parsed(self) -> None:
        cases = {
            "signer0_label0_sample1.mp4": "SIGNER0",
            "signer1_label12_sample15.mp4": "SIGNER1",
            "signer2_label31_sample10.mp4": "SIGNER2",
            "signer3_label5_sample1.mp4": "SIGNER3",
            "signer4_label20_sample10.mp4": "SIGNER4",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(extract_keypoints.extract_signer_id(Path(name)), expected)
                self.assertEqual(extract_signer_id_from_text(Path(name).stem), expected)

    def test_legacy_short_signer_formats(self) -> None:
        self.assertEqual(extract_keypoints.extract_signer_id(Path("S01_video.mp4")), "S01")
        self.assertEqual(extract_keypoints.extract_signer_id(Path("s1_video.mp4")), "S1")
        self.assertEqual(extract_keypoints.extract_signer_id(Path("S01_HALO_01.mp4")), "S01")
        self.assertEqual(extract_keypoints.extract_signer_id(Path("signer-02_HALO.mp4")), "SIGNER_02")

    def test_old_regex_bug_reproduced(self) -> None:
        """Dokumentasi bug: regex lama dengan \\b memang gagal pada nama WL-BISINDO."""
        import re

        old = re.search(r"\b(s\d{1,3}|signer[_-]?\d{1,3})\b", "signer0_label0_sample1", flags=re.IGNORECASE)
        self.assertIsNone(old)

    def test_unannotated_is_not_invented(self) -> None:
        for p in ("clips/0/0.MOV", "clips/23/6.MOV", "HALO/video_sample1.mp4", "class12/label3.mp4", "random.mp4"):
            with self.subTest(p=p):
                self.assertEqual(extract_keypoints.extract_signer_id(Path(p)), UNANNOTATED_SIGNER)
        self.assertEqual(extract_signer_id_from_text("", "sample1", "label0"), UNANNOTATED_SIGNER)


class TestWLBisindoLabels(unittest.TestCase):
    def test_label_space_is_official_and_separate(self) -> None:
        self.assertEqual(len(WLBISINDO_LABELS), 32)
        self.assertEqual(WLBISINDO_LABELS[0], "AIR")
        self.assertEqual(WLBISINDO_LABELS[10], "TERIMA_KASIH")
        self.assertEqual(WLBISINDO_LABELS[31], "MALAM")
        self.assertEqual(WLBISINDO_LICENSE, "CC BY-NC 4.0")
        overlap = set(WLBISINDO_LABELS.values()) & set(BISINDO_32_GLOSSES)
        self.assertEqual(overlap, set(WLBISINDO_CONCEPT_OVERLAP))
        self.assertEqual(len(overlap), 10)
        self.assertNotEqual(list(WLBISINDO_LABELS.values()), list(BISINDO_32_GLOSSES))

    def test_parse_all_labels_and_signers(self) -> None:
        for label in range(32):
            for s in range(5):
                rec = parse_wlbisindo_filename(f"signer{s}_label{label}_sample3.mp4")
                self.assertEqual(rec.source_label_id, label)
                self.assertEqual(rec.source_gloss, WLBISINDO_LABELS[label])
                self.assertEqual(rec.signer_id, f"SIGNER{s}")
                self.assertEqual(rec.sample_id, 3)
                self.assertEqual(rec.source, "wl_bisindo")

    def test_resolve_video_gloss_and_label_wl_source(self) -> None:
        self.assertEqual(
            extract_keypoints.resolve_video_gloss_and_label(Path("x/signer1_label10_sample5.mp4"), source="wl_bisindo"),
            ("TERIMA_KASIH", 10),
        )
        self.assertEqual(
            extract_keypoints.resolve_video_gloss_and_label(Path("signer4_label31_sample10.MP4"), source="wl_bisindo"),
            ("MALAM", 31),
        )
        with self.assertRaises(ValueError):
            extract_keypoints.resolve_video_gloss_and_label(
                Path("signer0_label0_sample1.mp4"), source="wl_bisindo", label_map={"0": ("GOOD MORNING", 0)}
            )
        # source='bisindo' (folder-gloss concepts.csv) tetap menolak berkas flat WL-BISINDO
        with self.assertRaises(ValueError):
            extract_keypoints.resolve_video_gloss_and_label(
                Path("wl_bisindo/signer0_label0_sample1.mp4"), source="bisindo", label_map={}
            )

    def test_out_of_range_and_invalid_names_rejected(self) -> None:
        for bad in (
            "signer0_label-1_sample1.mp4",
            "signer0_label32_sample1.mp4",
            "signer0_label100_sample1.mp4",
            "signer0_sample1.mp4",
            "label0_signer0_sample1.mp4",
            "signer0_label0_sample1.txt",
            "signerX_label0_sample1.mp4",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_wlbisindo_filename(bad)
        with self.assertRaises(ValueError) as ctx:
            parse_wlbisindo_filename("signer0_label32_sample1.mp4")
        self.assertIn("0..31", str(ctx.exception))

    def test_duplicate_names_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_wlbisindo_records(["signer0_label0_sample1.mp4", "SIGNER0_label0_sample1.mp4"])

    def test_concepts_csv_untouched_by_label_space(self) -> None:
        with CONCEPTS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            glosses = [r["bisindo_gloss"] for r in csv.DictReader(f)]
        # 32 baris pertama = kosakata yang benar-benar dikenali model; sisanya konsep roadmap (model_supported=0).
        self.assertEqual(glosses[:32], list(BISINDO_32_GLOSSES))
        self.assertEqual(len(glosses), len(set(glosses)))


class TestWLBisindoSplits(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = build_wlbisindo_records(_synthetic_wlbisindo_names())

    def test_signer_coverage(self) -> None:
        cov = signer_class_coverage(self.records)
        self.assertEqual(cov["SIGNER0"], list(range(12)))
        self.assertNotEqual(len(cov["SIGNER0"]), 32)
        for s in ("SIGNER1", "SIGNER2", "SIGNER3", "SIGNER4"):
            self.assertEqual(cov[s], list(range(32)))

    def test_si_signer0_only_test_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_wlbisindo_si_split(self.records, test_signers=["SIGNER0"])
        _, report = build_wlbisindo_si_split(self.records, test_signers=["SIGNER0"], require_full_coverage=False)
        self.assertFalse(report["si_valid"])
        self.assertEqual(report["coverage"]["test"]["missing_labels"], list(range(12, 32)))

    def test_si_valid_split(self) -> None:
        assign, report = build_wlbisindo_si_split(self.records, test_signers=["SIGNER3"], val_signers=["SIGNER4"])
        self.assertTrue(report["si_valid"])
        self.assertEqual(report["train_signers"], ["SIGNER0", "SIGNER1", "SIGNER2"])
        # Tidak ada signer di lebih dari satu split
        signer_splits = {}
        for rec in self.records:
            signer_splits.setdefault(rec.signer_id, set()).add(assign[rec.filename])
        self.assertTrue(all(len(v) == 1 for v in signer_splits.values()))
        with self.assertRaises(ValueError):
            build_wlbisindo_si_split(self.records, test_signers=["SIGNER3"], val_signers=["SIGNER3"])
        with self.assertRaises(ValueError):
            build_wlbisindo_si_split(self.records, test_signers=["SIGNER9"])

    def test_sd_split_deterministic_and_complete(self) -> None:
        a1 = assign_wlbisindo_sd_splits(self.records)
        a2 = assign_wlbisindo_sd_splits(list(reversed(self.records)))
        self.assertEqual(a1, a2)
        self.assertEqual(len(a1), 1600)
        split_labels = {"train": set(), "val": set(), "test": set()}
        split_signers = {"train": set(), "val": set(), "test": set()}
        for rec in self.records:
            split_labels[a1[rec.filename]].add(rec.source_label_id)
            split_signers[a1[rec.filename]].add(rec.signer_id)
        cov = validate_split_class_coverage(split_labels)
        self.assertTrue(all(v["complete"] for v in cov.values()))
        for sp in split_signers:
            self.assertEqual(len(split_signers[sp]), 5)
        counts = {sp: sum(1 for v in a1.values() if v == sp) for sp in ("train", "val", "test")}
        self.assertEqual(sum(counts.values()), 1600)
        self.assertGreater(counts["val"], 0)
        self.assertGreater(counts["test"], 0)

    @unittest.skipUnless(WL_ZIP.is_file(), "archive.zip WL-BISINDO NOT FOUND")
    def test_real_archive_metadata_without_extraction(self) -> None:
        before = WL_ZIP.stat().st_size, WL_ZIP.stat().st_mtime
        names = list_wlbisindo_zip_members(WL_ZIP)
        self.assertEqual(len(names), 1600)
        recs = build_wlbisindo_records(names)
        cov = signer_class_coverage(recs)
        self.assertEqual(cov["SIGNER0"], list(range(12)))
        for s in ("SIGNER1", "SIGNER2", "SIGNER3", "SIGNER4"):
            self.assertEqual(cov[s], list(range(32)))
        per_label = {}
        for r in recs:
            per_label[r.source_label_id] = per_label.get(r.source_label_id, 0) + 1
        self.assertEqual(per_label, {i: 50 for i in range(32)})
        self.assertEqual(before, (WL_ZIP.stat().st_size, WL_ZIP.stat().st_mtime))
        # Tidak ada video terekstrak di samping arsip
        self.assertEqual(list(WL_ZIP.parent.glob("*.mp4")), [])


class TestSignDatasetSICoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="sb_wl_si_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_manifest(self) -> Path:
        """Manifest uji berisi keypoint .npy nyata-format dari array nol (hanya untuk uji split, bukan data latih)."""
        kp_dir = self.tmp / "kp"
        kp_dir.mkdir()
        arr = np.zeros((4, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)
        rows = []
        for rec in build_wlbisindo_records(n for n in _synthetic_wlbisindo_names() if n.endswith("_sample1.mp4")):
            vid = Path(rec.filename).stem
            np.save(kp_dir / f"{vid}.npy", arr)
            rows.append(
                {
                    "video_id": vid,
                    "source": "wl_bisindo",
                    "gloss": rec.source_gloss,
                    "label": rec.source_label_id,
                    "signer": rec.signer_id,
                    "kp_path": f"kp/{vid}.npy",
                    "rgb_path": "",
                    "split_sd": "train",
                }
            )
        mp = self.tmp / "manifest.csv"
        with mp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return mp

    def test_signdataset_si_rejects_signer0_test(self) -> None:
        mp = self._write_manifest()
        with self.assertRaises(ValueError):
            SignDataset(mp, data_root=self.tmp, split="test", protocol="si", test_signer="SIGNER0")
        ds = SignDataset(
            mp, data_root=self.tmp, split="test", protocol="si", test_signer="SIGNER0",
            allow_partial_class_coverage=True,
        )
        self.assertEqual(len(ds.si_coverage_report["test"]), 20)

    def test_signdataset_si_accepts_full_coverage_signer(self) -> None:
        mp = self._write_manifest()
        ds = SignDataset(mp, data_root=self.tmp, split="test", protocol="si", test_signer="SIGNER3")
        self.assertEqual(len(ds), 32)
        self.assertEqual(ds.classes[0], "AIR")
        self.assertEqual(ds.class_to_idx["MALAM"], 31)
        self.assertEqual(ds.si_coverage_report["test"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)

