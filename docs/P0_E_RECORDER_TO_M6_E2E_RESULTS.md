# P0-E — RECORDER-TO-M6 END-TO-END RESULTS
## SignBridge ID–PH (BISINDO ↔ FSL)

Dokumen ini memisahkan secara tegas antara **Automated Software Tests**, **Manual Hardware Verification**, dan **Real-Data M6 Inference**.

---

## 1. Automated Software & Pipeline Tests (Terverifikasi)

| Pengujian | Perintah | Hasil | Keterangan |
| :--- | :--- | :---: | :--- |
| **Dictionary B Parity** | `python "...\check_labels.py"` | **PASSED (32/32)** | `BISINDO_32_GLOSSES == web/model/labels.json == web/js/config.js` |
| **Recorder & Parity JS** | `node --test tests/js/recorder.test.mjs tests/js/parity.test.mjs tests/js/handcrop.test.mjs` | **18 / 18 PASSED** (423.4 ms) | Mencakup timestamp per frame, penolakan target kosong/`HALO`, klasifikasi error mikrofon, WAV 16 kHz, hand crop, dan guard TTS. |
| **ZIP, Metadata & Missing Modality** | `node "...\test_zip_e2e_audit.mjs"; python "...\test_zip_e2e_audit.py"` | **PASSED** | STORE ZIP valid (`115,596` bytes, `testzip() == None`), bebas Zip Slip, `modality_mask = [1.0, 0.0, 0.0, 1.0]`. |
| **Python Multimodal Suite** | `pytest tests/test_multimodal_features.py tests/test_multimodal_model.py tests/test_multimodal_service.py -v` | **22 / 22 PASSED** (63.73 s) | Mencakup features, dataset loader, model M6, ONNX parity, dan `MultimodalService`. |

---

## 2. Manual Hardware Tests (Belum Dilakukan)

| Tahap | Status | Bukti |
| :--- | :---: | :--- |
| **Live Webcam + MediaPipe Holistic** | **`MANUAL VERIFICATION REQUIRED`** | Belum ada sesi perekaman browser nyata oleh pengguna. |
| **Live Microphone Capture (16 kHz Mono)** | **`MANUAL VERIFICATION REQUIRED`** | Belum ada rekaman mikrofon nyata oleh pengguna. |

---

## 3. Real-Data Manifest, Loader & M6 Inference (Blocked)

| Tahap | Status | Penjelasan Faktual |
| :--- | :---: | :--- |
| **Tahap 3: ZIP Nyata** | **`BLOCKED`** | `data/raw/web_zips/` tidak ada (`0` ZIP nyata). |
| **Tahap 4: Manifest & Preprocessing Nyata** | **`BLOCKED`** | `data/multimodal/manifest_multimodal.csv` tidak ada. |
| **Tahap 5: M6 Inference (`MultimodalService` / ONNX)** | **`BLOCKED`** | `web/model/multimodal_fusion.onnx` tidak ada (`available=False`, HTTP 503). Satu-satunya checkpoint PyTorch (`outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt`) dilatih memakai data random/sintetis (`--smoke`) dan tidak sah untuk klaim akurasi nyata. |
