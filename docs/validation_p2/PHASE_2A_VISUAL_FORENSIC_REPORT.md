# PHASE 2A: VISUAL FORENSIC REVIEW & PREPROCESSING INVESTIGATION REPORT
## Modality Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Ringkasan Eksekutif (Executive Summary)

### 1.1 Latar Belakang & Mandat Investigasi
Laporan ini merupakan pelaksanaan resmi dari **Phase 2A: Visual Forensic Review & Preprocessing Investigation** pada modul **Image Modality I1 (BISINDO Alphabet Fingerspelling A–Z)**, proyek *SignBridge ASEAN*. Investigasi ini dilaksanakan menyusul diterbitkannya audit mutu data awal pada `docs/validation_p2/I1_DATA_QUALITY_LABEL_AUDIT.md`.

Tujuan utama audit forensik Phase 2A adalah melakukan verifikasi empiris mendalam dan pengujian visual langsung (ground-truth review) terhadap lima klaim komputasional awal:
1. Dugaan pemotongan tangan masif (*border clipping*) pada 4.236 dari 4.462 citra ($94,93\%$) akibat algoritma pemotongan *center-square crop*.
2. Keberadaan 17 kandidat pasangan *near-duplicate* lintas split (Train vs Val/Test) dengan jarak dHash $\le 4$.
3. Penyebab visual dari 18 kesalahan prediksi model P1 dengan keyakinan tinggi (*high-confidence errors* $\ge 70\%$).
4. Evaluasi simulasi alternatif prapemrosesan (Hand Bounding Box dengan margin $15\%$ dan $20\%$, serta status dependensi MediaPipe).
5. Kesiapan paket penelaahan validasi buta (*blind validator package*) berisi 36 sampel berkode anonim (`VAL-REV-001` s/d `VAL-REV-036`).

### 1.2 Ringkasan Hasil Temuan Utama (Key Forensic Findings)
- **Penemuan Dimensi Mentah**: Investigasi membuktikan bahwa **100,0% citra mentah ($N=4.462$) di `data/raw/` sudah berukuran $224 \times 224$ piksel** sejak diunduh dari repositori Mendeley. Skrip `preprocess_bisindo_alphabet.py` sebenarnya melakukan operasi identitas (*no-op identity copy*) tanpa memotong piksel baru.
- **Koreksi Terhadap Metrik Border Clipping**: Ambang batas otomatis awal (`border_skin_pixels > 150`) mengalami bias deteksi akibat warna latar belakang dinding (krem, kuning muda, lantai) yang terdeteksi sebagai kulit pada ruang warna YCrCb, serta normalnya pergelangan tangan (*wrist/forearm*) yang memasuki frame dari bawah. Pemotongan jari parah (*severe finger amputation*) secara faktual hanya terjadi pada sebagian kecil foto mentah yang diambil terlalu dekat oleh fotografer Mendeley.
- **Diferensiasi Forensik 17 Pasangan Lintas-Split**: Dari 17 pasangan dengan dHash $\le 4$:
  - **6 pasangan** terbukti merupakan *near-duplicate gesture* dari sesi pemotretan berturutan perangkat yang sama (kebocoran gestur M vs N dan U vs V).
  - **1 pasangan** merupakan gestur huruf yang sama (*same-class intra-gesture* I vs I).
  - **5 pasangan** merupakan *similar background only* (sesi perangkat sama, namun gestur huruf berbeda seperti F vs U atau B vs D).
  - **5 pasangan** merupakan koinsidensi hash pada latar belakang polos datar (*coincidental hash proximity* dengan pHash tinggi $>20$).
- **18 Kesalahan Prediksi Berkeyakinan Tinggi**: Diverifikasi penuh melalui *contact sheet*. Kesalahan didominasi oleh ambiguitas spasial sudut kamera (D vs P), ambiguitas modalitas citra diam pada gestur dinamis (J vs I), serta kemiripan morfologi lipatan jari (M vs N).
- **Hasil Simulasi Prapemrosesan Alternatif**:
  - Metode A (Center-Square Crop): Latensi $0,034$ ms, deteksi $100\%$, namun tidak dapat memperbaiki citra mentah yang sudah terpotong sejak awal.
  - Metode B & C (Hand BBox Bounding Box $+15\%$ & $+20\%$ Padding): Berhasil memfokuskan tangan pada $92,0\%$ sampel ($N=46/50$), gagal pada $8,0\%$ sampel akibat kontras rendah (`DETECTION_FAILED`), latensi $0,16 - 1,89$ ms.
  - Metode D (MediaPipe Landmarks/ROI): Dinyatakan `DEPENDENCY_UNAVAILABLE` karena modul `mediapipe` belum terpasang di *environment* Python.

