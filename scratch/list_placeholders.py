with open("web/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("web/js/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

import re

unwired = []
wired = []

for line_no, line in enumerate(lines, 1):
    # check buttons
    btn_m = re.findall(r'<button\b([^>]*)>(.*?)</button>', line, re.DOTALL)
    for attrs, text in btn_m:
        id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
        dtab_m = re.search(r'data-tab=["\']([^"\']+)["\']', attrs)
        bid = id_m.group(1) if id_m else None
        dtab = dtab_m.group(1) if dtab_m else None
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        is_wired = False
        if bid and bid in app_js:
            is_wired = True
        elif dtab:
            is_wired = True
        if is_wired:
            wired.append((line_no, bid, dtab, clean_text))
        else:
            unwired.append((line_no, bid, clean_text))

print(f"Total Buttons: {len(wired) + len(unwired)}")
print(f"Wired Buttons: {len(wired)}")
print(f"Unwired (Placeholder) Buttons: {len(unwired)}")
print("\n--- UNWIRED / PLACEHOLDER BUTTONS LIST ---")
for idx, (lno, bid, txt) in enumerate(unwired, 1):
    print(f"{idx:2d}. Line {lno:4d} | ID: {str(bid):26s} | Text: '{txt[:40]}'")

