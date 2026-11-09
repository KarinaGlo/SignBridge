import json
import hashlib
from pathlib import Path
import re

print("=== TAHAP 1: VERIFIKASI FILE & KONFIGURASI ===")

# 1. student.onnx
onnx_path = Path("web/model/student.onnx")
assert onnx_path.exists(), "student.onnx does not exist"
onnx_bytes = onnx_path.read_bytes()
onnx_sha = hashlib.sha256(onnx_bytes).hexdigest()
print(f"student.onnx: size={len(onnx_bytes):,} bytes | sha256={onnx_sha}")
assert len(onnx_bytes) == 5458187, f"Unexpected size: {len(onnx_bytes)}"

# 2. labels.json
labels_path = Path("web/model/labels.json")
assert labels_path.exists(), "labels.json does not exist"
labels = json.loads(labels_path.read_text("utf-8"))
print(f"labels.json: count={len(labels)}, unique={len(set(labels))}")
assert len(labels) == 32
assert len(set(labels)) == 32
assert labels[0] == "AIR"
assert labels[1] == "BELAJAR"
assert labels[31] == "MALAM"

# 3. config.js
cfg_text = Path("web/js/config.js").read_text("utf-8")
assert 'studentModelUrl: "./model/student.onnx"' in cfg_text
assert "CATATAN AUDIT TEKNIS: student_int8.onnx" in cfg_text
m = re.search(r"export const BISINDO_GLOSSES\s*=\s*\[(.*?)\];", cfg_text, re.DOTALL)
cfg_glosses = re.findall(r'"([A-Z_]+)"', m.group(1))
assert cfg_glosses == labels, f"config.js BISINDO_GLOSSES != labels.json: {cfg_glosses} vs {labels}"
print(f"config.js BISINDO_GLOSSES matches labels.json: 32/32 (100%)")

# 4. recognizer.js
rec_text = Path("web/js/recognizer.js").read_text("utf-8")
assert 'source: "onnx-m0-neural"' in rec_text
assert "confidence: Number(prob)" in rec_text
assert "Ukuran logits tidak valid" in rec_text
assert "Model ONNX M0 belum dimuat" in rec_text

cs_match = re.search(r"async classifySequence\(.*?\)\s*\{(.*?)\n  \}", rec_text, re.DOTALL)
assert cs_match, "Could not find classifySequence"
cs_body = cs_match.group(1)
assert "_scorePhonologyDatabase" not in cs_body, "_scorePhonologyDatabase found in classifySequence!"
print("recognizer.js: Neural-first verified, _scorePhonologyDatabase completely isolated from classifySequence!")

# 5. app.js
app_text = Path("web/js/app.js").read_text("utf-8")
assert "ONNX Web M0 (Aktif - 32 WL-BISINDO)" in app_text
assert "Roadmap M2" in app_text
assert "Didukung M0" in app_text
print("app.js: Status and badges verified!")

print("\nTAHAP 1 STATUS: PASS")
