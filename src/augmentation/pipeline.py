"""
pipeline.py — Orkestrasi pipeline augmentasi data.

Rules:
- split ∈ {val, test} OR enabled=False: identity deterministik (tidak ada transformasi acak)
- split=train AND enabled=True: terapkan semua augmentasi dengan parameter acak

Requirements: 5.5, 5.6
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.augmentation.temporal_augmenter import TemporalAugmenter
from src.augmentation.spatial_keypoint_augmenter import SpatialKeypointAugmenter
from src.augmentation.spatial_rgb_augmenter import SpatialRGBAugmenter


@dataclass
class AugmentationConfig:
    """Konfigurasi untuk AugmentationPipeline."""

    enabled: bool = True
    split: str = "train"
    seed: Optional[int] = None


@dataclass
class AugmentationSample:
    """Sampel input/output untuk AugmentationPipeline."""

    keypoints: np.ndarray           # [T, 543, 3] float32
    frames: Optional[np.ndarray] = None  # [T, H, W, 3] float32


class AugmentationPipeline:
    """
    Pipeline augmentasi yang dikonfigurasi via AugmentationConfig.

    - split ∈ {val, test} OR enabled=False:
        identity deterministik — hanya kembalikan salinan input tanpa transformasi acak.
    - split=train AND enabled=True:
        terapkan TemporalAugmenter + SpatialKeypointAugmenter + SpatialRGBAugmenter.
    """

    _NON_TRAIN_SPLITS = {"val", "test"}

    def __init__(self, config: AugmentationConfig) -> None:
        self.config = config
        self._is_active = config.enabled and config.split not in self._NON_TRAIN_SPLITS

        if self._is_active:
            self._temporal = TemporalAugmenter(seed=config.seed)
            self._spatial_kp = SpatialKeypointAugmenter(seed=config.seed)
            self._spatial_rgb = SpatialRGBAugmenter(seed=config.seed)

    # ------------------------------------------------------------------
    # Callable interface
    # ------------------------------------------------------------------

    def __call__(self, sample: AugmentationSample) -> AugmentationSample:
        """
        Proses satu sampel.

        Untuk val/test atau pipeline dinonaktifkan:
            Kembalikan salinan keypoints tanpa transformasi acak apapun.

        Untuk train+enabled:
            Terapkan augmentasi temporal + spasial.

        Parameters
        ----------
        sample : AugmentationSample
            Sampel input yang berisi keypoints dan (opsional) frames.

        Returns
        -------
        AugmentationSample
            Sampel yang diproses.
        """
        if not self._is_active:
            # Identity — kembalikan salinan tanpa randomness
            return AugmentationSample(
                keypoints=sample.keypoints.copy(),
                frames=sample.frames.copy() if sample.frames is not None else None,
            )

        # --- Augmentasi temporal pada keypoints ---
        kp = self._temporal.speed_perturbation(sample.keypoints)
        kp = self._temporal.random_frame_drop(kp)
        kp = self._temporal.temporal_jitter(kp)

        # --- Augmentasi spasial keypoints ---
        kp, was_flipped = self._spatial_kp.augment(kp)

        # --- Augmentasi spasial frame RGB (jika ada) ---
        frames_out: Optional[np.ndarray] = None
        if sample.frames is not None:
            frames_out = self._spatial_rgb.augment(
                sample.frames,
                was_keypoint_flipped=was_flipped,
            )

        return AugmentationSample(keypoints=kp, frames=frames_out)