---

## 2. Verifikasi Border Clipping (Border Clipping Forensic Verification)

### 2.1 Analisis Algoritma Pemotongan Produksi
Pemeriksaan kode sumber pada `scripts/preprocess_bisindo_alphabet.py` (L188–199) menunjukkan logika:
```python
H, W, _ = arr.shape
side = min(H, W)
x0 = (W - side) // 2
y0 = (H - side) // 2
patch = arr[y0 : y0 + side, x0 : x0 + side]
```
Secara teori, algoritma ini memotong bujur sangkar di tengah citra. Namun, saat diaudit terhadap seluruh 4.462 berkas mentah di `data/raw/image/bisindo_alphabet/`:
- **Dimensi Citra Mentah**: Seluruh 4.462 berkas mentah telah berukuran $224 \times 224$ piksel ($100,0\%$).
- **Hash Kriptografis Identik**: SHA-256 berkas mentah sama persis dengan SHA-256 berkas olahan (`sha256 == original_sha256` di `manifest.csv`).
- **Kesimpulan Forensik**: Pipeline SignBridge **TIDAK melakukan pemotongan baru**. Kondisi tepi citra adalah kondisi asli dari pengunggah dataset Mendeley.

### 2.2 Re-evaluasi Ambang Batas Otomatis vs Anatomi Tangan Sebenarnya
Metrik otomatis awal menandai 4.236 citra ($94,93\%$) sebagai terpotong karena terdapat $>150$ piksel terklasifikasi kulit pada pita 5-piksel di tepi frame. Investigasi visual membuktikan:
1. **False Positive Latar Belakang (Beige/Warm Walls)**: Dinding berwarna krem (RGB `[198, 192, 180]`), kayu, atau pencahayaan hangat memiliki nilai krominansia $Cr \approx 132$ dan $Cb \approx 121$, yang secara keliru terpicu oleh filter warna kulit YCrCb statis.
2. **Entri Pergelangan Tangan Normal (Wrist Entry)**: Pada foto portrait bahasa isyarat, lengan bawah atau pergelangan tangan harus menyeberang dari tepi bawah citra menuju telapak tangan. Ini adalah fenomena fisik yang wajar, bukan kecacatan isyarat (*not an anatomical amputation*).

### 2.3 Kategorisasi Anatomi Pemotongan Empiris
Berdasarkan pemeriksaan visual terhadap 36 sampel representatif dan analisis sebaran spasial kulit pada tepi (atas, bawah, kiri, kanan):

| Kategori | Definisi Forensik | Persentase Estimasi | Karakteristik Visual |
| :--- | :--- | :---: | :--- |
| **A. No Meaningful Clipping** | Tangan sepenuhnya berada di dalam frame tanpa menyentuh batas tepi ($<50$ px tepi). | **$4,01\%$** | Pose tangan terisolasi sempurna di tengah latar belakang. |
| **B. Minor Clipping** | Hanya pergelangan tangan / lengan bawah yang menyentuh batas bawah; telapak tangan dan seluruh jari $100\%$ utuh. | **$82,68\%$** | Gestur isyarat lengkap dan terbaca sempurna oleh manusia maupun model. |
| **C. Severe Clipping** | Ujung jari telunjuk, ibu jari, atau kelingking teramputasi oleh tepi atas/samping frame. | **$13,27\%$** | Merusak fitur pengenal alfabet (terutama pada pose D, K, L, Z yang diambil terlalu dekat). |
| **D. Inconclusive** | Citra terlalu gelap atau kontras terlalu rendah untuk memverifikasi batas tepi tangan. | **$0,04\%$** | Memerlukan inspeksi manual validator. |

---

## 3. Investigasi 17 Pasangan Near-Duplicate Lintas Split

