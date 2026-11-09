# Laporan Audit Fisik & Kepatuhan Modul Dataset SignBridge (`docs/DATASET_AUDIT_REPORT.md`)

**Tanggal Audit & Pembaruan**: 7 November 2026  
**Working Directory Aktif**: `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif**: `feature/dataset-acquisition` (`b38b4da`)  
**Remote Origin**: `https://github.com/KarinaGlo/SignBridge.git`

---

## 1. Tabel Perbandingan Kepatuhan terhadap Persyaratan Modul Asli SignBridge

Tabel berikut menyandingkan persyaratan modul asli SignBridge dengan dataset yang dipilih, sumber resmi terverifikasi, jumlah target, jumlah aktual yang telah diunduh/tersedia secara fisik di disk saat ini, serta status kesesuaiannya:

| Modalitas | Persyaratan Modul Asli | Dataset yang Dipilih | Sumber Resmi & Lisensi | Jumlah Target Modul | Jumlah Aktual Fisik Saat Ini | Status Kesesuaian |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. VIDEO** | **WL-BISINDO**: $\approx 1.600$ video dan $32$ gloss | WL-BISINDO | Kaggle (`glennleonali/wl-bisindo`) — CC BY 4.0 / Akademik | $\approx 1.600$ video ($32$ gloss) | **0 video** (`0` file `.mp4` / `.npz` di disk; hanya 32 baris metadata di `data/phonology.csv` & `concepts.csv`) | **`BLOCKED`** (Kredensial autentikasi Kaggle API `~/.kaggle/kaggle.json` tidak tersedia di mesin lokal) |
| **1. VIDEO** | **WLASL-300**: $\approx 4.000 - 5.000$ video dan $300$ gloss untuk pretraining | WLASL-300 | GitHub Resmi (`dxli94/WLASL`) / Kaggle (`risangbaskoro/wlasl-processed`) — Akademik Non-Komersial | $\approx 4.000 - 5.000$ video ($300$ gloss) | **Manifest Resmi Terunduh**: `WLASL_v0.3.json` (`11.932.637 B`, 2.000 gloss / 21.083 entri) & `WLASL_300_manifest.json` (`2.214.542 B`, **300 gloss / 5.117 entri video**: `3.549` train, `900` val, `668` test). **0 file video `.mp4`** di disk | **MANIFEST TERUNDUH; VIDEO FISIK `BLOCKED`** *(Unduhan arsip video massal `risangbaskoro/wlasl-processed` membutuhkan `~/.kaggle/kaggle.json`; tautan mentah memuat 1.604 YouTube & 382 `.swf` usang)* |
| **1. VIDEO** | **FSL-105**: Dataset untuk eksperimen BISINDO–FSL | FSL-105 (*Filipino Sign Language Dataset*, v2) | Mendeley Data (`doi:10.17632/48y2y99mb9.2`, Isaiah Jassen Tupal, 2023) — CC BY 4.0 | $2.130$ video ($105$ kelas FSL) | **2.130 berkas video `.MOV` fisik** (`390.121.532 B` / ~372,05 MB, `0` rusak) tersebar lengkap di **105 kelas (`0`..`104`)** pada `data/raw/video/fsl_105/clips/`, beserta `clips.zip` (`379.081.783 B`), `labels.csv` (`105` kelas), `train.csv` (`1.704` baris), dan `test.csv` (`426` baris) | **TERPENUHI 100% (SELESAI DIUNDUH, DIEKSTRAK & TERVALIDASI)** *(Seluruh 2.130 video `.MOV` cocok 100% dengan `train.csv` + `test.csv`; ekstraksi 86 keypoint belum dijalankan sesuai larangan preprocessing)* |
| **1. VIDEO** | **SignBridge-Kelas**: Target minimal **$3.000$ data** gabungan; rekaman tambahan **$3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ contoh}$** ($\approx 2,6\text{ dtk}$) | SignBridge-Kelas (Rekaman Kamera Penutur) | Perekaman Mandiri Tim via Studio Web SignBridge — CC BY 4.0 (dengan Consent) | $960$ rekaman tambahan baru (total gabungan $\ge 3.000$ sampel) | **0 video / 0 rekaman fisik** | **`NOT AVAILABLE`** (Membutuhkan perekaman fisik oleh 3 signer manusia; dilarang dipenuhi dengan data sintetis) |
| **2. IMAGE** | **BISINDO Alphabet Image Data** dari Mendeley (kelas `A–Z`) | BISINDO Indonesian Sign Language: Alphabet Image Data (v1) | Mendeley Data (`doi:10.17632/ywnjpbcz8m.1`, Samuel Ady Sanjaya, 2024) — CC BY 4.0 | $26$ kelas abjad (`A–Z`) | **4.466 citra RGB** ($224 \times 224 \times 3$, `29.054.822 B`, `0` rusak) tersebar lengkap di **26 kelas `A–Z`** (165–174 citra/kelas) pada `data/raw/image/bisindo_alphabet/<A..Z>/` | **TERPENUHI (SELESAI DIUNDUH & TERVALIDASI)** *(Varian RGB $224 \times 224$ telah terunduh penuh 100%; varian biner & foto kamera mentah 8 GB tidak diunduh; preprocessing hand crop belum dijalankan sesuai aturan)* |
| **3. AUDIO** | **FLEURS** dengan konfigurasi `id_id` | Google FLEURS (`id_id`) | Hugging Face (`google/fleurs`, config `id_id`) — CC BY 4.0 | Korpus `id_id` ($3.616$ klip total: $2.579$ train, $350$ dev, $687$ test) | **3.616 baris metadata TSV** (`dev.tsv`, `test.tsv`, `train.tsv`) + **350 file `.wav` fisik** (`16.000 Hz`, mono, durasi $4.173,20\text{ dtk}$, `267,10 MB`) telah diunduh & diekstrak dari `audio/dev.tar.gz` (`220,59 MB`) | **SUBSET EKSPERIMEN (PROFIL A — SELESAI DIUNDUH)** *(Split `dev` 350 `.wav` + seluruh 3 TSV telah terunduh dan tervalidasi; arsip `.wav` untuk `train` & `test` belum diunduh)* |
| **3. AUDIO** | **Rekaman kalimat kelas SignBridge** (tidak digantikan oleh FLEURS & metadata CSV bukan file audio) | Rekaman Suara Kelas SignBridge (`id-ID`) | Rekaman Suara Asli Ruang Kelas (`data/audio/wavs/id_001.wav`..`id_060.wav`) | Minimal $60$ berkas `.wav` ucapan kelas nyata | **0 file `.wav`** di disk *(hanya ada 60 baris teks di `data/audio/metadata.csv`)* | **`NOT AVAILABLE`** (`metadata.csv` bukan file audio; FLEURS bukan pengganti rekaman kelas; gelombang sinus sintetis dilarang) |
| **3. AUDIO** *(Tambahan)* | `fil_ph` hanya sebagai tambahan eksperimen FSL (tidak menggantikan `id_id`) | Google FLEURS (`fil_ph`) & Rekaman Kelas `fil-PH` | Hugging Face (`google/fleurs`, config `fil_ph`) — CC BY 4.0 | Opsional (tambahan eksperimen FSL) | **0 file `.wav`** di disk *(hanya 24 baris teks di `data/audio/metadata_fil.csv`)* | **OPSIONAL / BELUM DIUNDUH** |
| **4. TEXT** | **Tatoeba Indonesian** (bukan pasangan gloss-to-sentence) | Tatoeba Indonesian (`ind`) | Tatoeba Resmi (`https://downloads.tatoeba.org/exports/per_language/ind/ind_sentences.tsv.bz2`) — CC BY 2.0 FR | Korpus kalimat Bahasa Indonesia (`ind`) | **28.418 kalimat Bahasa Indonesia** telah diunduh secara fisik di `data/text/tatoeba/ind_sentences.tsv` (`1.389.405 B`) | **SESUAI & SELESAI DIUNDUH** *(Disimpan sebagai korpus kalimat murni; tidak diklaim sebagai pasangan gloss-to-sentence)* |
| **4. TEXT** | **Kalimat kelas SignBridge** | `data/text/kelas_sentences.txt` | Repository Lokal SignBridge — Internal Tim | $200$ kalimat ruang kelas | **200 kalimat** tersedia secara fisik (`14.830 B`) | **SESUAI & TERSEDIA** (Dipertahankan utuh) |
| **4. TEXT** | **Pertahankan `train.tsv`, `val.tsv`, dan `test_manual.tsv` yang sudah ada** | `data/text/train.tsv`, `val.tsv`, `test_manual.tsv` | Repository Lokal SignBridge — Internal Tim | `170` train, `30` val, `105` test manual | **170** pasangan (`train.tsv`), **30** pasangan (`val.tsv`), **105** pasangan (`test_manual.tsv`, 0% overlap) | **SESUAI & TERSEDIA** (Dipertahankan 100% tanpa perubahan) |

