from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")

# Extract method names inside class SignBridgeApp
class_match = re.search(r'class SignBridgeApp\s*\{(.*)', app_js, re.DOTALL)
if class_match:
    lines = class_match.group(1).splitlines()
    method_lines = []
    for line in lines:
        m = re.match(r'^\s\s([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{', line)
        if m:
            method_lines.append(m.group(1))
    print("Class methods:", method_lines)

# Check async init()
init_match = re.search(r'async init\(\)\s*\{(.*?)\n  \}', app_js, re.DOTALL)
if init_match:
    print("\n--- init() code ---")
    print(init_match.group(1)[:1500])