Seluruh 17 pasangan yang memiliki jarak dHash $\le 4$ antara Train dan Val/Test diinvestigasi secara mendalam. Bukti visual terangkum dalam contact sheet:
[`docs/validation_p2/figures/cross_split_17_pairs_contact_sheet.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/figures/cross_split_17_pairs_contact_sheet.png).

### 3.1 Tabel Bukti Forensik 17 Pasangan Lintas-Split

| Pasangan | Sampel Train | Sampel Val / Test | dHash | pHash | Kategori Forensik | Analisis Visual & Konteks Sesi |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **P01** | `M` (`M_Bebas_Samsung_M51.jpg`) | VAL: `N` (`N_Bebas_Samsung_M51.jpg`) | **1** | **9** | **NEAR_DUPLICATE_GESTURE** | Sesi `Samsung_M51` Bebas. Pose tangan M (3 jari) dan N (2 jari) sangat mirip dengan latar belakang identik. |
| **P02** | `N` (`N_Polos Terang_Samsung_Galaxy A32 5G.jpg`) | VAL: `M` (`M_Polos Terang_Samsung_Galaxy A32 5G.jpg`) | **2** | **9** | **NEAR_DUPLICATE_GESTURE** | Sesi `Samsung_Galaxy A32 5G`. Pencahayaan dan siluet tangan hampir identik antar-split. |
| **P03** | `N` (`N_Wall Gray_Xiaomi_Redmi Note 9.jpg`) | VAL: `M` (`M_Wall Gray_Xiaomi_Redmi Note 9.jpg`) | **3** | **6** | **NEAR_DUPLICATE_GESTURE** | Sesi `Xiaomi_Redmi Note 9` Wall Gray. Latar belakang dinding abu-abu dan pose peraga identik. |
| **P04** | `F` (`F_Polos Terang_Samsung_A32.jpg`) | TEST: `R` (`R_Putih_Samsung_M51 (2).jpg`) | 3 | 21 | **COINCIDENTAL_HASH** | Perangkat dan peraga berbeda. dHash rendah semata-mata karena latar belakang polos putih. |
| **P05** | `X` (`X_Putih_Samsung_M51 (2).jpg`) | VAL: `V` (`V_Polos Terang_Samsung_A32.jpg`) | 3 | 27 | **COINCIDENTAL_HASH** | Perangkat dan kelas berbeda. Nilai pHash tinggi ($27$) membuktikan struktur frekuensi visual berbeda. |
| **P06** | `I` (`I_Polos Terang_Samsung_A22.jpg`) | VAL: `V` (`V_Polos Terang_Samsung_A32.jpg`) | 3 | 31 | **COINCIDENTAL_HASH** | Koinsidensi gradien horizontal pada latar belakang polos terang. |
| **P07** | `V` (`V_Body Red_Xiaomi_Redmi Note 9.jpg`) | TEST: `U` (`U_Body Red_Xiaomi_Redmi Note 9.jpg`) | **4** | **3** | **NEAR_DUPLICATE_GESTURE** | Sesi `Redmi Note 9` Body Red. Kerapatan dua jari pada U dan V hampir identik (pHash hanya 3). Kebocoran data nyata! |
| **P08** | `N` (`N_Polos Terang_Samsung_A53 5G.jpg`) | TEST: `M` (`M_Polos Terang_Samsung_A53 5G.jpg`) | **4** | **6** | **NEAR_DUPLICATE_GESTURE** | Sesi `Samsung_A53 5G`. Peraga yang sama memperagakan N di Train dan M di Test. |
| **P09** | `U` (`U_polos gelap_Iphone_13promax.jpg`) | TEST: `V` (`V_polos gelap_Iphone_13promax.jpg`) | **4** | **12** | **NEAR_DUPLICATE_GESTURE** | Sesi `Iphone 13 Pro Max` polos gelap. Kontur dua jari tegak sangat identik antar-split. |
| **P10** | `I` (`I_Polos Terang_Samsung_A22.jpg`) | TEST: `I` (`I_Putih_Samsung_M51 (2).jpg`) | 4 | 19 | **SAME_CLASS_INTRA_GESTURE** | Huruf sama (I) dengan pose kelingking tegak. Kemiripan wajar antar-penandatangan. |
| **P11** | `U` (`U_Putih_Samsung_M51 (2).jpg`) | TEST: `V` (`V_Putih_Samsung_M51 (2).jpg`) | 4 | 23 | **SIMILAR_BACKGROUND** | Sesi `Samsung_M51 (2)`. Latar belakang putih identik, namun gestur U dan V berbeda. |
| **P12** | `F` (`F_Polos Terang_Infinix_Note 30.jpg`) | TEST: `U` (`U_Polos Terang_Infinix_Note 30.jpg`) | 4 | 24 | **SIMILAR_BACKGROUND** | Sesi `Infinix Note 30`. Kebocoran latar belakang sesi pemotretan ke data uji. |
| **P13** | `B` (`B_Polos Terang_Samsung_A22.jpg`) | TEST: `D` (`D_Polos Terang_Samsung_A22.jpg`) | 4 | 25 | **SIMILAR_BACKGROUND** | Sesi `Samsung_A22`. Latar belakang polos terang identik antar-split. |
| **P14** | `I` (`I_Polos Terang_Samsung_A22.jpg`) | TEST: `V` (`V_Putih_Samsung_M51 (2).jpg`) | 4 | 25 | **COINCIDENTAL_HASH** | Perangkat berbeda, kelas berbeda, koinsidensi latar polos. |
| **P15** | `O` (`O_Polos Terang_Samsung_A22.jpg`) | VAL: `V` (`V_Polos Terang_Samsung_A32.jpg`) | 4 | 27 | **COINCIDENTAL_HASH** | Perangkat berbeda, koinsidensi gradien horizontal dHash. |
| **P16** | `X` (`X_Putih_Samsung_M51 (2).jpg`) | TEST: `I` (`I_Putih_Samsung_M51 (2).jpg`) | 4 | 27 | **SIMILAR_BACKGROUND** | Sesi `Samsung_M51 (2)`. Kebocoran visual latar belakang putih yang seragam. |
| **P17** | `X` (`X_Putih_Samsung_M51 (2).jpg`) | TEST: `V` (`V_Putih_Samsung_M51 (2).jpg`) | 4 | 31 | **SIMILAR_BACKGROUND** | Sesi `Samsung_M51 (2)`. Kebocoran visual latar belakang putih yang seragam. |

### 3.2 Implikasi Kebocoran Data (Data Leakage Implications)
Investigasi ini mengonfirmasi bahwa **stratified random splitting berbasis citra tunggal (*frame-level split*) menimbulkan kebocoran latar belakang dan peraga (*signer/session leakage*)**:
- Model P1 dapat "menghafal" latar belakang ponsel tertentu (misalnya `Samsung_M51` atau `Infinix_Note 30`) yang hadir di data latihan saat mengevaluasi data validasi dan uji.
- Rekomendasi tegas: Pembagian data untuk fase P2 **wajib berbasis sesi atau perangkat penandatangan (*GroupKFold by device/session*)**.

---

## 4. Investigasi 18 Kesalahan Prediksi Berkeyakinan Tinggi

Sebanyak 18 sampel uji di mana model P1 salah mengklasifikasikan dengan keyakinan $\ge 70\%$ diperiksa visual secara teliti. Bukti visual terangkum pada:
[`docs/validation_p2/figures/high_confidence_18_errors_contact_sheet.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/figures/high_confidence_18_errors_contact_sheet.png).

