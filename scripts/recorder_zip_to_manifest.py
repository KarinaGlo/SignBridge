"""ZIP dari "Perekam Dataset" web -> data latih SignBridge (kata & abjad).

  python scripts/recorder_zip_to_manifest.py --inp data/raw/web_zips --out data/selfrec
Keluaran:
  data/selfrec/keypoints/<clip>.npz        kp = keypoint MENTAH [F,86,3] (titik hilang = NaN, sama dengan ekstraksi Python)
  data/selfrec/manifest_own.csv            kata (32 gloss WL-BISINDO) -> --extra-manifest di scripts/train_m0_robust.py
  data/selfrec/fingerspell_landmarks.csv   huruf A–Z (landmark 2 tangan) -> --landmarks di scripts/train_fingerspell_landmarks.py
Klip dengan tangan terlihat < 8 frame dibuang. Ringkasan jumlah per perekam/kelas dicetak di akhir.
Catatan: rekaman anggota tim yang bukan penutur BISINDO = "rekaman penutur pemula"; laporkan terpisah.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from signbridge.constants import BISINDO_32_GLOSSES  # noqa: E402

GROUPS = {"pose": (0, 9), "lhand": (9, 30), "rhand": (30, 51), "face": (51, 86)}
LETTERS = [chr(c) for c in range(65, 91)]


def to_raw(frames):
    """List [F][86][3] dari web (titik hilang = 0) -> float32 dengan NaN untuk kelompok titik yang hilang."""
    kp = np.asarray(frames, dtype=np.float32)
    for a, b in GROUPS.values():
        miss = np.abs(kp[:, a:b, :2]).sum((1, 2)) < 1e-6
        kp[miss, a:b] = np.nan
    return kp


def _rel(p: Path) -> str:
    """Path relatif terhadap root repo bila memungkinkan (SignDataset membaca relatif data_root)."""
    try:
        return str(p.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p.resolve()).replace("\\", "/")


def iter_clips(inp: Path):
    for zf in sorted(inp.rglob("*.zip")):
        with zipfile.ZipFile(zf) as z:
            for name in z.namelist():
                if name.endswith("_kp.json"):
                    yield zf.name, json.loads(z.read(name))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", type=Path, default=ROOT / "data/raw/web_zips")
    ap.add_argument("--out", type=Path, default=ROOT / "data/selfrec")
    ap.add_argument("--min-hand-frames", type=int, default=8)
    a = ap.parse_args(argv)
    (a.out / "keypoints").mkdir(parents=True, exist_ok=True)
    words, letters, skipped = [], [], Counter()
    fs_cols = ["label", "group", "source", "n_hands"] + [f"h{h}_{k}_{c}" for h in range(2) for k in range(21) for c in "xy"]
    fs_rows = []
    seen = set()
    for zname, c in iter_clips(a.inp):
        cid = f"{c.get('clip_id', 'clip')}_{Path(zname).stem}"
        if cid in seen:
            continue
        seen.add(cid)
        target = str(c.get("target", "")).upper().replace(" ", "_")
        kp = to_raw(c.get("keypoints") or [[[0, 0, 0]] * 86])
        hand_frames = int((~np.isnan(kp[:, 9:51, 0]).all(1)).sum())
        if kp.ndim != 3 or kp.shape[1:] != (86, 3) or hand_frames < a.min_hand_frames:
            skipped["tangan terlalu sedikit / format salah"] += 1
            continue
        signer = "OWN_" + str(c.get("signer", "anon")).upper()
        if c.get("category") == "letter" and target in LETTERS:
            # ambil frame tengah (60%) yang ada tangannya, tiap 3 frame -> sampel landmark huruf
            F = len(kp)
            for t in range(int(F * 0.2), int(F * 0.8), 3):
                hs = [kp[t, a_:b_, :2] for a_, b_ in (GROUPS["lhand"], GROUPS["rhand"]) if not np.isnan(kp[t, a_:b_, 0]).all()]
                if not hs:
                    continue
                flat = [float(v) for h in hs for p in h for v in p] + [0.0] * (2 - len(hs)) * 42
                fs_rows.append([target, cid, "own", len(hs)] + [f"{v:.5f}" for v in flat])
            letters.append(target)
        elif target in BISINDO_32_GLOSSES:
            np.savez_compressed(a.out / "keypoints" / f"{cid}.npz", kp=kp)
            words.append({"video_id": f"own_{cid}", "source": "own", "gloss": target, "label": BISINDO_32_GLOSSES.index(target),
                          "signer": signer, "kp_path": _rel(a.out / "keypoints" / f"{cid}.npz"),
                          "rgb_path": "", "split_sd": "train"})
        else:
            skipped[f"target di luar kosakata model: {target}"] += 1
    with open(a.out / "manifest_own.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["video_id", "source", "gloss", "label", "signer", "kp_path", "rgb_path", "split_sd"]); w.writeheader(); w.writerows(words)
    with open(a.out / "fingerspell_landmarks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(fs_cols); w.writerows(fs_rows)
    print(f"[selfrec] klip kata={len(words)} | klip huruf={len(letters)} (sampel landmark={len(fs_rows)}) | dibuang={dict(skipped)}")
    print("[selfrec] per perekam:", dict(Counter(r["signer"] for r in words)))
    print("[selfrec] per kata  :", dict(sorted(Counter(r["gloss"] for r in words).items())))
    print("[selfrec] per huruf :", dict(sorted(Counter(letters).items())))


if __name__ == "__main__":
    main()
