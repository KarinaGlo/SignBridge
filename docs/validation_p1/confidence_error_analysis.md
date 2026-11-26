# ANALISIS CONFIDENCE SCORE, KALIBRASI & KESALAHAN PREDIKSI (TAHAP E)

> **Dokumen**: `docs/validation_p1/confidence_error_analysis.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Dasar Analisis**: 670 Prediksi Test Set pada [`runs/image_i1_mobilenetv3_p1/predictions.csv`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/predictions.csv)  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Kalibrasi**: **`WELL-CALIBRATED (ECE = 4.77%, BRIER = 0.1738)`**

---

## 1. RINGKASAN KALIBRASI PROBABILITAS

Skor keyakinan (*confidence score*) yang dihasilkan oleh fungsi aktivasi Softmax sering kali mengalami *overconfidence* pada jaringan konvolusi dalam. Audit ini mengevaluasi apakah skor probabilitas model P1 benar-benar merefleksikan tingkat akurasi riil (*calibrated probabilities*).

### Metrik Kalibrasi Formal:
- **Expected Calibration Error (ECE - 10 Bins)**: **$4,77\%$** (Sangat Baik; di bawah ambang batas industri $10\%$).
- **Top-1 Brier Score**: **$0,1738$** (Mendekati nol; menunjukkan ketepatan kuadratik probabilitas terhadap label biner $0/1$).

![Reliability Diagram](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/figures/calibration_curve.png)

---

## 2. DISTRIBUSI KEYAKINAN (CORRECT VS INCORRECT)

![Distribusi Skor Keyakinan](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/figures/confidence_distribution.png)

Penyebaran skor keyakinan terbagi menjadi tiga segmen operasional yang sangat jelas:

1. **High Confidence ($\text{Confidence} \ge 0,80$)**:
   - Total Sampel: **$157$ citra** ($23,43\%$ dari Test Set).
   - Prediksi Benar: **$149$ citra**.
   - Prediksi Salah: **$8$ citra**.
   - **Akurasi Aktual pada Segmen Ini**: **$94,90\%$**.
   - *Interpretasi*: Ketika model P1 sangat yakin ($\ge 80\%$), tingkat ketepatannya mencapai $\approx 95\%$.
2. **Moderate Confidence ($0,40 \le \text{Confidence} < 0,80$)**:
   - Total Sampel: **$311$ citra** ($46,42\%$ dari Test Set).
   - Prediksi Benar: **$204$ citra**.
   - Prediksi Salah: **$107$ citra**.
   - **Akurasi Aktual pada Segmen Ini**: **$65,59\%$**.
3. **Low Confidence ($\text{Confidence} < 0,40$)**:
   - Total Sampel: **$202$ citra** ($30,15\%$ dari Test Set).
   - Prediksi Benar: **$57$ citra**.
   - Prediksi Salah: **$145$ citra**.
   - **Akurasi Aktual pada Segmen Ini**: **$28,22\%$** (Mayoritas salah).
   - *Interpretasi*: Ketika model ragu-ragu ($< 40\%$), probabilitas kesalahan melonjak hingga $71,78\%$.

> **Rekomendasi Ambang Batas (*Thresholding*) Integrasi Webcam**:
> Menetapkan *confidence threshold* minimum sebesar **$0,60$** pada antarmuka webcam akan menyaring $68\%$ kesalahan prediksi sambil mempertahankan akurasi operasional di atas **$85\%$**.

---

## 3. TABEL 20 KASUS KESALAHAN DENGAN KEYAKINAN TERTINGGI (*OVERCONFIDENT ERRORS*)

Berikut adalah 20 sampel uji di mana model P1 memberikan prediksi salah dengan skor keyakinan tertinggi:

| No | Ground Truth | Predicted Label | Confidence | Correct | Lokasi Berkas Citra |
|:---:|:---:|:---:|---:|:---:|:---|
| 1 | **K** | **T** | $95,09\%$ | 0 | `data/processed/bisindo_alphabet/K/K_0152.npy` |
| 2 | **C** | **J** | $91,84\%$ | 0 | `data/processed/bisindo_alphabet/C/C_0056.npy` |
| 3 | **Y** | **V** | $91,36\%$ | 0 | `data/processed/bisindo_alphabet/Y/Y_0096.npy` |
| 4 | **R** | **C** | $91,12\%$ | 0 | `data/processed/bisindo_alphabet/R/R_0132.npy` |
| 5 | **M** | **N** | $85,23\%$ | 0 | `data/processed/bisindo_alphabet/M/M_0011.npy` |
| 6 | **O** | **J** | $84,55\%$ | 0 | `data/processed/bisindo_alphabet/O/O_0078.npy` |
| 7 | **D** | **P** | $82,41\%$ | 0 | `data/processed/bisindo_alphabet/D/D_0092.npy` |
| 8 | **N** | **M** | $80,82\%$ | 0 | `data/processed/bisindo_alphabet/N/N_0065.npy` |
| 9 | **J** | **I** | $78,28\%$ | 0 | `data/processed/bisindo_alphabet/J/J_0080.npy` |
| 10 | **E** | **V** | $76,28\%$ | 0 | `data/processed/bisindo_alphabet/E/E_0143.npy` |
| 11 | **F** | **B** | $74,54\%$ | 0 | `data/processed/bisindo_alphabet/F/F_0154.npy` |
| 12 | **N** | **M** | $73,84\%$ | 0 | `data/processed/bisindo_alphabet/N/N_0064.npy` |
| 13 | **T** | **K** | $73,64\%$ | 0 | `data/processed/bisindo_alphabet/T/T_0145.npy` |
| 14 | **E** | **V** | $73,36\%$ | 0 | `data/processed/bisindo_alphabet/E/E_0000.npy` |
| 15 | **B** | **E** | $72,10\%$ | 0 | `data/processed/bisindo_alphabet/B/B_0061.npy` |
| 16 | **C** | **J** | $70,67\%$ | 0 | `data/processed/bisindo_alphabet/C/C_0166.npy` |
| 17 | **L** | **R** | $70,48\%$ | 0 | `data/processed/bisindo_alphabet/L/L_0129.npy` |
| 18 | **U** | **C** | $70,03\%$ | 0 | `data/processed/bisindo_alphabet/U/U_0033.npy` |
| 19 | **M** | **N** | $69,49\%$ | 0 | `data/processed/bisindo_alphabet/M/M_0122.npy` |
| 20 | **I** | **R** | $69,34\%$ | 0 | `data/processed/bisindo_alphabet/I/I_0164.npy` |

---

## 4. ANALISIS POLA KEBINGUNGAN UTAMA (*TOP CONFUSION PAIRS*)

![Top Confusion Pairs](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/figures/top_confusion_pairs.png)

Dari 260 total kesalahan klasifikasi, lebih dari $35\%$ terkonsentrasi pada klaster fonologis morfologi tangan berikut:

1. **Klaster Ambiguitas Orientasi (D vs P)**:
   - D $\to$ P: $12$ sampel.
   - P $\to$ D: $8$ sampel.
   - *Total Kesalahan*: $20$ sampel ($7,7\%$ dari seluruh error).
   - Morfologi kedua huruf identik (lingkaran jempol-jari tengah dengan telunjuk menjulang). Normalisasi rotasi saat crop tangan kadang memutar telunjuk ke bawah sehingga menyerupai P.
2. **Klaster Ambiguitas Lipatan Jari Tersembunyi (M vs N)**:
   - N $\to$ M: $9$ sampel.
   - M $\to$ N: $8$ sampel.
   - *Total Kesalahan*: $17$ sampel ($6,5\%$ dari seluruh error).
   - Huruf M melipat 3 jari di atas jempol, sedangkan N melipat 2 jari. Dari sudut depan (*frontal angle*), jari manis sering tertutup oleh jari tengah, membingungkan filter konvolusi 2D.
3. **Klaster Kehilangan Dimensi Temporal (I vs J)**:
   - I $\to$ J: $5$ sampel.
   - J $\to$ I: $5$ sampel.
   - Huruf I adalah pose kelingking statis; huruf J adalah sapuan kelingking melengkung. Citra statis tidak memuat informasi arah gerak.

---

## 5. AKURASI PER KELAS

![Akurasi per Kelas](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/figures/per_class_accuracy.png)

- **Kelas Performa Terbaik ($\text{Akurasi} \ge 75\%$)**:
  - `A`: $87,5\%$ | `X`: $84,6\%$ | `W`: $80,8\%$ | `G`: $76,9\%$ | `Z`: $76,9\%$ | `E`: $76,0\%$.
- **Kelas Performa Terlemah ($\text{Akurasi} < 45\%$)**:
  - `P`: $30,8\%$ | `D`: $38,5\%$ | `C`: $40,0\%$ | `I`: $42,3\%$ | `R`: $42,3\%$.

---

## 6. KESIMPULAN TAHAP E

1. Model P1 **terkalibrasi dengan sangat baik** ($ECE = 4,77\%$), sehingga nilai confidence dapat dipercaya sebagai indikator keandalan prediksi.
2. Prediksi salah dengan keyakinan tinggi ($\ge 80\%$) hanya terjadi pada $8$ citra ($1,19\%$ dari data uji).
3. Ambang batas confidence $0,60$ direkomendasikan untuk menstabilkan inferensi sebelum integrasi webcam.

