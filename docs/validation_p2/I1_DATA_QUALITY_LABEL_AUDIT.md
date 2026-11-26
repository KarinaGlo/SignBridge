# PHASE 2: DATA QUALITY & LABEL VALIDATION AUDIT REPORT
## Modality Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Executive Summary & Audit Scope

### 1.1 Scope & Context
Audit teknis ini merupakan pelaksanaan **Phase 2: Data Quality & Label Validation Audit** untuk modul **Image Modality I1 (BISINDO Alphabet Fingerspelling A–Z)** pada proyek *SignBridge ASEAN*. Audit ini dirancang untuk melakukan investigasi forensik independen secara read-only terhadap kualitas visual, integritas pemrosesan citra, potensi noise anotasi (label noise), duplikasi perceptual (near-duplicates), dan kebocoran lintas split (cross-split data leakage) pada dataset olahan (*processed dataset*).

Pekerjaan ini melanjutkan temuan historis dari:
- `docs/validation_p1/FINAL_TRAINING_DATA_LINEAGE_VERIFICATION.md`
- `docs/validation_p1/LINEAGE_EVIDENCE_HARDENING.md`
- `docs/validation_p1/FINAL_LINEAGE_AUDIT_RECONCILIATION.md`
- `docs/validation_p1/FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md`

### 1.2 Key Dataset Lineage Baseline
- **Sumber Data Mentah**: Mendeley BISINDO Alphabet Dataset (total 4.466 berkas mentah dari 26 folder kelas A–Z).
- **Pengecualian Duplikat Kriptografis Mentah**: 4 berkas duplikat biner eksak lintas-kelas (`D/P` hash `a99273b2...` dan `B/E` hash `99c4a156...`) telah dikecualikan secara ketat pada tahap preprocessing (`EXCLUDED`).
- **Dataset Olahan Aktif**: 4.462 citra RGB terpusat berukuran $224 \times 224$ piksel, tersimpan dalam format `.jpg` dan `.npy` di `data/processed/bisindo_alphabet/`.
- **Status Model P1**: MobileNetV3-Small dilatih pada split 70% Train ($N=3.123$), 15% Validation ($N=669$), dan 15% Test ($N=670$), dengan akurasi validasi terbaik $60,24\%$ (403/669) dan akurasi test set $61,19\%$ (410/670). Checkpoint SHA-256: `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9`.

### 1.3 Audit Verdict Summary
| Metric / Checkpoint | Hasil Audit | Status |
| :--- | :--- | :---: |
| Total Processed Dataset | 4.462 sampel terverifikasi utuh di disk | **PASS** |
| Zero-Byte / Corrupted Files | 0 berkas rusak / 0 berkas kosong | **PASS** |
| Exact Hash Duplicates (Bitmap) | 0 pasangan duplikat eksak (dHash=0 & pHash=0) | **PASS** |
| Framing & Hand Clipping | 4.236 citra ($94,93\%$) mengalami pemotongan batas (clipping) akibat *center-crop* statis | **FAIL (LIMITATION)** |
| Cross-Class Near Duplicates | Ditemukan pasangan sangat mirip: Class M vs N ($d=4$) dan Class U vs V ($d=3.5$) | **WARNING** |
| Cross-Split Leakage (Capture Session) | 17 pasangan dengan Hamming distance $\le 4$ lintas Train vs Val/Test | **WARNING** |
| Bottom-5 Performance Classes | P (F1: 30,19%), C (F1: 34,48%), D (F1: 40,00%), R (F1: 41,51%), I (F1: 45,83%) | **CRITICAL REVIEW** |
| High-Confidence P1 Errors | 18 sampel salah klasifikasi dengan keyakinan model $\ge 70\%$ | **CANDIDATE NOISE** |
| Overall Phase 2 Verdict | **NEEDS_DATA_QUALITY_REVIEW** | **HOLD P2** |

> [!WARNING]
> Status **READY_FOR_P2** DITOLAK. Pelatihan ulang (retraining) P2 tidak boleh dimulai sebelum anomali *bounding/clipping* statis diselesaikan dan sampel kandidat label noise diperiksa oleh validator Tuli BISINDO tersertifikasi.

---

## 2. Processed Dataset Inventory & Split Integrity

### 2.1 Verifikasi Fisik dan Pembagian Data
Seluruh 4.462 rekaman dalam `data/processed/bisindo_alphabet/manifest.csv` telah diverifikasi secara fisik di disk. Tidak ditemukan berkas yang hilang, kosong (zero-byte), maupun corrupt. Setiap sampel memiliki pasangan berkas `.jpg` dan `.npy` berdimensi $224 \times 224 \times 3$ (RGB uint8).

