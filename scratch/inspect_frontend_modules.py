import re
from pathlib import Path

html_path = Path("web/index.html")
app_js_path = Path("web/js/app.js")
config_js_path = Path("web/js/config.js")

html = html_path.read_text(encoding="utf-8")
app_js = app_js_path.read_text(encoding="utf-8")
config_js = config_js_path.read_text(encoding="utf-8")

views = re.findall(r'id=["\']view-([^"\']+)["\']', html)
print("Views in index.html:", views)

navs = set(re.findall(r'data-view=["\']([^"\']+)["\']', html))
print("Nav targets (data-view):", navs)

# Buttons and interactive elements in each view
for view in views:
    # find section for view
    pattern = rf'<section[^>]+id=["\']view-{view}["\'].*?</section>'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        content = match.group(0)
        buttons = re.findall(r'<button[^>]+id=["\']([^"\']+)["\']', content)
        inputs = re.findall(r'<input[^>]+id=["\']([^"\']+)["\']', content)
        selects = re.findall(r'<select[^>]+id=["\']([^"\']+)["\']', content)
        print(f"\n--- View: {view} ---")
        print(f"Buttons ({len(buttons)}): {buttons}")
        print(f"Inputs ({len(inputs)}): {inputs}")
        print(f"Selects ({len(selects)}): {selects}")

print("\n--- Check config.js model path & labels ---")
model_match = re.search(r'MODEL_PATH:\s*["\']([^"\']+)["\']', config_js)
labels_match = re.search(r'LABELS_PATH:\s*["\']([^"\']+)["\']', config_js)
print("config.js MODEL_PATH:", model_match.group(1) if model_match else "Not found")
print("config.js LABELS_PATH:", labels_match.group(1) if labels_match else "Not found")
print("Does config mention student_int8.onnx?", "student_int8.onnx" in config_js)
print("Is MODEL_PATH student_int8?", "student_int8" in (model_match.group(1) if model_match else ""))

