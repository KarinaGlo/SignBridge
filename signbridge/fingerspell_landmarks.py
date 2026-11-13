"""Pengenal abjad jari BISINDO A–Z dari LANDMARK tangan (bukan piksel, bukan aturan geometri buatan).

Kenapa landmark? Abjad BISINDO sebagian besar memakai DUA tangan, dan bedanya ada pada bentuk jari + posisi
tangan satu terhadap yang lain. Landmark MediaPipe (21 titik/tangan) sudah dihitung oleh aplikasi web, jadi
klasifikasinya cukup MLP kecil (<100 KB) yang berjalan < 1 ms di browser, tanpa ONNX tambahan.

Fitur (127 angka) — HARUS identik dengan web/js/fingerspell_mlp.js (diuji tests/js/fingerspell_mlp.test.mjs):
  [0]       1 bila dua tangan, 0 bila satu tangan
  [1:43]    bentuk tangan A: 21 titik (x,y) relatif pergelangan A, dibagi ukuran telapak A
  [43:85]   bentuk tangan B: idem untuk tangan B (0 bila tidak ada)
  [85:127]  posisi 21 titik tangan B relatif pergelangan A, dibagi ukuran telapak A  (interaksi dua tangan)
Tangan A = tangan dengan pergelangan paling KIRI di gambar. Ukuran telapak = jarak pergelangan(0) -> pangkal
jari tengah(9). Hanya x,y yang dipakai (z MediaPipe tidak stabil antar kamera).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

LETTERS = [chr(c) for c in range(65, 91)]
N_FEAT = 127


def _shape(h, w, palm):
    return ((h - w) / palm).reshape(-1)


def hand_features(hands) -> np.ndarray:
    """hands: list berisi 1–2 array [21, >=2] koordinat gambar ternormalisasi (0..1). Return [127] float32."""
    hs = [np.asarray(h, dtype=np.float64)[:, :2] for h in hands if h is not None and len(h) == 21]
    hs = [h for h in hs if np.isfinite(h).all() and np.abs(h).sum() > 0]
    f = np.zeros(N_FEAT, dtype=np.float32)
    if not hs:
        return f
    hs = sorted(hs, key=lambda h: h[0, 0])[:2]
    a = hs[0]
    pa = max(float(np.linalg.norm(a[9] - a[0])), 1e-6)
    f[1:43] = _shape(a, a[0], pa)
    if len(hs) == 2:
        b = hs[1]
        pb = max(float(np.linalg.norm(b[9] - b[0])), 1e-6)
        f[0] = 1.0
        f[43:85] = _shape(b, b[0], pb)
        f[85:127] = _shape(b, a[0], pa)
    return f


def augment_hands(hands, rng):
    """Augmentasi pada level landmark: cermin (penutur kidal), rotasi kecil, skala, geser, jitter, buang 1 tangan."""
    out = [np.asarray(h, dtype=np.float64)[:, :2].copy() for h in hands]
    if rng.random() < 0.5:                                   # cermin horizontal
        out = [np.c_[1.0 - h[:, 0], h[:, 1]] for h in out]
    c = np.concatenate(out).mean(0)
    th = np.deg2rad(rng.uniform(-15, 15)); s = rng.uniform(0.85, 1.15)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) * s
    sh = rng.uniform(-0.05, 0.05, 2)
    out = [(h - c) @ R.T + c + sh + rng.normal(0, 0.004, h.shape) for h in out]
    if len(out) == 2 and rng.random() < 0.12:                # tangan kedua kadang tak terdeteksi kamera
        out = [out[int(rng.integers(2))]]
    return out


class MLP:
    """Forward pass MLP (ReLU) + softmax dari bobot JSON — sama persis dengan versi JS."""

    def __init__(self, weights: dict):
        self.mean = np.asarray(weights["mean"], np.float64); self.std = np.asarray(weights["std"], np.float64)
        self.layers = [(np.asarray(l["W"], np.float64), np.asarray(l["b"], np.float64)) for l in weights["layers"]]
        self.labels = weights["labels"]

    @classmethod
    def load(cls, path):
        return cls(json.load(open(path, encoding="utf-8")))

    def predict_proba(self, X):
        h = (np.atleast_2d(X) - self.mean) / self.std
        for i, (W, b) in enumerate(self.layers):
            h = h @ W + b
            if i < len(self.layers) - 1:
                h = np.maximum(h, 0)
        h = h - h.max(1, keepdims=True)
        e = np.exp(h)
        return e / e.sum(1, keepdims=True)


def export_weights(clf, mean, std, path, meta=None):
    """Simpan scikit-learn MLPClassifier sebagai JSON ringkas untuk browser."""
    w = {"labels": [str(c) for c in clf.classes_], "n_features": N_FEAT,
         "mean": np.round(mean, 6).tolist(), "std": np.round(std, 6).tolist(),
         "layers": [{"W": np.round(W, 4).tolist(), "b": np.round(b, 5).tolist()} for W, b in zip(clf.coefs_, clf.intercepts_)],
         "meta": meta or {}}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    json.dump(w, open(path, "w"), separators=(",", ":"))
    return w
