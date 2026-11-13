from pathlib import Path
import re

html = Path("web/index.html").read_text(encoding="utf-8")
app_js = Path("web/js/app.js").read_text(encoding="utf-8")

# Extract all document.getElementById("...") in app.js
get_elem_ids = re.findall(r'document\.getElementById\([\"\']([^\"\']+)[\"\']\)', app_js)
print(f"Total getElementById in app.js: {len(get_elem_ids)}")

missing_ids = []
present_ids = []
for gid in set(get_elem_ids):
    if f'id="{gid}"' in html or f"id='{gid}'" in html:
        present_ids.append(gid)
    else:
        missing_ids.append(gid)

print(f"Present IDs in HTML ({len(present_ids)}):", sorted(present_ids))
print(f"Missing IDs in HTML ({len(missing_ids)}):", sorted(missing_ids))