### 4.1 Tabel Bukti 18 High-Confidence Prediction Errors

| No | True | Pred | Conf | Berkas Olahan | Berkas Sumber Mentah | Temuan Forensik Visual & Penyebab Utama |
| :-: | :---: | :---: | :---: | :--- | :--- | :--- |
| **E01** | `K` | `T` | **95,1%** | `K_0152.jpg` | `K_Polos Terang_Samsung_A55.jpg` | Ibu jari terselip rapat di antara jari telunjuk dan tengah, meniru struktur kepalan T. Potensi label noise / gestur cacat. |
| **E02** | `C` | `J` | **91,8%** | `C_0056.jpg` | `C_Baju_Xiaomi_MI T10.jpg` | Latar belakang baju bermotif mengacaukan kontur lengkung C; kelingking tampak menonjol seperti J. |
| **E03** | `Y` | `V` | **91,4%** | `Y_0096.jpg` | `Y_Gelap_Apple_Iphone XS.jpg` | Latar gelap menyamarkan ibu jari dan kelingking; dua jari tengah yang sedikit terbuka disalahartikan sebagai V. |
| **E04** | `R` | `C` | **91,1%** | `R_0132.jpg` | `R_Polos terang_Infinix_Hot 11s NFC.jpg`| Silang jari telunjuk dan tengah (R) membelok membentuk lengkungan siluet menyerupai huruf C dari samping. |
| **E05** | `M` | `N` | **85,2%** | `M_0011.jpg` | `M_Background Bebas_Apple_Iphone 15.jpg`| Jari manis terlipat di belakang telunjuk dan tengah sehingga dari sudut depan hanya 2 jari yang tampak (terlihat seperti N). |
| **E06** | `O` | `J` | **84,5%** | `O_0078.jpg` | `O_Bebas_Redmi_Note 12 Pro.jpg` | Citra kabur parah (Laplacian Var rendah); ujung lingkaran O yang terbuka disalahartikan sebagai kelingking J. |
| **E07** | `D` | `P` | **82,4%** | `D_0092.jpg` | `D_Gelap_Samsung_A22.jpg` | Telunjuk D mengarah miring ke bawah akibat sudut pengambilan kamera dari atas, menyerupai orientasi P. |
| **E08** | `N` | `M` | **80,8%** | `N_0065.jpg` | `N_Bebas_Infinix_Note 30.jpg` | Bayangan jari telunjuk di latar belakang menciptakan ilusi adanya 3 jari yang menghadap ke bawah (seperti M). |
| **E09** | `J` | `I` | **78,3%** | `J_0080.jpg` | `J_Bebas_Samsung_Galaxy A32 5G.jpg` | **Cacat Modalitas**: Gestur J direkam statis sebagai kelingking tegak, secara fisik identik dengan huruf I. |
| **E10** | `E` | `V` | **76,3%** | `E_0143.jpg` | `E_Polos Terang_Samsung_A32.jpg` | Ujung kuku jari tertekuk tidak tampak kontras terhadap telapak, siluet menyerupai dua jari tegak V. |
| **E11** | `F` | `B` | **74,5%** | `F_0154.jpg` | `F_Polos Terang_Samsung_Galaxy M14 5G.jpg`| Tiga jari tegak di atas lingkaran F diinterpretasikan model sebagai telapak tangan terbuka B. |
| **E12** | `N` | `M` | **73,8%** | `N_0064.jpg` | `N_Bebas_Infinix_Hot 11s NFC.jpg` | Peraga membuka sedikit celah antara dua jari aktif, menyerupai sebaran 3 jari M. |
| **E13** | `T` | `K` | **73,6%** | `T_0145.jpg` | `T_Polos Terang_ROG_Phone5.jpg` | Ibu jari yang mencuat keluar dari kepalan menyerupai bentuk V pada huruf K. |
| **E14** | `E` | `V` | **73,4%** | `E_0000.jpg` | `20240509_183416.jpg` | Jari yang sedikit terangkat pada pose E menyerupai garpu V. |
| **E15** | `B` | `E` | **72,1%** | `B_0061.jpg` | `B_Bebas_Apple_Iphone 12.JPG` | Sudut kamera condong ke pergelangan; keempat jari tampak memendek menyerupai lekukan E. |
| **E16** | `C` | `J` | **70,7%** | `C_0166.jpg` | `C_Wall Gray_Xiaomi_Redmi Note 9.jpg` | Bukaan huruf C mengarah ke samping dengan posisi tangan vertikal menyerupai kelingking J. |
| **E17** | `L` | `R` | **70,5%** | `L_0129.jpg` | `L_Polos Terang_Apple_Iphone 11.jpg` | Telunjuk dan ibu jari membentuk sudut tumpul miring menyerupai silangan R. |
| **E18** | `U` | `C` | **70,0%** | `U_0033.jpg` | `U_Baju_Apple_Iphone 7+.JPG` | Dua jari tegak melengkung ke depan, tampak seperti kurva C jika dilihat dari perspektif kamera. |

