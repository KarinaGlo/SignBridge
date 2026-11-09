import sys
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(".").resolve()))

from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

print("=== 1. Test GET / ===")
resp = client.get("/")
print("Status code:", resp.status_code)
assert resp.status_code == 200
assert "SignBridge" in resp.text
assert "Mendobrak Hambatan Komunikasi" in resp.text
assert "Terjemahan Langsung" in resp.text
assert "Ruang Kelas Inklusif" in resp.text
print("GET / passed successfully! Title & Indonesian headings confirmed.")

print("=== 2. Test GET /css/style.css ===")
resp_css = client.get("/css/style.css")
print("Status code:", resp_css.status_code)
assert resp_css.status_code == 200
assert "--navy-primary: #10243e;" in resp_css.text
print("CSS loaded successfully with SaaS design variables!")

print("=== 3. Test GET /js/app.js ===")
resp_js = client.get("/js/app.js")
print("Status code:", resp_js.status_code)
assert resp_js.status_code == 200
print("JS app loaded successfully!")

print("=== 4. Test GET /health ===")
resp_health = client.get("/health")
print("Status code:", resp_health.status_code)
print("Health response:", resp_health.json())
assert resp_health.status_code == 200

print("=== 5. Test POST /sentence ===")
resp_sent = client.post("/sentence", json={"gloss": ["HALO", "GURU", "TERIMA_KASIH"]})
print("Sentence response:", resp_sent.json())
assert resp_sent.status_code == 200

print("=== ALL SERVER & FRONTEND TESTS PASSED WITH 0 ERRORS! ===")

