# Katalog Sumber Resmi Dataset Multimodal SignBridge (`docs/DATASET_SOURCE_CATALOG.md`)

**Proyek**: SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Branch**: `feature/dataset-acquisition`  
**Tanggal Pembaruan**: 7 November 2026 (Terkoreksi Sesuai Persyaratan Modul Asli SignBridge)

---

## 1. Katalog Sumber Dataset Wajib & Tambahan (Terverifikasi)

Seluruh sumber di bawah ini telah diverifikasi terhadap persyaratan modul asli **SignBridge** dan aturan keaslian data (tanpa klaim sintetis dan tanpa penggantian sepihak):

| ID | Modalitas | Persyaratan Modul | Dataset yang Dipilih | Sumber Resmi & Identifier | Lisensi | Target Modul | Estimasi Ukuran Download |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **V1** | **Video** | Word-level BISINDO (32 gloss) | **WL-BISINDO** | Kaggle: `glennleonali/wl-bisindo` (`https://www.kaggle.com/datasets/glennleonali/wl-bisindo`) | CC BY 4.0 / Akademik | $\approx 1.600$ video, $32$ gloss | $1,8 - 2,5\text{ GB}$ |
| **V2** | **Video** | Pretraining Lintas Bahasa (300 gloss) | **WLASL-300** | GitHub Resmi: `dxli94/WLASL` (`WLASL_v0.3.json`) & Mirror Kaggle: `risangbaskoro/wlasl-processed` | Akademik Non-Komersial (C-UDA) | $\approx 4.000 - 5.000$ video (**5.117 entri** di `WLASL_300_manifest.json`), $300$ gloss | **11,38 MB** (Manifest JSON terunduh); $3,8 - 4,8\text{ GB}$ (Video penuh via Kaggle `BLOCKED`) |
| **V3** | **Video** | Eksperimen Lintas Negara BISINDO–FSL | **FSL-105** | Mendeley Data: `doi:10.17632/48y2y99mb9.2` (`https://data.mendeley.com/datasets/48y2y99mb9/2`, Isaiah Jassen Tupal, 2023) | CC BY 4.0 | **2.130 video `.MOV`** (`1.704` train + `426` test), **105 kelas FSL** | **379.081.783 B** (`clips.zip` ~361,52 MB) / **390.121.532 B** (terekstrak ~372,05 MB) — **TERUNDUH 100%** |
| **V4** | **Video** | Rekaman Tambahan Mandiri & Gabungan `SignBridge-Kelas` | **SignBridge-Kelas (Rekaman Kamera Nyata)** | Akuisisi Mandiri Tim (3 signer baru $\times 32$ gloss $\times 10$ take, durasi $\approx 2,6\text{ detik}$) | Internal Tim / CC BY 4.0 (dengan Consent) | $960$ rekaman baru; total gabungan $\ge 3.000$ data | $400 - 800\text{ MB}$ (`NOT AVAILABLE` di internet; wajib rekaman fisik) |
| **I1** | **Image** | Ejaan Jari Statis BISINDO A–Z | **BISINDO Indonesian Sign Language: Alphabet Image Data (v1)** | Mendeley Data: `doi:10.17632/ywnjpbcz8m.1` (`https://data.mendeley.com/datasets/ywnjpbcz8m/1`, Samuel Ady Sanjaya, 2024) | CC BY 4.0 | $26$ kelas (`A`–`Z`), **4.466 citra RGB** ($224 \times 224 \times 3$) | **29.054.822 B** (~27,71 MB untuk varian RGB terkompresi; ~8,08 GB jika termasuk foto kamera mentah & siluet biner) |
| **A1** | **Audio** | Benchmark & Fine-Tuning ASR Bahasa Indonesia | **Google FLEURS (`id_id`)** | Hugging Face: `google/fleurs` (`https://huggingface.co/datasets/google/fleurs`, config `id_id`) | CC BY 4.0 | Subset `id_id` (train/dev/test, $\approx 2.800$ klip WAV 16 kHz) | $\approx 1,3\text{ GB}$ (penuh) / $\approx 150\text{ MB}$ (subset eksperimen) |
| **A2** | **Audio** | Rekaman Suara Kalimat Kelas SignBridge | **Rekaman Suara Kelas SignBridge (`id-ID`)** | Perekaman Suara Penutur Asli Ruang Kelas (bukan digantikan oleh FLEURS dan bukan nada sinus sintetis) | Internal Tim | Minimal $60$ berkas `.wav` fisik sesuai `data/audio/metadata.csv` | $\approx 15 - 30\text{ MB}$ (`NOT AVAILABLE` secara fisik saat ini) |
| **A3** | **Audio** *(Tambahan)* | Eksperimen Tambahan ASR Filipina (Opsional) | **Google FLEURS (`fil_ph`)** | Hugging Face: `google/fleurs` (config `fil_ph`) | CC BY 4.0 | Tambahan eksperimen FSL (tidak menggantikan `id_id`) | $\approx 1,3\text{ GB}$ (penuh) / $\approx 120\text{ MB}$ (subset) |
| **T1** | **Text** | Korpus Kalimat Bahasa Indonesia | **Tatoeba Indonesian (`ind`)** | Tatoeba Resmi: `https://downloads.tatoeba.org/exports/per_language/ind/ind_sentences.tsv.bz2` | CC BY 2.0 FR | Kalimat monolingual Bahasa Indonesia (`ind`) | $323\text{ KB}$ (`.bz2`) / $1,33\text{ MB}$ (`.tsv`, **28.418 kalimat**) |
| **T2** | **Text** | Kalimat Kelas & Pasangan Gloss-ke-Kalimat SignBridge | **Korpus Teks SignBridge Lokal** | Repository Lokal (`data/text/kelas_sentences.txt`, `train.tsv`, `val.tsv`, `test_manual.tsv`) | Internal Tim / CC BY 4.0 | $200$ kalimat kelas + $170$ train + $30$ val + $105$ test manual | $48,6\text{ KB}$ (Sudah tersedia di repo) |

