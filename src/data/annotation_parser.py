"""
annotation_parser.py — Parser dan serializer untuk file anotasi .jsonl.

Implementasi AnnotationParser yang:
  - Memuat setiap baris dari file .jsonl dan memvalidasi field wajib + tipe data.
  - Menyimpan list[VideoMetadata] ke file .jsonl yang valid.
  - Raise SchemaValidationError dengan detail lengkap untuk setiap baris bermasalah.

Requirements: 1.5, 15.2, 15.3, 15.4
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.data.models import VideoMetadata
from src.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: frozenset[str] = frozenset({"path", "gloss", "signer_id", "split"})
VALID_SPLITS: frozenset[str] = frozenset({"train", "val", "test"})

# Field opsional dan tipe yang diharapkan
OPTIONAL_FIELDS: dict[str, type] = {
    "duration_sec": (float, int),  # type: ignore[assignment]
    "resolution": str,
    "fps": (float, int),           # type: ignore[assignment]
}


# ---------------------------------------------------------------------------
# AnnotationParser
# ---------------------------------------------------------------------------

class AnnotationParser:
    """
    Parser dan validator untuk file anotasi .jsonl.

    Setiap baris dalam file harus berupa objek JSON valid dengan field wajib:
      - path     : string
      - gloss    : string
      - signer_id: string
      - split    : "train" | "val" | "test"

    Field opsional (duration_sec, resolution, fps) akan dibaca jika ada.
    """

    REQUIRED_FIELDS: frozenset[str] = REQUIRED_FIELDS
    VALID_SPLITS: frozenset[str] = VALID_SPLITS

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, path: Path) -> list[VideoMetadata]:
        """
        Load file .jsonl, validasi setiap baris, dan kembalikan list VideoMetadata.

        Parameters
        ----------
        path : Path
            Path ke file .jsonl yang akan dimuat.

        Returns
        -------
        list[VideoMetadata]
            Daftar metadata video yang sudah tervalidasi.

        Raises
        ------
        SchemaValidationError
            Jika ada baris yang tidak memiliki field wajib, memiliki tipe data salah,
            atau memiliki nilai split yang tidak valid. Error dilempar pada baris
            pertama yang bermasalah dengan detail: nama file, nomor baris, field
            bermasalah, dan nilai yang ditemukan.
        FileNotFoundError
            Jika path tidak ditemukan.
        """
        path = Path(path)
        records: list[VideoMetadata] = []

        with path.open("r", encoding="utf-8") as fh:
            for line_number, raw_line in enumerate(fh, start=1):
                raw_line = raw_line.strip()
                if not raw_line:
                    # Lewati baris kosong
                    continue

                # 1. Parse JSON
                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise SchemaValidationError(
                        file_path=path,
                        field_name="<json>",
                        found_value=raw_line[:120],
                        line_number=line_number,
                        message=(
                            f"Baris {line_number} pada '{path.name}' bukan JSON valid: {exc}"
                        ),
                    ) from exc

                # 2. Pastikan data adalah objek (dict)
                if not isinstance(data, dict):
                    raise SchemaValidationError(
                        file_path=path,
                        field_name="<root>",
                        found_value=type(data).__name__,
                        line_number=line_number,
                        message=(
                            f"Baris {line_number} pada '{path.name}' harus berupa objek JSON, "
                            f"bukan {type(data).__name__!r}"
                        ),
                    )

                # 3. Validasi field wajib hadir dan bertipe string
                for field_name in sorted(REQUIRED_FIELDS):  # sorted untuk pesan deterministik
                    if field_name not in data:
                        raise SchemaValidationError(
                            file_path=path,
                            field_name=field_name,
                            found_value=None,
                            line_number=line_number,
                            message=(
                                f"Baris {line_number} pada '{path.name}': "
                                f"field wajib '{field_name}' tidak ditemukan"
                            ),
                        )
                    value = data[field_name]
                    if not isinstance(value, str):
                        raise SchemaValidationError(
                            file_path=path,
                            field_name=field_name,
                            found_value=value,
                            line_number=line_number,
                            message=(
                                f"Baris {line_number} pada '{path.name}': "
                                f"field '{field_name}' harus string, ditemukan "
                                f"{type(value).__name__!r} dengan nilai {value!r}"
                            ),
                        )

                # 4. Validasi nilai split
                split_val: str = data["split"]
                if split_val not in VALID_SPLITS:
                    raise SchemaValidationError(
                        file_path=path,
                        field_name="split",
                        found_value=split_val,
                        line_number=line_number,
                        message=(
                            f"Baris {line_number} pada '{path.name}': "
                            f"nilai split '{split_val}' tidak valid. "
                            f"Nilai yang diizinkan: {sorted(VALID_SPLITS)}"
                        ),
                    )

                # 5. Baca field opsional
                duration_sec: Optional[float] = None
                resolution: Optional[str] = None
                fps: Optional[float] = None

                if "duration_sec" in data:
                    raw_dur = data["duration_sec"]
                    if raw_dur is not None:
                        if not isinstance(raw_dur, (int, float)):
                            raise SchemaValidationError(
                                file_path=path,
                                field_name="duration_sec",
                                found_value=raw_dur,
                                line_number=line_number,
                            )
                        duration_sec = float(raw_dur)

                if "resolution" in data:
                    raw_res = data["resolution"]
                    if raw_res is not None:
                        if not isinstance(raw_res, str):
                            raise SchemaValidationError(
                                file_path=path,
                                field_name="resolution",
                                found_value=raw_res,
                                line_number=line_number,
                            )
                        resolution = raw_res

                if "fps" in data:
                    raw_fps = data["fps"]
                    if raw_fps is not None:
                        if not isinstance(raw_fps, (int, float)):
                            raise SchemaValidationError(
                                file_path=path,
                                field_name="fps",
                                found_value=raw_fps,
                                line_number=line_number,
                            )
                        fps = float(raw_fps)

                # 6. Konstruksi VideoMetadata
                records.append(
                    VideoMetadata(
                        path=data["path"],
                        gloss=data["gloss"],
                        signer_id=data["signer_id"],
                        split=data["split"],
                        duration_sec=duration_sec,
                        resolution=resolution,
                        fps=fps,
                    )
                )

        logger.debug("Loaded %d records from '%s'", len(records), path.name)
        return records

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, records: list[VideoMetadata], path: Path) -> None:
        """
        Serialisasi list VideoMetadata ke file JSON Lines (.jsonl).

        Setiap baris berupa satu objek JSON valid. Field opsional yang bernilai
        None tidak disertakan dalam output.

        Parameters
        ----------
        records : list[VideoMetadata]
            Daftar metadata video yang akan disimpan.
        path : Path
            Path tujuan file .jsonl. Direktori induk akan dibuat jika belum ada.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                obj: dict = {
                    "path": record.path,
                    "gloss": record.gloss,
                    "signer_id": record.signer_id,
                    "split": record.split,
                }
                # Sertakan field opsional hanya jika bukan None
                if record.duration_sec is not None:
                    obj["duration_sec"] = record.duration_sec
                if record.resolution is not None:
                    obj["resolution"] = record.resolution
                if record.fps is not None:
                    obj["fps"] = record.fps

                fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

        logger.debug("Saved %d records to '%s'", len(records), path.name)


# ---------------------------------------------------------------------------
# AnnotationSerializer (alias untuk kompatibilitas nama dalam design doc)
# ---------------------------------------------------------------------------

AnnotationSerializer = AnnotationParser
