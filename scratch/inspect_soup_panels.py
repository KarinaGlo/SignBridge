from pathlib import Path
from bs4 import BeautifulSoup
import re

html = Path("web/index.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

panels = ["panel-translate", "panel-classroom", "panel-sessions", "panel-guide", "panel-practice", "panel-recorder", "panel-settings"]

for pid in panels:
    el = soup.find(id=pid)
    if not el:
        print(f"Panel {pid} NOT FOUND!")
        continue
    buttons = el.find_all("button")
    inputs = el.find_all("input")
    selects = el.find_all("select")
    cards = el.find_all(class_=re.compile(r"card|item|block|box"))
    print(f"\n================ Panel {pid} ================")
    print(f"Buttons: {[b.get('id') or b.get_text(strip=True)[:20] for b in buttons]}")
    print(f"Inputs: {[i.get('id') or i.get('placeholder', '')[:20] for i in inputs]}")
    print(f"Selects: {[s.get('id') for s in selects]}")
    print(f"Summary text: {el.get_text(strip=True)[:180]}...")

