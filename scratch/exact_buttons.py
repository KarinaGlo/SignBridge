with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("web/js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

import re

buttons = re.findall(r'<button\b([^>]*)>(.*?)</button>', html, re.DOTALL)
wired = []
unwired = []

for idx, (attrs, content) in enumerate(buttons, 1):
    id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
    dtab_m = re.search(r'data-tab=["\']([^"\']+)["\']', attrs)
    class_m = re.search(r'class=["\']([^"\']+)["\']', attrs)
    bid = id_m.group(1) if id_m else None
    dtab = dtab_m.group(1) if dtab_m else None
    cls = class_m.group(1) if class_m else ""
    text = re.sub(r'<[^>]+>', '', content).strip()
    text = " ".join(text.split())[:35]
    
    is_wired = False
    evidence = []
    if bid and bid in app_js:
        is_wired = True
        evidence.append(f"id '{bid}'")
    if dtab:
        is_wired = True
        evidence.append(f"data-tab '{dtab}'")
    if "btn-view-app" in cls:
        is_wired = True
        evidence.append("class .btn-view-app")
    
    if is_wired:
        wired.append((idx, bid, dtab, text, ", ".join(evidence)))
    else:
        unwired.append((idx, bid, text))

print(f"Total Buttons: {len(buttons)}")
print(f"Wired Buttons: {len(wired)}")
print(f"Unwired (Placeholder) Buttons: {len(unwired)}")

print("\n--- EXACT UNWIRED / PLACEHOLDER BUTTONS (Total 30) ---")
for i, (bnum, bid, txt) in enumerate(unwired, 1):
    print(f"[{i:2d}] Button #{bnum:2d} | ID: {str(bid):26s} | Text: '{txt}'")

