# PHASE 3.1 — REGRESSION TEST RESULTS
## SignBridge ID–PH (BISINDO ↔ FSL)

---

## 1. JavaScript Regression Tests (`18 / 18 PASSED`)
Perintah:
```powershell
node --test tests/js/recorder.test.mjs tests/js/parity.test.mjs tests/js/handcrop.test.mjs
```
Hasil: **18 passed, 0 failed** (263.53 ms), termasuk 3 tes baru Phase 3.1:
- `MultimodalCapture.pushFrame mencatat frame_index, timestamp_ms monotonik, valid_hand, dan keypoints` — **PASS**
- `MultimodalRecorder menolak target kosong, HALO, atau gloss di luar Dictionary B` — **PASS**
- `classifyMicrophoneError menandai izin ditolak sebagai missing tanpa memalsukan audio` — **PASS**

---

## 2. ZIP, Metadata & Missing Modality Validation (`PASSED`)
Perintah:
```powershell
node "...\test_zip_e2e_audit.mjs"; python "...\test_zip_e2e_audit.py"
```
Hasil: `WROTE_ZIP_BYTES: 115596`, `ZIP_METADATA_MISSING_MODALITY_TESTS_PASSED!`:
- Arsip STORE ZIP valid (`zipfile.testzip() == None`), bebas Zip Slip.
- Format `sample_id` (`SB_S01_AIR_T01`, `SB_S01_BELAJAR_T02`), `*_meta.json`, dan `modality_mask = [1.0, 0.0, 0.0, 1.0]` terverifikasi akurat.

---

## 3. Python Multimodal Tests (`22 / 22 PASSED`)
Perintah:
```powershell
pytest tests/test_multimodal_features.py tests/test_multimodal_model.py tests/test_multimodal_service.py -v
```
Hasil: **22 passed, 0 failed** (57.46 s, Exit Code `0`) — seluruh 12 tes fitur/dataset, 7 tes model/ONNX parity, dan 3 tes `MultimodalService` lulus.

---

## 4. Perangkat Keras Fisik (`MANUAL VERIFICATION REQUIRED`)
- Pengujian webcam fisik dan mikrofon fisik secara langsung di browser tetap berstatus **`MANUAL VERIFICATION REQUIRED`** dan dijalankan mengikuti [`PHASE_3_1_P0_E_TEST_PROCEDURE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_3_1_P0_E_TEST_PROCEDURE.md).
