"""
test_frame_extractor.py — Unit tests dan property-based tests untuk FrameExtractor.

Validates: Requirements 1.6
- Frame diekstrak pada 25 FPS
- Disimpan sebagai PNG dengan cv2.IMWRITE_PNG_COMPRESSION = 6
- Metadata (resolusi, durasi) dicatat ke JSONL
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from src.data.frame_extractor import (
    FrameExtractor,
    FrameExtractionResult,
    BatchExtractionReport,
    TARGET_FPS,
    PNG_COMPRESSION_LEVEL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_synthetic_video(
    path: Path,
    fps: float = 30.0,
    width: int = 64,
    height: int = 64,
    num_frames: int = 30,
    codec: str = "mp4v",
) -> Path:
    """
    Buat video sintetis menggunakan cv2.VideoWriter untuk keperluan testing.
    Setiap frame diisi dengan warna acak agar bisa diverifikasi.
    """
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    assert writer.isOpened(), f"Tidak dapat membuat VideoWriter untuk {path}"

    rng = np.random.default_rng(42)
    for i in range(num_frames):
        # Frame dengan warna berbeda per indeks agar mudah dibedakan
        color_val = int((i / max(num_frames - 1, 1)) * 200) + 20
        frame = np.full((height, width, 3), color_val, dtype=np.uint8)
        writer.write(frame)

    writer.release()
    assert path.exists(), f"Video tidak terbuat: {path}"
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def extractor() -> FrameExtractor:
    """FrameExtractor dengan pengaturan default (25 FPS, PNG compression 6)."""
    return FrameExtractor()


@pytest.fixture
def synthetic_video(tmp_path: Path) -> Path:
    """Video sintetis 64×64, 30 FPS, 30 frame — bisa di-extract ke ~25 frame."""
    video_path = tmp_path / "test_video.mp4"
    return create_synthetic_video(video_path, fps=30.0, width=64, height=64, num_frames=30)


@pytest.fixture
def synthetic_video_25fps(tmp_path: Path) -> Path:
    """Video sintetis 64×64, tepat 25 FPS, 25 frame."""
    video_path = tmp_path / "test_25fps.mp4"
    return create_synthetic_video(video_path, fps=25.0, width=64, height=64, num_frames=25)


@pytest.fixture
def synthetic_video_60fps(tmp_path: Path) -> Path:
    """Video sintetis 64×64, 60 FPS, 60 frame — downsampling lebih agresif."""
    video_path = tmp_path / "test_60fps.mp4"
    return create_synthetic_video(video_path, fps=60.0, width=64, height=64, num_frames=60)


# ---------------------------------------------------------------------------
# Tests: Konstruktor FrameExtractor
# ---------------------------------------------------------------------------

class TestFrameExtractorConstructor:

    def test_default_values(self):
        ext = FrameExtractor()
        assert ext.target_fps == TARGET_FPS  # 25
        assert ext.png_compression == PNG_COMPRESSION_LEVEL  # 6
        assert ext.write_metadata is True

    def test_custom_target_fps(self):
        ext = FrameExtractor(target_fps=15)
        assert ext.target_fps == 15

    def test_custom_png_compression(self):
        ext = FrameExtractor(png_compression=0)
        assert ext.png_compression == 0

    def test_png_compression_max_valid(self):
        ext = FrameExtractor(png_compression=9)
        assert ext.png_compression == 9

    def test_png_compression_min_valid(self):
        ext = FrameExtractor(png_compression=0)
        assert ext.png_compression == 0

    def test_png_compression_out_of_range_raises(self):
        with pytest.raises(ValueError, match="png_compression"):
            FrameExtractor(png_compression=10)

    def test_png_compression_negative_raises(self):
        with pytest.raises(ValueError, match="png_compression"):
            FrameExtractor(png_compression=-1)

    def test_target_fps_zero_raises(self):
        with pytest.raises(ValueError, match="target_fps"):
            FrameExtractor(target_fps=0)

    def test_target_fps_negative_raises(self):
        with pytest.raises(ValueError, match="target_fps"):
            FrameExtractor(target_fps=-5)

    def test_write_metadata_false(self):
        ext = FrameExtractor(write_metadata=False)
        assert ext.write_metadata is False


# ---------------------------------------------------------------------------
# Tests: extract() — jumlah frame dan penamaan file
# ---------------------------------------------------------------------------

class TestFrameExtractionFrameCount:

    def test_frame_count_within_tolerance_30fps_to_25fps(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """
        30-frame video at 30 FPS → duration ~1 sec → expected ~25 frames at 25 FPS.
        Toleransi ±1 karena rounding dalam frame sampling.
        """
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        # Expected: 30 frames sumber / (30/25) = 25 frames
        expected = 25
        assert abs(result.frame_count - expected) <= 1, (
            f"Expected ~{expected} frames, got {result.frame_count}"
        )

    def test_frame_count_exact_25fps_video(
        self, extractor: FrameExtractor, synthetic_video_25fps: Path, tmp_path: Path
    ):
        """Video 25 FPS → semua frame harus diekstrak (interval=1)."""
        output_dir = tmp_path / "frames_25fps"
        result = extractor.extract(synthetic_video_25fps, output_dir)

        # 25 frame video 25fps → 25 frame output (toleransi ±1)
        assert abs(result.frame_count - 25) <= 1

    def test_frame_count_60fps_to_25fps(
        self, extractor: FrameExtractor, synthetic_video_60fps: Path, tmp_path: Path
    ):
        """60-frame video at 60 FPS → duration ~1 sec → expected ~25 frames at 25 FPS."""
        output_dir = tmp_path / "frames_60fps"
        result = extractor.extract(synthetic_video_60fps, output_dir)

        expected = 25
        assert abs(result.frame_count - expected) <= 1

    def test_frame_count_matches_actual_files(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Jumlah frame di result.frame_count harus sesuai file PNG yang ada di disk."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        png_files = list(output_dir.glob("frame_*.png"))
        assert len(png_files) == result.frame_count

    def test_frame_count_matches_files_25fps(
        self, extractor: FrameExtractor, synthetic_video_25fps: Path, tmp_path: Path
    ):
        """Test konsistensi frame_count vs file pada video 25 FPS."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video_25fps, output_dir)

        png_files = list(output_dir.glob("frame_*.png"))
        assert len(png_files) == result.frame_count


