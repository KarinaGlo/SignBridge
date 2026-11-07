"""
crop.py — Contract 4: Deterministic Hand Bounding-Box Crop & Resize (Python <-> JS parity).

Follows Modul 03 Langkah 11 (Bab 4.11 p. 19):
  - Given 1 or 2 hand landmark sets (normalized [0, 1] or pixel coordinates) and image (W, H),
    computes the tight bounding box around all visible hand points, expands it to a square
    with +25% margin (`margin=0.25` on each side, i.e., side = max(w, h) * 1.5),
    and clamps to image bounds [0, W] x [0, H].
  - Identical logic is implemented in `web/js/handcrop.js` and verified by
    `tests/js/handcrop.test.mjs` and `pytest`.
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple
import numpy as np

from signbridge.constants import IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD


def compute_hand_crop_box(
    landmarks: Sequence[Sequence[float]] | np.ndarray,
    img_w: int,
    img_h: int,
    margin: float = 0.25,
) -> Dict[str, int]:
    """
    Compute a square crop bounding box around hand landmarks with +25% margin per side.

    Parameters
    ----------
    landmarks : array-like of shape [N, 2] or [N, 3]
        Normalized [0, 1] coordinates (if max <= 1.05) or pixel coordinates.
    img_w, img_h : int
        Width and height of the source image in pixels.
    margin : float
        Fractional margin added on each side of the max extent (default 0.25 -> 1 + 2*0.25 = 1.5x).

    Returns
    -------
    box : dict with integer keys {"x0", "y0", "x1", "y1", "size"}
    """
    pts = np.asarray(landmarks, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[0] == 0:
        side = min(img_w, img_h)
        x0 = (img_w - side) // 2
        y0 = (img_h - side) // 2
        return {"x0": int(x0), "y0": int(y0), "x1": int(x0 + side), "y1": int(y0 + side), "size": int(side)}

    # Keep only finite points
    valid = np.all(np.isfinite(pts[:, :2]), axis=1)
    pts = pts[valid, :2]
    if pts.shape[0] == 0:
        side = min(img_w, img_h)
        x0 = (img_w - side) // 2
        y0 = (img_h - side) // 2
        return {"x0": int(x0), "y0": int(y0), "x1": int(x0 + side), "y1": int(y0 + side), "size": int(side)}

    # Convert normalized [0, 1] to pixel coordinates if needed
    if np.max(np.abs(pts)) <= 1.5:
        xs = pts[:, 0] * float(img_w)
        ys = pts[:, 1] * float(img_h)
    else:
        xs = pts[:, 0]
        ys = pts[:, 1]

    min_x = float(np.min(xs))
    max_x = float(np.max(xs))
    min_y = float(np.min(ys))
    max_y = float(np.max(ys))

    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)
    span = max(max_x - min_x, max_y - min_y, 16.0)
    half_side = 0.5 * span * (1.0 + 2.0 * float(margin))

    # Clamp square crop inside image boundaries
    max_half = 0.5 * float(min(img_w, img_h))
    if half_side > max_half:
        half_side = max_half

    x0_f = cx - half_side
    y0_f = cy - half_side
    if x0_f < 0.0:
        x0_f = 0.0
    if y0_f < 0.0:
        y0_f = 0.0
    if x0_f + 2.0 * half_side > float(img_w):
        x0_f = float(img_w) - 2.0 * half_side
    if y0_f + 2.0 * half_side > float(img_h):
        y0_f = float(img_h) - 2.0 * half_side

    x0 = int(np.round(max(0.0, x0_f)))
    y0 = int(np.round(max(0.0, y0_f)))
    size = int(np.round(2.0 * half_side))
    size = max(1, min(size, img_w - x0, img_h - y0))

    return {
        "x0": x0,
        "y0": y0,
        "x1": x0 + size,
        "y1": y0 + size,
        "size": size,
    }


def _bilinear_resize_rgb(img: np.ndarray, out_h: int = IMAGE_SIZE, out_w: int = IMAGE_SIZE) -> np.ndarray:
    """
    Pure-NumPy deterministic bilinear resize of [H, W, 3] uint8/float32 image to [out_h, out_w, 3].
    """
    in_h, in_w, c = img.shape
    if in_h == out_h and in_w == out_w:
        return img.copy()

    row_idx = (np.arange(out_h, dtype=np.float32) + 0.5) * (in_h / float(out_h)) - 0.5
    col_idx = (np.arange(out_w, dtype=np.float32) + 0.5) * (in_w / float(out_w)) - 0.5
    row_idx = np.clip(row_idx, 0.0, max(0.0, float(in_h - 1)))
    col_idx = np.clip(col_idx, 0.0, max(0.0, float(in_w - 1)))

    r0 = np.floor(row_idx).astype(np.int64)
    r1 = np.minimum(r0 + 1, in_h - 1)
    c0 = np.floor(col_idx).astype(np.int64)
    c1 = np.minimum(c0 + 1, in_w - 1)

    dr = (row_idx - r0)[:, None, None]
    dc = (col_idx - c0)[None, :, None]

    img_f = img.astype(np.float32)
    top = (1.0 - dc) * img_f[r0[:, None], c0[None, :]] + dc * img_f[r0[:, None], c1[None, :]]
    bot = (1.0 - dc) * img_f[r1[:, None], c0[None, :]] + dc * img_f[r1[:, None], c1[None, :]]
    out = (1.0 - dr) * top + dr * bot
    if img.dtype == np.uint8:
        return np.clip(np.round(out), 0, 255).astype(np.uint8)
    return out.astype(np.float32)


def crop_and_resize_hand(
    image: np.ndarray,
    landmarks: Sequence[Sequence[float]] | np.ndarray,
    out_size: int = IMAGE_SIZE,
    margin: float = 0.25,
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Crop hand square region (+25% margin) from `image` [H, W, 3] and resize to [out_size, out_size, 3].
    """
    H, W = image.shape[:2]
    box = compute_hand_crop_box(landmarks, img_w=W, img_h=H, margin=margin)
    patch = image[box["y0"] : box["y1"], box["x0"] : box["x1"]]
    resized = _bilinear_resize_rgb(patch, out_h=out_size, out_w=out_size)
    return resized, box


def normalize_imagenet(img_rgb: np.ndarray) -> np.ndarray:
    """
    Convert [224, 224, 3] uint8 (0..255) or float [0, 1] RGB image to ONNX input tensor
    [1, 3, 224, 224] float32 normalized with ImageNet mean/std (Contract 5).
    """
    arr = img_rgb.astype(np.float32)
    if arr.max() > 1.5:
        arr = arr / 255.0
    mean = np.array(IMAGENET_MEAN, dtype=np.float32).reshape(1, 1, 3)
    std = np.array(IMAGENET_STD, dtype=np.float32).reshape(1, 1, 3)
    norm = (arr - mean) / std
    chw = np.transpose(norm, (2, 0, 1))  # [3, 224, 224]
    return chw[np.newaxis, ...].astype(np.float32)

