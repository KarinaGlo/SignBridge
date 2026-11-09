from pathlib import Path
import re

rec_js = Path("web/js/recognizer.js").read_text(encoding="utf-8")
ctor_m = re.search(r'constructor\([^\)]*\)\s*\{(.*?)\n  \}', rec_js, re.DOTALL)
if ctor_m:
    print("Recognizer constructor:\n", ctor_m.group(1)[:1200])

cfg_js = Path("web/js/config.js").read_text(encoding="utf-8")
model_m = re.findall(r'model/.*', cfg_js)
print("\nModel paths in config.js:", model_m)

