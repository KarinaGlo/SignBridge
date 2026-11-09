from pathlib import Path
import re

html = Path("web/index.html").read_text(encoding="utf-8")
panels = re.findall(r'id=["\'](panel-[^"\']+)["\']', html)
print("Panels in index.html:", panels)

# Also check sidebar buttons or nav buttons
nav_btns = re.findall(r'<button[^>]+data-panel=["\']([^"\']+)["\']', html)
print("data-panel buttons:", nav_btns)
if not nav_btns:
    # check class or onclick or aria-controls
    sidebar = re.search(r'<aside.*?</aside>', html, re.DOTALL)
    if sidebar:
        print("Sidebar content:")
        print(sidebar.group(0))

