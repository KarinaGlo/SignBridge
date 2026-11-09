import re
import os

with open("web/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find all src and href
links = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html)
print(f"Total attributes found: {len(links)}")

missing = []
found = []
external = []
anchors = []

for link in links:
    if link.startswith("#"):
        anchors.append(link)
    elif link.startswith("http://") or link.startswith("https://"):
        external.append(link)
    else:
        # local file path relative to web/
        clean_path = link.split("?")[0].split("#")[0]
        if clean_path.startswith("./"):
            clean_path = clean_path[2:]
        full_path = os.path.join("web", clean_path)
        if os.path.exists(full_path):
            found.append((link, full_path, os.path.getsize(full_path)))
        else:
            missing.append((link, full_path))

print("\n--- EXTERNAL CDN RESOURCES ---")
for ext in set(external):
    print(" ", ext)

print("\n--- LOCAL FOUND RESOURCES ---")
for orig, fp, sz in set(found):
    print(f"  [OK {sz:>8} bytes] {orig} -> {fp}")

print("\n--- MISSING LOCAL RESOURCES (POTENTIAL 404) ---")
for orig, fp in set(missing):
    print(f"  [MISSING 404] {orig} -> {fp}")

print(f"\nSummary: {len(found)} found local, {len(missing)} missing local, {len(external)} external CDN, {len(anchors)} anchor links.")

