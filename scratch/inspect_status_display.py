from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")
html = Path("web/index.html").read_text(encoding="utf-8")

# Search for engine-status or model status in index.html
status_elements = re.findall(r'<[^>]+(?:engine|model|status)[^>]*>', html, re.I)
print(f"Status elements in index.html ({len(status_elements)}):")
for el in status_elements[:15]:
    print(" ", el)

# Search for status updates in app.js
status_updates = [line for line in app_js.splitlines() if any(k in line for k in ["engine", "modelStatus", "ort", "recStatus", "modelUrl", "student.onnx", "student_int8"])]
print("\nStatus updates in app.js:")
for line in status_updates:
    print(" ", line.strip())

