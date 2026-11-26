"""
tests/test_track_external_collection.py
Unit tests for Field Data Collection Tracker (I1-P1) & Manifest Integration Fixes (GAP-01, GAP-02, GAP-03):
1. Relative path 'A/EXT_S01_A_01.jpg' (dataset-relative).
2. Relative path 'data/external/bisindo_validation/A/EXT_S01_A_01.jpg' (root-relative).
3. Absolute path.
4. File not found in either location.
5. Priority of data_dir if file exists in both candidates.
6. Actual manifest available (external_manifest.csv).
7. Actual manifest not available and template used as fallback.
8. Template containing sample line is not counted as data.
9. Empty manifest still produces NOT STARTED.
10. Evaluator and tracker use consistent path rules.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List

import pytest
from PIL import Image
import torch

from scripts.validation_p1.track_external_collection import (
    ROOT,
    TOTAL_TARGET,
    compute_sha256,
    resolve_image_path,
    scan_disk_images,
    track_collection_progress,
)
from scripts.validation_p1.evaluate_external_images import (
    evaluate_external_dataset,
    resolve_image_path as eval_resolve_image_path,
)


class MockModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.call_count = 0

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        self.call_count += 1
        logits = torch.zeros((x.shape[0], 26), dtype=torch.float32)
        logits[:, 0] = 10.0
        return logits


def _create_dummy_image(path: Path, color=(120, 140, 160)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (64, 64), color=color)
    img.save(path)


def _write_csv(path: Path, rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "image_path",
        "label",
        "signer_id",
        "capture_id",
        "capture_date",
        "device",
        "camera_angle",
        "lighting_condition",
        "background",
        "image_width",
        "image_height",
        "consent_status",
        "verified_label",
        "notes",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ==============================================================================
# GAP-01: PATH RESOLUTION UNIT TESTS
# ==============================================================================


def test_resolve_image_path_dataset_relative(tmp_path: Path):
    """1. Relative path 'A/EXT_S01_A_01.jpg' resolves against data_dir."""
    data_dir = tmp_path / "data" / "external" / "bisindo_validation"
    target_img = data_dir / "A" / "EXT_S01_A_01.jpg"
    _create_dummy_image(target_img)

    resolved = resolve_image_path("A/EXT_S01_A_01.jpg", data_dir=data_dir)
    assert resolved == target_img.resolve()
    assert resolved.exists()


def test_resolve_image_path_root_relative(tmp_path: Path, monkeypatch):
    """2. Relative path 'data/external/.../A/img.jpg' resolves against ROOT."""
    fake_root = tmp_path / "fake_repo"
    monkeypatch.setattr("scripts.validation_p1.track_external_collection.ROOT", fake_root)

    data_dir = fake_root / "data" / "external" / "bisindo_validation"
    target_img = data_dir / "A" / "EXT_S01_A_01.jpg"
    _create_dummy_image(target_img)

    rel_from_root = "data/external/bisindo_validation/A/EXT_S01_A_01.jpg"
    resolved = resolve_image_path(rel_from_root, data_dir=data_dir)
    assert resolved == target_img.resolve()
    assert resolved.exists()


def test_resolve_image_path_absolute(tmp_path: Path):
    """3. Absolute path is preserved and normalized."""
    abs_img = tmp_path / "random_dir" / "photo.jpg"
    _create_dummy_image(abs_img)

    resolved = resolve_image_path(str(abs_img), data_dir=tmp_path / "dummy_data_dir")
    assert resolved == abs_img.resolve()
    assert resolved.exists()


def test_resolve_image_path_not_found_both(tmp_path: Path):
    """4. File not found in either location produces predictable candidate."""
    data_dir = tmp_path / "dataset"
    data_dir.mkdir(parents=True)

    cand_data = resolve_image_path("B/ghost.jpg", data_dir=data_dir)
    assert cand_data == (data_dir / "B" / "ghost.jpg").resolve()
    assert not cand_data.exists()

    cand_root = resolve_image_path("data/ghost.jpg", data_dir=data_dir)
    assert cand_root == (ROOT / "data" / "ghost.jpg").resolve()
    assert not cand_root.exists()


def test_resolve_image_path_priority_data_dir(tmp_path: Path, monkeypatch):
    """5. Priority of data_dir if file exists in both candidates."""
    fake_root = tmp_path / "fake_root"
    monkeypatch.setattr("scripts.validation_p1.track_external_collection.ROOT", fake_root)

    data_dir = fake_root / "dataset"
    # Create file at data_dir / "sample.jpg"
    img_data_dir = data_dir / "sample.jpg"
    _create_dummy_image(img_data_dir, color=(1, 1, 1))

    # Create file at fake_root / "sample.jpg"
    img_root = fake_root / "sample.jpg"
    _create_dummy_image(img_root, color=(2, 2, 2))

    resolved = resolve_image_path("sample.jpg", data_dir=data_dir)
    assert resolved == img_data_dir.resolve(), "data_dir must take precedence over ROOT"


# ==============================================================================
# GAP-02: MANIFEST TRANSPARENCY UNIT TESTS
# ==============================================================================


def test_manifest_actual_available(tmp_path: Path):
    """6. When external_manifest.csv is present, it is recognized as ACTUAL_MANIFEST."""
    data_dir = tmp_path / "data_dir"
    actual_manifest = data_dir / "external_manifest.csv"
    template_manifest = data_dir / "external_manifest_template.csv"

    img = data_dir / "A" / "EXT_S01_A_01.jpg"
    _create_dummy_image(img)

    _write_csv(
        actual_manifest,
        [{"image_path": "A/EXT_S01_A_01.jpg", "label": "A", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"}],
    )
    _write_csv(template_manifest, [])

    summary = track_collection_progress(data_dir=data_dir)

    minfo = summary["manifest_info"]
    assert minfo["actual_manifest_exists"] is True
    assert minfo["manifest_mode"] == "ACTUAL_MANIFEST"
    assert minfo["active_manifest_path"] == str(actual_manifest.resolve())
    assert summary["total_valid_collected"] == 1


def test_manifest_template_fallback_transparent(tmp_path: Path):
    """7. When actual manifest is missing, template is used with explicit fallback status."""
    data_dir = tmp_path / "data_dir"
    template_manifest = data_dir / "external_manifest_template.csv"
    _write_csv(
        template_manifest,
        [{"image_path": "# CONTOH_PENGISIAN: A/test.jpg", "label": "A", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"}],
    )

    out_report = tmp_path / "report.md"
    summary = track_collection_progress(data_dir=data_dir, out_report=out_report)

    minfo = summary["manifest_info"]
    assert minfo["actual_manifest_exists"] is False
    assert minfo["manifest_mode"] == "TEMPLATE_FALLBACK"
    assert "BELUM DIBUAT" in minfo["status_label"]

    report_text = out_report.read_text(encoding="utf-8")
    assert "BELUM DIBUAT" in report_text
    assert "DIGUNAKAN SEBAGAI FALLBACK REFERENSI" in report_text


def test_template_sample_line_ignored(tmp_path: Path):
    """8. Template containing sample line prefixed with # is not counted as data."""
    data_dir = tmp_path / "data_dir"
    template_manifest = data_dir / "external_manifest_template.csv"
    template_manifest.parent.mkdir(parents=True)
    template_manifest.write_text(
        "image_path,label,signer_id,consent_status\n"
        "# CONTOH_PENGISIAN: A/EXT_S01_A_01.jpg,A,EXT_S01,CONSENT_SIGNED\n",
        encoding="utf-8",
    )

    summary = track_collection_progress(data_dir=data_dir)
    assert summary["total_valid_collected"] == 0
    assert summary["overall_status"] == "NOT STARTED"


