# LAPORAN VALIDASI FUNGSIONAL & KESIAPAN DEMONSTRASI (FASE 11)
**Proyek**: SignBridge ID–PH (BISINDO $\leftrightarrow$ FSL)  
**Tanggal Evaluasi**: 7 November 2026  
**Lingkungan Uji**: Windows Host + Docker Compose (`signbridge-asean` & `signbridge-postgres` PostgreSQL 16-alpine)  
**Endpoint Aktif**: `http://localhost:7860` (FastAPI Backend & Docs) & `http://localhost:8080` (PWA Frontend)

---

## 1. Fitur yang Berhasil Diuji Secara End-to-End

Seluruh komponen berikut telah diuji langsung terhadap container Docker aktif (`signbridge-asean` + `signbridge-postgres`), file media aktual (`.wav` & `.png`), runtime ONNX (`onnxruntime`), serta antarmuka PWA (`web/`):

1. **Persistensi Database PostgreSQL 16 & Volume Docker (`projek_1_pgdata`)**:
   - Penyimpanan dan pembacaan rekaman dataset melalui `POST /db/recordings` dan `GET /db/recordings`.
   - Pencatatan telemetri otomatis (*non-blocking inference logging*) ke tabel `inference_logs` dari keempat endpoint inferensi (`POST /predict`, `POST /asr`, `POST /sentence`, `POST /translate`) dan pembacaan melalui `GET /db/logs`.
   - Ketahanan data lintas `docker compose restart`: rekaman dan log inferensi tetap utuh di volume `/var/lib/docker/volumes/projek_1_pgdata/_data`.
   - Idempotensi *seeding*: tidak terjadi duplikasi data referensi setelah *restart* container (`sign_concepts = 58`, `model_versions = 20`, `evaluation_runs = 3`).
2. **Penyajian Aplikasi Web PWA & Navigasi Frontend (`http://localhost:8080`)**:
   - Seluruh aset statis (`/`, `/js/app.js`, `/js/vision.js`, `/js/recognizer.js`, `/js/fingerspell.js`, `/css/style.css`, `/model/labels.json`, `/model/fingerspell.json`, `/model/student.onnx`, `/model/fingerspell.onnx`) berhasil disajikan dengan kode HTTP `200 OK`.
   - Audit fungsional keempat tab navigasi utama (*Komunikasi 2 Arah*, *Kamus & Ejaan Jari A–Z*, *Rekam Dataset Mandiri*, *Metrik & Evaluasi*), kontrol izin kamera (`navigator.mediaDevices.getUserMedia`), serta tata letak responsif (*desktop* 2 kolom & *mobile* `<980px` 1 kolom).
3. **Alur Kerja Empat Modalitas (Video, Citra/Fingerspelling, Suara/Audio, Teks/Terjemahan)**:
   - **Video**: Prapemrosesan geometris 86 titik (`select_from_holistic` $\rightarrow$ `trim_inactive` $\rightarrow$ `normalize_pose` $\rightarrow$ `resample_frames` `[1, 64, 86, 3]`) dan inferensi ONNX (`student.onnx` FP32 & `student_int8.onnx` INT8) serta endpoint `POST /predict`.
   - **Citra / Fingerspelling A–Z**: Pembacaan file citra tangan `.png` nyata (`640x480`), pemotongan *bounding box* tangan +25% margin (`crop_and_resize_hand` $\rightarrow$ `224x224`), normalisasi ImageNet CHW (`[1, 3, 224, 224]`), dan inferensi ONNX `fingerspell.onnx`.
   - **Audio / Speech-to-Text & TTS**: Unggah file audio PCM WAV 16kHz 16-bit mono nyata (`48.044` byte, durasi `1,5` detik) ke `POST /asr` (`lang=id` & `lang=fil`), serta pemeriksaan integrasi Web Speech API (`webkitSpeechRecognition` & `speechSynthesis`) di [`web/js/speech.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/speech.js).
   - **Teks & Jembatan 3-Lapis ID–PH**: Pembentukan kalimat (`POST /sentence`) dan penerjemahan lintas bahasa Indonesia $\leftrightarrow$ Filipina (`POST /translate`) baik pada jalur normal (`L2`) maupun simulasi kegagalan jaringan (`force_l2_error=True` $\rightarrow$ fallback `L1`), serta evaluasi langsung pada 105 kalimat uji manusia disjoint ([`data/text/test_manual.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/test_manual.tsv)).

