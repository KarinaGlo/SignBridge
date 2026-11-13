from pathlib import Path
import re

html = Path("web/index.html").read_text(encoding="utf-8")
panels = ["panel-translate", "panel-classroom", "panel-sessions", "panel-guide", "panel-practice", "panel-recorder", "panel-settings"]

indices = []
for pid in panels:
    pos = html.find(f'id="{pid}"')
    indices.append((pos, pid))

indices.sort()
print("Panel positions:", indices)

for i in range(len(indices)):
    start_pos, pid = indices[i]
    end_pos = indices[i+1][0] if i+1 < len(indices) else html.find("</main>", start_pos)
    chunk = html[start_pos:end_pos]
    
    btn_details = []
    for b in re.finditer(r'<button([^>]*)>(.*?)</button>', chunk, re.DOTALL):
        attrs, text = b.group(1), b.group(2)
        id_m = re.search(r'id=["\']([^"\']+)["\']', attrs)
        bid = id_m.group(1) if id_m else "no-id"
        clean_text = re.sub(r'<[^>]+>', '', text).strip()[:25]
        btn_details.append(f"{bid} ('{clean_text}')")
        
    inputs = re.findall(r'<input[^>]+(?:id=["\']([^"\']+)["\']|placeholder=["\']([^"\']+)["\'])', chunk)
    selects = re.findall(r'<select[^>]+id=["\']([^"\']+)["\']', chunk)
    
    print(f"\n================ Panel: {pid} ================")
    print(f"Buttons ({len(btn_details)}): {btn_details}")
    print(f"Inputs: {inputs}")
    print(f"Selects: {selects}")

