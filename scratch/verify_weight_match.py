import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch
import numpy as np
from scratch.decode_onnx import parse_proto_fields

# Load PyTorch checkpoint
ckpt = torch.load('outputs/experiments/M0_student_baseline/best_model.pt', map_location='cpu')
sd = ckpt['model_state_dict']

# Load ONNX model bytes
with open('web/model/student.onnx', 'rb') as f:
    raw = f.read()

mf = parse_proto_fields(raw)
gd = [v for fn, wt, v in mf if fn == 7][0]
gf = parse_proto_fields(gd)
inits = [v for fn, wt, v in gf if fn == 5]

onnx_weights = {}
for init in inits:
    flds = parse_proto_fields(init)
    dims = [v for fn, wt, v in flds if fn == 1]
    name = [v.decode('utf-8', errors='ignore') for fn, wt, v in flds if fn == 8][0]
    raw_bytes = [v for fn, wt, v in flds if fn == 9][0]
    arr = np.frombuffer(raw_bytes, dtype=np.float32).reshape(dims)
    onnx_weights[name] = arr

print("Comparing weights between PyTorch best_model.pt and web/model/student.onnx:")
for name in ['head.weight', 'head.bias', 'pos_embed', 'input_proj.0.bias']:
    pt_val = sd[name].numpy()
    onnx_val = onnx_weights[name]
    diff = np.max(np.abs(pt_val - onnx_val))
    print(f"  {name:25s} max diff = {diff:.6e} -> {'IDENTICAL' if diff < 1e-5 else 'DIFFERENT WEIGHTS'}")

