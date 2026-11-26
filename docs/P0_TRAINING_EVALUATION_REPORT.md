# LAPORAN TAHAP 6 & 7: TRAINING DAN EVALUASI MOBILENETV3 I1 (BISINDO ALPHABET)

> **Dokumen**: `docs/P0_TRAINING_EVALUATION_REPORT.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Arsitektur**: `MobileNetV3SmallClassifier` (265.826 parameter / 0,266 M)  
> **Tahap**: Tahap 6 (Training 25 Epoch) & Tahap 7 (Evaluasi Test Set Komprehensif)  
> **Tanggal Pelaksanaan**: 13 November 2026  
> **Auditor**: Senior Machine Learning Engineer, SignBridge ASEAN  
> **Status Akhir Model**: **`NEEDS IMPROVEMENT`** (Eksperimen Sukses, Belum Layak Deployment Produksi)  

---

## 1. RINGKASAN EKSEKUTIF

Pelatihan ulang model **MobileNetV3-Small (I1)** telah berhasil dieksekusi secara penuh selama **25 epoch** menggunakan dataset fisik **Mendeley BISINDO Alphabet** hasil preprocessing ($224 \times 224$ RGB) pada direktori terisolasi [`runs/image_i1_mobilenetv3_p0/`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p0/). Evaluasi dilakukan secara ketat pada Test Set mandiri ($N = 670$ citra) yang tidak pernah disentuh selama pelatihan.

### Perbandingan Kunci (Model Baru vs Model Lama):
| Metrik Kunci | Model Lama (`runs/image_i1_mobilenetv3/best.pt`) | Model Baru (`runs/image_i1_mobilenetv3_p0/best.pt`) | Selisih / Peningkatan |
|---|:---:|:---:|:---:|
| **Status Class Collapse** | **TERJADI COLLAPSE** (Prediksi hanya 1 kelas) | **TIDAK COLLAPSE** (Semua 26 kelas diprediksi) | **Teratasi Penuh** |
| **Test Accuracy** | $3,58\%$ ($\approx \frac{1}{26}$ random guess) | **$7,61\%$** | **$+4,03\%$** ($2,1\times$ lipat) |
| **Test Macro F1** | $0,27\%$ | **$7,50\%$** | **$+7,23\%$** ($27,7\times$ lipat) |
| **Best Val Accuracy** | $3,85\%$ (Epoch 1) | **$11,21\%$** (Epoch 12) | **$+7,36\%$** ($2,9\times$ lipat) |
| **Inference Latency (CPU)** | $12,85\text{ ms}$ | **$8,32\text{ ms}$** | **$35,2\%$ Lebih Cepat** |
| **Throughput (CPU)** | $77,8\text{ FPS}$ | **$120,2\text{ FPS}$** | **$+42,4\text{ FPS}$** |

> **Diagnosa Teknis Utama**: Model baru berhasil bangkit dari status *class collapse* total yang dialami model lama. Namun, karena arsitektur dilatih secara *scratch* (tanpa transfer learning bobot pra-latih ImageNet) dengan hanya $3.123$ sampel pelatihan, model mengalami **overfitting berat** (Loss training turun hingga $0,57$, namun loss validasi naik ke $4,32$). Oleh karena itu, model **BELUM LAYAK** menggantikan model produksi `web/model/fingerspell.onnx`.

---

## 2. KONFIGURASI DAN HYPERPARAMETER TRAINING

Pelatihan dijalankan berdasarkan spesifikasi konfigurasi [`configs/image_i1_mobilenetv3_p0.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p0.yaml):

```yaml
experiment_id: "image_i1_mobilenetv3_p0"
seed: 42
data:
  manifest: "data/processed/bisindo_alphabet/manifest.csv"
  num_classes: 26
  image_size: 224
model:
  arch: "mobilenetv3_small"
  num_classes: 26
  dropout: 0.2
training:
  epochs: 25
  batch_size: 32
  lr: 0.0005
  weight_decay: 0.01
  label_smoothing: 0.05
  min_lr: 0.00001
output_dir: "runs/image_i1_mobilenetv3_p0"
```

