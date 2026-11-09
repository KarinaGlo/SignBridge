import http.server
import socketserver
import threading
import urllib.request
import os
import sys

PORT = 8088
WEB_DIR = os.path.abspath("web")

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def run_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler) as httpd:
        httpd.serve_forever()

t = threading.Thread(target=run_server, daemon=True)
t.start()

# Test endpoints
urls = [
    "/index.html",
    "/css/style.css",
    "/js/app.js",
    "/js/icons.js",
    "/js/config.js",
    "/js/vision.js",
    "/js/recognizer.js",
    "/js/fingerspell.js",
    "/js/speech.js",
    "/js/camera.js",
    "/js/canvas.js",
    "/js/ui.js",
    "/js/websocket.js",
    "/js/features.js",
    "/js/handcrop.js",
    "/js/recorder.js",
    "/js/practice.js",
    "/model/student.onnx",
    "/model/student_int8.onnx",
    "/model/fingerspell.onnx",
    "/model/labels.json",
    "/model/fingerspell.json"
]

print("=== TESTING HTTP SERVER DIRECTORY SERVING ===")
all_ok = True
for u in urls:
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}{u}", timeout=3)
        status = req.status
        mime = req.headers.get("Content-Type")
        length = req.headers.get("Content-Length")
        print(f"[{status}] {u:28} MIME: {mime:24} Length: {length}")
    except Exception as e:
        print(f"[FAIL] {u}: {e}")
        all_ok = False

print(f"\nAll static endpoints reachable: {all_ok}")

