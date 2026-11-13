"""
features.py — Contract 3: Keypoint preprocessing pipeline (Python <-> JS parity).

Pipeline stages (must match web/js/features.js bit-for-bit within < 1e-5):
  1. trim_inactive   : Trim leading & trailing frames where neither hand is visible
  2. normalize_pose  : Center at shoulder midpoint 0.5*(bahu_L + bahu_R) and divide by
                       shoulder width ||bahu_L - bahu_R||; replace NaN with 0.0
  3. resample_frames : Resample temporal axis to T_MAX=64 frames using floor((i + 0.5) * F / T_MAX)
  4. preprocess_keypoints / extract_and_normalize : Full pipeline returning float32 [64, 86, 3]
"""

from __future__ import annotations

from typing import Tuple
import numpy as np

from signbridge.constants import (
    NUM_KEYPOINTS,
    NUM_COORDS,
    T_MAX,
    L_SHOULDER_IDX,
    R_SHOULDER_IDX,
    LEFT_HAND_START,
    RIGHT_HAND_END,
)


def _frame_has_hand(frame_kp: np.ndarray) -> bool:
    """
    Return True if at least one hand coordinate in [9:51] is finite and non-zero.
    """
    hands = frame_kp[LEFT_HAND_START:RIGHT_HAND_END]  # [42, 3]
    finite = np.isfinite(hands)
    if not np.any(finite):
        return False
    # Check if there is any non-zero finite value
    valid_vals = np.where(finite, np.abs(hands), 0.0)
    return bool(np.sum(valid_vals) > 1e-6)


