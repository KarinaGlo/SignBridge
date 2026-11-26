# LAPORAN EVALUASI EKSPERIMEN I1-P1: TRANSFER LEARNING MOBILENETV3-SMALL PRETRAINED IMAGENET

> **Dokumen**: `docs/P1_TRAINING_EVALUATION_REPORT.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Arsitektur**: `torchvision.models.mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)`  
> **Parameter**: $1.544.506$ parameter ($\approx 1,545\text{ M}$) | Checkpoint Size: $6,01\text{ MB}$  
> **Dataset**: Mendeley BISINDO Alphabet ($4.462$ citra valid, $26$ kelas A–Z)  
> **Tahap Pelatihan**: Stage 1 Feature Extraction ($5$ epoch) + Stage 2 Fine-Tuning ($15$ epoch)  
> **Tanggal Pelaksanaan**: 13 November 2026  
> **Auditor**: Senior Machine Learning Engineer, SignBridge ASEAN  
> **Status Akhir Eksperimen**: **`IMPROVED`** (Peningkatan Signifikan Melampaui Baseline P0)

---

## 1. RINGKASAN EKSEKUTIF

Eksperimen **I1-P1** mengevaluasi penerapan arsitektur resmi **`torchvision.models.mobilenet_v3_small`** dengan bobot pra-latih ImageNet (*ImageNet-1K pretrained weights*) untuk menyelesaikan masalah *overfitting* berat dan akurasi rendah yang terjadi pada eksperimen scratch baseline P0.

Pelatihan dijalankan secara sistematis menggunakan strategi transfer learning dua tahap (*two-stage transfer learning*) dan dievaluasi secara ketat pada Test Set mandiri ($N = 670$ citra, $15,0\%$ dataset) yang tidak pernah disentuh selama optimasi bobot maupun seleksi hyperparameter.

### Perbandingan Utama P0 (Scratch Baseline) vs P1 (Pretrained ImageNet):
| Metrik Kunci | Baseline P0 (`runs/image_i1_mobilenetv3_p0/best.pt`) | Transfer Learning P1 (`runs/image_i1_mobilenetv3_p1/best.pt`) | Delta Peningkatan (P1 vs P0) | Evaluasi Status |
|---|:---:|:---:|:---:|:---:|
| **Arsitektur Model** | Custom 5-block CNN ($0,266\text{ M}$) | Official Torchvision MobileNetV3-Small ($1,545\text{ M}$) | $+1,279\text{ M}$ parameter | Arsitektur Standar Industri |
| **Inisialisasi Bobot** | Random Weight (*Scratch*) | **ImageNet-1K Pretrained (`DEFAULT`)** | Fitur visual teruji | Ekstraksi Fitur Unggul |
| **Test Accuracy** | **$7,61\%$** | **$61,19\%$** | **$+53,58\%$** ($8,04\times$ lipat) | **Sangat Signifikan** |
| **Test Macro F1** | **$7,50\%$** | **$61,57\%$** | **$+54,07\%$** ($8,21\times$ lipat) | **Sangat Signifikan** |
| **Test Macro Precision** | $8,23\%$ | **$63,30\%$** | **$+55,07\%$** ($7,69\times$ lipat) | Kualitas Prediksi Positif Tinggi |
| **Test Macro Recall** | $7,60\%$ | **$61,27\%$** | **$+53,67\%$** ($8,06\times$ lipat) | Sensitivitas Kelas Merata |
| **Test Weighted F1** | $7,49\%$ | **$61,53\%$** | **$+54,04\%$** | Keseimbangan Distribusi |
| **Kelas dengan Recall = 0** | **3 Kelas (C, D, N)** | **0 Kelas (Nihil)** | Teratasi $100\%$ | **Semua 26 Kelas Berhasil** |
| **Status Overfitting** | **Parah** (Train $0,57$ vs Val $4,32$) | **Terkendali Baik** (Train $1,11$ vs Val $1,55$) | Overfitting berhasil diredam | Generalisasi Terbukti |
| **Best Val Accuracy** | $11,21\%$ (Epoch 12) | **$60,24\%$** (Epoch 18) | **$+49,03\%$** ($5,37\times$ lipat) | Konvergensi Stabil |
| **Inference Latency (CPU)** | $8,32\text{ ms}$ | **$18,72\text{ ms}$** | $+10,40\text{ ms}$ | Sangat Memadai ($53,4\text{ FPS}$) |

> **Kesimpulan Status**: **`IMPROVED`**. Eksperimen I1-P1 secara meyakinkan membuktikan bahwa pemanfaatan transfer learning dari bobot pra-latih ImageNet melipatgandakan performa pengenalan abjad BISINDO hingga $8\times$ lipat, meredam overfitting, dan mengeliminasi fenomena *zero-recall* pada seluruh 26 kelas.

---

## 2. AUDIT PRA-TRAINING (RINGKASAN TAHAP A)

Audit pra-training lengkap telah didokumentasikan pada [`docs/P1_PRETRAINING_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/P1_PRETRAINING_AUDIT.md) dengan ringkasan temuan:

