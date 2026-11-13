"""
scripts/make_parity_fixture.py — Buat fixture JSON untuk uji paritas Python <-> JS.
Menghasilkan tests/js/fixtures/parity_fixture.json (keypoint & handcrop).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import NUM_COORDS, NUM_KEYPOINTS, T_MAX, select_from_holistic
from signbridge.features import (
    normalize_pose,
    preprocess_keypoints,
    resample_frames,
    trim_inactive,
)
from signbridge.image.crop import (
    compute_hand_crop_box,
    crop_and_resize_hand,
    normalize_imagenet,
)


def generate_parity_fixture(out_path: str | Path = "tests/js/fixtures/parity_fixture.json") -> Path:
    rng = np.random.default_rng(2026)

    # 1. Uji select_from_holistic
    pose33 = rng.uniform(0.1, 0.9, size=(33, 3)).astype(np.float32)
    left21 = rng.uniform(0.2, 0.8, size=(21, 3)).astype(np.float32)
    right21 = rng.uniform(0.2, 0.8, size=(21, 3)).astype(np.float32)
    face468 = rng.uniform(0.3, 0.7, size=(468, 3)).astype(np.float32)
    selected86 = select_from_holistic(pose33, left21, right21, face468)

    # 2. Sekuens keypoint dengan frame diam di awal & akhir
    F = 45
    kp_raw = np.zeros((F, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)
    # Frame 5..37 aktif
    active_len = 33
    active_kp = rng.uniform(0.15, 0.85, size=(active_len, NUM_KEYPOINTS, NUM_COORDS)).astype(np.float32)
    # Pastikan bahu kiri (idx 1) dan kanan (idx 2) terpisah jelas
    active_kp[:, 1, :] = np.array([0.62, 0.42, -0.05], dtype=np.float32)
    active_kp[:, 2, :] = np.array([0.38, 0.42, -0.05], dtype=np.float32)
    kp_raw[5:38] = active_kp

    trimmed = trim_inactive(kp_raw)
    normed, valid_mask = normalize_pose(trimmed)
    resampled, _ = resample_frames(normed, valid_mask, target_len=T_MAX)
    full_preproc, _ = preprocess_keypoints(kp_raw, target_len=T_MAX, trim=True)

    # 3. Hand crop & ImageNet normalization fixture (ukuran 32x40 agar JSON ringkas)
    img_h, img_w = 32, 40
    img_rgb = rng.integers(0, 256, size=(img_h, img_w, 3), dtype=np.uint8).astype(np.float32)
    hand_lm = rng.uniform(0.25, 0.75, size=(21, 3)).astype(np.float32)
    box = compute_hand_crop_box(hand_lm, img_w=img_w, img_h=img_h, margin=0.25)
    resized_small, _ = crop_and_resize_hand(img_rgb, hand_lm, out_size=16, margin=0.25)
    imagenet_chw = normalize_imagenet(resized_small)

    payload = {
        "holistic": {
            "pose33": pose33.tolist(),
            "left21": left21.tolist(),
            "right21": right21.tolist(),
            "face468": face468.tolist(),
            "expected_selected86": selected86.tolist(),
        },
        "sequence": {
            "kp_raw": kp_raw.tolist(),
            "expected_trimmed": trimmed.tolist(),
            "expected_normed": normed.tolist(),
            "expected_resampled": resampled.tolist(),
            "expected_preprocessed": full_preproc.tolist(),
        },
        "handcrop": {
            "img_h": img_h,
            "img_w": img_w,
            "img_rgb": img_rgb.tolist(),
            "hand_lm": hand_lm.tolist(),
            "expected_box": box,
            "out_size": 16,
            "expected_resized": resized_small.reshape(-1).tolist(),
            "expected_imagenet_chw": imagenet_chw.reshape(-1).tolist(),
        },
    }

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Parity fixture disimpan ke {target}")
    return target


if __name__ == "__main__":
    generate_parity_fixture()
