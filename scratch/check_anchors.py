import re

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find all href="#..."
anchors = set(re.findall(r'href=["\'](#[a-zA-Z0-9_\-]+)["\']', html))
# Find all id="..."
ids = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', html))

print("=== CHECKING INTERNAL ANCHORS ===")
for a in sorted(anchors):
    target = a[1:]
    exists = target in ids
    print(f"Anchor {a:20} -> id='{target}': {'FOUND' if exists else 'BROKEN TARGET'}")

