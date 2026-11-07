"""
validation.py — Validasi anotasi pose keypoints WLASL.

Requirements: 2.2
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Impor DataValidationError dari dataset_downloader agar konsisten dengan
# hierarki exception yang sudah ada di proyek.
from data.dataset_downloader import DataValidationError  # noqa: E402

# ---------------------------------------------------------------------------
# Data class hasil validasi
# ---------------------------------------------------------------------------

@dataclass
class WlaslAnnotationValidationResult:
    """Hasil validasi anotasi pose WLASL."""
    is_valid: bool
    num_annotations: int        # total entri anotasi dalam JSON
    num_videos: int             # total video ditemukan di data_dir (rekursif)
    missing_count: int          # max(0, num_videos - num_annotations)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

# Ekstensi video yang dikenali
_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm"}


class WlaslAnnotationValidator:
    """
    Validasi anotasi pose keypoints WLASL.

    Req 2.2: Verify annotation JSON has entries >= number of downloaded videos.
    """

    def validate(
        self,
        data_dir: Path,
        annotation_json_path: Path,
    ) -> WlaslAnnotationValidationResult:
        """
        Validasi ketersediaan dan kelengkapan anotasi WLASL.

        Parameters
        ----------
        data_dir:
            Direktori berisi video WLASL (struktur: data_dir/<gloss>/<video>.mp4).
            Pencarian video dilakukan secara rekursif.
        annotation_json_path:
            Path ke file anotasi JSON (WLASL_v0.3.json atau file anotasi pose).

        Returns
        -------
        WlaslAnnotationValidationResult
            Hasil validasi dengan is_valid=True jika num_annotations >= num_videos.

        Raises
        ------
        DataValidationError
            - Jika annotation_json_path tidak ditemukan, dengan pesan menyebutkan
              nama file dan jumlah anotasi yang hilang.
            - Jika num_annotations < num_videos, dengan pesan menyebutkan
              num_annotations, num_videos, dan selisihnya.

        Notes
        -----
        Format JSON yang didukung:
        1. WLASL_v0.3.json: list of {"gloss": ..., "instances": [...]}
           → total instances dihitung.
        2. Flat list: list of records (tidak memiliki key "instances")
           → len(list) dihitung.
        """
        annotation_json_path = Path(annotation_json_path)
        data_dir = Path(data_dir)

        # ------------------------------------------------------------------
        # Langkah 1: Periksa keberadaan file anotasi
        # ------------------------------------------------------------------
        if not annotation_json_path.exists():
            # Hitung video agar dapat memberikan pesan yang informatif
            num_videos = self._count_videos(data_dir)
            msg = (
                f"File anotasi tidak ditemukan: '{annotation_json_path.name}'. "
                f"Jumlah anotasi yang hilang: {num_videos}."
            )
            logger.error(msg)
            raise DataValidationError(msg)

        # ------------------------------------------------------------------
        # Langkah 2: Hitung jumlah video di data_dir (rekursif)
        # ------------------------------------------------------------------
        num_videos = self._count_videos(data_dir)
        logger.info("Jumlah video ditemukan di %s: %d", data_dir, num_videos)

        # ------------------------------------------------------------------
        # Langkah 3: Hitung jumlah entri anotasi
        # ------------------------------------------------------------------
        num_annotations = self._count_annotations(annotation_json_path)
        logger.info(
            "Jumlah entri anotasi di %s: %d",
            annotation_json_path.name, num_annotations,
        )

        # ------------------------------------------------------------------
        # Langkah 4: Bandingkan jumlah anotasi dengan jumlah video
        # ------------------------------------------------------------------
        missing_count = max(0, num_videos - num_annotations)

        if num_annotations < num_videos:
            msg = (
                f"Jumlah anotasi tidak mencukupi: ditemukan {num_annotations} anotasi "
                f"tetapi {num_videos} video ada di direktori. "
                f"Selisih (anotasi hilang): {missing_count}."
            )
            logger.error(msg)
            raise DataValidationError(msg)

        # ------------------------------------------------------------------
        # Langkah 5: Validasi berhasil
        # ------------------------------------------------------------------
        logger.info(
            "Validasi anotasi WLASL berhasil: %d anotasi >= %d video.",
            num_annotations, num_videos,
        )
        return WlaslAnnotationValidationResult(
            is_valid=True,
            num_annotations=num_annotations,
            num_videos=num_videos,
            missing_count=0,
            errors=[],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_videos(self, data_dir: Path) -> int:
        """Hitung semua file video (rekursif) dalam data_dir."""
        if not data_dir.exists():
            return 0
        return sum(
            1
            for f in data_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in _VIDEO_EXTENSIONS
        )

    def _count_annotations(self, annotation_json_path: Path) -> int:
        """
        Hitung jumlah entri anotasi dari file JSON.

        Mendukung dua format:
        1. WLASL_v0.3.json: list of {"gloss": ..., "instances": [...]}
           → hitung total instances
        2. Flat list: list of records
           → hitung len(list)
        """
        with open(annotation_json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not isinstance(data, list):
            # Format tidak dikenal — anggap satu entri
            logger.warning(
                "Format JSON tidak dikenal di %s — menggunakan count=1.",
                annotation_json_path.name,
            )
            return 1

        if len(data) == 0:
            return 0

        # Deteksi format WLASL_v0.3.json: elemen pertama memiliki key "instances"
        first = data[0]
        if isinstance(first, dict) and "instances" in first:
            total = sum(len(entry.get("instances", [])) for entry in data)
            return total

        # Flat list format
        return len(data)
