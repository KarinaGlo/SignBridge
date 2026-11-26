# LAPORAN INDEPENDENT RE-AUDIT: EVALUASI KINERJA & ANALISIS KESALAHAN MODEL I1-P1
## SignBridge ASEAN — Modality Image (MobileNetV3-Small BISINDO A–Z)

> **Dokumen**: `docs/validation_p1/RE_AUDIT_P1_PERFORMANCE.md`  
> **Tipe Evaluasi**: Independent Evaluation Recomputation & Error Diagnostics  
> **Dasar Bukti**: Inferensi 670 sampel Test Set pada `runs/image_i1_mobilenetv3_p1/predictions.csv`  
> **Tanggal Audit**: 17 November 2026  
> **Auditor**: Senior Machine Learning Auditor, Computer Vision Engineer, & Data Quality Analyst  
> **Status Verifikasi Metrik**: **`VERIFIED_WITH_DOCUMENTED_CORRECTIONS`**

---

## 1. METODOLOGI RE-AUDIT EVALUASI

Evaluasi dilakukan dengan merekomputasi seluruh metrik performa langsung dari file prediksi mentah baris-demi-baris ($N = 670$ baris pada `predictions.csv`) dan mencocokkannya dengan artefak pelaporan lain di repositori:
1. `runs/image_i1_mobilenetv3_p1/training_summary.json`
2. `runs/image_i1_mobilenetv3_p1/classification_report.txt`
3. `runs/image_i1_mobilenetv3_p1/confusion_matrix.csv`

---

## 2. REKOMPUTASI METRIK GLOBAL MODEL P1

Hasil perhitungan ulang metrik global terhadap 670 sampel uji:

| Metrik Evaluasi | Nilai Laporan Lama | Nilai Rekomputasi Aktual | Paritas Presisi | Status Target Baseline ($\ge 75\%$) |
|---|---|---|:---:|:---:|
| **Test Accuracy** | 61,19% | **61,1940%** (410 / 670) | **EXACT MATCH ✅** | **BELUM TERCAPAI (-13,81%)** |
| **Macro Average Precision** | 63,30% | **63,3019%** (0,6330) | **EXACT MATCH ✅** | **BELUM TERCAPAI (-11,70%)** |
| **Macro Average Recall** | 61,27% | **61,2707%** (0,6127) | **EXACT MATCH ✅** | **BELUM TERCAPAI (-13,73%)** |
| **Macro Average F1-Score** | 61,57% | **61,5662%** (0,6157) | **EXACT MATCH ✅** | **BELUM TERCAPAI (-13,43%)** |
| **Weighted Average F1-Score**| 61,53% | **61,5263%** (0,6153) | **EXACT MATCH ✅** | Mengikuti sebaran kelas |
| **Jumlah Prediksi Benar** | 410 sampel | **410 sampel** (61,19%) | **EXACT MATCH ✅** | - |
| **Jumlah Prediksi Salah** | 260 sampel | **260 sampel** (38,81%) | **EXACT MATCH ✅** | Objek diagnostik error |

### Konsistensi Lintas Artefak Evaluasi:
- `training_summary.json` vs Rekomputasi: **Paritas Sempurna ($Diff < 0,004\%$)**.
- `classification_report.txt` vs Rekomputasi: **100% Identik di seluruh 26 kelas**.
- `confusion_matrix.csv` vs Rekomputasi: **100% Identik (Sum = 670, Diagonal = 410, Off-diagonal = 260)**.

---

## 3. REKOMPUTASI PER-KELAS & RANKING KELUARAN (PER-CLASS PERFORMANCE)

Seluruh 26 kelas alfabet BISINDO dihitung ulang nilai Precision, Recall, F1, dan Support-nya:

