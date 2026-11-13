"""Animasi rujukan dari DATA ASLI -> web/model/ref/<NAMA>.json (menggantikan animasi sintetis di kamus & latihan).

Kata (32 gloss): dari keypoint mentah WL-BISINDO (raw_keypoints di .npz) — jalankan di PC yang punya data:
  python scripts/build_reference_signs.py --words --manifest data/manifest_wl_bisindo.csv
Huruf (A–Z): dari landmark abjad BISINDO nyata (data/ Krisna, MIT, atau data/selfrec/fingerspell_landmarks.csv):
  python scripts/build_reference_signs.py --letters-krisna ../realtime-bisindo-classification/data
Format: {"name","source","fps","frames":[[[x,y,z] x 86] x F]} koordinat gambar 0..1 (titik hilang = 0).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from signbridge.constants import BISINDO_32_GLOSSES  # noqa: E402

OUT = ROOT / "web" / "model" / "ref"


def _dump(name, frames, source, fps):
    OUT.mkdir(parents=True, exist_ok=True)
    fr = np.nan_to_num(np.asarray(frames, np.float32), nan=0.0)
    json.dump({"name": name, "source": source, "fps": fps,
               "frames": np.round(fr, 3).tolist()}, open(OUT / f"{name}.json", "w"), separators=(",", ":"))


def build_words(manifest: Path, max_frames: int = 72):
    rows = list(csv.DictReader(open(manifest, encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[r["gloss"].upper()].append(r)
    done = 0
    for g in BISINDO_32_GLOSSES:
        cands = []
        for r in by.get(g, []):
            p = ROOT / r["kp_path"]
            if not p.exists():
                continue
            with np.load(p) as d:
                raw = d["raw_keypoints"] if "raw_keypoints" in d else (d["kp"] if "kp" in d else None)
            if raw is None:
                continue
            hand = ~np.isnan(raw[:, 9:51, 0]).all(1) & (np.nan_to_num(np.abs(raw[:, 9:51, :2])).sum((1, 2)) > 0)
            if hand.sum() < 8:
                continue
            idx = np.where(hand)[0]
            clip = raw[max(0, idx[0] - 3): idx[-1] + 4]
            completeness = float(np.isfinite(clip[:, :51, 0]).mean())
            cands.append((completeness, len(clip), r, clip))
        if not cands:
            print(f"[kata] {g}: tidak ada klip -> dilewati"); continue
        med = np.median([c[1] for c in cands])
        best = max(cands, key=lambda c: (round(c[0], 2), -abs(c[1] - med)))   # paling lengkap, panjang mendekati median
        clip = best[3]
        if len(clip) > max_frames:
            clip = clip[np.linspace(0, len(clip) - 1, max_frames).round().astype(int)]
        _dump(g, clip, f"WL-BISINDO {best[2]['video_id']} (penutur asli)", 20)
        done += 1
    print(f"[kata] {done}/32 rujukan dari rekaman asli -> {OUT}")


def build_letters_krisna(d: Path, per_letter_frames: int = 6):
    sys.path.insert(0, str(ROOT / "scripts"))
    from train_fingerspell_landmarks import load_krisna
    rows = load_krisna(d).get("train", [])
    rng = np.random.default_rng(0)
    for L in [chr(c) for c in range(65, 91)]:
        cand = [h for lab, h, _ in rows if lab == L]
        two = [h for h in cand if len(h) == 2]
        hands = (two or cand)[int(rng.integers(len(two or cand)))]
        kp = np.zeros((86, 3), np.float32)
        hs = sorted([np.asarray(h)[:, :3] for h in hands], key=lambda h: h[0, 0])
        kp[30:51] = hs[0]                      # tangan kiri-gambar = tangan kanan penutur
        if len(hs) == 2:
            kp[9:30] = hs[1]
        frames = [kp] * per_letter_frames            # huruf = pose statis
        _dump(L, frames, "Abjad BISINDO, landmark asli (KrisnaSantosa15/realtime-bisindo-classification, MIT)", 10)
    print(f"[huruf] 26 rujukan -> {OUT}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", action="store_true")
    ap.add_argument("--manifest", type=Path, default=ROOT / "data/manifest_wl_bisindo.csv")
    ap.add_argument("--letters-krisna", type=Path)
    a = ap.parse_args()
    if a.words:
        build_words(a.manifest)
    if a.letters_krisna:
        build_letters_krisna(a.letters_krisna)


if __name__ == "__main__":
    main()
