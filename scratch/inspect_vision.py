from pathlib import Path
import re

vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")

# Let's inspect VisionManager
ctor = re.search(r'class VisionManager\s*\{(.*?)(?=class|\Z)', vis_js, re.DOTALL)
if ctor:
    content = ctor.group(1)
    methods = re.findall(r'^\s\s(async\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{', content, re.MULTILINE)
    print("VisionManager methods:", methods)

# Let's inspect start() and onResults()
start_m = re.search(r'async start\([^\)]*\)\s*\{(.*?)\n  \}', vis_js, re.DOTALL)
if start_m:
    print("\n--- start() ---")
    print(start_m.group(1)[:1200])

on_res = re.search(r'onResults\([^\)]*\)\s*\{(.*?)\n  \}', vis_js, re.DOTALL)
if on_res:
    print("\n--- onResults() ---")
    print(on_res.group(1)[:1200])

