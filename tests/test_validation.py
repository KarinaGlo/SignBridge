"""
Tests untuk WlaslAnnotationValidator.

Mencakup:
- Valid case: num_annotations >= num_videos → is_valid=True
- Missing annotation file → DataValidationError dengan nama file di pesan
- num_annotations < num_videos → DataValidationError dengan hitungan di pesan
- Empty data_dir (0 video) → is_valid=True
- Format WLASL_v0.3.json (list dengan "instances") dihitung dengan benar
- Format flat list dihitung dengan benar
- Pesan error menyebutkan missing_count

Requirements: 2.2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Tambahkan src ke sys.path agar import berfungsi
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.dataset_downloader import DataValidationError
from data.validation import WlaslAnnotationValidationResult, WlaslAnnotationValidator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator() -> WlaslAnnotationValidator:
    return WlaslAnnotationValidator()


def _make_data_dir(base: Path, num_videos: int) -> Path:
    """Buat data_dir dengan num_videos file .mp4 di bawahnya."""
    data_dir = base / "videos"
    if num_videos > 0:
        gloss_dir = data_dir / "gloss_test"
        gloss_dir.mkdir(parents=True, exist_ok=True)
        for i in range(num_videos):
            (gloss_dir / f"video_{i:04d}.mp4").write_bytes(b"\x00" * 64)
    else:
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _make_wlasl_annotation(path: Path, num_instances: int) -> Path:
    """Buat file anotasi format WLASL_v0.3.json dengan total num_instances."""
    data = [
        {
            "gloss": "test_gloss",
            "instances": [
                {"video_id": f"v{i:05d}", "url": f"https://example.com/v{i:05d}.mp4"}
                for i in range(num_instances)
            ],
        }
    ]
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _make_flat_annotation(path: Path, num_records: int) -> Path:
    """Buat file anotasi format flat list dengan num_records entri."""
    data = [{"video_id": f"v{i:05d}", "label": "test"} for i in range(num_records)]
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test: valid case (num_annotations >= num_videos) → is_valid=True
# ---------------------------------------------------------------------------

class TestValidCase:
    def test_exact_match_returns_valid(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Jika num_annotations == num_videos, harus mengembalikan is_valid=True."""
        data_dir = _make_data_dir(tmp_path, num_videos=5)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=5)

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_videos == 5
        assert result.num_annotations == 5
        assert result.missing_count == 0
        assert result.errors == []

    def test_more_annotations_than_videos_returns_valid(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Jika num_annotations > num_videos, harus tetap valid."""
        data_dir = _make_data_dir(tmp_path, num_videos=3)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=10)

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_videos == 3
        assert result.num_annotations == 10
        assert result.missing_count == 0


# ---------------------------------------------------------------------------
# Test: missing annotation file → DataValidationError dengan nama file
# ---------------------------------------------------------------------------

class TestMissingAnnotationFile:
    def test_raises_with_filename_in_message(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """DataValidationError harus menyebutkan nama file anotasi."""
        data_dir = _make_data_dir(tmp_path, num_videos=3)
        missing_path = tmp_path / "nonexistent_annotations.json"

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, missing_path)

        assert "nonexistent_annotations.json" in str(exc_info.value)

    def test_raises_with_missing_count_in_message(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Pesan error harus menyebutkan jumlah anotasi yang hilang (= num_videos)."""
        data_dir = _make_data_dir(tmp_path, num_videos=7)
        missing_path = tmp_path / "missing.json"

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, missing_path)

        # Jumlah hilang = num_videos = 7
        assert "7" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test: num_annotations < num_videos → DataValidationError dengan hitungan
# ---------------------------------------------------------------------------

class TestInsufficientAnnotations:
    def test_raises_data_validation_error(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Harus raise DataValidationError jika anotasi kurang dari video."""
        data_dir = _make_data_dir(tmp_path, num_videos=10)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=5)

        with pytest.raises(DataValidationError):
            validator.validate(data_dir, ann_path)

    def test_error_message_contains_num_annotations(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Pesan error harus menyebutkan num_annotations."""
        data_dir = _make_data_dir(tmp_path, num_videos=10)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=4)

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, ann_path)

        assert "4" in str(exc_info.value)

    def test_error_message_contains_num_videos(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Pesan error harus menyebutkan num_videos."""
        data_dir = _make_data_dir(tmp_path, num_videos=10)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=4)

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, ann_path)

        assert "10" in str(exc_info.value)

    def test_error_message_contains_difference(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Pesan error harus menyebutkan selisih (missing_count)."""
        data_dir = _make_data_dir(tmp_path, num_videos=10)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=4)

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, ann_path)

        # Selisih = 10 - 4 = 6
        assert "6" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test: empty data_dir (0 video) → is_valid=True
# ---------------------------------------------------------------------------

