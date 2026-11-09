import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch
import numpy as np
from scratch.decode_onnx import parse_proto_fields

# Load PyTorch checkpoint
ckpt = torch.load('outputs/experiments/M0_student_baseline/best_model.pt', map_location='cpu')
sd = ckpt['model_state_dict']

# Load ONNX model initializers
with open('web/model/student.onnx', 'rb') as f:
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

print(f"Total PyTorch tensors: {len(sd)}")
print(f"Total ONNX initializer tensors: {len(onnx_tensors)}")

# We know the mapping between PyTorch state_dict names and ONNX initializer names:
# Direct matches:
# 'pos_embed' -> 'pos_embed'
# 'input_proj.0.bias' -> 'input_proj.0.bias'
# 'input_proj.1.weight' -> 'input_proj.1.weight'
# 'input_proj.1.bias' -> 'input_proj.1.bias'
# 'encoder.layers.0.self_attn.in_proj_bias' -> 'encoder.layers.0.self_attn.in_proj_bias'
# 'encoder.layers.0.self_attn.out_proj.weight' -> 'encoder.layers.0.self_attn.out_proj.weight'
# 'encoder.layers.0.linear1.bias' -> 'encoder.layers.0.linear1.bias'
# 'encoder.layers.0.linear2.bias' -> 'encoder.layers.0.linear2.bias'
# 'head.weight' -> 'head.weight'
# 'head.bias' -> 'head.bias'
# Transposed weights:
# 'input_proj.0.weight' [160, 516] -> 'onnx::MatMul_909' [516, 160] (transposed)
# 'encoder.layers.0.self_attn.in_proj_weight' [480, 160] -> 'onnx::MatMul_913' [160, 480] (transposed)
# 'encoder.layers.0.linear1.weight' [640, 160] -> 'onnx::MatMul_921' [160, 640] (transposed)
# 'encoder.layers.0.linear2.weight' [160, 640] -> 'onnx::MatMul_922' [640, 160] (transposed)

mapping = [
    ('pos_embed', 'pos_embed', False),
    ('input_proj.0.bias', 'input_proj.0.bias', False),
    ('input_proj.1.weight', 'input_proj.1.weight', False),
    ('input_proj.1.bias', 'input_proj.1.bias', False),
    ('encoder.layers.0.self_attn.in_proj_bias', 'encoder.layers.0.self_attn.in_proj_bias', False),
    ('encoder.layers.0.self_attn.out_proj.weight', 'encoder.layers.0.self_attn.out_proj.weight', False),
    ('encoder.layers.0.linear1.bias', 'encoder.layers.0.linear1.bias', False),
    ('encoder.layers.0.linear2.bias', 'encoder.layers.0.linear2.bias', False),
    ('head.weight', 'head.weight', False),
    ('head.bias', 'head.bias', False),
    ('input_proj.0.weight', 'onnx::MatMul_909', True),
    ('encoder.layers.0.self_attn.in_proj_weight', 'onnx::MatMul_913', True),
    ('encoder.layers.0.linear1.weight', 'onnx::MatMul_921', True),
    ('encoder.layers.0.linear2.weight', 'onnx::MatMul_922', True),
]

print("\n| PyTorch Tensor | ONNX Initializer | Shape | Max Abs Diff | Mean Abs Diff | Cosine Sim | Exact Match |")
print("|:---|:---|:---:|:---:|:---:|:---:|:---:|")

for pt_name, onnx_name, is_transposed in mapping:
    pt_arr = sd[pt_name].numpy()
    onnx_arr = onnx_tensors[onnx_name]
    if is_transposed:
        onnx_comp = onnx_arr.T
    else:
        onnx_comp = onnx_arr
    
    max_diff = float(np.max(np.abs(pt_arr - onnx_comp)))
    mean_diff = float(np.mean(np.abs(pt_arr - onnx_comp)))
    exact = bool(max_diff == 0.0)
    
    # Cosine similarity
    flat_pt = pt_arr.flatten()
    flat_onnx = onnx_comp.flatten()
    norm_pt = np.linalg.norm(flat_pt)
    norm_onnx = np.linalg.norm(flat_onnx)
    if norm_pt > 0 and norm_onnx > 0:
        cos_sim = float(np.dot(flat_pt, flat_onnx) / (norm_pt * norm_onnx))
    else:
        cos_sim = 0.0
        
    print(f"| `{pt_name}` | `{onnx_name}` | `{list(pt_arr.shape)}` | {max_diff:.6f} | {mean_diff:.6f} | {cos_sim:.4f} | {exact} |")