def test_empty_manifest_still_not_started(tmp_path: Path):
    """9. Empty manifest still produces NOT STARTED and deficit 780."""
    data_dir = tmp_path / "data_dir"
    actual_manifest = data_dir / "external_manifest.csv"
    _write_csv(actual_manifest, [])

    summary = track_collection_progress(data_dir=data_dir)
    assert summary["overall_status"] == "NOT STARTED"
    assert summary["total_valid_collected"] == 0
    assert summary["total_shortfall"] == 780


# ==============================================================================
# GAP-03: CONSISTENCY BETWEEN TRACKER AND EVALUATOR
# ==============================================================================


def test_evaluator_and_tracker_consistent_path_rules(tmp_path: Path):
    """10. Evaluator and tracker resolve dataset-relative and root-relative paths identically."""
    data_dir = tmp_path / "data" / "external" / "bisindo_validation"
    img1 = data_dir / "A" / "EXT_S01_A_01.jpg"
    img2 = data_dir / "B" / "EXT_S01_B_01.jpg"
    _create_dummy_image(img1, color=(10, 20, 30))
    _create_dummy_image(img2, color=(40, 50, 60))

    # 1. Test dataset-relative path in both
    res_track1 = resolve_image_path("A/EXT_S01_A_01.jpg", data_dir=data_dir)
    res_eval1 = eval_resolve_image_path("A/EXT_S01_A_01.jpg", data_dir=data_dir)
    assert res_track1 == img1.resolve()
    assert res_eval1 == img1.resolve()

    # 2. Test manifest reading in evaluator using dataset-relative paths
    manifest = data_dir / "external_manifest.csv"
    _write_csv(
        manifest,
        [
            {"image_path": "A/EXT_S01_A_01.jpg", "label": "A", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
            {"image_path": "B/EXT_S01_B_01.jpg", "label": "B", "signer_id": "EXT_S01", "consent_status": "CONSENT_SIGNED"},
        ],
    )

    # Tracker evaluation
    summary_track = track_collection_progress(data_dir=data_dir, manifest_path=manifest)
    assert summary_track["total_valid_collected"] == 2
    assert summary_track["anomalies"]["missing_disk_count"] == 0

    # Evaluator evaluation with MockModel
    mock_model = MockModel()
    out_dir = tmp_path / "eval_out"
    summary_eval = evaluate_external_dataset(
        manifest_path=manifest,
        checkpoint_path=tmp_path / "dummy.pt",
        out_dir=out_dir,
        model=mock_model,
        data_dir=data_dir,
    )
    assert summary_eval["status"] == "EVALUATED"
    assert summary_eval["total_evaluated_samples"] == 2
    assert summary_eval["rejected_counts"]["file_not_found"] == 0
    assert mock_model.call_count == 2
