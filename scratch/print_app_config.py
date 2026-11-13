from pathlib import Path
import re

cfg_js = Path("web/js/config.js").read_text(encoding="utf-8")
idx = cfg_js.find("APP_CONFIG = {")
print(cfg_js[idx:idx+800])