| Kelas Alfabet | Precision | Recall | F1-Score | Support | Status Kategori Performa |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Kelas G** | **0,8696** | 0,7692 | **0,8163** | 26 | **Kategori 1: Unggul ($\ge 80\%$)** |
| **Kelas A** | 0,7500 | **0,8750** | **0,8077** | 24 | **Kategori 1: Unggul ($\ge 80\%$)** |
| **Kelas Z** | 0,8000 | 0,7692 | **0,7843** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas X** | 0,7097 | 0,8462 | **0,7719** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas E** | 0,7600 | 0,7600 | **0,7600** | 25 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas Q** | 0,7917 | 0,7308 | **0,7600** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas F** | 0,8947 | 0,6538 | **0,7556** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas L** | 0,7826 | 0,6923 | **0,7347** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas W** | 0,6562 | 0,8077 | **0,7241** | 26 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas B** | 0,7727 | 0,6800 | **0,7234** | 25 | Kategori 2: Menengah-Atas (70–79%) |
| **Kelas H** | 0,8824 | 0,5769 | **0,6977** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas M** | 0,6296 | 0,6538 | **0,6415** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas Y** | 0,7143 | 0,5769 | **0,6383** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas K** | 0,7647 | 0,5000 | **0,6047** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas V** | 0,5333 | 0,6154 | **0,5714** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas N** | 0,6087 | 0,5385 | **0,5714** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas S** | 0,4857 | 0,6538 | **0,5574** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas O** | 0,5357 | 0,5769 | **0,5556** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas T** | 0,4722 | 0,6538 | **0,5484** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas U** | 0,6667 | 0,4615 | **0,5455** | 26 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas J** | 0,4545 | 0,6000 | **0,5172** | 25 | Kategori 3: Menengah-Bawah (50–69%) |
| **Kelas I** | 0,5000 | 0,4231 | **0,4583** | 26 | **Kategori 4: Kritis / Gagal ($< 46\%$)** |
| **Kelas R** | 0,4074 | 0,4231 | **0,4151** | 26 | **Kategori 4: Kritis / Gagal ($< 46\%$)** |
| **Kelas D** | 0,4167 | 0,3846 | **0,4000** | 26 | **Kategori 4: Kritis / Gagal ($< 46\%$)** |
| **Kelas C** | 0,3030 | 0,4000 | **0,3448** | 25 | **Kategori 4: Kritis / Gagal ($< 46\%$)** |
| **Kelas P** | **0,2963** | **0,3077** | **0,3019** | 26 | **Kategori 4: Kritis / Gagal ($< 46\%$)** |

Visualisasi per-class F1 telah diperbarui pada [`docs/validation_p1/reaudit/per_class_f1.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/reaudit/per_class_f1.png).

---

## 4. ANALISIS KESALAHAN PASANGAN KELAS (CONFUSION PAIRS)

Audit mengklasifikasikan pasangan tertukar berikut berdasarkan **Observed Visual Class Confusion**:

| True Class | Predicted Class | Error Count | Support True Class | Percentage of True Class | Karakteristik Visual Teramati |
|:---:|:---:|:---:|:---:|:---:|---|
| **D** | **P** | **12** | 26 | **46,15%** | Kemiripan bentuk loop/telunjuk; perbedaan rotasi/arah |
| **N** | **M** | **9** | 26 | **34,62%** | Kepalan tangan dengan perbedaan jumlah jari (2 vs 3) |
| **M** | **N** | **8** | 26 | **30,77%** | Kepalan tangan tertukar timbal balik |
| **P** | **D** | **8** | 26 | **30,77%** | Tertukar timbal balik D $\leftrightarrow$ P |
| **U** | **C** | **7** | 26 | **26,92%** | Celah kurva tangan mirip saat dilihat dari profil miring |
| **I** | **C** | **5** | 26 | **19,23%** | Lengan bawah dan bayangan membentuk kurva |
| **J** | **I** | **5** | 25 | **20,00%** | Kemiripan pose kelingking pada frame statis tunggal |
| **I** | **J** | **5** | 26 | **19,23%** | Tertukar timbal balik I $\leftrightarrow$ J |
| **K** | **T** | **5** | 26 | **19,23%** | Posisi jempol terselip di antara jari |
| **P** | **T** | **5** | 26 | **19,23%** | Jempol menonjol pada siluet tangan |
| **Y** | **X** | **5** | 26 | **19,23%** | Lekukan jari kelingking/telunjuk |
| **R** | **J** | **4** | 26 | **15,38%** | Jari menyilang vs jari kelingking terangkat |
| **R** | **C** | **4** | 26 | **15,38%** | Siluet lekukan luar tangan |
| **E** | **V** | **3** | 25 | **12,00%** | Jari tertekuk vs dua jari terangkat |
| **V** | **E** | **3** | 26 | **11,54%** | Tertukar timbal balik E $\leftrightarrow$ V |

Visualisasi matriks konfusi 26x26 lengkap disimpan pada [`docs/validation_p1/reaudit/confusion_matrix.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/reaudit/confusion_matrix.png).

