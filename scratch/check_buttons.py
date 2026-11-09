import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("web/js/app.js", "r", encoding="utf-8") as f:
    js_app = f.read()

# Collect interactive elements
buttons = re.findall(r'<button\b([^>]*)>(.*?)</button>', html, re.DOTALL)
inputs = re.findall(r'<input\b([^>]*)>', html)
selects = re.findall(r'<select\b([^>]*)>', html)
forms = re.findall(r'<form\b([^>]*)>', html)

print(f"Total <button> elements: {len(buttons)}")
print(f"Total <input> elements:  {len(inputs)}")
print(f"Total <select> elements: {len(selects)}")
print(f"Total <form> elements:   {len(forms)}")

# Check buttons
interactive_buttons = []
for attrs, content in buttons:
    id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
    data_tab_m = re.search(r'data-tab=["\']([^"\']+)["\']', attrs)
    class_m = re.search(r'class=["\']([^"\']+)["\']', attrs)
    text = re.sub(r'<[^>]+>', '', content).strip()[:30]
    
    elem_id = id_m.group(1) if id_m else None
    data_tab = data_tab_m.group(1) if data_tab_m else None
    
    # Check if wired in app.js
    wired = False
    evidence = []
    if elem_id and elem_id in js_app:
        wired = True
        evidence.append(f"id '{elem_id}' in app.js")
    if data_tab:
        wired = True
        evidence.append(f"data-tab '{data_tab}' handled in switchAppTab")
    if "btn-view-app" in (class_m.group(1) if class_m else ""):
        wired = True
        evidence.append("class .btn-view-app handled in view switch")
        
    interactive_buttons.append((elem_id, data_tab, text, wired, ", ".join(evidence)))

print("\n=== BUTTON INTERACTIVITY AUDIT ===")
unwired_buttons = []
for bid, dtab, text, wired, ev in interactive_buttons:
    status = "WIRED" if wired else "PRESENTATIONAL / NO JS LISTENER"
    if not wired:
        unwired_buttons.append((bid, text))
    print(f"[{status:30}] ID: {str(bid):22} Tab: {str(dtab):12} Text: '{text}' ({ev})")

print(f"\nTotal buttons: {len(interactive_buttons)}, Wired: {len(interactive_buttons)-len(unwired_buttons)}, Presentational: {len(unwired_buttons)}")