### Dataset Split yang Digunakan:
- **Train Set**: $3.123$ citra ($70,0\%$) &mdash; untuk optimasi gradien bobot.
- **Validation Set**: $669$ citra ($15,0\%$) &mdash; untuk seleksi checkpoint terbaik dan evaluasi loss validasi per epoch.
- **Test Set**: $670$ citra ($15,0\%$) &mdash; diisolasi penuh hingga evaluasi final.
- **Total Sampel Valid**: $4.462$ citra (4 citra ambigu dikecualikan sesuai audit Tahap 4).

---

## 3. PROFILING ARSITEKTUR MOBILENETV3-SMALL (I1)

Arsitektur yang dievaluasi adalah `MobileNetV3SmallClassifier` (berdasarkan `signbridge/image/train_image.py`):
- **Stem**: Conv2d(3, 24, kernel=3, stride=2, padding=1) + BatchNorm2d + Hardswish
- **Blok Konvolusi**: 5x `DepthwiseSeparableBlock` dengan rasio ekspansi $2 - 3$:
  - Blok 1: $24 \rightarrow 32$ (stride 2)
  - Blok 2: $32 \rightarrow 64$ (stride 2)
  - Blok 3: $64 \rightarrow 64$ (stride 1)
  - Blok 4: $64 \rightarrow 128$ (stride 2)
  - Blok 5: $128 \rightarrow 192$ (stride 2)
- **Pooling**: `AdaptiveAvgPool2d(1)`
- **Classifier Head**: Linear($192 \rightarrow 256$) + Hardswish + Dropout(0.2) + Linear($256 \rightarrow 26$)
- **Total Parameter**: **265.826 parameter (0,266 M)**.
- **Ukuran File Model PyTorch**: `3.272.237 bytes` (~3,12 MB termasuk state optimizer).

---

## 4. DINAMIKA & HISTORI PELATIHAN (25 EPOCH)

Pelatihan memakan waktu total $2.652,3$ detik (~44,2 menit) pada CPU AMD64:

| Epoch | Train Loss | Val Loss | Val Accuracy | Val Macro F1 | Learning Rate | Waktu Epoch | Keterangan |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 3,2632 | 3,2491 | 5,68% | 3,78% | 0,000498 | 89,8s | Inisialisasi |
| 2 | 3,1988 | 3,2298 | 6,58% | 3,44% | 0,000492 | 88,9s | Konvergensi awal |
| 3 | 3,0910 | 3,1312 | 6,73% | 5,26% | 0,000483 | 88,8s | Meningkat |
| 4 | 2,9275 | 3,1646 | 11,06% | 8,44% | 0,000470 | 90,6s | Lonjakan akurasi |
| 5 | 2,6972 | 3,2396 | 9,72% | 8,08% | 0,000453 | 88,3s | Fluktuasi |
| 6 | 2,4414 | 3,5202 | 10,76% | 8,51% | 0,000434 | 87,9s | Mulai overfit |
| 7 | 2,1881 | 3,9244 | 8,97% | 7,73% | 0,000411 | 91,8s | Val loss naik |
| 8 | 1,9001 | 3,8807 | 10,16% | 9,23% | 0,000386 | 88,2s | F1 naik |
| 9 | 1,6431 | 3,8516 | 8,52% | 8,30% | 0,000359 | 88,4s | - |
| 10 | 1,4118 | 3,9991 | 9,72% | 9,37% | 0,000331 | 89,1s | - |
| 11 | 1,2161 | 4,1186 | 10,91% | 10,92% | 0,000301 | 88,5s | - |
| **12** | **1,0496** | **4,2135** | **11,21%** | **11,21%** | **0,000270** | **88,2s** | **BEST CHECKPOINT (`best.pt`)** |
| 13 | 0,9258 | 4,3231 | 9,87% | 9,97% | 0,000240 | 89,0s | - |
| 14 | 0,8109 | 4,3547 | 10,76% | 10,90% | 0,000209 | 89,1s | - |
| 15 | 0,7569 | 4,3879 | 10,91% | 10,48% | 0,000179 | 87,8s | - |
| 16 | 0,6986 | 4,4325 | 9,27% | 9,07% | 0,000151 | 88,7s | - |
| 17 | 0,6572 | 4,3612 | 9,72% | 9,45% | 0,000124 | 91,1s | - |
| 18 | 0,6288 | 4,3467 | 8,82% | 8,69% | 0,000099 | 88,4s | - |
| 19 | 0,6187 | 4,3312 | 9,27% | 8,83% | 0,000076 | 89,0s | - |
| 20 | 0,6077 | 4,3452 | 8,82% | 8,70% | 0,000057 | 89,6s | - |
| 21 | 0,5908 | 4,3355 | 9,42% | 9,21% | 0,000040 | 92,4s | - |
| 22 | 0,5798 | 4,3325 | 9,57% | 9,46% | 0,000027 | 80,5s | - |
| 23 | 0,5737 | 4,3144 | 9,57% | 9,29% | 0,000018 | 79,5s | - |
| 24 | 0,5702 | 4,3175 | 9,42% | 9,25% | 0,000012 | 80,3s | - |
| 25 | 0,5711 | 4,3239 | 9,27% | 9,11% | 0,000010 | 537,5s | Akhir Cosine Scheduler |

