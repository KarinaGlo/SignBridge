"""
tests/test_evaluate_external_images.py
Unit tests for hardened external validation pipeline:
1. Hard rejection of data without exact consent_status == 'CONSENT_SIGNED'
2. Data without valid consent NEVER enters model inference
3. Consistent signer_id metric grouping and prediction output
4. Backward compatibility fallback for subject_id without double counting
5. Empty and invalid manifest handling
"""

import csv
import json
from pathlib import Path
from typing import Dict, List

import pytest
import torch
from PIL import Image

from scripts.validation_p1.evaluate_external_images import (
    evaluate_external_dataset,
    resolve_signer_id,
)


class MockP1Model(torch.nn.Module):
    """Mock model that counts inference invocations and tracks input shapes."""

    def __init__(self, pred_class_idx: int = 0):
        super().__init__()
        self.pred_class_idx = pred_class_idx
        self.call_count = 0
        self.inferred_batches: List[torch.Tensor] = []

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.call_count += 1
        self.inferred_batches.append(x)
        batch_size = x.shape[0]
        logits = torch.zeros((batch_size, 26), dtype=torch.float32)
        logits[:, self.pred_class_idx] = 10.0
        return logits


def _create_dummy_image(img_path: Path):
    img_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    img.save(img_path)


def _write_csv(csv_path: Path, fieldnames: List[str], rows: List[Dict[str, str]]):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ==============================================================================
# 1. RESOLVE SIGNER ID TESTS
# ==============================================================================


def test_resolve_signer_id_precedence():
    """Signer ID takes precedence over subject_id."""
    row = {"signer_id": "EXT_S01", "subject_id": "LEGACY_S99"}
    assert resolve_signer_id(row) == "EXT_S01"


def test_resolve_signer_id_fallback():
    """Fallback to subject_id if signer_id is empty or missing."""
    row_empty = {"signer_id": "", "subject_id": "LEGACY_S99"}
    assert resolve_signer_id(row_empty) == "LEGACY_S99"

    row_missing = {"subject_id": "LEGACY_S99"}
    assert resolve_signer_id(row_missing) == "LEGACY_S99"


def test_resolve_signer_id_unknown():
    """Returns UNKNOWN_SIGNER if both are absent or blank."""
    assert resolve_signer_id({}) == "UNKNOWN_SIGNER"
    assert resolve_signer_id({"signer_id": "   ", "subject_id": "  "}) == "UNKNOWN_SIGNER"


# ==============================================================================
# 2. CONSENT VALIDATION & INFERENCE GATING TESTS
# ==============================================================================


def test_valid_consent_included_in_inference(tmp_path: Path):
    """Row with consent_status == 'CONSENT_SIGNED' must be processed and inferred."""
    img_path = tmp_path / "img_valid.jpg"
    _create_dummy_image(img_path)

    manifest_path = tmp_path / "manifest_valid.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "consent_status"],
        [
            {
                "image_path": str(img_path),
                "label": "A",
                "signer_id": "EXT_S01",
                "consent_status": "CONSENT_SIGNED",
            }
        ],
    )

    out_dir = tmp_path / "output_valid"
    mock_model = MockP1Model(pred_class_idx=0)  # Class 0 == 'A'

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "EVALUATED"
    assert summary["total_evaluated_samples"] == 1
    assert summary["rejected_counts"]["consent_invalid"] == 0
    assert summary["accuracy_pct"] == 100.0
    assert mock_model.call_count == 1, "Mock model must be called exactly once"

    pred_csv = out_dir / "external_predictions.csv"
    assert pred_csv.exists()
    with open(pred_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 1
        assert reader[0]["signer_id"] == "EXT_S01"
        assert reader[0]["true_char"] == "A"
        assert reader[0]["pred_char"] == "A"


def test_empty_consent_rejected_never_inferred(tmp_path: Path):
    """Rows with empty or whitespace-only consent must be rejected without inference."""
    img_path1 = tmp_path / "img1.jpg"
    img_path2 = tmp_path / "img2.jpg"
    _create_dummy_image(img_path1)
    _create_dummy_image(img_path2)

    manifest_path = tmp_path / "manifest_empty_consent.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "consent_status"],
        [
            {"image_path": str(img_path1), "label": "A", "signer_id": "EXT_S01", "consent_status": ""},
            {"image_path": str(img_path2), "label": "B", "signer_id": "EXT_S01", "consent_status": "   "},
        ],
    )

    out_dir = tmp_path / "output_empty_consent"
    mock_model = MockP1Model()

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "NO_VALID_DATA"
    assert summary["total_evaluated_samples"] == 0
    assert summary["rejected_counts"]["consent_invalid"] == 2
    assert mock_model.call_count == 0, "Model inference must NEVER be called for empty consent"


