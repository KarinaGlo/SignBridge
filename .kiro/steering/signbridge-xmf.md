---
inclusion: always
---
# SignBridge-XMF — konteks proyek untuk agen Kiro

- Model resmi proyek: **SignBridge-XMF (Cross-Modal Attention Fusion Transformer)**, kode di `signbridge/xmf/`.
  Jangan membuat model/preprocessing terpisah per modalitas — arahan Dosen: 4 modalitas (video, citra, audio, teks)
  di-ingest & dipreprocess BERSAMAAN dan masuk SATU model fusion.
- Data sumber: Google Drive "WL-BISINDO" → `data/raw/wlbisindo_drive/{video,citra,alfabet}` (symlink/rclone).
  Citra masih dicicil uploadnya; klip tanpa citra lengkap otomatis memakai frame dari mp4 yang sama (`video_fallback`).
- **Label selalu dari nama file** `signer{S}_label{L}_sample{N}[_fXX]` dan daftar `GLOSSES` di `signbridge/xmf/config.py`.
  Nama folder di `citra/` SALAH (folder `apa` = label0 = AIR) — jangan pernah memakai nama folder sebagai label.
- Urutan tahap: sync → `python -m signbridge.xmf.ingest` → `audio_bank` → `preprocess` → `train --protocol sd|si|final`
  → `evaluate` (otomatis) → `export` → `uvicorn server.app:app`. Semua dirangkum `scripts/run_xmf_pipeline.sh`.
- Metrik yang dilaporkan: subset **V+I (kamera saja)** pada protokol SD dan SI. Subset dengan audio/teks dipasangkan per
  konsep → bukan akurasi pengenalan isyarat.
- Python 3.11 + `.venv` (MediaPipe 0.10.11). Tes: `pytest tests/test_xmf.py`, `node --test tests/js/*.test.mjs`.
- Kontrak Python↔JS: ubah `signbridge/xmf/ops.py`/`config.py` → ubah juga `web/js/xmf.js`, lalu
  `python scripts/xmf_make_js_fixture.py` dan jalankan tes JS.
- Data, checkpoint, dan ONNX hasil training tidak di-commit (lihat `.gitignore`). Jangan commit model sintetis ke `web/model/`.