Tabel berikut menunjukkan distribusi kelas dan performa evaluasi P1 pada Test Set ($N=670$):

| Kelas | Train ($70\%$) | Val ($15\%$) | Test ($15\%$) | Total | Test Precision | Test Recall | Test F1-Score | Test Support |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 116 | 25 | 24 | 165 | 0.7500 | 0.8750 | **0.8077** | 24 |
| **B** | 118 | 25 | 25 | 168 | 0.7727 | 0.6800 | **0.7234** | 25 |
| **C** | 118 | 26 | 25 | 169 | 0.3030 | 0.4000 | **0.3448** | 25 |
| **D** | 118 | 25 | 26 | 169 | 0.4167 | 0.3846 | **0.4000** | 26 |
| **E** | 118 | 25 | 25 | 168 | 0.7600 | 0.7600 | **0.7600** | 25 |
| **F** | 121 | 26 | 26 | 173 | 0.8947 | 0.6538 | **0.7556** | 26 |
| **G** | 121 | 26 | 26 | 173 | 0.8696 | 0.7692 | **0.8163** | 26 |
| **H** | 121 | 26 | 26 | 173 | 0.8824 | 0.5769 | **0.6977** | 26 |
| **I** | 121 | 26 | 26 | 173 | 0.5000 | 0.4231 | **0.4583** | 26 |
| **J** | 118 | 26 | 25 | 169 | 0.4545 | 0.6000 | **0.5172** | 25 |
| **K** | 121 | 26 | 26 | 173 | 0.7647 | 0.5000 | **0.6047** | 26 |
| **L** | 120 | 26 | 26 | 172 | 0.7826 | 0.6923 | **0.7347** | 26 |
| **M** | 121 | 26 | 26 | 173 | 0.6296 | 0.6538 | **0.6415** | 26 |
| **N** | 121 | 26 | 26 | 173 | 0.6087 | 0.5385 | **0.5714** | 26 |
| **O** | 121 | 26 | 26 | 173 | 0.5357 | 0.5769 | **0.5556** | 26 |
| **P** | 120 | 25 | 26 | 171 | 0.2963 | 0.3077 | **0.3019** | 26 |
| **Q** | 121 | 26 | 26 | 173 | 0.7917 | 0.7308 | **0.7600** | 26 |
| **R** | 120 | 25 | 26 | 171 | 0.4074 | 0.4231 | **0.4151** | 26 |
| **S** | 121 | 26 | 26 | 173 | 0.4857 | 0.6538 | **0.5574** | 26 |
| **T** | 121 | 26 | 26 | 173 | 0.4722 | 0.6538 | **0.5484** | 26 |
| **U** | 121 | 26 | 26 | 173 | 0.6667 | 0.4615 | **0.5455** | 26 |
| **V** | 120 | 26 | 26 | 172 | 0.5333 | 0.6154 | **0.5714** | 26 |
| **W** | 119 | 25 | 26 | 170 | 0.6562 | 0.8077 | **0.7241** | 26 |
| **X** | 122 | 26 | 26 | 174 | 0.7097 | 0.8462 | **0.7719** | 26 |
| **Y** | 122 | 26 | 26 | 174 | 0.7143 | 0.5769 | **0.6383** | 26 |
| **Z** | 122 | 26 | 26 | 174 | 0.8000 | 0.7692 | **0.7843** | 26 |
| **Total / Avg** | **3.123** | **669** | **670** | **4.462** | **0.6508** | **0.6119** | **0.6180** | **670** |

---

## 3. Visual Quality Screening & Artifacts

### 3.1 Profiling Kualitas Citra Empiris
Pemeriksaan menyeluruh terhadap 4.462 citra olahan menghasilkan profil statistik visual sebagai berikut:

| Parameter Kualitas | Mean | Std Dev | Min | Median | Max | Ambang Deteksi Masalah | Jumlah Terflag |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **Luminance (Tingkat Terang)** | 121,32 | 40,09 | 4,58 | 122,80 | 248,68 | $< 30$ (Gelap Ekstrem) / $> 225$ (Terang Ekstrem) | 38 gelap / 57 terang |
| **Contrast (Deviasi Piksel)** | 46,06 | 13,87 | 9,67 | 45,12 | 101,67 | $< 18,0$ (Kontras Rendah / Cuci) | 35 citra |
| **Sharpness (Laplacian Var)** | 496,87 | 642,15 | 5,55 | 254,94 | 10.056,55 | $< 20,0$ (Kabur Parah / Motion Blur) | 36 parah / 120 sedang |
| **Hand Area Ratio** | 0,381 | 0,142 | 0,000 | 0,378 | 0,812 | $< 5\%$ (Tangan Tak Terlihat) / $> 65\%$ (Terlalu Dekat) | 127 kecil / 715 terlalu dekat |
| **Border Clipping Pixels** | 1.842 | 1.120 | 0 | 1.720 | 4.380 | $> 150$ piksel kulit menyentuh 5px batas tepi | **4.236 citra ($94,93\%$)** |

