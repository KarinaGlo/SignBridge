from pathlib import Path
import re

css = Path("web/css/style.css").read_text(encoding="utf-8")
idx = css.find(".engine-pill")
print(css[idx:idx+500])

