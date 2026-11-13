import sys
import os
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.models.student import StudentPoseTransformer

def export_m0():
    ckpt_path = ROOT / "outputs" / "experiments" / "M0_student_baseline" / "best_model.pt"
    out_path = ROOT / "scratch" / "student_m0_test.onnx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading checkpoint: {ckpt_path}")
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    
    cfg = ckpt.get("config", {})
    model_cfg = cfg.get("model", {})
    
    model = StudentPoseTransformer(
        num_classes=32,
        d_model=model_cfg.get("d_model", 160),
        nhead=model_cfg.get("nhead", 4),
        num_layers=model_cfg.get("num_layers", 4),
        dim_feedforward=model_cfg.get("dim_feedforward", 640),
        dropout=0.0,
        max_len=64,
        num_keypoints=86
    )
    
    missing, unexpected = model.load_state_dict(ckpt["model_state_dict"], strict=True)
    assert not missing and not unexpected, f"Mismatch: missing={missing}, unexpected={unexpected}"
    model.eval()
    
    dummy_input = torch.randn(1, 64, 86, 3, dtype=torch.float32)
    
    try:
        import onnx
    except ImportError:
        try:
            from torch.onnx._internal import onnx_proto_utils
            onnx_proto_utils._add_onnxscript_fn = lambda model_bytes, custom_opsets: model_bytes
        except Exception as e:
            print("Monkeypatch error:", e)

    print(f"Exporting to: {out_path}")
    torch.onnx.export(
        model,
        dummy_input,
        str(out_path),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["keypoints"],
        output_names=["logits"],
        dynamic_axes={
            "keypoints": {0: "batch_size"},
            "logits": {0: "batch_size"}
        }
    )
    print("Export finished successfully!")
    print(f"File size: {out_path.stat().st_size:,} bytes")

if __name__ == "__main__":
    export_m0()
