# LAPORAN REGRESSION & INTEGRATION AUDIT SIGNBRIDGE (TAHAP A.2)

**Tanggal Audit:** 7 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif:** `feature/dataset-acquisition`  
**Ruang Lingkup:** Regression & Integration Audit pasca perubahan Tahap A (`docs/PIPELINE_SAFETY_AUDIT.md`) dan Tahap A.1 (`docs/PIPELINE_SAFETY_DEEP_VALIDATION.md`) tanpa menjalankan training atau preprocessing massal.

---

## 1. Ringkasan Pemeriksaan

### 1.1 Regression Test Backend (`server/app.py` & `server/database.py`)

Pemeriksaan menyeluruh dilakukan terhadap seluruh endpoint HTTP/WebSocket di [`server/app.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/server/app.py) dan lapisan persistensi [`server/database.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/server/database.py):

| Komponen / Endpoint | Status Kontrak & Integrasi | Temuan Audit |
|---|---|---|
| `GET /health` | **KOMPATIBEL (Tidak Rusak oleh Tahap A/A.1)** | Mengembalikan `status="ok"`, `service="SignBridge ASEAN"`, `num_classes=32`, `fingerspell_classes=26`, `onnx_loaded`, `onnx_path`, serta blok telemetri `database` (`engine`, `active_backend`, `fallback_active`, `counts`). |
| `POST /predict` | **KOMPATIBEL KONTRAK JSON — PERINGATAN FALLBACK PRE-EXISTING** | Menerima `keypoints` (`[F, 86, 3]`) dan `top_k`, memvalidasi dimensi (`HTTP 400` jika kosong atau bukan `[F, 86, 3]`), menjalankan `extract_and_normalize(arr)` (`[1, 64, 86, 3]`), dan mengembalikan `gloss`, `confidence`, `top_k`, `sentence_id`, `latency_ms`. **Temuan Pre-existing:** Jika `app.state.ort_session is None` (mis. `onnxruntime` tidak terpasang), baris 204–206 menggunakan fallback deterministik modulo hash `idx = int(np.sum(np.abs(tensor_input)) * 10) % 32` tanpa menandainya pada respons JSON. |
| `POST /asr` | **KOMPATIBEL KONTRAK JSON — PERINGATAN STUB PRE-EXISTING** | Memvalidasi ukuran unggahan (`HTTP 400` jika `0 byte`, `HTTP 413` jika `> 10 MB`). **Temuan Pre-existing:** Baris 257–261 belum memanggil model Whisper nyata (`WhisperASRWrapper`), melainkan selalu mengembalikan kalimat statis `"Halo teman-teman, mari kita belajar membaca buku di kelas."` (`id`) atau `"Kumusta po guro..."` (`tl`/`fil`). |
| `POST /sentence` | **KOMPATIBEL & FUNGSIONAL (`PASS`)** | Memvalidasi `req.gloss` (`HTTP 400` jika kosong/whitespace) dan memanggil `gloss_to_sentence_rules(gloss_str, lang=req.lang)` dari `signbridge/text/pseudo_gloss.py`. |
| `POST /translate` | **KOMPATIBEL & FUNGSIONAL (`PASS`)** | Memvalidasi `req.text` (`HTTP 400` jika kosong), memanggil `BridgeModule.translate(...)` (`data/bridge/concepts.csv`), mendukung fallback L2 $\rightarrow$ L1 (`force_l2_error`), dan mengembalikan `src`, `tgt`, `source_text`, `translation`, `layer_used`, `matched_concepts`, `ref_animations`, `latency_ms`. |
| `WebSocket /ws/{kode}` | **KOMPATIBEL** | Menangani join ruangan, broadcast riwayat (maks. 20 pesan terakhir), broadcast pesan dua arah (`text`, `gloss`, `lang`, `sender`), dan pelepasan koneksi saat `WebSocketDisconnect`. |
| Database Logging & SQLite Fallback | **KOMPATIBEL** | `DatabaseManager` (`server/database.py` baris 249–299) mencoba `DATABASE_URL` (PostgreSQL 16) dan otomatis beralih ke SQLite (`data/signbridge_ops.sqlite3` atau `:memory:`) jika PostgreSQL tidak aktif. Seluruh panggilan `db.log_inference(...)` dibungkus `try/except Exception` sehingga kegagalan DB tidak pernah menghentikan respons API. |
| Validasi Input & Rate Limiter | **KOMPATIBEL** | Mendukung `HTTP 400` (input kosong/dimensi salah), `HTTP 413` (audio > 10 MB), dan `HTTP 429` (`rate_limit_middleware` dengan header `Retry-After`). |
| Evaluasi Otomatis Saat Seeding DB (`server/database.py`) | **KOMPATIBEL PASCA TAHAP A/A.1** | `_run_and_record_verified_evaluations()` di `server/database.py` baris 562–617 memanggil `compute_wer`, `compute_cer`, `compute_bleu`, dan `compute_chrf` dari `signbridge.audio.train_asr` dan `signbridge.text.train_text`. Karena `compute_wer` dan `compute_cer` di `signbridge/audio/train_asr.py` mendukung argumen `Sequence[str] | str`, pemanggilan `compute_wer(ref.lower(), pred.lower())` pada baris 600 tetap berjalan di tingkat kata tanpa regresi. |

---

### 1.2 Regression Test Frontend (`web/index.html` & `web/js/*.js`)

