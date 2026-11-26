# PHASE 3 — RECORDER REMAINING WORK BEFORE P0-E
## SignBridge ID–PH (BISINDO ↔ FSL)

1. **Verifikasi Perangkat Keras Langsung (`MANUAL VERIFICATION REQUIRED`)**:
   - Buka `web/index.html` melalui server lokal (`http://localhost:8080`) di browser dengan webcam & mikrofon fisik aktif.
   - Rekam 1–2 klip uji pada tab **Perekam Dataset**, unduh ZIP, lalu jalankan `scripts/build_multimodal_manifest.py` untuk memastikan 4 modalitas terisi nyata (`video`, `image`, `audio`, `text`).
2. **Perbaikan Kode Minor (Setelah Audit)**:
   - Hapus pemanggilan `speakText(...)` di `web/js/app.js#L1230` pada `bindRecorderControls()` agar Recorder benar-benar bebas dari pemanggilan TTS.
   - Ganti fallback `target = "HALO"` di `web/js/app.js#L1183` dan `web/js/recorder.js#L323` menjadi salah satu gloss valid di `BISINDO_GLOSSES` (mis. `"AIR"`).
   - Tambahkan array `timestamps` per frame pada `MultimodalCapture.pushFrame()` (`web/js/recorder.js`) dan simpan ke `*_kp.json` jika diperlukan untuk audit FPS/sinkronisasi.
   - Tampilkan peringatan visual di UI jika izin mikrofon ditolak sehingga perekam tahu audio tidak terekam.
