# Analisis Kesenjangan Akhir Dataset SignBridge (`docs/DATASET_GAP_ANALYSIS.md`)

**Proyek**: SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Working Directory**: `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif**: `feature/dataset-acquisition` (`HEAD: b38b4da`)  
**Tanggal Analisis**: 7 November 2026  
**Dokumen Acuan**:
- `docs/DATASET_AUDIT_REPORT.md`
- `docs/DATASET_DOWNLOAD_REPORT.md`
- `docs/DATASET_SOURCE_CATALOG.md`
- `data/DATASET_DOWNLOAD_MANIFEST.csv`

---

## 1. Ringkasan Kondisi Seluruh Modalitas (Executive Summary)

Berdasarkan audit fisik di disk dan validasi kriptografis SHA-256 pasca-eksekusi **Tahap 1 s/d Tahap 4**, kondisi kesiapan dataset **SignBridge** secara keseluruhan adalah **BELUM LENGKAP SECARA PENUH (PARSIAL — 52,4% KEBUTUHAN UTAMA TERPENUHI SECARA FISIK)** dan **BELUM SIAP UNTUK TRAINING AKHIR SESUAI MODUL TANPA PEMENUHAN DATA BISINDO & PENYESUAIAN PIPELINE**.

Secara spesifik per modalitas dan bahasa isyarat:
1. **Modalitas Video — Bahasa Isyarat Indonesia (`BISINDO`) [KRITIS — 0% TERSEDIA FISIK]**:
   - **WL-BISINDO** ($\approx 1.600$ video, $32$ gloss): **0 berkas video fisik** di disk (`BLOCKED` karena kredensial autentikasi Kaggle API `~/.kaggle/kaggle.json` belum tersedia).
   - **SignBridge-Kelas** ($3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ klip}$, durasi $\approx 2,6\text{ detik}$, target gabungan $\ge 3.000$ data): **0 berkas video fisik** di disk (`NOT AVAILABLE` karena membutuhkan perekaman kamera fisik oleh 3 penutur manusia).
   - **Video Referensi Jembatan (`data/ref_signs/bisindo/*.mp4`)**: **0 berkas video fisik** (32 path hanya tertulis di `data/bridge/concepts.csv`).
2. **Modalitas Video — Bahasa Isyarat Filipina (`FSL`) [100% TERSEDIA FISIK UNTUK FSL-105]**:
   - **FSL-105** (`doi:10.17632/48y2y99mb9.2`, v2): **2.130 berkas video `.MOV` fisik** (`390.121.532 B` / ~372,05 MB) tersebar lengkap di **105 kelas (`0`..`104`)** pada `data/raw/video/fsl_105/clips/`, lengkap dengan `labels.csv`, `train.csv` (`1.704`), dan `test.csv` (`426`).
   - *Catatan Tegas*: **FSL-105 adalah Bahasa Isyarat Filipina untuk eksperimen lintas negara (X3) dan TIDAK DAPAT dijadikan pengganti WL-BISINDO maupun SignBridge-Kelas.**
3. **Modalitas Video — Bahasa Isyarat Amerika (`ASL` — Pretraining) [HANYA MANIFEST JSON — 0% VIDEO FISIK]**:
   - **WLASL-300** ($\approx 4.000 - 5.000$ video, $300$ gloss): Manifest resmi `WLASL_v0.3.json` (`21.083` entri) dan `WLASL_300_manifest.json` (**300 gloss / 5.117 entri video**) telah tersedia secara fisik, tetapi **0 berkas video `.mp4` fisik** di disk (`BLOCKED` karena unduhan arsip video terproses di Kaggle membutuhkan `~/.kaggle/kaggle.json`, sedangkan URL mentah di JSON memuat 1.604 tautan YouTube dan 382 berkas `.swf` Flash usang).
   - *Catatan Tegas*: **WLASL-300 adalah data pretraining lintas bahasa (ASL) dan TIDAK DAPAT dijadikan pengganti WL-BISINDO.**
4. **Modalitas Image — Ejaan Jari Statis `BISINDO` (`A–Z`) [100% TERSEDIA FISIK]**:
   - **BISINDO Alphabet Image Data** (`doi:10.17632/ywnjpbcz8m.1`, v1): **4.466 citra RGB fisik** ($224 \times 224 \times 3$, `29.054.822 B`, `0` rusak) tersebar lengkap di seluruh **26 kelas (`A–Z`, 165–174 citra/kelas)** pada `data/raw/image/bisindo_alphabet/<A..Z>/`.
5. **Modalitas Audio — Speech-to-Text (`id-ID` & `fil-PH`) [PARSIAL — SUBSET BENCHMARK TERSEDIA, REKAMAN KELAS 0%]**:
   - **Google FLEURS (`id_id`)**: Tersedia fisik **350 berkas `.wav` (`16 kHz` mono, durasi 4.173,20 dtk / ~69,55 menit)** dari split `dev` (`audio/dev.tar.gz`) beserta seluruh **3.616 baris metadata TSV** (`train.tsv` 2.579, `dev.tsv` 350, `test.tsv` 687). Arsip audio fisik `train.tar.gz` dan `test.tar.gz` belum diunduh.
   - **Rekaman Suara Kelas SignBridge (`id-ID` & `fil-PH`)**: **0 berkas `.wav` fisik** (`NOT AVAILABLE`). Berkas `data/audio/metadata.csv` (60 baris) dan `metadata_fil.csv` (24 baris) hanya berisi teks daftar kalimat/path, bukan berkas audio.
6. **Modalitas Text — Kalimat Bahasa Indonesia & Gloss-to-Sentence [100% TERSEDIA FISIK]**:
   - **Tatoeba Indonesian (`ind`)**: **28.418 kalimat Bahasa Indonesia** tersedia fisik di `data/text/tatoeba/ind_sentences.tsv` (`1.389.405 B`). Merupakan kalimat monolingual murni, bukan pasangan `gloss-to-sentence`.
   - **Korpus Kelas & Pasangan Gloss-ke-Kalimat SignBridge**: `kelas_sentences.txt` (**200 kalimat**), `train.tsv` (**170 pasangan**), `val.tsv` (**30 pasangan**), dan `test_manual.tsv` (**105 pasangan** tulisan manusia, 0% overlap) tersedia fisik dan utuh 100%.

---

## 2. Tabel Persyaratan Modul vs Data Aktual di Disk

| No | Modalitas | Bahasa / Domain | Persyaratan Modul Asli SignBridge | Target Modul | Bukti Fisik Aktual di Disk Saat Ini | Selisih (Gap) terhadap Target Modul | Status Kesesuaian |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **VIDEO** | **BISINDO** (Word-Level) | **WL-BISINDO**: $\approx 1.600$ video dan $32$ gloss | $\approx 1.600$ video ($32$ gloss) | **0 video fisik** (`0` file `.mp4`/`.npz`; hanya 32 baris di `data/phonology.csv` & `concepts.csv`) | Kurang **$\approx 1.600$ video fisik BISINDO** (100% belum terunduh) | **`BLOCKED`** (Butuh `~/.kaggle/kaggle.json` untuk `glennleonali/wl-bisindo`) |
| 2 | **VIDEO** | **BISINDO** (Rekaman Tim) | **SignBridge-Kelas**: Target gabungan $\ge 3.000$ data; rekaman tambahan **$3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ contoh}$** ($\approx 2,6\text{ dtk}$) | $960$ video baru (total gabungan $\ge 3.000$ sampel) | **0 video fisik** | Kurang **$960$ video rekaman kamera nyata** (total gabungan kurang $\ge 3.000$ data) | **`NOT AVAILABLE`** (Wajib perekaman fisik oleh 3 signer manusia) |
| 3 | **VIDEO** | **FSL** (Filipino Sign Language) | **FSL-105**: Dataset untuk eksperimen lintas negara BISINDO–FSL | $2.130$ video ($105$ kelas FSL) | **2.130 video `.MOV` fisik** (`390.121.532 B`) di `data/raw/video/fsl_105/clips/<0..104>/` + `labels.csv` (`105`), `train.csv` (`1.704`), `test.csv` (`426`) | **0 kekurangan unduhan** *(Namun hanya 6 dari 105 kelas yang beririsan langsung dengan 32 konsep kelas SignBridge)* | **TERPENUHI 100% SECARA FISIK** *(Tidak menggantikan WL-BISINDO)* |
| 4 | **VIDEO** | **ASL** (Pretraining) | **WLASL-300**: $\approx 4.000 - 5.000$ video dan $300$ gloss untuk pretraining | $\approx 4.000 - 5.000$ video ($300$ gloss) | **Hanya Manifest JSON**: `WLASL_v0.3.json` (`21.083` entri) & `WLASL_300_manifest.json` (**5.117 entri / 300 gloss**). **0 video `.mp4` fisik** | Kurang **$5.117$ berkas video `.mp4` fisik** untuk 300 gloss | **MANIFEST TERSEDIA; VIDEO `BLOCKED`** (Butuh Kaggle API `risangbaskoro/wlasl-processed`) |
| 5 | **VIDEO** | **BISINDO & FSL** (Referensi Web) | Video referensi per konsep pada `data/bridge/concepts.csv` | $32$ video BISINDO + $32$ video FSL | **0 video fisik** (`data/ref_signs/` tidak ada) | Kurang **$64$ video referensi** (`data/ref_signs/bisindo/*.mp4` & `fsl/*.mp4`) | **`NOT AVAILABLE`** (Hanya path tertulis di `concepts.csv`) |
| 6 | **IMAGE** | **BISINDO** (Fingerspelling) | **BISINDO Alphabet Image Data** dari Mendeley (`A–Z`) | $26$ kelas (`A–Z`) | **4.466 citra RGB fisik** ($224 \times 224 \times 3$, `29.054.822 B`, `0` rusak) di `data/raw/image/bisindo_alphabet/<A..Z>/` | **0 kekurangan unduhan** *(Belum diekstrak ke `data/fingerspelling_crops` karena larangan preprocessing)* | **TERPENUHI 100% SECARA FISIK** |
| 7 | **AUDIO** | **Bahasa Indonesia (`id_id`)** | **Google FLEURS** konfigurasi `id_id` | Korpus `id_id` ($3.616$ klip: $2.579$ train, $350$ dev, $687$ test) | **350 berkas `.wav` fisik** (`dev.tar.gz`, `16 kHz` mono, **4.173,20 dtk**) + **3.616 baris TSV** (`train.tsv`, `dev.tsv`, `test.tsv`) | Kurang **$3.266$ berkas `.wav` fisik** (`2.579` di `train.tar.gz` + `687` di `test.tar.gz`) | **SUBSET EKSPERIMEN (PROFIL A — 9,7% WAV FISIK)** |
| 8 | **AUDIO** | **Bahasa Indonesia (`id-ID`)** | **Rekaman kalimat kelas SignBridge** | Minimal $60$ berkas `.wav` sesuai `data/audio/metadata.csv` | **0 berkas `.wav` fisik** *(hanya 60 baris teks di `metadata.csv`)* | Kurang **$60$ berkas `.wav` rekaman suara kelas nyata** | **`NOT AVAILABLE`** (FLEURS bukan pengganti; CSV bukan audio) |
| 9 | **AUDIO** | **Bahasa Filipina (`fil-PH`)** | Tambahan eksperimen FSL (`fil_ph` & rekaman kelas Filipina) | Opsional (`FLEURS fil_ph` & `24` baris `metadata_fil.csv`) | **0 berkas `.wav` fisik** *(hanya 24 baris teks di `metadata_fil.csv`)* | Kurang berkas `.wav` fisik jika eksperimen A4 (`asr_a4_tiny_ft_fil.yaml`) dijalankan | **OPSIONAL / `NOT AVAILABLE`** |
| 10 | **TEXT** | **Bahasa Indonesia (`ind`)** | **Tatoeba Indonesian** | Korpus kalimat Bahasa Indonesia (`ind`) | **28.418 kalimat Bahasa Indonesia** di `data/text/tatoeba/ind_sentences.tsv` (`1.389.405 B`) | **0 kekurangan unduhan** *(Monolingual kalimat; bukan pasangan gloss-to-sentence)* | **TERPENUHI 100% SECARA FISIK** |
| 11 | **TEXT** | **BISINDO Gloss $\rightarrow$ Indonesia** | **Kalimat kelas & TSV (`train.tsv`, `val.tsv`, `test_manual.tsv`)** | `200` kalimat kelas + `170` train + `30` val + `105` test manual | **200** kalimat (`kelas_sentences.txt`), **170** pasangan (`train.tsv`), **30** pasangan (`val.tsv`), **105** pasangan (`test_manual.tsv`) | **0 kekurangan berkas** *(Catatan: 170 train & 30 val dibangkitkan via `sentence_to_pseudo_gloss` dari kalimat kombinasi template)* | **TERPENUHI 100% SECARA FISIK** |

---

## 3. Tabel Jumlah Data Aktual per Bahasa dan Kelas

### 3.1 Ringkasan Kuantitatif Berdasarkan Bahasa Isyarat & Bahasa Lisan/Teks

| Bahasa / Sistem Isyarat | Modalitas | Nama Dataset | Jumlah Kelas / Gloss Target | Jumlah Kelas Fisik Tersedia | Jumlah Sampel Target | Jumlah Sampel Fisik Aktual (Non-Metadata) | Ukuran Fisik di Disk |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **BISINDO** (Indonesian Sign Language) | **Video** | `WL-BISINDO` | 32 gloss | **0 kelas video** (32 di CSV) | $\approx 1.600$ video | **0 video** (`BLOCKED`) | `0 B` (hanya `530 B` CSV) |
| **BISINDO** (Indonesian Sign Language) | **Video** | `SignBridge-Kelas` (Rekaman Tim) | 32 gloss | **0 kelas video** | $960$ video ($3 \times 32 \times 10$) | **0 video** (`NOT AVAILABLE`) | `0 B` |
| **BISINDO** (Indonesian Sign Language) | **Image** | `BISINDO Alphabet Image Data` (Mendeley v1) | 26 kelas (`A–Z`) | **26 kelas (`A–Z`)** | 26 kelas (`A–Z`) | **4.466 citra RGB** ($224 \times 224 \times 3$) | `29.054.822 B` (~27,71 MB) |
| **BISINDO $\rightarrow$ Bahasa Indonesia** | **Text** | `train.tsv`, `val.tsv`, `test_manual.tsv` | 32 gloss kosakata | **32 gloss kosakata** | 305 pasangan paralel | **305 pasangan** (`170` train + `30` val + `105` test) | `33.775 B` |
| **FSL** (Filipino Sign Language) | **Video** | `FSL-105` (Mendeley v2) | 105 kelas FSL | **105 kelas (`0`..`104`)** | 2.130 video | **2.130 video `.MOV`** (`1.704` train + `426` test) | `390.121.532 B` (~372,05 MB) + `379.081.783 B` (`.zip`) |
| **ASL** (American Sign Language) | **Video** | `WLASL-300` (Pretraining) | 300 gloss ASL | **0 kelas video** (`300` di JSON) | $\approx 4.000 - 5.000$ video | **0 video** (`5.117` entri hanya di JSON; `BLOCKED`) | `14.147.179 B` (hanya JSON) |
| **Bahasa Indonesia (`id-ID`)** | **Audio** | `Google FLEURS (id_id)` | Transkripsi ucapan | Split `dev` (`350` kalimat) | 3.616 klip `.wav` | **350 berkas `.wav`** (durasi **4.173,20 dtk**) | `267.099.980 B` (`.wav`) + `220.586.217 B` (`.tar.gz`) |
| **Bahasa Indonesia (`id-ID`)** | **Audio** | `Rekaman Suara Kelas SignBridge` | Kalimat ruang kelas | **0 berkas `.wav`** | 60 berkas `.wav` | **0 berkas `.wav`** (`NOT AVAILABLE`) | `0 B` (hanya `5.334 B` CSV) |
| **Bahasa Indonesia (`ind`)** | **Text** | `Tatoeba Indonesian` + `kelas_sentences.txt` | Kalimat monolingual | Kalimat monolingual | $28.418 + 200$ kalimat | **28.618 kalimat** (`28.418` Tatoeba + `200` kelas) | `1.404.235 B` (+ `330.738 B` `.bz2`) |
| **Bahasa Filipina (`fil-PH`)** | **Audio** | `metadata_fil.csv` & `FLEURS fil_ph` | Kalimat ruang kelas | **0 berkas `.wav`** | 24 berkas `.wav` | **0 berkas `.wav`** (`NOT AVAILABLE`) | `0 B` (hanya `1.849 B` CSV) |

### 3.2 Rincian Distribusi Kelas Aktual yang Tersedia Secara Fisik

1. **BISINDO Alphabet Image Data (`data/raw/image/bisindo_alphabet/<A..Z>/` — 26 Kelas, 4.466 Citra RGB)**:
   - Kelas dengan **165 citra**: `A` (1 kelas).
   - Kelas dengan **169 citra**: `B`, `C`, `E`, `J` (4 kelas).
   - Kelas dengan **170 citra**: `D`, `W` (2 kelas).
   - Kelas dengan **171 citra**: `R` (1 kelas).
   - Kelas dengan **172 citra**: `L`, `P`, `V` (3 kelas).
   - Kelas dengan **173 citra**: `F`, `G`, `H`, `I`, `K`, `M`, `N`, `O`, `Q`, `S`, `T`, `U` (12 kelas).
   - Kelas dengan **174 citra**: `X`, `Y`, `Z` (3 kelas).
2. **FSL-105 Video Dataset (`data/raw/video/fsl_105/clips/<0..104>/` — 105 Kelas, 2.130 Video `.MOV`)**:
   - Terbagi ke dalam **10 kategori semantik**: `GREETING` (`0–9`), `SURVIVAL` (`10–19`), `NUMBER` (`20–29`), `CALENDAR` (`30–41`), `DAYS` (`42–51`), `FAMILY` (`52–61`), `RELATIONSHIPS` (`62–71`), `COLOR` (`72–84`), `FOOD` (`85–94`), dan `DRINK` (`95–104`).
   - Setiap kelas memiliki **20 hingga 21 video `.MOV`** (`1.704` video pada `train.csv` [80%] dan `426` video pada `test.csv` [20%]).
3. **32 Gloss Target BISINDO (`data/phonology.csv` & `data/bridge/concepts.csv` — 0 Video Fisik)**:
   - `HALO, TERIMA_KASIH, MAAF, TOLONG, SAYA, KAMU, GURU, TEMAN, MAU, SUDAH, BELUM, BISA, TIDAK, ADA, BELAJAR, PAHAM, TANYA, BACA, TULIS, JAWAB, BUKU, TUGAS, KELAS, SEKOLAH, APA, SIAPA, DIMANA, KAPAN, BAGAIMANA, BAIK, BENAR, SALAH` (**0 video fisik per kelas saat ini**).

---

## 4. Daftar Dataset yang Sudah Lengkap vs Belum Lengkap

### 4.1 Dataset yang Sudah Lengkap Secara Fisik
1. **Text — Tatoeba Indonesian (`ind`)**: Lengkap 100% (**28.418 kalimat Bahasa Indonesia** di `data/text/tatoeba/ind_sentences.tsv` + arsip asli `.bz2`).
2. **Text — Korpus Kelas & Paralel Gloss-ke-Kalimat SignBridge**: Lengkap 100% (`kelas_sentences.txt` **200 kalimat**, `train.tsv` **170 pasangan**, `val.tsv` **30 pasangan**, `test_manual.tsv` **105 pasangan**).
3. **Image — BISINDO Alphabet Image Data (Mendeley v1, Varian RGB $224 \times 224$)**: Lengkap 100% (**4.466 citra RGB** di seluruh **26 kelas `A–Z`**, 0 berkas rusak).
4. **Video — FSL-105 (Mendeley v2)**: Lengkap 100% (**2.130 berkas video `.MOV`** di seluruh **105 kelas `0`..`104`**, lengkap dengan `labels.csv`, `train.csv`, `test.csv`, dan `clips.zip`).

### 4.2 Dataset yang Belum Lengkap (`SUBSET`, `BLOCKED`, atau `NOT AVAILABLE`)
1. **Video — WL-BISINDO (`Kaggle: glennleonali/wl-bisindo`)** $\rightarrow$ **`BLOCKED` (0 / ~1.600 video)**:
   - Tidak dapat diunduh tanpa berkas kredensial `~/.kaggle/kaggle.json`.
2. **Video — WLASL-300 (`dxli94/WLASL` / `Kaggle: risangbaskoro/wlasl-processed`)** $\rightarrow$ **`MANIFEST ONLY / VIDEO BLOCKED` (0 / 5.117 video `.mp4`)**:
   - Hanya manifest JSON (`WLASL_v0.3.json` & `WLASL_300_manifest.json`) yang tersedia di disk; arsip video terproses di Kaggle terblokir kredensial API, dan URL mentah di JSON tidak dapat diunduh utuh karena mencakup 1.604 tautan YouTube dan 382 berkas `.swf` mati.
3. **Video — SignBridge-Kelas ($3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ klip}$)** $\rightarrow$ **`NOT AVAILABLE` (0 / 960 video)**:
   - Belum dilakukan perekaman fisik menggunakan kamera oleh 3 penutur manusia.
4. **Video — Referensi Konsep Jembatan (`data/ref_signs/bisindo/*.mp4` & `data/ref_signs/fsl/*.mp4`)** $\rightarrow$ **`NOT AVAILABLE` (0 / 64 video)**:
   - Direktori `data/ref_signs/` belum ada di disk.
5. **Audio — Google FLEURS (`id_id`) Split `train` & `test`** $\rightarrow$ **`SUBSET EKSPERIMEN (PROFIL A)` (350 / 3.616 berkas `.wav` fisik)**:
   - Baru split `dev` (`350` berkas `.wav`) yang diunduh secara fisik; `train.tar.gz` (`2.579` `.wav`) dan `test.tar.gz` (`687` `.wav`) belum diunduh.
6. **Audio — Rekaman Suara Kelas SignBridge (`data/audio/wavs/id_001.wav`..`id_060.wav` & `wavs_fil/fil_001.wav`..`fil_024.wav`)** $\rightarrow$ **`NOT AVAILABLE` (0 / 84 berkas `.wav` fisik)**:
   - Hanya tersedia metadata teks di `data/audio/metadata.csv` dan `metadata_fil.csv`.

---

## 5. Audit Konsistensi Label, Kelas, Gloss, Struktur Direktori, dan Kompatibilitas Pipeline Saat Ini

Pemeriksaan langsung terhadap kode sumber pipeline di `scripts/`, `configs/`, dan `signbridge/` (tanpa mengubah kode) menemukan **6 ketidaksesuaian struktural (critical pipeline incompatibilities)** yang menyebabkan dataset fisik yang sudah diunduh **TIDAK AKAN TERBACA** jika pipeline dijalankan apa adanya saat ini:

| No | Komponen Pipeline (`scripts/` & `signbridge/`) | Yang Diharapkan oleh Kode Pipeline Saat Ini | Kondisi Aktual Dataset Fisik di Disk | Dampak Jika Pipeline Dijalankan Sekarang Tanpa Perubahan |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Ekstraksi Keypoint Video** (`scripts/extract_keypoints.py` baris 93–107) | Hanya memindai ekstensi `*.mp4` dan `*.webm` di `--raw data/raw/bisindo`, serta mengambil nama folder induk (`vf.parent.name.upper()`) untuk dicocokkan ke `BISINDO_32_GLOSSES`. | Video fisik **FSL-105** berada di `data/raw/video/fsl_105/clips/<0..104>/` dengan ekstensi **`.MOV` (huruf besar)** dan nama folder berupa angka **`0`..`104`**. Sedangkan folder `data/raw/bisindo` tidak ada (`0` video). | Skrip menemukan **`0` berkas `.mp4`/`.webm`**, lalu otomatis memanggil `ensure_demo_dataset()` (baris 96) yang membuat **data sintetis acak**! Kalaupun ekstensi `.MOV` ditambahkan tanpa pemetaan `labels.csv`, nama folder `0`..`104` tidak ada di `BISINDO_32_GLOSSES` sehingga dilabeli secara modulo `idx % 32` yang **salah total**. |
| **2** | **Kesenjangan Kosakata Lintas Negara** (`data/bridge/concepts.csv` vs `data/raw/video/fsl_105/labels.csv`) | `configs/05a_asean_fsl_pose.yaml` mengatur `num_classes: 32` untuk transfer BISINDO $\rightarrow$ FSL pada 32 konsep ruang kelas (`concepts.csv`). | Dari 32 `fsl_gloss` di `concepts.csv`, **hanya 6 gloss yang ada di dalam 105 kelas `FSL-105`**: `HELLO` (ID 3), `THANK YOU` (ID 7), `UNDERSTAND` (ID 10), `NO` (ID 14), `WRONG` (ID 16), dan `CORRECT` (ID 17). **26 konsep kelas lainnya** (`TEACHER, STUDY, BOOK, SCHOOL, ASK, READ, WRITE`, dll.) **tidak ada di FSL-105**. Selain itu, `labels.csv` memiliki spasi ekstra `"NINE "` (ID 28) dan typo `"WEELCHAIR PERSON"` (ID 68). | Eksperimen lintas negara X3 (`05a` & `05b`) tidak dapat memetakan 32 konsep ruang kelas secara 1-ke-1 ke `FSL-105` tanpa menyesuaikan daftar kelas evaluasi (6 kelas beririsan atau 105 kelas penuh FSL-105). |
| **3** | **Pemotongan Tangan Citra A–Z** (`scripts/crop_hands.py` baris 23–57 & `signbridge/image/train_image.py`) | `run_crop_hands(in_dir, out_dir, manifest_path)` di `scripts/crop_hands.py` **mengabaikan argumen `in_dir`** dan langsung membangkitkan 78 matriks acak `dummy_img = rng.integers(...)` ke `.npy`! Selain itu, path default berbeda-beda: `data/raw/images_mendeley` (`crop_hands.py`), `data/fingerspelling_crops` (`image_i1_mobilenetv3.yaml`), dan `data/images/manifest_images_mendeley.csv` (`train_image.py`). | **4.466 citra RGB asli** berada di `data/raw/image/bisindo_alphabet/<A..Z>/*.jpg`. Selain itu terdapat **8 berkas dengan anomali penamaan prefiks** asli dari Mendeley (`D_` di folder `C`, dua `E_` di `L`, tiga `0_` di `O`, `Y_` di `V`, `S_` di `Z`). | Jika `scripts/crop_hands.py` dan `train_image.py` dijalankan sekarang, **seluruh 4.466 citra asli Mendeley tidak akan pernah dibaca sama sekali**, dan model I1–I3 justru dilatih pada citra sintetis/pola sinus! |
| **4** | **Skema Kolom Fonologi** (`signbridge/constants.py` baris 221–228 vs `data/phonology.csv`) | `PHONOLOGY_COLUMNS` di kode mengharapkan 6 kolom: `handshape_dom`, `handshape_nondom`, `location`, `movement`, `orientation`, `handedness`. | `data/phonology.csv` hanya memiliki header 4 fitur: `gloss,handshape,location,movement,two_handed`. | Saat `load_phonology_map("data/phonology.csv")` dijalankan, 4 dari 6 kepala multitask fonologi (`handshape_dom`, `handshape_nondom`, `orientation`, `handedness`) tidak menemukan kolomnya dan diisi `-1` (*ignore index*). |
| **5** | **Konfigurasi Kelas Pretraining WLASL** (`configs/01_pose_pretrain_wlasl.yaml` baris 8) | Mengatur `num_classes: 100` (WLASL-100). | Persyaratan modul mewajibkan **WLASL-300** (`300` gloss, `5.117` entri pada `WLASL_300_manifest.json`). | Ketidaksesuaian dimensi kepala klasifikasi pretraining (`100` vs target modul `300`). |
| **6** | **Pipeline Audio ASR & Text Gloss-to-Sentence** (`signbridge/audio/train_asr.py`, `scripts/prepare_kelas_audio.py`, `signbridge/text/train_text.py`) | `prepare_kelas_audio.py` membuat nada sinus `440 Hz` sintetis; `train_asr.py` melatih model pada tensor acak `torch.randn(4, 80, 100)` dan mengevaluasi string *hardcoded*; `train_text.py` melatih GRU pada `torch.randint` tanpa membaca `train.tsv` / `val.tsv` / `ind_sentences.tsv`. | **350 berkas `.wav` asli FLEURS `id_id`** (`16 kHz` IEEE float 32-bit, `fmt_tag=3`) ada di `data/audio/fleurs/id_id/audio/dev/` dan **28.418 kalimat Tatoeba** ada di `data/text/tatoeba/ind_sentences.tsv`. *(Catatan: modul standar Python `wave` menolak `fmt_tag=3` IEEE float kecuali dibaca dengan `soundfile`/`torchaudio`/`scipy` atau dikonversi ke PCM 16-bit).* | Jika `train_asr.py` dan `train_text.py` dijalankan tanpa pembaruan loader data, berkas audio FLEURS dan korpus teks yang telah diunduh **tidak digunakan dalam proses training**. |

---

## 6. Daftar Masalah Lisensi dan Atribusi

| No | Dataset | Sumber Resmi | Lisensi Tercatat | Status Bukti Lisensi | Masalah / Ketentuan Atribusi yang Wajib Dipenuhi |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | **Tatoeba Indonesian (`ind`)** | `downloads.tatoeba.org` | **CC BY 2.0 FR** | **TERBUKTI RESMI** | Wajib mencantumkan atribusi ke *Tatoeba.org and its contributors* dan menyertakan tautan `https://tatoeba.org` serta lisensi CC BY 2.0 FR. |
| 2 | **Google FLEURS (`id_id`)** | `huggingface.co/datasets/google/fleurs` | **CC BY 4.0** | **TERBUKTI RESMI** | Wajib mengutip publikasi resmi *Conneau et al. (2022), "FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech"*. |
| 3 | **BISINDO Alphabet Image Data (v1)** | Mendeley Data (`doi:10.17632/ywnjpbcz8m.1`) | **CC BY 4.0** | **TERBUKTI RESMI** (Terverifikasi di `mendeley_metadata.json`) | Wajib mencantumkan atribusi penulis **Samuel Ady Sanjaya (2024)** beserta DOI `10.17632/ywnjpbcz8m.1`. |
| 4 | **FSL-105 (v2)** | Mendeley Data (`doi:10.17632/48y2y99mb9.2`) | **CC BY 4.0** | **TERBUKTI RESMI** (Terverifikasi di `mendeley_fsl105_metadata.json`) | Wajib mencantumkan atribusi penulis **Isaiah Jassen Tupal (2023)** beserta DOI `10.17632/48y2y99mb9.2`. |
| 5 | **WLASL-300 (`WLASL_v0.3.json`)** | GitHub `dxli94/WLASL` | **Computational Use of Data Agreement (C-UDA) / Academic Non-Commercial** | **TERBUKTI RESMI** | **Hanya untuk penggunaan riset akademik non-komersial**; wajib mengutip *Li et al. (WACV 2020)*; dilarang mendistribusikan ulang video untuk tujuan komersial. |
| 6 | **WL-BISINDO (`glennleonali/wl-bisindo`)** | Kaggle (`glennleonali/wl-bisindo`) | Diklaim Akademik / CC BY 4.0 di dokumentasi awal | **BELUM DAPAT DIBUKTIKAN SECARA FISIK (`UNVERIFIED`)** | Karena dataset masih **`BLOCKED`** (belum dapat diakses via Kaggle API tanpa kredensial), metadata lisensi asli dari halaman/arsip Kaggle serta izin redistribusi/consent signer **belum dapat diverifikasi secara fisik**. |
| 7 | **SignBridge-Kelas (Video 960 Klip & Audio 60 Klip)** | Akuisisi Mandiri Tim | Internal Tim / CC BY 4.0 | **BELUM TERSEDIA (`NOT AVAILABLE`)** | Saat perekaman fisik dilakukan nanti, wajib melampirkan formulir **Informed Consent** tertulis dari seluruh penutur (minimal 3 signer video dan penutur audio kelas) karena wajah dan suara terekam. |

---

## 7. Risiko Jika Training Dilakukan dengan Kondisi Sekarang

Apabila tahap preprocessing dan training langsung dijalankan sekarang **tanpa melengkapi dataset yang kurang dan tanpa memperbaiki ketidaksesuaian loader pipeline**, maka akan timbul **5 risiko fatal**:

1. **Risiko Fatal 1 — Model Utama BISINDO (`ST-GCN`, `Fusion`, `Student ONNX`) Dilatih pada 100% Data Sintetis Palsu**:
   - Karena `WL-BISINDO` ($\approx 1.600$ video) dan `SignBridge-Kelas` ($960$ video) masih `0` berkas fisik di disk, menjalankan `extract_keypoints.py` dan `signbridge/train.py` akan memicu `ensure_demo_dataset()` yang menghasilkan koordinat tangan sinusoidal sintetis (`np.sin`/`np.cos`). Model yang dihasilkan sama sekali tidak mengenali bahasa isyarat BISINDO nyata di dunia nyata dan melanggar aturan keaslian modul.
2. **Risiko Fatal 2 — Model Citra Ejaan Jari (`I1 MobileNetV3`, `I2 EfficientNet`, `I3 MobileViT`) Mengabaikan 4.466 Citra Mendeley yang Sudah Diunduh**:
   - Karena `scripts/crop_hands.py` saat ini mengabaikan folder input dan membangkitkan matriks piksel acak (`rng.integers`), menjalankan training citra tanpa memperbaiki skrip `crop_hands.py` dan `FingerspellDataset` akan menyebabkan model dilatih pada noise sintetis, bukan pada 4.466 citra BISINDO asli yang sudah ada di `data/raw/image/bisindo_alphabet/`.
3. **Risiko Fatal 3 — Video `FSL-105` (`.MOV`) Tidak Terbaca dan Salah Label**:
   - Menjalankan `extract_keypoints.py` pada `data/raw/video/fsl_105/clips/` tanpa menambahkan dukungan ekstensi `.MOV` dan tanpa memetakan ID folder `0..104` via `labels.csv` akan menghasilkan 0 video terekstrak (atau pelabelan modulo acak ke gloss BISINDO).
4. **Risiko Fatal 4 — Kegagalan Ekstraksi MediaPipe karena Dependensi Lingkungan Belum Terpasang**:
   - Lingkungan Python lokal saat ini (`Python 3.11.0b4`) belum memiliki paket `mediapipe`, `opencv-python` (`cv2`), dan `torch`. Karena `extract_video_to_86_nodes()` di `scripts/extract_keypoints.py` menangkap `Exception` secara diam-diam (`except Exception: pass`) lalu mengembalikan angka acak `rng.uniform`, menjalankan ekstraksi sebelum menginstal `mediapipe` dan `opencv-python` akan diam-diam merusak seluruh berkas `.npz` menjadi angka acak!
5. **Risiko Fatal 5 — Evaluasi ASR Audio & Teks Tidak Mencerminkan Data Aktual**:
   - Menjalankan `train_asr.py` dan `train_text.py` saat ini hanya akan mengeksekusi pelatihan dummy pada tensor acak tanpa menyentuh 350 berkas `.wav` Google FLEURS `id_id` maupun 28.418 kalimat Tatoeba Indonesian.

---

## 8. Rencana Prioritas Pemenuhan Kekurangan Dataset (Action Plan)

Untuk menutup seluruh kesenjangan di atas secara berurutan dan patuh terhadap aturan modul, berikut adalah urutan prioritas yang direkomendasikan:

### Prioritas 1 (Bloker Utama BISINDO & Pretraining Video — Wajib Sebelum Training Video)
1. **Konfigurasi Kredensial Kaggle API (`~/.kaggle/kaggle.json`)**:
   - Pasang token API Kaggle resmi milik tim agar dapat mengunduh:
     - **WL-BISINDO** (`glennleonali/wl-bisindo`, $\approx 1.600$ video, $32$ gloss) ke `data/raw/video/wl_bisindo/`.
     - **WLASL-300** (`risangbaskoro/wlasl-processed`, difilter menggunakan `WLASL_300_manifest.json` untuk **300 gloss / 5.117 klip**) ke `data/raw/video/wlasl_300/videos/`.
   - Verifikasi lisensi fisik dan hitung SHA-256 setelah unduhan selesai.
2. **Perekaman Fisik `SignBridge-Kelas` (Video & Audio Ruang Kelas)**:
   - Rekam **960 klip video BISINDO** ($3\text{ signer} \times 32\text{ gloss} \times 10\text{ take}$, durasi $\approx 2,6\text{ detik}$) dengan *Informed Consent* untuk memenuhi target gabungan $\ge 3.000$ sampel.
   - Rekam **60 berkas suara `.wav` (`16 kHz` mono PCM 16-bit)** sesuai kalimat pada `data/audio/metadata.csv` ke `data/audio/wavs/id_001.wav`..`id_060.wav` (serta 24 berkas `wavs_fil/` jika eksperimen Filipina dijalankan).

### Prioritas 2 (Kelengkapan Korpus Audio FLEURS `id_id`)
1. **Unduh `train.tar.gz` (`2.579` klip) dan `test.tar.gz` (`687` klip) dari Google FLEURS `id_id`**:
   - Melengkapi 350 klip `dev.tar.gz` yang sudah ada sehingga seluruh **3.616 klip `.wav` `id_id`** tersedia secara fisik untuk fine-tuning dan evaluasi Whisper ASR.

### Prioritas 3 (Penyelarasan Pipeline & Lingkungan Sebelum Preprocessing — Hanya Setelah Disetujui)
1. **Instalasi Dependensi Ekstraksi & Training**:
   - Instal `opencv-python`, `mediapipe`, `torch`, `torchvision`, `torchaudio`/`soundfile`, dan `pillow` pada virtual environment proyek.
2. **Perbaikan Skrip Preprocessing & Loader (Tanpa Fallback Sintetis Diam-diam)**:
   - Matikan *silent synthetic fallback* pada `scripts/extract_keypoints.py`, `scripts/crop_hands.py`, dan `scripts/prepare_kelas_audio.py` agar skrip benar-benar membaca berkas fisik yang telah diunduh (`data/raw/image/bisindo_alphabet/<A..Z>/*.jpg` dan `data/raw/video/fsl_105/clips/<0..104>/*.MOV`) serta gagal secara eksplisit jika berkas tidak ditemukan.
   - Saring 8 berkas citra dengan anomali prefiks nama di `BISINDO Alphabet Image Data` dan sesuaikan pemetaan kolom `data/phonology.csv` serta `num_classes: 300` pada `configs/01_pose_pretrain_wlasl.yaml`.

---

## 9. Rekomendasi Akhir: Apakah Proyek Sudah Siap Preprocessing dan Training?

> **KEPUTUSAN REKOMENDASI AKHIR: `BELUM SIAP SECARA PENUH (CONDITIONAL NO-GO UNTUK TRAINING PENUH; SIAP PARSIAL HANYA UNTUK MODALITAS TEXT, IMAGE BISINDO A–Z, DAN VIDEO FSL-105 SETELAH PENYELARASAN SKRIP PREPROCESSING)`**

### Rincian Kesiapan per Modalitas:
1. **Modalitas Text (`Gloss-to-Sentence` & Korpus Kalimat Bahasa Indonesia)**:
   - **Status Data**: **SIAP 100%** (`28.418` kalimat Tatoeba + `200` kalimat kelas + `170` train + `30` val + `105` test manual sudah lengkap di disk).
   - **Syarat Eksekusi**: Perlu memastikan skrip `signbridge/text/train_text.py` benar-benar memuat `train.tsv` dan `val.tsv` saat melatih model neural (`T1`/`T2`/`T3`).
2. **Modalitas Image (`BISINDO Alphabet A–Z`)**:
   - **Status Data**: **SIAP 100%** (**4.466 citra RGB** di seluruh **26 kelas `A–Z`** sudah lengkap dan tervalidasi di `data/raw/image/bisindo_alphabet/`).
   - **Syarat Eksekusi**: **Jangan menjalankan `scripts/crop_hands.py` sebelum skrip tersebut diperbaiki** agar membaca citra `.jpg` asli dari `data/raw/image/bisindo_alphabet/` (karena kode `crop_hands.py` saat ini masih menghasilkan citra dummy sintetis dan mengabaikan folder input).
3. **Modalitas Audio (`Whisper ASR id-ID`)**:
   - **Status Data**: **SIAP PARSIAL (SUBSET EKSPERIMEN)** — Tersedia **350 berkas `.wav` fisik** (`Google FLEURS id_id` split `dev`, durasi 69,55 menit) + 3.616 baris TSV, tetapi **rekaman suara kelas (`60` file `.wav`) masih `NOT AVAILABLE`** dan split `train`/`test` FLEURS belum diunduh.
   - **Syarat Eksekusi**: Jangan menjalankan `scripts/prepare_kelas_audio.py` (karena membuat gelombang sinus sintetis); gunakan 350 `.wav` asli FLEURS `id_id` (atau unduh `train.tar.gz` & `test.tar.gz` terlebih dahulu) serta rekam 60 audio kelas nyata.
4. **Modalitas Video (`WL-BISINDO`, `WLASL-300`, `FSL-105`, `SignBridge-Kelas`)**:
   - **Status Data**:
     - **FSL-105 (`2.130` video `.MOV`, `105` kelas)**: **SIAP 100% SECARA FISIK**, namun `scripts/extract_keypoints.py` wajib disesuaikan terlebih dahulu agar mengenali ekstensi `.MOV` dan `labels.csv`.
     - **WL-BISINDO ($\approx 1.600$ video, $32$ gloss)**: **BELUM SIAP (`BLOCKED` — 0 video fisik)**.
     - **WLASL-300 ($\approx 4.000 - 5.000$ video, $300$ gloss)**: **BELUM SIAP (`MANIFEST ONLY / VIDEO BLOCKED` — 0 video fisik)**.
     - **SignBridge-Kelas ($960$ video rekaman tim)**: **BELUM SIAP (`NOT AVAILABLE` — 0 video fisik)**.
   - **Kesimpulan Video**: **Training model utama video BISINDO (`M1`–`M4`) TIDAK BOLEH DIJALANKAN SEKARANG** karena belum ada satu pun berkas video BISINDO fisik di disk.

