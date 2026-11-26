#!/usr/bin/env python3
"""
test_phase_2c_irr.py

Unit test suite formal untuk memverifikasi seluruh komponen metodologis dan penanganan kondisi batas (edge cases)
pada pipa analisis Inter-Rater Reliability (calculate_inter_rater_agreement.py).

Proyek : SignBridge ASEAN - Image Modality I1 (MobileNetV3-Small BISINDO A-Z)
Fase    : Phase 2C.1 (Final Methodological Audit & Validator Distribution Preparation)
"""

import unittest
import tempfile
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Pastikan path repository terdaftar
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.validation_p2.calculate_inter_rater_agreement import (
    load_and_validate_response,
    compute_metrics,
    compute_bootstrap_kappa,
    create_working_copies_if_valid,
    quarantine_file,
    IngestionStatus,
    ValidationStatusEnum,
    StorageStatusEnum,
    EXPECTED_COLUMNS,
    VALID_DECISIONS,
)


class TestPhase2CIRR(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Baseline template 36 baris valid
        self.base_rows_a = [
            {
                "validator_code": "VAL-A",
                "sample_id": f"VAL-REV-{i:03d}",
                "decision": "CORRECT",
                "correct_letter": "",
                "regional_variation": "",
                "notes": "",
                "review_date": "2026-11-17",
            }
            for i in range(1, 37)
        ]
        self.base_rows_b = [
            {
                "validator_code": "VAL-B",
                "sample_id": f"VAL-REV-{i:03d}",
                "decision": "CORRECT",
                "correct_letter": "",
                "regional_variation": "",
                "notes": "",
                "review_date": "2026-11-17",
            }
            for i in range(1, 37)
        ]

        # Baseline template Schema V2 (Blind Letter Identification)
        self.base_v2_rows_a = [
            {
                "validator_code": "VAL-A",
                "sample_id": f"VAL-REV-{i:03d}",
                "identified_letter": "A",
                "decision": "IDENTIFIED",
                "regional_variation": "NO",
                "notes": "",
                "review_date": "2026-11-18",
            }
            for i in range(1, 37)
        ]
        self.base_v2_rows_b = [
            {
                "validator_code": "VAL-B",
                "sample_id": f"VAL-REV-{i:03d}",
                "identified_letter": "A",
                "decision": "IDENTIFIED",
                "regional_variation": "NO",
                "notes": "",
                "review_date": "2026-11-18",
            }
            for i in range(1, 37)
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_csv(self, filename, rows):
        p = self.temp_path / filename
        pd.DataFrame(rows).to_csv(p, index=False)
        return p

    # 1. Dua validator memberikan keputusan identik
    def test_01_identical_decisions(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        # Mixed categories, exactly identical
        for i in range(1, 10):
            rows_a[i]["decision"] = "INCORRECT"
            rows_a[i]["correct_letter"] = "B"
            rows_b[i]["decision"] = "INCORRECT"
            rows_b[i]["correct_letter"] = "B"

        p_a = self._write_csv("a01.csv", rows_a)
        p_b = self._write_csv("b01.csv", rows_b)

        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        df_b, stat_b = load_and_validate_response(p_b, "VAL-B")
        self.assertEqual(stat_a, "VALID")
        self.assertEqual(stat_b, "VALID")

        res = compute_metrics(df_a, df_b)
        self.assertEqual(res["decision_agreement"]["observed_agreement"], 1.0)
        self.assertEqual(res["decision_agreement"]["cohen_kappa"], 1.0)
        self.assertEqual(res["num_discrepancies"], 0)

    # 2. Dua validator memberikan keputusan berbeda (decision divergence)
    def test_02_divergent_decisions(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_a[0]["decision"] = "CORRECT"
        rows_b[0]["decision"] = "INCORRECT"
        rows_b[0]["correct_letter"] = "C"

        p_a = self._write_csv("a02.csv", rows_a)
        p_b = self._write_csv("b02.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        self.assertLess(res["decision_agreement"]["observed_agreement"], 1.0)
        self.assertGreaterEqual(res["num_discrepancies"], 1)
        self.assertIn("VAL-REV-001", [d["sample_id"] for d in res["discrepancies"]])

    # 3. Keduanya INCORRECT dan huruf alternatif sama
    def test_03_both_incorrect_same_letter(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_a[0]["decision"] = "INCORRECT"
        rows_a[0]["correct_letter"] = "M"
        rows_b[0]["decision"] = "INCORRECT"
        rows_b[0]["correct_letter"] = "M"

        p_a = self._write_csv("a03.csv", rows_a)
        p_b = self._write_csv("b03.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        let_res = res["correct_letter_agreement"]
        self.assertEqual(let_res["both_incorrect_count"], 1)
        self.assertEqual(let_res["matches_count"], 1)
        self.assertEqual(let_res["divergent_count"], 0)
        self.assertEqual(let_res["agreement_rate"], 1.0)

    # 4. Keduanya INCORRECT dan huruf alternatif berbeda
    def test_04_both_incorrect_different_letter(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_a[0]["decision"] = "INCORRECT"
        rows_a[0]["correct_letter"] = "M"
        rows_b[0]["decision"] = "INCORRECT"
        rows_b[0]["correct_letter"] = "N"

        p_a = self._write_csv("a04.csv", rows_a)
        p_b = self._write_csv("b04.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        let_res = res["correct_letter_agreement"]
        self.assertEqual(let_res["both_incorrect_count"], 1)
        self.assertEqual(let_res["matches_count"], 0)
        self.assertEqual(let_res["divergent_count"], 1)
        self.assertEqual(let_res["agreement_rate"], 0.0)
        self.assertIn("VAL-REV-001", let_res["divergent_sample_ids"])
        self.assertIn("VAL-REV-001", [d["sample_id"] for d in res["discrepancies"]])

    # 5. Salah satu validator memilih AMBIGUOUS
    def test_05_one_validator_ambiguous(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_a[2]["decision"] = "AMBIGUOUS"

        p_a = self._write_csv("a05.csv", rows_a)
        p_b = self._write_csv("b05.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        self.assertIn("VAL-REV-003", [d["sample_id"] for d in res["discrepancies"]])
        self.assertIn("VAL-REV-003", res["denominators"]["ambiguous_or_undeterminable_ids"])

    # 6. Salah satu validator memilih UNDETERMINABLE
    def test_06_one_validator_undeterminable(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_b[4]["decision"] = "UNDETERMINABLE"

        p_a = self._write_csv("a06.csv", rows_a)
        p_b = self._write_csv("b06.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        self.assertIn("VAL-REV-005", [d["sample_id"] for d in res["discrepancies"]])
        self.assertIn("VAL-REV-005", res["denominators"]["ambiguous_or_undeterminable_ids"])

    # 7. Zero-variance (seluruh keputusan sama, 100% agreement, Kappa undefined)
    def test_07_zero_variance_kappa_undefined(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]

        p_a = self._write_csv("a07.csv", rows_a)
        p_b = self._write_csv("b07.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")
        res = compute_metrics(df_a, df_b)

        self.assertEqual(res["decision_agreement"]["observed_agreement"], 1.0)
        self.assertIsNone(res["decision_agreement"]["cohen_kappa"])
        self.assertIn("UNDEFINED_ZERO_VARIANCE", res["decision_agreement"]["cohen_kappa_status"])

    # 8. Data kosong (all blank -> STATUS_PENDING)
    def test_08_empty_data_pending(self):
        rows_a = [dict(r, decision="") for r in self.base_rows_a]
        p_a = self._write_csv("a08.csv", rows_a)
        _, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIn("STATUS_PENDING", stat_a)

    # 9. Data parsial (sebagian terisi -> PARTIALLY_FILLED_ERROR)
    def test_09_partial_fill_error(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_a[0]["decision"] = ""  # Hanya 1 yang kosong
        p_a = self._write_csv("a09.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("PARTIALLY_FILLED_ERROR", stat_a)

    # 10. Sample ID duplikat
    def test_10_duplicate_sample_id(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_a[1]["sample_id"] = "VAL-REV-001"
        p_a = self._write_csv("a10.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("DUPLICATE_ID", stat_a)

    # 11. Sample ID tidak lengkap / hilang
    def test_11_incomplete_sample_id(self):
        rows_a = [dict(r) for r in self.base_rows_a[:35]]  # hanya 35 baris
        p_a = self._write_csv("a11.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("ROW_COUNT_MISMATCH", stat_a)

    # 12. Validator code tidak sesuai
    def test_12_wrong_validator_code(self):
        rows_a = [dict(r, validator_code="VAL-B") for r in self.base_rows_a]
        p_a = self._write_csv("a12.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("VALIDATOR_CODE_MISMATCH", stat_a)

    # 13. INCORRECT tanpa correct_letter
    def test_13_incorrect_without_letter(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_a[0]["decision"] = "INCORRECT"
        rows_a[0]["correct_letter"] = ""
        p_a = self._write_csv("a13.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("MISSING_CORRECT_LETTER", stat_a)

    # 14. Perbedaan urutan sample ID dalam file
    def test_14_out_of_order_sample_id(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        # Tukar baris 0 dan baris 1
        rows_a[0], rows_a[1] = rows_a[1], rows_a[0]
        p_a = self._write_csv("a14.csv", rows_a)
        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        self.assertIsNone(df_a)
        self.assertIn("ID_SEQUENCE_ERROR", stat_a)

    # 15. Misaligned sample ID antar file validator
    def test_15_misaligned_sample_id_between_files(self):
        rows_a = [dict(r) for r in self.base_rows_a]
        rows_b = [dict(r) for r in self.base_rows_b]
        rows_b[0]["sample_id"] = "VAL-REV-999"

        # Force DataFrame directly into compute_metrics to test alignment guard
        df_a = pd.DataFrame(rows_a)
        df_b = pd.DataFrame(rows_b)
        with self.assertRaises(ValueError) as ctx:
            compute_metrics(df_a, df_b)
        self.assertIn("SAMPLE_ALIGNMENT_ERROR", str(ctx.exception))

    # 16. Paired Bootstrap Confidence Interval (2000 replikasi, deterministik)
    def test_16_paired_bootstrap_kappa(self):
        labels = sorted(list(VALID_DECISIONS))
        y_a = ["CORRECT"] * 24 + ["INCORRECT"] * 8 + ["AMBIGUOUS"] * 4
        y_b = ["CORRECT"] * 22 + ["INCORRECT"] * 10 + ["AMBIGUOUS"] * 4

        res1 = compute_bootstrap_kappa(y_a, y_b, labels, n_replications=2000, seed=42)
        res2 = compute_bootstrap_kappa(y_a, y_b, labels, n_replications=2000, seed=42)

        self.assertEqual(res1["n_replications"], 2000)
        self.assertEqual(res1["valid_replications"], 2000)
        self.assertEqual(res1["undefined_replications"], 0)
        self.assertEqual(res1["bootstrap_status"], "CALCULATED")
        self.assertIsNotNone(res1["bootstrap_ci_95"])
        ci_low, ci_high = res1["bootstrap_ci_95"]
        self.assertLessEqual(ci_low, ci_high)
        # Reproducibility check: seed 42 must yield identical CI
        self.assertEqual(res1["bootstrap_ci_95"], res2["bootstrap_ci_95"])

    # 17. Paired Bootstrap pada kondisi batas Zero Variance
    def test_17_bootstrap_zero_variance(self):
        labels = sorted(list(VALID_DECISIONS))
        y_a = ["CORRECT"] * 36
        y_b = ["CORRECT"] * 36

        res = compute_bootstrap_kappa(y_a, y_b, labels, n_replications=2000, seed=42)
        self.assertEqual(res["valid_replications"], 0)
        self.assertEqual(res["undefined_replications"], 2000)
        self.assertIsNone(res["bootstrap_ci_95"])
        self.assertEqual(res["bootstrap_status"], "UNDEFINED_ZERO_VARIANCE_IN_ALL_BOOTSTRAPS")

    # 18. Klasifikasi Status Ingesti Baku & Penyimpanan (Phase 2C.7)
    def test_18_ingestion_status_classification(self):
        # 18.1 Empty template
        empty_rows = [dict(r, decision="") for r in self.base_rows_a]
        p_empty = self._write_csv("empty.csv", empty_rows)
        _, stat_empty = load_and_validate_response(p_empty, "VAL-A")
        self.assertEqual(stat_empty.category, IngestionStatus.EMPTY_TEMPLATE)
        self.assertEqual(stat_empty.validation_status, ValidationStatusEnum.EMPTY_TEMPLATE)
        self.assertEqual(stat_empty.storage_status, StorageStatusEnum.RAW_PRESERVED)

        # 18.2 Incomplete pending completion
        part_rows = [dict(r) for r in self.base_rows_a]
        part_rows[0]["decision"] = ""
        p_part = self._write_csv("part.csv", part_rows)
        _, stat_part = load_and_validate_response(p_part, "VAL-A")
        self.assertEqual(stat_part.category, IngestionStatus.INCOMPLETE_PENDING_COMPLETION)
        self.assertEqual(stat_part.validation_status, ValidationStatusEnum.INCOMPLETE_PENDING_COMPLETION)
        self.assertEqual(stat_part.storage_status, StorageStatusEnum.RAW_PRESERVED)

        # 18.3 Schema error (wrong col)
        bad_col_rows = [dict(r) for r in self.base_rows_a]
        for r in bad_col_rows:
            del r["validator_code"]
        p_bad = self._write_csv("bad_col.csv", bad_col_rows)
        _, stat_bad = load_and_validate_response(p_bad, "VAL-A")
        self.assertEqual(stat_bad.category, IngestionStatus.SCHEMA_ERROR)
        self.assertEqual(stat_bad.validation_status, ValidationStatusEnum.SCHEMA_ERROR)
        self.assertEqual(stat_bad.storage_status, StorageStatusEnum.RAW_PRESERVED)

        # 18.4 Valid complete response
        p_val = self._write_csv("valid.csv", self.base_rows_a)
        _, stat_val = load_and_validate_response(p_val, "VAL-A")
        self.assertEqual(stat_val.category, IngestionStatus.VALID_COMPLETE_RESPONSE)
        self.assertEqual(stat_val.validation_status, ValidationStatusEnum.VALID_COMPLETE_RESPONSE)
        self.assertEqual(stat_val.storage_status, StorageStatusEnum.RAW_PRESERVED)

    # 19. Proteksi Working Copy (hanya dibuat jika kedua file VALID_COMPLETE_RESPONSE)
    def test_19_working_copy_guard(self):
        p_val_a = self._write_csv("guard_val_a.csv", self.base_rows_a)
        part_rows = [dict(r) for r in self.base_rows_b]
        part_rows[0]["decision"] = ""
        p_part_b = self._write_csv("guard_part_b.csv", part_rows)

        dest_dir = self.temp_path / "working_copies"
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Satu file parsial -> harus ditolak
        ok, msg = create_working_copies_if_valid(p_val_a, p_part_b, dest_dir)
        self.assertFalse(ok)
        self.assertIn("Penolakan Working Copy", msg)
        self.assertFalse((dest_dir / "VALIDATOR_A_RESPONSE_ACTUAL.csv").exists())

        # Kedua file valid -> berhasil dibuat
        p_val_b = self._write_csv("guard_val_b.csv", self.base_rows_b)
        ok_both, msg_both = create_working_copies_if_valid(p_val_a, p_val_b, dest_dir)
        self.assertTrue(ok_both)
        self.assertTrue((dest_dir / "VALIDATOR_A_RESPONSE_ACTUAL.csv").exists())
        self.assertTrue((dest_dir / "VALIDATOR_B_RESPONSE_ACTUAL.csv").exists())

    # 20. Integritas Karantina (membuat salinan di karantina tanpa menghapus file sumber)
    def test_20_quarantine_integrity(self):
        p_bad = self._write_csv("quarantine_source.csv", [{"bad": "data"}])
        quarantine_dir = self.temp_path / "quarantine_target"

        target_q = quarantine_file(p_bad, quarantine_dir, reason="Corrupt format")
        # File sumber harus tetap ada
        self.assertTrue(p_bad.exists())
        # File target karantina harus tercipta
        self.assertTrue(target_q.exists())
        self.assertEqual(target_q.name, f"QUARANTINED_{p_bad.name}")

    # 21. Schema V2 Blind Letter Identification Metrics
    def test_21_schema_v2_blind_letter_identification_metrics(self):
        rows_a = [dict(r) for r in self.base_v2_rows_a]
        rows_b = [dict(r) for r in self.base_v2_rows_b]
        # Introduce 1 letter divergence at index 5
        rows_b[5]["identified_letter"] = "B"

        p_a = self._write_csv("v2_a.csv", rows_a)
        p_b = self._write_csv("v2_b.csv", rows_b)

        df_a, stat_a = load_and_validate_response(p_a, "VAL-A")
        df_b, stat_b = load_and_validate_response(p_b, "VAL-B")
        self.assertEqual(stat_a.schema_version, "SCHEMA_V2_BLIND_IDENTIFICATION")
        self.assertEqual(stat_b.schema_version, "SCHEMA_V2_BLIND_IDENTIFICATION")
        self.assertEqual(stat_a.category, ValidationStatusEnum.VALID_COMPLETE_RESPONSE)

        res = compute_metrics(df_a, df_b)
        self.assertEqual(res["schema_version"], "SCHEMA_V2_BLIND_IDENTIFICATION")
        self.assertEqual(res["letter_identification_agreement"]["divergent_count"], 1)
        self.assertEqual(res["letter_identification_agreement"]["matches_count"], 35)
        self.assertAlmostEqual(res["letter_identification_agreement"]["agreement_rate"], 35 / 36, places=4)
        self.assertEqual(res["gesture_clarity_agreement"]["observed_agreement"], 1.0)
        self.assertIn("VAL-REV-006", res["letter_identification_agreement"]["divergent_sample_ids"])

    # 22. Excel Workbook Loading and Pre-Distribution Validation
    def test_22_excel_workbook_loading_and_validation(self):
        wb_a_path = REPO_ROOT / "docs" / "validation_p2" / "phase_2c" / "distribution" / "validator_A" / "VALIDATOR_A_WORKBOOK.xlsx"
        wb_b_path = REPO_ROOT / "docs" / "validation_p2" / "phase_2c" / "distribution" / "validator_B" / "VALIDATOR_B_WORKBOOK.xlsx"

        self.assertTrue(wb_a_path.exists(), "Workbook A must exist")
        self.assertTrue(wb_b_path.exists(), "Workbook B must exist")

        df_a, stat_a = load_and_validate_response(wb_a_path, "VAL-A")
        df_b, stat_b = load_and_validate_response(wb_b_path, "VAL-B")

        self.assertEqual(len(df_a), 36)
        self.assertEqual(len(df_b), 36)
        self.assertEqual(stat_a.category, ValidationStatusEnum.EMPTY_TEMPLATE)
        self.assertEqual(stat_b.category, ValidationStatusEnum.EMPTY_TEMPLATE)
        self.assertEqual(stat_a.schema_version, "SCHEMA_V2_BLIND_IDENTIFICATION")
        self.assertEqual(stat_b.schema_version, "SCHEMA_V2_BLIND_IDENTIFICATION")

    # 23. Schema V2 Adjudication Triggers Detection
    def test_23_schema_v2_clarity_and_letter_divergence_triggers(self):
        rows_a = [dict(r) for r in self.base_v2_rows_a]
        rows_b = [dict(r) for r in self.base_v2_rows_b]

        # Trigger 1: Letter divergence on sample 1
        rows_a[0]["identified_letter"] = "C"
        rows_b[0]["identified_letter"] = "D"

        # Trigger 2: Clarity divergence on sample 2
        rows_a[1]["decision"] = "IDENTIFIED"
        rows_b[1]["decision"] = "AMBIGUOUS"

        # Trigger 3: Indeterminacy on sample 3
        rows_a[2]["decision"] = "UNDETERMINABLE"
        rows_b[2]["decision"] = "UNDETERMINABLE"

        p_a = self._write_csv("adj_a.csv", rows_a)
        p_b = self._write_csv("adj_b.csv", rows_b)

        df_a, _ = load_and_validate_response(p_a, "VAL-A")
        df_b, _ = load_and_validate_response(p_b, "VAL-B")

        res = compute_metrics(df_a, df_b)
        discrepancies = res["discrepancies"]
        discrepant_ids = [d["sample_id"] for d in discrepancies]

        self.assertIn("VAL-REV-001", discrepant_ids)
        self.assertIn("VAL-REV-002", discrepant_ids)
        self.assertIn("VAL-REV-003", discrepant_ids)

    # 24. Backward Compatibility Schema V1 vs Schema V2
    def test_24_backward_compatibility_schema_v1_and_v2(self):
        # V1 evaluation
        p_v1_a = self._write_csv("comp_v1_a.csv", self.base_rows_a)
        p_v1_b = self._write_csv("comp_v1_b.csv", self.base_rows_b)
        df_v1_a, stat_v1_a = load_and_validate_response(p_v1_a, "VAL-A")
        df_v1_b, stat_v1_b = load_and_validate_response(p_v1_b, "VAL-B")
        self.assertEqual(stat_v1_a.schema_version, "SCHEMA_V1_LEGACY_VERIFICATION")
        res_v1 = compute_metrics(df_v1_a, df_v1_b)
        self.assertEqual(res_v1["schema_version"], "SCHEMA_V1_LEGACY_VERIFICATION")

        # V2 evaluation
        p_v2_a = self._write_csv("comp_v2_a.csv", self.base_v2_rows_a)
        p_v2_b = self._write_csv("comp_v2_b.csv", self.base_v2_rows_b)
        df_v2_a, stat_v2_a = load_and_validate_response(p_v2_a, "VAL-A")
        df_v2_b, stat_v2_b = load_and_validate_response(p_v2_b, "VAL-B")
        self.assertEqual(stat_v2_a.schema_version, "SCHEMA_V2_BLIND_IDENTIFICATION")
        res_v2 = compute_metrics(df_v2_a, df_v2_b)
        self.assertEqual(res_v2["schema_version"], "SCHEMA_V2_BLIND_IDENTIFICATION")


if __name__ == "__main__":
    unittest.main()

