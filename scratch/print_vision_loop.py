from pathlib import Path

vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")
for i, line in enumerate(vis_js.splitlines()[500:580]):
    print(f"{i+501:3d}: {line}")

