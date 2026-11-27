"""
signbridge/xmf/data.py — Dataset 4-modalitas untuk SignBridge-XMF (membaca rekaman hasil preprocess.py).

Satu item = satu rekaman berpasangan {pose, frames, audio, text, mask, label}.
  * train : augmentasi + pasangan audio/teks diambil ulang secara acak dari konsep yang sama
            ("partner resampling") agar model tidak menghafal satu pasangan.
  * val/test : pasangan audio/teks deterministik dari split yang sesuai protokol (tanpa kebocoran).
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import Dataset

from signbridge.xmf.config import (
    M_AUDIO, M_TEXT, MODALITIES, SHAPES, TEXT_ALPHABET, classes_for, encode_text, texts_for,
)
from signbridge.xmf.ops import stable_hash

ROOT = Path(__file__).resolve().parents[2]

# Subset modalitas (V=video, I=citra, A=audio, T=teks) dipakai untuk sampling mask & evaluasi ablation
SUBSETS: Dict[str, List[int]] = {
    "VIAT": [1, 1, 1, 1], "VI": [1, 1, 0, 0], "V": [1, 0, 0, 0], "I": [0, 1, 0, 0],
    "A": [0, 0, 1, 0], "T": [0, 0, 0, 1], "VIA": [1, 1, 1, 0], "VIT": [1, 1, 0, 1],
}


def split_column(task: str, protocol: str) -> str:
    if protocol == "final":
        return "split_final"
    if task == "alphabet":
        return "split"
    return {"sd": "split_sd", "si": "split_si"}[protocol]


def read_rows(csv_path: Path, split_col: str, split: str) -> List[Dict]:
    with csv_path.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get(split_col) == split]


class AudioBank:
    def __init__(self, path: Optional[Path]):
        self.ok = bool(path and path.exists())
        if self.ok:
            z = np.load(path, allow_pickle=False)
            self.wave = z["wave"].astype(np.float32)
            self.label, self.split = z["label"], z["split"]

    def pick(self, label: int, split: str, rng: Optional[random.Random], key: str) -> Optional[np.ndarray]:
        if not self.ok:
            return None
        idx = np.where((self.label == label) & (self.split == split))[0]
        if len(idx) == 0:
            idx = np.where(self.label == label)[0]
        if len(idx) == 0:
            return None
        j = idx[rng.randrange(len(idx))] if rng else idx[stable_hash(key) % len(idx)]
        return self.wave[j]


def _typo(text: str, rng: random.Random) -> str:
    if len(text) < 3 or rng.random() > 0.3:
        return text
    i = rng.randrange(len(text))
    op = rng.random()
    if op < 0.33:
        return text[:i] + text[i + 1:]
    if op < 0.66:
        return text[:i] + rng.choice(TEXT_ALPHABET[:26]) + text[i + 1:]
    j = min(i + 1, len(text) - 1)
    lst = list(text)
    lst[i], lst[j] = lst[j], lst[i]
    return "".join(lst)


class XMFDataset(Dataset):
    def __init__(self, task: str, processed_csv: Path, split: str, protocol: str = "sd",
                 bank_path: Optional[Path] = None, train: bool = False, cache: bool = False):
        self.task, self.split, self.train = task, split, train
        self.shapes = SHAPES[task]
        self.rows = read_rows(processed_csv, split_column(task, protocol), split)
        self.bank = AudioBank(bank_path)
        self.texts = texts_for(task)
        self.classes = classes_for(task)
        self.cache = {} if cache else None
        self._rng = random.Random()

    def __len__(self) -> int:
        return len(self.rows)

    def labels(self) -> List[int]:
        return [int(r["label"]) for r in self.rows]

    def _load(self, i: int) -> Dict[str, np.ndarray]:
        if self.cache is not None and i in self.cache:
            return self.cache[i]
        with np.load(ROOT / self.rows[i]["npz_path"], allow_pickle=False) as z:
            d = {k: z[k] for k in ("pose", "frames", "audio", "text", "mask", "label")}
        if self.cache is not None:
            self.cache[i] = d
        return d

    # ------------------------------------------------------------------ augmentasi
    def _aug_pose(self, pose: np.ndarray, rng: random.Random) -> np.ndarray:
        T = pose.shape[0]
        x = pose.copy()
        if T > 1:   # time-warp: kecepatan 0.8-1.25 + potong acak lalu resample ke T
            speed = rng.uniform(0.8, 1.25)
            L = max(8, min(T, int(round(T / speed))))
            s = rng.randint(0, T - L) if L < T else 0
            idx = np.clip(s + np.floor((np.arange(T) + 0.5) * L / T).astype(int), 0, T - 1)
            x = x[idx]
            if rng.random() < 0.2:   # simulasi tangan hilang beberapa frame
                a = rng.randrange(T)
                x[a: a + rng.randint(1, 6), 9:51] = 0
        ang = math.radians(rng.uniform(-12, 12))
        rot = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]], np.float32)
        nz = np.abs(x).sum(-1, keepdims=True) > 0
        xy = x[..., :2] @ rot.T * rng.uniform(0.85, 1.15) + np.array([rng.uniform(-.1, .1), rng.uniform(-.1, .1)],
                                                                         np.float32)
        x[..., :2] = xy
        x += np.random.normal(0, 0.01, x.shape).astype(np.float32)
        return np.where(nz, x, 0).astype(np.float32)

    @staticmethod
    def _flip(pose: np.ndarray, frames: np.ndarray):
        p = pose.copy()
        p[..., 0] *= -1
        p[:, 9:30], p[:, 30:51] = pose[:, 30:51] * [-1, 1, 1], pose[:, 9:30] * [-1, 1, 1]
        return p, frames[:, :, ::-1].copy()

    def _aug_frames(self, fr: np.ndarray, rng: random.Random) -> np.ndarray:
        x = fr.astype(np.float32)
        F, H, W, _ = x.shape
        # zoom/geser kecil (sama untuk semua frame dalam klip -> konsisten temporal)
        sc = rng.uniform(0.85, 1.0)
        h = int(H * sc)
        y0, x0 = rng.randint(0, H - h), rng.randint(0, W - h)
        t = torch.from_numpy(x[:, y0:y0 + h, x0:x0 + h]).permute(0, 3, 1, 2)
        t = torch.nn.functional.interpolate(t, size=(H, W), mode="bilinear", align_corners=False)
        x = t.permute(0, 2, 3, 1).numpy()
        # warna: kecerahan, kontras, saturasi, sedikit pergeseran kanal (variasi kamera/pencahayaan)
        x = x * rng.uniform(0.7, 1.3) + rng.uniform(-25, 25)
        m = x.mean(axis=(1, 2, 3), keepdims=True)
        x = (x - m) * rng.uniform(0.7, 1.3) + m
        g = x.mean(-1, keepdims=True)
        x = (x - g) * rng.uniform(0.6, 1.4) + g
        x = x + np.array([rng.uniform(-12, 12) for _ in range(3)], np.float32)
        if rng.random() < 0.3:
            x = x + np.random.normal(0, 6, x.shape)
        return np.clip(x, 0, 255).astype(np.float32)

    def _aug_audio(self, a: np.ndarray, rng: random.Random) -> np.ndarray:
        x = np.roll(a, rng.randint(-4800, 4800)) * rng.uniform(0.4, 1.4)
        if rng.random() < 0.8:
            p = float(np.mean(x ** 2)) + 1e-8
            snr = rng.uniform(5, 30)
            x = x + np.random.normal(0, math.sqrt(p / 10 ** (snr / 10)), x.shape)
        return np.clip(x, -1, 1).astype(np.float32)

    # ------------------------------------------------------------------
    def __getitem__(self, i: int) -> Dict[str, torch.Tensor]:
        d = self._load(i)
        row = self.rows[i]
        label = int(d["label"])
        rng = self._rng if self.train else None
        pose = d["pose"].astype(np.float32)
        frames = d["frames"]                                     # uint8 [F,H,W,3]
        mask = d["mask"].astype(np.float32).copy()

        audio = self.bank.pick(label, self.split, rng, "a:" + row["sample_id"])
        if audio is None:
            audio = d["audio"].astype(np.float32)
        else:
            mask[M_AUDIO] = 1.0
        variants = self.texts[self.classes[label]]
        if rng:
            txt = _typo(rng.choice(variants), rng)
            if rng.random() < 0.5:
                txt = txt.upper() if rng.random() < 0.3 else txt.capitalize()
        else:
            txt = variants[stable_hash("t:" + row["sample_id"]) % len(variants)]
        text = np.array(encode_text(txt, self.shapes.text_len), np.int64)
        mask[M_TEXT] = 1.0

        if self.train:
            if self.task == "alphabet" and rng.random() < 0.5:
                pose, frames = self._flip(pose, frames)
            pose = self._aug_pose(pose, rng)
            fr = self._aug_frames(frames, rng)
            audio = self._aug_audio(audio, rng)
        else:
            fr = frames.astype(np.float32)
        return {
            "pose": torch.from_numpy(np.ascontiguousarray(pose)),
            "frames": torch.from_numpy(np.ascontiguousarray(fr.transpose(0, 3, 1, 2))),
            "audio": torch.from_numpy(np.ascontiguousarray(audio, dtype=np.float32)),
            "text": torch.from_numpy(text),
            "mask": torch.from_numpy(mask),
            "label": torch.tensor(label, dtype=torch.long),
        }


def sample_subset_masks(avail: torch.Tensor, probs: Dict[str, float], rng: random.Random) -> torch.Tensor:
    """Untuk tiap sampel, pilih subset modalitas sesuai distribusi; selalu sisakan >= 1 yang tersedia."""
    names, w = list(probs), list(probs.values())
    out = avail.clone()
    for b in range(avail.size(0)):
        m = torch.tensor(SUBSETS[rng.choices(names, w)[0]], dtype=avail.dtype, device=avail.device) * avail[b]
        out[b] = m if m.sum() > 0 else avail[b]
    return out


def subset_mask(avail: torch.Tensor, name: str) -> torch.Tensor:
    return avail * torch.tensor(SUBSETS[name], dtype=avail.dtype, device=avail.device)


__all__ = ["XMFDataset", "SUBSETS", "sample_subset_masks", "subset_mask", "MODALITIES"]
