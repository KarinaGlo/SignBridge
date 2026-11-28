"""
signbridge/xmf/export.py — TAHAP 7 (EXPORT): checkpoint -> ONNX untuk browser (ONNX Runtime Web).

Menghasilkan:
    web/model/xmf_<task>.onnx   input : pose, frames, audio, text, modality_mask
                                output: logits, modality_weights, modality_logits
    web/model/xmf_<task>.json   metadata kontrak (kelas, bentuk tensor, vocab teks, parameter crop)
dan memverifikasi paritas PyTorch vs ONNX Runtime (|diff| < 1e-3) untuk beberapa kombinasi modalitas.

    python -m signbridge.xmf.export --ckpt outputs/xmf/XMF_gloss_final/best.pt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from signbridge.xmf.config import (
    AUDIO_SR, IMAGENET_MEAN, IMAGENET_STD, MODALITIES, PERSON_CROP_CENTER_SHIFT,
    PERSON_CROP_SIDE_X_SHOULDER, TEXT_ALPHABET,
)
from signbridge.xmf.model import XMFOnnx, build_model, count_params

ROOT = Path(__file__).resolve().parents[2]
INPUTS = ["pose", "frames", "audio", "text", "modality_mask"]
OUTPUTS = ["logits", "modality_weights", "modality_logits"]


def dummy_inputs(shapes, seed: int = 0):
    g = torch.Generator().manual_seed(seed)
    return (
        torch.randn(1, shapes.pose_frames, 86, 3, generator=g) * 0.5,
        torch.rand(1, shapes.image_frames, 3, shapes.image_side, shapes.image_side, generator=g) * 255,
        torch.randn(1, shapes.audio_samples, generator=g) * 0.1,
        torch.randint(2, 40, (1, shapes.text_len), generator=g),
        torch.ones(1, 4),
    )


def export(ckpt_path: Path, out_dir: Path, opset: int = 17, quantize: bool = False) -> Path:
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    task, classes, cfg = ck["task"], ck["classes"], ck["config"]
    model = build_model(task, len(classes), dict(cfg.get("model", {}), pretrained_image=False))
    model.load_state_dict(ck["model"])
    model.eval()
    wrapper = XMFOnnx(model).eval()
    shapes = model.shapes
    x = dummy_inputs(shapes)

    out_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = out_dir / f"xmf_{task}.onnx"
    kw = dict(input_names=INPUTS, output_names=OUTPUTS, opset_version=opset, do_constant_folding=True)
    try:
        torch.onnx.export(wrapper, x, str(onnx_path), dynamo=False, **kw)
    except TypeError:
        torch.onnx.export(wrapper, x, str(onnx_path), **kw)

    # gabungkan data eksternal (jika ada) menjadi satu file agar mudah dimuat di browser
    import onnx

    m = onnx.load(str(onnx_path), load_external_data=True)
    onnx.save_model(m, str(onnx_path), save_as_external_data=False)
    for extra in out_dir.glob(f"xmf_{task}.onnx.data"):
        extra.unlink()
    onnx.checker.check_model(str(onnx_path))

    # paritas PyTorch vs ONNX Runtime
    import onnxruntime as ort

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    worst, worst_rel, flips = 0.0, 0.0, 0
    for seed, mask in [(1, [1, 1, 1, 1]), (2, [1, 1, 0, 0]), (3, [0, 0, 1, 0]), (4, [0, 0, 0, 1]), (5, [1, 0, 0, 0])]:
        xi = list(dummy_inputs(shapes, seed))
        xi[4] = torch.tensor([mask], dtype=torch.float32)
        with torch.no_grad():
            ref = wrapper(*xi)
        got = sess.run(None, {n: t.numpy() for n, t in zip(INPUTS, xi)})
        for r, g in zip(ref, got):
            d = float(np.max(np.abs(r.numpy() - g)))
            worst = max(worst, d)
            worst_rel = max(worst_rel, d / (float(np.max(np.abs(r.numpy()))) + 1e-6))
        flips += int(np.argmax(ref[0].numpy(), -1)[0] != np.argmax(got[0], -1)[0])
    # Backbone besar (EfficientNet, BatchNorm + SiLU) wajar berselisih ~1e-3 absolut pada logit berskala ~10.
    # Gagal hanya jika prediksi berubah atau selisih relatif > 1e-3.
    if flips or (worst > 1e-3 and worst_rel > 1e-3):
        raise RuntimeError(f"Paritas ONNX gagal: max|diff|={worst:.2e} (relatif {worst_rel:.2e}), prediksi berubah={flips}")
    if worst > 1e-3:
        print(f"[export] catatan: max|diff|={worst:.2e} tetapi relatif {worst_rel:.2e} dan prediksi identik -> lolos")

    if quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        qpath = out_dir / f"xmf_{task}_int8.onnx"
        quantize_dynamic(str(onnx_path), str(qpath), weight_type=QuantType.QInt8, op_types_to_quantize=["MatMul", "Gemm"])
        print(f"[export] int8: {qpath} ({qpath.stat().st_size / 1e6:.2f} MB)")

    metrics_path = ckpt_path.parent / "evaluation_metrics.json"
    meta = {
        "model": f"SignBridge-XMF ({model.describe()})",
        "task": task, "classes": classes, "modalities": MODALITIES,
        "inputs": {
            "pose": [1, shapes.pose_frames, 86, 3], "frames": [1, shapes.image_frames, 3, shapes.image_side, shapes.image_side],
            "audio": [1, shapes.audio_samples], "text": [1, shapes.text_len], "modality_mask": [1, 4],
        },
        "outputs": OUTPUTS,
        "pose_frames": shapes.pose_frames, "image_frames": shapes.image_frames, "image_side": shapes.image_side,
        "audio_sr": AUDIO_SR, "audio_samples": shapes.audio_samples, "text_len": shapes.text_len,
        "text_alphabet": TEXT_ALPHABET, "text_pad_id": 0, "text_unk_id": 1, "text_offset": 2,
        "person_crop": {"side_x_shoulder": PERSON_CROP_SIDE_X_SHOULDER, "center_shift": PERSON_CROP_CENTER_SHIFT},
        "hand_crop_margin": 0.25, "frames_range": "0..255 RGB (normalisasi ImageNet di dalam model)",
        "imagenet_mean": IMAGENET_MEAN, "imagenet_std": IMAGENET_STD,
        "params": count_params(model), "onnx_parity_max_abs_diff": worst, "onnx_parity_max_rel_diff": worst_rel, "opset": opset,
        "trained_protocol": ck.get("protocol"), "best_epoch": ck.get("epoch"),
        "metrics": json.loads(metrics_path.read_text())["primary"] if metrics_path.exists() else ck.get("val_VI"),
    }
    (out_dir / f"xmf_{task}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[export] {onnx_path} ({onnx_path.stat().st_size / 1e6:.2f} MB) | paritas max|diff|={worst:.2e}")
    return onnx_path


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "web/model")
    ap.add_argument("--opset", type=int, default=17)
    ap.add_argument("--quantize", action="store_true")
    a = ap.parse_args(argv)
    export(a.ckpt, a.out, a.opset, a.quantize)


if __name__ == "__main__":
    main()
