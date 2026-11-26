# LAPORAN INVESTIGASI FORENSIK DUPLIKASI DATASET LINTAS-KELAS
## SignBridge ASEAN — Modality Image I1-P1 (BISINDO A–Z)

> **Dokumen**: `docs/validation_p1/DUPLICATE_FORENSIC_AUDIT.md`  
> **Tipe Evaluasi**: Binary, Hash & Visual Forensic Dataset Audit  
> **Target Investigasi**: 4 Citra Terduplikasi Lintas-Kelas pada Dataset Mentah Mendeley  
> **Tanggal Audit**: 17 November 2026  
> **Auditor**: Senior Computer Vision Engineer, Dataset Forensics Specialist, & ML Methodology Reviewer  
> **Status Verifikasi Forensik**: **`VERIFIED_EXACT_DUPLICATE` (Kedua Pasangan)**

---

## 1. SCOPE & LATAR BELAKANG INVESTIGASI

Audit forensik ini dilakukan untuk menginvestigasi temuan empat citra pada dataset mentah BISINDO (`data/raw/image/bisindo_alphabet/`) yang dilaporkan memiliki hash biner identik tetapi terdaftar pada folder kelas yang berbeda.

Tujuan utama investigasi:
1. Menentukan apakah duplikasi tersebut bersifat identik pada level biner (`EXACT_BINARY_DUPLICATE`) atau sekadar kemiripan visual (`VISUAL_DUPLICATE_CANDIDATE`).
2. Menemukan path absolut dan relatif kedua pasangan secara independen.
3. Melakukan inspeksi visual komparatif (analisis piksel, Mean Absolute Error, dan rekonstruksi gestur tangan).
4. Menelusuri metadata EXIF, timestamp, dan dimensi file sumber.
5. Memetakan akar masalah (*root cause*) kemunculan duplikasi tersebut.

---

## 2. INVENTARISASI CITRA TERDUPLIKASI & PEMERIKSAAN SHA-256 (TASK 1 & TASK 2)

Pemindaian menyeluruh dilakukan terhadap seluruh **4.466 file citra mentah** di repositori. Hasil perhitungan SHA-256 pada level byte file asli mengonfirmasi bahwa di seluruh dataset mentah, hanya terdapat **tepat 2 grup duplikasi biner**, dan keduanya merupakan **duplikasi lintas-kelas (*cross-class duplicates*)**:

| Pasangan Terduplikasi | File Sumber 1 (Path & Nama File) | File Sumber 2 (Path & Nama File) | Hash SHA-256 (Byte-Level) | Kesamaan Hash | Status Forensik |
|:---:|---|---|---|:---:|:---:|
| **Grup 1 (D vs P)** | `data/raw/image/bisindo_alphabet/D/D_Polos Gelap_iPhone_XR.jpeg` | `data/raw/image/bisindo_alphabet/P/P_Polos Gelap_iPhone_XR.jpeg` | `a99273b2ca82794cb612bc3ace480521ae73d2cb41d6f406bbc14d586d095aa0` | **100% IDENTIK** | **`EXACT_BINARY_DUPLICATE`** |
| **Grup 2 (B vs E)** | `data/raw/image/bisindo_alphabet/B/B_polos gelap_Iphone_13promax.jpg` | `data/raw/image/bisindo_alphabet/E/E_polos gelap_Iphone_13promax.jpg` | `99c4a1565f4c49c05be9badc4be2836d9353e35acd49fe2e76dc08aa86d46e53` | **100% IDENTIK** | **`EXACT_BINARY_DUPLICATE`** |

### Perbandingan Parameter Fisik & Metadata:

| Parameter Evaluasi | Grup 1: File D | Grup 1: File P | Grup 2: File B | Grup 2: File E |
|---|---|---|---|---|
| **Ukuran File (Bytes)** | **5.119 bytes** | **5.119 bytes** | **7.041 bytes** | **7.041 bytes** |
| **Dimensi Piksel ($W \times H$)** | $224 \times 224$ | $224 \times 224$ | $224 \times 224$ | $224 \times 224$ |
| **Channel / Color Mode** | 3-Channel RGB | 3-Channel RGB | 3-Channel RGB | 3-Channel RGB |
| **Format Kompresi** | JPEG (JFIF) | JPEG (JFIF) | JPEG (JFIF) | JPEG (JFIF) |
| **Perangkat Perekam** | iPhone XR | iPhone XR | iPhone 13 Pro Max | iPhone 13 Pro Max |
| **Kondisi Latar** | Polos Gelap | Polos Gelap | Polos Gelap | Polos Gelap |
| **EXIF Metadata** | Kosong (Tercopot) | Kosong (Tercopot) | Kosong (Tercopot) | Kosong (Tercopot) |

