"""
signbridge/xmf/ops.py — Operasi preprocessing murni (NumPy/Pillow) yang DIPAKAI BERSAMA oleh
preprocess.py (offline) dan dicerminkan 1:1 oleh web/js/xmf.js (online di browser).

Tidak ada MediaPipe/OpenCV di sini supaya bisa diuji tanpa kamera.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np

from signbridge.xmf.config import (
    AUDIO_SR,
    NUM_COORDS,
    NUM_NODES,
    PERSON_CROP_CENTER_SHIFT,
    PERSON_CROP_SIDE_X_SHOULDER,
)

Box = Tuple[float, float, float]  # (cx, cy, side) dalam piksel


# ---------------------------------------------------------------------------
# Temporal
# ---------------------------------------------------------------------------
def uniform_indices(n: int, k: int) -> np.ndarray:
    """k indeks merata dari n frame: floor((i + 0.5) * n / k) — sama dengan resample keypoint."""
    if n <= 0:
        return np.zeros(k, dtype=np.int64)
    return np.minimum(((np.arange(k) + 0.5) * n / k).astype(np.int64), n - 1)


# ---------------------------------------------------------------------------
# Citra: crop badan-atas berpanduan pose (modalitas IMAGE tugas gloss)
# ---------------------------------------------------------------------------
def person_box_from_shoulders(
    l_sh: Sequence[float], r_sh: Sequence[float], width: int, height: int
) -> Optional[Box]:
    """Bahu kiri/kanan (koordinat ternormalisasi 0..1) -> kotak persegi (cx, cy, side) piksel."""
    lx, ly = float(l_sh[0]) * width, float(l_sh[1]) * height
    rx, ry = float(r_sh[0]) * width, float(r_sh[1]) * height
    if not all(np.isfinite([lx, ly, rx, ry])):
        return None
    sw = float(np.hypot(lx - rx, ly - ry))
    if sw < 4.0:
        return None
    cx, cy = 0.5 * (lx + rx), 0.5 * (ly + ry) + PERSON_CROP_CENTER_SHIFT * sw
    return cx, cy, PERSON_CROP_SIDE_X_SHOULDER * sw


def median_box(boxes: Sequence[Optional[Box]], width: int, height: int) -> Box:
    """Satukan kotak per-frame menjadi satu kotak stabil per klip (median); fallback: crop tengah."""
    valid = np.array([b for b in boxes if b is not None], dtype=np.float64)
    if len(valid) == 0:
        side = float(min(width, height))
        return width / 2.0, height / 2.0, side
    cx, cy, side = np.median(valid, axis=0)
    return float(cx), float(cy), float(side)


def crop_square(img: np.ndarray, box: Box, out_side: int) -> np.ndarray:
    """
    img uint8 [H, W, 3] -> uint8 [out, out, 3]. Area di luar gambar diisi hitam (0),
    sama dengan perilaku canvas di browser. Resize bilinear (Pillow).
    """
    from PIL import Image

    h, w = img.shape[:2]
    cx, cy, side = box
    x0, y0 = int(round(cx - side / 2)), int(round(cy - side / 2))
    s = max(1, int(round(side)))
    canvas = np.zeros((s, s, 3), dtype=np.uint8)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x0 + s), min(h, y0 + s)
    if sx1 > sx0 and sy1 > sy0:
        canvas[sy0 - y0: sy1 - y0, sx0 - x0: sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return np.asarray(Image.fromarray(canvas).resize((out_side, out_side), Image.BILINEAR), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Citra: crop tangan (modalitas IMAGE tugas alfabet) — sama dgn handcrop.js (+25 %)
# ---------------------------------------------------------------------------
def hand_box(hand21: np.ndarray, width: int, height: int, margin: float = 0.25) -> Optional[Box]:
    pts = np.asarray(hand21, dtype=np.float64)[:, :2]
    pts = pts[np.all(np.isfinite(pts), axis=1)]
    if len(pts) < 5:
        return None
    xs, ys = pts[:, 0] * width, pts[:, 1] * height
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) * (1.0 + 2 * margin)
    if side < 8:
        return None
    return float((xs.max() + xs.min()) / 2), float((ys.max() + ys.min()) / 2), float(side)


def union_box(boxes: Sequence[Optional[Box]]) -> Optional[Box]:
    valid = [b for b in boxes if b is not None]
    if not valid:
        return None
    x0 = min(b[0] - b[2] / 2 for b in valid)
    x1 = max(b[0] + b[2] / 2 for b in valid)
    y0 = min(b[1] - b[2] / 2 for b in valid)
    y1 = max(b[1] + b[2] / 2 for b in valid)
    return (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0)


# ---------------------------------------------------------------------------
# Pose statis tangan (modalitas VIDEO/pose tugas alfabet)
# ---------------------------------------------------------------------------
L_HAND, R_HAND = slice(9, 30), slice(30, 51)


def normalize_hands_static(kp86: np.ndarray) -> np.ndarray:
    """
    [86, 3] mentah -> [86, 3] dengan tiap tangan dinormalisasi relatif pergelangan (titik 0)
    dan dibagi ukuran telapak (pergelangan -> pangkal jari tengah, titik 9). Titik lain = 0.
    """
    kp = np.asarray(kp86, dtype=np.float32)
    out = np.zeros((NUM_NODES, NUM_COORDS), dtype=np.float32)
    for sl in (L_HAND, R_HAND):
        h = kp[sl]
        if not np.all(np.isfinite(h)) or np.abs(h).sum() < 1e-6:
            continue
        wrist = h[0]
        palm = float(np.linalg.norm(h[9, :2] - wrist[:2]))
        if palm < 1e-4:
            continue
        out[sl] = (h - wrist) / palm
    return out


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
def fit_audio(pcm: np.ndarray, n: int = 40_000, sr: int = AUDIO_SR, thresh_db: float = -35.0) -> np.ndarray:
    """
    Potong hening di awal/akhir (relatif puncak), lalu letakkan ucapan di TENGAH jendela n sampel.
    Browser melakukan hal yang sama sebelum mengirim gelombang ke model.
    """
    x = np.asarray(pcm, dtype=np.float32).reshape(-1)
    out = np.zeros(n, dtype=np.float32)
    if x.size == 0:
        return out
    peak = float(np.max(np.abs(x)))
    if peak < 1e-5:
        return out
    hop = sr // 100
    frames = x[: (x.size // hop) * hop].reshape(-1, hop) if x.size >= hop else x.reshape(1, -1)
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    keep = np.where(20 * np.log10(rms / peak + 1e-12) > thresh_db)[0]
    if len(keep):
        x = x[keep[0] * hop: (keep[-1] + 1) * hop]
    x = x / max(float(np.max(np.abs(x))), 1e-5) * 0.9
    if x.size >= n:
        start = (x.size - n) // 2
        return x[start: start + n].astype(np.float32)
    off = (n - x.size) // 2
    out[off: off + x.size] = x
    return out


def resample_linear(pcm: np.ndarray, sr_in: int, sr_out: int = AUDIO_SR) -> np.ndarray:
    pcm = np.asarray(pcm, dtype=np.float32)
    if sr_in == sr_out or pcm.size < 2:
        return pcm.copy()
    n_out = int(round(pcm.size * sr_out / sr_in))
    pos = np.arange(n_out, dtype=np.float64) * (pcm.size - 1) / max(n_out - 1, 1)
    return np.interp(pos, np.arange(pcm.size), pcm).astype(np.float32)


def stable_hash(text: str) -> int:
    import hashlib

    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:12], 16)