1. **Manifest & Integritas Dataset**:
   - Manifest: [`data/processed/bisindo_alphabet/manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/manifest.csv).
   - Sebanyak $4.462$ citra valid terdistribusi dalam 26 kelas alfabet (A–Z).
   - Pembagian dataset stratified: Train = $3.123$ ($70\%$), Val = $669$ ($15\%$), Test = $670$ ($15\%$).
2. **Data Leakage Check**:
   - SHA-256 intersection antar-split bernilai himpunan kosong ($\text{Train} \cap \text{Val} = \emptyset, \text{Train} \cap \text{Test} = \emptyset, \text{Val} \cap \text{Test} = \emptyset$). Tidak ada kebocoran citra antar-split.
3. **Penyebab Kegagalan Baseline P0**:
   - Arsitektur P0 bukanlah MobileNetV3-Small resmi, melainkan custom CNN 5-blok ($0,266\text{ M}$ parameter) yang dilatih dari nol (*from scratch*). Tanpa bobot pra-latih dan kapasitas memadai, model hanya menghafal noise training data ($Train Loss \to 0,57$) namun gagal total saat validasi ($Val Loss \to 4,32$).
4. **Resolusi Diskrepansi Prediksi P0 (26 vs 23 Kelas)**:
   - Evaluasi langsung pada test set membuktikan bahwa semua 26 kelas muncul pada array prediksi `y_pred` (tidak terjadi *single-class collapse*).
   - Namun, sebanyak 3 kelas (C, D, dan N) memiliki *True Positives* $= 0$ (Recall $= 0\%$). Dengan demikian, hanya 23 kelas yang prediksinya berhasil benar minimal satu kali.

---

## 3. ARSITEKTUR MODEL P1 & IMPLEMENTASI

Model diimplementasikan pada file baru [`signbridge/image/models/mobilenetv3_p1.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/models/mobilenetv3_p1.py):

- **Backbone**: `torchvision.models.mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)`
  - Terdiri dari 13 layer features (`features[0]` hingga `features[12]`) mencakup konvolusi awal, 11 blok Inverted Residual dengan Squeeze-and-Excitation (SE), dan konvolusi proyeksi 1x1.
- **Classification Head**:
  - Head default torchvision MobileNetV3-Small memiliki struktur:
    $$\text{AdaptiveAvgPool2d}(1) \to \text{Linear}(576, 1024) \to \text{Hardswish} \to \text{Dropout}(0.2) \to \text{Linear}(1024, 1000)$$
  - Lapisan terakhir `classifier[3]` diganti menjadi:
    $$\text{Linear}(1024, 26)$$
  - Bobot linear baru diinisialisasi menggunakan metode He/Kaiming normal dengan bias nol.
