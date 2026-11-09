from pathlib import Path
import re

vis_js = Path("web/js/vision.js").read_text(encoding="utf-8")
idx = vis_js.find("class VisionManager")
print(vis_js[idx:idx+2500])

