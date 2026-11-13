import os
import sys

def inspect_onnx(file_path):
    print(f"\n==========================================")
    print(f"Inspecting ONNX: {file_path}")
    print(f"File size: {os.path.getsize(file_path):,} bytes")
    try:
        import onnx
        model = onnx.load(file_path)
        print("ONNX IR Version:", model.ir_version)
        print("Producer Name:", model.producer_name)
        print("Producer Version:", model.producer_version)
        print("Graph Name:", model.graph.name)
        print("Inputs:")
        for inp in model.graph.input:
            shape = [d.dim_value if d.dim_value != 0 else d.dim_param for d in inp.type.tensor_type.shape.dim]
            print(f"  - Name: {inp.name}, Shape: {shape}, Type: {inp.type.tensor_type.elem_type}")
        print("Outputs:")
        for out in model.graph.output:
            shape = [d.dim_value if d.dim_value != 0 else d.dim_param for d in out.type.tensor_type.shape.dim]
            print(f"  - Name: {out.name}, Shape: {shape}, Type: {out.type.tensor_type.elem_type}")
        return True
    except ImportError:
        print("onnx library not installed, reading protobuf directly...")
        # We can read using raw protobuf if needed or check if onnx can be loaded
        return False

inspect_onnx("web/model/student.onnx")
inspect_onnx("web/model/student_int8.onnx")
inspect_onnx("web/model/fingerspell.onnx")