- **Parameter Breakdown**:
  - Total Parameter: **$1.544.506$ parameter** ($1,545\text{ M}$)
  - Parameter Backbone: $927.008$ parameter
  - Parameter Classifier Head: $617.498$ parameter

---

## 4. PREPROCESSING & AUGMENTASI BAHASA ISYARAT

1. **Input Normalization**:
   - Dimensi input: $224 \times 224$ piksel RGB, rentang $[0.0, 1.0]$.
   - Normalisasi standar ImageNet-1K: $\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$.
2. **Augmentasi Khusus Bahasa Isyarat (Hanya pada Train Set)**:
   - **RandomResizedCrop**: Skala konservatif $(0,92\text{--}1,0)$ dan rasio aspek $(0,95\text{--}1,05)$ untuk menjaga orientasi tangan.
   - **RandomRotation**: Rotasi kecil $\pm 10^\circ$ merefleksikan variasi alami kemiringan pergelangan tangan penutur.
   - **ColorJitter**: Brightness $\pm 15\%$, contrast $\pm 15\%$, saturation $\pm 10\%$ untuk simulasi variasi pencahayaan ruangan webcam.
   - **ATURAN WAJIB**: **TANPA HORIZONTAL FLIP**. Membalik citra tangan secara horizontal akan merusak polaritas isyarat (misalnya gestur tangan kanan tertukar menjadi gestur tangan kiri yang dapat mengubah makna fonologis abjad).
3. **Validation & Test Sets**:
   - Transformasi deterministik: Resize $224 \times 224$ + ToTensor + Normalisasi ImageNet tanpa augmentasi acak.

---

## 5. STRATEGI TRAINING DUA TAHAP (TWO-STAGE TRANSFER LEARNING)

Pelatihan dijalankan berdasarkan [`configs/image_i1_mobilenetv3_p1.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p1.yaml) dengan tahapan:

### A. Stage 1: Feature Extraction (Epoch 1 – 5)
- **Status Backbone**: Seluruh layer `features` dibekukan (*frozen*, `requires_grad = False`).
- **Parameter Terlatih**: $617.498$ parameter pada classifier head.
- **Optimizer**: AdamW ($lr = 10^{-3}$, weight decay $= 10^{-4}$).
- **Scheduler**: CosineAnnealingLR ($T_{\max} = 5, \eta_{\min} = 10^{-5}$).
- **Hasil Stage 1**: Akurasi validasi melonjak dari $36,17\%$ (Epoch 1) menjadi **$52,47\%$** (Epoch 5), membuktikan bahwa fitur visual representasional ImageNet langsung dapat dimanfaatkan untuk membedakan gestur alfabet.

### B. Stage 2: Fine-Tuning (Epoch 6 – 20)
- **Status Backbone**: Dibuka secara parsial dari layer atas (`features[9]` hingga `features[12]`).
  - Layer bawah (`features[0]` hingga `features[8]`) tetap dibekukan untuk mengunci filter visual tingkat rendah (*edges*, *corners*, tekstur dasar).
  - Parameter terlatih bertambah menjadi $1.353.986$ parameter.
- **Differential Learning Rates**:
  - Backbone ter-unfreeze: $lr = 10^{-5}$ (sangat rendah untuk menghindari *catastrophic forgetting*).
  - Classifier Head: $lr = 10^{-4}$.
- **Optimizer**: AdamW (weight decay $= 10^{-4}$).
- **Scheduler**: CosineAnnealingLR down to $\eta_{\min} = 10^{-6}$.
- **Early Stopping**: Patience $= 5$ epoch berdasarkan `Validation Macro F1`.
- **Hasil Stage 2**: Akurasi validasi terus meningkat hingga mencapai puncaknya pada **Epoch 18 (Val Acc: $60,24\%$, Val Macro F1: $59,58\%$)**. Checkpoint inilah yang disimpan sebagai `best.pt`.

---

## 6. HASIL EVALUASI KOMPREHENSIF PADA TEST SET

Evaluasi final dijalankan pada Test Set independen ($N = 670$ citra) menggunakan checkpoint terbaik [`runs/image_i1_mobilenetv3_p1/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/best.pt).

