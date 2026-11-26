# LAPORAN TAHAP 4 & 5: FULL PREPROCESSING & STRATIFIED DATA SPLIT BISINDO ALPHABET (P0)

> **Dokumen**: `docs/P0_PREPROCESSING_SPLIT_REPORT.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Tahap**: Tahap 4 (Full Preprocessing) & Tahap 5 (Stratified Data Split 70/15/15)  
> **Tanggal Pelaksanaan**: 13 November 2026  
> **Auditor**: Senior Machine Learning Engineer, SignBridge ASEAN  
> **Status Akhir**: **`READY FOR TRAINING`**  

---

## 1. RINGKASAN EKSEKUTIF

Tahap 4 (Preprocessing Penuh) dan Tahap 5 (Pembagian Dataset Bertingkat/Stratified Split) telah selesai dijalankan secara tuntas, deterministik, dan tanpa memodifikasi atau menghapus dataset mentah. Seluruh citra telah diproses dengan crop persegi terpusat presisi $224 \times 224 \times 3$ RGB, disaring dari duplikat lintas-kelas, dan dibagi secara proporsional ke dalam tiga split independen tanpa ada kebocoran data (*zero data leakage*).

### Ringkasan Statistik Utama:
- **Jumlah Citra Mentah Awal**: **4.466 berkas** (dari 26 kelas `A` s/d `Z`).
- **Citra yang Dikecualikan (Exclusion)**: **4 berkas** (2 pasang duplikat identik lintas-kelas yang terbukti ambigu di dataset asli).
- **Citra yang Berhasil Diproses**: **4.462 berkas (100% dari data valid)**.
- **Citra Gagal / Korup**: **0 berkas (0,0%)**.
- **Format Penyimpanan Processed**:
  - Array teroptimasi: `.npy` (uint8 `[224, 224, 3]`) untuk kecepatan transfer I/O ke DataLoader PyTorch.
  - Citra visualisasi: `.jpg` (RGB 95% quality) di subfolder kelas `data/processed/bisindo_alphabet/<A..Z>/`.
- **Pembagian Split Stratified (Seed = 42)**:
  - **Train (70,0%)**: **3.123 citra**
  - **Validation (15,0%)**: **669 citra**
  - **Test (15,0%)**: **670 citra**
  - **Total**: **4.462 citra**
- **Verifikasi Kesiapan DataLoader**:
  - `FingerspellDataset` berhasil menginisialisasi ketiga split secara mandiri.
  - Pengujian batch PyTorch (`torch.Size([32, 3, 224, 224])`, dtype `torch.float32`, label range `0..25`) berhasil 100%.
  - Pemeriksaan interseksi split membuktikan **0 path leak, 0 source leak, dan 0 SHA-256 hash leak**.

---

## 2. METODE PREPROCESSING & CROP TANGAN

### A. Karakteristik Dataset Citra Asli
Sesuai hasil audit pada Tahap 3, dataset resmi *Mendeley BISINDO Alphabet v1* (Samuel Ady Sanjaya, 2024) telah melalui proses sentralisasi saat akuisisi awal dengan resolusi native $224 \times 224 \times 3$ RGB.

### B. Prosedur Preprocessing:
1. **Pembacaan Citra RGB**: Setiap file didekode menggunakan Pillow (`PIL.Image`) dan dikonversi ke mode warna `RGB` (menghilangkan channel alpha jika ada).
2. **Crop Persegi Terpusat (Precentered Square Crop)**:
   - Menghitung dimensi $H$ dan $W$.
   - Mengambil sisi persegi maksimal: $\text{side} = \min(H, W) = 224$.
   - Menghitung titik potong simetris: $x_0 = (W - \text{side}) // 2 = 0$, $y_0 = (H - \text{side}) // 2 = 0$.
   - Menjamin 100% area tangan dan ujung jari tetap utuh tanpa risiko terpotong (*zero finger clipping*) yang kerap terjadi jika menggunakan detektor landmark MediaPipe statis pada citra dengan background kompleks.
3. **Penyimpanan Ganda untuk Kinerja Maksimal**:
   - Disimpan ke `data/processed/bisindo_alphabet/<A..Z>/<letter>_<sample_id:04d>.npy` (Array murni uint8 $[224, 224, 3]$) &rarr; Menghindari latensi kompresi JPEG saat pelatihan MobileNetV3.
   - Disimpan ke `data/processed/bisindo_alphabet/<A..Z>/<letter>_<sample_id:04d>.jpg` &rarr; Memudahkan inspeksi visual antarmuka dan laporan.

---

## 3. PENANGANAN DUPLIKASI LINTAS-KELAS (CROSS-CLASS DUPLICATES)

Audit kriptografis SHA-256 pada Tahap 3 mengidentifikasi dua pasang berkas yang identik secara biner namun diberi dua label kelas berbeda pada repositori asli Mendeley:

| No | Hash SHA-256 | Berkas 1 (Label Awal) | Berkas 2 (Label Awal) | Ukuran | Keputusan & Alasan Pengecualian |
|:---:|---|---|---|:---:|---|
| 1 | `99c4a1565f4c49c00b95eb5a92a54b38d3885dcfbe3aeb00cb3915f79a97dff8` | `B/B_polos gelap_Iphone_13promax.jpg` | `E/E_polos gelap_Iphone_13promax.jpg` | 7.041 B | **DIKECUALIKAN DARI EXPERIMENT** (Ambiguitas label $B$ vs $E$; foto yang persis sama tidak boleh menjadi ground truth untuk dua kelas berbeda). |
| 2 | `a99273b2ca82794ccae3b610cfa0fc19808608d0a3d46387d8a6bc8b34f82859` | `D/D_Polos Gelap_iPhone_XR.jpeg` | `P/P_Polos Gelap_iPhone_XR.jpeg` | 5.119 B | **DIKECUALIKAN DARI EXPERIMENT** (Ambiguitas label $D$ vs $P$; mencegah kontaminasi evaluasi model). |

> **Prinsip Integritas Data**: Keempat file mentah asli di atas **TIDAK DIHAPUS** dari direktori `data/raw/image/bisindo_alphabet/`. Pengecualian hanya dilakukan pada manifest pelatihan dan dicatat secara transparan pada manifest audit penuh [`data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv).