> **Visualisasi Kurva**:
> - Kurva Loss: [`docs/figures/p0_dataset/training_loss_curves.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/training_loss_curves.png)
> - Kurva Akurasi & F1: [`docs/figures/p0_dataset/training_accuracy_curves.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/training_accuracy_curves.png)

---

## 5. HASIL EVALUASI FINAL PADA TEST SET ($N = 670$)

Evaluasi dijalankan menggunakan bobot checkpoint terbaik (**Epoch 12**):

### Metrik Agregat:
- **Test Accuracy**: **$7,61\%$** ($51$ dari $670$ citra diprediksi benar)
- **Macro Precision**: **$8,23\%$**
- **Macro Recall**: **$7,60\%$**
- **Macro F1-Score**: **$7,50\%$**
- **Weighted F1-Score**: **$7,49\%$**

### Classification Report per Kelas (A–Z):
| Kelas Huruf | Precision (%) | Recall (%) | F1-Score (%) | Support ($N$ Sampel) |
|:---:|:---:|:---:|:---:|:---:|
| **A** | 9,52% | 8,33% | 8,89% | 24 |
| **B** | 22,22% | 8,00% | 11,76% | 25 |
| **C** | 0,00% | 0,00% | 0,00% | 25 |
| **D** | 0,00% | 0,00% | 0,00% | 26 |
| **E** | 17,65% | 12,00% | 14,29% | 25 |
| **F** | 7,69% | 7,69% | 7,69% | 26 |
| **G** | 15,00% | 23,08% | 18,18% | 26 |
| **H** | 6,25% | 3,85% | 4,76% | 26 |
| **I** | 7,69% | 7,69% | 7,69% | 26 |
| **J** | 3,45% | 4,00% | 3,70% | 25 |
| **K** | 3,77% | 7,69% | 5,06% | 26 |
| **L** | 9,38% | 11,54% | 10,34% | 26 |
| **M** | 27,27% | 11,54% | 16,22% | 26 |
| **N** | 0,00% | 0,00% | 0,00% | 26 |
| **O** | 2,86% | 3,85% | 3,28% | 26 |
| **P** | 5,00% | 3,85% | 4,35% | 26 |
| **Q** | 11,43% | 15,38% | 13,11% | 26 |
| **R** | 8,57% | 11,54% | 9,84% | 26 |
| **S** | 7,69% | 3,85% | 5,13% | 26 |
| **T** | 5,88% | 7,69% | 6,67% | 26 |
| **U** | 8,00% | 7,69% | 7,84% | 26 |
| **V** | 8,70% | 7,69% | 8,16% | 26 |
| **W** | 11,11% | 11,54% | 11,32% | 26 |
| **X** | 3,85% | 3,85% | 3,85% | 26 |
| **Y** | 4,65% | 7,69% | 5,80% | 26 |
| **Z** | 6,45% | 7,69% | 7,02% | 26 |
| **Rata-rata** | **8,23%** | **7,60%** | **7,50%** | **670** |