---

## 2. Catatan Kepatuhan & Batasan Penggunaan Dataset

1. **WLASL-300 Tidak Digantikan oleh WLASL-100**:
   - Target modul untuk pretraining lintas bahasa adalah **WLASL-300** ($\approx 4.000 - 5.000$ video, $300$ gloss). Apabila pada pelaksanaan bertahap (Profil A) hanya sebagian video yang diunduh terlebih dahulu, maka statusnya wajib dicatat sebagai **Subset Eksperimen (Belum Memenuhi Target Penuh Modul)**.
2. **Pemisahan Tegas antara FLEURS (`id_id`), Metadata CSV, dan Rekaman Suara Kelas**:
   - `Google FLEURS (id_id)` adalah korpus benchmark publik, **bukan pengganti** rekaman kalimat kelas SignBridge.
   - Berkas `data/audio/metadata.csv` (60 baris) dan `data/audio/metadata_fil.csv` (24 baris) hanya berisi teks daftar kalimat/metadata, **bukan** berkas audio `.wav` yang sudah tersedia.
3. **Sifat Asli Tatoeba Indonesian (`ind`)**:
   - Berkas resmi `ind_sentences.tsv.bz2` dari Tatoeba hanya berisi `(sentence_id, lang, sentence_text)` dalam Bahasa Indonesia (**28.418 kalimat**). Dataset ini **bukan** pasangan `gloss-to-sentence` asli dan tidak boleh diklaim sebagai pasangan anotasi gloss manusia.
4. **Rekaman Tambahan 960 Klip (`SignBridge-Kelas`)**:
   - Persyaratan modul mencakup $3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ klip}$ (durasi $\approx 2,6\text{ detik}$) untuk mencapai total gabungan $\ge 3.000$ sampel bersama `WL-BISINDO`. Karena dilarang membuat data sintetis untuk memenuhi target jumlah, komponen rekaman mandiri yang belum direkam secara fisik oleh manusia berstatus **`NOT AVAILABLE`**.
