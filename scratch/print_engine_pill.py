from pathlib import Path

html = Path("web/index.html").read_text(encoding="utf-8")
idx = html.find("engine-status-pill")
print(html[idx-100:idx+300])