def test_refused_consent_rejected_never_inferred(tmp_path: Path):
    """Rows with non-CONSENT_SIGNED values must be hard-rejected without inference."""
    img_paths = [tmp_path / f"img_refused_{i}.jpg" for i in range(4)]
    for p in img_paths:
        _create_dummy_image(p)

    manifest_path = tmp_path / "manifest_refused.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "consent_status"],
        [
            {"image_path": str(img_paths[0]), "label": "A", "signer_id": "EXT_S01", "consent_status": "CONSENT_REFUSED"},
            {"image_path": str(img_paths[1]), "label": "B", "signer_id": "EXT_S01", "consent_status": "CONSENT_PENDING"},
            {"image_path": str(img_paths[2]), "label": "C", "signer_id": "EXT_S01", "consent_status": "NO"},
            {"image_path": str(img_paths[3]), "label": "D", "signer_id": "EXT_S01", "consent_status": "consent_signed"},  # lowercase invalid
        ],
    )

    out_dir = tmp_path / "output_refused"
    mock_model = MockP1Model()

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "NO_VALID_DATA"
    assert summary["total_evaluated_samples"] == 0
    assert summary["rejected_counts"]["consent_invalid"] == 4
    assert mock_model.call_count == 0, "Model inference must NEVER be called for refused/invalid consent"


def test_missing_consent_column_rejected_never_inferred(tmp_path: Path):
    """Manifest without consent_status column must be rejected without inference."""
    img_path = tmp_path / "img_missing_col.jpg"
    _create_dummy_image(img_path)

    manifest_path = tmp_path / "manifest_missing_consent_col.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id"],  # consent_status omitted
        [{"image_path": str(img_path), "label": "A", "signer_id": "EXT_S01"}],
    )

    out_dir = tmp_path / "output_missing_col"
    mock_model = MockP1Model()

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "NO_VALID_DATA"
    assert summary["total_evaluated_samples"] == 0
    assert summary["rejected_counts"]["consent_invalid"] == 1
    assert mock_model.call_count == 0, "Model inference must NEVER be called when consent column is missing"


def test_strict_unconsented_data_gating_mixed_manifest(tmp_path: Path):
    """In a mixed manifest, unconsented rows are rejected; consented rows are inferred."""
    imgs = [tmp_path / f"mixed_{i}.jpg" for i in range(5)]
    for p in imgs:
        _create_dummy_image(p)

    manifest_path = tmp_path / "manifest_mixed.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "consent_status"],
        [
            {"image_path": str(imgs[0]), "label": "A", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(imgs[1]), "label": "B", "signer_id": "EXT_S01", "consent_status": ""},
            {"image_path": str(imgs[2]), "label": "C", "signer_id": "EXT_S02", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(imgs[3]), "label": "D", "signer_id": "EXT_S02", "consent_status": "CONSENT_REFUSED"},
            {"image_path": str(imgs[4]), "label": "E", "signer_id": "EXT_S03", "consent_status": "PENDING"},
        ],
    )

    out_dir = tmp_path / "output_mixed"
    mock_model = MockP1Model(pred_class_idx=0)

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "EVALUATED"
    assert summary["total_evaluated_samples"] == 2
    assert summary["total_rejected_samples"] == 3
    assert summary["rejected_counts"]["consent_invalid"] == 3
    assert mock_model.call_count == 2, "Model must ONLY be called for the 2 consented images"


# ==============================================================================
# 3. SIGNER_ID GROUPING & COMPATIBILITY TESTS
# ==============================================================================


