from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")

# Let's inspect methods on SignBridgeApp
methods = re.findall(r'^\s*([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{', app_js, re.MULTILINE)
print("SignBridgeApp methods:", methods)

# Let's search for how each module is handled
print("\n--- Event Listeners attached in setupEventListeners ---")
setup_match = re.search(r'setupEventListeners\(\)\s*\{(.*?)\n  \}', app_js, re.DOTALL)
if setup_match:
    setup_code = setup_match.group(1)
    listeners = re.findall(r'(?:getElementById|querySelector)\([\"\']([^\"\']+)[\"\']\)\??\.addEventListener\([\"\']([^\"\']+)[\"\']', setup_code)
    print("Listeners found:", len(listeners))
    for el, evt in listeners[:35]:
        print(f"  {el} -> {evt}")

