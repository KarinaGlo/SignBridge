"""
augment.py — Keypoint spatial & temporal augmentations on raw keypoints before normalization.

Follows Modul 04 Langkah 2 (Bab 5.2):
  - Operates on raw keypoints [F, 86, 3] (with NaN for missing) BEFORE shoulder normalization
  - Supports:
      * mirror_p      : horizontal flip (x -> 1.0 - x) + swap left/right pose, hands, and face
      * speed_range   : temporal speed perturbation (0.8x - 1.2x) & random time crop
      * rot_deg       : 2D in-plane rotation around shoulder center (±rot_deg)
      * scale_range   : isotropic spatial scaling
      * shift_range   : random 2D translation
      * noise_std     : Gaussian landmark jitter
      * hand_dropout_p: randomly mask one hand for a short span to improve occlusion robustness
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

from signbridge.constants import (
    ALL_FLIP_PAIRS,
    L_SHOULDER_IDX,
    R_SHOULDER_IDX,
    LEFT_HAND_START,
    LEFT_HAND_END,
    RIGHT_HAND_START,
    RIGHT_HAND_END,
)


def mirror_keypoints(kp: np.ndarray) -> np.ndarray:
    """
    Mirror keypoints horizontally (for left-handed / right-handed signer invariance)
    and swap left/right anatomical indices.

    Parameters
    ----------
    kp : np.ndarray [F, 86, 3] (or [86, 3])

    Returns
    -------
    mirrored : np.ndarray of same shape
    """
    out = kp.astype(np.float32, copy=True)
    squeeze = False
    if out.ndim == 2:
        out = out[np.newaxis, ...]
        squeeze = True

    # Reflect x coordinate around 0.5 if in [0, 1] raw image coords, else around 0.0
    finite_x = out[..., 0][np.isfinite(out[..., 0])]
    if finite_x.size > 0 and float(np.min(finite_x)) >= -0.05 and float(np.max(finite_x)) <= 1.05:
        out[..., 0] = 1.0 - out[..., 0]
    else:
        out[..., 0] = -out[..., 0]

    # Swap left/right landmark pairs
    for left_idx, right_idx in ALL_FLIP_PAIRS:
        tmp = out[:, left_idx, :].copy()
        out[:, left_idx, :] = out[:, right_idx, :]
        out[:, right_idx, :] = tmp

    return out[0] if squeeze else out


def augment_keypoints(
    kp: np.ndarray,
    rng: Optional[np.random.Generator] = None,
    mirror_p: float = 0.0,
    rot_deg: float = 12.0,
    scale_range: Tuple[float, float] = (0.9, 1.1),
    shift_range: float = 0.03,
    noise_std: float = 0.003,
    speed_range: Tuple[float, float] = (0.85, 1.15),
    hand_dropout_p: float = 0.1,
) -> np.ndarray:
    """
    Apply stochastic spatial and temporal augmentations to raw keypoints [F, 86, 3].
    """
    if rng is None:
        rng = np.random.default_rng()

    out = kp.astype(np.float32, copy=True)
    if out.ndim != 3 or out.shape[0] == 0:
        return out

    # 1. Horizontal mirror (handedness augmentation)
    if mirror_p > 0.0 and rng.random() < mirror_p:
        out = mirror_keypoints(out)

    # 2. Temporal speed perturbation & crop
    F = out.shape[0]
    if F >= 8 and speed_range[0] < speed_range[1]:
        speed = float(rng.uniform(speed_range[0], speed_range[1]))
        new_len = max(4, int(round(F / speed)))
        indices = np.clip(
            np.floor((np.arange(new_len) + 0.5) * F / new_len).astype(np.int64),
            0,
            F - 1,
        )
        out = out[indices]
        F = out.shape[0]

    # 3. 2D Rotation + Scale + Shift around approximate shoulder midpoint
    angle_rad = float(np.deg2rad(rng.uniform(-rot_deg, rot_deg))) if rot_deg > 0 else 0.0
    scale = float(rng.uniform(scale_range[0], scale_range[1]))
    dx = float(rng.uniform(-shift_range, shift_range))
    dy = float(rng.uniform(-shift_range, shift_range))

    cos_a = float(np.cos(angle_rad)) * scale
    sin_a = float(np.sin(angle_rad)) * scale

    # Estimate pivot from valid shoulders, default (0.5, 0.5)
    sh = out[:, [L_SHOULDER_IDX, R_SHOULDER_IDX], :2]
    finite_sh = np.isfinite(sh)
    if np.any(finite_sh):
        px = float(np.nanmean(sh[..., 0]))
        py = float(np.nanmean(sh[..., 1]))
    else:
        px, py = 0.5, 0.5

    x = out[..., 0] - px
    y = out[..., 1] - py
    out[..., 0] = (cos_a * x - sin_a * y) + px + dx
    out[..., 1] = (sin_a * x + cos_a * y) + py + dy
    out[..., 2] = out[..., 2] * scale

    # 4. Additive Gaussian noise on valid landmarks
    if noise_std > 0:
        noise = rng.normal(0.0, noise_std, size=out.shape).astype(np.float32)
        valid = np.isfinite(out)
        out = np.where(valid, out + noise, np.nan)

    # 5. Hand dropout (mask one hand in a small frame window)
    if hand_dropout_p > 0 and F >= 6 and rng.random() < hand_dropout_p:
        span = max(1, int(rng.integers(1, max(2, F // 5))))
        start = int(rng.integers(0, max(1, F - span)))
        if rng.random() < 0.5:
            out[start : start + span, LEFT_HAND_START:LEFT_HAND_END, :] = np.nan
        else:
            out[start : start + span, RIGHT_HAND_START:RIGHT_HAND_END, :] = np.nan

    return out.astype(np.float32)