### A. Metrik Agregat Test Set
- **Test Accuracy**: **$61,19\%$** (Baseline P0: $7,61\%$ | Peningkatan $+53,58\%$)
- **Macro Precision**: **$63,30\%$** (Baseline P0: $8,23\%$ | Peningkatan $+55,07\%$)
- **Macro Recall**: **$61,27\%$** (Baseline P0: $7,60\%$ | Peningkatan $+53,67\%$)
- **Macro F1-Score**: **$61,57\%$** (Baseline P0: $7,50\%$ | Peningkatan $+54,07\%$)
- **Weighted F1-Score**: **$61,53\%$** (Baseline P0: $7,49\%$ | Peningkatan $+54,04\%$)

### B. Classification Report per Kelas (26 Kelas A–Z)
| Kelas | Support | Precision | Recall | F1-Score | Status P0 vs P1 |
|:---:|:---:|:---:|:---:|:---:|:---|
| **A** | 24 | $75,00\%$ | **$87,50\%$** | $80,77\%$ | Sangat Tinggi (Recall P0: $8,33\%$) |
| **B** | 25 | $77,27\%$ | **$68,00\%$** | $72,34\%$ | Meningkat $8,5\times$ |
| **C** | 25 | $30,30\%$ | **$40,00\%$** | $34,48\%$ | **Bangkit dari Recall 0% di P0** |
| **D** | 26 | $41,67\%$ | **$38,46\%$** | $40,00\%$ | **Bangkit dari Recall 0% di P0** |
| **E** | 25 | $76,00\%$ | **$76,00\%$** | $76,00\%$ | Sangat Kuat |
| **F** | 26 | $89,47\%$ | **$65,38\%$** | $75,56\%$ | Presisi Tinggi |
| **G** | 26 | $86,96\%$ | **$76,92\%$** | $81,63\%$ | Sangat Kuat |
| **H** | 26 | $88,24\%$ | **$57,69\%$** | $69,77\%$ | Presisi Sangat Tinggi |
| **I** | 26 | $50,00\%$ | **$42,31\%$** | $45,83\%$ | Meningkat $5,5\times$ |
| **J** | 25 | $45,45\%$ | **$60,00\%$** | $51,72\%$ | Meningkat $15\times$ |
| **K** | 26 | $76,47\%$ | **$50,00\%$** | $60,47\%$ | Presisi Kuat |
| **L** | 26 | $78,26\%$ | **$69,23\%$** | $73,47\%$ | Gestur 'L' Terklasifikasi Baik |
| **M** | 26 | $62,96\%$ | **$65,38\%$** | $64,15\%$ | Meningkat $5,7\times$ |
| **N** | 26 | $60,87\%$ | **$53,85\%$** | $57,14\%$ | **Bangkit dari Recall 0% di P0** |
| **O** | 26 | $53,57\%$ | **$57,69\%$** | $55,56\%$ | Meningkat $15\times$ |
| **P** | 26 | $29,63\%$ | **$30,77\%$** | $30,19\%$ | Meningkat $8\times$ |
| **Q** | 26 | $79,17\%$ | **$73,08\%$** | $76,00\%$ | Kuat |
| **R** | 26 | $40,74\%$ | **$42,31\%$** | $41,51\%$ | Jari Menyilang Terdeteksi |
| **S** | 26 | $48,57\%$ | **$65,38\%$** | $55,74\%$ | Meningkat $17\times$ |
| **T** | 26 | $47,22\%$ | **$65,38\%$** | $54,84\%$ | Meningkat $8,5\times$ |
| **U** | 26 | $66,67\%$ | **$46,15\%$** | $54,55\%$ | Presisi Baik |
| **V** | 26 | $53,33\%$ | **$61,54\%$** | $57,14\%$ | Meningkat $8\times$ |
| **W** | 26 | $65,62\%$ | **$80,77\%$** | $72,41\%$ | Sangat Kuat |
| **X** | 26 | $70,97\%$ | **$84,62\%$** | $77,19\%$ | Sangat Kuat |
| **Y** | 26 | $71,43\%$ | **$57,69\%$** | $63,83\%$ | Gestur Jempol-Kelingking |
| **Z** | 26 | $80,00\%$ | **$76,92\%$** | $78,43\%$ | Sangat Kuat |