# ---------------------------------------------------------------------------
# Tests: penamaan file PNG
# ---------------------------------------------------------------------------

class TestFrameFilenaming:

    def test_frame_files_named_correctly(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """File harus bernama frame_000000.png, frame_000001.png, dst."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        for i in range(result.frame_count):
            expected_name = f"frame_{i:06d}.png"
            assert (output_dir / expected_name).exists(), (
                f"File {expected_name} tidak ditemukan"
            )

    def test_no_gap_in_frame_sequence(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Tidak boleh ada celah dalam urutan frame (0, 1, 2, ... N-1)."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        indices = sorted(
            int(f.stem.split("_")[1])
            for f in output_dir.glob("frame_*.png")
        )
        expected_indices = list(range(result.frame_count))
        assert indices == expected_indices

    def test_frame_files_are_png_format(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Semua file harus berekstensi .png."""
        output_dir = tmp_path / "frames"
        extractor.extract(synthetic_video, output_dir)

        all_files = [f for f in output_dir.iterdir() if f.name.startswith("frame_")]
        assert all(f.suffix == ".png" for f in all_files)

    def test_png_files_are_readable_by_opencv(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Setiap file PNG harus dapat dibaca ulang oleh cv2.imread."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        for i in range(result.frame_count):
            png_path = output_dir / f"frame_{i:06d}.png"
            img = cv2.imread(str(png_path))
            assert img is not None, f"cv2.imread gagal membaca {png_path.name}"
            assert img.ndim == 3  # BGR, 3 channel

    def test_output_dir_created_automatically(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """output_dir harus dibuat otomatis jika belum ada."""
        output_dir = tmp_path / "nested" / "deep" / "output"
        assert not output_dir.exists()

        result = extractor.extract(synthetic_video, output_dir)
        assert output_dir.exists()
        assert result.frame_count > 0


# ---------------------------------------------------------------------------
# Tests: resolusi dan durasi
# ---------------------------------------------------------------------------

class TestResolutionAndDuration:

    def test_resolution_detected_correctly(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Resolusi 64x64 harus terdeteksi dengan benar."""
        video_path = tmp_path / "video_64x64.mp4"
        create_synthetic_video(video_path, fps=25.0, width=64, height=64, num_frames=25)

        result = extractor.extract(video_path, tmp_path / "out")
        assert result.resolution == "64x64"

    def test_resolution_128x96(self, extractor: FrameExtractor, tmp_path: Path):
        """Resolusi berbeda harus terdeteksi dengan benar."""
        video_path = tmp_path / "video_128x96.mp4"
        create_synthetic_video(video_path, fps=25.0, width=128, height=96, num_frames=10)

        result = extractor.extract(video_path, tmp_path / "out")
        assert result.resolution == "128x96"

    def test_resolution_format_is_WxH(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Format resolusi harus 'WxH' (width × height)."""
        result = extractor.extract(synthetic_video, tmp_path / "out")
        parts = result.resolution.split("x")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_duration_is_positive(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Durasi harus bernilai positif."""
        result = extractor.extract(synthetic_video, tmp_path / "out")
        assert result.duration_sec > 0.0

    def test_duration_approximately_correct(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Video 30 frame @ 30 FPS → durasi ~1.0 detik (toleransi ±0.1)."""
        video_path = tmp_path / "video_30frames.mp4"
        create_synthetic_video(video_path, fps=30.0, width=64, height=64, num_frames=30)

        result = extractor.extract(video_path, tmp_path / "out")
        # Durasi = 30 frame / 30 fps = 1.0 detik
        assert abs(result.duration_sec - 1.0) < 0.1, (
            f"Durasi diharapkan ~1.0 detik, dapat {result.duration_sec}"
        )

    def test_duration_longer_video(self, extractor: FrameExtractor, tmp_path: Path):
        """Video 75 frame @ 25 FPS → durasi ~3.0 detik."""
        video_path = tmp_path / "video_75frames.mp4"
        create_synthetic_video(video_path, fps=25.0, width=64, height=64, num_frames=75)

        result = extractor.extract(video_path, tmp_path / "out")
        # Durasi = 75 frame / 25 fps = 3.0 detik
        assert abs(result.duration_sec - 3.0) < 0.15


# ---------------------------------------------------------------------------
# Tests: fps_extracted
# ---------------------------------------------------------------------------

class TestFpsExtracted:

    def test_fps_extracted_equals_target_fps(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """fps_extracted harus selalu sama dengan target_fps (default: 25)."""
        result = extractor.extract(synthetic_video, tmp_path / "out")
        assert result.fps_extracted == float(TARGET_FPS)

    def test_fps_extracted_custom_target(self, tmp_path: Path):
        """fps_extracted harus mencerminkan target_fps yang dikonfigurasi."""
        ext = FrameExtractor(target_fps=15)
        video_path = tmp_path / "vid.mp4"
        create_synthetic_video(video_path, fps=30.0, num_frames=30)

        result = ext.extract(video_path, tmp_path / "out")
        assert result.fps_extracted == 15.0


# ---------------------------------------------------------------------------
# Tests: metadata.jsonl
# ---------------------------------------------------------------------------

class TestMetadataJsonl:

    def test_metadata_file_created(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """metadata.jsonl harus dibuat di output_dir setelah ekstraksi."""
        output_dir = tmp_path / "frames"
        extractor.extract(synthetic_video, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        assert metadata_path.exists()

    def test_metadata_contains_required_fields(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """metadata.jsonl harus memiliki field: video_path, output_dir,
        frame_count, resolution, duration_sec, fps_extracted."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        record = json.loads(metadata_path.read_text(encoding="utf-8").strip())

        assert "video_path" in record
        assert "output_dir" in record
        assert "frame_count" in record
        assert "resolution" in record
        assert "duration_sec" in record
        assert "fps_extracted" in record

    def test_metadata_values_match_result(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Nilai dalam metadata.jsonl harus cocok dengan FrameExtractionResult."""
        output_dir = tmp_path / "frames"
        result = extractor.extract(synthetic_video, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        record = json.loads(metadata_path.read_text(encoding="utf-8").strip())

        assert record["frame_count"] == result.frame_count
        assert record["resolution"] == result.resolution
        assert record["fps_extracted"] == result.fps_extracted
        assert abs(record["duration_sec"] - result.duration_sec) < 1e-5

    def test_metadata_is_valid_json(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        """Setiap baris metadata.jsonl harus valid JSON."""
        output_dir = tmp_path / "frames"
        extractor.extract(synthetic_video, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        for line in metadata_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                obj = json.loads(line)  # tidak boleh raise
                assert isinstance(obj, dict)

    def test_metadata_not_created_when_write_metadata_false(
        self, synthetic_video: Path, tmp_path: Path
    ):
        """Jika write_metadata=False, metadata.jsonl tidak boleh dibuat."""
        ext = FrameExtractor(write_metadata=False)
        output_dir = tmp_path / "frames"
        ext.extract(synthetic_video, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        assert not metadata_path.exists()

    def test_metadata_appended_on_multiple_extractions(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Memanggil extract() dua kali ke output_dir yang sama harus append JSONL."""
        video1 = tmp_path / "v1.mp4"
        video2 = tmp_path / "v2.mp4"
        create_synthetic_video(video1, fps=25.0, num_frames=10)
        create_synthetic_video(video2, fps=25.0, num_frames=10)

        output_dir = tmp_path / "frames"
        extractor.extract(video1, output_dir)
        extractor.extract(video2, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        lines = [l for l in metadata_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# Tests: FrameExtractionResult fields
# ---------------------------------------------------------------------------

class TestFrameExtractionResult:

    def test_result_success_is_true(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        result = extractor.extract(synthetic_video, tmp_path / "out")
        assert result.success is True
        assert result.error is None

    def test_result_video_path_matches(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        result = extractor.extract(synthetic_video, tmp_path / "out")
        assert result.video_path == str(synthetic_video)

    def test_result_output_dir_matches(
        self, extractor: FrameExtractor, synthetic_video: Path, tmp_path: Path
    ):
        output_dir = tmp_path / "out_check"
        result = extractor.extract(synthetic_video, output_dir)
        assert result.output_dir == str(output_dir)


# ---------------------------------------------------------------------------
# Tests: error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:

    def test_file_not_found_raises(self, extractor: FrameExtractor, tmp_path: Path):
        """FileNotFoundError harus di-raise untuk video yang tidak ada."""
        missing = tmp_path / "does_not_exist.mp4"
        with pytest.raises(FileNotFoundError):
            extractor.extract(missing, tmp_path / "out")

    def test_corrupt_file_raises_runtime_error(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """RuntimeError harus di-raise untuk file yang tidak dapat dibuka OpenCV."""
        corrupt = tmp_path / "corrupt.mp4"
        corrupt.write_bytes(b"this is not a valid video file at all")

        with pytest.raises(RuntimeError):
            extractor.extract(corrupt, tmp_path / "out")

    def test_error_message_contains_path(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Pesan FileNotFoundError harus menyebutkan path file."""
        missing = tmp_path / "nonexistent_video.mp4"
        with pytest.raises(FileNotFoundError) as exc_info:
            extractor.extract(missing, tmp_path / "out")
        assert "nonexistent_video.mp4" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Tests: extract_batch()
# ---------------------------------------------------------------------------

class TestExtractBatch:

    def test_batch_returns_results_for_each_video(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """extract_batch harus mengembalikan satu hasil per video."""
        videos = []
        for i in range(3):
            p = tmp_path / f"video_{i}.mp4"
            create_synthetic_video(p, fps=25.0, num_frames=10)
            videos.append(p)

        output_dir = tmp_path / "batch_out"
        results = extractor.extract_batch(videos, output_dir)

        assert len(results) == 3

    def test_batch_each_video_in_subdirectory(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Setiap video harus disimpan dalam subdirektori tersendiri (namafile stem)."""
        videos = []
        for name in ["alpha", "beta", "gamma"]:
            p = tmp_path / f"{name}.mp4"
            create_synthetic_video(p, fps=25.0, num_frames=10)
            videos.append(p)

        output_dir = tmp_path / "batch_out"
        extractor.extract_batch(videos, output_dir)

        for name in ["alpha", "beta", "gamma"]:
            assert (output_dir / name).exists(), (
                f"Subdirektori '{name}' tidak ditemukan"
            )

    def test_batch_all_results_success(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Semua hasil harus success=True untuk video yang valid."""
        videos = []
        for i in range(2):
            p = tmp_path / f"vid_{i}.mp4"
            create_synthetic_video(p, fps=25.0, num_frames=15)
            videos.append(p)

        results = extractor.extract_batch(videos, tmp_path / "out")
        assert all(r.success for r in results)

    def test_batch_missing_video_returns_failure_entry(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Video yang tidak ada harus menghasilkan entry dengan success=False,
        bukan melempar exception ke caller."""
        valid_video = tmp_path / "valid.mp4"
        create_synthetic_video(valid_video, fps=25.0, num_frames=10)

        missing_video = tmp_path / "missing.mp4"

        results = extractor.extract_batch(
            [valid_video, missing_video], tmp_path / "out"
        )

        assert len(results) == 2
        # video valid → sukses
        assert results[0].success is True
        # video hilang → gagal
        assert results[1].success is False
        assert results[1].error is not None

    def test_batch_order_preserved(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Urutan hasil harus sama dengan urutan input video_paths."""
        videos = []
        for name in ["zeta", "alpha", "mu"]:
            p = tmp_path / f"{name}.mp4"
            create_synthetic_video(p, fps=25.0, num_frames=10)
            videos.append(p)

        results = extractor.extract_batch(videos, tmp_path / "out")

        for i, video_path in enumerate(videos):
            assert results[i].video_path == str(video_path)

    def test_batch_empty_list(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """extract_batch dengan list kosong harus mengembalikan list kosong."""
        results = extractor.extract_batch([], tmp_path / "out")
        assert results == []

    def test_batch_metadata_per_video(
        self, extractor: FrameExtractor, tmp_path: Path
    ):
        """Setiap subdirektori harus memiliki metadata.jsonl-nya sendiri."""
        videos = []
        for name in ["clip_a", "clip_b"]:
            p = tmp_path / f"{name}.mp4"
            create_synthetic_video(p, fps=25.0, num_frames=10)
            videos.append(p)

        output_dir = tmp_path / "out"
        extractor.extract_batch(videos, output_dir)

        for name in ["clip_a", "clip_b"]:
            metadata_path = output_dir / name / "metadata.jsonl"
            assert metadata_path.exists(), (
                f"metadata.jsonl tidak ditemukan di {output_dir / name}"
            )


# ---------------------------------------------------------------------------
# Tests: PNG compression parameter
# ---------------------------------------------------------------------------

class TestPngCompression:

    @pytest.mark.parametrize("level", [0, 1, 5, 6, 9])
    def test_valid_compression_levels_accepted(self, level: int, tmp_path: Path):
        """Semua level kompresi 0–9 harus diterima."""
        ext = FrameExtractor(png_compression=level)
        assert ext.png_compression == level

    def test_compression_10_raises_value_error(self):
        """Level 10 harus raise ValueError."""
        with pytest.raises(ValueError):
            FrameExtractor(png_compression=10)

    def test_compression_0_produces_valid_png(self, tmp_path: Path):
        """PNG dengan kompresi 0 harus tetap dapat dibaca."""
        ext = FrameExtractor(png_compression=0)
        video_path = tmp_path / "vid.mp4"
        create_synthetic_video(video_path, fps=25.0, num_frames=5)

        output_dir = tmp_path / "out"
        result = ext.extract(video_path, output_dir)

        assert result.frame_count > 0
        frame = cv2.imread(str(output_dir / "frame_000000.png"))
        assert frame is not None

    def test_compression_9_produces_valid_png(self, tmp_path: Path):
        """PNG dengan kompresi 9 harus tetap dapat dibaca."""
        ext = FrameExtractor(png_compression=9)
        video_path = tmp_path / "vid.mp4"
        create_synthetic_video(video_path, fps=25.0, num_frames=5)

        output_dir = tmp_path / "out"
        result = ext.extract(video_path, output_dir)

        assert result.frame_count > 0
        frame = cv2.imread(str(output_dir / "frame_000000.png"))
        assert frame is not None

    def test_default_compression_is_6(self):
        """Level kompresi default harus 6 sesuai Requirements 1.6."""
        ext = FrameExtractor()
        assert ext.png_compression == 6


# ---------------------------------------------------------------------------
# Tests: Requirement 1.6 khusus
# ---------------------------------------------------------------------------

class TestRequirement16:

    def test_target_fps_constant_is_25(self):
        """Konstanta TARGET_FPS harus 25 (Requirements 1.6)."""
        assert TARGET_FPS == 25

    def test_png_compression_constant_is_6(self):
        """Konstanta PNG_COMPRESSION_LEVEL harus 6 (Requirements 1.6)."""
        assert PNG_COMPRESSION_LEVEL == 6

    def test_default_extractor_uses_25fps(self):
        """FrameExtractor default harus menggunakan 25 FPS."""
        ext = FrameExtractor()
        assert ext.target_fps == 25

    def test_frame_image_dimensions_preserved(self, tmp_path: Path):
        """Dimensi frame yang tersimpan di PNG harus sama dengan resolusi video."""
        video_path = tmp_path / "vid.mp4"
        W, H = 96, 72
        create_synthetic_video(video_path, fps=25.0, width=W, height=H, num_frames=10)

        ext = FrameExtractor()
        output_dir = tmp_path / "out"
        result = ext.extract(video_path, output_dir)

        # Cek dimensi gambar dari file PNG pertama
        img = cv2.imread(str(output_dir / "frame_000000.png"))
        assert img is not None
        assert img.shape[1] == W  # width
        assert img.shape[0] == H  # height

        # Resolusi juga harus dilaporkan dengan benar
        assert result.resolution == f"{W}x{H}"

    def test_metadata_resolution_matches_image_dimensions(self, tmp_path: Path):
        """Resolusi dalam metadata.jsonl harus cocok dengan dimensi frame PNG."""
        video_path = tmp_path / "vid.mp4"
        W, H = 80, 60
        create_synthetic_video(video_path, fps=25.0, width=W, height=H, num_frames=10)

        ext = FrameExtractor()
        output_dir = tmp_path / "out"
        ext.extract(video_path, output_dir)

        metadata_path = output_dir / "metadata.jsonl"
        record = json.loads(metadata_path.read_text(encoding="utf-8").strip())
        assert record["resolution"] == f"{W}x{H}"


# ---------------------------------------------------------------------------
# Property-Based Tests (Hypothesis)
# Validates: Requirements 1.6
# ---------------------------------------------------------------------------

@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    num_frames=st.integers(min_value=5, max_value=50),
    src_fps=st.sampled_from([15.0, 24.0, 25.0, 30.0, 60.0]),
)
def test_property_frame_count_proportional_to_duration(
    tmp_path_factory, num_frames: int, src_fps: float
):
    """
    Property: Jumlah frame yang diekstrak tidak melebihi min(sumber, durasi × target_fps).

    Ketika src_fps <= target_fps, semua frame sumber diambil (tidak ada frame yang
    dilewati). Ketika src_fps > target_fps, frame di-subsample ke target_fps.

    Validates: Requirements 1.6
    """
    tmp_path = tmp_path_factory.mktemp("pbt_fc")
    video_path = tmp_path / "video.mp4"
    create_synthetic_video(video_path, fps=src_fps, width=32, height=32, num_frames=num_frames)

    ext = FrameExtractor(target_fps=25)
    result = ext.extract(video_path, tmp_path / "out")

    # Durasi teoritis
    duration_sec = num_frames / src_fps

    if src_fps <= 25.0:
        # Semua frame diambil (interval = 1.0, tidak ada sub-sampling)
        expected_frames = num_frames
    else:
        # Sub-sampled: ≈ duration × target_fps
        expected_frames = duration_sec * 25

    # Toleransi ±2 untuk rounding dan presisi floating point
    assert abs(result.frame_count - expected_frames) <= 2, (
        f"src={src_fps}fps, {num_frames} frames, duration={duration_sec:.2f}s, "
        f"expected≈{expected_frames:.1f}, got {result.frame_count}"
    )


@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    num_frames=st.integers(min_value=5, max_value=30),
)
def test_property_frame_files_sequential_no_gaps(tmp_path_factory, num_frames: int):
    """
    Property: File frame harus berurutan tanpa celah (frame_000000.png hingga frame_N-1.png).

    Validates: Requirements 1.6
    """
    tmp_path = tmp_path_factory.mktemp("pbt_seq")
    video_path = tmp_path / "video.mp4"
    create_synthetic_video(video_path, fps=25.0, width=32, height=32, num_frames=num_frames)

    ext = FrameExtractor(target_fps=25)
    output_dir = tmp_path / "out"
    result = ext.extract(video_path, output_dir)

    # Kumpulkan indeks dari nama file
    indices = sorted(
        int(f.stem.split("_")[1])
        for f in output_dir.glob("frame_*.png")
    )
    expected = list(range(result.frame_count))
    assert indices == expected, (
        f"Indeks frame tidak berurutan. Expected: {expected[:5]}... Got: {indices[:5]}..."
    )


@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    # Gunakan kelipatan 2 agar cv2.VideoWriter tidak snap ke dimensi berbeda
    # karena banyak codec (termasuk mp4v) memerlukan dimensi genap.
    half_width=st.integers(min_value=16, max_value=64),
    half_height=st.integers(min_value=16, max_value=48),
)
def test_property_resolution_reported_correctly(
    tmp_path_factory, half_width: int, half_height: int
):
    """
    Property: Resolusi yang dilaporkan harus sesuai dengan resolusi video sumber.

    Menggunakan dimensi genap karena codec mp4v membutuhkan dimensi genap.

    Validates: Requirements 1.6
    """
    width = half_width * 2
    height = half_height * 2

    tmp_path = tmp_path_factory.mktemp("pbt_res")
    video_path = tmp_path / "video.mp4"
    create_synthetic_video(
        video_path, fps=25.0, width=width, height=height, num_frames=5
    )

    ext = FrameExtractor()
    result = ext.extract(video_path, tmp_path / "out")

    assert result.resolution == f"{width}x{height}", (
        f"Expected resolution {width}x{height}, got {result.resolution}"
    )


@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
@given(
    num_frames=st.integers(min_value=5, max_value=50),
    src_fps=st.sampled_from([25.0, 30.0]),
)
def test_property_metadata_fields_consistent_with_result(
    tmp_path_factory, num_frames: int, src_fps: float
):
    """
    Property: Semua field dalam metadata.jsonl harus konsisten dengan FrameExtractionResult.

    Validates: Requirements 1.6
    """
    tmp_path = tmp_path_factory.mktemp("pbt_meta")
    video_path = tmp_path / "video.mp4"
    create_synthetic_video(video_path, fps=src_fps, width=32, height=32, num_frames=num_frames)

    ext = FrameExtractor()
    output_dir = tmp_path / "out"
    result = ext.extract(video_path, output_dir)

    metadata_path = output_dir / "metadata.jsonl"
    record = json.loads(metadata_path.read_text(encoding="utf-8").strip())

    assert record["frame_count"] == result.frame_count
    assert record["resolution"] == result.resolution
    assert record["fps_extracted"] == result.fps_extracted
    assert abs(record["duration_sec"] - result.duration_sec) < 1e-5


@settings(max_examples=15, suppress_health_check=[HealthCheck.too_slow])
@given(
    compression=st.integers(min_value=0, max_value=9),
    num_frames=st.integers(min_value=3, max_value=10),
)
def test_property_valid_compression_levels_produce_readable_pngs(
    tmp_path_factory, compression: int, num_frames: int
):
    """
    Property: Semua level kompresi PNG 0–9 harus menghasilkan file PNG yang valid.

    Validates: Requirements 1.6
    """
    tmp_path = tmp_path_factory.mktemp("pbt_comp")
    video_path = tmp_path / "video.mp4"
    create_synthetic_video(video_path, fps=25.0, width=32, height=32, num_frames=num_frames)

    ext = FrameExtractor(png_compression=compression)
    output_dir = tmp_path / "out"
    result = ext.extract(video_path, output_dir)

    # Semua frame harus dapat dibaca ulang
    for i in range(result.frame_count):
        img = cv2.imread(str(output_dir / f"frame_{i:06d}.png"))
        assert img is not None, (
            f"PNG tidak valid pada compression={compression}, frame_{i:06d}.png"
        )
