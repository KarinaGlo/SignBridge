"""
temporal_augmenter.py — Augmentasi temporal untuk sekuens keypoint/frame.

Requirements: 5.1
"""

from __future__ import annotations

import math

import numpy as np


class TemporalAugmenter:
    """
    Augmentasi temporal untuk sekuens frame:
    - Speed perturbation (resampling dengan faktor kecepatan)
    - Random frame dropping
    - Temporal jitter (offset frame)
    """

    def __init__(
        self,
        speed_range: tuple[float, float] = (0.7, 1.3),
        max_frame_drop_ratio: float = 0.20,
        max_temporal_jitter: int = 3,
        seed: int | None = None,
    ) -> None:
        self.speed_range = speed_range
        self.max_frame_drop_ratio = max_frame_drop_ratio
        self.max_temporal_jitter = max_temporal_jitter
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def speed_perturbation(
        self,
        sequence: np.ndarray,
        speed_factor: float | None = None,
    ) -> np.ndarray:
        """
        Resample sequence pada faktor kecepatan speed_factor s ∈ speed_range.
        Panjang output = floor(T / s).
        Interpolasi linear antara frame menggunakan np.interp pada setiap fitur.

        Parameters
        ----------
        sequence : np.ndarray
            Array input dengan shape [T, ...].
        speed_factor : float | None
            Faktor kecepatan. Jika None, disample secara uniform dari speed_range.

        Returns
        -------
        np.ndarray
            Array dengan shape [floor(T/s), ...].
        """
        if speed_factor is None:
            speed_factor = float(
                self.rng.uniform(self.speed_range[0], self.speed_range[1])
            )

        T = len(sequence)
        n_out = max(1, int(math.floor(T / speed_factor)))
        src_indices = np.linspace(0, T - 1, n_out)

        out = np.zeros((n_out,) + sequence.shape[1:], dtype=sequence.dtype)
        for i, idx in enumerate(src_indices):
            lo = int(math.floor(idx))
            hi = min(int(math.ceil(idx)), T - 1)
            frac = idx - lo
            out[i] = sequence[lo] * (1.0 - frac) + sequence[hi] * frac

        return out

    def random_frame_drop(
        self,
        sequence: np.ndarray,
        drop_ratio: float | None = None,
    ) -> np.ndarray:
        """
        Drop subset acak dari frame.
        Frame yang dipertahankan = ceil(T * (1 - drop_ratio)).
        Jika drop_ratio adalah None, disample dari [0, max_frame_drop_ratio].

        Parameters
        ----------
        sequence : np.ndarray
            Array input dengan shape [T, ...].
        drop_ratio : float | None
            Proporsi frame yang di-drop. Jika None, disample secara acak.

        Returns
        -------
        np.ndarray
            Frame yang dipertahankan dalam urutan asli.
        """
        if drop_ratio is None:
            drop_ratio = float(self.rng.uniform(0.0, self.max_frame_drop_ratio))

        T = len(sequence)
        n_retain = math.ceil(T * (1.0 - drop_ratio))
        n_retain = max(1, min(n_retain, T))

        # Pilih indeks secara acak tanpa penggantian, lalu urutkan
        chosen = self.rng.choice(T, size=n_retain, replace=False)
        chosen.sort()
        return sequence[chosen]

    def temporal_jitter(
        self,
        sequence: np.ndarray,
        offset: int | None = None,
    ) -> np.ndarray:
        """
        Geser sekuens sebesar offset frame. Zero-pad sesuai kebutuhan.
        Jika offset adalah None, disample dari [-max_temporal_jitter, max_temporal_jitter].

        Parameters
        ----------
        sequence : np.ndarray
            Array input dengan shape [T, ...].
        offset : int | None
            Jumlah frame untuk digeser (positif = geser maju, negatif = geser mundur).

        Returns
        -------
        np.ndarray
            Sekuens yang digeser dengan shape yang sama [T, ...].
        """
        if offset is None:
            offset = int(
                self.rng.integers(
                    -self.max_temporal_jitter,
                    self.max_temporal_jitter + 1,
                )
            )

        T = len(sequence)
        out = np.zeros_like(sequence)

        if offset >= 0:
            # Geser ke kanan: frame mulai dari posisi offset
            src_end = min(T - offset, T)
            if src_end > 0:
                out[offset : offset + src_end] = sequence[:src_end]
        else:
            # Geser ke kiri: mulai dari -offset
            src_start = -offset
            n_copy = T - src_start
            if n_copy > 0:
                out[:n_copy] = sequence[src_start : src_start + n_copy]

        return out
