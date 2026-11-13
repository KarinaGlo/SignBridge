import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch
import numpy as np
from scratch.decode_onnx import parse_proto_fields
import struct

# Load PyTorch checkpoint
ckpt = torch.load('outputs/experiments/M0_student_baseline/best_model.pt', map_location='cpu')
sd = ckpt['model_state_dict']

# Load ONNX model bytes
with open('web/model/student.onnx', 'rb') as f:
    raw = f.read()

model_fields = parse_proto_fields(raw)
graph_data = [val for fn, wt, val in model_fields if fn == 7][0]
graph_fields = parse_proto_fields(graph_data)
initializers = [val for fn, wt, val in graph_fields if fn == 5]

print("Total initializers in ONNX:", len(initializers))
# In TensorProto:
# field 1: dims (repeated int64)
# field 2: data_type (int32)
# field 7: raw_data (bytes)
# field 8: name (string)
onnx_tensors = {}
for init in initializers:
    fields = parse_proto_fields(init)
    dims = [v for fn, wt, v in fields if fn == 1]
    name = [v.decode('utf-8', errors='ignore') for fn, wt, v in fields if fn == 8]
    raw_bytes = [v for fn, wt, v in fields if fn == 7]
    float_data = [v for fn, wt, v in fields if fn == 4]
    
    tname = name[0] if name else 'unnamed'
    if raw_bytes:
        arr = np.frombuffer(raw_bytes[0], dtype=np.float32).reshape(dims)
        onnx_tensors[tname] = arr
    elif float_data:
        arr = np.array(float_data, dtype=np.float32).reshape(dims)
        onnx_tensors[tname] = arr

print(f"Decoded {len(onnx_tensors)} weight tensors from ONNX.")
for k, v in list(onnx_tensors.items())[:5]:
    print(f"  ONNX: {k} shape={v.shape}")

# Compare with checkpoint weights
matches = 0
checked = 0
for pt_name, pt_val in sd.items():
    pt_arr = pt_val.cpu().numpy()
    # Check if this exact array or its values appear in onnx_tensors
    for onnx_name, onnx_arr in onnx_tensors.items():
        if pt_arr.shape == onnx_arr.shape:
            checked += 1
            diff = np.max(np.abs(pt_arr - onnx_arr))
            if diff < 1e-4:
                matches += 1
                print(f"MATCH! PT {pt_name} == ONNX {onnx_name} (diff={diff:.6e})")

print(f"\nResult: Checked {checked} shape-matching tensors. Matches found: {matches}")