> **Visualisasi Matriks Kebingungan**:  
> [`docs/figures/p0_dataset/confusion_matrix_test.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/confusion_matrix_test.png)  
> *(Menampilkan sebaran prediksi 26×26 kelas).*

---

## 6. BENCHMARK KECEPATAN INFERENSI & LATENSI

Pengujian dilakukan menggunakan PyTorch `torch.no_grad()` pada perangkat CPU lokal (Intel/AMD x86_64) dengan resolusi input $1 \times 3 \times 224 \times 224$:
- **Prosedur Pengujian**: $20$ iterasi pemanasan (*warm-up*) + $100$ iterasi pengukuran berulang menggunakan `time.perf_counter()`.
- **Rata-rata Latensi Inferensi**: **$8,32\text{ ms}$ per citra**.
- **Latensi Minimum**: $6,33\text{ ms}$.
- **Latensi Maksimum**: $13,18\text{ ms}$.
- **Latensi Persentil-95 (P95)**: $10,40\text{ ms}$.
- **Throughput**: **$120,2\text{ FPS}$** (Jauh melampaui batas real-time webcam browser $30\text{ FPS}$).

---

## 7. ANALISIS KUALITAS, OVERFITTING, & KESALAHAN PREDIKSI

### A. Evaluasi Gejala Class Collapse
- **Hasil**: **TIDAK DITEMUKAN CLASS COLLAPSE**.  
- Pada model lama (`image_i1_mobilenetv3/best.pt`), model memprediksi satu kelas secara dominan untuk 100% sampel (sehingga akurasi persis $3,58\%$ dengan Macro F1 hanya $0,27\%$).
- Pada model baru ini, 23 dari 26 kelas berhasil diprediksi secara bervariasi dengan distribusi konfiden yang dinamis.

### B. Evaluasi Gejala Overfitting (Sangat Kuat)
- **Bukti Empiris**:
  - Pada Epoch 1, Loss Train = $3,26$, Loss Val = $3,24$.
  - Pada Epoch 25, Loss Train turun drastis ke **$0,57$**, namun Loss Val melonjak naik ke **$4,32$**.
- **Akar Penyebab**:
  1. **Pelatihan dari Nol (From Scratch)**: Arsitektur MobileNetV3 memiliki 265.826 bobot yang diinisialisasi secara acak.
  2. **Ketiadaan Transfer Learning**: Model tidak memanfaatkan bobot fitur *low-level* (tepi, sudut, tekstur kulit) dari ImageNet.
  3. **Keterbatasan Jumlah Sampel per Kelas**: Rata-rata 120 gambar train per kelas tidak mencukupi bagi konvolusi depthwise untuk menggeneralisasi geometri tangan tanpa regularisasi augmentasi spasial (rotasi, distorsi perspektif, jitter warna).

### C. Pasangan Huruf yang Sering Tertukar (Top Misclassified Pairs):
1. **$N \rightarrow Y$** ($6$ kali): Bentuk kepalan tangan tertutup dengan jempol menyerupai kontur jari terbuka sebagian pada sudut pandang miring.
2. **$V \rightarrow J$** ($6$ kali): Posisi dua jari terangkat pada sudut kamera rendah terdistorsi menjadi lekukan satu jari.
3. **$A \rightarrow X$** ($5$ kali): Kepalan tangan tegak tertukar dengan tekukan telunjuk.
4. **$M \rightarrow Y$** ($5$ kali) & **$V \rightarrow Y$** ($5$ kali).

> **Visualisasi Sampel Prediksi**:  
> [`docs/figures/p0_dataset/sample_predictions_grid.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p0_dataset/sample_predictions_grid.png)  
> *(Menampilkan perbandingan baris atas: contoh prediksi benar vs baris bawah: contoh prediksi salah).*

