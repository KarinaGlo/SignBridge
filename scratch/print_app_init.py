from pathlib import Path

app_js = Path("web/js/app.js").read_text(encoding="utf-8")
idx = app_js.find("engine-status-text")
print(app_js[idx-100:idx+400])

