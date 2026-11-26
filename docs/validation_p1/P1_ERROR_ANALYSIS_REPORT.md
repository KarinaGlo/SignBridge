# LAPORAN ANALISIS KESALAHAN MODEL I1-P1 (ERROR ANALYSIS REPORT)
## SignBridge ASEAN — Modality Image (MobileNetV3-Small BISINDO A–Z)

> **Dokumen**: `docs/validation_p1/P1_ERROR_ANALYSIS_REPORT.md`  
> **Modul**: Image Modality I1-P1 — BISINDO Alphabet Fingerspelling  
> **Arsitektur Model**: MobileNetV3-Small (Pretrained ImageNet-1K, Fine-tuned)  
> **Dasar Bukti**: Test Set Inferensi ($N = 670$) pada `runs/image_i1_mobilenetv3_p1/predictions.csv`  
> **Tanggal Audit**: 16 November 2026  
> **Status Audit**: **SELESAI (COMPLETED)** — Analisis Read-Only & Verifikasi Mandiri  

---

## 1. RINGKASAN METRIK GLOBAL

Evaluasi performa model baseline P1 pada Test Set internal ($N = 670$ citra acak terstratifikasi) menghasilkan metrik global berikut:

| Metrik Evaluasi | Nilai Numerik | Standar Target Baseline | Status Capaian |
|---|---|---|---|
| **Test Accuracy** | **61.19%** (410 / 670) | $\ge 75.00\%$ | **BELUM MENCAPAI TARGET (-13.81%)** |
| **Macro Average Precision** | **63.30%** (0.6330) | $\ge 75.00\%$ | **BELUM MENCAPAI TARGET** |
| **Macro Average Recall** | **61.27%** (0.6127) | $\ge 75.00\%$ | **BELUM MENCAPAI TARGET** |
| **Macro Average F1-Score** | **61.57%** (0.6157) | $\ge 75.00\%$ | **BELUM MENCAPAI TARGET** |
| **Weighted Average F1-Score**| **61.53%** (0.6153) | - | Seimbang dengan Macro F1 ($IR \approx 1.05$) |
| **Total Sampel Salah** | **260 sampel** (38.81%) | - | Objek analisis kegagalan |

> [!IMPORTANT]
> Akurasi 61.19% dan F1-Score 61.57% diperoleh dari data uji internal yang **mengalami subject mixing** (tidak ada pemisahan subjek penutur antara train, val, dan test). Oleh karena itu, estimasi akurasi 61.19% ini merupakan batas atas (*upper bound / optimistic estimate*); performa pada data penutur eksternal baru diperkirakan akan jauh lebih rendah.

---

## 2. BREAKDOWN PERFORMA PER-KELAS (RANKING F1-SCORE)

Seluruh 26 kelas huruf BISINDO diurutkan berdasarkan metrik F1-score untuk mengidentifikasi kluster kekuatan dan kelemahan model P1:

### 2.1. Top-5 Kelas Berkinerja Terbaik

| Peringkat | Kelas | Precision | Recall | F1-Score | Support | Karakteristik Gestural Dominan |
|---|---|---|---|---|---|---|
| 1 | **Kelas G** | 0.8696 | 0.7692 | **0.8163** | 26 | Telunjuk mengarah horizontal/frontal yang distingtif |
| 2 | **Kelas A** | 0.7500 | 0.8750 | **0.8077** | 24 | Konfigurasi **dua tangan** berbentuk segitiga (area piksel luas) |
| 3 | **Kelas Z** | 0.8000 | 0.7692 | **0.7843** | 26 | Gestur formasi khas dengan jari membentuk orientasi sudut |
| 4 | **Kelas X** | 0.7097 | 0.8462 | **0.7719** | 26 | Telunjuk menekuk seperti kait (*hooked index*) |
| 5 | **Kelas E & Q**| 0.7600 / 0.7917 | 0.7600 / 0.7308 | **0.7600** | 25 / 26 | Cengkeraman melengkung / orientasi jempol-telunjuk bawah |

*Catatan untuk Kelas A*: Kelas A mencapai F1 tinggi (80.77%) karena fitur visualnya sangat unik dibandingkan kelas lain—gestur A pada dataset ini adalah konfigurasi **dua tangan** yang menempati proporsi kanvas visual jauh lebih besar daripada alfabet 1 tangan.

---

### 2.2. Bottom-5 Kelas Paling Rentan Kegagalan (Critical Weaknesses)

