from pathlib import Path
import re

html = Path("web/index.html").read_text(encoding="utf-8")
app_js = Path("web/js/app.js").read_text(encoding="utf-8")

panels = ['panel-translate', 'panel-classroom', 'panel-sessions', 'panel-guide', 'panel-practice', 'panel-recorder', 'panel-settings']

for p in panels:
    pattern = rf'(<div[^>]+id=["\']{p}["\'].*?)(?=<div[^>]+id=["\']panel-|<div[^>]+class=["\']sidebar-footer|\Z)'
    match = re.search(rf'<div[^>]+id=["\']{p}["\'].*?</section>|<div[^>]+id=["\']{p}["\'].*?</div>(?=\s*<div[^>]+id=["\']panel-|\s*</main>)', html, re.DOTALL)
    if not match:
        # try simpler pattern
        idx = html.find(f'id="{p}"')
        sub = html[idx:idx+800] if idx != -1 else "NOT FOUND"
        print(f"\n================ Panel: {p} ================")
        print(sub[:400] + "...")
    else:
        print(f"\n================ Panel: {p} ================")
        print(match.group(0)[:500] + "...")

# Check tab switching logic in app.js
tab_switches = [line for line in app_js.splitlines() if 'data-app-tab' in line or 'switchTab' in line or 'panel-' in line]
print("\n--- Tab switching occurrences in app.js ---")
for line in tab_switches[:30]:
    print(line.strip())

