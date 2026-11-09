# Laporan Akuisisi & Validasi Dataset SignBridge (`docs/DATASET_DOWNLOAD_REPORT.md`)

**Proyek**: SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Working Directory**: `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif**: `feature/dataset-acquisition`  
**Tanggal Pembaruan**: 7 November 2026

---

## 1. Ringkasan Eksekutif

Dokumen ini mencatat hasil akuisisi dan validasi akhir (*Final Validation*) secara fisik dan kriptografis (SHA-256) untuk keempat modalitas yang telah dieksekusi:
1. **Tahap 1 — Modality Text**: Unduhan penuh **Tatoeba Indonesian (`ind`)** (**28.418 kalimat**) + verifikasi keutuhan `train.tsv` (170), `val.tsv` (30), `test_manual.tsv` (105), dan `kelas_sentences.txt` (200).
2. **Tahap 2 — Modality Audio**: Unduhan resmi **Google FLEURS (`id_id`)** dari Hugging Face (`dev.tsv` 350 baris, `test.tsv` 687 baris, `train.tsv` 2.579 baris — total metadata **3.616 klip**, serta arsip audio fisik `audio/dev.tar.gz` berisi **350 berkas `.wav` 16 kHz mono**, durasi total **4.173,20 detik**). Rekaman suara kelas mandiri (`data/audio/wavs/*.wav`) berstatus **`NOT AVAILABLE`**.
3. **Tahap 3 — Modality Image**: Unduhan resmi **BISINDO Indonesian Sign Language: Alphabet Image Data** (Versi 1, `doi:10.17632/ywnjpbcz8m.1`, Samuel Ady Sanjaya, 2024) dari **Mendeley Data** ke `data/raw/image/bisindo_alphabet/<A..Z>/`. Seluruh **26 kelas (`A–Z`)** tersedia lengkap dengan total **4.466 citra RGB berukuran $224 \times 224 \times 3$** (`29.054.822 byte` / ~27,71 MB), **0 gagal unduh**, dan **0 berkas rusak**.
4. **Tahap 4 — Modality Video**:
   - **FSL-105 (`doi:10.17632/48y2y99mb9.2`, CC BY 4.0, Isaiah Jassen Tupal, 2023)**: Unduhan penuh 100% dari **Mendeley Data** ke `data/raw/video/fsl_105/`, mencakup `labels.csv` (**105 kelas**), `train.csv` (**1.704 baris**), `test.csv` (**426 baris**), arsip `clips.zip` (`379.081.783 byte` / 361,52 MB, `CRC-32` 100% utuh), serta ekstraksi seluruh **2.130 berkas video `.MOV`** (`390.121.532 byte` / 372,05 MB) di `data/raw/video/fsl_105/clips/<0..104>/` dengan **0 berkas rusak / 0-byte**.
   - **WLASL-300 (`dxli94/WLASL`, Li et al., WACV 2020)**: Unduhan manifest resmi `WLASL_v0.3.json` (`11.932.637 byte`, 2.000 gloss / 21.083 entri) dan ekstraksi manifest subset target `WLASL_300_manifest.json` (`2.214.542 byte`, **300 gloss / 5.117 entri video**). Berkas video fisik WLASL-300 (`Kaggle: risangbaskoro/wlasl-processed`) dan **WL-BISINDO** (`Kaggle: glennleonali/wl-bisindo`, ~1.600 video, 32 gloss) berstatus **`BLOCKED`** karena ketiadaan kredensial autentikasi `~/.kaggle/kaggle.json` pada mesin lokal.
   - **SignBridge-Kelas** ($3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ klip}$, durasi $\approx 2,6\text{ detik}$, target gabungan $\ge 3.000$ sampel): Berstatus **`NOT AVAILABLE`** karena membutuhkan perekaman kamera fisik oleh penutur manusia dan dilarang menggunakan data sintetis.

---

## 2. Validasi Kriptografis & Fisik — Tahap 1: Modality Text

| No | Path Berkas | Tersedia Fisik | Ukuran Aktual (Byte) | Jumlah Baris / Entri | SHA-256 (Disk) | Status Validasi |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | `data/text/tatoeba/ind_sentences.tsv.bz2` | **Ya** (`True`) | `330.738 B` | Arsip (`28.418` baris) | `661f416c60401127560043fa7a464fd25d4c5377f9200597fa2130c34324b46a` | **VALID — Arsip Asli Utuh** |
| 2 | `data/text/tatoeba/ind_sentences.tsv` | **Ya** (`True`) | `1.389.405 B` | **28.418 baris** | `67b56a16f2a0c9ec5d7f48edd02165ab69592b1667f3bfa44e9c4252f9ab7e1b` | **VALID — 100% Identik Hasil Dekompresi `.bz2`** |
| 3 | `data/text/kelas_sentences.txt` | **Ya** (`True`) | `14.830 B` | **200 kalimat** | `6fddbfd1cc90572be56b229cec3cd988c13097ab7158faf7982bcecbae020686` | **VALID — Tidak Berubah (`git status` bersih)** |
| 4 | `data/text/train.tsv` | **Ya** (`True`) | `22.565 B` | 171 baris (**170 pasangan**) | `508de2272c67c93f06de654f106aee3772c0fef23e611a7463b5fbf5ac97348c` | **VALID — Tidak Berubah (`git status` bersih)** |
| 5 | `data/text/val.tsv` | **Ya** (`True`) | `4.483 B` | 31 baris (**30 pasangan**) | `96a8d589063cb2fc5ec08cb2914d0769a09994c19bd64be45b0ef587ec881c02` | **VALID — Tidak Berubah (`git status` bersih)** |
| 6 | `data/text/test_manual.tsv` | **Ya** (`True`) | `6.727 B` | 106 baris (**105 pasangan**) | `1f610faa6339117b9517ed04a599bd08f6ed28babf22292fe548bc83c8553d82` | **VALID — Tidak Berubah (`git status` bersih)** |

---

## 3. Validasi Kriptografis & Fisik — Tahap 2: Modality Audio (`Google FLEURS id_id`)

| No | Path Berkas / Direktori | Tersedia Fisik | Ukuran Aktual (Byte) | Jumlah Baris / Berkas | SHA-256 (Disk) | Status Validasi & Keterangan |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | `data/audio/fleurs/id_id/dev.tsv` | **Ya** (`True`) | `200.236 B` | **350 baris** | `8377bf6d8738491b7b0672de47e42123ce07b069a0db920ab6300e3ecce02c18` | **VALID — Metadata Split Dev `id_id`** |
| 2 | `data/audio/fleurs/id_id/test.tsv` | **Ya** (`True`) | `408.796 B` | **687 baris** | `824cad6367283d95f545911eec051c488c182baa13a63227c6330af3c8f80741` | **VALID — Metadata Split Test `id_id`** |
| 3 | `data/audio/fleurs/id_id/train.tsv` | **Ya** (`True`) | `1.499.201 B` | **2.579 baris** | `5a4285ed00caff57f9dce155c7c1f636cfb9c322a795d55e04d98d4b7696fcec` | **VALID — Metadata Split Train `id_id`** |
| 4 | `data/audio/fleurs/id_id/audio/dev.tar.gz` | **Ya** (`True`) | `220.586.217 B` (~210,37 MB) | Arsip `350` file `.wav` | `74e5f1c8676a321dc4c34944b171846d40923dabe765a767d8dbc2f56cac3142` | **VALID — Arsip Audio Resmi (`id_id/audio/dev.tar.gz`)** |
| 5 | `data/audio/fleurs/id_id/audio/dev/*.wav` | **Ya** (`True`) | `267.099.980 B` (~254,73 MB) | **350 file `.wav`** (durasi **4.173,20 dtk**) | Terverifikasi 100% dari `dev.tar.gz` | **VALID — 350/350 cocok dengan `dev.tsv` (`16.000 Hz`, `mono`, `IEEE float 32-bit`, `0` file rusak)** |
| 6 | `data/audio/metadata.csv` | **Ya** (`True`) | `5.334 B` | 61 baris (**60 baris teks**) | `15025bf52801864631aaf90df9ebfc79d4863af955f338930d2dffee2e47460c` | **HANYA METADATA TEKS** (Tidak berubah vs `HEAD`; file `.wav` rekaman kelas berstatus **`NOT AVAILABLE`**) |
| 7 | `data/audio/metadata_fil.csv` | **Ya** (`True`) | `1.849 B` | 25 baris (**24 baris teks**) | `72cb11744391bbe0497ed0c5a04ce5018d97778a90014de5ebfc6c8528536b6d` | **HANYA METADATA TEKS** (Tidak berubah vs `HEAD`; file `.wav` rekaman kelas berstatus **`NOT AVAILABLE`**) |

---

## 4. Validasi Kriptografis & Fisik — Tahap 3: Modality Image (`BISINDO Alphabet Image Data`)

### 4.1 Verifikasi Sumber Resmi, Versi, Lisensi, dan Atribusi
- **Nama Dataset Resmi**: *BISINDO Indonesian Sign Language: Alphabet Image Data*
- **Platform & Identifier**: Mendeley Data — `id: ywnjpbcz8m`, **Versi 1** (`version: 1`)
- **DOI Resmi**: `10.17632/ywnjpbcz8m.1`
- **URL Resmi**: `https://data.mendeley.com/datasets/ywnjpbcz8m/1`
- **Tanggal Publikasi**: 18 Oktober 2024 (`2024-10-18T16:23:32.042Z`)
- **Penulis / Kontributor**: **Samuel Ady Sanjaya** (`profile_id: b61817e4-7738-4947-a45a-7d5c4cc09752`)
- **Lisensi Resmi**: **Creative Commons Attribution 4.0 International (CC BY 4.0)** (`http://creativecommons.org/licenses/by/4.0`)
  - Ketentuan: Bebas dibagikan, disalin, dan diadaptasi dengan syarat mencantumkan atribusi penulis (*Samuel Ady Sanjaya, 2024, doi:10.17632/ywnjpbcz8m.1*), menyertakan tautan lisensi CC BY 4.0, serta menyebutkan jika ada perubahan yang dilakukan.

### 4.2 Pemisahan Varian Berkas di Repository Mendeley vs Berkas yang Diunduh
Katalog resmi Mendeley (`mendeley_metadata.json`, `16.923` total entri berkas di 79 folder) memuat 4 varian representasi dari pengumpulan data yang sama:
1. **Varian 1 — Compressed RGB Images $224 \times 224$ (26 Folder Kelas `A–Z`)** $\rightarrow$ **BERHASIL DIUNDUH 100% (`4.466` citra RGB, `0` gagal, `0` rusak)**:
   - Seluruh **4.466 citra RGB** telah diunduh ke `data/raw/image/bisindo_alphabet/<A..Z>/` dengan total ukuran aktual **29.054.822 byte (~27,71 MB)**.
   - Setiap berkas diverifikasi satu per satu terhadap nilai `sha256_hash` dan `size` resmi dari Mendeley API (`4.466/4.466` cocok 100%).
2. **Varian 2 — Binary Silhouette Images $224 \times 224$ (26 Folder, `3.846` berkas, `~45,65 MB`)** $\rightarrow$ **TIDAK DIUNDUH (Tidak diperlukan oleh pipeline RGB SignBridge)**.
3. **Varian 3 — Uncompressed Raw Camera Photos (26 Folder, `4.773` berkas termasuk `4` berkas macOS `._*` AppleDouble 4 KB dan `10` berkas `.heic`, `~8.077,45 MB`)** $\rightarrow$ **TIDAK DIUNDUH (Profil A menggunakan varian RGB terkompresi $224 \times 224$ resmi dari dataset yang sama)**.
4. **Varian 4 — Chain Code Text Encodings (1 Folder, `3.842` berkas `.txt`, `~5,71 MB`)** $\rightarrow$ **TIDAK DIUNDUH (Bukan berkas citra)**.

### 4.3 SHA-256 Berkas Penting & Manifes Modality Image

| No | Path Berkas Penting | Ukuran Aktual (Byte) | Jumlah Entri | SHA-256 | Keterangan |
| :--- | :--- | :---: | :---: | :--- | :--- |
| 1 | `data/raw/image/bisindo_alphabet/mendeley_metadata.json` | `12.888.179 B` | `16.923` entri API | `5e7a2412cf3394025a77429215f74a6430948ffbe6a02ebebe74a8a07c5cce40` | Katalog JSON resmi dari Mendeley Public API |
| 2 | `data/raw/image/bisindo_alphabet/file_hashes_sha256.csv` | `814.357 B` | `4.466` baris citra | `466fa84eab63454f7e8c89f3c2916a514e558fffcad44693c0c35c2ea884bdec` | Daftar SHA-256, ukuran byte, dan dimensi seluruh 4.466 citra yang diunduh |
| 3 | `data/raw/image/bisindo_alphabet/download_verification_summary.json` | `2.445 B` | `26` kelas (`A–Z`) | `18a09e8ea0de5880f4e52e89aef1e9950976fd3b26c9e641862a9a4eff816804` | Ringkasan verifikasi unduhan & distribusi kelas |

### 4.4 Tabel Distribusi Aktual Kelas A–Z (`data/raw/image/bisindo_alphabet/<A..Z>/`)

Seluruh **26 kelas (`A` s/d `Z`)** telah diperiksa secara fisik. Setiap gambar berhasil dibuka, memiliki header JPEG valid (`SOI 0xFFD8` & `SOF0/SOF2`), dimensi tepat **$224 \times 224 \times 3$ (RGB)**, dan **0 gambar rusak**:

| Kelas | Path Direktori | Jumlah Gambar Aktual | Ukuran Aktual (Byte) | Dimensi Terverifikasi | Gambar Rusak | Catatan Anomali Penamaan Asli Mendeley |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **A** | `data/raw/image/bisindo_alphabet/A/` | **165** | `1.119.016 B` | `224x224x3` (100%) | 0 | — |
| **B** | `data/raw/image/bisindo_alphabet/B/` | **169** | `1.123.436 B` | `224x224x3` (100%) | 0 | — |
| **C** | `data/raw/image/bisindo_alphabet/C/` | **169** | `1.034.845 B` | `224x224x3` (100%) | 0 | Terdapat 1 file berprefiks `D_` (`D_Bebas_Redmi_Note 12 Pro.jpg`) dari folder asli Mendeley |
| **D** | `data/raw/image/bisindo_alphabet/D/` | **170** | `1.145.859 B` | `224x224x3` (100%) | 0 | — |
| **E** | `data/raw/image/bisindo_alphabet/E/` | **169** | `1.059.931 B` | `224x224x3` (100%) | 0 | — |
| **F** | `data/raw/image/bisindo_alphabet/F/` | **173** | `1.137.105 B` | `224x224x3` (100%) | 0 | — |
| **G** | `data/raw/image/bisindo_alphabet/G/` | **173** | `1.085.416 B` | `224x224x3` (100%) | 0 | — |
| **H** | `data/raw/image/bisindo_alphabet/H/` | **173** | `1.176.225 B` | `224x224x3` (100%) | 0 | — |
| **I** | `data/raw/image/bisindo_alphabet/I/` | **173** | `1.056.053 B` | `224x224x3` (100%) | 0 | — |
| **J** | `data/raw/image/bisindo_alphabet/J/` | **169** | `1.008.876 B` | `224x224x3` (100%) | 0 | — |
| **K** | `data/raw/image/bisindo_alphabet/K/` | **173** | `1.132.032 B` | `224x224x3` (100%) | 0 | — |
| **L** | `data/raw/image/bisindo_alphabet/L/` | **172** | `1.054.994 B` | `224x224x3` (100%) | 0 | Terdapat 2 file berprefiks `E_` (`E_Baju_Apple_Iphone 11.jpg`, `E_Bebas_Apple_Iphone 11.jpg`) dari folder asli |
| **M** | `data/raw/image/bisindo_alphabet/M/` | **173** | `1.218.898 B` | `224x224x3` (100%) | 0 | — |
| **N** | `data/raw/image/bisindo_alphabet/N/` | **173** | `1.207.744 B` | `224x224x3` (100%) | 0 | — |
| **O** | `data/raw/image/bisindo_alphabet/O/` | **173** | `1.111.957 B` | `224x224x3` (100%) | 0 | Terdapat 3 file berprefiks angka `0_` (`0_BEBAS_Apple_Iphone 12.JPG`, dll.) untuk huruf `O` |
| **P** | `data/raw/image/bisindo_alphabet/P/` | **172** | `1.162.542 B` | `224x224x3` (100%) | 0 | — |
| **Q** | `data/raw/image/bisindo_alphabet/Q/` | **173** | `1.187.760 B` | `224x224x3` (100%) | 0 | — |
| **R** | `data/raw/image/bisindo_alphabet/R/` | **171** | `1.074.184 B` | `224x224x3` (100%) | 0 | — |
| **S** | `data/raw/image/bisindo_alphabet/S/` | **173** | `1.178.613 B` | `224x224x3` (100%) | 0 | — |
| **T** | `data/raw/image/bisindo_alphabet/T/` | **173** | `1.145.194 B` | `224x224x3` (100%) | 0 | — |
| **U** | `data/raw/image/bisindo_alphabet/U/` | **173** | `1.074.214 B` | `224x224x3` (100%) | 0 | — |
| **V** | `data/raw/image/bisindo_alphabet/V/` | **172** | `1.077.810 B` | `224x224x3` (100%) | 0 | Terdapat 1 file berprefiks `Y_` (`Y_Polos Gelap_Iphone_14 Pro.jpg`) dari folder asli |
| **W** | `data/raw/image/bisindo_alphabet/W/` | **170** | `1.159.501 B` | `224x224x3` (100%) | 0 | — |
| **X** | `data/raw/image/bisindo_alphabet/X/` | **174** | `1.145.926 B` | `224x224x3` (100%) | 0 | — |
| **Y** | `data/raw/image/bisindo_alphabet/Y/` | **174** | `1.152.633 B` | `224x224x3` (100%) | 0 | — |
| **Z** | `data/raw/image/bisindo_alphabet/Z/` | **174** | `1.024.058 B` | `224x224x3` (100%) | 0 | Terdapat 1 file berprefiks `S_` (`S_Baju_Iphone_14 Pro.jpg`) dari folder asli |
| **TOTAL** | **26 Kelas (`A–Z`)** | **4.466 gambar** | **`29.054.822 B`** (~27,71 MB) | **100% `224x224x3` RGB** | **0** | Distribusi ekstensi: `.jpg` (`3.842`), `.jpeg` (`312`), `.JPG` (`312`) |

### 4.5 Keterbatasan Dataset yang Ditemukan Secara Faktual
1. **Ketidaksamaan Kecil Jumlah Sampel Antar Kelas**: Jumlah gambar per kelas berkisar antara **165** (kelas `A`) hingga **174** (kelas `X`, `Y`, `Z`), dengan rata-rata $171,77$ gambar per kelas.
2. **Anomali Penamaan Berkas dari Kontributor Asli (8 dari 4.466 Berkas)**:
   - Sebagaimana tercatat pada tabel di atas, terdapat 5 berkas yang memiliki prefiks huruf berbeda dari nama foldernya (`D_` di folder `C`, dua `E_` di folder `L`, `Y_` di folder `V`, `S_` di folder `Z`) serta 3 berkas di folder `O` yang menggunakan angka `0_` alih-alih huruf `O_`. Sesuai aturan untuk tidak mengubah dataset asli, berkas-berkas tersebut disimpan apa adanya seperti di Mendeley Data dan dicatat agar dapat disaring pada tahap preprocessing nantinya.
3. **Belum Dilakukan Preprocessing Hand Crop (`+25%` Margin)**:
   - Sesuai instruksi Tahap 3 (*"Jangan menjalankan training atau preprocessing"*), seluruh 4.466 citra disimpan murni di `data/raw/image/bisindo_alphabet/<A..Z>/` dan belum diproses ke `data/fingerspelling_crops/`.

---

## 5. Validasi Kriptografis & Fisik — Tahap 4: Modality Video

### 5.1 Verifikasi Sumber Resmi, Versi, Lisensi, dan Atribusi Dataset Video

| ID | Dataset | Sumber Resmi & Identifier | Penulis / Kontributor | Lisensi Resmi | Status Akuisisi Fisik |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **V3** | **FSL-105** (*FSL-105: A dataset for recognizing 105 Filipino sign language videos*, Versi 2) | Mendeley Data: `doi:10.17632/48y2y99mb9.2` (`https://data.mendeley.com/datasets/48y2y99mb9/2`, publikasi 19 Mei 2023) | **Isaiah Jassen Tupal** | **CC BY 4.0** (`http://creativecommons.org/licenses/by/4.0`) | **TERPENUHI 100%** (`2.130` video `.MOV` & `105` kelas terunduh dan diekstrak penuh) |
| **V2** | **WLASL-300** (*Word-Level American Sign Language*, 300 Glosses Pretraining) | GitHub Resmi: `dxli94/WLASL` (`WLASL_v0.3.json`) & Mirror Video: Kaggle `risangbaskoro/wlasl-processed` | **Dongxu Li et al.** (WACV 2020) | **Academic Non-Commercial** (C-UDA) | **MANIFEST TERUNDUH (`5.117` entri / `300` gloss); VIDEO FISIK `BLOCKED`** (Butuh kredensial Kaggle API `~/.kaggle/kaggle.json` & tautan mentah memuat 1.604 YouTube + 382 `.swf` mati) |
| **V1** | **WL-BISINDO** (*Word-Level BISINDO*, 32 Glosses) | Kaggle: `glennleonali/wl-bisindo` (`https://www.kaggle.com/datasets/glennleonali/wl-bisindo`) | **Glenn Leonali** | **CC BY 4.0 / Akademik** | **`BLOCKED`** (Membutuhkan kredensial autentikasi `~/.kaggle/kaggle.json` yang belum terpasang di mesin lokal) |
| **V4** | **SignBridge-Kelas** (Rekaman Mandiri 3 Signer $\times$ 32 Gloss $\times$ 10 Take = 960 Klip, $\approx 2,6\text{ dtk}$) | Akuisisi Kamera Fisik Mandiri Tim SignBridge | **Tim SignBridge** | **Internal Tim / CC BY 4.0** | **`NOT AVAILABLE`** (Wajib perekaman manusia nyata; dilarang membuat video/keypoint sintetis) |

### 5.2 Tabel Validasi Kriptografis SHA-256 & Ukuran Aktual — Tahap 4: Modality Video

| No | Path Berkas / Direktori | Tersedia Fisik | Ukuran Aktual (Byte) | Jumlah Entri / Berkas | SHA-256 (Disk) | Status Validasi & Keterangan |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| 1 | `data/raw/video/fsl_105/mendeley_fsl105_metadata.json` | **Ya** (`True`) | `5.409 B` | Metadata API v2 | `3b541ee18d6944ad80ca7b2919e171e4cfc522a122123324c5434c285f48e568` | **VALID — Metadata Resmi Mendeley Data (`48y2y99mb9` v2)** |
| 2 | `data/raw/video/fsl_105/labels.csv` | **Ya** (`True`) | `2.022 B` | **105 kelas FSL** (`0`..`104`, 10 kategori) | `6074947fc905eecf20a341388551aeab0b32341928778a1f87d6c3bca073b630` | **VALID — 100% Cocok dengan SHA-256 Mendeley API** |
| 3 | `data/raw/video/fsl_105/train.csv` | **Ya** (`True`) | `58.851 B` | **1.704 baris klip** | `861a76cae835e284ac76ef37dc077ae0b6c793beb9c378eda1fce5f408dc609f` | **VALID — 100% Cocok dengan SHA-256 Mendeley API** |
| 4 | `data/raw/video/fsl_105/test.csv` | **Ya** (`True`) | `14.755 B` | **426 baris klip** | `3dd8e83294a63b7c02fd1ee3ebd1d179aa4b0437ff9cfb3febab5d0e1da0ccf7` | **VALID — 100% Cocok dengan SHA-256 Mendeley API** |
| 5 | `data/raw/video/fsl_105/clips.zip` | **Ya** (`True`) | `379.081.783 B` (361,52 MB) | Arsip `2.130` video `.MOV` | `c048c0820be1621101dfedeabb76a9fbfca76ed2868eebe23b4cb90d5c748463` | **VALID — 100% Cocok dengan SHA-256 Mendeley API & Lulus Uji `CRC-32` (`testzip() == None`)** |
| 6 | `data/raw/video/fsl_105/clips/<0..104>/*.MOV` | **Ya** (`True`) | `390.121.532 B` (372,05 MB) | **2.130 berkas `.MOV`** di **105 folder kelas** (`20–21` video/kelas) | Terverifikasi dari `clips.zip` | **VALID — 2.130/2.130 path di `train.csv` (`1.704`) + `test.csv` (`426`) cocok 100%; `0` berkas 0-byte/rusak** |
| 7 | `data/raw/video/wlasl_300/WLASL_v0.3.json` | **Ya** (`True`) | `11.932.637 B` (11,38 MB) | `2.000` gloss (`21.083` entri video) | `31ba5a5c421bdbff87494ee22ca6d4e276a8dfac44f43cc9a58b76ed1c4cd684` | **VALID — Manifest Resmi `dxli94/WLASL`** |
| 8 | `data/raw/video/wlasl_300/WLASL_300_manifest.json` | **Ya** (`True`) | `2.214.542 B` (2,11 MB) | **300 gloss** (**5.117 entri video**: `3.549` train, `900` val, `668` test) | `37854fbb69078b025c29c7441ead4bd6d20a7f2c949b9dd51e4a608c06c7ff55` | **VALID — Manifest Target WLASL-300** *(URL: `3.099` direct MP4, `1.604` YouTube, `382` SWF, `32` lainnya)* |
| 9 | `data/phonology.csv` | **Ya** (`True`) | `530 B` | 33 baris (**32 gloss BISINDO**) | `a3c6bd8d2c683eb6efbe41ec3f1bdbf3835fa43902a1ee26e81fc83d82780bb4` | **VALID — Tidak Berubah (`git status` bersih)** |
| 10 | `data/bridge/concepts.csv` | **Ya** (`True`) | `3.586 B` | 33 baris (**32 konsep C01–C32**) | `dc4a55f2341b66c620ba71b8322b7d72bd1e59177ab2660c4c3979871894480b` | **VALID — Tidak Berubah (`git status` bersih)** |
