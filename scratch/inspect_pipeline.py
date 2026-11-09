from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")
rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")
cfg_js = Path("web/js/config.js").read_text(encoding="utf-8")

print("=== RECOGNIZER.JS INIT ===")
init_m = re.search(r'async init\(\)\s*\{(.*?)\n  \}', rec_js, re.DOTALL)
if init_m:
    print(init_m.group(1)[:1200])

print("\n=== RECOGNIZER.JS CLASSIFY SEQUENCE ===")
cls_m = re.search(r'async classifySequence\([^\)]*\)\s*\{(.*?)\n  \}', rec_js, re.DOTALL)
if cls_m:
    print(cls_m.group(1)[:1200])

print("\n=== VISION.JS CAMERA & MEDIAPIPE ===")
start_cam = re.search(r'async start\([^\)]*\)\s*\{(.*?)\n  \}', vis_js, re.DOTALL)
if start_cam:
    print("vision.js start():\n", start_cam.group(1)[:1000])

on_res = re.search(r'onResults\([^\)]*\)\s*\{(.*?)\n  \}', vis_js, re.DOTALL)
if on_res:
    print("vision.js onResults():\n", on_res.group(1)[:1000])

