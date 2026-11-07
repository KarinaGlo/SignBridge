"""
keypoint_parser.py — Parser, validator, dan serializer untuk array keypoint .npy.

Requirements: 15.1, 15.3
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from src.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------

NUM_KEYPOINTS = 543
NUM_COORDS = 3
T_MIN = 1
T_MAX = 10_000
DTYPE = np.float32
VALUE_MIN = -1.0
VALUE_MAX = 1.0


# ---------------------------------------------------------------------------
# KeypointParser
# ---------------------------------------------------------------------------

class KeypointParser:
    """
    Parser dan validator untuk file keypoint .npy.

    Schema yang valid:
    - Shape: [T, 543, 3], T ∈ [1, 10000]
    - dtype: float32
    - Values: ∈ [-1.0, 1.0]  (NaN dianggap tidak valid)

    Requirements 15.1: Validates shape, dtype, value range.
    Requirements 15.3: Raises SchemaValidationError dengan field_name
                       (the constraint that failed) dan found_value.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, path: Path) -> np.ndarray:
        """
        Load dan validasi array keypoint dari file .npy.

        Parameters
        ----------
        path : Path
            Path ke file .npy yang akan dimuat.

        Returns
        -------
        np.ndarray
            Array [T, 543, 3] float32 yang sudah tervalidasi.

        Raises
        ------
        FileNotFoundError
            Jika file tidak ditemukan.
        SchemaValidationError
            Jika shape, dtype, atau nilai tidak valid.
            - field_name = "shape"  → shape tidak sesuai [T, 543, 3]
            - field_name = "dtype"  → dtype bukan float32
            - field_name = "values" → ada nilai di luar [-1.0, 1.0] atau NaN
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File keypoint tidak ditemukan: {path}")

        array: np.ndarray = np.load(str(path))
        self.validate(array, file_path=path)
        logger.debug("Loaded keypoint array %s from '%s'", array.shape, path.name)
        return array

    def save(self, array: np.ndarray, path: Path) -> None:
        """
        Validasi dan simpan array keypoint ke file .npy.

        Validasi dilakukan sebelum penyimpanan. Direktori induk dibuat
        otomatis jika belum ada.

        Parameters
        ----------
        array : np.ndarray
            Array keypoint yang akan disimpan.
        path : Path
            Path tujuan file .npy.

        Raises
        ------
        SchemaValidationError
            Jika array tidak valid (shape, dtype, atau nilai salah).
        """
        path = Path(path)
        self.validate(array, file_path=path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(path), array)
        logger.debug("Saved keypoint array %s to '%s'", array.shape, path.name)

    def validate(self, array: np.ndarray, file_path: Path | None = None) -> None:
        """
        Validasi array keypoint tanpa load/save.

        Urutan pemeriksaan: shape → dtype → values.

        Parameters
        ----------
        array : np.ndarray
            Array yang akan divalidasi.
        file_path : Path | None
            Path file sumber (untuk pesan error). Gunakan Path("<unknown>")
            jika tidak ada path.

        Raises
        ------
        SchemaValidationError
            Jika array tidak sesuai skema yang diharapkan.
        """
        fp = Path(file_path) if file_path is not None else Path("<unknown>")

        # 1. Shape check: (T, 543, 3) dengan T ∈ [T_MIN, T_MAX]
        if not (
            array.ndim == 3
            and array.shape[1] == NUM_KEYPOINTS
            and array.shape[2] == NUM_COORDS
            and T_MIN <= array.shape[0] <= T_MAX
        ):
            raise SchemaValidationError(
                file_path=fp,
                field_name="shape",
                found_value=str(array.shape),
                message=(
                    f"Validasi skema gagal pada '{fp.name}': "
                    f"shape harus [T, {NUM_KEYPOINTS}, {NUM_COORDS}] "
                    f"dengan T ∈ [{T_MIN}, {T_MAX}], "
                    f"ditemukan {array.shape!s}"
                ),
            )

        # 2. Dtype check: float32
        if array.dtype != np.float32:
            raise SchemaValidationError(
                file_path=fp,
                field_name="dtype",
                found_value=str(array.dtype),
                message=(
                    f"Validasi skema gagal pada '{fp.name}': "
                    f"dtype harus float32, ditemukan {array.dtype!s}"
                ),
            )

        # 3. Value range check: [-1.0, 1.0], NaN dianggap tidak valid
        #    np.nanmin/nanmax agar kita bisa melaporkan nilai aktual,
        #    kemudian cek NaN secara terpisah.
        has_nan = bool(np.any(np.isnan(array)))
        arr_min = float(np.nanmin(array)) if not (array.size == 0) else 0.0
        arr_max = float(np.nanmax(array)) if not (array.size == 0) else 0.0

        if has_nan or arr_min < VALUE_MIN or arr_max > VALUE_MAX:
            if has_nan:
                found_str = "min=nan, max=nan"
            else:
                found_str = f"min={arr_min:.4f}, max={arr_max:.4f}"
            raise SchemaValidationError(
                file_path=fp,
                field_name="values",
                found_value=found_str,
                message=(
                    f"Validasi skema gagal pada '{fp.name}': "
                    f"nilai harus ∈ [{VALUE_MIN}, {VALUE_MAX}] dan tidak NaN, "
                    f"ditemukan {found_str}"
                ),
            )