### 3.2 Analisis Kritis Artefak Preprocessing: Center-Square Crop
Temuan paling signifikan dari audit kualitas visual adalah **kegagalan metodologis pada proses cropping awal**:
1. Script preprocessing `scripts/preprocess_bisindo_alphabet.py` (L188–199) melakukan *center-square crop* statis berbasis dimensi minimum (`min(H, W)`) tanpa menggunakan deteksi lokasi tangan (hand bounding box).
2. Akibatnya, pada $94,93\%$ citra ($N=4.236$), bagian tangan—terutama pergelangan tangan, ujung jari telunjuk, atau ibu jari—terpotong langsung oleh batas citra (border clipping).
3. Pemotongan ekstrem ini mengaburkan fitur morfologi tangan yang sangat krusial, seperti orientasi jari pada kelas D dan P, atau konfigurasi lipatan jari pada kelas M dan N.

---

## 4. Error Analysis & Class Confusion Review (Model P1)

### 4.1 Evaluasi Kinerja Model P1 pada Test Set ($N=670$)
- **Akurasi Keseluruhan**: $61,19\%$ (410 benar dari 670 sampel).
- **Total Kesalahan Prediksi**: 260 sampel ($38,81\%$).
- **Distribusi Keyakinan Kesalahan**:
  - Keyakinan Tinggi ($\ge 70\%$): **18 sampel** (Model sangat yakin tetapi keliru).
  - Keyakinan Sedang ($40\% - 70\%$): **163 sampel**.
  - Keyakinan Rendah ($< 40\%$): **79 sampel**.

### 4.2 Analisis Mendalam 5 Kelas Terendah (Bottom-5 Classes)
1. **Kelas P (F1: 30,19% | Recall: 30,77% | Precision: 29,63%)**:
   - Menjadi kelas dengan performa terburuk di seluruh dataset.
   - Dari 26 sampel test kelas P, hanya 8 yang terprediksi benar.
   - Terdistorsi parah ke arah **Kelas D** (8 kali) dan **Kelas T** (5 kali).
2. **Kelas C (F1: 34,48% | Recall: 40,00% | Precision: 30,30%)**:
   - Dari 25 sampel test, 15 salah diklasifikasikan.
   - Terdistorsi ke arah **J** (3 kali), **R** (3 kali), **O** (3 kali), dan **U** (2 kali).
3. **Kelas D (F1: 40,00% | Recall: 38,46% | Precision: 41,67%)**:
   - Dari 26 sampel test, 16 salah diklasifikasikan.
   - Mengalami konfusi masif ke arah **Kelas P sebanyak 12 kali (46,15% dari seluruh sampel D)**.
4. **Kelas R (F1: 41,51% | Recall: 42,31% | Precision: 40,74%)**:
   - Dari 26 sampel test, 15 salah diklasifikasikan.
   - Terdistorsi ke arah **J** (4 kali), **C** (4 kali), **I** (2 kali), dan **Z** (2 kali).
5. **Kelas I (F1: 45,83% | Recall: 42,31% | Precision: 50,00%)**:
   - Dari 26 sampel test, 15 salah diklasifikasikan.
   - Terdistorsi ke arah **C** (5 kali) dan **J** (5 kali).

### 4.3 Matriks Pasangan Konfusi Dominan
Tabel berikut merangkum 10 pasangan kesalahan prediksi terbanyak pada P1:

| No | Pasangan Konfusi (True $\to$ Pred) | Jumlah Kesalahan | Karakteristik Visual & Linguistik BISINDO |
| :---: | :---: | :---: | :--- |
| 1 | **D $\to$ P** | **12** | D (telunjuk mengarah ke atas) vs P (telunjuk mengarah ke bawah/bawah-depan). Kemiringan kamera menyebabkan inversi orientasi. |
| 2 | **N $\to$ M** | **9** | N (2 jari menghadap ke bawah) vs M (3 jari menghadap ke bawah). Lipatan jari manis sering tidak tampak jelas dari sudut depan. |
| 3 | **M $\to$ N** | **8** | Konfusi timbal-balik simetris dengan N $\to$ M. |
| 4 | **P $\to$ D** | **8** | Konfusi timbal-balik simetris dengan D $\to$ P (Total konfusi timbal balik D $\leftrightarrow$ P mencapai 20 sampel). |
| 5 | **U $\to$ C** | **7** | Kelengkungan jari pada sudut diagonal menyerupai kurva gestur C. |
| 6 | **I $\to$ C** | **5** | Jari kelingking yang melengkung atau sudut pengambilan samping menimbulkan ilusi siluet C. |
| 7 | **I $\to$ J** | **5** | **Faktor Modalitas**: Huruf J adalah gestur dinamis (gerakan menggambar kurva J) yang direkam statis sebagai pose jari kelingking tegak, persis sama dengan huruf I. |
| 8 | **J $\to$ I** | **5** | Konfusi timbal-balik sempurna antara pose statis huruf bergerak. |
| 9 | **K $\to$ T** | **5** | Letak ibu jari di antara telunjuk dan jari tengah menimbulkan ambiguitas tinggi jika resolusi lokal rendah. |
| 10 | **P $\to$ T** | **5** | Oklusi jari pada posisi telunjuk menghadap bawah menyerupai struktur kepalan T. |

