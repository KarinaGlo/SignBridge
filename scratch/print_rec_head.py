from pathlib import Path
import re

rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
for i, line in enumerate(rec_js.splitlines()[:60]):
    print(f"{i+1:3d}: {line}")

