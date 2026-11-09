from pathlib import Path
from html.parser import HTMLParser
import re

html = Path("web/index.html").read_text(encoding="utf-8")
app_js = Path("web/js/app.js").read_text(encoding="utf-8")

panels = ["panel-translate", "panel-classroom", "panel-sessions", "panel-guide", "panel-practice", "panel-recorder", "panel-settings"]

for pid in panels:
    pattern = rf'<div[^>]+id=["\']{pid}["\'].*?(?=<div[^>]+id=["\']panel-|<aside|\Z)'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        print(f"Panel {pid} NOT MATCHED")
        continue
    content = match.group(0)
    buttons = re.findall(r'<button[^>]*>(.*?)</button>', content, re.DOTALL)
    btn_details = []
    for b in re.finditer(r'<button([^>]*)>(.*?)</button>', content, re.DOTALL):
        attrs, text = b.group(1), b.group(2)
        id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
        bid = id_m.group(1) if id_m else "no-id"
        clean_text = re.sub(r'<[^>]+>', '', text).strip()[:25]
        btn_details.append(f"{bid} ('{clean_text}')")
    
    inputs = re.findall(r'<input[^>]+id=["\']([^"\']+)["\']', content)
    selects = re.findall(r'<select[^>]+id=["\']([^"\']+)["\']', content)
    
    print(f"\n================ Panel {pid} ================")
    print(f"Buttons ({len(btn_details)}): {btn_details}")
    print(f"Inputs: {inputs}")
    print(f"Selects: {selects}")

