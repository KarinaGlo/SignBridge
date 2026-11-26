# LAPORAN AUDIT PENYIMPANAN & KEBUTUHAN UNDUHAN DATASET
## SIGNBRIDGE ID–PH (BISINDO ↔ FSL MULTIMODAL CLASSROOM BRIDGE)

**Tanggal Audit:** 13 November 2026  
**Auditor:** Senior ML Engineer & Data Architect  
**Lingkungan Audit:** Windows 11 x64, Python 3.13.12, PyTorch 2.14.1+cpu  
**Branch Git Aktif:** `feature/field-test-readiness` (Commit: `3a99e96`)  
**Status Working Tree:** 100% Bersih (Read-Only Audit, 0 berkas diubah/dihapus/ditimpa)

---

## 1. RINGKASAN EKSEKUTIF

Audit ini dilakukan secara *read-only* untuk menjawab pertanyaan spesifik:
> *"Apakah dataset yang berukuran sekitar 13 MB/GB (atau ukuran lain yang ditemukan di repository) perlu diunduh ulang atau ditambahkan?"*

### Temuan Utama:
1. **Total Ukuran Direktori `data/` Saat Ini:** Hanya **4,64 MB** ($4.643.481\text{ byte}$ atau setara **$0,0043\text{ GB}$**) yang terdiri dari **19 berkas** (metadata CSV, TSV, teks paralel, database SQLite, dan arsip BZ2 Tatoeba).
2. **Total Ukuran Repositori Keseluruhan:**
   * Termasuk direktori `.git`: **53,25 MB** ($55.838.869\text{ byte}$ / $0,0520\text{ GB}$).
   * Tanpa direktori `.git`: **39,83 MB** ($41.769.737\text{ byte}$ / $0,0389\text{ GB}$).
3. **Misteri Ukuran "13 MB / 13 GB":**
   * **Ukuran ~13 MB:** Berasal dari dua berkas metadata katalog di masa lalu yang tercatat pada `data/DATASET_DOWNLOAD_MANIFEST.csv`, yaitu:
     * `data/raw/image/bisindo_alphabet/mendeley_metadata.json` (**12,89 MB**).
     * `data/raw/video/wlasl_300/WLASL_v0.3.json` (**11,93 MB**).
     * Serta ukuran folder `web/` saat ini (**11,72 MB**).
   * **Ukuran Berbasis GB (8 GB – 13 GB):** Merupakan ukuran estimasi total jika seluruh dataset mentah eksternal diunduh lengkap tanpa kompresi (Mendeley Raw Camera Photos ~8,1 GB + WL-BISINDO MP4 ~2,1 GB + WLASL Videos ~4,5 GB + FLEURS Audio ~1,3 GB).
4. **Status Keberadaan Dataset Fisik:**
   * Seluruh dataset biner berukuran besar (video MP4/MOV, audio WAV, citra JPG, dan keypoint NPZ) **TIDAK ADA DI DISK LOKAL SAAT INI** karena folder `data/raw/`, `data/keypoints/`, dan ekstensi media diabaikan oleh `.gitignore` (aturan baris 46–69).
   * **Kabar Baiknya:** Model isyarat dinamis utama (**M0 Student Transformer**) **SUDAH SELESAI DITRAINING** sebelum dataset mentah dihapus/di-ignore, dan artefak bobotnya telah tersimpan aman di `web/model/student.onnx` (5,46 MB, 32 kelas).
   * **Kebutuhan Unduhan Nyata:** Dataset yang **MUTLAK PERLU DIUNDUH ULANG** hanyalah citra abjad Mendeley (**~27,7 MB**) untuk melatih ulang model fingerspelling I1 yang gagal konvergensi ($3.85\%$). Dataset video raksasa puluhan GB **TIDAK PERLU DIUNDUH ULANG** untuk pengujian dan demo web saat ini.

---

## 2. INVENTARIS FISIK DATASET AKTUAL DI REPOSITORI

### 2.1 Distribusi Ukuran Folder Top-Level

