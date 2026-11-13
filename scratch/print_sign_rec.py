from pathlib import Path
import re

rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
idx = rec_js.find("class SignRecognizer")
print(rec_js[idx:idx+1500])

