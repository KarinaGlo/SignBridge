# LAPORAN PELATIHAN MODEL M0 STUDENT BASELINE (WL-BISINDO)

| Metadata Dokumen | Nilai |
|---|---|
| **Tanggal Pelatihan** | 2026-11-08 |
| **Proyek** | SignBridge ASEAN (BISINDO ↔ FSL) |
| **Tahap** | TAHAP A.4 — M0 Student Baseline Training (WL-BISINDO) |
| **Branch Git** | `feature/dataset-acquisition` |
| **Git HEAD** | `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` |
| **Engineer / Auditor** | Senior Machine Learning Engineer & Research Scientist |
| **Status Akhir** | **TRAINING COMPLETED** |

---

## 1. TUJUAN EKSPERIMEN

Eksperimen **M0 Student Baseline** bertujuan membangun dan melatih model dasar (*first reproducible baseline*) untuk klasifikasi 32 kelas bahasa isyarat BISINDO menggunakan dataset keypoint spatio-temporal WL-BISINDO yang telah diekstraksi dan diaudit pada Tahap A.3.3 dan A.3.4.

Model ini berfungsi sebagai patokan performa (*benchmark anchor*) tanpa menggunakan transfer learning dari model luar (WLASL), tanpa knowledge distillation dari model guru (*teacher*), dan tanpa modalitas multimodal VideoMAE/RGB.

---

## 2. DATASET & PEMBAGIAN SPLIT

Pelatihan menggunakan dataset keypoint WL-BISINDO dengan protokol resmi **Signer-Dependent (SD)** sesuai Kontrak 1 & 3:

| Split | Jumlah Sampel | Persentase | Representasi Kelas |
|---|---:|---:|---:|
| **Train** | **960** | 60,00% | 32 / 32 kelas (100%) |
| **Validation** | **180** | 11,25% | 32 / 32 kelas (100%) |
| **Test** | **460** | 28,75% | 32 / 32 kelas (100%) |
| **Total** | **1.600** | 100,00% | 32 / 32 kelas (100%) |

- **Dimensi Input**: Tensor `[B, 64, 86, 3]` float32.
- **Valid Mask**: Boolean mask `[B, 64, 86]` untuk memisahkan landmark fisik aktif dari koordinat non-aktif/missing.
- **Zero Synthetic Fallbacks**: 100% sampel bersumber dari data fisik riil tanpa pembangkitan data sintetis.
- **Zero Data Leakage**: Telah diverifikasi bahwa tidak ada video ID atau hash keypoint yang beririsan lintas split.

---

## 3. PREPROCESSING & VALID MASK HANDLING

Preprocessing data dijalankan sesuai Kontrak 3 SignBridge:
1. **Trim Inactive**: Memotong frame awal dan akhir di mana kedua tangan belum berada di ruang isyarat.
2. **Normalisasi Geometris**: Titik tengah bahu di-center ke $(0, 0, 0)$ dan dibagi dengan lebar bahu $\|\mathbf{bahu}_L - \mathbf{bahu}_R\| = 1.0$.
3. **Resampling Temporal**: Menginterpolasi sumbu waktu menjadi tepat $T = 64$ frame.
4. **Penanganan Valid Mask**: Landmark yang invalid (`valid_mask == False`) dipastikan tetap bernilai strictly `(0.0, 0.0, 0.0)` melalui masking spasial:
   $$\mathbf{P}_{\text{masked}} = \mathbf{P} \odot \mathbf{M}$$
   di mana $\mathbf{M}$ adalah valid mask yang diperluas ke dimensi koordinat. Dengan demikian, model tidak menangkap noise atau artefak pada tangan kiri pasif (khususnya pada 28 kelas satu-tangan dominan).
5. **Data Augmentasi (Khusus Train Set)**:
   - Rotasi random: $\pm 12^\circ$
   - Skala random: $[0.9, 1.1]$
   - Geser random: $\pm 0.03$ unit
   - Jitter kecepatan temporal: $[0.85, 1.15]$
   - Dropout tangan acak: $p = 0.10$

