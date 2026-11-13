import re

def inspect_binary_onnx(path):
    with open(path, "rb") as f:
        data = f.read()
    print(f"\n--- {path} ---")
    print("Size:", len(data), "bytes")
    # Search for input/output tensor names
    # Usually in ONNX string fields, names like 'keypoints', 'logits', 'input', 'output', 'image' appear
    matches = set(re.findall(rb'[a-zA-Z0-9_]{3,30}', data[:5000]))
    readable = [m.decode('ascii', errors='ignore') for m in matches if any(k in m.lower() for k in [b'key', b'log', b'in', b'out', b'node', b'shape', b'float', b'conv', b'linear', b'dense', b'model', b'sign', b'stgcn', b'student', b'finger'])]
    print("Prominent symbols in header:", sorted(readable)[:25])

inspect_binary_onnx("web/model/student.onnx")
inspect_binary_onnx("web/model/fingerspell.onnx")