---

## 5. Perceptual Similarity & Near-Duplicate Analysis

### 5.1 Metodologi Komputasi Hash Persepsi
Untuk mendeteksi duplikasi visual di luar exact cryptographic SHA-256, dilakukan komputasi dua algoritma perceptual hashing pada 64-bit:
1. **Difference Hash (dHash)**: Memetakan gradien intensitas horizontal ($9 \times 8$ piksel).
2. **Perceptual Hash (pHash)**: Memetakan koefisien frekuensi rendah Discrete Cosine Transform ($32 \times 32$ piksel dengan $8 \times 8$ DCT).

### 5.2 Distribusi Jarak Hamming Antar Citra ($N = 4.462$)
Dihitung seluruh kombinasi berpasangan ($> 9,9$ juta pasangan):

| Kategori Hubungan Pasangan | Jarak 0 (Identik) | Jarak 1–2 (Hampir Identik) | Jarak 3–4 (Sangat Mirip) | Jarak 5–6 (Mirip Parsial) | Jarak 7–8 (Konteks Mirip) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Lintas Kelas (Cross-Class)** | 1* | 4 | 37 | 126 | 401 |
| **Lintas Split (Train vs Val/Test)** | 0 | 2 | 15 | 49 | 154 |
| **Intra-Kelas (Same Class)** | 0 | 0 | 1 | 8 | 17 |

*\*Catatan*: Pasangan jarak dHash = 0 ditemukan antara `I/I_0146.jpg` dan `X/X_0166.jpg`. Namun setelah verifikasi pHash ($d=8$), hal ini disebabkan oleh latar belakang polos terang dengan kontras rendah yang mendominasi dHash, bukan karena pose tangan identik.

### 5.3 Temuan Signifikan Lintas-Kelas (Cross-Class Near Duplicates)
Ditemukan pasangan citra antar-kelas yang memiliki kemiripan perseptual sangat tinggi (rerata jarak dHash & pHash $\le 4,0$):
1. **Kelas M vs Kelas N**:
   - Sampel 1: `data/processed/bisindo_alphabet/M/M_0148.jpg` (Asal: `M_Polos Terang_Samsung_A32.jpg`)
   - Sampel 2: `data/processed/bisindo_alphabet/N/N_0148.jpg` (Asal: `N_Polos Terang_Samsung_A32.jpg`)
   - Jarak dHash: 4, Jarak pHash: 4, Rerata: **4,0**.
   - Analisis: Diambil pada sesi pemotretan berturutan oleh pengguna dan perangkat yang sama (`Samsung_A32`), dengan latar belakang dan pencahayaan identik.
2. **Kelas U vs Kelas V**:
   - Sampel 1: `data/processed/bisindo_alphabet/U/U_0092.jpg` (Asal: `U_Body Red_Xiaomi_Redmi Note 9.jpg`)
   - Sampel 2: `data/processed/bisindo_alphabet/V/V_0091.jpg` (Asal: `V_Body Red_Xiaomi_Redmi Note 9.jpg`)
   - Jarak dHash: 4, Jarak pHash: 3, Rerata: **3,5**.
   - Analisis: Jarak antara jari telunjuk dan jari tengah sangat rapat pada gestur V, sehingga secara siluet dan persepsi visual hampir tidak dapat dibedakan dari gestur U.

### 5.4 Evaluasi Kebocoran Data Lintas-Split (Cross-Split Data Leakage)
- Tidak ditemukan duplikat biner eksak lintas-split ($d=0$).
- Namun, ditemukan **17 pasangan dengan jarak dHash $\le 4$ antara Train dan Val/Test**.
- **Penyebab Utama**: Protokol pemisahan data (`train_test_split` stratified acak) dilakukan pada tingkat citra individual (*frame-level*), bukan pada tingkat sesi perekaman atau penandatangan (*signer-level* atau *device-session-level*). Akibatnya, pose tangan dari sesi pemotretan yang sama (misalnya `Samsung_M51` atau `Galaxy A32`) terdistribusi di Train dan Val/Test, menciptakan kebocoran visual latar belakang (*background entanglement leakage*).

