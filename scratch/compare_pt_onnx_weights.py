import sys, os
sys.path.insert(0, os.path.abspath('.'))
import torch
from scratch.decode_onnx import parse_proto_fields

# Load PyTorch checkpoint
ckpt = torch.load('outputs/experiments/M0_student_baseline/best_model.pt', map_location='cpu')
sd = ckpt['model_state_dict']
print('PyTorch checkpoint parameter names (first 10):')
for k in list(sd.keys())[:10]:
    print(' ', k, sd[k].shape, sd[k].dtype)
print('Total PyTorch parameters in state_dict:', len(sd))

# Load ONNX initializers
with open('web/model/student.onnx', 'rb') as f:
    raw = f.read()

model_fields = parse_proto_fields(raw)
graph_data = [val for fn, wt, val in model_fields if fn == 7][0]
graph_fields = parse_proto_fields(graph_data)
initializers = [val for fn, wt, val in graph_fields if fn == 5]
print('\nONNX initializers count:', len(initializers))
init_names = []
for init in initializers:
    init_fields = parse_proto_fields(init)
    name = [v.decode('utf-8', errors='ignore') for fn, wt, v in init_fields if fn == 1]
    init_names.append(name[0] if name else 'unnamed')
print('ONNX initializer names (first 10):')
for n in init_names[:10]:
    print(' ', n)
