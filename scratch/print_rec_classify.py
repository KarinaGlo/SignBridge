from pathlib import Path

rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
for i, line in enumerate(rec_js.splitlines()[200:300]):
    print(f"{i+201:3d}: {line}")