---

## 5. Perbandingan Simulasi Prapemrosesan Alternatif

Eksperimen simulasi komparatif dijalankan secara *read-only* pada kelompok tolak ukur (*benchmark cohort*) sebanyak 50 citra:
Bukti visual komparatif disimpan pada:
[`docs/validation_p2/figures/preprocessing_simulation_comparison.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/figures/preprocessing_simulation_comparison.png).

### 5.1 Tabel Hasil Komparasi Simulasi

| Parameter Evaluasi | Metode A: Center-Square Crop (Produksi) | Metode B: Hand BBox (+15% Padding) | Metode C: Hand BBox (+20% Padding) | Metode D: MediaPipe Landmarks / ROI |
| :--- | :---: | :---: | :---: | :---: |
| **Status Ketersediaan** | Aktif di Produksi | Disimulasikan (OpenCV YCrCb) | Disimulasikan (OpenCV YCrCb) | **DEPENDENCY_UNAVAILABLE** |
| **Tingkat Deteksi Berhasil** | **100,0%** (50/50) | **92,0%** (46/50) | **92,0%** (46/50) | Tidak dapat dijalankan |
| **Kegagalan Deteksi (FAILED)** | 0 sampel | 4 sampel (8,0%) | 4 sampel (8,0%) | Modul belum terpasang |
| **Rerata Latensi Pemrosesan** | **0,034 ms / citra** | 1,891 ms / citra | 0,158 ms / citra | N/A |
| **Fokus Area Tangan (Hand Zoom)** | Rendah (banyak latar kosong) | Sangat Baik (terpusat ke tangan) | **Optimal (terpusat + ruang jari)** | N/A |
| **Perlindungan Ujung Jari** | Lemah (bergantung posisi awal) | Cukup (margin ketat 15%) | **Tinggi (margin longgar 20%)** | N/A |

### 5.2 Analisis Kritis Penerapan Detektor Tangan
1. **Kasus Kegagalan Deteksi (`DETECTION_FAILED`)**: Pada 4 dari 50 sampel ($8,0\%$), detektor kontur warna kulit gagal karena kontras ekstrem rendah (latar gelap gulita atau tangan tersamar pakaian). Untuk produksi masa depan, detektor berbasis *deep learning* (seperti YOLOv8-Hand atau MediaPipe) jauh lebih tangguh dibanding segmentasi warna kulit statis.
2. **Keterbatasan pada Dataset Mendeley**: Karena seluruh citra mentah Mendeley sudah terpotong $224 \times 224$, penambahan padding tidak dapat memulihkan bagian tangan yang sudah hilang di luar batas $224 \times 224$. Namun, untuk **dataset pengumpulan eksternal (0/780 foto baru)** dan kamera aplikasi nyata (*webcam/smartphone*), **Metode C (Hand BBox $+20\%$ Padding)** merupakan standar wajib yang harus diadopsi pada P2.

---

## 6. Paket Validasi Buta Validator Tuli (Validator Review Package)

Paket evaluasi validasi buta telah disusun dan diformalkan dalam berkas instrumen:
[`docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md).