---

## 2. Bukti Pengujian Aktual

### 2.1 Verifikasi Volume & Persistensi PostgreSQL Lintas Restart Container

**Inspeksi Volume Docker (`docker volume inspect projek_1_pgdata`)**:
```json
[
  {
    "CreatedAt": "2026-11-07T11:16:38Z",
    "Driver": "local",
    "Labels": {
      "com.docker.compose.project": "projek_1",
      "com.docker.compose.volume": "pgdata"
    },
    "Mountpoint": "/var/lib/docker/volumes/projek_1_pgdata/_data",
    "Name": "projek_1_pgdata",
    "Scope": "local"
  }
]
```

**Bukti `POST /db/recordings` & `GET /db/recordings` (Sebelum & Sesudah `docker compose restart`)**:
```json
{
  "post_recording": {
    "status_code": 200,
    "body": {
      "status": "created",
      "id": 1,
      "recording_code": "SBK_FASE11_S01_HALO_001"
    }
  },
  "recordings_after_restart": {
    "db_connected": true,
    "count": 1,
    "items": [
      {
        "id": 1,
        "recording_code": "SBK_FASE11_S01_HALO_001",
        "signer_id": "FASE11_S01",
        "gloss": "HALO",
        "repetition": 1,
        "duration": 2.6,
        "file_path": "data/raw/selfrec/SBK_FASE11_S01_HALO_001.webm",
        "keypoint_path": "data/keypoints/selfrec/SBK_FASE11_S01_HALO_001.npz",
        "consent_status": "approved",
        "validation_status": "valid"
      }
    ]
  }
}
```

**Bukti `/db/status` Sesudah `docker compose restart` (Tidak Ada Duplikasi Seeding)**:
```json
{
  "db_connected": true,
  "active_backend": "postgresql",
  "database_url": "postgresql+psycopg2://signbridge:***@postgres:5432/signbridge_db",
  "tables": [
    "sign_concepts",
    "model_versions",
    "evaluation_runs",
    "inference_logs",
    "dataset_recordings"
  ],
  "counts": {
    "sign_concepts": 58,
    "model_versions": 20,
    "evaluation_runs": 3,
    "inference_logs": 9,
    "dataset_recordings": 1
  },
  "last_error": null
}
```

**Bukti Pencatatan `GET /db/logs` Lintas Keempat Endpoint Inferensi**:
- `id=2`: `endpoint="/predict"`, `modality="video"`, `room_code="ASEAN11"`, `input_summary="keypoints shape=[24, 86, 3]"`, `output_summary="top1=HALO"`, `confidence=0.0483`, `latency_ms=31.23`, `status="success"`
- `id=3`: `endpoint="/asr"`, `modality="audio"`, `input_summary="audio_bytes=48044 lang=id"`, `latency_ms=1.0`, `status="success"`
- `id=5`: `endpoint="/sentence"`, `modality="text"`, `room_code="ASEAN11"`, `input_summary="gloss=SAYA MAU TANYA GURU lang=id"`, `output_summary="Saya mau tanya guru."`, `status="success"`
- `id=8`: `endpoint="/translate"`, `modality="bridge"`, `room_code="ASEAN11"`, `input_summary="id->fil: Saya belajar di rumah."`, `status="fallback"`

### 2.2 Bukti Pengujian Aset Statis Frontend (`http://localhost:8080`)