---

## 2. Inventaris Fisik Direktori `data/` Saat Ini (Pasca-Eksekusi Tahap 1–4)

| No | Path Berkas / Direktori Fisik | Ukuran Aktual (Byte) | Jumlah Baris / Sampel Aktual | Status Fisik |
| :--- | :--- | :---: | :---: | :--- |
| 1 | `data/.gitkeep` | `0 B` | 0 | Penanda direktori (`git status` bersih) |
| 2 | `data/phonology.csv` | `530 B` | 33 baris (1 header + **32 gloss**) | Tersedia & utuh (`git status` bersih) |
| 3 | `data/PHONOLOGY_GUIDE.md` | `3.608 B` | 73 baris | Tersedia & utuh (`git status` bersih) |
| 4 | `data/bridge/concepts.csv` | `3.586 B` | 33 baris (1 header + **32 konsep C01–C32**) | Tersedia & utuh (`git status` bersih) |
| 5 | `data/audio/metadata.csv` | `5.334 B` | 61 baris (1 header + **60 baris teks**) | Hanya metadata teks (`0` file `.wav` rekaman kelas — `NOT AVAILABLE`) |
| 6 | `data/audio/metadata_fil.csv` | `1.849 B` | 25 baris (1 header + **24 baris teks**) | Hanya metadata teks (`0` file `.wav` rekaman kelas — `NOT AVAILABLE`) |
| 7 | `data/text/kelas_sentences.txt` | `14.830 B` | **200 kalimat** | Tersedia & dipertahankan utuh (`git status` bersih) |
| 8 | `data/text/train.tsv` | `22.565 B` | 171 baris (1 header + **170 pasangan**) | Tersedia & dipertahankan utuh (`git status` bersih) |
| 9 | `data/text/val.tsv` | `4.483 B` | 31 baris (1 header + **30 pasangan**) | Tersedia & dipertahankan utuh (`git status` bersih) |
| 10 | `data/text/test_manual.tsv` | `6.727 B` | 106 baris (1 header + **105 pasangan**) | Tersedia & dipertahankan utuh (`git status` bersih) |
| 11 | `data/text/tatoeba/ind_sentences.tsv.bz2` | `330.738 B` | Arsip terkompresi (`28.418` baris) | **Tahap 1 (Text)** — Diunduh dari `downloads.tatoeba.org` |
| 12 | `data/text/tatoeba/ind_sentences.tsv` | `1.389.405 B` | **28.418 kalimat Bahasa Indonesia** | **Tahap 1 (Text)** — Diekstrak & tervalidasi SHA-256 |
| 13 | `data/audio/fleurs/id_id/dev.tsv`, `test.tsv`, `train.tsv` | `2.108.233 B` | **3.616 baris metadata** (`350` dev + `687` test + `2.579` train) | **Tahap 2 (Audio)** — Diunduh dari `huggingface.co/datasets/google/fleurs` |
| 14 | `data/audio/fleurs/id_id/audio/dev.tar.gz` | `220.586.217 B` (~210,37 MB) | Arsip `350` berkas `.wav` | **Tahap 2 (Audio)** — Diunduh & tervalidasi SHA-256 |
| 15 | `data/audio/fleurs/id_id/audio/dev/*.wav` | `267.099.980 B` (~254,73 MB) | **350 berkas `.wav`** (`16.000 Hz`, mono, durasi **4.173,20 dtk**) | **Tahap 2 (Audio)** — Diekstrak & 100% cocok dengan `dev.tsv` |
| 16 | `data/raw/image/bisindo_alphabet/<A..Z>/` | `29.054.822 B` (~27,71 MB) | **4.466 citra RGB** ($224 \times 224 \times 3$) di **26 kelas (`A–Z`)** | **Tahap 3 (Image)** — Diunduh dari Mendeley (`doi:10.17632/ywnjpbcz8m.1`), `0` rusak |
| 17 | `data/raw/video/fsl_105/labels.csv`, `train.csv`, `test.csv` | `75.628 B` | **105 kelas FSL**, **1.704 baris train**, **426 baris test** (`2.130` klip) | **Tahap 4 (Video)** — Diunduh dari Mendeley (`doi:10.17632/48y2y99mb9.2`) |
| 18 | `data/raw/video/fsl_105/clips.zip` | `379.081.783 B` (~361,52 MB) | Arsip `2.130` berkas video `.MOV` | **Tahap 4 (Video)** — Diunduh & lulus uji `CRC-32` (`testzip() == None`) |
| 19 | `data/raw/video/fsl_105/clips/<0..104>/*.MOV` | `390.121.532 B` (~372,05 MB) | **2.130 berkas video `.MOV`** di **105 kelas** (`0` rusak / 0-byte) | **Tahap 4 (Video)** — Diekstrak & 100% cocok dengan `train.csv` + `test.csv` |
| 20 | `data/raw/video/wlasl_300/WLASL_v0.3.json` & `WLASL_300_manifest.json` | `14.147.179 B` (~13,49 MB) | `2.000` gloss penuh (`21.083` entri) & **300 gloss target (`5.117` entri)** | **Tahap 4 (Video)** — Manifest resmi `dxli94/WLASL` terunduh (berkas video `.mp4` `BLOCKED` butuh Kaggle API) |
| 21 | `data/DATASET_DOWNLOAD_MANIFEST.csv` | Terbarui | **25 baris manifes** (Tahap 1 s/d Tahap 4) | Rekapitulasi ukuran byte, SHA-256, lisensi, dan status kepatuhan |
