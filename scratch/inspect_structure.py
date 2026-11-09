from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")
html = Path("web/index.html").read_text(encoding="utf-8")

# Look for tabs/panels in app.js
panels = re.findall(r'tab|panel|view', app_js, re.I)
print("Panel occurrences in app.js:", len(panels))

# Look for switchTab or switchView or similar functions
functions = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', app_js)
print("Functions in app.js:", functions)

const_funcs = re.findall(r'const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', app_js)
print("Const arrow funcs in app.js:", const_funcs[:20])

# Find all id attributes in index.html
ids = re.findall(r'id=["\']([^"\']+)["\']', html)
print(f"Total IDs in index.html: {len(ids)}")
print("Sample IDs:", [i for i in ids if any(k in i.lower() for k in ['nav', 'tab', 'panel', 'view', 'btn', 'modal', 'live', 'class', 'session', 'dict', 'practice', 'record', 'setting'])][:40])

