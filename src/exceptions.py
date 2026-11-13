"""
exceptions.py — Hierarki exception terpusat untuk SignBridge BISINDO.

Requirements: 15.3
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class SignBridgeError(Exception):
    """Base exception untuk semua error SignBridge."""


# ---------------------------------------------------------------------------
# Data & Schema errors
# ---------------------------------------------------------------------------

class SchemaValidationError(SignBridgeError):
    """
    Raised ketika file data (.npy atau .jsonl) tidak sesuai skema yang diharapkan.

    Attributes
    ----------
    file_path : Path | str
        Nama atau path file yang bermasalah.
    field_name : str
        Nama field atau dimensi yang tidak valid.
    found_value : Any
        Nilai aktual yang ditemukan (berbeda dari yang diharapkan).
    line_number : int | None
        Nomor baris (1-based) untuk file JSONL; None untuk file .npy.
    """

    def __init__(
        self,
        file_path: Path | str,
        field_name: str,
        found_value: Any,
        line_number: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.file_path = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.field_name = field_name
        self.found_value = found_value
        self.line_number = line_number

        if message is None:
            loc = f" (baris {line_number})" if line_number is not None else ""
            message = (
                f"Validasi skema gagal pada '{self.file_path.name}'{loc}: "
                f"field '{field_name}' memiliki nilai tidak valid: {found_value!r}"
            )
        super().__init__(message)


class DataValidationError(SignBridgeError):
    """
    Raised ketika integritas dataset tidak sesuai ekspektasi (jumlah video, gloss, signer).
    Proses harus dihentikan dan laporan ditulis ke data/validation_errors.txt.
    """


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------

class ConfigValidationError(SignBridgeError):
    """
    Raised ketika parameter konfigurasi berada di luar rentang valid.

    Attributes
    ----------
    param_name : str
        Nama parameter yang bermasalah.
    found_value : Any
        Nilai yang diberikan.
    valid_range : str
        Deskripsi rentang atau nilai yang valid.
    """

    def __init__(
        self,
        param_name: str,
        found_value: Any,
        valid_range: str,
        message: Optional[str] = None,
    ) -> None:
        self.param_name = param_name
        self.found_value = found_value
        self.valid_range = valid_range

        if message is None:
            message = (
                f"Konfigurasi tidak valid: parameter '{param_name}' = {found_value!r} "
                f"berada di luar rentang valid {valid_range}"
            )
        super().__init__(message)


# ---------------------------------------------------------------------------
# Graph errors
# ---------------------------------------------------------------------------

class GraphConfigError(SignBridgeError):
    """
    Raised ketika konfigurasi Keypoint_Graph tidak valid
    (node index di luar rentang, isolated node, dll.).
    """


# ---------------------------------------------------------------------------
# Checkpoint / training errors
# ---------------------------------------------------------------------------

class CheckpointNotFoundError(SignBridgeError):
    """Raised ketika path checkpoint --resume tidak ditemukan."""


# ---------------------------------------------------------------------------
# Hardware / inference errors
# ---------------------------------------------------------------------------

class WebcamError(SignBridgeError):
    """Raised ketika webcam tidak terdeteksi."""


class CameraPermissionError(SignBridgeError):
    """Raised ketika getUserMedia ditolak oleh browser."""


class InferenceInitError(SignBridgeError):
    """Raised ketika MediaPipe atau ONNX Runtime gagal diinisialisasi dalam < 5 detik."""