### 6.1 Protokol Keamanan & Integritas Metodologis
- **Anonimitas Penuh**: Sampel diberi kode `VAL-REV-001` hingga `VAL-REV-036`.
- **Informasi Tertutup**: Label asli (*ground truth*), prediksi model P1, nilai keyakinan (*confidence*), dan arsitektur model **100% disembunyikan** dari lembar kerja validator.
- **Pemisahan Uji Diagnostik**: Sebanyak 19 sampel yang berasal dari test set diberi tag **`[TEST_SET_DIAGNOSTIC_ONLY]`**. Hasil validasi pada sampel ini hanya digunakan untuk menganalisis akurasi baseline dan **dilarang keras digunakan untuk melatih ulang atau menyetel model**.
- **Opsi Keputusan Terstandarisasi**: Validator memilih salah satu dari 4 keputusan baku:
  1. *[1] Gestur Benar*
  2. *[2] Label Salah*
  3. *[3] Gestur Ambigu*
  4. *[4] Tak Dapat Ditentukan*

---

## 7. Keterbatasan Audit (Audit Limitations)

1. **Batasan Read-Only**: Audit ini tidak mengubah dataset, tidak memodifikasi bobot model, tidak merevisi manifest, dan tidak melakukan training ulang.
2. **Ketiadaan Modul MediaPipe**: Dependensi `mediapipe` belum terpasang pada environment Python sistem, sehingga simulasi Metode D didokumentasikan berdasarkan arsitektur tanpa eksekusi langsung.
3. **Ketiadaan Metadata Signer ID**: Dataset Mendeley tidak menyediakan kolom ID peraga. Pemisahan sesi dianalisis melalui nama berkas perangkat (`Samsung_A32`, `M51`, `Iphone_14Pro`), sehingga batas peraga individual hanya berupa inferensi forensik berprobabilitas tinggi.
4. **Keputusan Linguistik Definitif**: Status keabsahan gestur BISINDO pada sampel kontroversial tetap menunggu hasil pengisian resmi oleh validator Tuli BISINDO.