---

## 6. Potential Label Noise & Annotation Discrepancies

### 6.1 Indikasi Label Noise Berdasarkan Bukti
Dari hasil investigasi, terdapat indikasi kuat adanya *label noise* pada dataset mentah Mendeley:
1. **Preseden Duplikasi Lintas-Kelas**: Penemuan historis bahwa `D/D_Polos Gelap_iPhone_XR.jpeg` identik biner 100% dengan `P/P_Polos Gelap_iPhone_XR.jpeg` membuktikan bahwa kontributor dataset mentah pernah salah meletakkan berkas yang sama ke dua folder kelas yang berbeda.
2. **Ambiguitas Spasial D vs P**: Kelas D dan P memiliki konfigurasi tangan yang secara struktural berlawanan arah vertikal. Pada foto mentah di mana orientasi kamera miring atau diambil dari sudut atas/bawah, anotasi manual sangat rentan tertukar.
3. **Ambiguitas Modalitas Statis I vs J**: Dalam kamus BISINDO, huruf J dibentuk dengan menggerakkan kelingking membentuk lengkungan J di udara. Ketika difoto dalam bentuk gambar diam tunggal tanpa informasi lintasan gerak, huruf J yang tertangkap adalah pose statis kelingking, yang secara visual identik dengan huruf I. Anotator memberi label 'J' semata-mata karena subjek diinstruksikan memperagakan J, meskipun secara visual citra tersebut adalah 'I'.
4. **Kesalahan Konfusi Tinggi P1 (High-Confidence Errors)**: 18 sampel di mana model P1 memberikan probabilitas output $\ge 70\%$ pada kelas yang berbeda dengan label ground-truth mengindikasikan bahwa fitur visual citra tersebut secara objektif lebih condong ke kelas lain daripada label yang tertera di manifest.

---

## 7. Impact on Model Performance & Generalization

1. **Plafon Kinerja (Performance Ceiling) MobileNetV3-Small**:
   - Model mengalami *plateau* pada akurasi $\sim 60\% - 61\%$ (Val: 60,24%, Test: 61,19%).
   - Plafon ini bukan disebabkan oleh keterbatasan kapasitas arsitektur MobileNetV3-Small, melainkan karena batas teoritis Bayes error rate yang tinggi akibat:
     a) Ambiguitas intrinsik citra statis untuk gestur dinamis (I vs J).
     b) Kerusakan fitur gestur akibat pemotongan batas (*clipping*) pada $94,93\%$ citra.
     c) Potensi label noise pada pasangan D/P, M/N, dan U/V.
2. **Risiko Generalisasi pada Lingkungan Nyata (Field Test / External Validation)**:
   - Pada dataset eksternal nyata (progres saat ini 0/780 foto terkumpul), model yang dilatih dengan citra *center-crop* akan mengalami penurunan performa drastis jika posisi tangan pengguna berada di luar pusat frame atau latar belakang berubah.
   - Tanpa modul deteksi tangan (*hand bounding box detector*), model mengandalkan korelasi semu (*spurious correlations*) antara gestur tangan dan fitur latar belakang perangkat tertentu.

---

## 8. Material for Blind Human Validation Session

Untuk memfasilitasi sesi validasi buta oleh validator Tuli BISINDO, disusun daftar terkurasi sebanyak **36 sampel representatif** yang mencakup seluruh spektrum anomali yang ditemukan.

### 8.1 Format Instrumen Validasi Buta
- Setiap sampel diberi kode anonim (`VAL-REV-001` s/d `VAL-REV-036`) untuk mencegah bias penilai.
- Prediksi model disembunyikan dari lembar kerja validator.
- Validator diminta menilai:
  1. Apakah pose tangan valid sesuai kaidah BISINDO?
  2. Huruf apakah yang sebenarnya diperagakan secara objektif?
  3. Apakah kualitas visual (pencahayaan/ketajaman/pemotongan) memadai untuk dikenali?

### 8.2 Tabel Sampel Kurasi Validasi Buta

