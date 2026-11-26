# PHASE 3.1 — RECORDER FIX REPORT
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

Laporan ini mendokumentasikan perbaikan terkontrol terhadap 3 temuan audit Recorder pada Phase 3 tanpa mengubah arsitektur M6, Dictionary B, atau format dataset lama.

---

## 1. Ringkasan Berkas yang Diubah

| Berkas | Perubahan Utama | Backward Compatibility |
| :--- | :--- | :--- |
| [`web/js/recorder.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js) | (1) `MultimodalCapture.pushFrame()` menyimpan `frame_index`, `timestamp_ms`, `valid_hand`, dan `keypoints` dengan referensi waktu tunggal `recordingStartMs` bersama audio (`audioStartOffsetMs`); (2) `MultimodalRecorder.addClip()` menolak target kosong/`"HALO"`/di luar `BISINDO_GLOSSES` atau `FINGERSPELL_LABELS`; (3) `classifyMicrophoneError()` mengklasifikasikan error izin/perangkat mikrofon dan mencatat `audio_status` + `audio_missing_reason` tanpa memalsukan WAV. | `keypoints` tetap `[F][86][3]`; `frameRecords` bersifat opsional agar data/test lama tanpa `frameRecords` tetap berjalan. |
| [`web/js/app.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js) | (1) `populateTargets()` menambahkan placeholder kosong `-- Pilih Target --` agar target tidak terisi otomatis; (2) `recBtn` menolak perekaman bila target belum dipilih atau tidak valid di Dictionary B; (3) menghapus pemanggilan `speakText()` pada `bindRecorderControls()` dan menampilkan pesan peringatan visual yang jelas ketika `audioStatus === "missing"`. | Tidak mengubah alur tab lain (`panel-translate`, dll.). |
| [`tests/js/recorder.test.mjs`](file:///d:/SEMESTER%205/ML/Projek_1/tests/js/recorder.test.mjs) | Menambahkan 3 regression test baru (per-frame timestamps, penolakan target kosong/`HALO`, dan klasifikasi error mikrofon). | Seluruh 15 test lama tetap dipertahankan dan lulus. |

---

## 2. Detail Perbaikan per Task

### Task A — Timestamp per Frame
- `MultimodalCapture` menggunakan `nowMs()` (`performance.now()` dengan fallback `Date.now()`) yang diinisialisasi pada `this.recordingStartMs` untuk menyinkronkan `timestamp_ms` video dan `audioStartOffsetMs` audio pada referensi waktu yang sama.
- Setiap frame pada `frameRecords` memuat: `frame_index`, `timestamp_ms`, `valid_hand`, dan `keypoints`.
- `*_kp.json` menyimpan `keypoints` (kompatibel penuh dengan `load_pose()` di `signbridge/multimodal/features.py`) dan `frame_records`. `*_meta.json` menyimpan `frame_timestamps_ms` serta `audio_start_offset_ms`.

### Task B — Fallback Label (Dictionary B)
- Fallback `"HALO"` dihapus dari [`web/js/app.js#L1183`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1183) dan [`web/js/recorder.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js).
- Jika pengguna belum memilih target, UI menampilkan pesan wajib memilih target dan tidak membuat klip/sampel apa pun.
- `MultimodalRecorder.addClip()` memvalidasi target terhadap `BISINDO_GLOSSES` (32 gloss, Dictionary B) atau `FINGERSPELL_LABELS` (A–Z) dan melempar `Error` jika tidak valid.

### Task C — Microphone Error UI
- `MultimodalCapture.capture()` menangkap error mikrofon melalui `classifyMicrophoneError(err)` (`permission_denied`, `device_not_found`, `capture_error`, atau `empty_audio_stream`).
- Kamera/video tetap berfungsi jika tersedia, audio ditandai `audio_status = "missing"` dengan `audio_missing_reason` di `*_meta.json` tanpa membuat WAV palsu, dan UI menampilkan pesan peringatan jelas beserta ajakan mencoba rekam ulang.
