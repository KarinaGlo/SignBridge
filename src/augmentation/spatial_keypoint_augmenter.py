"""
spatial_keypoint_augmenter.py — Augmentasi spasial untuk sekuens keypoint.

Layout MediaPipe:
  [0:21]   — tangan kiri (21 keypoint)
  [21:42]  — tangan kanan (21 keypoint)
  [42:75]  — pose tubuh (33 keypoint)
  [75:543] — wajah (468 keypoint)

Requirements: 5.2, 5.4
"""

from __future__ import annotations

import math

import numpy as np

# Indeks slice tangan sesuai layout MediaPipe Holistic
LEFT_HAND_SLICE = slice(0, 21)
RIGHT_HAND_SLICE = slice(21, 42)


class SpatialKeypointAugmenter:
    """
    Augmentasi spasial untuk sekuens keypoint skeleton.

    Operasi yang didukung:
    - Horizontal flip (dengan swap label tangan kiri/kanan)
    - Rotasi 2D
    - Penambahan noise Gaussian
    """

    def __init__(
        self,
        flip_prob: float = 0.5,
        rotation_range: tuple[float, float] = (-15.0, 15.0),
        noise_std: float = 0.02,
        seed: int | None = None,
    ) -> None:
        self.flip_prob = flip_prob
        self.rotation_range = rotation_range
        self.noise_std = noise_std
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def flip(self, sequence: np.ndarray) -> tuple[np.ndarray, bool]:
        """
        Horizontal flip pada sekuens keypoint.

        Langkah:
        1. Negatifkan koordinat x: sequence[:, :, 0] = -sequence[:, :, 0]
        2. Tukar tangan kiri [0:21] ↔ tangan kanan [21:42]

        Property: flip(flip(seq)) == seq (involusi)

        Parameters
        ----------
        sequence : np.ndarray
            Array keypoint dengan shape [T, K, 3].

        Returns
        -------
        tuple[np.ndarray, bool]
            (sekuens yang di-flip, True)
        """
        out = sequence.copy()

        # 1. Negatifkan koordinat x
        out[:, :, 0] = -out[:, :, 0]

        # 2. Tukar tangan kiri ↔ tangan kanan
        left = out[:, LEFT_HAND_SLICE, :].copy()
        right = out[:, RIGHT_HAND_SLICE, :].copy()
        out[:, LEFT_HAND_SLICE, :] = right
        out[:, RIGHT_HAND_SLICE, :] = left

        return out, True

    def rotate_2d(
        self,
        sequence: np.ndarray,
        angle_deg: float | None = None,
    ) -> np.ndarray:
        """
        Rotasi koordinat (x, y) sebesar angle_deg. Koordinat z tidak berubah.
        R = [[cos θ, -sin θ], [sin θ, cos θ]]
        Hasil di-clip ke [-1, 1].

        Parameters
        ----------
        sequence : np.ndarray
            Array keypoint dengan shape [T, K, 3].
        angle_deg : float | None
            Sudut rotasi dalam derajat. Jika None, disample dari rotation_range.

        Returns
        -------
        np.ndarray
            Array keypoint yang dirotasi dengan shape [T, K, 3].
        """
        if angle_deg is None:
            angle_deg = float(
                self.rng.uniform(self.rotation_range[0], self.rotation_range[1])
            )

        theta = math.radians(angle_deg)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        out = sequence.copy()
        x = sequence[:, :, 0]
        y = sequence[:, :, 1]

        out[:, :, 0] = cos_t * x - sin_t * y
        out[:, :, 1] = sin_t * x + cos_t * y

        # Clip ke [-1, 1]
        out = np.clip(out, -1.0, 1.0)
        return out

    def add_gaussian_noise(
        self,
        sequence: np.ndarray,
        std: float | None = None,
    ) -> np.ndarray:
        """
        Tambahkan noise N(0, std) ke semua koordinat. Clip ke [-1, 1].

        Parameters
        ----------
        sequence : np.ndarray
            Array keypoint dengan shape [T, K, 3].
        std : float | None
            Standar deviasi noise. Jika None, gunakan self.noise_std.

        Returns
        -------
        np.ndarray
            Array keypoint dengan noise ditambahkan.
        """
        if std is None:
            std = self.noise_std

        noise = self.rng.normal(0.0, std, size=sequence.shape).astype(sequence.dtype)
        out = sequence + noise
        out = np.clip(out, -1.0, 1.0)
        return out

    def augment(
        self,
        sequence: np.ndarray,
        rng: np.random.Generator | None = None,
    ) -> tuple[np.ndarray, bool]:
        """
        Terapkan flip (dengan flip_prob), rotate, dan noise.

        Parameters
        ----------
        sequence : np.ndarray
            Array keypoint dengan shape [T, K, 3].
        rng : np.random.Generator | None
            Generator acak opsional. Jika None, gunakan self.rng.

        Returns
        -------
        tuple[np.ndarray, bool]
            (sekuens yang di-augmentasi, was_flipped)
        """
        _rng = rng if rng is not None else self.rng

        was_flipped = False
        out = sequence

        if float(_rng.random()) < self.flip_prob:
            out, was_flipped = self.flip(out)

        out = self.rotate_2d(out)
        out = self.add_gaussian_noise(out)

        return out, was_flipped