> **Analisis Kritis Recall**: Pada eksperimen baseline P0, kelas C, D, dan N memiliki nilai recall $0\%$ (tidak berhasil menebak satupun sampel uji). Pada P1, seluruh 26 kelas memiliki **Recall $> 30\%$**, dengan rata-rata recall melampaui **$61,27\%$**.

---

## 7. ANALISIS CONFUSION MATRIX & KESALAHAN PREDIKSI

Visualisasi confusion matrix tersimpan pada [`docs/figures/p1/confusion_matrix_p1.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p1/confusion_matrix_p1.png) dan distribusi prediksi pada [`docs/figures/p1/prediction_distribution_p1.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p1/prediction_distribution_p1.png).

### 10 Pasangan Kelas yang Paling Sering Tertukar:
1. **D $\to$ P ($12$ kali)** & **P $\to$ D ($8$ kali)**:
   - *Penyebab Fonologis*: Bentuk jari isyarat D dan P dalam alfabet BISINDO memiliki kemiripan morfologi tangan yang sangat tinggi (jari telunjuk menjulang dengan jempol dan jari tengah melingkar), di mana perbedaannya terletak pada orientasi vertikal vs horizontal-bawah. Variasi sudut crop menyebabkan ambiguitas fitur 2D.
2. **N $\to$ M ($9$ kali)** & **M $\to$ N ($8$ kali)**:
   - *Penyebab Fonologis*: Gestur M melipat 3 jari di atas ibu jari, sedangkan gestur N melipat 2 jari di atas ibu jari. Pada citra $224 \times 224$ dari sudut depan, lipatan jari ketiga sering kali terhalang (*occluded*).
3. **U $\to$ C ($7$ kali)**:
   - Jari telunjuk dan tengah yang rapat membentuk lengkungan tipis yang pada resolusi rendah menyerupai bukaan kurva huruf C.
4. **I $\to$ C ($5$ kali)**:
   - Kelingking yang melengkung saat penutur tidak mengangkat tangan tegak lurus.
5. **I $\to$ J ($5$ kali)** & **J $\to$ I ($5$ kali)**:
   - Huruf I adalah isyarat statis kelingking ke atas, sedangkan J adalah gerakan dinamis melengkung (*hook stroke*). Pada dataset citra statis 2D, representasi spasial I dan J hampir identik karena informasi trajektori temporal tidak ada pada gambar tunggal.
6. **K $\to$ T ($5$ kali)** & **P $\to$ T ($5$ kali)**:
   - Posisi ibu jari yang menyempil di antara lipatan jari.

---

## 8. ANALISIS OVERFITTING & DIVERGENSI LOSS

Grafik kurva pelatihan tersimpan pada [`docs/figures/p1/training_loss_curves.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p1/training_loss_curves.png) dan [`docs/figures/p1/training_accuracy_curves.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/figures/p1/training_accuracy_curves.png):

- **Baseline P0 (Overfitting Parah)**:
  - Training loss turun dari $3,21 \to 0,57$ ($+82\%$ penurunan).
  - Validation loss justru melonjak drastis dari $3,19 \to 4,32$.
  - Gap train-val loss mencapai **$3,75$**, mengindikasikan model hanya menghafal citra training.
