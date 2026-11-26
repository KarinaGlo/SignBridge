# P0-E — PRE-FLIGHT AUDIT
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

---

## 1. Verifikasi Kesiapan Kode & Dokumentasi Phase 3 / 3.1

| Item Audit | Status | Bukti Aktual di Repositori |
| :--- | :---: | :--- |
| Dokumentasi Phase 3 & 3.1 | **OK** | [`PHASE_3_RECORDER_FINAL_READINESS_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_3_RECORDER_FINAL_READINESS_AUDIT.md), [`PHASE_3_1_RECORDER_FIX_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_3_1_RECORDER_FIX_REPORT.md), [`PHASE_3_1_P0_E_TEST_PROCEDURE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_3_1_P0_E_TEST_PROCEDURE.md). |
| Perbaikan Phase 3.1 di `web/js/recorder.js` | **OK** | `classifyMicrophoneError`, `frameRecords` (`frame_index`, `timestamp_ms`, `valid_hand`, `keypoints`), validasi Dictionary B tanpa fallback `HALO`, `audio_status` & `audio_missing_reason`. |
| Perbaikan Phase 3.1 di `web/js/app.js` | **OK** | Placeholder `-- Pilih Target --`, penolakan target kosong/tidak valid, penghapusan `speakText()` pada `bindRecorderControls()`, peringatan error mikrofon. |
| Integritas Dictionary B (32 Gloss) | **OK** | `BISINDO_32_GLOSSES` ([`signbridge/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/constants.py)) == [`web/model/labels.json`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/labels.json) == `BISINDO_GLOSSES` ([`web/js/config.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/config.js)) — **32/32 cocok eksak**. |
| Dependensi Runtime Python | **OK** | `torch 2.14.1+cpu`, `onnxruntime 1.31.1`, `numpy 2.4.4`, `Pillow`, `PyYAML` terpasang. |

---

## 2. Pemeriksaan Ketersediaan Artefak P0-E (Sebelum Pengujian Pengguna)

| Artefak | Lokasi | Status | Keterangan |
| :--- | :--- | :---: | :--- |
| Berkas ZIP Recorder Nyata | `data/raw/web_zips/` | **TIDAK ADA (`False`)** | 0 berkas `SignBridge_*.zip` ditemukan di seluruh repositori. |
| Manifest Multimodal Nyata | `data/multimodal/manifest_multimodal.csv` | **TIDAK ADA (`False`)** | Belum ada ZIP untuk diekstrak oleh `scripts/build_multimodal_manifest.py`. |
| Model ONNX M6 | `web/model/multimodal_fusion.onnx` | **TIDAK ADA (`False`)** | `MultimodalService` mengembalikan `available=False` (HTTP 503). |
| Checkpoint PyTorch M6 Nyata | `outputs/experiments/M6_multimodal_fusion/best_model.pt` | **TIDAK ADA (`False`)** | Belum ada training data nyata. |
| Smoke Checkpoint (Sintetis) | [`outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt`](file:///d:/SEMESTER%205/ML/Projek_1/outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt) | **ADA (`True`)** | Dilatih pada data random/sintetis (`--smoke`, 2 epoch); **bukan** model terlatih data nyata. |