| Path Aset | Status HTTP | Ukuran (Byte) | Content-Type |
| :--- | :---: | :---: | :--- |
| `/` (`web/index.html`) | `200 OK` | `13.527` | `text/html; charset=utf-8` |
| `/js/app.js` | `200 OK` | `33.873` | `application/javascript` |
| `/js/vision.js` | `200 OK` | `19.800` | `application/javascript` |
| `/js/recognizer.js` | `200 OK` | `16.923` | `application/javascript` |
| `/js/fingerspell.js` | `200 OK` | `8.523` | `application/javascript` |
| `/css/style.css` | `200 OK` | `5.142` | `text/css; charset=utf-8` |
| `/model/labels.json` | `200 OK` | `389` | `application/json` |
| `/model/fingerspell.json` | `200 OK` | `211` | `application/json` |
| `/model/student.onnx` | `200 OK` | `1.743.872` | `application/octet-stream` |
| `/model/fingerspell.onnx` | `200 OK` | `1.062.205` | `application/octet-stream` |

---

## 3. Hasil Fungsional Tiap Modalitas (Pemisahan Jujur: Data Nyata vs Sintetis/Fallback)

### 3.1 Modalitas 1 — Video (32 Kata BISINDO & FSL)
- **Pipeline Kamera & Prapemrosesan**:
  - Di browser ([`web/js/vision.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/vision.js)), `VisionManager` mengakses webcam via `navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })` dan mengekstrak 86 titik anatomis melalui `@mediapipe/holistic` (9 titik pose tubuh atas, 21 tangan kiri, 21 tangan kanan, 35 titik wajah).
  - Gerbang keamanan tangan aktif (`hasVisibleHand = Boolean(left21 || right21)`): saat pengguna tidak mengangkat tangan ke kamera, sistem menahan inferensi dan menampilkan HUD `"MENUNGGU TANGAN"` sehingga tidak memicu kata secara acak saat pengguna diam.
  - Prapemrosesan di [`signbridge/features.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/features.py) dan [`web/js/features.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/features.js) identik (`max_diff < 1e-5` pada 7 pengujian Node.js) dan menghasilkan tensor `[1, 64, 86, 3]` `float32`.
- **Pemisahan Prediksi ONNX vs Klasifikasi Fonologi Deterministik vs Rekaman Nyata**:
  - **Dataset Video pada Repositori**: Tidak terdapat rekaman kamera pengguna nyata (`.npz` / `.mp4`) yang disimpan di dalam repositori (`real_repo_npz_count = 0`). Fungsi `ensure_demo_dataset` membangkitkan sekuens *keypoint* sintetis untuk keperluan pengujian pipa kode.
  - **Perilaku Model ONNX (`student.onnx` & `student_int8.onnx`)**: File `web/model/student.onnx` (`1,66 MB`) dan `student_int8.onnx` (`0,44 MB`) diekspor dari arsitektur `StudentPoseTransformer` tanpa bobot hasil pelatihan video nyata (`ckpt_path=None`). Saat diuji pada 5 sampel `.npz` (`[24, 86, 3]` $\rightarrow$ `[1, 64, 86, 3]`) maupun via `POST /predict`, model ONNX berjalan mulus dengan latensi `31,23 ms` dan paritas FP32 vs INT8 `max_logit_diff = 0.0`, tetapi menghasilkan *confidence* seragam `0.0483`–`0.0804` (mendekati peluang acak $1/32 = 0.03125$).
  - **Perilaku Real-Time di Browser ([`web/js/recognizer.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recognizer.js))**: Karena logit ONNX memiliki *spread* rendah (`< 1.5`), pengenalan kamera langsung di browser secara otomatis menggunakan pencocokan fitur fonologi deterministik (`classifyByPhonology`: bentuk jari `0..7`, lokasi anatomis kepala/mulut/dada/perut, arah gerak, dan 1 vs 2 tangan sesuai [`data/phonology.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/phonology.csv)).
  - **Klaim Akurasi**: Kami **tidak mengklaim** akurasi pengenalan video BISINDO/FSL di dunia nyata dari angka tabel desain (`M0..M5`), karena bobot `student.onnx` saat ini belum dilatih pada korpus video BISINDO/FSL nyata.

### 3.2 Modalitas 2 — Citra / Fingerspelling Abjad A–Z
- **Pengujian Citra Tangan & Pemotongan (`crop_and_resize_hand`)**:
  - Diuji menggunakan citra RGB tangan `640x480` (`scratch/test_hand_photo.png`) beserta 21 titik *landmark* tangan.
  - Fungsi [`crop_and_resize_hand`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/crop.py#L48-L83) berhasil menghitung kotak potong persegi dengan margin +25% (`x0=100, y0=36, x1=482, y1=418, size=382`), mengubah ukuran ke `224x224x3` (`scratch/test_hand_cropped_224.png`), dan menormalisasi ke tensor ImageNet CHW `[1, 3, 224, 224]` (`min=-1.6384`, `max=1.855`).
- **Inferensi ONNX (`web/model/fingerspell.onnx`) & Evaluasi Jujur**:
  - Model `fingerspell.onnx` (`MobileNetV3-Small`, `0,266M` parameter, ukuran `1,01 MB`) menghasilkan prediksi 5 teratas: `A (0.0416)`, `O (0.0415)`, `D (0.0407)`, `J (0.0406)`, `P (0.0406)` dengan `logit_spread = 0.1327`.
  - Sesuai catatan evaluasi aktual di [`runs/image_i1_mobilenetv3/result.json`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3/result.json), akurasi uji model `I1` saat ini adalah **`test_acc = 0.0385` (`3,85%`)** dan **`macro_f1 = 0.0385`** dengan `latency_cpu_ms = 9.04 ms`, yang setara dengan tebakan acak pada 26 kelas ($1/26 = 3,846\%$).
  - Di sisi frontend ([`web/js/fingerspell.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/fingerspell.js)), pengenalan ejaan jari dari kamera menggunakan klasifikasi geometri 21 titik jari (`classifyHandshape21`) ketika tangan ditahan stabil selama 7 frame berturut-turut. Selain itu, antarmuka web saat ini belum menyediakan tombol `<input type="file">` khusus untuk mengunggah file foto tangan statis secara langsung dari halaman browser.