def test_signer_id_grouping_and_output(tmp_path: Path):
    """Metrics must group by signer_id, handle subject_id fallback, and avoid double counting."""
    imgs = [tmp_path / f"signer_img_{i}.jpg" for i in range(4)]
    for p in imgs:
        _create_dummy_image(p)

    manifest_path = tmp_path / "manifest_signers.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "subject_id", "consent_status"],
        [
            {"image_path": str(imgs[0]), "label": "A", "signer_id": "EXT_S01", "subject_id": "", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(imgs[1]), "label": "B", "signer_id": "EXT_S01", "subject_id": "", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(imgs[2]), "label": "C", "signer_id": "EXT_S02", "subject_id": "", "consent_status": "CONSENT_SIGNED"},
            # Row 4 uses subject_id fallback without signer_id:
            {"image_path": str(imgs[3]), "label": "D", "signer_id": "", "subject_id": "EXT_S03", "consent_status": "CONSENT_SIGNED"},
        ],
    )

    out_dir = tmp_path / "output_signers"
    mock_model = MockP1Model(pred_class_idx=0)

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "EVALUATED"
    assert summary["total_evaluated_samples"] == 4

    signer_perf = summary["per_signer_performance"]
    assert set(signer_perf.keys()) == {"EXT_S01", "EXT_S02", "EXT_S03"}
    assert signer_perf["EXT_S01"]["samples"] == 2
    assert signer_perf["EXT_S02"]["samples"] == 1
    assert signer_perf["EXT_S03"]["samples"] == 1
    # Check no double counting
    total_signer_samples = sum(s["samples"] for s in signer_perf.values())
    assert total_signer_samples == 4

    pred_csv = out_dir / "external_predictions.csv"
    with open(pred_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert "signer_id" in reader[0]
        assert [r["signer_id"] for r in reader] == ["EXT_S01", "EXT_S01", "EXT_S02", "EXT_S03"]


# ==============================================================================
# 4. MANIFEST EDGE CASES: EMPTY & INVALID LABEL
# ==============================================================================


def test_empty_manifest_files(tmp_path: Path):
    """Empty CSV file or CSV with only headers returns PENDING EXTERNAL DATA without inference."""
    empty_file = tmp_path / "completely_empty.csv"
    empty_file.write_text("", encoding="utf-8")

    out_dir1 = tmp_path / "out_empty1"
    mock1 = MockP1Model()
    res1 = evaluate_external_dataset(empty_file, tmp_path / "dummy.pt", out_dir1, model=mock1)
    assert res1["status"] == "PENDING EXTERNAL DATA"
    assert res1["total_evaluated_samples"] == 0
    assert mock1.call_count == 0

    header_only_file = tmp_path / "header_only.csv"
    header_only_file.write_text("image_path,label,signer_id,consent_status\n", encoding="utf-8")
    out_dir2 = tmp_path / "out_empty2"
    mock2 = MockP1Model()
    res2 = evaluate_external_dataset(header_only_file, tmp_path / "dummy.pt", out_dir2, model=mock2)
    assert res2["status"] == "PENDING EXTERNAL DATA"
    assert res2["total_evaluated_samples"] == 0
    assert mock2.call_count == 0


def test_invalid_label_rejected(tmp_path: Path):
    """Rows with invalid labels must be rejected and never inferred."""
    img_paths = [tmp_path / f"invalid_lbl_{i}.jpg" for i in range(4)]
    for p in img_paths:
        _create_dummy_image(p)

    manifest_path = tmp_path / "manifest_invalid_label.csv"
    _write_csv(
        manifest_path,
        ["image_path", "label", "signer_id", "consent_status"],
        [
            {"image_path": str(img_paths[0]), "label": "INVALID_LABEL", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(img_paths[1]), "label": "99", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(img_paths[2]), "label": "", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
            {"image_path": str(img_paths[3]), "label": "?", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
        ],
    )

    out_dir = tmp_path / "output_invalid_label"
    mock_model = MockP1Model()

    summary = evaluate_external_dataset(
        manifest_path=manifest_path,
        checkpoint_path=tmp_path / "dummy_best.pt",
        out_dir=out_dir,
        model=mock_model,
    )

    assert summary["status"] == "NO_VALID_DATA"
    assert summary["total_evaluated_samples"] == 0
    assert summary["rejected_counts"]["invalid_label"] == 4
    assert mock_model.call_count == 0, "Model inference must NEVER be called for invalid labels"