---

## 4. ARSITEKTUR MODEL M0 STUDENT

Model mengimplementasikan arsitektur **`StudentPoseTransformer`** sesuai Bab 2.3 & Bab 1.4:

```
Input Keypoints: [B, 64, 86, 3]
       │
       ▼
 [Hitung Kecepatan Temporal dx = P_{t} - P_{t-1}]
       │
       ▼
 [Konkatenasi Posisi (3) + Kecepatan (3) = 6 fitur per node]
       │
 [Reshape ke Vektor Frame: 86 * 6 = 516 fitur per frame]
       │
       ▼
 [Linear Projection: 516 -> d_model (160)]
       │
 [LayerNorm(160) + Dropout(0.10)]
       │
 [Penjumlahan Positional Embedding: Parameter(1, 64, 160)]
       │
       ▼
 [4-Layer Transformer Encoder]
   - nhead: 4
   - dim_feedforward: 640
   - activation: GELU
   - dropout: 0.10
       │
       ▼
 [LayerNorm(160)]
       │
 [Temporal Global Average Pooling: Mean over 64 frames -> [B, 160]]
       │
       ▼
 [Linear Classifier Head: 160 -> 32 Kelas]
       │
       ▼
 Output Logits: [B, 32]
```

### Parameter Count
- **Total Trainable Parameters**: **1.335.872** parameter ($\sim 1,34\text{M}$).
- **Ukuran Bobot FP32**: $\sim 5,1\text{ MB}$ (sangat ringan, siap dikonversi ke INT8 ONNX sub-1,5 MB untuk inferensi browser < 50ms).

---

## 5. LINGKUNGAN TRAINING & HYPERPARAMETER

### Lingkungan Hardware & Software (Terisolasi di `.venv_m0`)

| Parameter Lingkungan | Nilai |
|---|---|
| **Environment Isolation** | Dedicated Virtualenv `.venv_m0` |
| **Python** | `Python 3.11.0b4` (host runtime terjaga) |
| **PyTorch** | `2.2.2+cpu` (sesuai baris 6 `requirements.txt`) |
| **NumPy** | `1.26.4` (sesuai baris 26 `requirements.txt`) |
| **Device Pelatihan** | CPU (Intel Host, AMD64) |
| **GPU Terdeteksi** | NVIDIA GeForce RTX 3050 (6 GB) — disimpan untuk M2/M3 |
| **Random Seed** | `42` (deterministik penuh) |

### Konfigurasi Hyperparameter

| Hyperparameter | Nilai Konfigurasi |
|---|---|
| **Optimizer** | `AdamW` |
| **Initial Learning Rate** | `1e-3` ($0,001$) |
| **Weight Decay** | `0,01` |
| **Loss Function** | `CrossEntropyLoss` (dengan label smoothing = `0.1`) |
| **Batch Size** | `32` |
| **Maksimum Epoch** | `100` |
| **Early Stopping** | Patience `10` epoch pada validation loss |
| **Learning Rate Scheduler** | `ReduceLROnPlateau` (factor=`0.5`, patience=`4`, min_lr=`1e-5`) |

---

## 6. PROSES TRAINING & DIVERGENSI PEMBELAJARAN

Pelatihan berjalan selama **58 epoch** sebelum dipicu oleh mekanisme *Early Stopping* (berhenti otomatis setelah 10 epoch tanpa penurunan validation loss):
- **Durasi Total Pelatihan**: **23,78 menit** ($1.426,52$ detik) pada CPU host.
- **Rerata Waktu per Epoch**: $\sim 24,5$ detik (termasuk komputasi augmentasi *on-the-fly*).
- **Epoch Terbaik**: **Epoch 48** (Validation Loss = **0,7375**, Validation Accuracy = **97,78%**).

### Ringkasan Perkembangan Metrik Epoch Kunci