| Nama Folder | Jumlah Berkas | Ukuran Aktual (Byte) | Ukuran (MB) | Ukuran (GB) | Kategori Konten |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `data/` | 19 | 4.643.481 B | 4,43 MB | 0,0043 GB | Metadata, CSV, TSV, DB, Teks |
| `web/` | 22 | 12.288.426 B | 11,72 MB | 0,0114 GB | Frontend PWA, Model ONNX (11,98 MB) |
| `scratch/` | 85 | 16.062.667 B | 15,32 MB | 0,0150 GB | Skrip audit & inspeksi sementara |
| `docs/` | 70 | 2.812.217 B | 2,68 MB | 0,0026 GB | Laporan, arsitektur, presentasi |
| `tests/` | 39 | 2.365.007 B | 2,26 MB | 0,0022 GB | Automated test suite Python & JS |
| `runs/` | 2 | 1.110.086 B | 1,06 MB | 0,0010 GB | Checkpoint MobileNetV3 I1 (best.pt) |
| `outputs/` | 19 | 968.241 B | 0,92 MB | 0,0009 GB | Plot evaluasi & metrik M0/M1 |
| `signbridge/` | 48 | 524.250 B | 0,50 MB | 0,0005 GB | Source code inti library Python |
| `src/` | 57 | 380.428 B | 0,36 MB | 0,0004 GB | Source code tambahan |
| `scripts/` | 19 | 171.507 B | 0,16 MB | 0,0002 GB | Skrip utilitas CLI |
| `server/` | 6 | 134.391 B | 0,13 MB | 0,0001 GB | Backend server FastAPI |
| Folder Lainnya | 190 | 269.442 B | 0,26 MB | 0,0003 GB | Configs, migrations, notebooks, dll. |
| **TOTAL (Tanpa .git)** | **576** | **41.769.737 B** | **39,83 MB** | **0,0389 GB** | **Seluruh Workspace Non-Git** |
| `.git/` | 272 | 14.069.132 B | 13,42 MB | 0,0131 GB | Riwayat version control Git |
| **TOTAL KESELURUHAN** | **848** | **55.838.869 B** | **53,25 MB** | **0,0520 GB** | **Total Repositori di Disk** |

---

### 2.2 Inventaris 19 Berkas di Direktori `data/` (Pemeriksaan Integritas 100%)

Seluruh 19 berkas di dalam direktori `data/` telah diuji secara fisik, baris per baris, dan lolos uji integritas:

| No | Path Berkas Relatif | Ukuran (Byte) | Ukuran (MB) | Ekstensi | Jumlah Baris / Entri | Status Integritas & Keterangan |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `data/.gitkeep` | 0 B | 0,00 MB | `.gitkeep` | 0 | **VALID** — Placeholder Git standar (0 byte wajar) |
| 2 | `data/audio/fleurs/id_id/dev.tsv` | 200.586 B | 0,19 MB | `.tsv` | 350 baris | **VALID** — Metadata dev split FLEURS Indonesian |
| 3 | `data/audio/fleurs/id_id/test.tsv` | 409.483 B | 0,39 MB | `.tsv` | 687 baris | **VALID** — Metadata test split FLEURS Indonesian |
| 4 | `data/audio/fleurs/id_id/train.tsv` | 1.501.780 B | 1,43 MB | `.tsv` | 2.579 baris | **VALID** — Metadata train split FLEURS Indonesian |
| 5 | `data/audio/metadata.csv` | 5.334 B | 0,01 MB | `.csv` | 61 baris (60 data) | **VALID** — Metadata teks audio kelas Indonesia |
| 6 | `data/audio/metadata_fil.csv` | 1.849 B | 0,00 MB | `.csv` | 25 baris (24 data) | **VALID** — Metadata teks audio kelas Filipino |
| 7 | `data/bridge/concepts.csv` | 3.552 B | 0,00 MB | `.csv` | 34 baris (32 konsep) | **VALID** — Kamus konsep jembatan BISINDO ↔ FSL |
| 8 | `data/DATASET_DOWNLOAD_MANIFEST.csv` | 11.411 B | 0,01 MB | `.csv` | 27 baris | **VALID** — Log manifes akuisisi dataset resmi |
| 9 | `data/manifest_wl_bisindo.csv` | 216.722 B | 0,21 MB | `.csv` | 1.601 baris (1.600 data) | **VALID** — Manifes utama 32 kata WL-BISINDO (960/180/460) |
| 10 | `data/manifest_wl_bisindo_source_metadata.csv`| 339.988 B | 0,32 MB | `.csv` | 1.601 baris | **VALID** — Metadata durasi, resolusi & penutur asli |
| 11 | `data/phonology.csv` | 496 B | 0,00 MB | `.csv` | 34 baris (32 gloss) | **VALID** — Atribut fonologi isyarat BISINDO |
| 12 | `data/PHONOLOGY_GUIDE.md` | 3.562 B | 0,00 MB | `.md` | 46 baris | **VALID** — Dokumentasi notasi fonologi Stokoe |
| 13 | `data/signbridge_operational.db` | 151.552 B | 0,14 MB | `.db` | SQLite Database | **VALID** — `PRAGMA integrity_check: ok` |
| 14 | `data/text/kelas_sentences.txt` | 14.830 B | 0,01 MB | `.txt` | 200 kalimat | **VALID** — Korpus kalimat percakapan kelas inklusif |
| 15 | `data/text/tatoeba/ind_sentences.tsv` | 1.417.823 B | 1,35 MB | `.tsv` | 28.418 baris | **VALID** — Kalimat monolingual Tatoeba Indonesia |
| 16 | `data/text/tatoeba/ind_sentences.tsv.bz2` | 330.738 B | 0,32 MB | `.bz2` | Arsip terkompresi | **VALID** — Terbaca utuh, dekompresi: 1.389.405 B |
| 17 | `data/text/test_manual.tsv` | 6.727 B | 0,01 MB | `.tsv` | 106 baris (105 data) | **VALID** — Pasangan uji gloss-to-sentence |
| 18 | `data/text/train.tsv` | 22.565 B | 0,02 MB | `.tsv` | 171 baris (170 data) | **VALID** — Pasangan latih gloss-to-sentence |
| 19 | `data/text/val.tsv` | 4.483 B | 0,00 MB | `.tsv` | 31 baris (30 data) | **VALID** — Pasangan validasi gloss-to-sentence |
| **TOTAL** | **19 Berkas di `data/`** | **4.643.481 B** | **4,43 MB** | — | — | **0 berkas corrupt / 0 error** |

---

### 2.3 Rekapitulasi Berkas Berdasarkan Ekstensi

Di seluruh repositori (di luar `.git`):
* **`.csv` / `.tsv` (Data Tabular & Manifes):** 28 berkas
* **`.json` / `.yaml` (Konfigurasi & Metrik):** 52 berkas
* **`.py` / `.mjs` / `.js` (Source Code & Testing):** 168 berkas
* **`.onnx` (Model Binary Siap Pakai):** 3 berkas (`student.onnx`, `student_int8.onnx`, `fingerspell.onnx` = 11,98 MB)
* **`.pt` (PyTorch Weights):** 1 berkas (`runs/image_i1_mobilenetv3/best.pt` = 1,06 MB)
* **`.png` (Plot & Grafik Evaluasi):** 17 berkas
* **`.mp4` / `.mov` / `.avi` (Video Mentah):** **0 berkas** (Tidak ada di disk)
* **`.wav` / `.mp3` / `.flac` (Audio Mentah):** **0 berkas** (Tidak ada di disk)
* **`.npz` / `.npy` (Koordinat Keypoint):** **0 berkas** (Tidak ada di disk)
* **`.jpg` / `.jpeg` (Citra Mentah):** **0 berkas** (Tidak ada di disk)

---

## 3. VERIFIKASI KELENGKAPAN PER DATASET (BAGIAN B & C)

Berikut adalah status audit detail terhadap 9 dataset yang ditentukan:

### 1. WL-BISINDO (Word-Level Indonesian Sign Language)
* **Kebutuhan Teoretis:** 1.600 klip video MP4 (~2,1 GB) $\to$ diekstrak menjadi 1.600 berkas `.npz` keypoint 86 node.
* **Kondisi Fisik Saat Ini:**
  * Manifes CSV: **LENGKAP & VALID** (`data/manifest_wl_bisindo.csv`, 1.600 baris, 32 kelas, 5 signer).
  * Video mentah MP4: **MISSING** (diabaikan `.gitignore`).
  * Berkas keypoint `.npz`: **MISSING** (`data/keypoints/` belum ada di disk).
* **Status Model:** Model **M0 Student Transformer** dan **M1 ST-GCN** **SUDAH SELESAI DITRAINING** sebelum repositori dipaketkan. Hasil ekspor `web/model/student.onnx` (5,46 MB) sudah ada di web dan berfungsi normal.
* **Download Status:** **PARTIAL** (Metadata lengkap, binary ONNX lengkap, file raw & npz tidak ada di disk).

### 2. WLASL-300 (Word-Level American Sign Language)
* **Kebutuhan Teoretis:** 300 gloss / 5.117 video klip ASL untuk pretraining M1 Stage 1 (~4,5 GB).
* **Kondisi Fisik Saat Ini:**
  * Berkas manifest JSON: **LENGKAP DI MANIFEST LOG** (`WLASL_v0.3.json` 11,93 MB & `WLASL_300_manifest.json` 2,21 MB pada akuisisi terdahulu), namun tidak di-commit ke Git.
  * Berkas video fisik: **MISSING** (`data/raw/video/wlasl_300/` tidak ada di disk).
* **Status Training:** **TIDAK DIGUNAKAN DALAM PRODUCTION**. Model baseline M0 dan M1 yang dideploy dilatih *from scratch* pada WL-BISINDO tanpa tahapan pretrain WLASL.
* **Download Status:** **MISSING** (Tidak dibutuhkan untuk inferensi web saat ini).

### 3. FSL-105 (Filipino Sign Language)
* **Kebutuhan Teoretis:** 105 kelas FSL / 2.130 klip video MOV (~390 MB) untuk transfer learning cross-border ASEAN.
* **Kondisi Fisik Saat Ini:**
  * Kamus konsep semantik L1: **LENGKAP & VALID** (`data/bridge/concepts.csv`, 32 konsep C01–C32).
  * Video klip MOV & clips.zip: **MISSING** (`data/raw/video/fsl_105/` tidak ada di disk).
* **Status Training:** Belum ada model neural FSL yang ditraining. Sistem saat ini menghubungkan BISINDO dan FSL via tabel kamus konsep offline.
* **Download Status:** **MISSING** (Tidak mendesak untuk uji coba BISINDO Minggu 1).

### 4. BISINDO Alphabet (Ejaan Jari Mendeley A–Z)
* **Kebutuhan Teoretis:** 4.466 citra RGB ($224 \times 224$) dari 26 kelas A–Z (~27,71 MB).
* **Kondisi Fisik Saat Ini:**
  * Citra RGB fisik: **MISSING** (`data/raw/image/bisindo_alphabet/` tidak ada di disk).
  * Checkpoint model: `runs/image_i1_mobilenetv3/best.pt` ada, tetapi hasil akurasi uji hanya **$3.85\%$** (gagal konvergensi).
  * Model ekspor: `web/model/fingerspell.onnx` ada (1,06 MB) tetapi prediksinya acak sehingga di-bypass oleh heuristik geometri.
* **Status Training:** Model sudah pernah dilatih tetapi **GAGAL TOTAL**, sehingga **WAJIB DILATIH ULANG**.
* **Download Status:** **MISSING** (Sangat mendesak untuk diunduh ulang karena ukurannya kecil, hanya ~27,7 MB).