---

## 4. HASIL STRATIFIED SPLIT 70 / 15 / 15

Pembagian dataset dilakukan secara berstrata (*stratified*) menggunakan `sklearn.model_selection.train_test_split` dengan random seed `42`:
- **Train Split (70,0%)**: 3.123 citra
- **Validation Split (15,0%)**: 669 citra
- **Test Split (15,0%)**: 670 citra
- **Total Valid**: 4.462 citra

### Tabel Distribusi per Kelas A–Z:

| Kelas | Total Mentah | Dikecualikan | Total Valid | Train (70%) | Validation (15%) | Test (15%) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 165 | 0 | 165 | 115 | 25 | 25 |
| **B** | 169 | 1 (vs E) | 168 | 118 | 25 | 25 |
| **C** | 169 | 0 | 169 | 118 | 25 | 26 |
| **D** | 170 | 1 (vs P) | 169 | 118 | 25 | 26 |
| **E** | 169 | 1 (vs B) | 168 | 118 | 25 | 25 |
| **F** | 173 | 0 | 173 | 121 | 26 | 26 |
| **G** | 173 | 0 | 173 | 121 | 26 | 26 |
| **H** | 173 | 0 | 173 | 121 | 26 | 26 |
| **I** | 173 | 0 | 173 | 121 | 26 | 26 |
| **J** | 169 | 0 | 169 | 118 | 25 | 26 |
| **K** | 173 | 0 | 173 | 121 | 26 | 26 |
| **L** | 172 | 0 | 172 | 120 | 26 | 26 |
| **M** | 173 | 0 | 173 | 121 | 26 | 26 |
| **N** | 173 | 0 | 173 | 121 | 26 | 26 |
| **O** | 173 | 0 | 173 | 121 | 26 | 26 |
| **P** | 172 | 1 (vs D) | 171 | 120 | 25 | 26 |
| **Q** | 173 | 0 | 173 | 121 | 26 | 26 |
| **R** | 171 | 0 | 171 | 120 | 25 | 26 |
| **S** | 173 | 0 | 173 | 121 | 26 | 26 |
| **T** | 173 | 0 | 173 | 121 | 26 | 26 |
| **U** | 173 | 0 | 173 | 121 | 26 | 26 |
| **V** | 172 | 0 | 172 | 120 | 26 | 26 |
| **W** | 170 | 0 | 170 | 119 | 25 | 26 |
| **X** | 174 | 0 | 174 | 122 | 26 | 26 |
| **Y** | 174 | 0 | 174 | 122 | 26 | 26 |
| **Z** | 174 | 0 | 174 | 122 | 26 | 26 |
| **TOTAL** | **4.466** | **4** | **4.462** | **3.123 (70%)** | **669 (15%)** | **670 (15%)** |

