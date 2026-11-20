"""
signbridge/export_onnx_multimodal.py — Ekspor M6 ke ONNX + uji paritas PyTorch vs onnxruntime.

    python -m signbridge.export_onnx_multimodal \
        --ckpt outputs/experiments/M6_multimodal_fusion/best_model.pt --out web/model/multimodal_fusion.onnx

Masukan ONNX : pose[1,64,86,3] f32, image[1,3,112,112] f32, audio[1,64,248] f32, text[1,64] i64, modality_mask[1,4] f32
Keluaran ONNX: logits[1,32], modality_weights[1,4]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from signbridge.models.multimodal import MultimodalOnnxWrapper, SignBridgeMultimodalFusion
from signbridge.multimodal.constants import AUDIO_SHAPE, IMAGE_SHAPE, POSE_SHAPE, TEXT_MAX_LEN

INPUT_NAMES = ["pose", "image", "audio", "text", "modality_mask"]
OUTPUT_NAMES = ["logits", "modality_weights"]


def dummy_inputs(batch: int = 1, seed: int = 0):
    g = torch.Generator().manual_seed(seed)
    return (
        torch.randn(batch, *POSE_SHAPE, generator=g),
        torch.randn(batch, *IMAGE_SHAPE, generator=g),
        torch.randn(batch, *AUDIO_SHAPE, generator=g),
        torch.randint(2, 40, (batch, TEXT_MAX_LEN), generator=g),
        torch.tensor([[1.0, 1.0, 1.0, 1.0]] * batch),
    )


def export(model: SignBridgeMultimodalFusion, out_path: Path, opset: int = 17) -> Path:
    model.eval()
    wrapper = MultimodalOnnxWrapper(model).eval()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        wrapper, dummy_inputs(), str(out_path),
        input_names=INPUT_NAMES, output_names=OUTPUT_NAMES,
        dynamic_axes={n: {0: "batch"} for n in INPUT_NAMES + OUTPUT_NAMES},
        opset_version=opset, do_constant_folding=True,
    )
    return out_path


def check_parity(model: SignBridgeMultimodalFusion, onnx_path: Path, tol: float = 1e-4) -> float:
    import onnxruntime as ort

    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    worst = 0.0
    for mask in ([1, 1, 1, 1], [1, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0]):
        inp = list(dummy_inputs(seed=sum(mask)))
        inp[4] = torch.tensor([mask], dtype=torch.float32)
        with torch.no_grad():
            ref = MultimodalOnnxWrapper(model).eval()(*inp)
        got = sess.run(None, {n: t.numpy() for n, t in zip(INPUT_NAMES, inp)})
        for r, o in zip(ref, got):
            worst = max(worst, float(np.max(np.abs(r.numpy() - o))))
    if worst > tol:
        raise AssertionError(f"Paritas PyTorch vs ONNX gagal: selisih maks {worst:.2e} > {tol}")
    return worst


def main() -> None:
    ap = argparse.ArgumentParser(description="Ekspor M6 multimodal fusion ke ONNX")
    ap.add_argument("--ckpt", type=str, default="outputs/experiments/M6_multimodal_fusion/best_model.pt")
    ap.add_argument("--out", type=str, default="web/model/multimodal_fusion.onnx")
    args = ap.parse_args()

    ckpt = torch.load(args.ckpt, map_location="cpu")
    mcfg = (ckpt.get("config") or {}).get("model", {})
    model = SignBridgeMultimodalFusion(num_classes=32, **mcfg)
    model.load_state_dict(ckpt["model"])
    path = export(model, Path(args.out))
    diff = check_parity(model, path)
    print(f"[export_onnx_multimodal] {path} ({path.stat().st_size / 1e6:.2f} MB), selisih maks PyTorch-ONNX {diff:.2e}")


if __name__ == "__main__":
    main()