class TestEmptyDataDir:
    def test_empty_dir_with_annotations_is_valid(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """data_dir kosong (0 video) harus selalu valid."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=100)

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_videos == 0
        assert result.missing_count == 0

    def test_empty_dir_with_zero_annotations_is_valid(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """0 video dan 0 anotasi harus valid (nothing to validate)."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)
        ann_path = _make_flat_annotation(tmp_path / "annotations.json", num_records=0)

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_videos == 0
        assert result.num_annotations == 0
        assert result.missing_count == 0

    def test_nonexistent_data_dir_treated_as_zero_videos(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Direktori data yang tidak ada = 0 video → valid asalkan ada anotasi."""
        data_dir = tmp_path / "does_not_exist"
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=5)

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_videos == 0


# ---------------------------------------------------------------------------
# Test: format WLASL_v0.3.json (list dengan "instances") dihitung dengan benar
# ---------------------------------------------------------------------------

class TestWlaslFormatCounting:
    def test_counts_total_instances_across_glosses(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Total instances harus dijumlahkan dari semua entri gloss."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)

        data = [
            {"gloss": "gloss_a", "instances": [{"video_id": f"v{i}"} for i in range(10)]},
            {"gloss": "gloss_b", "instances": [{"video_id": f"w{i}"} for i in range(15)]},
            {"gloss": "gloss_c", "instances": [{"video_id": f"x{i}"} for i in range(5)]},
        ]
        ann_path = tmp_path / "WLASL_v0.3.json"
        ann_path.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate(data_dir, ann_path)

        assert result.num_annotations == 30  # 10 + 15 + 5

    def test_empty_instances_counted_as_zero(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Gloss dengan instances kosong harus berkontribusi 0."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)

        data = [
            {"gloss": "gloss_a", "instances": []},
            {"gloss": "gloss_b", "instances": [{"video_id": "v001"}]},
        ]
        ann_path = tmp_path / "WLASL_v0.3.json"
        ann_path.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate(data_dir, ann_path)

        assert result.num_annotations == 1

    def test_wlasl_format_validated_against_videos(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Pastikan hitungan WLASL format digunakan saat membandingkan dengan video."""
        data_dir = _make_data_dir(tmp_path, num_videos=8)

        # 3 + 5 = 8 instances, tepat sama dengan num_videos
        data = [
            {"gloss": "gloss_a", "instances": [{"video_id": f"v{i}"} for i in range(3)]},
            {"gloss": "gloss_b", "instances": [{"video_id": f"w{i}"} for i in range(5)]},
        ]
        ann_path = tmp_path / "WLASL_v0.3.json"
        ann_path.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate(data_dir, ann_path)

        assert result.is_valid is True
        assert result.num_annotations == 8


# ---------------------------------------------------------------------------
# Test: format flat list dihitung dengan benar
# ---------------------------------------------------------------------------

class TestFlatListFormatCounting:
    def test_flat_list_counted_by_length(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Format flat list harus menggunakan len(list) sebagai count."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)

        num_records = 42
        ann_path = _make_flat_annotation(tmp_path / "annotations.json", num_records=num_records)

        result = validator.validate(data_dir, ann_path)

        assert result.num_annotations == num_records

    def test_flat_list_without_instances_key(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """List yang tidak memiliki key 'instances' harus dianggap flat format."""
        data_dir = _make_data_dir(tmp_path, num_videos=0)

        data = [
            {"video_path": "/path/to/v001.mp4", "label": "MAKAN"},
            {"video_path": "/path/to/v002.mp4", "label": "MINUM"},
            {"video_path": "/path/to/v003.mp4", "label": "BUKU"},
        ]
        ann_path = tmp_path / "pose_annotations.json"
        ann_path.write_text(json.dumps(data), encoding="utf-8")

        result = validator.validate(data_dir, ann_path)

        assert result.num_annotations == 3

    def test_flat_list_validated_against_videos(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Flat list dengan jumlah < video harus raise DataValidationError."""
        data_dir = _make_data_dir(tmp_path, num_videos=10)
        ann_path = _make_flat_annotation(tmp_path / "annotations.json", num_records=5)

        with pytest.raises(DataValidationError):
            validator.validate(data_dir, ann_path)


# ---------------------------------------------------------------------------
# Test: error message menyebutkan missing_count
# ---------------------------------------------------------------------------

class TestErrorMessageMissingCount:
    def test_missing_count_in_insufficient_annotation_error(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Selisih (missing_count) harus ada di pesan DataValidationError."""
        data_dir = _make_data_dir(tmp_path, num_videos=20)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=13)

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, ann_path)

        # missing_count = 20 - 13 = 7
        assert "7" in str(exc_info.value)

    def test_missing_count_in_missing_file_error(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Saat file hilang, missing_count (= num_videos) harus ada di pesan."""
        data_dir = _make_data_dir(tmp_path, num_videos=15)
        missing_path = tmp_path / "not_here.json"

        with pytest.raises(DataValidationError) as exc_info:
            validator.validate(data_dir, missing_path)

        # missing_count = num_videos = 15
        assert "15" in str(exc_info.value)

    def test_valid_result_has_zero_missing_count(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """WlaslAnnotationValidationResult.missing_count harus 0 jika valid."""
        data_dir = _make_data_dir(tmp_path, num_videos=5)
        ann_path = _make_wlasl_annotation(tmp_path / "annotations.json", num_instances=10)

        result = validator.validate(data_dir, ann_path)

        assert result.missing_count == 0


# ---------------------------------------------------------------------------
# Test: berbagai ekstensi video dikenali
# ---------------------------------------------------------------------------

class TestVideoExtensionRecognition:
    def test_counts_mp4_avi_mov_webm(
        self, validator: WlaslAnnotationValidator, tmp_path: Path
    ):
        """Semua ekstensi .mp4, .avi, .mov, .webm harus dihitung."""
        data_dir = tmp_path / "mixed_videos"
        data_dir.mkdir(parents=True)

        (data_dir / "v001.mp4").write_bytes(b"\x00")
        (data_dir / "v002.avi").write_bytes(b"\x00")
        (data_dir / "v003.mov").write_bytes(b"\x00")
        (data_dir / "v004.webm").write_bytes(b"\x00")
        (data_dir / "v005.txt").write_bytes(b"\x00")   # non-video, harus dilewati

        ann_path = _make_flat_annotation(tmp_path / "annotations.json", num_records=4)

        result = validator.validate(data_dir, ann_path)

        assert result.num_videos == 4
        assert result.is_valid is True
