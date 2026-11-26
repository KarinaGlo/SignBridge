# PHASE 3 — RECORDER TEST RESULTS
## SignBridge ID–PH (BISINDO ↔ FSL)

---

## 1. Automated Tests Executed (Actual Runs)

| Test Suite | Command | Result | Scope Covered |
| :--- | :--- | :---: | :--- |
| **JavaScript Regression Tests** | `node --test tests/js/recorder.test.mjs tests/js/parity.test.mjs tests/js/handcrop.test.mjs` | **15 / 15 PASSED** (288.0 ms) | `computeHandCropBox`, `cropAndResizeHand`, `normalizeImagenet`, `selectFromHolistic`, `trimInactive`, `normalizePose`, `resampleFrames(64)`, `preprocessKeypoints`, `resampleLinear`, `encodeWavPCM16`, `csvEscape`, `MultimodalRecorder`, `CLASSROOM_CONTEXT_PROMPTS` (32 gloss), `sample_id` (`SB_S05_...`), `drawSkeleton86`, `speakText` muted in `panel-recorder`. |
| **Python Multimodal Tests** | `pytest tests/test_multimodal_features.py tests/test_multimodal_model.py tests/test_multimodal_service.py -v` | **22 / 22 PASSED** (42.91 s) | Preprocessing 4 modalitas, `assign_splits` (`sd` & `si`), `build_multimodal_manifest` dari ZIP, `SignBridgeMultimodalFusion` shapes/masking/dropout/loss/ONNX parity, `MultimodalService` API. |
| **ZIP, Metadata & Missing Modality E2E Test** | `node ...test_zip_e2e_audit.mjs; python ...test_zip_e2e_audit.py` | **PASSED** | Pembuatan STORE ZIP via `buildStoreZip`, `zipfile.testzip()` = `None`, Zip Slip check, `sample_id` `SB_S01_AIR_T01` & `SB_S01_BELAJAR_T02`, konsistensi `*_meta.json`, dan `modality_mask = [1.0, 0.0, 0.0, 1.0]` saat audio & image hilang. |

---

## 2. Hardware / Browser Tests (`MANUAL VERIFICATION REQUIRED`)

| Test Area | Status | Alasan |
| :--- | :---: | :--- |
| **Camera Stream Test** (`getUserMedia` video + MediaPipe Holistic live frames) | **`MANUAL VERIFICATION REQUIRED`** | Memerlukan kamera fisik dan sesi browser interaktif (`http://localhost:8080`). |
| **Audio Capture Test** (`getUserMedia` mic + `ScriptProcessorNode` + speaker muted) | **`MANUAL VERIFICATION REQUIRED`** | Memerlukan perangkat mikrofon fisik dan izin browser. |