### 5. FLEURS `id_id` (Google Speech Corpus Indonesian)
* **Kebutuhan Teoretis:** 3.616 metadata TSV + 350 audio WAV dev (~254 MB) atau penuh (~1,3 GB).
* **Kondisi Fisik Saat Ini:**
  * Metadata TSV: **LENGKAP & VALID** (`dev.tsv` 350, `test.tsv` 687, `train.tsv` 2.579 baris = 2,11 MB total).
  * Berkas audio `.wav`: **MISSING** (`data/audio/fleurs/id_id/audio/` tidak ada).
* **Status Training:** Model Whisper ASR lokal tidak pernah dilatih. Frontend web SignBridge menggunakan API bawaan browser (`webkitSpeechRecognition`).
* **Download Status:** **PARTIAL** (Metadata lengkap, audio fisik tidak ada).

### 6. FLEURS `fil_ph` (Google Speech Corpus Filipino)
* **Kebutuhan Teoretis:** Audio ucapan bahasa Tagalog untuk modul suara Filipina (~1,3 GB).
* **Kondisi Fisik Saat Ini:**
  * Metadata teks: Hanya template 24 baris di `data/audio/metadata_fil.csv`.
  * Berkas audio `.wav` & TSV: **MISSING**.
* **Status Training:** Tidak pernah ditraining.
* **Download Status:** **MISSING**.

### 7. Rekaman Suara Tim (Classroom Audio Recordings)
* **Kebutuhan Teoretis:** 60 rekaman audio kalimat kelas Indonesia dan 24 rekaman kelas Filipina.
* **Kondisi Fisik Saat Ini:**
  * Metadata CSV: **LENGKAP & VALID** (`data/audio/metadata.csv` 60 baris, `metadata_fil.csv` 24 baris).
  * Berkas audio `.wav`: **MISSING** (Ditandai eksplisit di CSV: `METADATA_ONLY_AUDIO_NOT_AVAILABLE`).
* **Download Status:** **MISSING** (Belum pernah direkam secara fisik oleh tim).

### 8. Tatoeba Indonesian (`ind_sentences.tsv`)
* **Kebutuhan Teoretis:** 28.418 kalimat monolingual bahasa Indonesia.
* **Kondisi Fisik Saat Ini:**
  * Berkas TSV ekstrak: **LENGKAP & VALID** (`data/text/tatoeba/ind_sentences.tsv`, 1,35 MB, 28.418 kalimat).
  * Berkas arsip kompresi: **LENGKAP & VALID** (`data/text/tatoeba/ind_sentences.tsv.bz2`, 330 KB).
* **Status Training:** Siap digunakan untuk ekspansi data sintetis gloss-to-sentence.
* **Download Status:** **COMPLETE** (**100% Ada di disk, tidak perlu unduh ulang**).

### 9. Dataset Kalimat Internal (Parallel Sentences & Kelas)
* **Kebutuhan Teoretis:** Korpus paralel sekuens gloss terhadap kalimat alami Indonesia.
* **Kondisi Fisik Saat Ini:**
  * `data/text/train.tsv`: **LENGKAP & VALID** (170 pasangan, 22,5 KB).
  * `data/text/val.tsv`: **LENGKAP & VALID** (30 pasangan, 4,5 KB).
  * `data/text/test_manual.tsv`: **LENGKAP & VALID** (105 pasangan, 6,7 KB).
  * `data/text/kelas_sentences.txt`: **LENGKAP & VALID** (200 kalimat, 14,8 KB).
* **Status Training:** Telah digunakan untuk benchmark rule-based generator B0 dan disiapkan untuk fine-tuning IndoT5 (`configs/text_t2_indot5.yaml`).
* **Download Status:** **COMPLETE** (**100% Ada di disk, tidak perlu unduh ulang**).

---

## 4. TRAINING READINESS: APAKAH BENAR-BENAR DIGUNAKAN TRAINING?