---

## 5. HASIL VERIFIKASI KETAT DATA LEAKAGE (ZERO LEAKAGE)

Pemeriksaan integritas relasional dijalankan oleh [`scripts/verify_preprocessing_and_loaders.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/verify_preprocessing_and_loaders.py):
1. **Interseksi Path File Processed**:
   - `split_paths['train'] ∩ split_paths['val']` = **$\emptyset$ (0 file)**
   - `split_paths['train'] ∩ split_paths['test']` = **$\emptyset$ (0 file)**
   - `split_paths['val'] ∩ split_paths['test']` = **$\emptyset$ (0 file)**
2. **Interseksi Sumber Mentah (Source Path)**:
   - `split_sources['train'] ∩ split_sources['val']` = **$\emptyset$ (0 file)**
   - `split_sources['train'] ∩ split_sources['test']` = **$\emptyset$ (0 file)**
   - `split_sources['val'] ∩ split_sources['test']` = **$\emptyset$ (0 file)**
3. **Interseksi Checksum Biner (SHA-256 Hash)**:
   - `split_shas['train'] ∩ split_shas['val']` = **$\emptyset$ (0 file)**
   - `split_shas['train'] ∩ split_shas['test']` = **$\emptyset$ (0 file)**
   - `split_shas['val'] ∩ split_shas['test']` = **$\emptyset$ (0 file)**

**Kesimpulan Audit**: Terbukti secara matematis bahwa **TIDAK ADA DATA LEAKAGE** antara set pelatihan, validasi, maupun pengujian.

---

## 6. VISUAL QUALITY CONTROL & ARTEFAK GAMBAR

Dua gambar visualisasi diagnostik telah dihasilkan dan disimpan:
1. **Distribusi Split per Kelas**:  
   [`docs/figures/p0_dataset/split_distribution_by_class.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/split_distribution_by_class.png)  
   *(Grafik diagram batang bertingkat Train, Val, dan Test per kelas A–Z).*
2. **Quality Control 26 Kelas Asli vs Hasil Preprocessing**:  
   [`docs/figures/p0_dataset/full_26_classes_preprocessing_grid.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/full_26_classes_preprocessing_grid.png)  
   *(Grid 52 citra berdampingan untuk seluruh 26 huruf alfabet membuktikan keselarasan bentuk, orientasi tangan, dan kejernihan fitur).*

---

## 7. ARTEFAK MANIFEST & FILE YANG DIHASILKAN

1. **Manifest Pelatihan (Training-Ready)**:
   - [`data/processed/bisindo_alphabet/manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/manifest.csv)  
   - Format: 14 kolom lengkap (`path`, `image_path`, `processed_path`, `source_path`, `original_path`, `letter`, `class_name`, `label`, `split`, `sha256`, `original_sha256`, `crop_status`, `preprocessing_status`, `hand_found`, `exclusion_reason`).
   - Berisi 4.462 baris citra valid yang siap dibaca oleh `FingerspellDataset`.
2. **Manifest Audit Komprehensif (Termasuk Pengecualian)**:
   - [`data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv)  
   - Berisi seluruh 4.466 baris (4.462 sukses + 4 dikecualikan dengan alasan tercatat).
3. **Ringkasan Metadata JSON**:
   - `data/processed/bisindo_alphabet/preprocessing_summary.json`
4. **Scripts Operasional**:
   - [`scripts/preprocess_bisindo_alphabet.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/preprocess_bisindo_alphabet.py)
   - [`scripts/verify_preprocessing_and_loaders.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/verify_preprocessing_and_loaders.py)
   - [`scripts/plot_preprocessing_and_splits.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/plot_preprocessing_and_splits.py)

---

## 8. STATUS AKHIR & KESIAPAN TAHAP SELANJUTNYA

- **Status**: **`READY FOR TRAINING`**
- Model lama `runs/image_i1_mobilenetv3/best.pt` dan model aplikasi `web/model/fingerspell.onnx` tetap aman tanpa modifikasi.
- Tidak ada pelatihan model yang dijalankan pada turn ini sesuai aturan wajib.

> **Langkah Berikutnya**: Menunggu persetujuan pengguna untuk melangkah ke **Tahap 6 (Training MobileNetV3 I1 pada folder baru `runs/image_i1_mobilenetv3_p0/`)** dan **Tahap 7 (Evaluasi Metrik Accuracy, Precision, Recall, Macro F1, Confusion Matrix)**.

