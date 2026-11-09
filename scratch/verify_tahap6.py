import hashlib
from pathlib import Path
import subprocess

print("=== TAHAP 6: REGRESI & FINAL GIT INTEGRITY ===")

# 1. Hashes
files = [
    ("best_model.pt", Path("outputs/experiments/M0_student_baseline/best_model.pt")),
    ("student.onnx", Path("web/model/student.onnx")),
    ("labels.json", Path("web/model/labels.json")),
    ("config.js", Path("web/js/config.js")),
]

for name, p in files:
    data = p.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"{name:15s}: size={len(data):,} bytes | sha256={sha}")

# 2. Git HEAD
res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
head = res.stdout.strip()
print(f"Current Git HEAD: {head}")
assert head == "b38b4da93b525f68edf4a9cfe6eb9331e13582e2", f"Git HEAD mismatch: {head}"
print("Git HEAD is intact: b38b4da93b525f68edf4a9cfe6eb9331e13582e2")

print("\nTAHAP 6 STATUS: PASS")