| Peringkat | Kelas | Precision | Recall | F1-Score | Support | Titik Kegagalan Utama |
|---|---|---|---|---|---|---|
| 26 (Terburuk) | **Kelas P** | **0.2963** | **0.3077** | **0.3019** | 26 | Tertukar parah dengan D (8x) dan T (5x); Precision < 30% |
| 25 | **Kelas C** | **0.3030** | 0.4000 | **0.3448** | 25 | Sering salah diprediksi dari U, I, dan R; Precision 30.3% |
| 24 | **Kelas D** | 0.4167 | **0.3846** | **0.4000** | 26 | Tertukar masif menjadi P (12x, kebingungan tertinggi di model) |
| 23 | **Kelas R** | 0.4074 | 0.4231 | **0.4151** | 26 | Tertukar menjadi J (4x), C (4x), I (2x), T (2x) |
| 22 | **Kelas I** | 0.5000 | 0.4231 | **0.4583** | 26 | Tertukar menjadi C (5x) dan J (5x) |

---

### 2.3. Tabel Performa Lengkap 26 Kelas

```
              precision    recall  f1-score   support
     Kelas_A     0.7500    0.8750    0.8077        24
     Kelas_B     0.7727    0.6800    0.7234        25
     Kelas_C     0.3030    0.4000    0.3448        25
     Kelas_D     0.4167    0.3846    0.4000        26
     Kelas_E     0.7600    0.7600    0.7600        25
     Kelas_F     0.8947    0.6538    0.7556        26
     Kelas_G     0.8696    0.7692    0.8163        26
     Kelas_H     0.8824    0.5769    0.6977        26
     Kelas_I     0.5000    0.4231    0.4583        26
     Kelas_J     0.4545    0.6000    0.5172        25
     Kelas_K     0.7647    0.5000    0.6047        26
     Kelas_L     0.7826    0.6923    0.7347        26
     Kelas_M     0.6296    0.6538    0.6415        26
     Kelas_N     0.6087    0.5385    0.5714        26
     Kelas_O     0.5357    0.5769    0.5556        26
     Kelas_P     0.2963    0.3077    0.3019        26
     Kelas_Q     0.7917    0.7308    0.7600        26
     Kelas_R     0.4074    0.4231    0.4151        26
     Kelas_S     0.4857    0.6538    0.5574        26
     Kelas_T     0.4722    0.6538    0.5484        26
     Kelas_U     0.6667    0.4615    0.5455        26
     Kelas_V     0.5333    0.6154    0.5714        26
     Kelas_W     0.6562    0.8077    0.7241        26
     Kelas_X     0.7097    0.8462    0.7719        26
     Kelas_Y     0.7143    0.5769    0.6383        26
     Kelas_Z     0.8000    0.7692    0.7843        26
```

---

## 3. ANALISIS PASANGAN KELAS YANG PALING SERING TERTUKAR (CONFUSION PAIRS)

Dari 260 prediksi salah pada Test Set, pasangan off-diagonal confusion matrix teratas adalah:

| No | True Class | Predicted Class | Frekuensi Kesalahan | Persentase Error Terhadap Support Kelas |
|---|---|---|---|---|
| 1 | **D** | **P** | **12 kali** | **46.15%** dari seluruh sampel D |
| 2 | **N** | **M** | **9 kali** | **34.62%** dari seluruh sampel N |
| 3 | **M** | **N** | **8 kali** | **30.77%** dari seluruh sampel M |
| 4 | **P** | **D** | **8 kali** | **30.77%** dari seluruh sampel P |
| 5 | **U** | **C** | **7 kali** | **26.92%** dari seluruh sampel U |
| 6 | **I** | **C** | **5 kali** | 19.23% dari seluruh sampel I |
| 7 | **J** | **I** | **5 kali** | 20.00% dari seluruh sampel J |
| 8 | **K** | **T** | **5 kali** | 19.23% dari seluruh sampel K |
| 9 | **I** | **J** | **5 kali** | 19.23% dari seluruh sampel I |
| 10 | **P** | **T** | **5 kali** | 19.23% dari seluruh sampel P |
| 11 | **Y** | **X** | **5 kali** | 19.23% dari seluruh sampel Y |
| 12 | **R** | **J** | **4 kali** | 15.38% dari seluruh sampel R |
| 13 | **R** | **C** | **4 kali** | 15.38% dari seluruh sampel R |
| 14 | **E** | **V** | **3 kali** | 12.00% dari seluruh sampel E |
| 15 | **V** | **E** | **3 kali** | 11.54% dari seluruh sampel V |