| Anonymous ID | Kategori Sampel | Label Asal | Prediksi P1 (Conf) | Flag Kualitas Visual | Berkas Sumber Mentah | Tujuan Evaluasi Validator Tuli |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `VAL-REV-001` | **HIGH_CONF_ERROR** | `K` | T (0.95) | `BORDER_CLIPPING` | `K_Polos Terang_Samsung_A55.jpg` | Verifikasi letak ibu jari: apakah gestur K valid atau sebenarnya T? |
| `VAL-REV-002` | **HIGH_CONF_ERROR** | `C` | J (0.92) | `BORDER_CLIPPING` | `C_Baju_Xiaomi_MI T10.jpg` | Verifikasi kelengkungan jari: apakah membentuk C atau kelingking J? |
| `VAL-REV-003` | **HIGH_CONF_ERROR** | `Y` | V (0.91) | `BORDER_CLIPPING` | `Y_Gelap_Apple_Iphone XS.jpg` | Verifikasi ekstensi ibu jari dan kelingking pada latar gelap. |
| `VAL-REV-004` | **HIGH_CONF_ERROR** | `R` | C (0.91) | `BORDER_CLIPPING` | `R_Polos terang_Infinix_Hot 11s NFC.jpg` | Verifikasi silang jari telunjuk dan tengah (R) vs kelengkungan C. |
| `VAL-REV-005` | **HIGH_CONF_ERROR** | `M` | N (0.85) | `BORDER_CLIPPING` | `M_Background Bebas_Apple_Iphone 15.jpg` | Hitung jumlah jari aktif yang menghadap bawah (3 untuk M vs 2 untuk N). |
| `VAL-REV-006` | **HIGH_CONF_ERROR** | `O` | J (0.85) | `SEVERE_BLUR, BORDER_CLIPPING` | `O_Bebas_Redmi_Note 12 Pro.jpg` | Evaluasi lingkaran O pada citra kabur. |
| `VAL-REV-007` | **HIGH_CONF_ERROR** | `D` | P (0.82) | `BORDER_CLIPPING` | `D_Gelap_Samsung_A22.jpg` | Verifikasi arah telunjuk: apakah tegak ke atas (D) atau miring/bawah (P)? |
| `VAL-REV-008` | **HIGH_CONF_ERROR** | `N` | M (0.81) | `BORDER_CLIPPING` | `N_Bebas_Infinix_Note 30.jpg` | Hitung jumlah jari aktif (2 jari N vs 3 jari M). |
| `VAL-REV-009` | **HIGH_CONF_ERROR** | `J` | I (0.78) | `BORDER_CLIPPING` | `J_Bebas_Samsung_Galaxy A32 5G.jpg` | Evaluasi keterbacaan huruf J dalam modalitas citra diam. |
| `VAL-REV-010` | **HIGH_CONF_ERROR** | `E` | V (0.76) | `NORMAL` | `E_Polos Terang_Samsung_A32.jpg` | Verifikasi lekukan kuku/jari E vs dua jari tegak V. |
| `VAL-REV-011` | **HIGH_CONF_ERROR** | `F` | B (0.75) | `BORDER_CLIPPING` | `F_Polos Terang_Samsung_Galaxy M14 5G.jpg` | Verifikasi lingkaran telunjuk-ibu jari F vs 4 jari tegak B. |
| `VAL-REV-012` | **HIGH_CONF_ERROR** | `N` | M (0.74) | `BORDER_CLIPPING` | `N_Bebas_Infinix_Hot 11s NFC.jpg` | Konfirmasi visual label N vs M pada perangkat Infinix. |
| `VAL-REV-013` | **HIGH_CONF_ERROR** | `T` | K (0.74) | `BORDER_CLIPPING` | `T_Polos Terang_ROG_Phone5.jpg` | Verifikasi letak ibu jari di antara telunjuk (T) vs bentuk V ibu jari (K). |
| `VAL-REV-014` | **HIGH_CONF_ERROR** | `E` | V (0.73) | `BORDER_CLIPPING` | `20240509_183416.jpg` | Verifikasi pose E pada nama berkas bertanggal. |
| `VAL-REV-015` | **HIGH_CONF_ERROR** | `B` | E (0.72) | `BORDER_CLIPPING, OVERSIZED_HAND` | `B_Bebas_Apple_Iphone 12.JPG` | Verifikasi 4 jari tegak (B) vs tekukan jari (E). |
| `VAL-REV-016` | **OUTLIER_BLUR** | `Z` | N/A | `SEVERE_BLUR, BORDER_CLIPPING, OVERSIZED` | `Z_Polos Terang_Samsung_A21S.jpeg` | Uji kelayakan identifikasi pada Laplacian Var sangat rendah ($5,5$). |
| `VAL-REV-017` | **OUTLIER_BLUR** | `O` | N/A | `EXTREME_DARK, LOW_CONTRAST, SEVERE_BLUR` | `O_Background Gelap_Iphone 14 Pro.jpg` | Uji kelayakan gestur O pada kondisi gelap ekstrem dan kabur ($5,8$). |
| `VAL-REV-018` | **OUTLIER_BLUR** | `C` | N/A | `EXTREME_DARK, LOW_CONTRAST, SEVERE_BLUR` | `C_Background Gelap_Iphone 14 Pro.jpg` | Uji kelayakan gestur C pada kondisi gelap ekstrem dan kabur ($6,7$). |
| `VAL-REV-019` | **OUTLIER_BLUR** | `Z` | N/A | `EXTREME_DARK, LOW_CONTRAST, SEVERE_BLUR` | `Z_Background Gelap_Iphone 14 Pro.jpg` | Uji kelayakan gestur Z pada kondisi gelap ekstrem dan kabur ($6,7$). |
| `VAL-REV-020` | **OUTLIER_BLUR** | `V` | N/A | `SEVERE_BLUR, BORDER_CLIPPING` | `V_Polos Terang_Samsung_A21S.jpeg` | Uji kelayakan gestur V pada kondisi motion blur parah ($7,1$). |
| `VAL-REV-021` | **OUTLIER_LIGHTING**| `B` | N/A | `EXTREME_DARK, SMALL_HAND` | `B_Background Gelap_Iphone 14 Pro.jpg` | Uji kelayakan keterbacaan gestur B pada rata-rata luminansi $17,1$. |
| `VAL-REV-022` | **OUTLIER_LIGHTING**| `C` | N/A | `EXTREME_DARK, BORDER_CLIPPING` | `C_Gelap_Apple_Iphone XS.jpg` | Uji keterbacaan siluet C pada pencahayaan rendah (luminansi $23,2$). |
| `VAL-REV-023` | **OUTLIER_LIGHTING**| `C` | N/A | `EXTREME_DARK, BORDER_CLIPPING` | `C_Polos Gelap_Vivo_V23 5G.jpg` | Uji keterbacaan siluet C pada pencahayaan rendah (luminansi $26,6$). |
| `VAL-REV-024` | **OUTLIER_LIGHTING**| `D` | N/A | `EXTREME_DARK, SEVERE_BLUR` | `D_Background Gelap_Iphone 14 Pro.jpg` | Uji keterbacaan telunjuk D pada luminansi ekstrem rendah $13,8$. |
| `VAL-REV-025` | **OUTLIER_CLIPPING**| `H` | N/A | `BORDER_CLIPPING, OVERSIZED_HAND` | `H_Terang_Iph_Iph15.jpg` | Evaluasi dampak pemotongan batas ekstrem pada gestur horizontal H. |
| `VAL-REV-026` | **OUTLIER_CLIPPING**| `Z` | N/A | `BORDER_CLIPPING, OVERSIZED_HAND` | `Z_Polos Terang_Oppo_Reno 11f.jpg` | Evaluasi dampak pemotongan batas ekstrem pada telunjuk Z. |
| `VAL-REV-027` | **OUTLIER_CLIPPING**| `Z` | N/A | `BORDER_CLIPPING, OVERSIZED_HAND` | `Z_Terang_Apple_Iphone XS.jpg` | Evaluasi pemotongan batas pada perangkat iPhone XS. |
| `VAL-REV-028` | **OUTLIER_CLIPPING**| `O` | N/A | `LOW_CONTRAST, BORDER_CLIPPING` | `O_Bebas_Oppo_A Series.jpg.jpg` | Evaluasi pemotongan kontur lingkaran O akibat center-crop. |
| `VAL-REV-029` | **OUTLIER_CLIPPING**| `O` | N/A | `BORDER_CLIPPING, OVERSIZED_HAND` | `O_Bebas_Iphone_14 Pro.jpg` | Evaluasi pemotongan batas tangan berukuran besar pada frame. |
| `VAL-REV-030` | **NEAR_DUPLICATE** | `M` | Mirip N (dist 4.0) | `NEAR_DUP_PAIR` | `M_Polos Terang_Samsung_A32.jpg` | Konfirmasi independen: apakah gestur ini valid M dan berbeda dari N? |
| `VAL-REV-031` | **NEAR_DUPLICATE** | `U` | Mirip V (dist 3.5) | `NEAR_DUP_PAIR` | `U_Body Red_Xiaomi_Redmi Note 9.jpg` | Konfirmasi independen: apakah kerapatan jari valid U dan bukan V? |
| `VAL-REV-032` | **CONTROL_BASELINE**| `A` | A (1.00) | `NORMAL` | `A_Baju_Vivo_V23 5G.jpg` | Kontrol kualitas standar: kepalan tangan A yang jelas dan benar. |
| `VAL-REV-033` | **CONTROL_BASELINE**| `B` | B (1.00) | `NORMAL` | `B_Baju_Xiaomi _Note 8 Pro.jpg` | Kontrol kualitas standar: telapak tangan B tegak sempurna. |
| `VAL-REV-034` | **CONTROL_BASELINE**| `L` | L (1.00) | `NORMAL` | `L_Background Baju (Garis)_Samsung_A53.jpg`| Kontrol kualitas standar: sudut siku-siku L yang jelas. |
| `VAL-REV-035` | **CONTROL_BASELINE**| `O` | O (1.00) | `NORMAL` | `O_Background _Bebas_POCO_F4.jpg` | Kontrol kualitas standar: lingkaran O yang presisi. |
| `VAL-REV-036` | **CONTROL_BASELINE**| `Y` | Y (1.00) | `NORMAL` | `Y_Background Baju (Garis)_Samsung_A53.jpg`| Kontrol kualitas standar: gestur tanduk Y yang jelas. |

