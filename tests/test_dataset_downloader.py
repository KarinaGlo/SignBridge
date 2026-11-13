"""
Tests untuk DatasetDownloader.

Mencakup:
- Unit tests: DownloadResult, _download_file_with_retry, validate_wl_bisindo_integrity,
  _generate_markdown_report, _parse_wlasl_manifest, _count_wlasl_structure
- Integrasi: download_wlasl dengan mock HTTP server
- Edge cases: file corrupt, ambang batas keberhasilan, direktori kosong

Requirements: 1.1, 2.1, 2.4, 2.5
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Tambahkan src ke sys.path agar import berfungsi
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.dataset_downloader import (
    DatasetDownloader,
    DataValidationError,
    DownloadAbortedError,
    DownloadResult,
    ValidationReport,
    _download_file_with_retry,
    _safe_filename,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def downloader() -> DatasetDownloader:
    return DatasetDownloader(retry_attempts=2, retry_delay=0.0, timeout=5)


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def valid_wl_bisindo_dir(tmp_path: Path) -> Path:
    """Buat struktur WL-BISINDO yang valid: 32 gloss × 50 video."""
    dataset_dir = tmp_path / "wl_bisindo"
    gloss_names = [f"gloss_{i:02d}" for i in range(32)]
    for gloss in gloss_names:
        gloss_dir = dataset_dir / gloss
        gloss_dir.mkdir(parents=True)
        for j in range(50):
            (gloss_dir / f"video_{j:03d}.mp4").write_bytes(b"\x00" * 100)
    return dataset_dir


@pytest.fixture
def incomplete_wl_bisindo_dir(tmp_path: Path) -> Path:
    """Buat struktur WL-BISINDO yang tidak lengkap: beberapa gloss kurang video."""
    dataset_dir = tmp_path / "wl_bisindo_incomplete"
    for i in range(32):
        gloss_dir = dataset_dir / f"gloss_{i:02d}"
        gloss_dir.mkdir(parents=True)
        # Gloss pertama dan terakhir hanya punya 30 video (kurang)
        count = 30 if i in (0, 31) else 50
        for j in range(count):
            (gloss_dir / f"video_{j:03d}.mp4").write_bytes(b"\x00" * 100)
    return dataset_dir


@pytest.fixture
def sample_wlasl_manifest() -> list[dict]:
    """Manifest WLASL kecil untuk testing."""
    return [
        {
            "gloss": "book",
            "instances": [
                {"video_id": "00001", "url": "https://example.com/book/00001.mp4", "signer_id": 1},
                {"video_id": "00002", "url": "https://example.com/book/00002.mp4", "signer_id": 2},
            ],
        },
        {
            "gloss": "drink",
            "instances": [
                {"video_id": "00003", "url": "https://example.com/drink/00003.mp4", "signer_id": 1},
                {"video_id": "00004", "url": "https://example.com/drink/00004.mp4", "signer_id": 3},
            ],
        },
    ]


# ---------------------------------------------------------------------------
# Tests: DownloadResult
# ---------------------------------------------------------------------------

class TestDownloadResult:
    def test_success_rate_all_success(self):
        result = DownloadResult(success=True, files_downloaded=100, files_failed=0)
        assert result.success_rate == 1.0

    def test_success_rate_all_failed(self):
        result = DownloadResult(success=False, files_downloaded=0, files_failed=10)
        assert result.success_rate == 0.0

    def test_success_rate_partial(self):
        result = DownloadResult(success=True, files_downloaded=80, files_failed=20)
        assert result.success_rate == pytest.approx(0.80)

    def test_success_rate_empty(self):
        """Jika tidak ada file sama sekali, success_rate = 1.0 (tidak ada kegagalan)."""
        result = DownloadResult(success=True, files_downloaded=0, files_failed=0)
        assert result.success_rate == 1.0

    def test_default_fields(self):
        result = DownloadResult(success=True, files_downloaded=5, files_failed=1)
        assert result.validation_errors == []
        assert result.failed_urls == []
        assert result.report_path is None


# ---------------------------------------------------------------------------
# Tests: _safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename:
    def test_normal_url(self):
        assert _safe_filename("https://example.com/path/video.mp4") == "video.mp4"

    def test_url_without_filename(self):
        name = _safe_filename("https://example.com/")
        assert name == "file"

    def test_url_with_query(self):
        # Query string harus diabaikan
        name = _safe_filename("https://example.com/video.mp4?token=abc")
        assert name == "video.mp4"


# ---------------------------------------------------------------------------
# Tests: _download_file_with_retry
# ---------------------------------------------------------------------------

class TestDownloadFileWithRetry:
    def test_success_on_first_attempt(self, tmp_path: Path):
        dest = tmp_path / "video.mp4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"fake video content"]

        mock_session = MagicMock()
        mock_session.get.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_session.get.return_value = mock_response

        result = _download_file_with_retry(
            url="https://example.com/video.mp4",
            dest=dest,
            retries=3,
            delay=0.0,
            session=mock_session,
        )
        assert result is True
        assert dest.exists()
        assert dest.stat().st_size > 0

    def test_fails_on_http_error(self, tmp_path: Path):
        dest = tmp_path / "video.mp4"

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        result = _download_file_with_retry(
            url="https://example.com/notfound.mp4",
            dest=dest,
            retries=2,
            delay=0.0,
            session=mock_session,
        )
        assert result is False
        assert not dest.exists()

    def test_corrupt_file_zero_bytes(self, tmp_path: Path):
        """File 0 byte dianggap corrupt — harus gagal (Req 2.4)."""
        dest = tmp_path / "corrupt.mp4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b""]  # konten kosong → 0 byte

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        result = _download_file_with_retry(
            url="https://example.com/corrupt.mp4",
            dest=dest,
            retries=2,
            delay=0.0,
            session=mock_session,
        )
        assert result is False

    def test_retry_on_network_error(self, tmp_path: Path):
        """Harus mencoba ulang setelah RequestException."""
        import requests as req_lib

        dest = tmp_path / "video.mp4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"video data"]

        mock_session = MagicMock()
        # Percobaan 1: gagal network, percobaan 2: berhasil
        mock_session.get.side_effect = [
            req_lib.ConnectionError("network down"),
            mock_response,
        ]

        result = _download_file_with_retry(
            url="https://example.com/video.mp4",
            dest=dest,
            retries=3,
            delay=0.0,
            session=mock_session,
        )
        assert result is True
        assert dest.exists()


# ---------------------------------------------------------------------------
# Tests: validate_wl_bisindo_integrity
# ---------------------------------------------------------------------------

class TestValidateWlBisindoIntegrity:
    def test_valid_dataset_passes(
        self, downloader: DatasetDownloader, valid_wl_bisindo_dir: Path
    ):
        report = downloader.validate_wl_bisindo_integrity(valid_wl_bisindo_dir)
        assert report.is_valid is True
        assert report.total_glosses == 32
        assert report.num_errors == 0
        assert report.glosses_with_errors == []

    def test_incomplete_dataset_raises(
        self, downloader: DatasetDownloader, incomplete_wl_bisindo_dir: Path
    ):
        with pytest.raises(DataValidationError):
            downloader.validate_wl_bisindo_integrity(incomplete_wl_bisindo_dir)

    def test_validation_errors_written_to_file(
        self, downloader: DatasetDownloader, incomplete_wl_bisindo_dir: Path, tmp_path: Path
    ):
        """File validation_errors.txt harus dibuat jika ada error (Req 1.3)."""
        with pytest.raises(DataValidationError):
            downloader.validate_wl_bisindo_integrity(incomplete_wl_bisindo_dir)

        error_file = incomplete_wl_bisindo_dir.parent / "validation_errors.txt"
        assert error_file.exists()
        content = error_file.read_text(encoding="utf-8")
        # Harus menyebutkan gloss yang bermasalah
        assert "gloss_00" in content or "gloss_31" in content

    def test_nonexistent_dir_raises(self, downloader: DatasetDownloader, tmp_path: Path):
        with pytest.raises(DataValidationError, match="tidak ditemukan"):
            downloader.validate_wl_bisindo_integrity(tmp_path / "nonexistent")

    def test_wrong_gloss_count_reported(self, downloader: DatasetDownloader, tmp_path: Path):
        """Direktori dengan jumlah gloss berbeda dari 32 harus dilaporkan."""
        dataset_dir = tmp_path / "wrong_gloss_count"
        for i in range(10):  # hanya 10 gloss
            gdir = dataset_dir / f"gloss_{i:02d}"
            gdir.mkdir(parents=True)
            for j in range(50):
                (gdir / f"video_{j:03d}.mp4").write_bytes(b"\x00")

        with pytest.raises(DataValidationError):
            downloader.validate_wl_bisindo_integrity(dataset_dir)

    def test_errors_mention_gloss_and_signer(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """Pesan error harus menyebutkan gloss dan signer yang bermasalah (Req 1.3)."""
        dataset_dir = tmp_path / "sparse"
        for i in range(32):
            gdir = dataset_dir / f"gloss_{i:02d}"
            gdir.mkdir(parents=True)
            count = 5 if i == 3 else 50  # gloss_03 hanya punya 5 video
            for j in range(count):
                (gdir / f"video_{j:03d}.mp4").write_bytes(b"\x00")

        with pytest.raises(DataValidationError):
            downloader.validate_wl_bisindo_integrity(dataset_dir)

        error_file = dataset_dir.parent / "validation_errors.txt"
        content = error_file.read_text(encoding="utf-8")
        assert "gloss_03" in content


# ---------------------------------------------------------------------------
# Tests: _generate_markdown_report
# ---------------------------------------------------------------------------

class TestGenerateMarkdownReport:
    def test_report_created(self, downloader: DatasetDownloader, tmp_path: Path):
        report_path = downloader._generate_markdown_report(
            dataset_name="TestDataset",
            output_dir=tmp_path,
            files_downloaded=100,
            files_failed=5,
            glosses=10,
            signers=3,
            failed_files=["https://example.com/fail.mp4"],
        )
        assert report_path.exists()
        assert report_path.suffix == ".md"

    def test_report_contains_required_fields(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """Laporan harus berisi: jumlah video, gloss, signer, file gagal (Req 2.5)."""
        report_path = downloader._generate_markdown_report(
            dataset_name="WLASL",
            output_dir=tmp_path,
            files_downloaded=21083,
            files_failed=200,
            glosses=2006,
            signers=119,
            failed_files=["https://example.com/fail1.mp4", "https://example.com/fail2.mp4"],
        )
        content = report_path.read_text(encoding="utf-8")

        assert "21" in content  # jumlah video
        assert "2006" in content or "2,006" in content  # jumlah gloss
        assert "119" in content  # jumlah signer
        assert "200" in content  # file gagal
        assert "WLASL" in content

    def test_report_filename_matches_dataset(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        report_path = downloader._generate_markdown_report(
            dataset_name="WL-BISINDO",
            output_dir=tmp_path,
            files_downloaded=1600,
            files_failed=0,
            glosses=32,
            signers=5,
            failed_files=[],
        )
        assert "wl-bisindo" in report_path.name.lower()

    def test_report_no_failed_section_when_empty(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        report_path = downloader._generate_markdown_report(
            dataset_name="TestDataset",
            output_dir=tmp_path,
            files_downloaded=10,
            files_failed=0,
            glosses=5,
            signers=2,
            failed_files=[],
        )
        content = report_path.read_text(encoding="utf-8")
        assert "File Gagal" not in content

    def test_report_with_extra_info(self, downloader: DatasetDownloader, tmp_path: Path):
        report_path = downloader._generate_markdown_report(
            dataset_name="WLASL",
            output_dir=tmp_path,
            files_downloaded=1000,
            files_failed=50,
            glosses=500,
            signers=60,
            failed_files=[],
            extra_info={"success_rate_pct": "95.2%", "threshold_pct": "80%"},
        )
        content = report_path.read_text(encoding="utf-8")
        assert "95.2%" in content
        assert "80%" in content


# ---------------------------------------------------------------------------
# Tests: _parse_wlasl_manifest
# ---------------------------------------------------------------------------

class TestParseWlaslManifest:
    def test_parses_correct_number_of_tasks(
        self,
        downloader: DatasetDownloader,
        sample_wlasl_manifest: list[dict],
        tmp_path: Path,
    ):
        tasks = downloader._parse_wlasl_manifest(sample_wlasl_manifest, tmp_path)
        assert len(tasks) == 4  # 2 gloss × 2 video masing-masing

    def test_dest_paths_include_gloss(
        self,
        downloader: DatasetDownloader,
        sample_wlasl_manifest: list[dict],
        tmp_path: Path,
    ):
        tasks = downloader._parse_wlasl_manifest(sample_wlasl_manifest, tmp_path)
        gloss_names = {t[1].parent.name for t in tasks}
        assert "book" in gloss_names
        assert "drink" in gloss_names

    def test_skips_entries_without_url(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        manifest = [
            {
                "gloss": "hello",
                "instances": [
                    {"video_id": "v001", "url": ""},      # url kosong — harus dilewati
                    {"video_id": "v002", "url": "https://example.com/v002.mp4"},
                    {"video_id": "", "url": "https://example.com/v003.mp4"},  # id kosong
                ],
            }
        ]
        tasks = downloader._parse_wlasl_manifest(manifest, tmp_path)
        assert len(tasks) == 1  # hanya v002 yang valid

    def test_empty_manifest(self, downloader: DatasetDownloader, tmp_path: Path):
        tasks = downloader._parse_wlasl_manifest([], tmp_path)
        assert tasks == []


# ---------------------------------------------------------------------------
# Tests: _count_wlasl_structure
# ---------------------------------------------------------------------------

class TestCountWlaslStructure:
    def test_counts_glosses_correctly(
        self, downloader: DatasetDownloader, sample_wlasl_manifest: list[dict]
    ):
        glosses, _ = downloader._count_wlasl_structure(sample_wlasl_manifest)
        assert glosses == 2

    def test_counts_unique_signers(
        self, downloader: DatasetDownloader, sample_wlasl_manifest: list[dict]
    ):
        _, signers = downloader._count_wlasl_structure(sample_wlasl_manifest)
        # signer_id 1, 2, 3 → 3 signer unik
        assert signers == 3

    def test_empty_manifest(self, downloader: DatasetDownloader):
        glosses, signers = downloader._count_wlasl_structure([])
        assert glosses == 0
        assert signers == 0


# ---------------------------------------------------------------------------
# Tests: download_wlasl — mocked HTTP
# ---------------------------------------------------------------------------

class TestDownloadWlasl:
    def _make_video_response(self) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.iter_content.return_value = [b"fake video data"]
        return resp

    def _make_manifest_response(self, manifest: list[dict]) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.iter_content.return_value = [json.dumps(manifest).encode()]
        return resp

    def test_successful_download_generates_report(
        self, downloader: DatasetDownloader, tmp_path: Path, sample_wlasl_manifest: list[dict]
    ):
        """Jika semua file berhasil, harus menghasilkan laporan Markdown (Req 2.5)."""
        manifest_json = json.dumps(sample_wlasl_manifest).encode()

        manifest_resp = MagicMock()
        manifest_resp.status_code = 200
        manifest_resp.iter_content.return_value = [manifest_json]

        video_resp = MagicMock()
        video_resp.status_code = 200
        video_resp.iter_content.return_value = [b"video content here"]

        with patch.object(downloader._session, "get") as mock_get:
            mock_get.return_value = manifest_resp

            # Manifest sudah ada di disk — tulis dulu
            manifest_path = tmp_path / "WLASL_v0.3.json"
            manifest_path.write_text(json.dumps(sample_wlasl_manifest), encoding="utf-8")

            # Semua video download berhasil
            mock_get.return_value = video_resp

            result = downloader.download_wlasl(tmp_path)

        assert result.success is True
        assert result.report_path is not None
        assert result.report_path.exists()

    def test_abort_when_below_threshold(
        self, downloader: DatasetDownloader, tmp_path: Path, sample_wlasl_manifest: list[dict]
    ):
        """Harus raise DownloadAbortedError jika < 80% berhasil (Req 2.4)."""
        # Tulis manifest
        manifest_path = tmp_path / "WLASL_v0.3.json"
        manifest_path.write_text(json.dumps(sample_wlasl_manifest), encoding="utf-8")

        # Semua download gagal (HTTP 500)
        fail_resp = MagicMock()
        fail_resp.status_code = 500

        with patch.object(downloader._session, "get", return_value=fail_resp):
            with pytest.raises(DownloadAbortedError):
                downloader.download_wlasl(tmp_path)

    def test_failed_files_logged(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """File yang gagal harus dicatat ke log (Req 2.4)."""
        small_manifest = [
            {
                "gloss": "hello",
                "instances": [
                    {"video_id": "v001", "url": "https://example.com/v001.mp4", "signer_id": 1},
                ],
            }
        ]
        manifest_path = tmp_path / "WLASL_v0.3.json"
        manifest_path.write_text(json.dumps(small_manifest), encoding="utf-8")

        fail_resp = MagicMock()
        fail_resp.status_code = 404

        with patch.object(downloader._session, "get", return_value=fail_resp):
            with pytest.raises(DownloadAbortedError):
                downloader.download_wlasl(tmp_path)

        log_file = tmp_path / "logs" / "wlasl_failed_downloads.log"
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "example.com" in log_content

    def test_skips_already_downloaded_files(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """File yang sudah ada dan tidak corrupt tidak perlu diunduh ulang."""
        small_manifest = [
            {
                "gloss": "book",
                "instances": [
                    {"video_id": "v001", "url": "https://example.com/v001.mp4", "signer_id": 1},
                ],
            }
        ]
        manifest_path = tmp_path / "WLASL_v0.3.json"
        manifest_path.write_text(json.dumps(small_manifest), encoding="utf-8")

        # Buat file video yang sudah ada
        existing = tmp_path / "book" / "v001.mp4"
        existing.parent.mkdir(parents=True, exist_ok=True)
        existing.write_bytes(b"existing video data")

        # Mock session tidak boleh dipanggil untuk file ini
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("should not be called")
        downloader._session = mock_session

        result = downloader.download_wlasl(tmp_path)
        assert result.success is True
        assert result.files_downloaded == 1
        assert result.files_failed == 0


# ---------------------------------------------------------------------------
# Tests: download_wl_bisindo — mocked subprocess
# ---------------------------------------------------------------------------

class TestDownloadWlBisindo:
    def test_success_generates_report(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """Download berhasil harus menghasilkan laporan Markdown."""
        output_dir = tmp_path / "wl_bisindo"

        # Buat beberapa video seolah kaggle CLI sudah mengunduh
        for i in range(2):
            gdir = output_dir / f"gloss_{i:02d}"
            gdir.mkdir(parents=True)
            for j in range(3):
                (gdir / f"video_{j:03d}.mp4").write_bytes(b"\x00")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = downloader.download_wl_bisindo("dataset/wl-bisindo", output_dir)

        assert result.success is True
        assert result.report_path is not None
        assert result.report_path.exists()

    def test_kaggle_not_found(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """Jika kaggle CLI tidak ada, harus mengembalikan DownloadResult gagal."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = downloader.download_wl_bisindo("dataset/wl-bisindo", tmp_path)

        assert result.success is False
        assert any("Kaggle CLI" in e for e in result.validation_errors)

    def test_all_retries_fail(
        self, downloader: DatasetDownloader, tmp_path: Path
    ):
        """Jika semua percobaan kaggle CLI gagal, harus mengembalikan failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="authentication error"
            )
            result = downloader.download_wl_bisindo("dataset/wl-bisindo", tmp_path)

        assert result.success is False
        assert len(result.validation_errors) > 0