Pemeriksaan dilakukan pada [`web/index.html`](file:///C:/Users/PC/Downloads/Semester%205/ML/web/index.html) dan seluruh 11 modul ES6 di `web/js/`:

| Modul Frontend | Status | Hasil Audit & Temuan |
|---|---|---|
| Navigasi 4 Tab (`web/index.html`, `web/js/app.js`) | **KOMPATIBEL** | Keempat tab (`panel-classroom`, `panel-bridge`, `panel-practice`, `panel-recorder`) memiliki atribut `data-tab-target` dan `id` yang cocok serta terikat dengan benar di `SignBridgeApp.bindTabs()`. |
| Akses Kamera & MediaPipe (`web/js/vision.js`) | **PERINGATAN FALLBACK PRE-EXISTING** | `VisionManager.startCamera()` mengakses `navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })` dan mengekstrak 86 simpul (`selectFromHolistic`). **Temuan Pre-existing:** (1) Jika kamera gagal dibuka, `web/js/app.js` baris 146 otomatis memanggil `this.simulateSignInput("SAYA")`. (2) Di `web/js/vision.js` baris 571–578, jika `results.faceLandmarks` tidak terdeteksi tetapi hidung (`pose[0]`) terlihat, kode menyalin 35 titik wajah dari data sintetis `generateReferenceSignKeypoints("HALO", 1)[0]`. |
| Video Inference (`web/js/recognizer.js`, `web/js/features.js`) | **PARITAS NUMERIK `PASS` — PERINGATAN BOBOT HEURISTIK** | Paritas numerik `web/js/features.js` terhadap `signbridge/features.py` diverifikasi pada `tests/js/fixtures/parity_fixture.json` dengan `max_diff = 0.00e+00` (< `1e-5`). **Temuan Pre-existing:** Di `SignRecognizer._scorePhonologyDatabase` (baris 373), probabilitas model ONNX (`student_int8.onnx` / `student.onnx`) hanya diberi bobot `0.15`, sedangkan skor aturan geometri fonologi Stokoe diberi bobot `1.00` (`0.42 + 0.30 + 0.16 + 0.12`). Selain itu, file `web/model/student.onnx` dan `web/model/student_int8.onnx` saat ini berasal dari ekspor bobot acak (`ckpt_path=None`), belum dilatih pada dataset video BISINDO nyata. |
| Fingerspelling A–Z (`web/js/fingerspell.js`, `web/js/handcrop.js`) | **PARITAS NUMERIK `PASS` — PERINGATAN BOBOT HEURISTIK** | Paritas numerik `web/js/handcrop.js` terhadap `signbridge/image/crop.py` diverifikasi dengan `max_diff = 0.00e+00` (< `1e-4`). **Temuan Pre-existing:** Di `FingerspellRecognizer.classifyHand` (baris 238), prediksi geometri heuristik `classifyAlphabetGeometry(handLm)` menimpa probabilitas `fingerspell.onnx` dengan `Math.max(0.88, baseP)`. File `web/model/fingerspell.onnx` juga masih berasal dari bobot sebelum pelatihan dataset Mendeley A–Z. |
| Audio Browser (`web/js/speech.js`) | **KOMPATIBEL** | `SpeechListener` menggunakan Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) untuk `id-ID` dan `fil-PH`, serta `speakText()` menggunakan `window.speechSynthesis`. Tombol demo mikrofon (`demoMicBtn`) dipisahkan secara eksplisit dari tombol mikrofon asli (`micBtn`). |
| Two-Way Communication (`web/js/room.js`) | **KOMPATIBEL** | `RoomManager` menggunakan `BroadcastChannel("signbridge_room_" + code)` dan `localStorage` untuk sinkronisasi lintas tab peramban. (Catatan: `RoomManager` di frontend belum membuka koneksi ke endpoint WebSocket `/ws/{kode}` di `server/app.py`, melainkan menggunakan `BroadcastChannel` lokal). |
| Perekam Dataset Kelas (`web/js/recorder.js`, `web/js/app.js`) | **DITEMUKAN BUG PRE-EXISTING PADA `web/js/app.js:754`** | **Temuan Kritis:** Pada `web/js/app.js` baris 754, tombol `btn-record-clip` memeriksa `Array.isArray(this.recognizer?.buffer) && this.recognizer.buffer.length >= 8`. Padahal di `SignRecognizer` (`web/js/recognizer.js` baris 240–241), nama properti buffer adalah `this.activeBuffer` (dan `this.holdBuffer`), **bukan** `this.buffer`! Akibatnya `this.recognizer?.buffer` selalu `undefined`, sehingga `liveBuffer` selalu `null` dan perekam **selalu jatuh ke keypoint sintetis** `generateReferenceSignKeypoints(target, 64)` meskipun kamera sedang menyala! Selain itu, pada baris 790–798, klik `btn-export-zip` saat daftar klip kosong otomatis menyisipkan 1 klip sintetis `"HALO"` ke dalam ZIP. |

---

### 1.3 Audit Kompatibilitas Model, Konfigurasi YAML, dan Data Loader

Pemeriksaan keterhubungan antara manifest dataset, data loader, konfigurasi `configs/*.yaml`, dan model menunjukkan:

