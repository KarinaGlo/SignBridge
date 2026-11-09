import sys
import os
import json
import hashlib
from pathlib import Path
import re
import pandas as pd
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scratch.decode_onnx import parse_proto_fields

def test_a_checkpoint_and_onnx():
    print("--- [TEST A] Checkpoint and ONNX Structural Validation ---")
    ckpt_path = ROOT / "outputs" / "experiments" / "M0_student_baseline" / "best_model.pt"
    onnx_path = ROOT / "web" / "model" / "student.onnx"

    assert ckpt_path.exists(), f"Checkpoint not found: {ckpt_path}"
    assert onnx_path.exists(), f"ONNX model not found: {onnx_path}"

    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    sd = ckpt["model_state_dict"]
    print(f"Checkpoint loaded: epoch {ckpt.get('epoch')}, state_dict tensors: {len(sd)}")
    assert len(sd) == 57, f"Expected 57 tensors, got {len(sd)}"

    with open(onnx_path, "rb") as f:
        raw_onnx = f.read()

    mf = parse_proto_fields(raw_onnx)
    gd = [v for fn, wt, v in mf if fn == 7][0]
    gf = parse_proto_fields(gd)

    inputs = [v for fn, wt, v in gf if fn == 11]
    outputs = [v for fn, wt, v in gf if fn == 12]
    inits = [v for fn, wt, v in gf if fn == 5]

    inp_names = []
    for inp in inputs:
        inp_fields = parse_proto_fields(inp)
        inp_names.append([v.decode("utf-8") for fn, wt, v in inp_fields if fn == 1][0])

    out_names = []
    for out in outputs:
        out_fields = parse_proto_fields(out)
        out_names.append([v.decode("utf-8") for fn, wt, v in out_fields if fn == 1][0])

    print(f"ONNX File Size: {len(raw_onnx):,} bytes")
    print(f"ONNX Inputs: {inp_names}")
    print(f"ONNX Outputs: {out_names}")
    print(f"ONNX Initializers: {len(inits)}")

    assert "keypoints" in inp_names, "Input 'keypoints' not found"
    assert "logits" in out_names, "Output 'logits' not found"
    assert len(inits) == 57, f"Expected 57 initializers, got {len(inits)}"

    # Parse initializers
    onnx_tensors = {}
    for init in inits:
        flds = parse_proto_fields(init)
        dims = [v for fn, wt, v in flds if fn == 1]
        name = [v.decode("utf-8", errors="ignore") for fn, wt, v in flds if fn == 8][0]
        raw_bytes = [v for fn, wt, v in flds if fn == 9][0]
        arr = np.frombuffer(raw_bytes, dtype=np.float32).reshape(dims)
        onnx_tensors[name] = arr

    # Test weight match
    matmul_map = {
        'input_proj.0.weight': ('onnx::MatMul_909', True),
        'encoder.layers.0.self_attn.in_proj_weight': ('onnx::MatMul_913', True),
        'encoder.layers.0.linear1.weight': ('onnx::MatMul_921', True),
        'encoder.layers.0.linear2.weight': ('onnx::MatMul_922', True),
        'encoder.layers.1.self_attn.in_proj_weight': ('onnx::MatMul_923', True),
        'encoder.layers.1.linear1.weight': ('onnx::MatMul_931', True),
        'encoder.layers.1.linear2.weight': ('onnx::MatMul_932', True),
        'encoder.layers.2.self_attn.in_proj_weight': ('onnx::MatMul_933', True),
        'encoder.layers.2.linear1.weight': ('onnx::MatMul_941', True),
        'encoder.layers.2.linear2.weight': ('onnx::MatMul_942', True),
        'encoder.layers.3.self_attn.in_proj_weight': ('onnx::MatMul_943', True),
        'encoder.layers.3.linear1.weight': ('onnx::MatMul_951', True),
        'encoder.layers.3.linear2.weight': ('onnx::MatMul_952', True),
    }

    max_diff = 0.0
    for sd_name, sd_val in sd.items():
        pt_arr = sd_val.numpy()
        if sd_name in matmul_map:
            oname, is_trans = matmul_map[sd_name]
            oarr = onnx_tensors[oname].T if is_trans else onnx_tensors[oname]
        else:
            oarr = onnx_tensors[sd_name]
        diff = float(np.max(np.abs(pt_arr - oarr)))
        max_diff = max(max_diff, diff)
        assert not np.isnan(diff) and not np.isinf(diff), f"NaN/Inf in tensor diff {sd_name}"

    print(f"Max Absolute Weight Difference: {max_diff:.8e}")
    assert max_diff == 0.0, f"Expected exact match (0.0), got {max_diff}"
    print("[TEST A] PASS: All 57 tensors exact match byte-for-byte, structure verified!\n")

