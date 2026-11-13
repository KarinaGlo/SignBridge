from pathlib import Path

rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
for i, line in enumerate(rec_js.splitlines()[450:530]):
    print(f"{i+451:3d}: {line}")