### 3.3 Modalitas 3 — Audio (Speech-to-Text & Text-to-Speech)
- **Web Speech API di Browser ([`web/js/speech.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/speech.js))**:
  - Menggunakan `window.SpeechRecognition || window.webkitSpeechRecognition` untuk pengenalan suara langsung di browser Chrome/Edge (`id-ID` dan `fil-PH`), serta `window.speechSynthesis` untuk pembacaan suara (TTS) otomatis.
  - Jika browser tidak mendukung Web Speech API, `SpeechManager` secara otomatis melakukan fallback ke simulasi transkripsi atau ke endpoint backend `POST /asr`.
- **Endpoint Backend `POST /asr` ([`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py#L239-L281))**:
  - Diuji dengan file audio WAV PCM 16kHz 16-bit mono nyata (`scratch/test_audio_16k.wav`, `48.044` byte).
  - Validasi batas ukuran (`HTTP 400` untuk file kosong, `HTTP 413` untuk file `> 10 MB`) dan pencatatan ke PostgreSQL `inference_logs` berfungsi penuh.
  - **Status Implementasi Aktual**: Endpoint `POST /asr` di [`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py#L254-L281) saat ini memeriksa ukuran byte file audio dan mengembalikan kalimat respons deterministik (*fallback/mock response*: `"Halo teman-teman, mari kita belajar membaca buku di kelas."` untuk `id` dan `"Kumusta po guro, gusto ko pong magtanong sa klase."` untuk `fil`), **bukan** menjalankan dekode akustik model Whisper (`faster-whisper` / `openai-whisper`) terhadap gelombang suara di dalam file `.wav`.

### 3.4 Modalitas 4 — Teks & Jembatan Komunikasi 3-Lapis (BISINDO $\leftrightarrow$ FSL)
- **Pembentukan Kalimat (`POST /sentence` / `gloss_to_sentence_rules`)**:
  - Mengubah deret gloss menjadi kalimat bahasa Indonesia (`id`) maupun Filipina (`fil`) secara deterministik menggunakan aturan morfosintaksis (`B0-RuleBased` di [`signbridge/text/pseudo_gloss.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/text/pseudo_gloss.py)).
  - Contoh hasil live container: `["SAYA", "MAU", "TANYA", "GURU"]` $\rightarrow$ `"Saya mau tanya guru."` (`lang="id"`) dan `"Ako ay gustong magtanong sa guro."` (`lang="fil"`).
  - Evaluasi aktual `B0-RuleBased` pada **105 pasangan uji manusia disjoint** ([`data/text/test_manual.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/test_manual.tsv)): **`BLEU = 3.21`**, **`chrF = 57.50`**. (Skor BLEU 4-gram rendah karena kalimat referensi manusia di `test_manual.tsv` menggunakan ekspansi sopan santun panjang seperti *"Halo Bapak dan Ibu Guru."* untuk gloss `HALO GURU`, sedangkan `B0` menghasilkan *"Halo guru."*; kemiripan karakter `chrF = 57.50` mengonfirmasi kecocokan leksikal inti).
- **Penerjemahan Jembatan 3-Lapis (`POST /translate` / [`signbridge/bridge.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/bridge.py))**:
  - **Lapis 1 (`L1` Konsep Kamus Offline)**: Menerjemahkan kata demi kata dan memetakan konsep ke berkas referensi animasi (`web/model/refs/<concept_id>_fsl.json` / `_bisindo.json`).
  - **Lapis 2 (`L2` Kalimat)**: Menggunakan tabel frasa bilingual kelas (`phrase_map_id_to_fil` / `phrase_map_fil_to_id`) dengan fallback otomatis ke `L1` untuk kalimat di luar daftar frasa atau ketika `force_l2_error=True`. Model saraf NLLB-200 / M2M100 tidak dimuat secara lokal di container untuk menjaga ukuran image tetap ringan.
  - **Lapis 3 (`L3` Animasi Isyarat Referensi)**: Mengembalikan path referensi animasi (`ref_animations`), dan di sisi browser ([`web/js/vision.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/vision.js#L377-L487)) fungsi `generateReferenceSignKeypoints` merender animasi kerangka 86 titik secara prosedural berdasarkan parameter fonologi di [`data/phonology.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/phonology.csv).

---

## 4. Ringkasan Metrik Aktual vs Metrik Referensi Desain

| Modalitas | Komponen / Model | Sumber Pengukuran Aktual | Metrik Aktual Terverifikasi | Status Kejujuran Engineering |
| :--- | :--- | :--- | :--- | :--- |
| **Video** | `student.onnx` (FP32) vs `student_int8.onnx` (INT8) | Uji paritas ONNX (`export_onnx.py` & 5 sampel `.npz`) | `max_diff = 0.0000`, ukuran FP32 `1,66 MB`, INT8 `0,44 MB`, latensi API `31,23 ms`, top-1 conf `~0.048–0.080` | Model ONNX valid secara struktural, namun bobot belum dilatih pada video nyata (masih bobot inisialisasi). |
| **Citra (A–Z)** | `I1` MobileNetV3-Small (`fingerspell.onnx`) | [`runs/image_i1_mobilenetv3/result.json`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3/result.json) & uji PNG `640x480` | `test_acc = 3.85%` (`0.0385`), `macro_f1 = 0.0385`, `latency_cpu = 9.04 ms`, top-1 conf `0.0416` | Akurasi aktual setara peluang acak $1/26$ (`3,85%`); perlu pelatihan ulang pada dataset foto tangan A–Z nyata. |
| **Audio (ASR)** | Endpoint `POST /asr` | Uji unggah WAV PCM 16kHz (`48.044` byte) ke container Docker | Latensi HTTP `~1,0 ms`, `rtf = 0.0004` (respons statis/fallback) | `POST /asr` di server masih menggunakan respons teks deterministik, belum memanggil model Whisper asli. |
| **Teks (Gloss$\rightarrow$Kalimat)** | `B0-RuleBased` (`gloss_to_sentence_rules`) | Evaluasi langsung pada 105 kalimat [`data/text/test_manual.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/test_manual.tsv) | `BLEU = 3.21`, `chrF = 57.50`, latensi API `0,05–0,12 ms` | Berfungsi nyata secara deterministik (`id` & `fil`); model saraf `T1`/`T2` tersedia di modul latih tetapi belum diaktifkan di endpoint runtime. |
| **Database** | PostgreSQL 16 (`signbridge-postgres`) | Uji CRUD + `docker compose restart` | `5` tabel aktif, `58` konsep, `20` model, `3` evaluasi, `1` rekaman & `9` log bertahan lintas *restart* | **100% Berfungsi Nyata & Persisten** pada volume `projek_1_pgdata`. |

---

## 5. Temuan Bug & Perbaikan yang Telah Diterapkan pada FASE 11

Selama audit fungsional FASE 11, ditemukan **3 bug fungsional nyata** dan ketiganya telah diperbaiki secara terarah tanpa mengubah kontrak API maupun skema database:

1. **Bug 1 — Label Model `B0+T2-Hybrid` Tidak Sesuai Implementasi Aktual di `POST /sentence` ([`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py#L310-L315))**:
   - *Temuan*: Endpoint `POST /sentence` hanya memanggil fungsi aturan deterministik `gloss_to_sentence_rules` (dan mencatat `model_code="B0"` ke tabel `inference_logs`), tetapi mengembalikan `"model": "B0+T2-Hybrid"` pada respons JSON.
   - *Perbaikan*: Diubah menjadi `"model": "B0-RuleBased"` agar selaras 100% dengan implementasi aktual dan pencatatan database.
2. **Bug 2 — Kamus L1 Bridge Kehilangan 20 Kosakata Isyarat Dasar Saat `concepts.csv` Dimuat ([`signbridge/bridge.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/bridge.py#L92-L105))**:
   - *Temuan*: Ketika `BridgeModule` memuat 32 konsep kelas dari `data/bridge/concepts.csv` (`C01..C32`), kamus pencarian `_by_id_word` dan `_by_fil_word` tidak menyertakan kosakata dasar di `DEFAULT_CONCEPTS_ROWS` (seperti `rumah` $\leftrightarrow$ `bahay`, `ibu` $\leftrightarrow$ `nanay`, `pagi` $\leftrightarrow$ `umaga`, `makan` $\leftrightarrow$ `kain`). Akibatnya, kalimat `"Saya belajar di rumah."` pada mode fallback `L1` menghasilkan `"Ako Mag-aral di rumah."` (kata `rumah` gagal diterjemahkan).
   - *Perbaikan*: Menginisialisasi kamus pencarian L1 dengan `DEFAULT_CONCEPTS_ROWS` terlebih dahulu sebelum menimpanya dengan `self.concepts` dari `concepts.csv`, tanpa mengubah `len(self.concepts) == 32`. Setelah perbaikan, `"Saya belajar di rumah."` pada fallback `L1` berhasil menerjemahkan `rumah` menjadi `bahay` (`concepts: ["C05", "C15", "HOUSE"]`).
3. **Bug 3 — Ketidakcocokan Properti `clip.clip_id` vs `clip.clipId` & Buffer Kamera pada Studio Rekam Dataset ([`web/js/app.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L753-L768))**:
   - *Temuan*: `MultimodalRecorder.addClip()` di [`web/js/recorder.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L126) mengembalikan objek dengan properti camelCase `clipId`, sedangkan [`web/js/app.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L762) membaca `clip?.clip_id` (selalu `undefined`). Selain itu, tombol simpan klip selalu membangkitkan *keypoint* sintetis meskipun kamera sedang aktif merekam buffer.
   - *Perbaikan*: Menggunakan buffer *keypoint* kamera nyata (`this.recognizer.buffer.slice(-64)`) apabila kamera sedang berjalan, serta membaca `clip?.clipId || clip?.clip_id` agar `recording_code` yang dikirim ke PostgreSQL (`POST /db/recordings`) konsisten dengan `clip_id` di dalam manifes `.zip`.

---

## 6. Fitur yang Belum Selesai / Keterbatasan Aktual Saat Ini

1. **Bobot Model Video (`student.onnx`) & Citra (`fingerspell.onnx`) Belum Dilatih pada Dataset Dunia Nyata**:
   - `student.onnx` masih menggunakan bobot inisialisasi (`ckpt_path=None`), dan `fingerspell.onnx` (`runs/image_i1_mobilenetv3`) baru mencapai akurasi uji `3,85%` (setara peluang acak $1/26$). Pengenalan langsung di browser saat ini ditopang oleh aturan geometri/fonologi deterministik (`classifyByPhonology` & `classifyHandshape21`).
2. **Backend `POST /asr` Masih Menggunakan Respons Fallback Deterministik**:
   - Meskipun Web Speech API di browser (`webkitSpeechRecognition`) dapat menangkap suara pengguna secara nyata di Chrome/Edge, endpoint server `POST /asr` belum terhubung ke mesin inferensi Whisper (`faster-whisper` / `openai-whisper` / ONNX Whisper) dan masih mengembalikan teks contoh statis berdasarkan parameter bahasa.
3. **Model Terjemahan Kalimat L2 (`BridgeModule.translate_text`) Berbasis Tabel Frasa + Fallback L1**:
   - Penerjemahan kalimat penuh di `L2` mengandalkan kamus frasa kelas bilingual (`phrase_map_id_to_fil`) dan *token-by-token* `L1` fallback, belum menjalankan model NMT (seperti NLLB-200 / M2M100) atau Seq2Seq `T1`/`T2` pada waktu jalan (*runtime*).
4. **Antarmuka Unggah File Gambar Tangan Statis di Halaman Web**:
   - Pipeline pemotongan tangan (`cropAndResizeHand`) dan inferensi `fingerspell.onnx` sudah tersedia di [`web/js/fingerspell.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/fingerspell.js), tetapi halaman [`web/index.html`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html) belum memiliki kontrol `<input type="file" accept="image/*">` untuk mengunggah foto tangan dari file lokal.

---

## 7. Rekomendasi Prioritas Berikutnya

1. **Prioritas 1 — Integrasi Whisper Ringan (`faster-whisper` / `whisper-tiny` INT8) pada Endpoint `POST /asr`**:
   - Mengganti respons statis di [`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py#L254-L281) dengan pemanggilan model `faster-whisper` (`tiny` atau `base` CPU INT8) dengan fallback otomatis ke respons aman jika model belum terunduh, sehingga unggahan file `.wav` dari klien menghasilkan transkripsi akustik nyata.
2. **Prioritas 2 — Pelatihan & Ekspor Ulang Bobot `fingerspell.onnx` dan `student.onnx` dari Dataset Nyata**:
   - Melatih `MobileNetV3-Small` (`I1`) pada dataset citra jari A–Z BISINDO/ASL nyata hingga melampaui akurasi $>85\%$ dan mengekspor ulang `web/model/fingerspell.onnx`.
   - Mengumpulkan rekaman *keypoint* 86 titik melalui tab **Rekam Dataset Mandiri** (yang kini telah terhubung ke PostgreSQL `dataset_recordings` dan ekspor `.zip`), melatih `StudentPoseTransformer` (`M5`), dan mengekspor ulang `web/model/student.onnx`.
3. **Prioritas 3 — Penambahan Tombol Unggah Foto Tangan (`<input type="file">`) pada UI Frontend**:
   - Menambahkan tombol unggah gambar pendamping kamera di [`web/index.html`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html) agar pengguna dapat menguji inferensi `fingerspell.onnx` menggunakan file foto tangan statis langsung dari antarmuka web.