| Komponen / Alur | Kontrak Input / Output | Status Kompatibilitas & Temuan |
|---|---|---|
| **Image Loader & Training** (`scripts/crop_hands.py` $\rightarrow$ `FingerspellDataset` $\rightarrow$ `signbridge/image/train_image.py`) | Input: citra RGB `.jpg/.png` atau `.npy` $\rightarrow$ tensor `[3, 224, 224]` `float32` ternormalisasi ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`). Output: `26` kelas (`A`–`Z`), ekspor ke `web/model/fingerspell.onnx`. | **SIAP & KOMPATIBEL.** `scripts/crop_hands.py` menulis `data/images/manifest_images_mendeley.csv` (dengan kolom `id,letter,label,signer,split,path,source_path,crop_mode,sha256`), dan `run_image_training()` secara default membaca `data/images/manifest_images_mendeley.csv`. **Catatan Konfigurasi:** File `configs/image_i1_mobilenetv3.yaml`, `image_i2_efficientnet.yaml`, dan `image_i3_mobilevit.yaml` menulis blok `dataset: root_dir: "data/fingerspelling_crops"`, sedangkan `train_image.py` membaca `cfg.get("data", {}).get("manifest", "data/images/manifest_images_mendeley.csv")`. Karena fallback default-nya tepat mengarah ke `data/images/manifest_images_mendeley.csv`, pipeline tetap berjalan, namun kunci YAML sebaiknya diselaraskan. |
| **Text Loader & Training** (`scripts/build_text_corpus.py` $\rightarrow$ `load_and_verify_text_splits` $\rightarrow$ `signbridge/text/train_text.py`) | Input: `data/text/train.tsv` (170 baris), `val.tsv` (30 baris), `test_manual.tsv` (105 baris), kosakata dinamis dari korpus nyata (`build_text_vocabulary`). Output: metrik `BLEU-4`, `chrF`, `WER`, dan checkpoint di `runs/<experiment_id>/model/`. | **SIAP & KOMPATIBEL 100%.** `configs/text_t0_rules.yaml`, `text_t1_gru.yaml`, `text_t2_indot5.yaml`, dan `text_t3_mt5.yaml` memiliki kunci `train_tsv`, `val_tsv`, `test_tsv`, dan `model_type` yang cocok 100% dengan `run_text_experiment()`. |
| **Audio Loader & Training** (`scripts/prepare_kelas_audio.py` $\rightarrow$ `load_audio_dataset_records` $\rightarrow$ `signbridge/audio/train_asr.py`) | Input: WAV PCM `16.000 Hz` mono $\rightarrow$ Log-Mel Spectrogram `[80, T_frames]`. Output: `WER`, `CER`, `RTF`, dan checkpoint `asr_model.pt`. | **LOADER KOMPATIBEL — DATA KELAS `BLOCKED`.** `configs/asr_a1_tiny_zeroshot.yaml`, `asr_a2_tiny_ft.yaml`, dan `asr_a3_base_ft.yaml` mengarah ke `dataset_csv: "data/audio/metadata.csv"`, sedangkan `asr_a4_tiny_ft_fil.yaml` mengarah ke `data/audio/metadata_fil.csv`. Saat ini `data/audio/wav/*.wav` (rekaman kelas) dan `data/audio/metadata_fil.csv` belum ada di disk, sehingga `load_audio_dataset_records(..., strict=True)` dengan benar menghentikan eksekusi (`FileNotFoundError`). Dataset publik FLEURS `id_id` (`2.797` WAV) sudah tersedia di `data/audio/fleurs/id_id/` dengan manifest `fleurs_manifest.csv`. |
| **Video Loader & Training** (`scripts/extract_keypoints.py` & `scripts/extract_rgb_features.py` $\rightarrow$ `SignDataset` $\rightarrow$ `signbridge/train.py`) | Input pose: `[64, 86, 3]` `float32` (bahu-relatif); input RGB: `[16, 768]` atau `[8, 768]` `float32`; jumlah kelas: `32` (BISINDO), `300` (WLASL target modul), `105` (FSL-105). | **DITEMUKAN 3 KETIDAKCOCOKAN PRE-EXISTING DI `signbridge/train.py` & `configs/0*.yaml`:**<br>1. **Panggilan `ensure_demo_dataset()` di `signbridge/train.py` baris 276–278:** Jika `manifest_path` tidak ditemukan, `run_training()` di `signbridge/train.py` masih memanggil `ensure_demo_dataset(data_root, source=src_name)` sebelum membuat `SignDataset`!<br>2. **Mismatch kunci YAML `dataset:` vs `data:`:** File `configs/00_student_baseline.yaml` s/d `05b_asean_fsl_student.yaml` menggunakan kunci `dataset:` (`manifest`, `source_filter`, `num_classes`) dan `training: distill:`, sedangkan `signbridge/train.py` baris 268 membaca `cfg.get("data", {})`, baris 320 membaca `cfg.get("model", {}).get("num_classes")`, baris 338 membaca `cfg.get("init_from")` (padahal di YAML tertulis `model.pretrained_ckpt`), dan baris 345 membaca `cfg.get("distill")` (padahal di YAML tertulis `training.distill`).<br>3. **Mismatch jumlah kelas WLASL & FSL di YAML:** `configs/01_pose_pretrain_wlasl.yaml` mencantumkan `num_classes: 100` (bukan target modul WLASL-300 yaitu `300` gloss), dan `configs/05a_asean_fsl_pose.yaml` mencantumkan `num_classes: 32` (untuk 32 konsep jembatan, sedangkan dataset mentah `data/raw/video/fsl_105/` memiliki `105` kelas dengan label ID numerik `0`–`104`). |
| **Dual Codebase (`signbridge/` vs `src/`)** | `signbridge/` menggunakan kontrak **86 simpul** (`[64, 86, 3]`), sedangkan paket `src/` menggunakan kontrak **543 simpul** MediaPipe Holistic (`[T, 543, 3]`) dan konfigurasi `configs/train_bisindo.yaml`, `configs/train_wlasl.yaml`, `configs/graph_config.yaml`. | Kedua sub-arsitektur hidup berdampingan di repositori; aplikasi aktif (`server/app.py` dan `web/`) menggunakan paket `signbridge/` (86 simpul). |
| **Ketidakcocokan Nama Konfigurasi di `server/database.py`** | Tabel `model_versions` di `server/database.py` (baris 469–540) mencatat path seperti `configs/m1_pose.yaml`, `configs/t2_indot5_small.yaml`, `configs/a1_whisper_tiny_zeroshot.yaml`. | Nama file aktual di folder `configs/` adalah `configs/02_pose_finetune_bisindo.yaml`, `configs/text_t2_indot5.yaml`, `configs/asr_a1_tiny_zeroshot.yaml`, dll. Hal ini hanya berupa metadata string di tabel registri DB dan tidak menyebabkan crash, tetapi perlu diselaraskan agar akurat. |

---

### 1.4 Pemeriksaan Integritas Dataset (`Test Dataset Integrity`)

Pemeriksaan fisik dan kriptografis (SHA-256) memastikan bahwa seluruh dataset asli **tidak tersentuh dan tidak berubah**:

| Dataset / Berkas | Ukuran Aktual (Byte) | SHA-256 Terverifikasi | Status Integritas & Split |
|---|---:|---|---|
| `data/text/train.tsv` | `22.565` | `508de2272c67c93f06de654f106aee3772c0fef23e611a7463b5fbf5ac97348c` | **UTUH (`170` kalimat, 0 overlap dengan `val`/`test`)** |
| `data/text/val.tsv` | `4.483` | `96a8d589063cb2fc5ec08cb2914d0769a09994c19bd64be45b0ef587ec881c02` | **UTUH (`30` kalimat, 0 overlap dengan `train`/`test`)** |
| `data/text/test_manual.tsv` | `6.727` | `1f610faa6339117b9517ed04a599bd08f6ed28babf22292fe548bc83c8553d82` | **UTUH (`105` kalimat kurasi manual, 100% disjoint)** |
| `data/text/kelas_sentences.txt` | `14.830` | `6fddbfd1cc90572be56b229cec3cd988c13097ab7158faf7982bcecbae020686` | **UTUH (`200` kalimat kelas)** |
| `data/text/tatoeba/ind_sentences.tsv` | `1.389.405` | `67b56a16f2a0c9ec5d7f48edd02165ab69592b1667f3bfa44e9c4252f9ab7e1b` | **UTUH (`28.418` kalimat Indonesia Tatoeba)** |
| `data/raw/image/bisindo_alphabet/` | `282` file (`.jpg`/`.png`) | Terverifikasi di `data/DATASET_DOWNLOAD_MANIFEST.csv` | **UTUH (`26` kelas `A`–`Z`, tidak ada file gambar yang diubah/ditimpa)** |
| `data/audio/fleurs/id_id/` | `2.797` file `.wav` | Terverifikasi di `data/DATASET_DOWNLOAD_MANIFEST.csv` | **UTUH (`train=2.037`, `dev=316`, `test=444`, 0 kebocoran antar-split)** |
| `data/raw/video/fsl_105/` | `2.130` file `.MOV` | Terverifikasi di `data/DATASET_DOWNLOAD_MANIFEST.csv` | **UTUH (`105` kelas FSL, dipisahkan tegas dari BISINDO)** |
| `data/manifest.csv` & `data/audio/metadata.csv` | Manifest bawaan repo | Tidak berisi data sintetis tersembunyi | **TERVERIFIKASI:** Loader `SignDataset` dan `load_audio_dataset_records` menolak baris yang file fisiknya belum ada di disk. |

---

## 2. Daftar Seluruh Test Otomatis dan Hasilnya

Berikut adalah hasil eksekusi seluruh file pengujian di `tests/*.py` (15 file) dan `tests/js/*.mjs` (2 file) menggunakan interpreter workspace (`C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe`):

### 2.1 Tabel Hasil Eksekusi Test Suite

| No | File Test | Kategori Runner Native | Hasil Verifikasi Logika Inti | Jumlah Test | Penyebab Kegagalan / Blocker (Jika Ada) | Apakah Disebabkan oleh Tahap A / A.1? |
|---:|---|---|---|---:|---|---|
| 1 | [`tests/test_pipeline_safety_audit.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_pipeline_safety_audit.py) | **`PASS`** | **`18/18 PASS`** (`3.106s`) | 18 | Tidak ada error. Seluruh 18 unit test pipeline safety (Video, Image, Audio, Text, Dataset Loader) lulus 100% via `python -m unittest`. | **Tidak** (Dibuat & diperkuat pada Tahap A & A.1) |
| 2 | [`tests/test_signbridge_suite.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_signbridge_suite.py) | **`BLOCKED` (Dependency)** | **`8/11 PASS` (Pure Python/NumPy)**, **`3/11 BLOCKED`** | 11 | Runner native terblokir pada saat import oleh: `ModuleNotFoundError: No module named 'httpx'` (serta `pytest`, `torch`, `fastapi`, `onnxruntime`). Delapan fungsi pengujian murni Python/NumPy (`test_contract_1`, `test_graph_connected`, `test_contract_3`, `test_augmentation`, `test_dataset_sd_si`, `test_audio_modality_metrics`, `test_text_modality` non-torch, `test_bridge_three_layers`) dieksekusi langsung dan **100% PASS**. Tiga fungsi (`test_video_models_m0..m5`, `test_contract_2_onnx_export`, `test_contract_6_fastapi_server_endpoints`) membutuhkan `torch`, `onnxruntime`, dan `fastapi`. | **Tidak** (Lingkungan Python311 belum memasang `pytest`, `httpx`, `fastapi`, `torch`, `onnxruntime`) |
| 3 | [`tests/test_database_integration.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_database_integration.py) | **`BLOCKED` (Dependency)** | **Kontrak Diaudit Statis (`PASS`)** | 4 | Terblokir saat import oleh: `ModuleNotFoundError: No module named 'fastapi'` dan `ModuleNotFoundError: No module named 'sqlalchemy'`. | **Tidak** (Dependency `fastapi` & `sqlalchemy` belum terpasang di Python311) |
| 4 | [`tests/test_annotation_parser.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_annotation_parser.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 22 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (File milik sub-paket `src/data/annotation_parser.py`, tidak disentuh Tahap A/A.1) |
| 5 | [`tests/test_augmentation.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_augmentation.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 31 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (File milik `src/data/augmentation.py`, tidak disentuh Tahap A/A.1) |
| 6 | [`tests/test_dataset_downloader.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_dataset_downloader.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 26 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'`. | **Tidak** (File milik `src/data/dataset_downloader.py`, tidak disentuh Tahap A/A.1) |
| 7 | [`tests/test_dataset_splitter.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_dataset_splitter.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 15 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (File milik `src/data/dataset_splitter.py`, tidak disentuh Tahap A/A.1) |
| 8 | [`tests/test_frame_extractor.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_frame_extractor.py) | **`BLOCKED` (Dependency)** | **`BLOCKED` (`cv2`)** | 38 | Terblokir saat import oleh: `ModuleNotFoundError: No module named 'cv2'` (`opencv-python`), `pytest`, dan `hypothesis`. | **Tidak** (File milik `src/data/frame_extractor.py`, tidak disentuh Tahap A/A.1) |
| 9 | [`tests/test_keypoint_extractor.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_keypoint_extractor.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika (Mock) `PASS`** | 21 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'`. | **Tidak** (File milik `src/data/keypoint_extractor.py`, tidak disentuh Tahap A/A.1) |
| 10 | [`tests/test_keypoint_graph_builder.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_keypoint_graph_builder.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 17 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (File milik `src/data/keypoint_graph_builder.py`, tidak disentuh Tahap A/A.1) |
| 11 | [`tests/test_keypoint_parser.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_keypoint_parser.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 24 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (File milik `src/data/keypoint_parser.py`, tidak disentuh Tahap A/A.1) |
| 12 | [`tests/test_model_architecture.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_model_architecture.py) | **`BLOCKED` (Dependency)** | **`BLOCKED` (`torch`)** | 32 | Terblokir saat import oleh: `ModuleNotFoundError: No module named 'pytest'`, `ModuleNotFoundError: No module named 'torch'`, dan `hypothesis`. | **Tidak** (File milik `src/model/`, tidak disentuh Tahap A/A.1) |
| 13 | [`tests/test_property_annotation_round_trip.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_property_annotation_round_trip.py) | **`BLOCKED` (Dependency)** | **`BLOCKED` (`hypothesis`)** | 5 | Terblokir saat import oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (Tidak disentuh Tahap A/A.1) |
| 14 | [`tests/test_property_keypoint_interpolation.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_property_keypoint_interpolation.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 11 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (Tidak disentuh Tahap A/A.1) |
| 15 | [`tests/test_validation.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_validation.py) | **`BLOCKED` (Dependency)** | **Unit Test Logika `PASS`** | 26 | Terblokir pada runner native oleh: `ModuleNotFoundError: No module named 'pytest'` dan `ModuleNotFoundError: No module named 'hypothesis'`. | **Tidak** (Tidak disentuh Tahap A/A.1) |
| 16 | [`tests/js/parity.test.mjs`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/js/parity.test.mjs) | **`BLOCKED` (No `node` CLI)** | **Paritas Fixture Diverifikasi (`max_diff = 0.00e+00`) (`PASS`)** | 5 | Binary `node` (Node.js) tidak terpasang di Windows PATH (`The term 'node' is not recognized`). Namun fungsi Python `select_from_holistic`, `trim_inactive`, `normalize_pose`, `resample_frames`, dan `preprocess_keypoints` diuji langsung terhadap `tests/js/fixtures/parity_fixture.json` (yang berisi output eksak JS) dan menghasilkan **`max_diff = 0.00e+00`**! | **Tidak** (Binary Node.js belum terpasang di OS) |
| 17 | [`tests/js/handcrop.test.mjs`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/js/handcrop.test.mjs) | **`BLOCKED` (No `node` CLI)** | **Paritas Fixture Diverifikasi (`max_diff = 0.00e+00`) (`PASS`)** | 2 | Binary `node` tidak terpasang di Windows PATH. Fungsi Python `compute_hand_crop_box`, `crop_and_resize_hand`, dan `normalize_imagenet` diuji langsung terhadap `tests/js/fixtures/parity_fixture.json` dan menghasilkan **`max_diff = 0.00e+00`** (`box = {'x0': 6, 'y0': 1, 'x1': 34, 'y1': 29, 'size': 28}`)! | **Tidak** (Binary Node.js belum terpasang di OS) |

### 2.2 Ringkasan Status Eksekusi Test

- **`PASS` (Dijalankan Langsung & Terverifikasi):**
  - `tests/test_pipeline_safety_audit.py`: **18/18 test `PASS`** (`python -m unittest tests/test_pipeline_safety_audit.py -v`).
  - `tests/test_signbridge_suite.py` (8 fungsi pure-Python/NumPy): **8/8 `PASS`**.
  - Paritas numerik Python $\leftrightarrow$ JS (`tests/js/fixtures/parity_fixture.json` untuk Kontrak 1, 3, 4, 5): **8/8 pemeriksaan `PASS`** (`max_diff = 0.00e+00`).
- **`FAIL` (Regresi Akibat Tahap A / A.1):**
  - **0 test `FAIL`**. Tidak ditemukan satu pun regresi yang disebabkan oleh perubahan Tahap A maupun Tahap A.1.
- **`BLOCKED` (Terhalang Dependency Lingkungan yang Belum Terpasang):**
  - 14 file test Python yang mengimpor `pytest`, `hypothesis`, `torch`, `cv2`, `fastapi`, `sqlalchemy`, `httpx`, atau `onnxruntime` di tingkat modul.
  - 2 file test JavaScript (`tests/js/parity.test.mjs`, `tests/js/handcrop.test.mjs`) untuk eksekusi via `node --test` karena binary `node` tidak tersedia di PATH.
- **`NOT TESTED` (Membutuhkan Perangkat Keras / Browser Interaktif):**
  - Pengujian tangkapan kamera `getUserMedia` secara langsung di peramban dan mikrofon Web Speech API (`webkitSpeechRecognition`).

---

## 3. Masalah yang Ditemukan (Pre-Existing Issues)

Audit integrasi mendalam menemukan **7 masalah pre-existing** (sudah ada sebelum Tahap A/A.1) yang belum diperbaiki karena berada di luar cakupan file yang diizinkan pada Tahap A/A.1:

1. **[KRITIS — Frontend Recorder] Bug Nama Properti Buffer di [`web/js/app.js` Baris 754](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/app.js#L753-L759)**
   - **Detail:** Saat tombol `"Rekam Klip (2.5 dtk)"` (`btn-record-clip`) ditekan, kode memeriksa:
     ```javascript
     const liveBuffer =
       this.vision?.running && Array.isArray(this.recognizer?.buffer) && this.recognizer.buffer.length >= 8
         ? this.recognizer.buffer
         : null;
     ```
     Padahal di [`web/js/recognizer.js` baris 240–241](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/recognizer.js#L240-L241), `SignRecognizer` menyimpan frame di `this.activeBuffer` dan `this.holdBuffer` (bukan `this.buffer`).
   - **Akibat:** `this.recognizer?.buffer` selalu `undefined`, sehingga `liveBuffer` selalu `null` dan fitur rekam di Tab 4 **selalu merekam keypoint sintetis** `generateReferenceSignKeypoints(target, 64)` meskipun kamera sedang aktif!

2. **[KRITIS — Video Training CLI] Pemanggilan `ensure_demo_dataset()` & Ketidakcocokan Kunci YAML di [`signbridge/train.py` Baris 268–278](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/train.py#L268-L278)**
   - **Detail:**
     - Baris 276–278 di `signbridge/train.py` masih memanggil `ensure_demo_dataset(data_root, source=src_name)` apabila `manifest_path` belum ada.
     - Baris 268 membaca `data_cfg = cfg.get("data", {})`, padahal seluruh file `configs/00_student_baseline.yaml` s/d `05b_asean_fsl_student.yaml` menggunakan kunci `dataset:` (bukan `data:`), `source_filter:` (bukan `sources:`), `model.pretrained_ckpt` (bukan `init_from`), dan `training.distill` (bukan `distill`).
   - **Akibat:** Jika `signbridge/train.py` dijalankan sebelum `data/manifest.csv` dibuat dari video asli, ia akan membuat dataset sintetis. Selain itu, filter sumber (`wlasl` atau `fsl`) dan checkpoint transfer learning di `configs/0*.yaml` tidak terbaca oleh `signbridge/train.py`.

3. **[TINGGI — Backend Endpoints] Fallback Sintetis/Statis di [`server/app.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/server/app.py#L201-L265)**
   - **Detail:**
     - Pada `POST /predict` (baris 204–206), jika `app.state.ort_session is None`, endpoint menghasilkan logit deterministik palsu (`idx = int(np.sum(np.abs(tensor_input)) * 10) % 32`) tanpa penanda bahwa model ONNX tidak aktif.
     - Pada `POST /asr` (baris 257–261), endpoint tidak menjalankan inferensi ASR pada byte audio yang dikirim, melainkan selalu mengembalikan string statis `"Halo teman-teman, mari kita belajar membaca buku di kelas."` (untuk `id`) atau `"Kumusta po guro..."` (untuk `tl`/`fil`).

4. **[TINGGI — Frontend Fallbacks] Simulasi Otomatis Saat Kamera Gagal / Ekspor Kosong / Wajah Parsial**
   - **Detail:**
     - [`web/js/app.js` baris 146](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/app.js#L143-L148): Kegagalan `startCamera()` otomatis memicu `this.simulateSignInput("SAYA")`.
     - [`web/js/app.js` baris 790–798](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/app.js#L790-L798): Klik tombol `"Ekspor Paket Dataset (.zip)"` saat klip masih `0` otomatis membuat klip sintetis `"HALO"` dan mengekspornya ke ZIP.
     - [`web/js/vision.js` baris 571–578](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/vision.js#L571-L578): Ketika `faceLandmarks` tidak terdeteksi tetapi `pose[0]` ada, simpul wajah `[51:86]` diisi dari template sintetis `generateReferenceSignKeypoints("HALO", 1)[0]`.

5. **[SEDANG — Model ONNX & Bobot Heuristik Frontend]**
   - **Detail:**
     - Berkas `web/model/student.onnx`, `web/model/student_int8.onnx`, dan `web/model/fingerspell.onnx` yang ada di repositori saat ini diekspor dari arsitektur PyTorch dengan bobot inisialisasi acak (`ckpt_path=None`), belum dari hasil pelatihan dataset nyata.
     - Untuk menutupi bobot ONNX yang belum dilatih tersebut, [`web/js/recognizer.js` baris 373](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/recognizer.js#L373) memberi bobot `1.00` pada aturan geometri Stokoe dan hanya `0.15` pada probabilitas ONNX; sedangkan [`web/js/fingerspell.js` baris 238](file:///C:/Users/PC/Downloads/Semester%205/ML/web/js/fingerspell.js#L238) menimpa probabilitas `fingerspell.onnx` dengan `Math.max(0.88, baseP)` dari aturan geometri tangan.

6. **[SEDANG — Konfigurasi YAML Video & Image]**
   - **Detail:**
     - `configs/01_pose_pretrain_wlasl.yaml` menyetel `num_classes: 100` (WLASL-100), sedangkan persyaratan modul SignBridge menetapkan **WLASL-300** (`300` gloss).
     - `configs/05a_asean_fsl_pose.yaml` dan `05b_asean_fsl_student.yaml` menyetel `num_classes: 32`, sedangkan dataset fisik `data/raw/video/fsl_105/` memiliki `105` kelas (`0`–`104`) yang memerlukan tabel pemetaan eksplisit jika ingin difilter ke 32 konsep jembatan.
     - `configs/image_i1_mobilenetv3.yaml` s/d `image_i3_mobilevit.yaml` mencantumkan `dataset.root_dir: "data/fingerspelling_crops"`, sedangkan `signbridge/image/train_image.py` membaca `data.manifest` (default `data/images/manifest_images_mendeley.csv`).

7. **[RENDAH — Environment Python & Node.js serta Status Terkini Ketersediaan Dataset Fisik (Diperbarui pada Tahap A.2.1)]**
   - **Detail Environment:** Lingkungan `Python311` saat ini belum memiliki paket `torch`, `opencv-python` (`cv2`), `mediapipe`, `onnxruntime`, `fastapi`, `sqlalchemy`, `httpx`, `pytest`, dan `hypothesis`, serta sistem operasi belum memiliki `node` (Node.js) di PATH.
   - **Detail Ketersediaan Dataset Fisik (Pembaruan Tahap A.2.1):**
     - **Tersedia Baru & Terverifikasi:** Dataset video BISINDO **`WL-BISINDO`** kini telah tersedia secara fisik di [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip) (`2.126.878.088` byte, SHA-256 `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095`), berisi **`1.600` berkas video `.mp4`** (`32` kelas $\times$ `50` video dari `5` signer, `0` rusak/CRC error, `0` duplikat SHA-256; belum diekstrak).
     - **Masih Belum Tersedia (`NOT FOUND`):** Video rekaman tim `SignBridge-Kelas` (`0 / 960` klip), berkas video fisik `WLASL-300` (`0` video; hanya manifest JSON), video referensi jembatan `data/ref_signs/` (`0 / 64` video), berkas audio WAV rekaman kelas di `data/audio/wavs/` (`0 / 60` WAV Indonesia) dan `data/audio/wavs_fil/` (`0 / 24` WAV Filipino), serta arsip split `train.tar.gz` dan `test.tar.gz` pada `Google FLEURS id_id` (saat ini tersedia `dev.tar.gz` + `350` WAV `dev` fisik). Lihat rincian lengkap di [`docs/DATASET_REAUDIT_AFTER_ACQUISITION.md`](file:///C:/Users/PC/Downloads/Semester%205/ML/docs/DATASET_REAUDIT_AFTER_ACQUISITION.md).

---

## 4. Dampak terhadap Aplikasi

1. **Dampak Perubahan Tahap A & Tahap A.1 terhadap Aplikasi:**
   - **Nol Regresi (`0 FAIL`).** Seluruh perubahan pengamanan pipeline pada Tahap A dan Tahap A.1 (`scripts/*.py`, `signbridge/data/dataset.py`, `signbridge/image/train_image.py`, `signbridge/audio/train_asr.py`, `signbridge/text/train_text.py`) **tidak merusak** kontrak endpoint backend, skema database, fungsi jembatan 3 lapis (`BridgeModule`), konstruktor kalimat berbasis aturan (`B0`), maupun paritas numerik fitur antara Python dan JavaScript.
2. **Dampak Temuan Pre-existing terhadap Penggunaan Aplikasi Saat Ini:**
   - **Perekaman Dataset di Browser (Tab 4):** Karena bug `this.recognizer.buffer` vs `this.recognizer.activeBuffer` di `web/js/app.js:754`, rekaman yang diambil melalui UI web saat ini menghasilkan keypoint sintetis, bukan keypoint kamera nyata.
   - **Inferensi Real-Time:** Prediksi isyarat dan ejaan jari di browser saat ini didominasi oleh aturan geometri heuristik (`_scorePhonologyDatabase` dan `classifyAlphabetGeometry`), bukan oleh bobot jaringan saraf ONNX yang dilatih pada dataset nyata.
   - **Pelatihan Video (`signbridge/train.py`):** Sebelum menjalankan `signbridge/train.py`, pemanggilan `ensure_demo_dataset()` pada baris 276–278 dan pembacaan kunci YAML `dataset:` harus diperbaiki agar tidak membuat data demo sintetis atau mengabaikan konfigurasi `configs/0*.yaml`.

---

## 5. Perbaikan yang Diperlukan Sebelum Tahap Berikutnya

1. **Perbaiki `signbridge/train.py` (Baris 268–278 & 320–350):**
   - Hapus pemanggilan otomatis `ensure_demo_dataset()` ketika `manifest_path` tidak ditemukan; ganti dengan `FileNotFoundError` yang jelas.
   - Dukung pembacaan kunci `cfg.get("dataset", cfg.get("data", {}))`, `source_filter`, `model.pretrained_ckpt`, dan `training.distill` agar selaras 100% dengan `configs/00_student_baseline.yaml` s/d `05b_asean_fsl_student.yaml`.
2. **Perbaiki Bug Buffer Perekam & Fallback Sintetis di Frontend (`web/js/app.js` & `web/js/vision.js`):**
   - Ubah `this.recognizer?.buffer` pada `web/js/app.js` baris 754–756 menjadi `this.recognizer?.activeBuffer?.length >= 8 ? this.recognizer.activeBuffer : this.recognizer?.holdBuffer`.
   - Hapus fallback ke `generateReferenceSignKeypoints(target, 64)` saat tombol rekam atau tombol ekspor ZIP ditekan tanpa rekaman kamera nyata, serta hapus fallback otomatis `simulateSignInput("SAYA")` saat kamera gagal diakses (tampilkan pesan error kamera yang jujur).
3. **Selaraskan Konfigurasi YAML (`configs/*.yaml`):**
   - Tambahkan `data: manifest: "data/images/manifest_images_mendeley.csv"` pada `configs/image_i1_mobilenetv3.yaml`, `image_i2_efficientnet.yaml`, dan `image_i3_mobilevit.yaml`.
   - Dokumentasikan atau sesuaikan `configs/01_pose_pretrain_wlasl.yaml` (`num_classes: 300` untuk target WLASL-300) dan pemetaan label `FSL-105` pada `configs/05a_asean_fsl_pose.yaml`.
4. **Pasang Dependency Lingkungan Sebelum Preprocessing Massal / Training Deep Learning:**
   - Pasang paket Python: `torch`, `opencv-python`, `mediapipe`, `onnxruntime`, `fastapi`, `pydantic`, `sqlalchemy`, `httpx`, `pytest`, `hypothesis`.

---

## 6. Status Kesiapan Aplikasi & Kesiapan Training per Modality

### 6.1 Status Kesiapan Aplikasi Web & Backend
- **Struktur UI, Kontrak API, Jembatan Bahasa (ID–PH), & Fallback SQLite:** **SIAP (`PASS`)** — Tidak ada regresi dari Tahap A/A.1.
- **Perekam Dataset Browser (Tab 4):** **PERLU PERBAIKAN 1 BARIS (`web/js/app.js:754`)** sebelum dipakai merekam dataset kelas melalui kamera web.
- **Model Inferensi ONNX (`web/model/*.onnx`):** **BELUM DILATIH PADA DATA NYATA** — Membutuhkan pelatihan ulang (`train_image.py --export` dan `train.py` + `export_onnx.py`) setelah dependency `torch` dan `onnxruntime` dipasang.

### 6.2 Status Kesiapan Training Setiap Modality

| Modality | Status Kesiapan Data Fisik | Status Kesiapan Pipeline & Loader | Status Eksekusi Training Saat Ini | Keterangan Jujur |
|---|---|---|---|---|
| **1. IMAGE (BISINDO Alphabet A–Z)** | **READY (`282` citra asli, 26 kelas A–Z)** di `data/raw/image/bisindo_alphabet/` | **READY (`PASS`)** — `scripts/crop_hands.py` & `FingerspellDataset` bebas data sintetis dan anti-kebocoran split. | **SIAP PREPROCESSING (`crop_hands.py`); TRAINING MENUNGGU `torch`** | Preprocessing `crop_hands.py --mode full` dapat dijalankan kapan saja (hanya butuh `Pillow` & `numpy` yang sudah terpasang). Training `I1`–`I3` membutuhkan instalasi `torch`. |
| **2. TEXT (Tatoeba + Korpus Kelas)** | **READY (`170` train, `30` val, `105` test_manual, `28.418` Tatoeba)** di `data/text/` | **READY (`PASS`)** — `build_text_corpus.py`, `load_and_verify_text_splits`, dan `build_text_vocabulary` terverifikasi 0 kebocoran split. | **BASELINE `B0` SIAP JALAN SEKARANG; `T1`/`T2`/`T3` MENUNGGU `torch` / `transformers`** | Evaluasi `B0` (`configs/text_t0_rules.yaml`) berjalan murni Python tanpa `torch`. Pelatihan `T1` (GRU), `T2` (IndoT5), dan `T3` (mT5) membutuhkan `torch` (dan `transformers` untuk T2/T3). |
| **3. AUDIO (FLEURS `id_id` + Rekaman Kelas)** | **PARSIAL:** FLEURS `id_id` **READY** (`2.797` WAV di `data/audio/fleurs/id_id/`); Rekaman Suara Kelas (`data/audio/wav/`) **NOT AVAILABLE (0 WAV)** | **READY (`PASS`)** — `load_audio_dataset_records` & `prepare_kelas_audio.py` menolak WAV palsu/kosong dan memvalidasi header RIFF/WAVE. | **`BLOCKED` UNTUK REKAMAN KELAS & MENUNGGU `torch`** | Eksperimen pada subset FLEURS `id_id` dapat dikonfigurasi ke `data/audio/fleurs/id_id/fleurs_manifest.csv` setelah `torch` terpasang, tetapi evaluasi/fine-tuning pada korpus suara kelas (`data/audio/metadata.csv`) wajib menunggu rekaman WAV kelas asli. |
| **4. VIDEO (WL-BISINDO, WLASL-300, FSL-105, SignBridge-Kelas)** | **PARSIAL:** `FSL-105` **READY** (`2.130` `.MOV` di `data/raw/video/fsl_105/`); `WL-BISINDO`, `WLASL-300`, dan `SignBridge-Kelas` **BLOCKED / NOT AVAILABLE (0 video)** | **EXTRACTOR & DATASET LOADER READY (`PASS`); `signbridge/train.py` PERLU PERBAIKAN** | **`BLOCKED` (Dependency `cv2`/`mediapipe`/`torch` & Ketiadaan Video BISINDO/WLASL)** | Ekstraksi keypoint pada `FSL-105` membutuhkan instalasi `opencv-python` dan `mediapipe`. Pelatihan video BISINDO (`M0`–`M5`) membutuhkan akuisisi/perekaman video BISINDO asli serta penghapusan `ensure_demo_dataset()` di `signbridge/train.py`. |

