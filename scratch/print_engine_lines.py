from pathlib import Path

html = Path("web/index.html").read_text(encoding="utf-8")
for i, line in enumerate(html.splitlines()):
    if "engine-status" in line:
        print(f"{i+1}: {line}")