---

## 3. INSPEKSI FORENSIK VISUAL & ANALISIS PIKSEL (TASK 3)

Dilakukan decoding citra secara independen menggunakan OpenCV dan PIL untuk menguji apakah ada perbedaan nilai piksel setelah dekompresi:

```
Hasil Uji Piksel:
- Grup 1 (D vs P): Mean Absolute Error (MAE) = 0,000000 | Max Pixel Difference = 0,0
- Grup 2 (B vs E): Mean Absolute Error (MAE) = 0,000000 | Max Pixel Difference = 0,0
```

Seluruh visualisasi perbandingan telah dibuat dan disimpan di direktori baru [`docs/validation_p1/duplicate_forensics/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/duplicate_forensics/):
1. [`pair1_D_vs_P_comparison.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/duplicate_forensics/pair1_D_vs_P_comparison.png) — Perbandingan berdampingan D vs P beserta selisih matriks piksel (amplifikasi 50x menunjukkan nol deviasi).
2. [`pair2_B_vs_E_comparison.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/duplicate_forensics/pair2_B_vs_E_comparison.png) — Perbandingan berdampingan B vs E beserta selisih matriks piksel.
3. [`duplicate_contact_sheet.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/duplicate_forensics/duplicate_contact_sheet.png) — Lembar kontak visual 4 citra sekaligus.

---

## 4. TEMUAN VISUAL MORFOLOGI GESTUR TANGAN

Pemeriksaan multimodal visual secara mendalam terhadap bentuk tangan riil pada kedua citra mengungkapkan fakta penting:

### 4.1. Analisis Visual Pasangan D vs P (`D_Polos Gelap_iPhone_XR.jpeg` & `P_Polos Gelap_iPhone_XR.jpeg`):
- **Bentuk Gestur Aktual**: Gestur menggunakan **dua tangan (*two-handed gesture*)**.
  - Tangan kiri: Telunjuk tegak lurus mengarah ke atas membentuk garis vertikal lurus (*straight spine*).
  - Tangan kanan: Jempol dan telunjuk membentuk kurva setengah lingkaran (*arch/loop*), menyentuh ujung dan pangkal telunjuk tangan kiri.
- **Bentuk Huruf Representasi**: Formasi visual kedua tangan ini secara eksplisit meniru **huruf kapital "D"**.
- **Anomali**: File ini dimasukkan ke folder `D/` dengan nama `D_Polos Gelap_iPhone_XR.jpeg`, namun file yang persis sama disalin (*cloned*) ke folder `P/` dengan nama `P_Polos Gelap_iPhone_XR.jpeg`. Bentuk visual sama sekali tidak membentuk huruf "P".

### 4.2. Analisis Visual Pasangan B vs E (`B_polos gelap_Iphone_13promax.jpg` & `E_polos gelap_Iphone_13promax.jpg`):
- **Bentuk Gestur Aktual**: Gestur menggunakan **dua tangan (*two-handed gesture*)**.
  - Tangan kanan: Jari telunjuk tegak vertikal membentuk tiang utama.
  - Tangan kiri: Tiga jari (telunjuk, tengah, dan manis) diarahkan horizontal mendatar menyentuh tiang vertikal tangan kanan pada bagian atas, tengah, dan bawah.
- **Bentuk Huruf Representasi**: Formasi tiga garis horizontal pada satu tiang vertikal ini secara visual merepresentasikan **huruf kapital "E"**.
- **Anomali**: File ini disalin ke folder `B/` dengan nama `B_polos gelap_Iphone_13promax.jpg` dan ke folder `E/` dengan nama `E_polos gelap_Iphone_13promax.jpg`. Bentuk visual tidak membentuk dua lengkungan huruf "B".

---

## 5. KESIMPULAN AUDIT FORENSIK DUPLIKASI

1. **Konfirmasi Binary Duplicate**: Keempat file terbukti 100% merupakan **`EXACT_BINARY_DUPLICATE`** (bukan variasi pose, bukan kompresi ulang, melainkan file klon identik bit-by-bit).
2. **Karakteristik Penamaan**: Pola nama file `[Huruf]_[Background]_[Perangkat]` membuktikan bahwa pembuat dataset asli menyalin file yang sama, lalu sekadar mengubah huruf awalan nama file agar cocok dengan folder target.
3. **Penyebab Utama**: Terjadi **`SOURCE_DATASET_DUPLICATE`** dan **`HUMAN_ANNOTATION_ERROR`** pada repositori sumber Mendeley Data sebelum diunduh ke dalam repositori SignBridge ASEAN.

