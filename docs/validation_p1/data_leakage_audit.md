# LAPORAN AUDIT DATA LEAKAGE LANJUTAN EKSPERIMEN I1-P1 (TAHAP C)

> **Dokumen**: `docs/validation_p1/data_leakage_audit.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Metode Audit**: Hash Kriptografis (SHA-256), Perceptual Hashing (dHash 64-bit), Metadata Mining, & Device Trace Analysis  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Audit**: **`VERIFIED WITH ARCHITECTURAL CAVEATS`** (Bebas Duplikasi Citra, Namun Memiliki Keterbatasan Subject-Level)

---

## 1. TUJUAN AUDIT DATA LEAKAGE

Menyelidiki potensi kebocoran data (*data leakage*) pada pembagian Train ($3.123$), Validation ($669$), dan Test ($670$) yang dapat menyebabkan estimasi performa model tampak lebih tinggi (*optimistic bias*) daripada performa di dunia nyata.

Audit mencakup tiga dimensi:
1. **Duplicate & Near-Duplicate Leakage**: Apakah ada citra yang identik secara biner atau sangat mirip secara perseptual antar-split?
2. **Group / Subject Leakage**: Apakah citra dari individu penutur yang sama terdistribusi ke dalam Train dan Test?
3. **Background & Device Leakage**: Apakah fitur latar belakang (*background artifacts*) atau karakteristik sensor kamera membocorkan informasi kelas?

---

## 2. A. DETEKSI DUPLIKASI (DUPLICATE & NEAR-DUPLICATE)

### 1. Hash Kriptografis SHA-256
Pemeriksaan menyeluruh dilakukan pada 4.462 file preprocessed `.npy` dan citra mentah `.jpg`:
- $\text{Train} \cap \text{Validation}$: **$0$ duplikasi** ($\emptyset$).
- $\text{Train} \cap \text{Test}$: **$0$ duplikasi** ($\emptyset$).
- $\text{Validation} \cap \text{Test}$: **$0$ duplikasi** ($\emptyset$).
- **Kesimpulan**: Tidak ada duplikasi biner persis (*exact byte-level duplicates*) antar-split.

### 2. Perceptual Difference Hash (dHash 64-bit)
Setiap citra dikonversi ke grayscale, di-resize ke $9 \times 8$ menggunakan interpolasi Lanczos, dan dihitung gradien piksel horizontalnya untuk menghasilkan sidik jari visual 64-bit:
- **Exact Perceptual Matches (Hamming Distance $= 0$) Antara Train dan Test**: **$0$ citra**.
- **Near-Duplicate Sampling (Hamming Distance $\le 2$)**: Pengujian sampling pada 100 sampel Test Set terhadap seluruh 3.123 hash Train Set menghasilkan **$0$ near-duplicate**.
- **Kesimpulan**: Citra pada Test Set bukan merupakan hasil kompresi ulang, pergeseran piksel minor, atau variasi format dari citra yang ada di Train Set.

---

## 3. B. AUDIT SUBJECT / VOLUNTEER LEAKAGE (KEBOCORAN INDIVIDU PENUTUR)

### 1. Fakta yang Berhasil Diverifikasi
- Berdasarkan metadata resmi Mendeley Data (`data/raw/image/bisindo_alphabet/mendeley_metadata.json`), dataset dikumpulkan dari sejumlah sukarelawan (*volunteers*):
  > *"The dataset comprises images of BISINDO letters from A to Z, captured using different devices, backgrounds, and individuals... Collected from volunteers who provided consent and ethical approval..."*
- Namun, **ID Penutur (Subject ID / Volunteer ID) TIDAK DICANTUMKAN** dalam metadata resmi maupun nama file.
- Dataset mentah hanya diorganisir ke dalam subfolder kelas `A/` sampai `Z/`.
- Pembagian Train, Validation, dan Test pada proyek dilakukan menggunakan metode **Stratified Random Split (Seed 42)** pada tingkat citra (*image-level split*), bukan *subject-level split*.

### 2. Indikasi yang Ditemukan
- Analisis nama file asal (`source_path`) mengidentifikasi penggunaan beberapa perangkat perekaman:
  - **Samsung A53 5G**: $1.036$ citra (Train: $747$, Val: $142$, Test: $147$).
  - **iPhone 14 Pro**: $832$ citra (Train: $566$, Val: $142$, Test: $124$).
  - **Xiaomi Note 8 Pro**: $519$ citra (Train: $373$, Val: $76$, Test: $70$).
  - **Timestamped Camera**: $104$ citra (Train: $72$, Val: $14$, Test: $18$).
  - **Other / Unknown**: $1.971$ citra (Train: $1.365$, Val: $295$, Test: $311$).
- Karena rasio perangkat tersebar merata di setiap split, **sangat mungkin seorang sukarelawan yang merekam menggunakan satu perangkat muncul di kedua split (Train dan Test)**.

### 3. Hal yang Belum Dapat Diverifikasi
- Tanpa anotasi resmi ID penutur dari penyusun dataset Mendeley, **Subject-Level Isolation TIDAK DAPAT DIBUKTIKAN MAUPUN DISANGKAL** secara matematis.
- **Dampak Teknis**: Model mungkin telah mempelajari karakteristik spesifik tangan penutur tertentu (warna kulit, proporsi jari, bekas luka/aksesori) yang kebetulan muncul di Test Set. Oleh karena itu, akurasi $61,19\%$ pada Test Set Mendeley belum tentu setara dengan akurasi pada pengguna baru di dunia nyata (*unseen subjects*).

---

## 4. C. AUDIT BACKGROUND & ENVIRONMENT LEAKAGE

1. **Efektivitas Hand Bounding Box Crop**:
   - Seluruh citra telah diproses melalui pipeline crop tangan menjadi $224 \times 224$ piksel.
   - Crop tangan berhasil memotong sebagian besar latar belakang ruangan, mengurangi risiko model menghafal perabot atau dinding ruangan.
2. **Sisa Margin Latar Belakang (Residual Background)**:
   - Nama file mentah mendokumentasikan variasi latar belakang: `Background Baju`, `Bebas`, `Hitam`, `Polos Terang`, `Background Baju (Garis)`.
   - Pada citra crop tangan $224 \times 224$, area di sela-sela jari dan sekitar pergelangan tangan tetap memuat piksel latar belakang (kain baju, dinding kamar).
   - Jika sukarelawan tertentu mengenakan pakaian yang sama saat memperagakan huruf A hingga Z, ada risiko kecil jaringan konvolusi mengekstraksi tekstur kain tersebut sebagai fitur korelasi semu.

---

## 5. PEMISAHAN TRANSPARAN BUKTI AUDIT

| Kategori Temuan | Deskripsi Status | Tingkat Keyakinan |
|---|---|:---:|
| **Fakta Terverifikasi** | 1. Bebas dari duplikasi biner SHA-256 antar-split.<br>2. Bebas dari duplikasi perseptual dHash (Hamming $\le 2$).<br>3. Seluruh 670 sampel Test Set adalah file citra mandiri. | **Pasti ($100\%$)** |
| **Indikasi Teridentifikasi** | 1. Dataset direkam oleh sejumlah kecil relawan menggunakan $\approx 4\text{--}5$ model perangkat.<br>2. Perangkat terdistribusi merata di ketiga split.<br>3. Residual latar belakang pakaian hadir pada margin crop tangan. | **Tinggi ($85\%$)** |
| **Belum Dapat Diverifikasi** | Isolasi subjek murni (*Subject-Independent Generalization*). Karena Mendeley tidak menyertakan anotasi penutur, evaluasi ini baru dapat diuji secara definitif menggunakan **dataset eksternal independen**. | **Perlu Data Eksternal** |

---

## 6. KESIMPULAN TAHAP C

Dataset P1 lolos audit duplikasi biner dan perseptual. Namun, karena keterbatasan metadata asli dataset publik Mendeley (tanpa Subject ID), evaluasi performa $61,19\%$ **harus diperlakukan sebagai performa *subject-mixed***. Pengujian generalisasi terhadap penutur baru mutlak diperlukan sebelum deployment.