---

## 9. Technical Recommendations for P2 Dataset Preparation

Sebelum fase pelatihan P2 (*P2 Retraining*) diizinkan untuk dimulai, tim teknis wajib mengimplementasikan lima perbaikan esensial berikut:

1. **Ganti Center-Crop Statis dengan Deteksi Tangan Dinamis (Dynamic Hand Bounding Box)**:
   - Hentikan pemotongan $224 \times 224$ berbasis pusat citra (`min(H, W)`).
   - Terapkan detektor tangan otomatis (misalnya MediaPipe Hands atau YOLO-Hand) dengan margin bantalan (*padding*) $15\% - 20\%$ di sekeliling batas tangan sebelum di-resize ke $224 \times 224$. Hal ini akan mengeliminasi $94,93\%$ masalah *border clipping*.
2. **Definisi Ulang Modalitas Huruf Dinamis (J dan Z)**:
   - Pisahkan penanganan huruf dinamis (J dan Z) dari klasifikasi citra statis murni, ATAU tentukan *canonical static keyframe* yang disepakati secara resmi oleh ahli BISINDO.
   - Alternatif arsitektur: gunakan modul video temporal atau optical flow / pose trajectory untuk J dan Z.
3. **Penyaringan Sampel Berkualitas Sangat Rendah (Quality Filtering)**:
   - Buang citra dengan *Laplacian variance* $< 15$ (kabur ekstrem tak teridentifikasi) dan luminansi $< 20$ (gelap gulita tanpa detail jari), atau lakukan re-capture terstandarisasi.