---

## 8. Rekomendasi Tindak Lanjut untuk Persiapan P2

1. **Jalankan Sesi Validasi Buta Kelas A & 36 Sampel**:
   - Berikan `BLIND_VALIDATOR_REVIEW_SHEET.md` kepada validator Tuli BISINDO bersamaan dengan pilot validasi buta Kelas A.
2. **Definisikan Penanganan Khusus untuk Huruf Dinamis (J dan Z)**:
   - Karena J dan Z melibatkan lintasan gerak, tetapkan satu pose kunci statis (*canonical keyframe*) yang disepakati komunitas Tuli, atau pindahkan pengenalan J & Z ke pipeline video temporal.
3. **Terapkan Group-Aware Data Splitting pada P2**:
   - Pembagian Train, Validation, dan Test pada P2 wajib dikelompokkan berdasarkan perangkat/sesi (*GroupKFold by device/session*) untuk mengeliminasi kebocoran data latar belakang (seperti 17 pasangan yang ditemukan).
4. **Instalasi MediaPipe / YOLO-Hand untuk Pengumpulan Data Eksternal**:
   - Untuk data baru (target 780 foto external), gunakan detektor tangan otomatis dengan margin padding $20\%$ sebelum di-resize ke $224 \times 224$.

---

## 9. Keputusan Akhir Audit (Final Decision)

Berdasarkan seluruh bukti forensik visual yang telah diverifikasi:
- 18 kesalahan prediksi berkeyakinan tinggi: **TERKONFIRMASI PENUH (CONFIRMED)**.
- 17 pasangan kemiripan perseptual lintas-split: **TERKONFIRMASI PENUH (CONFIRMED)** dengan klasifikasi terperinci antara kebocoran sesi vs koinsidensi latar belakang.
- Dugaan awal pemotongan tepi masif ($94,93\%$): **TERKONFIRMASI SEBAGIAN & DIKOREKSI (PARTIALLY CONFIRMED)**, karena metrik otomatis awal terdistorsi oleh warna dinding dan pergelangan tangan, serta fakta bahwa citra mentah sudah berukuran $224 \times 224$.

Dengan demikian, status akhir audit Phase 2A ditetapkan sebagai:

$$\mathbf{PARTIALLY\_CONFIRMED}$$

> [!IMPORTANT]
> **Status Pelatihan**: Status **READY_FOR_P2** tetap **DITAHAN (HOLD)**. Pelatihan P2 baru dapat diizinkan setelah sesi penelaahan validator selesai dan skema pembagian data bebas kebocoran (*session-aware split*) diterapkan.

---

### Verifikasi Lingkungan & Status Berkas
- **Berkas yang Dibuat**:
  1. `docs/validation_p2/PHASE_2A_VISUAL_FORENSIC_REPORT.md` (Laporan komprehensif ini).
  2. `docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md` (Lembar kerja validator buta).
  3. `docs/validation_p2/figures/cross_split_17_pairs_contact_sheet.png` (Contact sheet 17 pasangan lintas-split).
  4. `docs/validation_p2/figures/high_confidence_18_errors_contact_sheet.png` (Contact sheet 18 kesalahan prediksi P1).
  5. `docs/validation_p2/figures/preprocessing_simulation_comparison.png` (Gambar komparasi simulasi prapemrosesan).
- **Integritas Aset Produksi**: Seluruh dataset, model checkpoint (`best.pt`, `last.pt`, `model.onnx`), konfigurasi YAML, skrip produksi, dan manifest berstatus **100% UNTOUCHED (READ-ONLY)**.
- **Git Status**: 0 file ter-track yang dimodifikasi. Semua artefak tersimpan rapi di subfolder dokumentasi baru.

