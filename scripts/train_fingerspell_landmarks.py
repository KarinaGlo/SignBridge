"""Latih pengenal abjad jari BISINDO A–Z dari landmark tangan -> web/model/fingerspell_mlp.json

Sumber data (boleh digabung):
  --krisna DIR    data/ dari github.com/KrisnaSantosa15/realtime-bisindo-classification (MIT): train/val/test.csv,
                  42 landmark (2 tangan) x (x,y,z) berselang per titik, kolom pertama 'label'.
  --landmarks CSV hasil `--extract` di bawah (kolom: label,group,source,n_hands,h0_0_x,h0_0_y,...,h1_20_y)
  --extract DIR   folder foto A/..Z/ (mis. Mendeley 4.466 foto di PC Gloria) -> ekstraksi MediaPipe Hands -> CSV
                  (butuh: pip install mediapipe==0.10.14, memakai mp.solutions.hands)

Contoh (PC Gloria):
  python scripts/train_fingerspell_landmarks.py --extract data/raw/image/bisindo_alphabet --out-csv data/fingerspell/mendeley_landmarks.csv
  python scripts/train_fingerspell_landmarks.py --krisna ../realtime-bisindo-classification/data \\
         --landmarks data/fingerspell/mendeley_landmarks.csv --test-source mendeley
`--test-source mendeley` = uji LINTAS-DATASET (dilatih tanpa foto Mendeley, diuji di Mendeley): angka paling jujur.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signbridge.fingerspell_landmarks import (LETTERS, MLP, augment_hands, export_weights,  # noqa: E402
                                              hand_features)


# ----------------------------------------------------------------- pemuatan data
def load_krisna(d: Path):
    """Return dict split -> list of (label, hands, group)."""
    out = {}
    for split in ("train", "val", "test"):
        f = d / f"{split}.csv"
        if not f.exists():
            continue
        rows = []
        with open(f, encoding="utf-8") as fh:
            r = csv.reader(fh); next(r)
            for i, row in enumerate(r):
                v = np.asarray([float(x) if x.strip() else np.nan for x in row[1:]], np.float64).reshape(42, 3)
                ok = lambda h: np.isfinite(h).all() and np.abs(h).sum() > 0   # x,y,z berselang per titik
                hands = [h for h in (v[:21], v[21:]) if ok(h)]
                if not hands:
                    continue
                rows.append((row[0].strip().upper(), hands, f"krisna_{split}_{i}"))
        out[split] = rows
    return out


def load_landmark_csv(path: Path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            hands = []
            for h in range(int(r["n_hands"])):
                hands.append(np.array([[float(r[f"h{h}_{k}_x"]), float(r[f"h{h}_{k}_y"])] for k in range(21)]))
            rows.append((r["label"].upper(), hands, r["group"], r.get("source", "landmarks")))
    return rows


def extract_images(img_dir: Path, out_csv: Path, source: str):
    """Foto A/..Z/*.jpg -> landmark MediaPipe Hands (static, maks 2 tangan) -> CSV."""
    import cv2
    import mediapipe as mp
    hands_sol = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.3)
    cols = ["label", "group", "source", "n_hands"] + [f"h{h}_{k}_{a}" for h in range(2) for k in range(21) for a in "xy"]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    n = found = 0
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(cols)
        for f in sorted(img_dir.rglob("*")):
            if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue
            lab = next((p.upper() for p in reversed(f.relative_to(img_dir).parts[:-1]) if p.upper() in LETTERS), None)
            if lab is None:
                continue
            n += 1
            img = cv2.imread(str(f))
            if img is None:
                continue
            res = hands_sol.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            hs = [[(lm.x, lm.y) for lm in h.landmark] for h in (res.multi_hand_landmarks or [])][:2]
            if not hs:
                continue
            found += 1
            flat = [v for h in hs for p in h for v in p] + [0.0] * (2 - len(hs)) * 42
            w.writerow([lab, f"{source}_{f.stem}", source, len(hs)] + [f"{v:.5f}" for v in flat])
    print(f"[ekstraksi] {found}/{n} foto ada tangannya -> {out_csv}")


# ----------------------------------------------------------------- latih & evaluasi
def featurize(rows, rng=None, copies=0):
    X, y = [], []
    for lab, hands, *_ in rows:
        X.append(hand_features(hands)); y.append(lab)
        for _ in range(copies):
            X.append(hand_features(augment_hands(hands, rng))); y.append(lab)
    return np.asarray(X, np.float32), np.asarray(y)


def report(name, model, rows):
    if not rows:
        return None
    X, y = featurize(rows)
    p = np.asarray(model.labels)[model.predict_proba(X).argmax(1)]
    acc = float((p == y).mean())
    per = {L: float((p[y == L] == L).mean()) for L in LETTERS if (y == L).any()}
    conf = Counter((a, b) for a, b in zip(y, p) if a != b).most_common(8)
    f1s = []
    for L in per:
        tp = ((p == L) & (y == L)).sum(); fp = ((p == L) & (y != L)).sum(); fn = ((p != L) & (y == L)).sum()
        f1s.append(0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    print(f"[{name}] n={len(y)} akurasi={acc:.4f} macro-F1={np.mean(f1s):.4f} | sering tertukar: "
          + ", ".join(f"{a}->{b}({c})" for (a, b), c in conf))
    return {"n": len(y), "acc": acc, "macro_f1": float(np.mean(f1s)), "per_letter": per,
            "top_confusions": [[a, b, c] for (a, b), c in conf]}


def robustness(model, rows, rng):
    """Uji ketahanan: cermin (kidal), satu tangan hilang, rotasi/skala/geser."""
    out = {}
    for name, fn in {
        "cermin": lambda hs: [np.c_[1 - np.asarray(h)[:, 0], np.asarray(h)[:, 1]] for h in hs],
        "tangan_kedua_hilang": lambda hs: hs[:1],
        "rotasi_skala_geser": lambda hs: augment_hands(hs, rng) if False else _geom(hs, rng),
    }.items():
        rr = [(lab, fn(hands)) for lab, hands, *_ in rows]
        X, y = featurize(rr)
        p = np.asarray(model.labels)[model.predict_proba(X).argmax(1)]
        out[name] = float((p == y).mean())
    print("[ketahanan] " + " | ".join(f"{k}={v:.3f}" for k, v in out.items()))
    return out


def _geom(hs, rng):
    hs = [np.asarray(h, np.float64)[:, :2] for h in hs]
    c = np.concatenate(hs).mean(0); th = np.deg2rad(rng.uniform(-12, 12)); s = rng.uniform(0.8, 1.2)
    R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]) * s
    return [(h - c) @ R.T + c + rng.uniform(-.1, .1, 2) for h in hs]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--krisna", type=Path)
    ap.add_argument("--landmarks", type=Path, nargs="*", default=[])
    ap.add_argument("--extract", type=Path)
    ap.add_argument("--out-csv", type=Path, default=Path("data/fingerspell/landmarks.csv"))
    ap.add_argument("--source", default="mendeley")
    ap.add_argument("--test-source", default=None, help="sumber yang SELURUHNYA dijadikan uji lintas-dataset")
    ap.add_argument("--copies", type=int, default=3, help="salinan augmentasi per sampel latih")
    ap.add_argument("--hidden", default="256,128")
    ap.add_argument("--out", type=Path, default=Path("web/model/fingerspell_mlp.json"))
    ap.add_argument("--report", type=Path, default=Path("outputs/experiments/F1_fingerspell_mlp/result.json"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(argv)
    if a.extract:
        extract_images(a.extract, a.out_csv, a.source)
        return

    from sklearn.neural_network import MLPClassifier
    rng = np.random.default_rng(a.seed)
    train, val, test, cross = [], [], [], []
    if a.krisna:
        k = load_krisna(a.krisna)
        train += k.get("train", []); val += k.get("val", []); test += k.get("test", [])
    for p in a.landmarks:
        rows = load_landmark_csv(p)
        if a.test_source and rows and rows[0][3] == a.test_source:
            cross += rows; continue
        groups = sorted({r[2] for r in rows}); rng.shuffle(groups)
        gte, gva = set(groups[: len(groups) // 7]), set(groups[len(groups) // 7: 2 * len(groups) // 7])
        for r in rows:
            (test if r[2] in gte else val if r[2] in gva else train).append(r)
    print(f"[data] latih={len(train)} val={len(val)} uji={len(test)} uji-lintas-dataset={len(cross)}")

    Xtr, ytr = featurize(train, rng, a.copies)
    mean, std = Xtr.mean(0), Xtr.std(0) + 1e-6
    clf = MLPClassifier(hidden_layer_sizes=tuple(int(h) for h in a.hidden.split(",")), alpha=3e-4,
                        batch_size=256, learning_rate_init=1e-3, max_iter=200, early_stopping=True,
                        validation_fraction=0.1, n_iter_no_change=12, random_state=a.seed)
    clf.fit((Xtr - mean) / std, ytr)
    meta = {"sources": {"krisna": bool(a.krisna), "landmarks": [str(p) for p in a.landmarks]},
            "train_samples": int(len(train)), "augment_copies": a.copies}
    w = export_weights(clf, mean, std, a.out, meta)
    model = MLP(w)
    res = {"model": "F1_fingerspell_mlp", "hidden": a.hidden, "params": int(sum(np.size(l["W"]) + np.size(l["b"]) for l in w["layers"])),
           "val": report("val", model, val), "test": report("uji", model, test), "cross_dataset": report("lintas-dataset", model, cross),
           "robustness_test": robustness(model, test, rng), "web_model": str(a.out),
           "catatan": "uji Krisna berasal dari augmentasi foto yang sama -> optimistis; angka jujur = cross_dataset"}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.report, "w"), indent=2)
    print(f"[ok] {a.out} ({a.out.stat().st_size/1024:.0f} KB) + {a.report}")


if __name__ == "__main__":
    main()