4. **Signer-Aware / Session-Aware Data Splitting**:
   - Pembagian Train, Validation, dan Test tidak boleh dilakukan secara acak murni per citra (*stratified frame-level*).
   - Seluruh citra dari perangkat dan sesi pemotretan yang sama (misal `Samsung_A32` atau `iPhone 14 Pro`) harus berada dalam satu split yang sama untuk mencegah *data leakage* latar belakang dan mengukur kemampuan generalisasi model yang sebenarnya.
5. **Eksekusi Validasi Buta Manusia (Blind Human Validation)**:
   - Laksanakan sesi penelaahan 36 sampel pada Tabel 8.2 bersama validator Tuli BISINDO sebelum mengubah atau menghapus anotasi apa pun.

---

## 10. Audit Verdict & Sign-Off Block

### 10.1 Audit Status Determination
Berdasarkan bukti komputasional objektif:
- Struktur dataset processed utuh dan bebas kerusakan biner ($100\%$ terbaca, $0$ zero-byte).
- Namun, terdapat cacat pemrosesan fisik masif (*border clipping* pada $94,93\%$ citra), distorsi modalitas statis pada huruf dinamis (I vs J), keberadaan *near-duplicates* lintas-kelas (M vs N dan U vs V), serta 18 kesalahan prediksi berkeyakinan tinggi yang mengindikasikan *label noise*.

Dengan demikian, status akhir dari Phase 2 Data Quality & Label Validation Audit ditetapkan sebagai:

$$\mathbf{NEEDS\_DATA\_QUALITY\_REVIEW}$$

> [!CAUTION]
> **Peringatan Keras Rekayasa**:
> Status **READY_FOR_P2** secara tegas **DITOLAK**. Pelatihan P2 tanpa perbaikan *bounding box* dan koreksi label hanya akan melatih ulang model pada data yang terpotong dan ambigu, sehingga tidak akan menyelesaikan akar masalah akurasi rendah pada kelas P, C, D, R, dan I.

### 10.2 Sign-Off Block
- **Auditor**: Senior Machine Learning Data Auditor, Computer Vision Specialist, & BISINDO Quality Analyst
- **Modality**: Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
- **Status Validasi Manusia**: `PENDING VALIDATOR`
- **Status Pengumpulan Eksternal**: `NOT STARTED` (0/780)
- **Status Pilot Validasi Buta Kelas A**: `PILOT_HOLD`
- **Tanggal Audit**: 17 November 2026
- **Lokasi Laporan**: `docs/validation_p2/I1_DATA_QUALITY_LABEL_AUDIT.md`

