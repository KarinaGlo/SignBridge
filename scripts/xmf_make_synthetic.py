"""
scripts/xmf_make_synthetic.py — Data SINTETIS untuk uji asap (smoke test) pipeline XMF.

BUKAN data penelitian. Hanya memastikan train -> evaluate -> export -> web berjalan tanpa MediaPipe/GPU.
Menulis ke data/xmf_synth/ (terpisah dari data asli) beserta config configs/xmf_synth_<task>.yaml.

    python scripts/xmf_make_synthetic.py --task gloss --per-class 12
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signbridge.xmf.config import SHAPES, classes_for, encode_text, texts_for  # noqa: E402
from signbridge.xmf.preprocess import PROCESSED_COLUMNS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["gloss", "alphabet"], default="gloss")
    ap.add_argument("--per-class", type=int, default=12)
    ap.add_argument("--out", type=Path, default=ROOT / "data/xmf_synth")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    sh, classes = SHAPES[a.task], classes_for(a.task)
    C = len(classes)
    d = a.out / a.task
    d.mkdir(parents=True, exist_ok=True)
    proto_pose = rng.normal(0, 1, (C, 86, 3)).astype(np.float32)
    proto_rgb = rng.integers(30, 225, (C, 3)).astype(np.float32)
    rows = []
    for c in range(C):
        for k in range(a.per_class):
            signer = k % 5
            t = np.linspace(0, 1, sh.pose_frames)[:, None, None]
            pose = proto_pose[c] * (0.6 + 0.4 * np.sin(2 * np.pi * t * (1 + c % 3))) + rng.normal(0, .3, (sh.pose_frames, 86, 3))
            frames = np.clip(proto_rgb[c] + rng.normal(0, 40, (sh.image_frames, sh.image_side, sh.image_side, 3)), 0, 255)
            tt = np.arange(sh.audio_samples) / 16000
            audio = 0.3 * np.sin(2 * np.pi * (200 + 40 * c) * tt) * (np.abs(tt - 1.25) < .4) + rng.normal(0, .02, tt.size)
            txt = texts_for(a.task)[classes[c]][k % 3]
            sid = f"synth_{a.task}_c{c}_k{k}"
            npz = d / f"{sid}.npz"
            np.savez_compressed(npz, pose=pose.astype(np.float16), frames=frames.astype(np.uint8),
                                audio=audio.astype(np.float16), text=np.array(encode_text(txt), np.int16),
                                mask=np.ones(4, np.float32), label=np.int64(c), text_str=np.array(txt))
            split = "test" if k % 6 == 5 else ("val" if k % 6 == 4 else "train")
            rows.append({"sample_id": sid, "task": a.task, "label": c, "class_name": classes[c], "signer": signer,
                         "group": f"s{signer}", "npz_path": str(npz.relative_to(ROOT)), "has_video": 1,
                         "has_image": 1, "has_audio": 1, "has_text": 1, "image_source": "synthetic",
                         "split_sd": split, "split_si": "test" if signer == 4 else split,
                         "split_final": "val" if split == "val" else "train", "split": split})
    csv_path = a.out / f"{a.task}_processed.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PROCESSED_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    cfg = yaml.safe_load((ROOT / f"configs/xmf_{a.task}.yaml").read_text())
    cfg.update({"experiment_id": f"XMF_SYNTH_{a.task}", "processed_csv": str(csv_path.relative_to(ROOT)),
                "audio_bank": None, "num_workers": 0, "cache": True})
    cfg["model"]["pretrained_image"] = False
    cfg["training"].update({"max_epochs": 4, "batch_size": 16})
    (ROOT / f"configs/xmf_synth_{a.task}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"[synth] {len(rows)} sampel SINTETIS -> {csv_path}")


if __name__ == "__main__":
    main()