- **Transfer Learning P1 (Terkendali & Sehat)**:
  - Training loss turun bertahap dari $2,77 \to 1,11$.
  - Validation loss ikut turun dari $2,28 \to 1,55$.
  - Gap train-val loss hanya **$0,44$**.
  - Akurasi validasi bergerak selaras dengan akurasi training ($Train: 77,2\%$ vs $Val: 60,2\%$).
  - **Kesimpulan**: *Overfitting* berhasil ditekan secara drastis melalui kombinasi augmentasi konservatif, regularisasi dropout ($0,2$), weight decay ($10^{-4}$), dan transfer learning ImageNet.

---

## 9. PENGUKURAN PERFORMA & LATENSI INFERENSI (CPU)

Pengukuran dilakukan pada prosesor CPU menggunakan 20 iterasi warm-up dan 100 iterasi benchmark inferensi per citra:

| Parameter Benchmark | Baseline P0 (Mini-CNN) | Transfer Learning P1 (MobileNetV3-Small) | Keterangan |
|---|:---:|:---:|:---|
| **Mean Latency** | $8,32\text{ ms}$ | **$18,72\text{ ms}$** | $+10,4\text{ ms}$ (Tambahan blok SE & Inverted Residual) |
| **Median Latency** | $8,15\text{ ms}$ | **$18,30\text{ ms}$** | Sangat stabil dan konsisten |
| **P95 Latency** | $10,12\text{ ms}$ | **$21,59\text{ ms}$** | Jauh di bawah batas toleransi real-time ($50\text{ ms}$) |
| **Throughput (FPS)** | $120,2\text{ FPS}$ | **$53,4\text{ FPS}$** | **$1,78\times$ di atas standar real-time webcam (30 FPS)** |
| **Ukuran Checkpoint** | $1,08\text{ MB}$ | **$6,01\text{ MB}$** | Sangat ringan untuk diekspor ke ONNX web |

> **Catatan Validitas Benchmark**: Pengukuran latensi di atas murni merefleksikan inferensi PyTorch model terhadap tensor input $[1, 3, 224, 224]$ pada CPU lokal. Pengukuran ini belum mencakup *overhead* deteksi tangan MediaPipe, crop bounding box, normalisasi kanvas di JavaScript, maupun transmisi frame pada peramban web.

---

## 10. REKAPITULASI FILE & ARTEFAK YANG DIHASILKAN

Seluruh artefak eksperimen dibuat pada direktori terisolasi tanpa mengubah kode produksi maupun artefak P0:

### A. File Baru yang Dibuat:
1. **Laporan Audit**: [`docs/P1_PRETRAINING_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/P1_PRETRAINING_AUDIT.md)
2. **Laporan Evaluasi**: [`docs/P1_TRAINING_EVALUATION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/P1_TRAINING_EVALUATION_REPORT.md)
3. **Arsitektur Model**: [`signbridge/image/models/__init__.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/models/__init__.py), [`signbridge/image/models/mobilenetv3_p1.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/models/mobilenetv3_p1.py)
4. **Konfigurasi Eksperimen**: [`configs/image_i1_mobilenetv3_p1.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p1.yaml)
5. **Script Training & Evaluasi**: [`scripts/train_and_evaluate_p1.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/train_and_evaluate_p1.py)
6. **Artefak Model (`runs/image_i1_mobilenetv3_p1/`)**:
   - `best.pt` ($6,01\text{ MB}$, bobot checkpoint terbaik pada Epoch 18)
   - `last.pt` ($6,01\text{ MB}$, bobot epoch terakhir)
   - `training_history.csv` (log numerik train/val loss, akurasi, F1 per epoch)
   - `training_config.yaml` (arsip konfigurasi pelatihan)
   - `training_summary.json` (ringkasan metrik mesin JSON lengkap)
   - `classification_report.txt` (metrik precision/recall/F1 per kelas)
   - `confusion_matrix.csv` (matriks kebingungan numerik $26 \times 26$)
   - `predictions.csv` (prediksi baris-demi-baris pada 670 citra test set)