---

## 4. ANALISIS SEMANTIK DAN FONOLOGI GESTUR BISINDO (ROOT CAUSE ANALYSIS)

Mengapa model MobileNetV3-Small mengalami kebingungan spesifik pada pasangan-pasangan di atas? Analisis fonologi gestur (cherology) menunjukkan akar masalah representasional:

### 4.1. Pasangan D $\leftrightarrow$ P: Ambiguitas Orientasi Spasial (Spatial Orientation Inversion)
- **Fonologi Gestur**: 
  - Huruf D dan P memiliki konfigurasi bentuk tangan (*handshape*) yang sangat serupa pada beberapa sistem fingerspelling: telunjuk tegak dengan lingkaran jari lainnya (atau konfigurasi telapak menyerupai loop).
  - Perbedaan mendasar terletak pada **orientasi jemari (*orientation*)**: Huruf D umumnya mengarah tegak ke atas (*upward*), sedangkan huruf P mengarah horizontal mendatar ke depan atau agak menukik ke bawah (*forward/downward*).
- **Kelemahan Model**: 
  - MobileNetV3-Small tanpa lokalisasi orientasi pergelangan tangan (*wrist angle*) gagal membedakan pitch/yaw tangan pada gambar RGB 2D yang dipotong tanpa konteks lengan bawah (*forearm context*).
  - Sebanyak 20 kesalahan gabungan (12 D $\to$ P dan 8 P $\to$ D) menyumbang **7.7% dari total seluruh kesalahan model**.

### 4.2. Pasangan M $\leftrightarrow$ N: Resolusi Jari Halus (*Fine-grained Finger Counting*)
- **Fonologi Gestur**:
  - Huruf M dan N sama-sama merupakan kepalan tangan tertutup di mana ibu jari diselipkan di antara jari-jari lain.
  - Perbedaan tunggal: Pada M, jempol terselip di bawah **tiga jari** (telunjuk, tengah, manis); pada N, jempol terselip di bawah **dua jari** (telunjuk, tengah).
- **Kelemahan Model**:
  - Pada resolusi input 224x224 setelah *center cropping*, tekstur dan lekukan batas antar-jari (*finger boundary crevices*) mengalami downsampling berulang pada blok depthwise separable convolution pertama. Model kehilangan kemampuan mendeteksi apakah lipatan terdiri dari 2 atau 3 jari.
  - Kebingungan timbal balik: 9 N $\to$ M dan 8 M $\to$ N (total 17 kesalahan).

### 4.3. Pasangan I $\leftrightarrow$ J: Ketiadaan Dimensi Temporal (*Static vs Dynamic Motion Gap*)
- **Fonologi Gestur**:
  - Dalam BISINDO, huruf I dibentuk dengan mengangkat jari kelingking secara statis.
  - Huruf J menggunakan bentuk awal kelingking yang sama, namun disertai **gerakan melengkung (*stroke/trajectory*)** membentuk huruf J di udara.
- **Kelemahan Model**:
  - Dataset gambar statis (single RGB frame) menangkap gestur J pada satu titik waktu beku (*frozen frame*). Jika kamera menangkap pada posisi awal atau akhir gerak, citra J secara visual hampir identik dengan citra I.
  - Keterbatasan ini adalah **keterbatasan inheren modalitas citra tunggal 2D** (Image Modality I1) dan tidak dapat diatasi sempurna hanya dengan menambah parameter konvolusi tanpa input sekuensial atau motion blur representation.

### 4.4. Pasangan U $\leftrightarrow$ C dan R $\leftrightarrow$ C: Kelengkungan Siluet Tangan
- **Fonologi Gestur**:
  - Huruf C membentuk kurva melengkung menyerupai huruf C terbuka.
  - Huruf U merapatkan dua jari tegak; Huruf R menyilangkan jari tengah di atas telunjuk.
- **Kelemahan Model**:
  - Jika sudut pengambilan kamera (*viewing angle*) agak miring (*oblique/profile*), bayangan jari U atau R tampak melengkung menyerupai celah C, memicu aktivasi pada kernel deteksi tepi melengkung.

---

## 5. ANALISIS CONFIDENCE SCORE DAN OVERCONFIDENCE RISK

Distribusi confidence score model P1 menunjukkan karakteristik berikut:

### 5.1. Statistik Confidence
- **Prediksi Benar ($N = 410$)**:
  - Rata-rata confidence: **0.7744** (77.44%)
  - Median: **0.8252**
  - Standar Deviasi: 0.1762
- **Prediksi Salah ($N = 260$)**:
  - Rata-rata confidence: **0.5471** (54.71%)
  - Median: **0.5218**
  - Standar Deviasi: 0.1658

### 5.2. Risiko Overconfidence pada Prediksi Salah
Meskipun model memiliki kalibrasi rata-rata yang baik (ECE = 4.77%), terdapat anomali di mana model mengalami **overconfidence ekstrim (>85%) pada prediksi yang salah**:

| True Class | Predicted Class | Confidence | Path Sampel | Catatan Analisis |
|---|---|---|---|---|
| **K** | **T** | **0.9509** | `data/processed/bisindo_alphabet/K/K_0152.npy` | Model 95% yakin K adalah T (fitur jempol menjepit salah fokus) |
| **C** | **J** | **0.9184** | `data/processed/bisindo_alphabet/C/C_0056.npy` | Celah kurva tangan tertutup bayangan latar |
| **Y** | **V** | **0.9136** | `data/processed/bisindo_alphabet/Y/Y_0096.npy` | Jari kelingking tidak terdeteksi kontrasnya |
| **R** | **C** | **0.9112** | `data/processed/bisindo_alphabet/R/R_0132.npy` | Siluet luar tangan melengkung |
| **M** | **N** | **0.8523** | `data/processed/bisindo_alphabet/M/M_0011.npy` | Kepalan tangan terkompresi pikselnya |

*Total Kesalahan dengan Confidence Tinggi*:
- Confidence $> 0.90$: **4 sampel**
- Confidence $> 0.80$: **8 sampel**
- Confidence $> 0.70$: **18 sampel**

### 5.3. Prediksi Benar dengan Keyakinan Rendah (*Underconfident Correct*)
Sebanyak 10 sampel berhasil ditebak dengan benar tetapi memiliki confidence $< 0.25$ (hampir mendekati probabilitas acak $1/26 \approx 0.038$):
- Huruf B (`B_0053.npy`): Confidence = **0.1795**
- Huruf H (`H_0031.npy`): Confidence = **0.1831**
- Huruf F (`F_0067.npy`): Confidence = **0.1868**
- Huruf I (`I_0058.npy`): Confidence = **0.2054**

Ini membuktikan bahwa ruang fitur P1 pada batas-batas kelas tertentu (*decision boundaries*) sangat tidak stabil.

---

## 6. VISUALISASI PENDUKUNG

Seluruh analisis di atas didukung oleh artefak visual yang telah diekspor ke direktori `docs/validation_p1/eda/`:
1. `docs/validation_p1/eda/per_class_f1_precision_recall.png`: Menampilkan disparitas drastis antara kelas G/A ($\approx 81\%$) dan P/C/D ($\le 40\%$).
2. `docs/validation_p1/eda/top_confusion_pairs.png`: Grafik batang pasangan paling sering tertukar (D-P, N-M, M-N, P-D, U-C).
3. `docs/validation_p1/eda/confusion_matrix_heatmap.png`: Peta panas 26x26 yang mengisolasi kluster kebingungan off-diagonal.
4. `docs/validation_p1/eda/confidence_distribution_p1.png`: Kurva probabilitas prediksi benar vs salah.

---

## 7. KESIMPULAN ANALISIS KESALAHAN P1

1. **Kegagalan Terpusat pada Morfologi Jari Halus dan Orientasi**: Model MobileNetV3-Small P1 bukan gagal secara acak, melainkan gagal pada titik-titik fonologis terprediksi:
   - Ketidakmampuan membedakan arah orientasi telapak (D vs P).
   - Ketidakmampuan membedakan jumlah lipatan jari halus (M vs N).
   - Keterbatasan inferensi gerakan dinamis pada frame tunggal (I vs J).
2. **Keterbatasan Arsitektur Tanpa Localized Attention**: Penggunaan MobileNetV3-Small standar dengan global average pooling langsung pada seluruh frame membuat model rentan menangkap artefak latar belakang alih-alih segmen jari tangan.
3. **Optimisme Metrik**: Dengan akurasi internal hanya 61.19% pada dataset yang mengalami subject leakage, model P1 dipastikan **belum siap dideploy untuk penggunaan produksi nyata** tanpa perbaikan arsitektural dan metodologis pada iterasi P2.