| Epoch | Train Loss | Train Acc (%) | Val Loss | Val Acc (%) | Learning Rate | Catatan |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 3,0924 | 13,85% | 2,5461 | 21,67% | 0,001000 | Inisialisasi awal |
| 5 | 1,7471 | 55,94% | 1,6651 | 58,89% | 0,001000 | Konvergensi cepat |
| 10 | 1,0630 | 85,42% | 1,1195 | 86,11% | 0,001000 | Pola gestur terbentuk |
| 20 | 0,9309 | 89,38% | 1,0021 | 88,89% | 0,001000 | Stabilitas leksikal |
| 27 | 0,7247 | 97,92% | 0,8084 | 96,67% | 0,000500 | LR decayed ke 5e-4 |
| 34 | 0,6603 | 100,00% | 0,7633 | 97,22% | 0,000500 | Akurasi train 100% |
| **48** | **0,6570** | **99,79%** | **0,7375** | **97,78%** | **0,000250** | **BEST CHECKPOINT** |
| 58 | 0,6523 | 100,00% | 0,7445 | 97,22% | 0,000125 | Early stopping stop |

---

## 7. HASIL EVALUASI FINAL

Model terbaik (**Epoch 48**) dievaluasi pada Validation Set dan dilakukan pengujian akhir **satu kali (*one-shot*) pada Test Set** (460 sampel held-out yang belum pernah dilihat model selama training maupun pemilihan epoch):

### Metrik Evaluasi Kuantitatif

| Metrik Evaluasi | Validation Set (N=180) | Test Set (N=460) | Target Minimal Kontrak |
|---|---:|---:|:---:|
| **Loss (Cross Entropy)** | **0,7375** | **0,6820** | - |
| **Top-1 Accuracy** | **97,78%** | **99,13%** | $> 70,0\%$ |
| **Top-5 Accuracy** | **100,00%** | **100,00%** | $> 90,0\%$ |
| **Macro Precision** | **97,85%** | **99,18%** | $> 70,0\%$ |
| **Macro Recall** | **97,78%** | **99,12%** | $> 70,0\%$ |
| **Macro F1-Score** | **97,78%** | **99,12%** | $> 70,0\%$ |
| **Weighted F1-Score** | **97,70%** | **99,13%** | $> 70,0\%$ |

Pada test set berukuran 460 sampel, model berhasil memprediksi **456 sampel dengan benar** dan hanya salah pada **4 sampel**!

---

## 8. ANALISIS KELAS TERBAIK & TERBURUK

### 5 Kelas dengan Performa Tertinggi (F1-Score 100%)

| Label | Gloss | Precision | Recall | F1-Score | Support (Test) |
|---:|---|---:|---:|---:|---:|
| 0 | AIR | 1,0000 | 1,0000 | **1,0000** | 15 |
| 1 | BELAJAR | 1,0000 | 1,0000 | **1,0000** | 15 |
| 28 | PAGI | 1,0000 | 1,0000 | **1,0000** | 14 |
| 29 | SIANG | 1,0000 | 1,0000 | **1,0000** | 14 |
| 30 | SORE | 1,0000 | 1,0000 | **1,0000** | 14 |

Sebanyak **26 dari 32 kelas** memperoleh F1-Score sempurna **100,0%**.

### 5 Kelas dengan Performa Terendah

| Label | Gloss | Precision | Recall | F1-Score | Support (Test) |
|---:|---|---:|---:|---:|---:|
| 14 | KAPAN | 0,8667 | 0,9286 | **0,8966** | 14 |
| 15 | DIMANA | 1,0000 | 0,8571 | **0,9231** | 14 |
| 2 | CARI | 1,0000 | 0,9333 | **0,9655** | 15 |
| 18 | MERAH | 0,9333 | 1,0000 | **0,9655** | 14 |
| 10 | TERIMA_KASIH | 0,9375 | 1,0000 | **0,9677** | 15 |

### Analisis Kesalahan Klasifikasi (Confusion Analysis)

