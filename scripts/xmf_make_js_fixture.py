"""Buat tests/js/fixtures/xmf_fixture.json dari fungsi Python (sumber kebenaran paritas Python <-> JS)."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from signbridge.xmf.config import encode_text  # noqa: E402
from signbridge.xmf.ops import fit_audio, normalize_hands_static, person_box_from_shoulders, uniform_indices  # noqa: E402

rng = np.random.default_rng(7)
texts = ["Terima_Kasih", "selamat  PAGI!", "di mana?", "Hijau-daun é", ""]
boxes = []
for _ in range(6):
    l, r = rng.uniform(0.2, 0.8, 2).round(4).tolist(), rng.uniform(0.2, 0.8, 2).round(4).tolist()
    w, h = int(rng.integers(200, 1280)), int(rng.integers(200, 720))
    boxes.append({"l": l, "r": r, "w": w, "h": h, "box": person_box_from_shoulders(l, r, w, h)})
kp = np.full((86, 3), np.nan, np.float32)
kp[9:30] = rng.uniform(0.3, 0.6, (21, 3)).round(4)
kp[30:51] = rng.uniform(0.4, 0.7, (21, 3)).round(4)
pcm = np.zeros(12000, np.float32); pcm[4000:7000] = (0.4 * np.sin(np.arange(3000) / 7)).astype(np.float32)
pcm = pcm.round(5)
fx = {
    "text": [{"text": t, "ids": encode_text(t)} for t in texts],
    "person_box": boxes,
    "uniform": [{"n": n, "k": k, "idx": uniform_indices(n, k).tolist()} for n, k in [(100, 16), (7, 16), (64, 16), (1, 4)]],
    "hands": {"kp": np.where(np.isnan(kp), None, kp).tolist(), "out": normalize_hands_static(kp).round(6).tolist()},
    "audio": {"pcm": pcm.tolist(), "n": 16000, "out_sum": float(np.abs(fit_audio(pcm, 16000)).sum()),
              "first_nz": int(np.argmax(np.abs(fit_audio(pcm, 16000)) > 1e-6))},
}
out = ROOT / "tests/js/fixtures/xmf_fixture.json"
out.write_text(json.dumps(fx))
print("fixture ->", out)
