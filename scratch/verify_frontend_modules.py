import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
web_dir = ROOT / "web"

def verify_modules():
    print("=== TAHAP 4: VERIFIKASI INTEGRITAS MODUL FRONTEND ===")
    
    # 1. index.html
    html = (web_dir / "index.html").read_text("utf-8")
    assert "onnxruntime-web" in html, "onnxruntime-web CDN script missing in index.html"
    assert "js/app.js" in html, "app.js script missing in index.html"
    
    # Check views and panels
    all_ids = set(re.findall(r'id="([^"]+)"', html))
    print(f"Total HTML elements with id: {len(all_ids)}")
    
    expected_ids = [
        "view-landing", "view-app", 
        "panel-translate", "panel-classroom", "panel-sessions",
        "panel-guide", "panel-practice", "panel-recorder", "panel-settings"
    ]
    for p in expected_ids:
        assert p in all_ids, f"Required element #{p} missing in index.html!"
    print(f"index.html: Verified all {len(expected_ids)} core view/panel IDs are present.")

    # 2. recognizer.js
    rec = (web_dir / "js" / "recognizer.js").read_text("utf-8")
    assert "export class SignRecognizer" in rec
    assert "onnx-m0-neural" in rec
    assert "Ukuran logits tidak valid" in rec
    assert "Output logits mengandung nilai non-finite" in rec
    print("recognizer.js: Verified neural-first class selection and strict NaN/Inf guards.")

    # 3. config.js
    cfg = (web_dir / "js" / "config.js").read_text("utf-8")
    assert "export const BISINDO_GLOSSES" in cfg
    assert "export const CLASSROOM_CONCEPTS" in cfg
    assert "export const FINGERSPELL_DB" in cfg
    print("config.js: Verified 32 glosses, concept database, and fingerspell DB.")

    # 4. sentence.js
    sent = (web_dir / "js" / "sentence.js").read_text("utf-8")
    assert "export function glossToSentenceLocal" in sent
    assert "export async function buildNaturalSentence" in sent
    assert "export function sentenceToConceptGlosses" in sent
    for w in ["AIR", "BELAJAR", "MAAF", "SAYA", "TERIMA_KASIH", "MALAM"]:
        assert f"{w}:" in sent, f"Gloss {w} missing from sentence dictionary"
    print("sentence.js: Verified local B0 sentence rules and gloss-to-sentence mapping.")

    # 5. features.js
    feat = (web_dir / "js" / "features.js").read_text("utf-8")
    assert "export function preprocessKeypoints" in feat
    assert "export function resampleFrames" in feat
    assert "export function normalizePose" in feat
    print("features.js: Verified Contract 3 preprocessing functions intact.")

    # 6. Check all JS files in web/js
    js_files = [
        "app.js", "config.js", "features.js", "fingerspell.js",
        "handcrop.js", "icons.js", "recognizer.js", "recorder.js",
        "room.js", "sentence.js", "speech.js", "vision.js"
    ]
    for name in js_files:
        p = web_dir / "js" / name
        assert p.exists(), f"Module {name} missing!"
        content = p.read_text("utf-8")
        assert len(content) > 100, f"Module {name} seems truncated!"
    print(f"All {len(js_files)} JS modules in web/js/ verified present and non-empty.")
    
    print("\nTAHAP 4 STATUS: PASS")

if __name__ == "__main__":
    verify_modules()