Dari confusion matrix, kesalahan prediksi terpusat pada:
1. **`DIMANA` vs `KAPAN`**:
   Dua sampel dari kelas `DIMANA` (label 15) diprediksi sebagai `KAPAN` (label 14). Secara fonologis dalam BISINDO, kedua isyarat tanya ini memiliki kemiripan orientasi telapak tangan dan lintasan gerakan di depan dada.
2. **`CARI` vs `TERIMA_KASIH`**:
   Satu sampel `CARI` (label 2) mengalami ambiguitas transisi tangan saat mendekati dagu/dada.
3. Seluruh kelas dua tangan (`MOTOR`, `BAGAIMANA`, `TEMAN`, `RUMAH`) memperoleh F1-score **100,0%** tanpa satu pun kesalahan klasifikasi.

---

## 9. KETERBATASAN MODEL M0

Sebagai model baseline pertama, M0 memiliki batas lingkup metodologis yang jelas:
1. **Signer-Dependent Scope**: Evaluasi dilakukan pada protokol Signer-Dependent (SD), di mana seluruh 5 signer terdistribusi di train, val, dan test. Model belum diuji pada protokol *Leave-One-Signer-Out* (Signer-Independent / SI).
2. **Isolated Gloss Classification**: Model hanya mengenali isyarat kata terisolasi (*isolated sign language recognition* / ISLR), bukan penerjemahan kalimat berkesinambungan (*continuous sign language translation* / CSLT).
3. **Modalitas Pose Tunggal**: Model belum memanfaatkan fitur RGB penampilan tangan/wajah (VideoMAE).

---

## 10. DAFTAR ARTEFAK HASIL EKSPERIMEN

Seluruh berkas artefak tersimpan rapi pada direktori:
`outputs/experiments/M0_student_baseline/`

| Berkas Artefak | Tipe / Format | Deskripsi |
|---|---|---|
| [`best_model.pt`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/best_model.pt) | PyTorch Checkpoint | State dict bobot model terbaik (Epoch 48, Val Acc 97,78%) |
| [`last_model.pt`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/last_model.pt) | PyTorch Checkpoint | State dict bobot model epoch terakhir (Epoch 58) |
| [`training_config.yaml`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/training_config.yaml) | YAML Config | Seluruh konfigurasi hyperparameter dan dataset M0 |
| [`training_history.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/training_history.csv) | CSV Log | Metrik train/val loss, accuracy, dan LR dari Epoch 1 s.d. 58 |
| [`evaluation_metrics.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/evaluation_metrics.json) | JSON Summary | Ringkasan metrik evaluasi test set, top-5, dan class ranking |
| [`classification_report.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/classification_report.csv) | CSV Report | Laporan presisi, recall, dan F1 per 32 kelas |
| [`confusion_matrix.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/confusion_matrix.png) | PNG Visual | Matriks kebingungan 32x32 pada 460 sampel test |
| [`training_loss.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/training_loss.png) | PNG Visual | Kurva penurunan training vs validation loss |
| [`training_accuracy.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/training_accuracy.png) | PNG Visual | Kurva peningkatan training vs validation accuracy |
| [`experiment_metadata.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/outputs/experiments/M0_student_baseline/experiment_metadata.json) | JSON Metadata | Metadata hardware, dependensi versi, seed, dan git commit |

---

## 11. KESIMPULAN & STATUS AKHIR

### Status: **`TRAINING COMPLETED`**

Model baseline **M0 Student Baseline** telah berhasil dilatih dari nol (*from scratch*), tersimpan secara lengkap, dan melampaui seluruh target performa dasar:
- **Test Accuracy**: **99,13%**
- **Test Macro F1-Score**: **99,12%**
- **Test Top-5 Accuracy**: **100,00%**
- **Reproducibility**: 100% terjaga melalui seed 42 dan konfigurasi YAML.
- **Git Status**: Branch `feature/dataset-acquisition` dengan Git HEAD `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` terjaga utuh tanpa commit/push.

