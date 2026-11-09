from pathlib import Path

vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")
for i, line in enumerate(vis_js.splitlines()[:160]):
    print(f"{i+1:3d}: {line}")

