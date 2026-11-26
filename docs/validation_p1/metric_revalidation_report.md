# LAPORAN REVALIDASI METRIK EVALUASI EKSPERIMEN I1-P1 (TAHAP B)

> **Dokumen**: `docs/validation_p1/metric_revalidation_report.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Dasar Bukti**: Rekalkulasi `predictions.csv` ($N = 670$) & Live Forward-Pass `best.pt`  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Verifikasi Metrik**: **`VERIFIED & 100% REPRODUCIBLE`** (Paritas Paripurna)

---

## 1. RINGKASAN AUDIT METRIK

Audit ini bertujuan memverifikasi apakah metrik performa Test Set yang dilaporkan pada eksperimen I1-P1 benar-benar bersumber dari inferensi checkpoint `best.pt` tanpa fabrikasi, distorsi, atau kebocoran komputasi.

Dilakukan dua pengujian independen:
1. **Audit Integritas File Prediksi**: Analisis baris-demi-baris pada [`runs/image_i1_mobilenetv3_p1/predictions.csv`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/predictions.csv).
2. **Pengujian Inferensi Ulang Langsung (*Live Forward-Pass*)**: Memuat bobot `best.pt` ke arsitektur MobileNetV3-Small baru, menjalankan inferensi deterministik pada seluruh 670 sampel Test Set, dan mencocokkan setiap prediksi dengan baris `predictions.csv`.

---

## 2. AUDIT INTEGRITAS `predictions.csv`

Pemeriksaan konsistensi pada 670 baris prediksi menghasilkan temuan berikut:
- **Jumlah Baris Data**: Tepat $670$ baris (tidak ada baris kosong atau hilang).
- **Jumlah Ground Truth Valid**: $670$ sampel berlabel alfabet A–Z (indeks $0\text{--}25$).
- **Jumlah Prediksi Valid**: $670$ prediksi berlabel alfabet A–Z (indeks $0\text{--}25$).
- **Nilai Kosong / NaN / Null**: **Nol ($0$)**.
- **Kelas di Luar Jangkauan**: **Nol ($0$)**.
- **Rentang Confidence Score**: Minimum $0,1051$ ($10,51\%$), Maksimum $0,9996$ ($99,96\%$), Rata-rata $0,6012$ ($60,12\%$).

---

## 3. PENGUJIAN PARITAS INFERENSI ULANG LANGSUNG (*LIVE CHECKPOINT INFERENCE*)

Model dimuat dari [`runs/image_i1_mobilenetv3_p1/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/best.pt) ke memori, dan dievaluasi terhadap DataLoader Test Set deterministik ($N = 670$):

$$\text{Jumlah Diskrepansi Prediksi} = 0 \text{ dari } 670 \text{ citra } (0,00\%)$$

Setiap indeks prediksi kelas dari output logit model PyTorch menghasilkan nilai yang identik $100\%$ dengan data pada `predictions.csv`. Hal ini membuktikan bahwa:
- File `predictions.csv` benar-benar merupakan hasil eksekusi model `best.pt`.
- Tidak ada modifikasi manual pasca-pelatihan.
- Pipeline evaluasi deterministik sepenuhnya dapat direproduksi (*reproducible*).

---

## 4. REKALKULASI SELURUH METRIK & TABEL KONSISTENSI

Berikut perbandingan metrik hasil rekalkulasi audit independen dengan artefak laporan yang ada:

| Metrik Evaluasi | Hasil Rekalkulasi Audit | `training_summary.json` | `classification_report.txt` | `P1_TRAINING_EVALUATION_REPORT.md` | Status Konsistensi |
|---|:---:|:---:|:---:|:---:|:---:|
| **Test Accuracy** | **$61,1940\%$** | $61,19\%$ | $61,19\%$ | $61,19\%$ | **KONSISTEN $100\%$** |
| **Macro Precision** | **$63,3004\%$** | $63,30\%$ | $63,30\%$ | $63,30\%$ | **KONSISTEN $100\%$** |
| **Macro Recall** | **$61,2737\%$** | $61,27\%$ | $61,27\%$ | $61,27\%$ | **KONSISTEN $100\%$** |
| **Macro F1-Score** | **$61,5662\%$** | $61,57\%$ | $61,57\%$ | $61,57\%$ | **KONSISTEN $100\%$** |
| **Weighted Precision** | **$63,3021\%$** | N/A | $63,30\%$ | N/A | **KONSISTEN $100\%$** |
| **Weighted Recall** | **$61,1940\%$** | N/A | $61,19\%$ | N/A | **KONSISTEN $100\%$** |
| **Weighted F1-Score** | **$61,5320\%$** | $61,53\%$ | $61,53\%$ | $61,53\%$ | **KONSISTEN $100\%$** |
| **Unique Predicted Classes** | **26 Kelas** | 26 Kelas | 26 Kelas | 26 Kelas | **KONSISTEN $100\%$** |
| **Zero-Recall Classes** | **0 Kelas ($\emptyset$)** | 0 Kelas | 0 Kelas | 0 Kelas | **KONSISTEN $100\%$** |

> **Catatan Toleransi**: Seluruh perbedaan angka antara rekalkulasi audit dan artefak laporan berada di bawah $0,01\%$, yang murni timbul akibat pembulatan dua angka di belakang koma (*standard decimal rounding*). Tidak ditemukan inkonsistensi metrik.

---

## 5. AUDIT DISTRIBUSI PREDIKSI PER KELAS

Frekuensi prediksi tiap kelas pada Test Set menunjukkan penyebaran yang proporsional terhadap ground truth:
- **Rentang Ground Truth per Kelas**: $24\text{--}26$ sampel per kelas.
- **Rentang Jumlah Prediksi per Kelas**: Minimum $11$ sampel (Kelas P), Maksimum $48$ sampel (Kelas T).
- **Semua 26 Kelas Memiliki True Positives (TP $> 0$)**:
  - Minimum TP: Kelas P ($8$ sampel benar dari 26).
  - Maksimum TP: Kelas X ($22$ sampel benar dari 26).
  - Seluruh 26 kelas memiliki Recall $\ge 30,77\%$.

---

## 6. KESIMPULAN TAHAP B

Hasil evaluasi I1-P1 (**Akurasi $61,19\%$**, **Macro F1 $61,57\%$**) adalah **VALID**, **OTENTIK**, dan **TERVERIFIKASI PENUH**. Laporan evaluasi sebelumnya mencerminkan data aktual tanpa manipulasi.

