import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("web/js/app.js", "r", encoding="utf-8") as f:
    js_app = f.read()

inputs = re.findall(r'<input\b([^>]*)>', html)
selects = re.findall(r'<select\b([^>]*)>', html)

print("=== INPUT ELEMENTS ===")
for inp in inputs:
    id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
    type_m = re.search(r'type=["\']([^"\']+)["\']', inp)
    inp_id = id_m.group(1) if id_m else "no-id"
    inp_type = type_m.group(1) if type_m else "text"
    in_js = inp_id in js_app
    print(f"[{'WIRED' if in_js else 'PRESENTATIONAL'}] id='{inp_id}' type='{inp_type}'")

print("\n=== SELECT ELEMENTS ===")
for sel in selects:
    id_m = re.search(r'id=["\']([^"\']+)["\']', sel)
    sel_id = id_m.group(1) if id_m else "no-id"
    in_js = sel_id in js_app
    print(f"[{'WIRED' if in_js else 'PRESENTATIONAL'}] id='{sel_id}'")

