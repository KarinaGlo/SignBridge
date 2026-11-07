"""
frame_extractor.py — Ekstraksi frame video ke PNG untuk SignBridge BISINDO.

Mengekstrak frame video pada 25 FPS dan menyimpannya sebagai file PNG
dengan compression level 6 (Requirements 1.6).
Metadata resolusi dan durasi video disimpan ke JSONL.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2

logger = logging.getLogger(__name__)

# ── Konstanta ──────────────────────────────────────────────────────────────────
TARGET_FPS: int = 25
PNG_COMPRESSION_LEVEL: int = 6  # skala 0–9 sesuai Requirements 1.6


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class FrameExtractionResult:
    """Hasil ekstraksi frame dari satu file video."""

    video_path: str
    """Path absolut video sumber."""

    output_dir: str
    """Direktori tempat frame PNG disimpan."""

    frame_count: int
    """Jumlah frame yang berhasil diekstrak dan disimpan."""

    resolution: str
    """Resolusi video dalam format 'WxH' (contoh: '640x480')."""

    duration_sec: float
    """Durasi video dalam detik."""

    fps_extracted: float
    """FPS yang digunakan saat ekstraksi (selalu TARGET_FPS = 25)."""

    success: bool = True
    """True jika ekstraksi berhasil tanpa error fatal."""

    error: Optional[str] = None
    """Pesan error jika extraction gagal; None jika berhasil."""


@dataclass
class BatchExtractionReport:
    """Laporan hasil batch extraction."""

    total: int
    """Jumlah video yang diproses."""

    succeeded: int
    """Jumlah video yang berhasil diekstrak."""

    failed: int
    """Jumlah video yang gagal diekstrak."""

    results: list[FrameExtractionResult] = field(default_factory=list)
    """Daftar hasil per video."""


# ── FrameExtractor ─────────────────────────────────────────────────────────────

class FrameExtractor:
    """
    Ekstraksi frame video ke PNG pada 25 FPS dengan compression level 6.

    Sesuai Requirements 1.6:
    - Frame diekstrak pada 25 FPS
    - Disimpan sebagai PNG dengan cv2.IMWRITE_PNG_COMPRESSION = 6
    - Metadata (resolusi, durasi) dicatat ke JSONL

    Contoh penggunaan::

        extractor = FrameExtractor()
        result = extractor.extract(
            video_path=Path("data/raw/MAKAN_s01_001.mp4"),
            output_dir=Path("data/frames/MAKAN_s01_001")
        )
        print(result.frame_count, result.resolution, result.duration_sec)
    """

    def __init__(
        self,
        target_fps: int = TARGET_FPS,
        png_compression: int = PNG_COMPRESSION_LEVEL,
        write_metadata: bool = True,
    ) -> None:
        """
        Args:
            target_fps: FPS target untuk ekstraksi frame (default: 25).
            png_compression: Level kompresi PNG 0–9 (default: 6).
            write_metadata: Jika True, tulis metadata ke JSONL di output_dir.
        """
        if not 0 <= png_compression <= 9:
            raise ValueError(
                f"png_compression harus dalam rentang [0, 9], "
                f"diberikan: {png_compression}"
            )
        if target_fps <= 0:
            raise ValueError(
                f"target_fps harus > 0, diberikan: {target_fps}"
            )

        self.target_fps = target_fps
        self.png_compression = png_compression
        self.write_metadata = write_metadata

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract(
        self,
        video_path: Path,
        output_dir: Path,
    ) -> FrameExtractionResult:
        """
        Ekstrak frame dari satu video pada target_fps, simpan sebagai PNG.

        Frame diberi nama berurutan: ``frame_000000.png``, ``frame_000001.png``, dst.
        Jika write_metadata=True, metadata video ditambahkan ke
        ``<output_dir>/metadata.jsonl``.

        Args:
            video_path: Path ke file video sumber.
            output_dir: Direktori output untuk frame PNG.
                        Dibuat otomatis jika belum ada.

        Returns:
            FrameExtractionResult dengan frame_count, resolution, duration_sec,
            dan fps_extracted.

        Raises:
            FileNotFoundError: Jika video_path tidak ada.
            RuntimeError: Jika video tidak dapat dibuka oleh OpenCV.
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)

        if not video_path.exists():
            raise FileNotFoundError(
                f"File video tidak ditemukan: {video_path}"
            )

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(
                f"Tidak dapat membuka video: {video_path}"
            )

        try:
            result = self._extract_from_cap(cap, video_path, output_dir)
        finally:
            cap.release()

        if self.write_metadata and result.success:
            self._append_metadata(result, output_dir)

        return result

    def extract_batch(
        self,
        video_paths: list[Path],
        output_dir: Path,
    ) -> list[FrameExtractionResult]:
        """
        Batch extraction: ekstrak frame dari banyak video.

        Setiap video disimpan dalam subdirektori tersendiri di output_dir,
        menggunakan stem (nama tanpa ekstensi) video sebagai nama subdirektori.

        Args:
            video_paths: Daftar path ke file video.
            output_dir: Direktori root output. Subdirektori dibuat per video.

        Returns:
            List of FrameExtractionResult, satu per video (urutan sama dengan
            video_paths). Video yang gagal tetap menghasilkan entry dengan
            success=False.
        """
        output_dir = Path(output_dir)
        results: list[FrameExtractionResult] = []

        for video_path in video_paths:
            video_path = Path(video_path)
            video_output_dir = output_dir / video_path.stem

            try:
                result = self.extract(video_path, video_output_dir)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Gagal mengekstrak %s: %s", video_path, exc
                )
                result = FrameExtractionResult(
                    video_path=str(video_path),
                    output_dir=str(video_output_dir),
                    frame_count=0,
                    resolution="0x0",
                    duration_sec=0.0,
                    fps_extracted=float(self.target_fps),
                    success=False,
                    error=str(exc),
                )

            results.append(result)
            logger.info(
                "[%s/%s] %s → %d frame",
                len(results),
                len(video_paths),
                video_path.name,
                result.frame_count,
            )

        return results

    # ── Private helpers ────────────────────────────────────────────────────────

    def _extract_from_cap(
        self,
        cap: cv2.VideoCapture,
        video_path: Path,
        output_dir: Path,
    ) -> FrameExtractionResult:
        """Lakukan ekstraksi dari VideoCapture yang sudah terbuka."""

        # Baca properti video sumber
        src_fps: float = cap.get(cv2.CAP_PROP_FPS)
        total_frames: int = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Hitung durasi; hindari division-by-zero
        if src_fps > 0 and total_frames > 0:
            duration_sec = total_frames / src_fps
        else:
            duration_sec = 0.0

        resolution = f"{width}x{height}"

        # Hitung interval frame: ambil 1 frame setiap N frame sumber
        # Jika src_fps <= target_fps, ambil semua frame
        if src_fps > 0 and src_fps > self.target_fps:
            frame_interval = src_fps / self.target_fps
        else:
            frame_interval = 1.0

        output_dir.mkdir(parents=True, exist_ok=True)

        frame_count = 0
        src_frame_index = 0
        next_target_index = 0.0  # indeks sumber float berikutnya yang perlu diambil

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Ambil frame ini jika indeks sumber mencapai/melewati next_target_index
            if src_frame_index >= next_target_index:
                out_path = output_dir / f"frame_{frame_count:06d}.png"
                cv2.imwrite(
                    str(out_path),
                    frame,
                    [cv2.IMWRITE_PNG_COMPRESSION, self.png_compression],
                )
                frame_count += 1
                next_target_index += frame_interval

            src_frame_index += 1

        return FrameExtractionResult(
            video_path=str(video_path),
            output_dir=str(output_dir),
            frame_count=frame_count,
            resolution=resolution,
            duration_sec=round(duration_sec, 6),
            fps_extracted=float(self.target_fps),
            success=True,
            error=None,
        )

    def _append_metadata(
        self,
        result: FrameExtractionResult,
        output_dir: Path,
    ) -> None:
        """Tambahkan satu baris metadata ke <output_dir>/metadata.jsonl."""
        metadata_path = output_dir / "metadata.jsonl"
        record = {
            "video_path": result.video_path,
            "output_dir": result.output_dir,
            "frame_count": result.frame_count,
            "resolution": result.resolution,
            "duration_sec": result.duration_sec,
            "fps_extracted": result.fps_extracted,
        }
        with metadata_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
