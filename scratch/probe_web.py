import http.server
import socketserver
import threading
import urllib.request
import time
from pathlib import Path

PORT = 8999
web_dir = Path("web").resolve()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(web_dir), **kwargs)

httpd = socketserver.TCPServer(("", PORT), Handler)
t = threading.Thread(target=httpd.serve_forever)
t.daemon = True
t.start()

time.sleep(0.5)

print("=== 1. Test GET http://localhost:8999/index.html ===")
with urllib.request.urlopen(f"http://localhost:{PORT}/index.html") as response:
    html = response.read().decode('utf-8')
    assert response.status == 200
    assert "SignBridge" in html
    assert "Mendobrak Hambatan Komunikasi" in html
    assert "Terjemahan Langsung" in html
    assert "Ruang Kelas Inklusif" in html
    print(f"OK! Received {len(html)} bytes of HTML.")

print("=== 2. Test GET http://localhost:8999/css/style.css ===")
with urllib.request.urlopen(f"http://localhost:{PORT}/css/style.css") as response:
    css = response.read().decode('utf-8')
    assert response.status == 200
    assert "--navy-primary: #10243e;" in css
    assert "--teal-primary: #10b8a6;" in css
    print(f"OK! Received {len(css)} bytes of CSS.")

print("=== 3. Test GET http://localhost:8999/js/app.js ===")
with urllib.request.urlopen(f"http://localhost:{PORT}/js/app.js") as response:
    js = response.read().decode('utf-8')
    assert response.status == 200
    assert "SignBridgeApp" in js
    print(f"OK! Received {len(js)} bytes of JS.")

print("=== 4. Test GET http://localhost:8999/js/icons.js ===")
with urllib.request.urlopen(f"http://localhost:{PORT}/js/icons.js") as response:
    icons = response.read().decode('utf-8')
    assert response.status == 200
    assert "translate" in icons
    print(f"OK! Received {len(icons)} bytes of Icons JS.")

httpd.shutdown()
print("=== ALL PROBES COMPLETED SUCCESSFULLY! ===")