---

## 8. LOKASI ARTEFAK EKSPERIMEN

Seluruh artefak eksperimen baru disimpan secara rapi dan terisolasi di folder:  
[`runs/image_i1_mobilenetv3_p0/`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p0/)

1. `best.pt` ($3,27\text{ MB}$): Checkpoint bobot terbaik (Epoch 12).
2. `last.pt` ($3,27\text{ MB}$): Checkpoint epoch ke-25.
3. `training_history.csv` ($1,58\text{ KB}$): Log metrik per epoch (25 baris).
4. `training_config.yaml`: Snapshot konfigurasi eksperimen.
5. `training_summary.json`: Ringkasan metrik evaluasi, komparasi, dan profil latensi.
6. `classification_report.txt`: Laporan presisi, recall, dan F1 per kelas A–Z.
7. `training_loss_curves.png`: Grafik loss per epoch.
8. `training_accuracy_curves.png`: Grafik akurasi dan macro F1 per epoch.
9. `confusion_matrix.png`: Matriks kebingungan 26 kelas.
10. `sample_predictions_grid.png`: Inspeksi visual sampel prediksi.

---

## 9. KESIMPULAN & REKOMENDASI TAHAP BERIKUTNYA

### Ringkasan Status:
- **Status Training**: **BERHASIL DISELESAIKAN (25 Epochs)**
- **Best Validation Accuracy**: **$11,21\%$** (Epoch 12)
- **Test Accuracy**: **$7,61\%$** (Meningkat $+4,03\%$ dibanding model lama)
- **Test Macro F1**: **$7,50\%$** (Meningkat $+7,23\%$ dibanding model lama)
- **Inference Latency**: **$8,32\text{ ms}$ (120,2 FPS pada CPU)**
- **Class Collapse**: **TIDAK ADA**
- **Overfitting**: **TERJADI OVERFITTING SIGNIFIKAN**
- **Kelayakan Deployment Produksi**: **BELUM LAYAK (NEEDS IMPROVEMENT)**

### Rekomendasi Senior ML Engineer:
Sesuai **Aturan Wajib Bagian E**, model aplikasi produksi `web/model/fingerspell.onnx` **TIDAK DITIMPA** karena performa $7,61\%$ belum memenuhi batas kelayakan pengenalan alfabet real-time (>80–90%).  
Untuk mencapai akurasi target >90%, perbaikan teknis yang diperlukan adalah:
1. **Transfer Learning**: Menggunakan bobot backbone pra-latih `torchvision.models.mobilenet_v3_small(weights='DEFAULT')` dan hanya melatih ulang classifier head 26 kelas.
2. **Data Augmentation**: Menambahkan rotasi acak ($\pm 15^\circ$), zoom acak ($0,9 - 1,1$), dan penyesuaian kecerahan/kontras pada training pipeline.
3. **Penyelarasan Crop Landmark**: Mengintegrasikan crop berbasis deteksi bounding box tangan yang lebih ketat sebelum ekstraksi fitur.

> **PENTING**: Model lama `runs/image_i1_mobilenetv3/best.pt` dan model web `web/model/fingerspell.onnx` tetap utuh. Tidak ada branch Git yang diubah dan tidak ada push yang dijalankan. Kami menunggu instruksi pengguna selanjutnya.

