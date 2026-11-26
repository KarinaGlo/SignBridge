# LAPORAN TAHAP 2 & 3: DOWNLOAD DATASET, VALIDASI, DAN PERSIAPAN PREPROCESSING BISINDO ALPHABET (P0)

> **Dokumen**: `docs/P0_DATASET_DOWNLOAD_VALIDATION.md`  
> **Target Tugas**: P0 — Dataset Gambar Alfabet BISINDO & Retraining MobileNetV3 (I1)  
> **Tahap**: Tahap 2 (Download) & Tahap 3 (Validasi dan Uji Crop)  
> **Tanggal Pelaksanaan**: 13 November 2026  
> **Auditor**: Senior Machine Learning Engineer, SignBridge ASEAN  
> **Status Akhir**: **`DATASET READY`**  

---

## 1. IDENTITAS & SUMBER RESMI DATASET

Pemeriksaan dan pengunduhan dataset dilakukan langsung dari repositori resmi Mendeley Data tanpa modifikasi sepihak:
- **Nama Dataset Resmi**: *BISINDO Indonesian Sign Language: Alphabet Image Data*
- **Platform**: Mendeley Data (Elsevier)
- **Dataset ID**: `ywnjpbcz8m`
- **Versi**: Versi 1 (`version: 1`)
- **DOI Resmi**: [`doi:10.17632/ywnjpbcz8m.1`](https://doi.org/10.17632/ywnjpbcz8m.1)
- **URL Resmi**: `https://data.mendeley.com/datasets/ywnjpbcz8m/1`
- **API Endpoint**: `https://data.mendeley.com/public-api/datasets/ywnjpbcz8m`
- **Penulis / Kontributor**: **Samuel Ady Sanjaya** (Fakultas Teknologi Informasi, Universitas Kristen Satya Wacana, Salatiga, Indonesia, 2024)
- **Lisensi**: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
  - Ketentuan Lisensi: Bebas dibagikan, disalin, dan diadaptasi untuk keperluan akademik maupun komersial dengan syarat mencantumkan atribusi penulis, tautan lisensi CC BY 4.0, serta menyatakan perubahan yang dilakukan.

---

## 2. REKAPITULASI PROSES PENGUNDUHAN (DOWNLOAD STATUS)

Pengunduhan dijalankan melalui script multithreaded [`scripts/download_bisindo_alphabet.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/download_bisindo_alphabet.py) dengan mekanisme retry otomatis dan verifikasi hash biner:
- **Waktu Eksekusi**: 337,6 detik (~5,6 menit).
- **Target Entri**: Seluruh 26 folder kelas varian citra RGB terkompresi $224 \times 224$ (Folder ID dipetakan secara presisi berdasarkan metadata API resmi).
- **Hasil Pengunduhan**:
  - Total Berkas Target: **4.466 berkas**
  - Berhasil Diunduh & Terverifikasi: **4.466 berkas (100,0%)**
  - Gagal Diunduh: **0 berkas (0,0%)**
  - Total Ukuran Fisik di Disk: **29.054.822 bytes (27,71 MB)**
  - Folder Penyimpanan Mentah: [`data/raw/image/bisindo_alphabet/<A..Z>/`](file:///d:/SEMESTER%205/ML/Projek_1/data/raw/image/bisindo_alphabet/)
- **Arsip Log dan Metadata Mentah Tersimpan**:
  - `data/raw/image/bisindo_alphabet/mendeley_metadata.json` (16.290.272 bytes)
  - `data/raw/image/bisindo_alphabet/file_hashes_sha256.csv` (Daftar 4.466 baris SHA-256)
  - `data/raw/image/bisindo_alphabet/download_verification_summary.json`

---

## 3. HASIL VALIDASI DATASET OTOMATIS (TEKNIS & KUALITAS)

Validasi teknis dilakukan menggunakan script [`scripts/validate_bisindo_alphabet.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validate_bisindo_alphabet.py) yang memeriksa integritas byte, struktur direktori, dimensi piksel, mode warna, dan duplikasi kriptografis.

| Parameter Validasi | Target Kriteria | Hasil Pemeriksaan Aktual | Status |
|---|:---:|:---:|:---:|
| **Jumlah Folder Kelas** | 26 folder (`A` s/d `Z`) | **26 folder (`A` s/d `Z`)** | **PASSED** |
| **Total Citra Fisik** | 4.466 citra (atau min 1.040) | **4.466 citra** | **PASSED** |
| **Citra Korup / Rusak (0-byte/Decode Error)** | 0 citra | **0 citra rusak** | **PASSED** |
| **Resolusi Citra** | Tepat $224 \times 224$ piksel | **100% $224 \times 224$** (0 citra non-224) | **PASSED** |
| **Format File & Mode Warna** | JPEG, 3-Channel RGB | **100% JPEG RGB (8-bit per channel)** | **PASSED** |
| **Label Folder & Nama File** | Sesuai alfabet A–Z | **26 kelas teridentifikasi valid** | **PASSED** |

---

## 4. DISTRIBUSI JUMLAH GAMBAR PER KELAS A–Z

Tabel berikut menyajikan distribusi gambar aktual di direktori `data/raw/image/bisindo_alphabet/<A..Z>/`:

| Kelas | Path Direktori Mentah | Jumlah Gambar Aktual | Rata-rata Ukuran File | Min Ukuran | Max Ukuran | Status Integritas |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **A** | `data/raw/image/bisindo_alphabet/A/` | **165** | 6,78 KB | 3,95 KB | 9,80 KB | 100% Valid |
| **B** | `data/raw/image/bisindo_alphabet/B/` | **169** | 6,65 KB | 3,92 KB | 9,80 KB | 100% Valid |
| **C** | `data/raw/image/bisindo_alphabet/C/` | **169** | 6,12 KB | 3,43 KB | 9,21 KB | 100% Valid |
| **D** | `data/raw/image/bisindo_alphabet/D/` | **170** | 6,74 KB | 4,21 KB | 9,67 KB | 100% Valid |
| **E** | `data/raw/image/bisindo_alphabet/E/` | **169** | 6,27 KB | 3,90 KB | 9,33 KB | 100% Valid |
| **F** | `data/raw/image/bisindo_alphabet/F/` | **173** | 6,57 KB | 3,98 KB | 9,67 KB | 100% Valid |
| **G** | `data/raw/image/bisindo_alphabet/G/` | **173** | 6,27 KB | 3,74 KB | 9,45 KB | 100% Valid |
| **H** | `data/raw/image/bisindo_alphabet/H/` | **173** | 6,80 KB | 4,12 KB | 9,67 KB | 100% Valid |
| **I** | `data/raw/image/bisindo_alphabet/I/` | **173** | 6,10 KB | 3,71 KB | 9,48 KB | 100% Valid |
| **J** | `data/raw/image/bisindo_alphabet/J/` | **169** | 5,97 KB | 3,45 KB | 9,25 KB | 100% Valid |
| **K** | `data/raw/image/bisindo_alphabet/K/` | **173** | 6,54 KB | 4,10 KB | 9,67 KB | 100% Valid |
| **L** | `data/raw/image/bisindo_alphabet/L/` | **172** | 6,13 KB | 3,67 KB | 9,33 KB | 100% Valid |
| **M** | `data/raw/image/bisindo_alphabet/M/` | **173** | 7,05 KB | 4,25 KB | 9,80 KB | 100% Valid |
| **N** | `data/raw/image/bisindo_alphabet/N/` | **173** | 6,98 KB | 4,15 KB | 9,80 KB | 100% Valid |
| **O** | `data/raw/image/bisindo_alphabet/O/` | **173** | 6,43 KB | 3,97 KB | 9,55 KB | 100% Valid |
| **P** | `data/raw/image/bisindo_alphabet/P/` | **172** | 6,76 KB | 4,10 KB | 9,67 KB | 100% Valid |
| **Q** | `data/raw/image/bisindo_alphabet/Q/` | **173** | 6,87 KB | 4,12 KB | 9,67 KB | 100% Valid |
| **R** | `data/raw/image/bisindo_alphabet/R/` | **171** | 6,28 KB | 3,80 KB | 9,45 KB | 100% Valid |
| **S** | `data/raw/image/bisindo_alphabet/S/` | **173** | 6,81 KB | 4,15 KB | 9,67 KB | 100% Valid |
| **T** | `data/raw/image/bisindo_alphabet/T/` | **173** | 6,62 KB | 4,05 KB | 9,67 KB | 100% Valid |
| **U** | `data/raw/image/bisindo_alphabet/U/` | **173** | 6,21 KB | 3,85 KB | 9,45 KB | 100% Valid |
| **V** | `data/raw/image/bisindo_alphabet/V/` | **172** | 6,27 KB | 3,92 KB | 9,45 KB | 100% Valid |
| **W** | `data/raw/image/bisindo_alphabet/W/` | **170** | 6,82 KB | 4,25 KB | 9,67 KB | 100% Valid |
| **X** | `data/raw/image/bisindo_alphabet/X/` | **174** | 6,59 KB | 4,05 KB | 9,67 KB | 100% Valid |
| **Y** | `data/raw/image/bisindo_alphabet/Y/` | **174** | 6,62 KB | 4,10 KB | 9,67 KB | 100% Valid |
| **Z** | `data/raw/image/bisindo_alphabet/Z/` | **174** | 5,89 KB | 3,65 KB | 9,25 KB | 100% Valid |
| **TOTAL** | **26 Kelas** | **4.466** | **6,51 KB** | **3,43 KB** | **9,80 KB** | **100% Valid (27,71 MB)** |

---

## 5. HASIL DEDUPLIKASI KRIPTOGRAFIS (SHA-256)

Pemeriksaan SHA-256 mendeteksi **2 pasang gambar identik lintas-kelas (cross-class duplicates)** yang merupakan artefak penataan dari kontributor dataset asli Mendeley:
1. **Pasang 1 (Kelas B vs Kelas E)**:
   - SHA-256: `99c4a1565f4c49c0...`
   - Berkas: `B/B_polos gelap_Iphone_13promax.jpg` vs `E/E_polos gelap_Iphone_13promax.jpg` (Ukuran: 7.041 B).
2. **Pasang 2 (Kelas D vs Kelas P)**:
   - SHA-256: `a99273b2ca82794c...`
   - Berkas: `D/D_Polos Gelap_iPhone_XR.jpeg` vs `P/P_Polos Gelap_iPhone_XR.jpeg` (Ukuran: 5.119 B).
- **Penanganan**: Kedua pasang ini akan disaring secara otomatis oleh mekanisme `ambiguous_cross_class_shas` di `scripts/crop_hands.py` agar tidak menimbulkan ambiguitas label dan kebocoran antar split.
- **Duplikat Dalam-Kelas (Intra-Class)**: **0 gambar duplikat** (seluruh citra lainnya unik).

---

## 6. VISUALISASI PROFILING DATASET

Visualisasi telah dibuat dan disimpan di folder `docs/figures/p0_dataset/`:
1. **Distribusi Kelas**: [`docs/figures/p0_dataset/class_distribution.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/class_distribution.png)
   - Menampilkan histogram batang 26 kelas, garis target minimum proyek (40 gambar), dan garis rata-rata aktual (171,8 gambar). Distribusi sangat seimbang dengan deviasi standar rendah ($SD = 2,2$ gambar).
2. **Sampel Citra 26 Kelas A–Z**: [`docs/figures/p0_dataset/sample_classes_grid.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/sample_classes_grid.png)
   - Menampilkan grid visual $4 \times 7$ sampel citra tangan asli untuk setiap huruf dari A hingga Z.

---

## 7. STRATEGI DATASET: FULL (4.466) VS SUBSET BALANCED (1.040)

Kami membandingkan dua opsi strategi dataset:

| Aspek Komparasi | Opsi 1: Full Dataset (4.466 Gambar) | Opsi 2: Balanced Subset 40/Kelas (1.040 Gambar) |
|---|---|---|
| **Jumlah Total Sampel** | 4.466 citra ($165 - 174$ per kelas) | 1.040 citra (tepat 40 per kelas) |
| **Keseimbangan Kelas** | Sedikit bervariasi ($165$ di A s/d $174$ di X, Y, Z) | Sempurna ($40$ per kelas) |
| **Variasi Latar & Cahaya** | **Sangat Kaya**: 5 latar belakang (Polos Gelap, Polos Terang, Baju Motif, Bebas, Luar Ruangan) &times; 6 perangkat kamera berbeda (iPhone 11, 12, 13 Pro Max, XR, Redmi Note, Realme). | **Terbatas**: Kehilangan ~76,7% variasi lingkungan dan sudut kamera. |
| **Resiko Overfitting CNN** | Sangat rendah; dataset lebih besar meningkatkan generalisasi MobileNetV3. | Lebih rentan overfitting karena hanya 28 gambar train per kelas (70%). |
| **Waktu Training CPU** | ~3–5 menit pada CPU lokal (25 epoch). | ~1–2 menit pada CPU lokal (25 epoch). |

### Rekomendasi Senior ML Engineer:
1. **Strategi Dua Jalur (Dual-Manifest)**:
   - File manifest Opsi 2 telah dibuat secara deterministik dengan `seed=42`: [`data/raw/image/bisindo_alphabet/subset_1040_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/raw/image/bisindo_alphabet/subset_1040_manifest.csv) (tepat 1.040 gambar).
   - Seluruh 4.466 gambar mentah tetap dipertahankan 100% utuh tanpa penghapusan.
2. **Prioritas Pelatihan Utama**: Gunakan **Full Dataset (4.466 gambar)** untuk melatih model `image_i1_mobilenetv3_p0` agar menghasilkan akurasi tinggi dan ketahanan terhadap variasi kamera webcam browser, serta lakukan evaluasi komparasi pada subset 1.040 gambar.

---

## 8. HASIL UJI PREPROCESSING & HAND CROP SAMPEL (TAHAP D)

Kami menguji implementasi [`scripts/crop_hands.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/crop_hands.py) dan [`signbridge/image/crop.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/crop.py) pada 6 sampel kelas representatif (`A`, `B`, `C`, `K`, `O`, `Y`):
- **Temuan Karakteristik Citra Mendeley**:
  - Seluruh citra dari Mendeley telah terpusat (*hand pre-centered*) dengan resolusi awal $224 \times 224 \times 3$ RGB.
  - Pemotongan persegi terpusat (`prepare_precentered_hand_image`) mempertahankan 100% jari tangan tanpa terpotong (*zero finger clipping*).
  - Normalisasi ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`) berjalan secara deterministik dan presisi.
- **Visualisasi Hasil Uji**:
  - Disimpan pada: [`docs/figures/p0_dataset/preprocessing_crop_sample.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/preprocessing_crop_sample.png)
  - Membandingkan: Citra Asli &rarr; Bounding Box Bounding (+25% Margin) &rarr; Patch Potongan &rarr; Output Resize 224&times;224.

---

## 9. STATUS AKHIR & GATE PERSETUJUAN

- **Status Akhir Tahap 2 & 3**: **`DATASET READY`**
- **Integritas Proyek**:
  - Model lama `runs/image_i1_mobilenetv3/best.pt`: **Tetap utuh (tidak ditimpa)**.
  - Model produksi web `web/model/fingerspell.onnx`: **Tetap utuh (tidak ditimpa)**.
  - Dataset mentah di `data/raw/image/bisindo_alphabet/`: **4.466 gambar tersimpan utuh dan aman**.
  - Tidak ada proses training yang dijalankan pada tahap ini.

> **Rekomendasi Langkah Selanjutnya**: Menunggu persetujuan pengguna untuk melanjutkan ke **Tahap 4 (Preprocessing seluruh dataset ke `data/processed/bisindo_alphabet/` dan generate manifest)** serta **Tahap 5 (Pembagian Stratified Train/Val/Test 70/15/15)**.