def trim_inactive(kp: np.ndarray) -> np.ndarray:
    """
    Remove leading and trailing frames where neither hand is detected.
    If no frame has a detected hand, return the original sequence unchanged.

    Parameters
    ----------
    kp : np.ndarray [F, 86, 3]

    Returns
    -------
    trimmed : np.ndarray [F', 86, 3] with F' >= 1
    """
    if kp.ndim != 3 or len(kp) == 0:
        return np.zeros((1, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)

    F = kp.shape[0]
    first_valid = -1
    last_valid = -1
    for t in range(F):
        if _frame_has_hand(kp[t]):
            if first_valid == -1:
                first_valid = t
            last_valid = t

    if first_valid == -1:
        return kp.astype(np.float32, copy=True)

    return kp[first_valid : last_valid + 1].astype(np.float32, copy=True)


def normalize_pose(kp: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Shoulder-relative pose normalization per frame:
        x_hat = (x - 0.5 * (bahu_L + bahu_R)) / ||bahu_L - bahu_R||

    If shoulders on frame t are missing (NaN) or degenerate (||bahu_L - bahu_R|| < 1e-4),
    fallback to the last valid center & scale (or default center=[0.5, 0.5, 0.0], scale=0.25).
    Missing keypoints (NaN) are replaced with 0.0 and recorded as False in valid_mask.

    Parameters
    ----------
    kp : np.ndarray [F, 86, 3]

    Returns
    -------
    norm_kp    : np.ndarray [F, 86, 3] float32 (no NaNs)
    valid_mask : np.ndarray [F, 86] bool (True where original keypoint was finite)
    """
    kp_f32 = np.asarray(kp, dtype=np.float32)
    if kp_f32.ndim == 2:
        kp_f32 = kp_f32[np.newaxis, ...]

    F, V, C = kp_f32.shape
    norm_kp = np.zeros((F, V, C), dtype=np.float32)
    valid_mask = np.all(np.isfinite(kp_f32), axis=-1)  # [F, 86]

    prev_center = np.array([0.5, 0.5, 0.0], dtype=np.float32)
    prev_scale = 0.25

    # Pre-scan for the first valid shoulder pair so frame 0 has a good fallback if needed
    for t in range(F):
        if valid_mask[t, L_SHOULDER_IDX] and valid_mask[t, R_SHOULDER_IDX]:
            b_l = kp_f32[t, L_SHOULDER_IDX]
            b_r = kp_f32[t, R_SHOULDER_IDX]
            dist = float(np.sqrt(np.sum((b_l - b_r) ** 2)))
            if dist >= 1e-4:
                prev_center = 0.5 * (b_l + b_r)
                prev_scale = dist
                break

    for t in range(F):
        if valid_mask[t, L_SHOULDER_IDX] and valid_mask[t, R_SHOULDER_IDX]:
            b_l = kp_f32[t, L_SHOULDER_IDX]
            b_r = kp_f32[t, R_SHOULDER_IDX]
            dist = float(np.sqrt(np.sum((b_l - b_r) ** 2)))
            if dist >= 1e-4:
                center = 0.5 * (b_l + b_r)
                scale = dist
                prev_center = center
                prev_scale = scale
            else:
                center = prev_center
                scale = prev_scale
        else:
            center = prev_center
            scale = prev_scale

        inv_scale = np.float32(1.0 / scale)
        for v in range(V):
            if valid_mask[t, v]:
                norm_kp[t, v, 0] = np.float32((kp_f32[t, v, 0] - center[0]) * inv_scale)
                norm_kp[t, v, 1] = np.float32((kp_f32[t, v, 1] - center[1]) * inv_scale)
                norm_kp[t, v, 2] = np.float32((kp_f32[t, v, 2] - center[2]) * inv_scale)
            else:
                norm_kp[t, v, 0] = 0.0
                norm_kp[t, v, 1] = 0.0
                norm_kp[t, v, 2] = 0.0

    return norm_kp, valid_mask


def resample_frames(
    kp: np.ndarray,
    valid_mask: np.ndarray | None = None,
    target_len: int = T_MAX,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Resample sequence of length F to `target_len` (default 64) using midpoint floor indexing:
        idx[i] = min(F - 1, int(floor((i + 0.5) * F / target_len)))

    This deterministic rule is identical in Python and JavaScript (features.js).

    Parameters
    ----------
    kp         : np.ndarray [F, 86, 3]
    valid_mask : np.ndarray [F, 86] bool or None
    target_len : int (default 64)

    Returns
    -------
    resampled_kp   : np.ndarray [target_len, 86, 3] float32
    resampled_mask : np.ndarray [target_len, 86] bool
    """
    F = kp.shape[0]
    if valid_mask is None:
        valid_mask = np.any(kp != 0.0, axis=-1)

    if F == 0:
        return (
            np.zeros((target_len, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32),
            np.zeros((target_len, NUM_KEYPOINTS), dtype=bool),
        )

    indices = [min(F - 1, int(np.floor((i + 0.5) * F / target_len))) for i in range(target_len)]
    idx_arr = np.array(indices, dtype=np.int64)
    return kp[idx_arr].astype(np.float32, copy=True), valid_mask[idx_arr].astype(bool, copy=True)


def preprocess_keypoints(
    kp: np.ndarray,
    target_len: int = T_MAX,
    trim: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Full keypoint preprocessing pipeline:
        trim_inactive -> normalize_pose -> resample_frames(target_len=64)

    Returns
    -------
    pose : np.ndarray [target_len, 86, 3] float32
    mask : np.ndarray [target_len, 86] bool
    """
    arr = np.asarray(kp, dtype=np.float32)
    if arr.ndim == 2:
        arr = arr[np.newaxis, ...]
    if trim:
        arr = trim_inactive(arr)
    norm_kp, valid_mask = normalize_pose(arr)
    return resample_frames(norm_kp, valid_mask, target_len=target_len)


def extract_and_normalize(
    kp: np.ndarray,
    target_len: int = T_MAX,
) -> np.ndarray:
    """
    Convenience wrapper returning ONNX-ready tensor of shape [1, 64, 86, 3] float32.
    Matches `extractAndNormalize` in `web/js/features.js`.
    """
    pose, _ = preprocess_keypoints(kp, target_len=target_len, trim=True)
    return pose[np.newaxis, ...].astype(np.float32)