> [!NOTE]
> Pasangan-pasangan di atas diklasifikasikan sebagai **`OBSERVED VISUAL CLASS CONFUSION`**. Meskipun kemiripan morfologi visualnya sangat nyata secara geometris, klaim apakah kebingungan ini merupakan representasi dialek/fonologi BISINDO regional tetap berstatus **`UNVERIFIED HYPOTHESIS`** hingga divalidasi oleh penutur Tuli asli.

---

## 5. AUDIT DISTRIBUSI KEYAKINAN & KALIBRASI (CONFIDENCE & CALIBRATION)

### 5.1. Koreksi Discrepancy Statistik Keyakinan (Re-Audit Finding)
Pemeriksaan ulang menemukan bahwa nilai rata-rata confidence pada laporan sebelumnya tidak tepat. Nilai aktual yang dihitung langsung dari `predictions.csv` adalah:

| Statistik Keyakinan | Nilai Laporan Lama | Nilai Rekomputasi Aktual | Catatan Discrepancy |
|---|---|---|---|
| **Mean Confidence (Prediksi Benar)** | 0,7744 (77,44%) | **0,6747** (67,47%) | Laporan lama over-estimasi keyakinan benar sebesar $\approx +10\%$ |
| **Mean Confidence (Prediksi Salah)** | 0,5471 (54,71%) | **0,4135** (41,35%) | Laporan lama over-estimasi keyakinan salah sebesar $\approx +13\%$ |
| **Median Confidence (Benar)** | 0,8252 | **0,6892** | Median aktual lebih rendah |
| **Median Confidence (Salah)** | 0,5218 | **0,3710** | Median aktual lebih rendah |
| **Expected Calibration Error (ECE)** | 4,77% (10 bins) | **4,77%** (0,0477) | **EXACT MATCH ✅** |

Visualisasi distribusi keyakinan aktual disimpan pada [`docs/validation_p1/reaudit/confidence_distribution.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/reaudit/confidence_distribution.png).

### 5.2. Audit Kasus Overconfidence Ekstrim
Meskipun rata-rata keyakinan pada prediksi salah adalah 41,35%, terdapat anomali kegagalan fatal di mana model sangat yakin pada prediksi yang salah:
- Prediksi salah dengan Confidence $> 0,90$: **4 sampel**
- Prediksi salah dengan Confidence $> 0,85$: **5 sampel**
- Prediksi salah dengan Confidence $> 0,80$: **8 sampel**
- Prediksi salah dengan Confidence $> 0,70$: **18 sampel**

Contoh kasus overconfidence terburuk yang terverifikasi pada disk:
1. `K_0152.npy` (True: K, Pred: T, Confidence: **0,9509**) — Model 95% yakin K adalah T.
2. `C_0056.npy` (True: C, Pred: J, Confidence: **0,9184**) — Model 91,8% yakin C adalah J.
3. `Y_0096.npy` (True: Y, Pred: V, Confidence: **0,9136**) — Model 91,4% yakin Y adalah V.
4. `R_0132.npy` (True: R, Pred: C, Confidence: **0,9112**) — Model 91,1% yakin R adalah C.
5. `M_0011.npy` (True: M, Pred: N, Confidence: **0,8523**) — Model 85,2% yakin M adalah N.

---

## 6. KESIMPULAN RE-AUDIT PERFORMA P1

1. **Akurasi 61,19% Terverifikasi dan Sah**: Angka Test Accuracy 61,19% dan Macro F1 61,57% terbukti bersumber dari inferensi riil `best.pt` tanpa fabrikasi.
2. **Koreksi Terhadap Laporan Sebelumnya**: Statistik rata-rata confidence terbukti lebih rendah dari laporan sebelumnya (benar: 67,47% vs salah: 41,35%), menunjukkan bahwa model sebenarnya memiliki tingkat keraguan (*uncertainty*) yang lebih tinggi daripada yang dilaporkan sebelumnya.
3. **Penyebab Kegagalan**: Kegagalan terkonsentrasi pada ambiguitas visual orientasi (D vs P), penghitungan lipatan jari halus (M vs N), dan ketiadaan fitur temporal (I vs J), diperparah oleh adanya sampel duplikat raw pada Mendeley.

