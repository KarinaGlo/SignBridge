# PHASE 3 — RECORDER FINAL READINESS AUDIT
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

> [!IMPORTANT]
> **STATUS AKHIR RECORDER: `READY WITH ISSUES`**
> - **Seluruh unit test & kontrak kompatibilitas M6 lulus** (`15/15` JS tests, `22/22` Python tests, dan ZIP/metadata/missing-modality test).
> - Namun terdapat **isu minor kode/metadata** serta **pengujian perangkat keras (kamera & mikrofon fisik)** yang masih berstatus **`MANUAL VERIFICATION REQUIRED`** sebelum perekaman massal P0-E dimulai.

---

## A. Audit Camera (`web/js/vision.js`, `web/js/app.js`, `web/js/recorder.js`)
- **Permission & Video Stream**: `VisionManager.startCamera()` memanggil `navigator.mediaDevices.getUserMedia(...)`. Pada tab `panel-recorder`, `syncRecorderCameraStream()` menautkan `this.vision.stream` ke `#rec-camera-video`.
- **Video Dimensions & `readyState`**: `VisionManager` memeriksa `this.videoEl.readyState >= 2`; `MultimodalCapture._snapshot()` memeriksa `v.videoWidth` dan `v.videoHeight` sebelum menggambar ke kanvas.
- **Skeleton Overlay & MediaPipe Holistic**: MediaPipe Holistic mengekstrak 86 titik melalui `selectFromHolistic` (`web/js/features.js`); `drawSkeleton86` menggambar kerangka pada `#rec-camera-preview` saat `currentAppTab === "panel-recorder"`.
- **Frame Sampling & Continuity**: `pushFrame()` menampung frame `[x,y,z]` selama `capture.active === true` (2.500 ms; klip dengan `< 8` frame dibuang). Kamera tidak dihentikan saat merekam.
- **Temuan / Issue**: **Frame timestamps per-frame tidak disimpan** di `*_kp.json` maupun `*_meta.json` (hanya ada `created_at` per klip).

## B. Audit Image (`web/js/handcrop.js`, `web/js/recorder.js`)
- **Bounding Box & Margin**: `computeHandCropBox(..., margin = 0.25)` menghitung kotak persegi di sekitar 21 titik tangan dengan margin 25% (identik dengan Python `< 1e-5`).
- **Output & Format**: `*_hand.jpg` diekspor sebagai JPEG (`quality = 0.9`) berukuran **`224×224`** (`*_portrait.jpg` `320×H`, `quality = 0.85`).
- **Penanganan Tangan Kiri/Kanan & Tanpa Tangan**: `recorder.js#L210` memprioritaskan `rightHand21` lalu fallback ke `leftHand21` (isyarat dua tangan hanya meng-crop tangan kanan). Jika tangan tidak terdeteksi pada semua frame, `handSnapshot` tetap `null` (`handJpg = null`, modalitas image ditandai hilang).
- **Kompatibilitas M6**: `load_image()` di [`signbridge/multimodal/features.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py#L89-L101) secara otomatis me-resize `224×224` ke `112×112` + normalisasi ImageNet.

## C. Audit Audio (`web/js/recorder.js`, `web/js/speech.js`, `web/js/app.js`)
- **Capture & Format**: `navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } })` merekam mono melalui `ScriptProcessorNode(4096, 1, 1)`, di-resample via `resampleLinear` ke **16 kHz**, dan dikodekan ke **PCM 16-bit mono WAV** (`encodeWavPCM16`) selama target `2500 ms`.
- **Pencegahan Loopback**: `src -> node -> muteGain (gain=0) -> ctx.destination` mencegah audio keluar ke speaker sambil menjaga `ScriptProcessorNode` tetap aktif.
- **Isolasi TTS**: Masuk ke `panel-recorder` memanggil `window.speechSynthesis.cancel()` (`app.js#L213`), dan `speakText()` di [`web/js/speech.js#L68-L73`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/speech.js#L68-L73) mengembalikan `false` (`muted_in_recorder_panel`) saat `currentAppTab === "panel-recorder"`.
- **Temuan / Issue**: `app.js#L1230` masih memanggil `speakText(\`Klip \${target} tersimpan\`, "id-ID")` (hanya aman karena guard di `speech.js`, sebaiknya dihapus dari `bindRecorderControls()` agar tidak bergantung pada state global). Selain itu, kegagalan izin mikrofon ditangkap diam-diam (`catch (_e)`) tanpa peringatan visual di status UI.

## D. Audit Text dan Label (`web/js/app.js`, `web/js/recorder.js`, `web/js/config.js`)
- **Dictionary B & Anti-Leakage**: `BISINDO_GLOSSES` cocok 32/32. Tombol `btn-suggest-prompt` mengisi `CLASSROOM_CONTEXT_PROMPTS[target]` (kalimat dialog kelas tanpa menyalin target gloss).
- **Sample ID**: `MultimodalRecorder.addClip()` menghasilkan `SB_<SIGNER_ID>_<GLOSS>_T<TAKE_ID>` (mis. `SB_S01_AIR_T01`).
- **Temuan / Issue**: Fallback `target = "HALO"` di `app.js#L1183` dan `recorder.js#L323` **tidak ada di `BISINDO_GLOSSES`** (menghasilkan `label = -1` jika dropdown kosong).

## E. Audit ZIP dan Metadata (`web/js/recorder.js`, `scripts/build_multimodal_manifest.py`)
- **Isi ZIP**: `buildStoreZip()` menghasilkan arsip STORE ZIP valid berisi `*_kp.json`, `*_hand.jpg`, `*_portrait.jpg`, `*.wav`, `*_meta.json`, dan `manifest_selfrec.csv`.
- **Proteksi & Konsistensi**: `unpack_zips()` di `build_multimodal_manifest.py` memvalidasi path traversal (Zip Slip). Uji pembongkaran ZIP nyata mengonfirmasi `testzip() == None`, ID unik, dan pelacakan missing modality yang akurat.

## F. Kompatibilitas M6
- Dirinci lengkap pada [`PHASE_3_RECORDER_M6_COMPATIBILITY.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_3_RECORDER_M6_COMPATIBILITY.csv): seluruh 4 modalitas kompatibel dengan kontrak tensor M6 `[B,64,86,3]`, `[B,3,112,112]`, `[B,64,248]`, dan `[B,64]`.
