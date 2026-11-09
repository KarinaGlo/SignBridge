from pathlib import Path
import re

app_js = Path("web/js/app.js").read_text(encoding="utf-8")
html = Path("web/index.html").read_text(encoding="utf-8")
room_js = Path("web/js/room.js").read_text(encoding="utf-8")
speech_js = Path("web/js/speech.js").read_text(encoding="utf-8")
rec_js = Path("web/js/recorder.js").read_text(encoding="utf-8")

print("=== 1. LIVE TRANSLATION ===")
live_btns = ["btn-toggle-camera", "btn-mic-listen", "btn-toggle-captions", "btn-fullscreen-camera", "btn-clear-glosses", "btn-commit-spelled", "btn-back-spelled", "btn-send-hearing"]
for b in live_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")

print("\n=== 2. CLASSROOM ===")
class_btns = ["btn-classroom-invite", "btn-classroom-end", "btn-copy-class-code", "btn-give-floor"]
for b in class_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")
# Check tabs inside classroom: shared lesson, discussion, transcript
class_tabs = re.findall(r'data-class-tab=[\"\']([^\"\']+)[\"\']', html)
print("  Classroom tabs:", set(class_tabs))

print("\n=== 3. SESSIONS ===")
sess_btns = ["btn-export-all-sessions"]
for b in sess_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")
# Check session items in HTML or generated
print("  Sessions in HTML:", "session-item" in html, "session-item" in app_js)

print("\n=== 4. DICTIONARY (Language Guide) & 5. GRAMMAR ===")
guide_btns = ["guide-search", "guide-cat-all", "tab-guide-dict", "tab-guide-grammar"]
for b in guide_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")
print("  Concept cards rendering in JS:", "renderConceptBoard" in app_js)

print("\n=== 6. PRACTICE (Latihan Mandiri) ===")
prac_btns = ["practice-target-select", "btn-practice-random", "btn-practice-try"]
for b in prac_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")

print("\n=== 7. RECORDER (Perekam Dataset) ===")
rec_btns = ["btn-rec-start", "btn-rec-stop", "btn-rec-discard", "btn-export-zip"]
for b in rec_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")

print("\n=== 8. SETTINGS ===")
sett_btns = ["theme-toggle", "setting-theme-select", "setting-onnx-ep", "setting-conf-threshold"]
for b in sett_btns:
    in_html = b in html
    in_js = b in app_js
    print(f"  {b}: HTML={in_html}, JS_listener={in_js}")

print("\n=== BACKEND / WEBSOCKET CONNECTION ===")
print("  RoomManager in room.js:")
ws_matches = re.findall(r'WebSocket|fetch\([^\)]*\)', room_js)
print("  RoomManager networking calls:", ws_matches)

