"""
scripts/web_record_to_npz.py — Konversi rekaman JSON/ZIP dari web ke .npz dan manifest CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import BISINDO_32_GLOSSES, MANIFEST_COLUMNS, NUM_COORDS, NUM_KEYPOINTS


def convert_web_records(
    in_dir: Path,
    out_kp_dir: Path,
    out_manifest: Path,
) -> int:
    out_kp_dir.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    json_payloads: list[tuple[str, dict]] = []
    if in_dir.exists():
        for jf in sorted(in_dir.rglob("*_kp.json")):
            json_payloads.append((jf.stem, json.loads(jf.read_text(encoding="utf-8"))))
        for zf in sorted(in_dir.rglob("*.zip")):
            with zipfile.ZipFile(zf, "r") as z:
                for name in z.namelist():
                    if name.endswith("_kp.json"):
                        data = json.loads(z.read(name).decode("utf-8"))
                        json_payloads.append((Path(name).stem, data))

    for idx, (stem, payload) in enumerate(json_payloads):
        gloss = str(payload.get("target", "HALO")).upper()
        label = BISINDO_32_GLOSSES.index(gloss) if gloss in BISINDO_32_GLOSSES else 0
        signer = str(payload.get("signer", "S01"))
        kp_arr = np.asarray(payload.get("keypoints", []), dtype=np.float32)
        if kp_arr.ndim != 3 or kp_arr.shape[1:] != (NUM_KEYPOINTS, NUM_COORDS):
            kp_arr = np.zeros((32, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)

        vid_id = str(payload.get("clip_id", f"selfrec_{stem}_{idx:03d}"))
        npz_path = out_kp_dir / f"{vid_id}.npz"
        np.savez_compressed(npz_path, keypoints=kp_arr, gloss=gloss, label=label, signer=signer)

        rows.append(
            {
                "video_id": vid_id,
                "source": "selfrec",
                "gloss": gloss,
                "label": label,
                "signer": signer,
                "kp_path": str(npz_path.as_posix()),
                "rgb_path": "",
                "split_sd": "train" if idx % 5 < 3 else ("val" if idx % 5 == 3 else "test"),
            }
        )

    with out_manifest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(MANIFEST_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Konversi rekaman web ke .npz")
    parser.add_argument("--in", dest="in_dir", type=str, default="data/raw/selfrec")
    parser.add_argument("--out-kp", type=str, default="data/keypoints/selfrec")
    parser.add_argument("--out-manifest", type=str, default="data/manifest_selfrec.csv")
    args = parser.parse_args()

    n = convert_web_records(Path(args.in_dir), Path(args.out_kp), Path(args.out_manifest))
    print(f"[web_record_to_npz] Mengonversi {n} klip ke {args.out_manifest}")


if __name__ == "__main__":
    main()