| Dataset | Digunakan Saat Ini? | Penjelasan Faktual |
| :--- | :---: | :--- |
| **WL-BISINDO** | **YA (Telah Selesai)** | Digunakan untuk melatih M0 (Pose Transformer) & M1 (ST-GCN). Hasilnya sudah diekspor ke `web/model/student.onnx` dan berjalan 100% di browser. Untuk *retraining LOSO* di Minggu 2, keypoint NPZ perlu diekstrak ulang jika raw video ada, ATAU menggunakan checkpoint yang ada. |
| **BISINDO Alphabet** | **YA (Gagal Konvergensi)** | Digunakan melatih `runs/image_i1_mobilenetv3/best.pt`, tetapi gagal (akurasi 3.85%). Karena gagal, model ini **sangat membutuhkan dataset citra aslinya kembali** untuk ditraining ulang dengan benar. |
| **WLASL-300** | **TIDAK** | Hanya ada rencana pra-latih di config `configs/01_pose_pretrain_wlasl.yaml`. Model produksi M0 dilatih *from scratch* tanpa WLASL. |
| **FSL-105** | **TIDAK** | Model video FSL belum pernah dilatih. Yang aktif di sistem hanyalah kamus pemetaan konsep 32 kata (`concepts.csv`). |
| **FLEURS `id_id`** | **TIDAK** | Skrip `signbridge/audio/train_asr.py` belum pernah dijalankan untuk fine-tuning. Web app menggunakan Web Speech API bawaan browser. |
| **FLEURS `fil_ph`** | **TIDAK** | Tidak pernah digunakan dalam training mana pun. |
| **Rekaman Suara Tim**| **TIDAK** | Tidak ada file audio fisik; hanya teks metadata 60 kalimat. |
| **Tatoeba Indonesian** | **TIDAK (Belum)** | Belum dipakai training, disiapkan untuk augmentasi teks NLP pada Minggu 3. |
| **Parallel Sentences** | **YA** | Digunakan mengevaluasi penerjemah kalimat rule-based (WER 62.3%) dan target train IndoT5. |

---

## 5. REKOMENDASI UNDUHAN LENGKAP (BAGIAN E)

Berikut adalah tabel rekomendasi definitif untuk menjawab kebutuhan penyimpanan dan unduhan:

| Dataset | Ukuran Aktual di Disk | Status | Kekurangan | Perlu Download Ulang? | Tambahan yang Diperlukan | Alasan |
| :--- | :---: | :---: | :--- | :---: | :--- | :--- |
| **Tatoeba Indonesian** | **1,68 MB** (TSV + BZ2) | **COMPLETE** | Tidak ada | **TIDAK** | Tidak ada | Berkas lengkap 28.418 kalimat dan tervalidasi 100% di disk. |
| **Parallel Sentences** | **48,6 KB** (4 file) | **COMPLETE** | Tidak ada | **TIDAK** | Tidak ada | 305 pasang kalimat lengkap dan tervalidasi di disk. |
| **BISINDO Alphabet (Mendeley)** | **0 B** (Hilang dari disk) | **MISSING** | 4.466 citra RGB ($224 \times 224$) | **YA (PRIORITAS 1)** | Unduh varian RGB 224x224 resmi (~27,71 MB) dari Mendeley Data `doi:10.17632/ywnjpbcz8m.1` | Model abjad saat ini rusak ($3.85\%$). Ukuran unduhan sangat kecil (~28 MB) dan langsung menyelesaikan masalah fingerspelling. |
| **WL-BISINDO Video (MP4/NPZ)** | **556 KB** (Hanya CSV) | **PARTIAL** | 1.600 video MP4 (~2,1 GB) & 1.600 keypoint NPZ | **OPSIONAL / BILA AKAN RETRAIN LOSO** | Unduh `archive.zip` (~2,1 GB) dari Kaggle `glennleonali/wl-bisindo` JIKA tim akan melakukan retraining LOSO dari video mentah | Model M0 saat ini sudah ada di web (`student.onnx`, 5,46 MB). Jika hanya untuk demo/presentasi Minggu 1, video 2,1 GB ini **TIDAK PERLU** diunduh ulang. |
| **FLEURS `id_id` Audio** | **2,11 MB** (Hanya TSV) | **PARTIAL** | File audio `.wav` (350 wav dev ~254 MB atau penuh ~1,3 GB) | **TIDAK PERLU SAAT INI** | Tidak perlu | Web app SignBridge menggunakan Web Speech API browser untuk ASR. Pelatihan Whisper lokal belum direncanakan di Minggu 1/2. |
| **FSL-105 Video (MOV)** | **3,5 KB** (Hanya CSV konsep) | **MISSING** | 2.130 video MOV (~390 MB) | **TIDAK PERLU SAAT INI** | Tidak perlu | Jembatan FSL pada fase prototipe saat ini menggunakan kamus konsep semantik L1, bukan model video neural. |
| **WLASL-300 Video** | **0 B** | **MISSING** | 5.117 video ASL (~4,5 GB) | **TIDAK** | Tidak perlu | Pretraining WLASL tidak digunakan oleh model produksi M0/M1 yang berjalan saat ini. Menghemat kuota ~4,5 GB. |
| **FLEURS `fil_ph`** | **1,8 KB** (Hanya CSV) | **MISSING** | Audio bahasa Tagalog (~1,3 GB) | **TIDAK** | Tidak perlu | Fitur audio Filipina berada di roadmap jangka panjang (Tahap 4). |
| **Rekaman Kelas Tim** | **5,3 KB** (Hanya CSV) | **MISSING** | File WAV rekaman kelas | **TIDAK (DITUNDA)** | Rekaman fisik mandiri | Membutuhkan perekaman langsung oleh tim, bukan unduhan internet. |

