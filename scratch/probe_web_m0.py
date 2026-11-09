import http.server
import socketserver
import threading
import urllib.request
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
web_dir = ROOT / "web"
PORT = 8998

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def log_message(self, format, *args):
        pass # suppress server logs

def probe_http():
    httpd = socketserver.TCPServer(("", PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    time.sleep(0.5)

    base = f"http://localhost:{PORT}"
    results = {}

    # 1. Probe index.html
    req = urllib.request.urlopen(f"{base}/index.html")
    results["index.html"] = {
        "status": req.status,
        "size": len(req.read()),
        "content_type": req.headers.get("Content-Type")
    }

    # 2. Probe student.onnx
    req = urllib.request.urlopen(f"{base}/model/student.onnx")
    onnx_bytes = req.read()
    results["student.onnx"] = {
        "status": req.status,
        "size": len(onnx_bytes),
        "content_type": req.headers.get("Content-Type"),
        "expected_size": 5458187
    }

    # 3. Probe labels.json
    req = urllib.request.urlopen(f"{base}/model/labels.json")
    labels = json.loads(req.read().decode("utf-8"))
    results["labels.json"] = {
        "status": req.status,
        "count": len(labels),
        "first": labels[0],
        "second": labels[1],
        "last": labels[-1]
    }

    # 4. Probe config.js
    req = urllib.request.urlopen(f"{base}/js/config.js")
    cfg = req.read().decode("utf-8")
    results["config.js"] = {
        "status": req.status,
        "has_32_glosses": "AIR" in cfg and "MALAM" in cfg,
        "has_m0_notes": "CATATAN AUDIT TEKNIS" in cfg
    }

    # 5. Probe recognizer.js
    req = urllib.request.urlopen(f"{base}/js/recognizer.js")
    rec = req.read().decode("utf-8")
    results["recognizer.js"] = {
        "status": req.status,
        "has_neural_source": "onnx-m0-neural" in rec,
        "has_error_handling": "Model ONNX M0 belum dimuat" in rec
    }

    # 6. Probe student_int8.onnx status
    req = urllib.request.urlopen(f"{base}/model/student_int8.onnx")
    results["student_int8.onnx"] = {
        "status": req.status,
        "size": len(req.read())
    }

    httpd.shutdown()
    return results

if __name__ == "__main__":
    res = probe_http()
    print("HTTP Server Probe Results:")
    print(json.dumps(res, indent=2))
    assert res["index.html"]["status"] == 200
    assert res["student.onnx"]["status"] == 200
    assert res["student.onnx"]["size"] == 5458187
    assert res["labels.json"]["count"] == 32
    assert res["labels.json"]["first"] == "AIR"
    assert res["labels.json"]["last"] == "MALAM"
    assert res["config.js"]["has_32_glosses"] is True
    assert res["recognizer.js"]["has_neural_source"] is True
    print("\nALL HTTP SERVING PROBES PASSED (6/6)!")

