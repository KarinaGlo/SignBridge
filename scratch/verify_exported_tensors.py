import sys
import os
from pathlib import Path
import struct
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

class RawProtobufReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def has_more(self):
        return self.pos < len(self.data)

    def read_varint(self):
        res = 0
        shift = 0
        while True:
            b = self.data[self.pos]
            self.pos += 1
            res |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return res

    def read_tag(self):
        if not self.has_more():
            return None, None
        v = self.read_varint()
        return (v >> 3), (v & 0x7)

    def skip_field(self, wire_type):
        if wire_type == 0:
            self.read_varint()
        elif wire_type == 1:
            self.pos += 8
        elif wire_type == 2:
            l = self.read_varint()
            self.pos += l
        elif wire_type == 5:
            self.pos += 4
        else:
            raise ValueError(f"Unknown wire type {wire_type}")

    def read_bytes(self):
        l = self.read_varint()
        res = self.data[self.pos:self.pos+l]
        self.pos += l
        return res

def parse_tensor_proto(tensor_bytes):
    r = RawProtobufReader(tensor_bytes)
    dims = []
    data_type = None
    name = None
    raw_data = None
    float_data = []

    while r.has_more():
        field_num, wire_type = r.read_tag()
        if field_num is None:
            break
        if field_num == 1: # dims
            if wire_type == 2: # packed varint
                packed = r.read_bytes()
                pr = RawProtobufReader(packed)
                while pr.has_more():
                    dims.append(pr.read_varint())
            else:
                dims.append(r.read_varint())
        elif field_num == 2: # data_type
            data_type = r.read_varint()
        elif field_num == 4: # float_data
            if wire_type == 2: # packed
                b = r.read_bytes()
                count = len(b) // 4
                float_data = list(struct.unpack(f"<{count}f", b))
            elif wire_type == 5: # 32-bit fixed
                float_data.append(struct.unpack("<f", r.data[r.pos:r.pos+4])[0])
                r.pos += 4
        elif field_num == 8: # name
            name = r.read_bytes().decode("utf-8", errors="ignore")
        elif field_num == 9: # raw_data
            raw_data = r.read_bytes()
        else:
            r.skip_field(wire_type)

    if raw_data is not None and len(raw_data) > 0:
        arr = np.frombuffer(raw_data, dtype=np.float32)
    elif len(float_data) > 0:
        arr = np.array(float_data, dtype=np.float32)
    else:
        arr = np.array([], dtype=np.float32)

    if dims and arr.size == np.prod(dims):
        arr = arr.reshape(dims)
    return name, arr, dims, data_type

def parse_onnx_model(onnx_path):
    data = Path(onnx_path).read_bytes()
    r = RawProtobufReader(data)
    ir_version = None
    opset_version = None
    graph_bytes = None

    while r.has_more():
        field_num, wire_type = r.read_tag()
        if field_num is None:
            break
        if field_num == 1:
            ir_version = r.read_varint()
        elif field_num == 2:
            # opset_import
            op_bytes = r.read_bytes()
            opr = RawProtobufReader(op_bytes)
            while opr.has_more():
                of, ow = opr.read_tag()
                if of == 2:
                    opset_version = opr.read_varint()
                else:
                    opr.skip_field(ow)
        elif field_num == 7:
            graph_bytes = r.read_bytes()
        else:
            r.skip_field(wire_type)

    # Parse graph
    gr = RawProtobufReader(graph_bytes)
    initializers = {}
    inputs = []
    outputs = []

    while gr.has_more():
        fn, wt = gr.read_tag()
        if fn is None:
            break
        if fn == 5: # initializer
            tb = gr.read_bytes()
            name, arr, dims, dt = parse_tensor_proto(tb)
            initializers[name] = arr
        elif fn == 11: # input
            ib = gr.read_bytes()
            ir = RawProtobufReader(ib)
            iname = None
            while ir.has_more():
                infn, inwt = ir.read_tag()
                if infn == 1:
                    iname = ir.read_bytes().decode("utf-8")
                else:
                    ir.skip_field(inwt)
            inputs.append(iname)
        elif fn == 12: # output
            ob = gr.read_bytes()
            opr = RawProtobufReader(ob)
            oname = None
            while opr.has_more():
                onfn, onwt = opr.read_tag()
                if onfn == 1:
                    oname = opr.read_bytes().decode("utf-8")
                else:
                    opr.skip_field(onwt)
            outputs.append(oname)
        else:
            gr.skip_field(wt)

    return {
        "ir_version": ir_version,
        "opset_version": opset_version,
        "inputs": inputs,
        "outputs": outputs,
        "initializers": initializers
    }

def main():
    onnx_path = ROOT / "scratch" / "student_m0_test.onnx"
    ckpt_path = ROOT / "outputs" / "experiments" / "M0_student_baseline" / "best_model.pt"

    print("Parsing ONNX model...")
    meta = parse_onnx_model(onnx_path)
    print(f"ONNX IR version: {meta['ir_version']}")
    print(f"ONNX Opset version: {meta['opset_version']}")
    print(f"ONNX Inputs: {meta['inputs']}")
    print(f"ONNX Outputs: {meta['outputs']}")
    print(f"ONNX Initializers count: {len(meta['initializers'])}")

    print("\nLoading PyTorch checkpoint...")
    ckpt = torch.load(str(ckpt_path), map_location="cpu")
    sd = ckpt["model_state_dict"]
    print(f"PyTorch State Dict Tensors: {len(sd)}")

    # Check matching of all major layers
    matched = 0
    diffs = []
    cos_sims = []

    print("\nComparing ONNX initializers vs PyTorch checkpoint tensors:")
    for sd_name, sd_val in sd.items():
        val_np = sd_val.cpu().numpy()
        # Find corresponding initializer in ONNX
        # ONNX names usually match PyTorch parameter names or are direct prefixes
        cand = None
        if sd_name in meta["initializers"]:
            cand = meta["initializers"][sd_name]
        else:
            # check if any initializer name matches or ends with sd_name
            for iname, iarr in meta["initializers"].items():
                if iname == sd_name or iname.endswith("." + sd_name) or sd_name.endswith(iname):
                    if iarr.shape == val_np.shape:
                        cand = iarr
                        break

        if cand is not None:
            max_d = float(np.max(np.abs(cand - val_np)))
            dot = float(np.dot(cand.flatten(), val_np.flatten()))
            n1 = float(np.linalg.norm(cand.flatten()))
            n2 = float(np.linalg.norm(val_np.flatten()))
            cos = dot / (n1 * n2 + 1e-12)
            diffs.append(max_d)
            cos_sims.append(cos)
            matched += 1
            if max_d > 1e-5:
                print(f"  [DIFF > 1e-5] {sd_name}: max_diff={max_d:.6e}, cos_sim={cos:.6f}")
            else:
                pass
        else:
            print(f"  [NOT FOUND IN ONNX INITIALIZERS] {sd_name} (shape {val_np.shape})")

    print(f"\nTotal PyTorch tensors: {len(sd)}")
    print(f"Matched directly with ONNX initializers: {matched}")
    print(f"Max absolute difference across all matched tensors: {max(diffs):.8e}")
    print(f"Min cosine similarity across all matched tensors: {min(cos_sims):.8f}")
    print(f"Mean cosine similarity across all matched tensors: {np.mean(cos_sims):.8f}")

if __name__ == "__main__":
    main()