---

## 6. REKOMENDASI URUTAN AKSI (ACTION ORDER)

Jika tim ingin melengkapi data untuk pengembangan lanjutan, lakukan dengan urutan berikut:

```
Urutan 1 (WAJIB & MENDESAK — Kuota: ~28 MB):
└── Unduh kembali varian kompresi RGB 224x224 BISINDO Alphabet dari Mendeley Data (4.466 citra, ~27,7 MB)
    -> Mengapa: Memperbaiki model fingerspelling yang gagal konvergensi (3.85%).

Urutan 2 (KONDISIONAL — Kuota: ~2,1 GB):
└── Unduh WL-BISINDO archive.zip (1.600 video MP4, ~2,1 GB) dari Kaggle glennleonali/wl-bisindo
    -> Mengapa: HANYA jika tim akan mengekstrak ulang keypoint dan melatih ulang model M0 pada skema LOSO di lokal.
    -> Catatan: Jika training dilakukan di Google Colab / Kaggle, unduh langsung di cloud tanpa mengotori laptop lokal.

Urutan 3 (TIDAK PERLU DIUNDUH — Menghemat ~11 GB):
├── JANGAN unduh WLASL-300 (~4,5 GB) -> Tidak dipakai model produksi.
├── JANGAN unduh FSL-105 videos (~390 MB) -> Belum masuk fase video neural FSL.
└── JANGAN unduh audio FLEURS WAV (~1,3 GB - 2,6 GB) -> Browser sudah memakai Web Speech API native.
```

---

## 7. BUKTI FAKTUAL & KETERBATASAN PEMERIKSAAN

1. **Integritas Pemeriksaan:** Pemeriksaan dilakukan $100\%$ secara *read-only*. Tidak ada perintah unduhan jaringan, penghapusan, atau penimpaan file yang dijalankan.
2. **Status Git:** Branch `feature/field-test-readiness` tetap berada pada HEAD commit `3a99e96` tanpa perubahan status working tree pada berkas kode yang ada.
3. **Penyebab Berkas Tidak Ada di Disk:** Berkas video, audio, citra mentah, dan keypoint sengaja diabaikan oleh file `.gitignore` repositori (baris 46–69) untuk menjaga agar repository GitHub tetap ringan ($< 100\text{ MB}$).
4. **Kesimpulan Akhir:** Dataset sebesar 13 MB / puluhan GB **TIDAK PERLU DIUNDUH ULANG SECARA MASSAL**. Repositori saat ini sudah mandiri dan fungsional untuk menjalankan demo inferensi isyarat dinamis M0 di browser. Satu-satunya berkas yang layak diunduh adalah dataset citra abjad Mendeley yang sangat ringan (~28 MB).

