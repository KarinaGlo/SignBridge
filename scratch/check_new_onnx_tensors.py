import sys, os
from pathlib import Path
sys.path.insert(0, os.path.abspath('.'))
import torch
import numpy as np
from scratch.decode_onnx import parse_proto_fields

# Load PyTorch checkpoint
ckpt = torch.load('outputs/experiments/M0_student_baseline/best_model.pt', map_location='cpu')
sd = ckpt['model_state_dict']

# Load ONNX model initializers
with open('scratch/student_m0_test.onnx', 'rb') as f:
    raw = f.read()

mf = parse_proto_fields(raw)
gd = [v for fn, wt, v in mf if fn == 7][0]
gf = parse_proto_fields(gd)
inits = [v for fn, wt, v in gf if fn == 5]

onnx_tensors = {}
for init in inits:
    flds = parse_proto_fields(init)
    dims = [v for fn, wt, v in flds if fn == 1]
    name = [v.decode('utf-8', errors='ignore') for fn, wt, v in flds if fn == 8][0]
    raw_bytes = [v for fn, wt, v in flds if fn == 9][0]
    arr = np.frombuffer(raw_bytes, dtype=np.float32).reshape(dims)
    onnx_tensors[name] = arr

print(f"Total PyTorch tensors in state_dict: {len(sd)}")
print(f"Total ONNX initializer tensors: {len(onnx_tensors)}")

# List all tensor names in ONNX
print("\nAll ONNX initializer names:")
for n, a in onnx_tensors.items():
    print(f"  {n}: shape {list(a.shape)}")

# Compare across all matching tensors
diffs = []
cos_sims = []

print("\n| PyTorch Tensor | ONNX Initializer | Shape | Max Abs Diff | Mean Abs Diff | Cosine Sim | Exact Match |")
print("|:---|:---|:---:|:---:|:---:|:---:|:---:|")

for sd_name, sd_val in sd.items():
    pt_arr = sd_val.numpy()
    # Check direct name
    onnx_arr = None
    transposed = False
    if sd_name in onnx_tensors:
        onnx_arr = onnx_tensors[sd_name]
    else:
        # Check if transposed or onnx::MatMul
        for iname, iarr in onnx_tensors.items():
            if iarr.shape == pt_arr.shape:
                onnx_arr = iarr
                break
            elif iarr.ndim == 2 and pt_arr.ndim == 2 and iarr.shape == (pt_arr.shape[1], pt_arr.shape[0]):
                onnx_arr = iarr.T
                transposed = True
                break

    if onnx_arr is not None:
        max_d = float(np.max(np.abs(pt_arr - onnx_arr)))
        mean_d = float(np.mean(np.abs(pt_arr - onnx_arr)))
        flat_pt = pt_arr.flatten()
        flat_onnx = onnx_arr.flatten()
        dot = float(np.dot(flat_pt, flat_onnx))
        n1 = float(np.linalg.norm(flat_pt))
        n2 = float(np.linalg.norm(flat_onnx))
        cos = dot / (n1 * n2 + 1e-12) if (n1 > 0 and n2 > 0) else 0.0
        exact = bool(max_d == 0.0)
        diffs.append(max_d)
        cos_sims.append(cos)
        print(f"| `{sd_name}` | `{iname if onnx_arr is not onnx_tensors.get(sd_name) else sd_name}` | `{list(pt_arr.shape)}` | {max_d:.8f} | {mean_d:.8f} | {cos:.6f} | {exact} |")
    else:
        print(f"| `{sd_name}` | *NOT MATCHED* | `{list(pt_arr.shape)}` | - | - | - | False |")

print(f"\nSummary:")
print(f"Total compared: {len(diffs)}")
print(f"Max absolute difference: {max(diffs):.8e}")
print(f"Min cosine similarity: {min(cos_sims):.6f}")
print(f"Mean cosine similarity: {np.mean(cos_sims):.6f}")

