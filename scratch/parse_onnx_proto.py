import sys

# Let's inspect using google.protobuf
from google.protobuf import message
import struct

# ONNX ModelProto field tags:
# ir_version = 1 (int64)
# opset_import = 8 (repeated OperatorSetIdProto)
# producer_name = 2 (string)
# producer_version = 3 (string)
# domain = 4 (string)
# model_version = 5 (int64)
# doc_string = 6 (string)
# graph = 7 (GraphProto)

# Let's see if we can decode the graph inputs, outputs, and initializers
with open("web/model/student.onnx", "rb") as f:
    raw = f.read()

print("student.onnx byte length:", len(raw))

# Let's check if onnx proto definition can be loaded from PyTorch torch.onnx if available
try:
    import torch
    # torch internal has onnx proto definitions
    import torch.onnx._internal.exporter as exporter
    print("torch loaded")
except Exception as e:
    print("torch import error:", e)

# Alternatively, parse via basic protobuf reflection or inspect raw strings
import re
print("Searching for tensor dimensions and names in student.onnx...")
names = re.findall(rb'[a-zA-Z0-9_/]{3,40}', raw[:10000])
print("First 20 identifiers in student.onnx:", [n.decode('ascii', errors='ignore') for n in names[:20]])

