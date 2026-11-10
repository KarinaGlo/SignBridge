# SIGNBRIDGE — LAPORAN PUBLIKASI GIT (GITHUB PUSH REPORT)

Dokumen ini mencatat bukti verifikasi menyeluruh dari proses staging, commit, dan push perubahan stabilisasi pengenalan isyarat real-time SignBridge M0 ke repository GitHub.

---

## 1. Informasi Repository dan Remote

- **Repository Target**: `https://github.com/KarinaGlo/SignBridge.git`
- **Remote Name**: `origin`
- **Fetch URL**: `https://github.com/KarinaGlo/SignBridge.git`
- **Push URL**: `https://github.com/KarinaGlo/SignBridge.git`

```text
origin	https://github.com/KarinaGlo/SignBridge.git (fetch)
origin	https://github.com/KarinaGlo/SignBridge.git (push)
```

---

## 2. Branch yang Digunakan

- **Branch Aktif**: `feature/field-test-readiness`
- **Status Branch**: Up to date dengan `origin/feature/field-test-readiness`
- **URL Branch GitHub**: [https://github.com/KarinaGlo/SignBridge/tree/feature/field-test-readiness](https://github.com/KarinaGlo/SignBridge/tree/feature/field-test-readiness)

---

## 3. Commit Hash & Pesan Commit

- **Commit Hash (Short)**: `7b4c4e8`
- **Commit Hash (Full)**: `7b4c4e86ec1172b3c56eeb7b79f6dcdf7c7e7d3e`
- **Commit Message**: `fix: stabilize M0 real-time sign recognition`
- **Author**: KarinaGlo <gloriadanapricilia@gmail.com>

---

## 4. Daftar File yang Di-commit

Total **22 file** (`2231 insertions(+)`, `97 deletions(-)`):

| No. | File Path | Status | Deskripsi Singkat |
|:---:|:---|:---:|:---|
| 1 | `docs/SIGNBRIDGE_HTTP_501_FIX.md` | New | Dokumentasi investigasi & perbaikan HTTP 501 `/sentence` dan circuit-breaker lokal B0 |
| 2 | `docs/SIGNBRIDGE_LIVE_RECOGNITION_FIX.md` | New | Laporan investigasi mendalam rekaman Edge, audit model M0, dan evaluasi jujur |
| 3 | `docs/SIGNBRIDGE_RECOGNITION_ACCURACY_IMPROVEMENT.md` | New | Laporan audit paritas geometris dan perbaikan akurasi pengenalan webcam |
| 4 | `scratch/eval_reference_32.py` | New | Skrip evaluasi offline 32 sekuens referensi |
| 5 | `scratch/reference_32_classes.json` | New | Data sekuens referensi 32 kelas untuk pengujian offline |
| 6 | `scripts/replay_eval.mjs` | New | Skrip evaluasi offline strict (`predicted === expected`) & supresi false-positive |
| 7 | `signbridge/constants.py` | Modified | Sinkronisasi `BISINDO_32_GLOSSES` ke 32 label WL-BISINDO resmi (`AIR`..`MALAM`) |
| 8 | `tests/js/recognizer_stability.test.mjs` | New | Test suite kestabilan recognizer, two-tier threshold, dynamic FPS, dan framing |
| 9 | `tests/js/sentence.test.mjs` | New | Test suite circuit-breaker HTTP 501 dan pembentukan kalimat B0 lokal |
| 10 | `tests/test_signbridge_suite.py` | Modified | Perbaikan PyTest menggunakan `tmp_path` agar tidak menimpa model produksi |
| 11 | `web/css/style.css` | Modified | Penambahan gaya visual HUD debug overlay, status badge, dan layout kamera |
| 12 | `web/index.html` | Modified | Integrasi panel HUD overlay `#debug-overlay-panel` pada view kamera utama |
| 13 | `web/js/app.js` | Modified | Integrasi dynamic threshold, framing alert, feedback badge transparan, dan kandidat klik |
| 14 | `web/js/config.js` | Modified | Konfigurasi two-tier threshold (`candidate: 0.25`, `autoSpeak: 0.50`), timing ms adaptif |
| 15 | `web/js/fingerspell.js` | Modified | Sinkronisasi penamaan kelas fingerspell dan stabilitas temporal |
| 16 | `web/js/recognizer.js` | Modified | Batas signing space adaptif (close framing Y=0.95), FPS dinamis, klasifikasi two-tier |
| 17 | `web/js/sentence.js` | Modified | Circuit-breaker otomatis fallback lokal B0 saat backend 501 |
| 18 | `web/js/speech.js` | Modified | Kompatibilitas TTS Chromium/Edge (`resume()` handling), chime konfirmasi audio |
| 19 | `web/js/vision.js` | Modified | Koreksi un-mirror teks kanvas (`ctx.scale(-1, 1)`) agar tidak terbalik cermin |
| 20 | `web/model/labels.json` | Modified | Sinkronisasi 32 label resmi WL-BISINDO (`AIR`..`MALAM`) |
| 21 | `web/model/student_int8.onnx` | Modified | Penyelarasan salinan unquantized FP32 dengan model terlatih 5.46 MB |
| 22 | `web/sw.js` | Modified | Pembaruan cache Service Worker ke versi v7 untuk memuat model terbaru |

---

## 5. Hasil Pengujian JavaScript (Node.js)

Perintah: `node --test tests/js/parity.test.mjs tests/js/handcrop.test.mjs tests/js/recognizer_stability.test.mjs tests/js/sentence.test.mjs`

```text
✔ Kontrak 4: computeHandCropBox (+25% margin) identik dengan Python (5.84ms)
✔ Kontrak 4 & 5: cropAndResizeHand dan normalizeImagenet identik dengan Python (< 1e-5) (6.46ms)
✔ Kontrak 1 & 3: selectFromHolistic identik dengan Python (< 1e-6) (6.63ms)
✔ Kontrak 3: trimInactive memangkas frame diam identik dengan Python (13.75ms)
✔ Kontrak 3: normalizePose (pusat bahu & lebar bahu) identik dengan Python (< 1e-5) (14.69ms)
✔ Kontrak 3: resampleFrames(64) identik dengan Python (< 1e-5) (11.44ms)
✔ Kontrak 3: preprocessKeypoints end-to-end identik dengan Python (< 1e-5) (24.80ms)
✔ isInSigningSpace: deteksi posisi tangan aktif vs istirahat (2.87ms)
✔ hasDetectedHands: validasi keberadaan tangan (0.89ms)
✔ SignRecognizer: supresi false positive saat tangan diam di posisi istirahat (8.47ms)
✔ SignRecognizer: supresi hasil berkeyakinan rendah (confidence threshold) (18.56ms)
✔ classifyAlphabetGeometry & FingerspellRecognizer: pengenalan bentuk abjad jari 21 titik (2.59ms)
✔ SignRecognizer: toleransi tracking dropout 1-2 frame (grace period) tanpa mereset activeBuffer (1.24ms)
✔ SignRecognizer: ambang batas 0.35 menerima prediksi valid dengan margin kuat (11.01ms)
✔ isInSigningSpace: deteksi tangan aktif ketika ujung jari terangkat meski pergelangan di batas bawah (0.52ms)
✔ isInSigningSpace: adaptif terhadap posisi kamera dekat (midShoulderY >= 0.50) (0.36ms)
✔ checkCameraFraming: mendeteksi posisi terlalu dekat dan tangan terpotong di tepi (1.27ms)
✔ SignRecognizer: dua tingkat ambang batas (candidate vs auto-speak) (8.71ms)
✔ SignRecognizer: getDynamicThresholds menghitung frame sesuai FPS (0.46ms)
✔ glossToSentenceLocal: konstruksi kalimat B0 lokal bahasa Indonesia (5.82ms)
✔ glossToSentenceLocal: konstruksi kalimat B0 lokal bahasa Filipina (0.57ms)
✔ buildNaturalSentence: bebas HTTP 501 saat apiBaseUrl kosong (Edge/Offline Mode) (0.81ms)
✔ buildNaturalSentence: circuit-breaker aktif saat server mengembalikan 501 (3.97ms)
✔ buildNaturalSentence: sukses menggunakan server saat endpoint 200 OK (1.01ms)
✔ sentenceToConceptGlosses: konversi teks ucapan menjadi konsep isyarat (1.48ms)

ℹ tests 25 | suites 0 | pass 25 | fail 0 | cancelled 0 | skipped 0 | todo 0
ℹ duration_ms 405.06ms
```
**Status: 25/25 Tests PASS (100%)**

---

## 6. Hasil Pengujian Python (PyTest)

Perintah: `python -m pytest tests/test_signbridge_suite.py tests/test_database_integration.py -v`

```text
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-8.2.2, pluggy-1.6.0
rootdir: D:\SEMESTER 5\ML\Projek_1
collected 18 items

tests/test_signbridge_suite.py::test_contract_1_constants_and_holistic_selection PASSED [  5%]
tests/test_signbridge_suite.py::test_graph_connected PASSED              [ 11%]
tests/test_signbridge_suite.py::test_contract_3_features_pipeline PASSED [ 16%]
tests/test_signbridge_suite.py::test_augmentation_and_mirror_swap PASSED [ 22%]
tests/test_signbridge_suite.py::test_dataset_sd_si_and_phonology PASSED  [ 27%]
tests/test_signbridge_suite.py::test_video_models_m0_m1_m2_m3_m4_m5 PASSED [ 33%]
tests/test_signbridge_suite.py::test_contract_2_onnx_export_and_parity PASSED [ 38%]
tests/test_signbridge_suite.py::test_contract_4_and_5_handcrop_and_image_models PASSED [ 44%]
tests/test_signbridge_suite.py::test_audio_modality_metrics PASSED       [ 50%]
tests/test_signbridge_suite.py::test_text_modality_and_disjoint_manual_test PASSED [ 55%]
tests/test_signbridge_suite.py::test_bridge_three_layers_and_fallback PASSED [ 61%]
tests/test_signbridge_suite.py::test_contract_6_fastapi_server_endpoints PASSED [ 66%]
tests/test_database_integration.py::test_db_schema_seeding_and_status PASSED [ 72%]
tests/test_database_integration.py::test_db_concepts_models_and_evaluations_endpoints PASSED [ 77%]
tests/test_database_integration.py::test_inference_logging_and_recordings_crud PASSED [ 83%]
tests/test_database_integration.py::test_database_failure_graceful_degradation PASSED [ 88%]
tests/test_database_integration.py::test_runtime_startup_without_torch PASSED [ 94%]
tests/test_database_integration.py::test_training_imports_remain_available PASSED [100%]

======================= 18 passed, 7 warnings in 22.81s =======================
```
**Status: 18/18 Tests PASS (100%)**

---

## 7. Verifikasi SHA-256 Model Sebelum dan Sesudah Push

| File | Parameter | Nilai Sebelum Push | Nilai Sesudah Push | Status Integritas |
|:---|:---|:---|:---|:---:|
| `web/model/student.onnx` | Ukuran File | 5,458,187 bytes | 5,458,187 bytes | **IDENTIK (100%)** |
| `web/model/student.onnx` | SHA-256 Hash | `48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572` | `48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572` | **IDENTIK (100%)** |

---

## 8. Status Working Tree

```text
## feature/field-test-readiness...origin/feature/field-test-readiness
```
Working tree bersih (*clean*). Seluruh perubahan yang direncanakan telah di-stage dan di-commit tanpa ada file yang tertinggal.

---

## 9. Status Push GitHub

```text
To https://github.com/KarinaGlo/SignBridge.git
   aed6c19..7b4c4e8  feature/field-test-readiness -> feature/field-test-readiness
branch 'feature/field-test-readiness' set up to track 'origin/feature/field-test-readiness'.
```

Verifikasi `git ls-remote`:
```text
7b4c4e86ec1172b3c56eeb7b79f6dcdf7c7e7d3e	refs/heads/feature/field-test-readiness
```
Commit `7b4c4e8` telah resmi tercatat di remote repository GitHub.

---

## 10. Catatan Terkait File yang Tidak Dimasukkan

- Direktori `data/keypoints/` tidak dimasukkan karena memang dikecualikan oleh aturan `.gitignore` (baris 50) dan tidak disimpan di repositori Git.
- Lingkungan virtual (`.venv`, `.venv_m0`), file temporary (`.pytest_cache`, `__pycache__`), dan file environment lokal (`.env`) tetap aman dan diabaikan sesuai aturan `.gitignore`.
- Model produksi `web/model/student.onnx` tidak mengalami perubahan bit/bobot selama proses commit/push ini.