7. **Visualisasi Ilmiah (`docs/figures/p1/`)**:
   - `training_loss_curves.png` (kurva loss Stage 1 & Stage 2)
   - `training_accuracy_curves.png` (kurva akurasi train vs val)
   - `training_f1_curves.png` (kurva Macro F1 validasi)
   - `confusion_matrix_p1.png` (matriks visual 26 kelas)
   - `prediction_distribution_p1.png` (perbandingan prediksi vs ground truth)
   - `sample_predictions_p1.png` (grid sampel prediksi benar dan salah)

### B. File Kritis yang Tidak Diubah / Dijaga Utuh:
- Model ONNX produksi: [`web/model/fingerspell.onnx`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/fingerspell.onnx) (tidak disentuh).
- Model baseline lama: [`runs/image_i1_mobilenetv3/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3/best.pt) (tidak disentuh).
- Checkpoint P0: [`runs/image_i1_mobilenetv3_p0/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p0/best.pt) (tidak disentuh).
- Frontend web & UI (`web/index.html`, `web/js/*`) (tidak disentuh).
- Backend FastAPI & Database PostgreSQL (tidak disentuh).
- Git repository working tree (tidak ada branch switch, commit, atau push).

---

## 11. KETERBATASAN EKSPERIMEN & MASALAH YANG TERSISA

1. **Ambiguitas Spasial Isyarat Serupa**:
   - Pasangan gestur D vs P ($20$ kesalahan total) dan M vs N ($17$ kesalahan total) memiliki kesamaan bentuk tangan yang sangat tinggi. Model citra 2D murni membutuhkan penajaman fitur orientasi pergelangan tangan atau integrasi estimasi sudut MediaPipe Hand Landmarks.
2. **Keterbatasan Isyarat Dinamis (I vs J, Z)**:
   - Huruf J dan Z secara tradisional merupakan gestur dinamis yang melibatkan sapuan gerakan (*motion stroke*). Pengenalan berbasis citra tunggal statis kehilangan informasi arah gerak sehingga huruf I dan J masih sering tertukar ($10$ kesalahan total).
3. **Domain Gap dengan Pengguna Kamera Nyata**:
   - Dataset Mendeley direkam dalam kondisi pencahayaan dan latar belakang tertentu. Meskipun augmentasi telah diterapkan, uji coba langsung menggunakan webcam browser perlu diverifikasi lebih lanjut.

---

## 12. KESIMPULAN & REKOMENDASI TAHAP BERIKUTNYA

### Kesimpulan
Eksperimen **I1-P1** telah berhasil secara meyakinkan dengan status **`IMPROVED`**:
- Akurasi pengenalan abjad BISINDO meningkat dari **$7,61\%$ menjadi $61,19\%$** ($+53,58\%$).
- Macro F1 meningkat dari **$7,50\%$ menjadi $61,57\%$** ($+54,07\%$).
- Seluruh 26 kelas abjad A–Z berhasil dikenali dengan recall positif.
- Throughput CPU mencapai **$53,4\text{ FPS}$**, siap untuk inferensi real-time.

### Rekomendasi Langkah Selanjutnya:
1. **Eksperimen I1-P2 (Hand-Landmark Guided / Attention Branch)**:
   - Memadukan citra RGB dengan fitur keypoints koordinat 21 titik tangan MediaPipe (atau multi-scale feature fusion) untuk menyelesaikan ambiguitas pasangan mirip seperti D vs P dan M vs N.
2. **Eksperimen I2 (EfficientNet-B0) & I3 (MobileViT)**:
   - Melatih model I2 dan I3 dengan strategi transfer learning yang sama untuk mengevaluasi apakah arsitektur transformer-hybrid mampu mencapai akurasi $> 75\%$.
3. **Ekspor Terkendali ke ONNX Web (Tahap Validasi Deployment)**:
   - Menyiapkan script ekspor ONNX terisolasi di `runs/image_i1_mobilenetv3_p1/fingerspell_p1.onnx` untuk benchmarking kecepatan di browser runtime (ONNX Runtime Web) sebelum memutuskan penggantian model produksi `web/model/fingerspell.onnx`.

