from pathlib import Path

vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")
for i, line in enumerate(vis_js.splitlines()[580:640]):
    print(f"{i+581:3d}: {line}")