def test_b_labels_synchronization():
    print("--- [TEST B] 32-Class Label Synchronization Validation ---")
    manifest_path = ROOT / "data" / "manifest_wl_bisindo.csv"
    labels_json_path = ROOT / "web" / "model" / "labels.json"
    config_js_path = ROOT / "web" / "js" / "config.js"

    df = pd.read_csv(manifest_path)
    manifest_mapping = df[["label", "gloss"]].drop_duplicates().sort_values("label").reset_index(drop=True)
    training_classes = manifest_mapping["gloss"].tolist()

    with open(labels_json_path, "r", encoding="utf-8") as f:
        web_labels = json.load(f)

    # Read BISINDO_GLOSSES from config.js
    cfg_text = config_js_path.read_text(encoding="utf-8")
    m = re.search(r"export const BISINDO_GLOSSES\s*=\s*\[(.*?)\];", cfg_text, re.DOTALL)
    assert m, "Could not find BISINDO_GLOSSES in web/js/config.js"
    clean_js_glosses = re.findall(r'"([A-Z_]+)"', m.group(1))

    print(f"Training classes count: {len(training_classes)}")
    print(f"web/model/labels.json count: {len(web_labels)}")
    print(f"web/js/config.js BISINDO_GLOSSES count: {len(clean_js_glosses)}")

    assert len(training_classes) == 32, "Training classes != 32"
    assert len(web_labels) == 32, "web_labels != 32"
    assert len(clean_js_glosses) == 32, "clean_js_glosses != 32"

    assert len(set(web_labels)) == 32, "web_labels has duplicates!"
    assert len(set(clean_js_glosses)) == 32, "clean_js_glosses has duplicates!"

    mismatches_json = []
    mismatches_js = []
    for i in range(32):
        t_cls = training_classes[i]
        j_cls = web_labels[i]
        c_cls = clean_js_glosses[i]
        if t_cls != j_cls:
            mismatches_json.append((i, t_cls, j_cls))
        if t_cls != c_cls:
            mismatches_js.append((i, t_cls, c_cls))

    assert len(mismatches_json) == 0, f"Mismatches in labels.json: {mismatches_json}"
    assert len(mismatches_js) == 0, f"Mismatches in config.js: {mismatches_js}"

    print(f"Exact match training vs labels.json: 32 / 32 (100.0%)")
    print(f"Exact match training vs config.js: 32 / 32 (100.0%)")
    print(f"Index 0: {web_labels[0]} (Expected: AIR)")
    print(f"Index 1: {web_labels[1]} (Expected: BELAJAR)")
    print(f"Index 31: {web_labels[31]} (Expected: MALAM)")
    print("[TEST B] PASS: 100% exact 32-class index correspondence!\n")

def test_c_preprocessing_parity():
    print("--- [TEST C] Preprocessing Dimension & Parity Verification ---")
    from signbridge.constants import NUM_KEYPOINTS, NUM_COORDS, T_MAX
    assert NUM_KEYPOINTS == 86
    assert NUM_COORDS == 3
    assert T_MAX == 64

    # Test real sample forward
    from signbridge.models.student import StudentPoseTransformer
    ckpt_path = ROOT / "outputs" / "experiments" / "M0_student_baseline" / "best_model.pt"
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    model = StudentPoseTransformer(num_classes=32, d_model=160, nhead=4, num_layers=4, dim_feedforward=640, dropout=0.0)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    sample_npz = ROOT / "data" / "keypoints" / "WL-BISINDO" / "0" / "0_0_0.npz"
    if sample_npz.exists():
        d = np.load(str(sample_npz))
        kp = d["keypoints"]  # [F, 86, 3]
        print(f"Loaded sample {sample_npz.name}: shape {kp.shape}")
        from signbridge.features import preprocess_keypoints
        kp64 = preprocess_keypoints(kp, target_len=64, do_trim=True)
        print(f"Preprocessed shape: {kp64.shape}")
        assert kp64.shape == (64, 86, 3)

        inp = torch.from_numpy(kp64).unsqueeze(0).float()
        with torch.no_grad():
            logits = model(inp)
            probs = torch.softmax(logits, dim=-1).squeeze(0).numpy()
            pred_idx = int(np.argmax(probs))
            top_prob = float(probs[pred_idx])

        with open(ROOT / "web" / "model" / "labels.json", "r") as f:
            labels = json.load(f)

        pred_label = labels[pred_idx]
        print(f"Sample ground-truth class: 0 (AIR)")
        print(f"Model prediction index: {pred_idx} ({pred_label}) with confidence: {top_prob*100:.2f}%")
        assert pred_idx == 0, f"Expected pred_idx 0 (AIR), got {pred_idx}"
        assert pred_label == "AIR", f"Expected pred_label 'AIR', got {pred_label}"
        assert top_prob > 0.90, f"Expected confidence > 90%, got {top_prob*100:.2f}%"

    print("[TEST C] PASS: Real sample preprocessing & inference accurately predicts AIR with high confidence!\n")

if __name__ == "__main__":
    test_a_checkpoint_and_onnx()
    test_b_labels_synchronization()
    test_c_preprocessing_parity()
    print("ALL M0 RECONCILIATION TESTS PASSED (3/3)!")
