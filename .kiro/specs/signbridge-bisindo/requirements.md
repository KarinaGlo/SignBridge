# Requirements Document

## Introduction

SignBridge ID–PH adalah sistem pengenalan dan penerjemahan bahasa isyarat lintas-negara yang
menghubungkan **BISINDO** (Bahasa Isyarat Indonesia) dengan **FSL** (Filipino Sign Language)
secara real-time melalui browser tanpa instalasi. Sistem mengimplementasikan **4 modalitas input**:
(M) video/keypoint via ST-GCN dan VideoMAE, (I) gambar ejaan jari, (A) audio ASR via Whisper,
dan (B/T) konversi gloss ke kalimat. Ketiga modalitas digabungkan melalui **Jembatan 3 Lapis**
(kamus offline, terjemahan neural NLLB, animasi keypoint) untuk komunikasi BISINDO↔FSL.

Proyek ini berdimensi penelitian skripsi tim dengan kontribusi ilmiah berupa: (1) dataset
**SignBridge-Kelas** ≥3.000 sampel multimodal, (2) arsitektur two-stream gated fusion terbuka,
(3) jembatan BISINDO↔FSL 3 lapis, (4) infrastruktur PWA+WebRTC berbasis browser tanpa instalasi,
dan (5) benchmark terbuka untuk komunitas ASEAN. Proyek mendukung pencapaian SDG 4.5, 4.a,
17.6, dan 17.16/17.17.

---

## Glossary

- **SignBridge**: Nama sistem keseluruhan yang dikembangkan dalam penelitian ini.
- **BISINDO**: Bahasa Isyarat Indonesia — bahasa isyarat komunitas Tuli Indonesia.
- **FSL**: Filipino Sign Language — bahasa isyarat komunitas Tuli Filipina.
- **WLASL**: Word-Level American Sign Language — dataset bahasa isyarat Amerika untuk pretraining.
- **WL-BISINDO**: Word-Level BISINDO — dataset bahasa isyarat Indonesia awal (32 gloss, 5 signer).
- **SignBridge-Kelas**: Dataset multimodal baru yang direkam tim, target ≥3.000 sampel (video + audio + gambar + teks + keypoint).
- **FSL-105**: Filipino Sign Language dataset, 105 kelas, digunakan untuk eksperimen jembatan.
- **Gloss**: Satuan kata/konsep dalam bahasa isyarat yang direpresentasikan oleh satu tanda tangan.
- **Stream_A**: Alur pemrosesan keypoint skeleton (ST-GCN / Pose-Transformer), input `[B, 64, 86, 3]`.
- **Stream_B**: Alur pemrosesan penampilan visual RGB (VideoMAE / I3D), input `[B, 16, 3, 224, 224]`.
- **Gated_Fusion**: Modul penggabungan dua alur: g = σ(W[p̄; r̄]), z = g⊙p̄ + (1-g)⊙r̄.
- **Teacher_Model**: Model besar hasil fine-tuning sebagai sumber distilasi pengetahuan (E5).
- **Student_Model**: Model kecil hasil distilasi dari Teacher_Model, pose-only, ≤10 MB ONNX (E6).
- **MediaPipe_Holistic**: Library Google untuk ekstraksi keypoint tubuh secara real-time.
- **86_Keypoint**: Layout reduksi keypoint: tangan kanan [0:21], tangan kiri [21:42], pose [42:75], wajah selektif [75:86].
- **Normalisasi_Bahu**: x = (x − 0.5·(bahu_L + bahu_R)) / ‖bahu_L − bahu_R‖.
- **T_max**: Panjang sekuens keypoint maksimum yang diterima model, ditetapkan **64** frame (kontrak ONNX).
- **Fonologi_Head**: Kepala prediksi multitask: handshape, lokasi, arah gerak.
- **ONNX_Runtime_Web**: Runtime inferensi WebAssembly/WebGL untuk browser.
- **Keypoint_Graph**: Representasi graf spasial dari 86 node keypoint.
- **ST-GCN**: Spatio-Temporal Graph Convolutional Network.
- **VideoMAE**: Model self-supervised berbasis Masked Autoencoder untuk video.
- **Knowledge_Distillation**: Kompresi model: Teacher melatih Student. α=0.5, T=4 (kontrak).
- **Split_SD**: Signer-Dependent — rasio 60/10/30 (train/val/test).
- **Split_SI**: Signer-Independent — leave-one-signer-out 5-fold.
- **Signer**: Individu yang melakukan tanda tangan dalam video dataset.
- **Augmentasi_Temporal**: Augmentasi pada dimensi waktu (speed perturbation, frame dropping, jitter).
- **Augmentasi_Spasial**: Augmentasi pada dimensi ruang (flip, rotasi, noise, color jitter).
- **Jembatan_3_Lapis**: L1 kamus offline (concepts.csv), L2 terjemahan neural NLLB-200, L3 animasi keypoint.
- **manifest.csv**: File metadata dataset dengan 9 kolom wajib (kontrak tidak boleh berubah).
- **concepts.csv**: Kamus konsep jembatan BISINDO↔FSL (L1 offline).
- **labels.json**: File label 32 gloss BISINDO (kontrak ONNX model video).
- **fingerspell.json**: File label 26 huruf A–Z (kontrak ONNX model gambar).
- **features.py / features.js**: Preprocessing keypoint — harus identik output (parity contract).
- **parity.test.mjs**: Test Node.js untuk verifikasi parity Python↔JavaScript preprocessing.
- **GERKATIN**: Gerakan Kesejahteraan Tunarungu Indonesia.
- **SLB**: Sekolah Luar Biasa.
- **FastAPI**: Framework Python untuk REST API backend inferensi.
- **PWA**: Progressive Web App — web yang dapat diinstal dan berjalan offline.
- **WebRTC**: Web Real-Time Communication — teknologi komunikasi peer-to-peer di browser.
- **PeerJS**: Library JavaScript abstraksi WebRTC untuk kelas multi-perangkat.
- **NLLB**: No Language Left Behind — model terjemahan neural multilingual Meta AI.
- **WER**: Word Error Rate — metrik evaluasi ASR.
- **CER**: Character Error Rate — metrik evaluasi ASR tingkat karakter.
- **RTF**: Real-Time Factor — rasio waktu pemrosesan terhadap durasi audio.
- **BLEU**: Bilingual Evaluation Understudy — metrik evaluasi model teks.
- **chrF**: Character n-gram F-score — metrik evaluasi model teks.
- **Top-1_Accuracy**: Akurasi prediksi teratas.
- **Top-5_Accuracy**: Akurasi di mana label benar termasuk dalam 5 prediksi teratas.
- **Optuna_TPE**: Tree-structured Parzen Estimator — metode hyperparameter tuning.
- **Inference_Latency**: Waktu dari penerimaan input hingga menghasilkan output.
- **Model_Size**: Ukuran file bobot model dalam Megabyte (MB).

---

## Requirements

---

### Requirement 1: Pengumpulan dan Persiapan Dataset SignBridge-Kelas

**User Story:** Sebagai peneliti, saya ingin memiliki dataset SignBridge-Kelas yang bersih
dan terstruktur dalam format multimodal, sehingga semua modalitas (video, audio, gambar, teks,
keypoint) dapat dilatih dan dievaluasi secara adil dan reprodusibel.

#### Acceptance Criteria

1. WHEN skrip perekaman dijalankan, THE SignBridge SHALL merekam video RGB dan audio secara
   serentak menggunakan webcam dan mikrofon dengan resolusi minimal 480p dan frame rate minimal
   25 FPS.
2. THE SignBridge SHALL membangun dataset SignBridge-Kelas dengan target ≥3.000 sampel multimodal,
   setiap sampel berisi: file video (.mp4), file audio (.wav 16kHz mono), gambar ejaan jari
   (.jpg), file keypoint 86 node (.npy), dan teks gloss (string).
3. THE SignBridge SHALL menyimpan metadata setiap sampel dalam `manifest.csv` dengan kolom wajib:
   `id`, `gloss`, `signer_id`, `split`, `video_path`, `audio_path`, `image_path`,
   `keypoint_path`, `text` — kolom ini tidak boleh berubah (kontrak antarmuka).
4. THE SignBridge SHALL memvalidasi integritas dataset dengan memverifikasi bahwa setiap rekaman
   memenuhi: format MP4/AVI/WAV, resolusi ≥ 480p, FPS ≥ 25, durasi 1–10 detik, dan MediaPipe
   dapat mengekstrak 86 keypoint.
5. IF validasi gagal untuk suatu sampel, THEN THE SignBridge SHALL menolak sampel tersebut,
   mempertahankan dataset utama tidak berubah, dan mencatat alasan kegagalan ke
   `data/validation_errors.txt`.
6. THE SignBridge SHALL mendokumentasikan lisensi dataset, sumber, proses pengumpulan, informasi
   persetujuan, potensi bias, dan batasan penggunaan dalam file `DATA_CARD.md`.
7. WHEN registrasi signer baru, THE SignBridge SHALL menghasilkan form persetujuan data dalam
   format PDF dalam Bahasa Indonesia dan memblokir sesi perekaman hingga form ditandatangani.

---

### Requirement 2: Akuisisi Dataset Eksternal

**User Story:** Sebagai peneliti, saya ingin menggunakan dataset eksternal (WLASL, FSL-105,
FLEURS) sebagai sumber pretraining dan evaluasi lintas-bahasa, sehingga model mendapat transfer
knowledge yang kaya.

#### Acceptance Criteria

1. THE SignBridge SHALL mengunduh dataset WLASL yang berisi minimal 21.083 klip video dari 2.006
   gloss untuk pretraining model video.
2. THE SignBridge SHALL mengunduh FSL-105 (Filipino Sign Language, 105 kelas) sebagai dataset
   sekunder untuk eksperimen jembatan (X1–X4).
3. THE SignBridge SHALL mengunduh FLEURS id_id (Indonesian) untuk fine-tune dan evaluasi model
   ASR (A1–A3).
4. IF file video tidak dapat diunduh (HTTP ≠ 200) atau rusak (ukuran 0 byte), THEN THE SignBridge
   SHALL mencatat file yang gagal ke log dan melanjutkan proses; WHEN selesai, THE SignBridge SHALL
   menghentikan proses jika < 80% file berhasil diunduh.
5. WHEN unduhan selesai, THE SignBridge SHALL menghasilkan laporan Markdown berisi: jumlah video
   berhasil diunduh, jumlah gloss/signer, dan jumlah file gagal.

---

### Requirement 3: Ekstraksi dan Normalisasi Keypoint 86 Node

**User Story:** Sebagai peneliti, saya ingin mengekstrak 86 keypoint relevan dari setiap video,
sehingga Stream_A dapat memproses informasi gerakan tangan secara struktural dengan ukuran model
yang efisien.

#### Acceptance Criteria

1. WHEN sebuah video diproses, THE SignBridge SHALL mengekstrak tepat **86 keypoint per frame**
   menggunakan MediaPipe Holistic dengan layout: tangan kanan [0:21], tangan kiri [21:42], pose
   tubuh [42:75], wajah selektif [75:86] — layout ini tidak boleh berubah (kontrak constants.py).
2. WHEN video selesai diproses, THE SignBridge SHALL menyimpan koordinat keypoint dalam format
   NumPy `.npy` dengan dimensi `[T, 86, 3]`, dtype float32.
3. THE SignBridge SHALL menerapkan normalisasi bahu pada setiap frame:
   `x = (x − 0.5·(bahu_L + bahu_R)) / ‖bahu_L − bahu_R‖`; IF jarak bahu = 0, THE SignBridge
   SHALL menggunakan bounding box frame sebelumnya yang valid.
4. IF MediaPipe gagal mendeteksi suatu frame, THEN THE SignBridge SHALL menggunakan interpolasi
   linear dari frame valid dalam jendela ±5 frame; IF tidak ada frame valid dalam jendela,
   THE SignBridge SHALL mengisi dengan nol dan mencatat ke log: indeks frame, kelompok keypoint,
   jumlah keypoint yang di-zero-pad.
5. THE SignBridge SHALL memotong sekuens keypoint ke T_max=**64** frame (uniform sampling atau
   padding dengan nol jika T < 64) — T_max=64 adalah kontrak ONNX yang tidak boleh berubah.
6. WHEN video selesai diproses, THE SignBridge SHALL menyimpan confidence score per keypoint per
   frame dalam format `[T, 86, 1]` float32 ke file `_conf.npy` terpisah.

---

### Requirement 4: Konstruksi Graf Keypoint untuk Stream_A

**User Story:** Sebagai peneliti, saya ingin merepresentasikan 86 keypoint sebagai graf spasial,
sehingga ST-GCN dapat mempelajari hubungan struktural antar sendi tubuh.

#### Acceptance Criteria

1. THE SignBridge SHALL mendefinisikan Keypoint_Graph dengan **86 node** yang sesuai dengan
   layout constants.py dan sisi yang mewakili koneksi anatomis antar sendi.
2. THE SignBridge SHALL mengimplementasikan tiga jenis koneksi: spasial (anatomis), temporal
   (keypoint sama pada frame berurutan), dan simetri (tangan kanan ↔ tangan kiri).
3. THE SignBridge SHALL menyimpan topologi Keypoint_Graph dalam `configs/graph_config.yaml`;
   WHEN dimuat, THE SignBridge SHALL memvalidasi semua node index ∈ [0, 85] dan menolak
   konfigurasi invalid dengan pesan kesalahan spesifik.
4. THE SignBridge SHALL memvalidasi bahwa Keypoint_Graph tidak memiliki isolated node; IF
   ditemukan, THE SignBridge SHALL mengeluarkan `GraphConfigError` dengan indeks node yang
   terisolasi.

---

### Requirement 5: Augmentasi Data

**User Story:** Sebagai peneliti, saya ingin menerapkan augmentasi data komprehensif, sehingga
model dapat menggeneralisasi dengan baik meskipun dataset terbatas.

#### Acceptance Criteria

1. WHILE data latih dimuat, THE SignBridge SHALL menerapkan Augmentasi_Temporal: speed
   perturbation 0.7×–1.3×, random frame dropping ≤ 20%, temporal jitter ±3 frame.
2. WHILE data latih dimuat, THE SignBridge SHALL menerapkan Augmentasi_Spasial pada keypoint:
   horizontal flipping dengan swap tangan kanan/kiri konsisten, rotasi 2D ±15°, Gaussian noise
   std ≤ 0.02.
3. WHILE data latih dimuat, THE SignBridge SHALL menerapkan Augmentasi_Spasial pada frame RGB:
   horizontal flipping sinkron dengan keypoint, random crop skala 0.8–1.0, color jitter
   (brightness/contrast/saturation ±0.2).
4. WHEN horizontal flipping diterapkan, THE SignBridge SHALL menukar keypoint tangan kanan
   (index 0–20) dan tangan kiri (index 21–41) secara konsisten.
5. THE SignBridge SHALL memastikan tidak ada augmentasi acak pada split validasi atau pengujian —
   hanya normalisasi standar yang diperbolehkan.
6. WHEN `augmentation.enabled` = `false`, THE SignBridge SHALL melewati semua augmentasi pada
   split training dan hanya menerapkan normalisasi standar.

---

### Requirement 6: Dataset Sendiri dan Perekaman Tambahan

**User Story:** Sebagai peneliti, saya ingin merekam data SignBridge-Kelas multimodal dari
berbagai signer, sehingga dataset memiliki variasi yang cukup untuk pelatihan semua modalitas.

#### Acceptance Criteria

1. THE SignBridge SHALL menyediakan skrip perekaman (`record_dataset.py`) yang mendukung
   parameter: `--gloss`, `--signer-id`, `--output-dir`, `--fps 30`, `--resolution 640x480`,
   `--audio`, `--image`.
2. WHEN sesi perekaman satu gloss dimulai, THE SignBridge SHALL menampilkan instruksi teks
   dalam Bahasa Indonesia, hitung mundur 3 detik, lalu merekam 2–5 detik.
3. THE SignBridge SHALL merekam video RGB dan audio secara serentak; WHEN selesai, THE SignBridge
   SHALL menyimpan semua file (video, audio, keypoint) dan memperbarui `manifest.csv` secara
   otomatis.
4. THE SignBridge SHALL merekam minimal 3 signer untuk semua gloss target, menghasilkan ≥3.000
   sampel multimodal.
5. WHEN sesi perekaman selesai, THE SignBridge SHALL menyimpan video dalam format MP4 dengan
   struktur direktori SignBridge-Kelas dan memasukkannya ke split training secara otomatis.
6. IF webcam tidak terdeteksi, THEN THE SignBridge SHALL menampilkan pesan kesalahan dalam
   Bahasa Indonesia dan menghentikan proses tanpa membuat file output.

---

### Requirement 7: Implementasi Stream_A — Pemrosesan Keypoint 86 Node

**User Story:** Sebagai peneliti, saya ingin mengimplementasikan Stream_A berbasis ST-GCN atau
Pose-Transformer dengan input 86 keypoint, sehingga sistem dapat mempelajari pola gerakan tangan
secara struktural efisien.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Stream_A menggunakan arsitektur ST-GCN dengan
   minimal 10 blok konvolusi graf spatio-temporal, masing-masing terdiri dari konvolusi graf
   spasial dan konvolusi temporal.
2. WHEN sekuens keypoint diproses, THE SignBridge SHALL menghasilkan vektor fitur **[B, 512]**
   dari input `[B, T_max=64, 86, 3]`.
3. WHEN sekuens keypoint lebih pendek dari 64 frame, THE SignBridge SHALL menerapkan zero-padding
   ke T_max=64 dan membuat boolean mask `[64]` (True=valid, False=padding).
4. THE SignBridge SHALL mendukung konfigurasi melalui YAML: num_blocks (default 10, valid 4–20),
   hidden_dim (default 256, valid 128–512), num_heads (default 8, valid 1–16); IF nilai di luar
   rentang, THE SignBridge SHALL menolak dengan pesan menyebut parameter dan rentang valid.
5. WHEN Pose-Transformer dipilih sebagai alternatif, THE SignBridge SHALL mengimplementasikan
   encoder transformer dengan positional dan temporal embedding, menghasilkan output [B, 512].

---

### Requirement 8: Implementasi Stream_B — Pemrosesan RGB VideoMAE

**User Story:** Sebagai peneliti, saya ingin mengimplementasikan Stream_B berbasis VideoMAE,
sehingga sistem dapat mempelajari pola penampilan visual dari urutan frame RGB.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Stream_B menggunakan VideoMAE yang di-pretrain pada
   dataset berskala besar (Kinetics-400 atau Similar) sebagai inisialisasi bobot.
2. THE SignBridge SHALL mengubah ukuran frame RGB ke 224×224 piksel dan menormalisasi dengan
   mean=[0.485, 0.456, 0.406] dan std=[0.229, 0.224, 0.225].
3. THE SignBridge SHALL menghasilkan vektor fitur **[B, 512]** dari input `[B, 16, 3, 224, 224]`.
4. WHEN video memiliki panjang bervariasi, THE SignBridge SHALL menerapkan uniform temporal
   sampling untuk mengambil T=16 frame; IF video < 16 frame, THE SignBridge SHALL mereplikasi
   frame terakhir hingga 16 frame.
5. THE SignBridge SHALL mendukung pembekuan lapisan awal melalui konfigurasi
   `stream_b.frozen_layers`.

---

### Requirement 9: Implementasi Gated Fusion Module

**User Story:** Sebagai peneliti, saya ingin menggabungkan Stream_A dan Stream_B menggunakan
Gated Fusion, sehingga model dapat memilih secara adaptif kontribusi pose dan RGB.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Gated Fusion Module dengan formula:
   `g = σ(W[p̄; r̄])`, `z = g⊙p̄ + (1-g)⊙r̄` di mana p̄ adalah fitur pose dan r̄ adalah
   fitur RGB.
2. THE Gated_Fusion SHALL menghasilkan output z dengan dimensi **512**, identik dengan dimensi
   input masing-masing stream.
3. Gate g SHALL bernilai ∈ [0, 1] secara element-wise (karena sigmoid), sehingga output z
   adalah convex combination antara p̄ dan r̄.
4. WHEN E5 (Cross-Attention) dipilih sebagai alternatif, THE SignBridge SHALL mengimplementasikan
   bidirectional cross-attention: Stream_A sebagai query ke Stream_B dan sebaliknya, dengan
   multi-head attention ≥8 kepala dan Post-LN.
5. WHILE inferensi berlangsung dengan E5, THE SignBridge SHALL menyimpan attention weights
   `[num_heads, T_query, T_key]` per arah untuk keperluan visualisasi.

---

### Requirement 10: Implementasi Kepala Klasifikasi Gloss

**User Story:** Sebagai peneliti, saya ingin memiliki kepala klasifikasi gloss yang tepat,
sehingga model dapat memprediksi 32 gloss BISINDO dari representasi fusi.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan GlossHead: FC(512) → LayerNorm → GELU → FC(num_classes).
2. THE SignBridge SHALL mendukung num_classes secara dinamis via `model.num_classes` tanpa
   mengubah kode sumber.
3. WHEN model dilatih, THE SignBridge SHALL menggunakan label smoothing cross-entropy dengan
   smoothing ∈ [0.0, 1.0) (default 0.1); IF di luar rentang, THE SignBridge SHALL menolak
   konfigurasi.
4. WHEN satu epoch validasi selesai, THE SignBridge SHALL melaporkan Top-1 dan Top-5 Accuracy;
   IF num_classes ≤ 5, hanya Top-1 yang dilaporkan.

---

### Requirement 11: Implementasi Fonologi_Head untuk Multitask Learning

**User Story:** Sebagai peneliti, saya ingin menambahkan kepala prediksi fitur fonologis sebagai
auxiliary task, sehingga model mendapat sinyal pelatihan tambahan yang meningkatkan akurasi gloss.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Fonologi_Head sebagai tiga sub-kepala independen:
   handshape (10–50 kelas), lokasi (5–20 kelas), arah gerak (4–12 kelas).
2. THE SignBridge SHALL mendefinisikan anotasi fonologis untuk seluruh gloss dalam
   `phonology.csv` (kolom: gloss, handshape, lokasi, arah_gerak).
3. WHEN model dilatih dengan Fonologi_Head, THE SignBridge SHALL menggunakan loss teacher:
   `ℒ = CE_ls(y) + 0.3·(CE_pose + CE_rgb) + 0.5·(1/|F|)·Σ_f CE(fonologi_f)`.
4. WHEN satu epoch validasi selesai, THE SignBridge SHALL melaporkan akurasi ketiga
   sub-kepala secara bersamaan dan terpisah.
5. WHEN `model.use_fonologi_head` = `false`, THE SignBridge SHALL menggunakan
   `ℒ = CE_ls(y)` saja dan tidak melaporkan metrik fonologis.
6. IF file `phonology.csv` tidak ditemukan atau tidak valid saat training, THEN THE SignBridge
   SHALL menghentikan proses dengan pesan menyebut nama file dan error validasi.

---

### Requirement 12: Pretraining pada Dataset WLASL

**User Story:** Sebagai peneliti, saya ingin melakukan pretraining pada WLASL sebelum fine-tuning
ke BISINDO, sehingga model dapat memanfaatkan pengetahuan lintas bahasa isyarat.

#### Acceptance Criteria

1. THE SignBridge SHALL menjalankan pretraining menggunakan file konfigurasi YAML terpisah dari
   konfigurasi fine-tuning BISINDO.
2. WHEN pretraining selesai, THE SignBridge SHALL menyimpan checkpoint terbaik berdasarkan Top-1
   Accuracy pada split validasi WLASL.
3. THE SignBridge SHALL mencapai Top-1 Accuracy ≥ 60% pada WLASL-100; IF tidak tercapai,
   THE SignBridge SHALL mencatat warning di log (proses tidak dihentikan).
4. WHEN `--resume <path>` diberikan, THE SignBridge SHALL melanjutkan dari checkpoint dengan
   memulihkan bobot, state optimizer, epoch terakhir, dan riwayat metrik; IF file tidak ditemukan,
   THE SignBridge SHALL menghentikan proses.
5. THE SignBridge SHALL mencatat kurva loss dan akurasi per epoch ke TensorBoard dan W&B.

---

### Requirement 13: Fine-Tuning dan Eksperimen E0–E7

**User Story:** Sebagai peneliti, saya ingin menjalankan eksperimen E0–E7 secara sistematis,
sehingga kontribusi setiap komponen arsitektur dapat diukur dan dilaporkan.

#### Acceptance Criteria

1. THE SignBridge SHALL menjalankan eksperimen video secara berurutan: E0 (student baseline), E1
   (ST-GCN dari nol), E2 (ST-GCN + pretrain WLASL), E3 (+ Fonologi Head), E4 (fusion concat),
   E5 (fusion cross-attention), E6 (student distilasi E5), E7 (VideoMAE RGB-only).
2. WHEN fine-tuning dimulai (E2 ke atas), THE SignBridge SHALL memuat bobot pretrained dan
   menerapkan learning rate diferensial: lapisan pretrained × 0.1, lapisan baru × base_lr
   (default 1e-4, rentang valid 1e-5–1e-2).
3. WHEN Teacher_Model (E5) selesai, THE SignBridge SHALL mencapai rata-rata Top-1 Accuracy ≥85%
   pada split SD test dan ≥70% pada split SI (5-fold LOSO).
4. THE SignBridge SHALL menghentikan training (early stopping) jika Top-1 pada validasi tidak
   meningkat selama 10 epoch berturut-turut.
5. WHEN epoch validasi selesai, THE SignBridge SHALL menyimpan checkpoint jika Top-1 lebih baik
   dari salah satu dari 3 checkpoint terbaik yang tersimpan (maksimum 3 checkpoint).
6. THE SignBridge SHALL menjalankan hyperparameter tuning dengan **Optuna TPE, 20 trial** untuk
   model video.
7. WHEN fine-tuning selesai, THE SignBridge SHALL menghasilkan laporan Markdown berisi:
   konfigurasi, kurva loss/akurasi per epoch, dan hasil evaluasi akhir per fold.

---

### Requirement 14: Distilasi Pengetahuan ke Student_Model (E6)

**User Story:** Sebagai peneliti, saya ingin mendistilasikan Teacher_Model (E5) ke Student_Model
pose-only yang ringan, sehingga inferensi real-time di browser menjadi layak.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Student_Model berbasis pose-only (keypoint saja,
   tanpa RGB).
2. WHEN distilasi dijalankan, THE SignBridge SHALL menggunakan loss:
   `ℒ = α·CE(y,s) + (1-α)·T²·KL(σ(t/T) ‖ σ(s/T))` dengan **α=0.5, T=4** (kontrak tidak boleh
   berubah).
3. WHEN distilasi selesai, THE Student_Model SHALL mencapai Top-1 Accuracy ≥78% pada split test.
4. THE Student_Model SHALL memiliki ukuran ONNX file ≤ **10 MB** setelah kuantisasi INT8.
5. WHEN distilasi selesai, THE SignBridge SHALL mengekspor Student_Model ke ONNX **opset 17**
   dengan kontrak antarmuka: input float32 `[1, 64, 86, 3]`, output float32 `[1, 32]` —
   kontrak ini tidak boleh berubah.
6. WHEN ekspor ONNX selesai, THE SignBridge SHALL memvalidasi output ONNX vs PyTorch pada 100
   sampel; perbedaan probabilitas maksimum ≤ **1e-4** element-wise.
7. IF Student_Model < 78%, THEN THE SignBridge SHALL mencatat warning: akurasi, threshold, dan
   rekomendasi (turunkan α, naikkan T, atau tambah epoch).

---

### Requirement 15: Model Gambar Ejaan Jari (I1–I3)

**User Story:** Sebagai peneliti, saya ingin melatih tiga model klasifikasi gambar ejaan jari,
sehingga sistem dapat mengenali huruf A–Z dari foto statis secara akurat.

#### Acceptance Criteria

1. THE SignBridge SHALL melatih tiga model: I1 (MobileNetV3-Small), I2 (EfficientNet-B0),
   I3 (MobileViT-XS) pada dataset gambar ejaan jari A–Z (26 kelas).
2. THE SignBridge SHALL menggunakan split 70/15/15 (train/val/test) stratified per huruf, dengan
   preprocessing: resize 224×224, normalisasi ImageNet.
3. THE SignBridge SHALL menjalankan hyperparameter tuning dengan **Optuna TPE, 12 trial** per
   arsitektur.
4. WHEN model terbaik dipilih, THE SignBridge SHALL mengekspor ke `fingerspell.onnx` dengan
   kontrak antarmuka: input float32 `[1, 3, 224, 224]`, output float32 `[1, 26]` — kontrak
   ini tidak boleh berubah.
5. THE SignBridge SHALL menyimpan label dalam `fingerspell.json` berisi tepat 26 entri A–Z
   dalam urutan alphabetis — kontrak ini tidak boleh berubah.
6. THE SignBridge SHALL mencapai Top-1 Accuracy ≥90% pada test set untuk model I2 terbaik.

---

### Requirement 16: Model Audio ASR (A0–A3)

**User Story:** Sebagai peneliti, saya ingin melatih model ASR untuk Bahasa Indonesia, sehingga
sistem dapat mengonversi ucapan pengguna ke teks secara akurat dan cepat.

#### Acceptance Criteria

1. THE SignBridge SHALL mengevaluasi empat konfigurasi ASR: A0 (Whisper-tiny zero-shot), A1
   (Whisper-tiny fine-tune), A2 (Whisper-base fine-tune), A3 (Whisper-base fine-tune +
   augmentasi noise).
2. THE SignBridge SHALL menggunakan FLEURS id_id sebagai dataset fine-tuning dan evaluasi,
   dengan metrik: **WER, CER, RTF**.
3. THE SignBridge SHALL mencapai WER ≤ **15%** pada FLEURS id_id test set untuk model A2.
4. THE SignBridge SHALL mencapai RTF ≤ **0.5×** (pemrosesan lebih cepat dari real-time 2×)
   pada CPU Intel Core i5 gen-8.
5. THE SignBridge SHALL menyediakan endpoint `POST /asr` yang menerima file audio (WAV/MP3/WebM,
   maks 10 MB) dan mengembalikan `{"text": "<transkripsi>"}`.
6. IF file audio > 10 MB, THEN THE FastAPI SHALL mengembalikan HTTP 413 dengan pesan Bahasa
   Indonesia.
7. IF audio bisu atau tidak terdeteksi ucapan, THE SignBridge SHALL mengembalikan `{"text": ""}`.

---

### Requirement 17: Model Teks Gloss→Kalimat (B0, T1–T3)

**User Story:** Sebagai peneliti, saya ingin melatih model yang mengonversi urutan gloss BISINDO
ke kalimat Bahasa Indonesia yang alami, sehingga pengguna tidak perlu memahami notasi gloss.

#### Acceptance Criteria

1. THE SignBridge SHALL mengevaluasi empat model: B0 (aturan heuristik), T1 (GRU + Bahdanau
   Attention), T2 (IndoT5-small fine-tune), T3 (mT5-small fine-tune).
2. THE SignBridge SHALL menggunakan split 80/10/10 dari korpus pseudo-gloss → kalimat Indonesia,
   dengan metrik: **BLEU-4, chrF, WER, exact match**.
3. THE SignBridge SHALL mencapai BLEU-4 ≥ **25** dan chrF ≥ **40** pada test set untuk model T2.
4. THE SignBridge SHALL menyediakan endpoint `POST /sentence` yang menerima
   `{"gloss": "SAYA MAKAN NASI"}` dan mengembalikan `{"text": "Saya sedang makan nasi."}`.
5. WHEN `model.use_fonologi_head` = `false`, THE SignBridge SHALL tetap mendukung endpoint
   `/sentence` menggunakan model T2 (IndoT5-small) sebagai default.

---

### Requirement 18: Jembatan BISINDO–FSL 3 Lapis (MT0–MT3, X1–X4)

**User Story:** Sebagai peneliti, saya ingin membangun jembatan komunikasi BISINDO↔FSL, sehingga
pengguna Indonesia dan Filipina dapat berkomunikasi melalui isyarat masing-masing.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan Jembatan 3 Lapis:
   - **L1**: Lookup kamus offline via `concepts.csv` (tidak butuh jaringan).
   - **L2**: Terjemahan neural via NLLB-200 endpoint `/translate`.
   - **L3**: Animasi keypoint rekaman yang diputar di browser.
2. THE BridgeModule SHALL mencoba L1 terlebih dahulu; IF gloss tidak ada di kamus, THEN mencoba
   L2; IF L2 gagal (jaringan tidak tersedia), THEN mengembalikan error dan mencatat warning.
3. THE SignBridge SHALL menyimpan kamus dalam `concepts.csv` dengan kolom:
   `concept_id, bisindo_gloss, fsl_gloss, bisindo_label_id, fsl_label_id`.
4. THE SignBridge SHALL melatih model terjemahan FSL-side: X1 (init WLASL), X2 (init BISINDO),
   X3 (dari nol), X4 (student distilasi).
5. THE SignBridge SHALL mengevaluasi tiga model terjemahan neural: MT1 (M2M100-418M), MT2
   (NLLB-600M), MT3 (NLLB-1.3B) dengan metrik BLEU lintas-bahasa isyarat.
6. THE SignBridge SHALL menyediakan endpoint `POST /translate` yang menerima
   `{"text": "...", "src": "BISINDO", "tgt": "FSL"}` dan mengembalikan
   `{"translation": "...", "layer_used": "L1"}`.
7. THE Jembatan SHALL mencakup ≥ **95%** gloss target via L1 atau L2 kombinasi.

---

### Requirement 19: Parser dan Serializer Format Data

**User Story:** Sebagai peneliti, saya ingin memiliki parser dan serializer yang andal untuk
semua format data, sehingga data dapat dimuat, diproses, dan disimpan tanpa kehilangan informasi.

#### Acceptance Criteria

1. WHEN file keypoint `.npy` dimuat, THE SignBridge SHALL memvalidasi: dimensi `[T, 86, 3]`,
   T ∈ [1, 10.000], dtype float32; IF validasi gagal, THE SignBridge SHALL raise
   `SchemaValidationError` dengan nama file dan constraint yang dilanggar.
2. WHEN `manifest.csv` dimuat, THE SignBridge SHALL memvalidasi bahwa setiap baris memiliki
   semua 9 kolom wajib dan split ∈ {"train", "val", "test"}; IF validasi gagal, THE SignBridge
   SHALL raise `SchemaValidationError` dengan nomor baris dan kolom yang hilang.
3. FOR ALL SampleMetadata yang valid, serializing ke manifest.csv lalu deserializing SHALL
   menghasilkan object dengan nilai identik untuk semua 9 kolom wajib.
4. THE SignBridge SHALL mendokumentasikan skema semua format data dalam `DATA_FORMAT.md`:
   dimensi array, tipe data, rentang nilai, dan semua kolom wajib.
5. THE SignBridge SHALL memastikan preprocessing `features.py` (Python) dan `features.js`
   (JavaScript) menghasilkan output identik element-wise dalam toleransi 1e-5, diverifikasi
   oleh `parity.test.mjs` yang berjalan otomatis dalam CI.

---

### Requirement 20: Web Application — PWA + WebRTC

**User Story:** Sebagai pengguna akhir (siswa/guru), saya ingin menggunakan sistem melalui
browser tanpa instalasi dan dapat berkomunikasi dengan pengguna lain secara real-time.

#### Acceptance Criteria

1. THE SignBridge SHALL menyediakan Web Application berbasis HTML/CSS/JS murni yang berjalan
   tanpa plugin atau instalasi tambahan di Chrome 90+, Firefox 88+, Edge 90+.
2. THE Web Application SHALL mengimplementasikan enam fitur utama: (a) Papan Isyarat (input gloss
   → kalimat), (b) Ejaan Jari (kamera → huruf real-time), (c) Takarir Suara (mikrofon → teks),
   (d) Jembatan ID↔PH (terjemah BISINDO ↔ FSL), (e) Kelas Multi-Perangkat (WebRTC+PeerJS ≥2
   perangkat), (f) Rekam Data (multimodal: video+audio+gambar+teks).
3. WHEN pengguna mengakses antarmuka, THE SignBridge SHALL meminta izin kamera via
   `getUserMedia`; IF ditolak, THE SignBridge SHALL menampilkan pesan Bahasa Indonesia dan
   tautan panduan.
4. WHEN Student_Model dimuat, THE SignBridge SHALL memproses setiap frame webcam dengan
   Inference_Latency ≤ **100 ms/frame** pada Core i5 gen-8 atau Passmark ≥ 6.000.
5. THE Web Application SHALL diimplementasikan sebagai **PWA** dengan Service Worker untuk
   mendukung mode offline terbatas (kamus L1 selalu tersedia offline).
6. THE Web Application SHALL di-hosting di **GitHub Pages** (development, port 8080) dan
   **Azure Static Web Apps** (produksi).
7. IF kepercayaan prediksi < 0.5, THEN THE SignBridge SHALL menampilkan indikator "tidak yakin"
   dan tidak menampilkan label gloss sebagai hasil final.
8. IF browser tidak mendukung ONNX Runtime Web, THEN THE SignBridge SHALL menampilkan pesan
   dengan browser yang didukung dan menawarkan mode fallback unggah video.

---

### Requirement 21: FastAPI Server dan Deployment Docker

**User Story:** Sebagai peneliti, saya ingin men-deploy sistem dengan Docker dan menyediakan
semua endpoint API yang diperlukan, sehingga seluruh pipeline dapat berjalan dengan satu perintah.

#### Acceptance Criteria

1. THE SignBridge SHALL mengimplementasikan FastAPI backend dengan endpoint:
   - `POST /predict` — keypoint `[1,64,86,3]` float32 binary → `{gloss, confidence, top5, inference_time_ms}`
   - `POST /asr` — file audio → `{text}`
   - `POST /sentence` — `{gloss}` → `{text}`
   - `POST /translate` — `{text, src, tgt}` → `{translation, layer_used}`
   - `GET /ws/{kode}` — WebSocket relay untuk kelas multi-perangkat
2. THE FastAPI SHALL memproses `POST /predict` dan mengembalikan respons ≤ **2 detik** untuk
   keypoint satu sampel.
3. THE FastAPI SHALL mendokumentasikan semua endpoint via OpenAPI 3.0 di `/docs`.
4. IF file yang dikirim bukan format yang didukung atau > batas ukuran, THEN THE FastAPI SHALL
   mengembalikan HTTP 400 (format/ukuran video) atau HTTP 413 (audio > 10 MB) dengan pesan
   Bahasa Indonesia.
5. THE SignBridge SHALL mengimplementasikan rate limiting 60 req/menit/IP; IF batas terlampaui,
   THE FastAPI SHALL mengembalikan HTTP 429 dengan header `Retry-After`.
6. THE SignBridge SHALL menyediakan `docker-compose.yml` yang menjalankan: service `web` (port
   8080) dan service `api` (port 7860) dengan perintah `docker compose up`.
7. THE SignBridge SHALL mendukung deployment ke **Azure**: Static Web Apps (web) dan Container
   Apps (API) dengan CI/CD via GitHub Actions.

---

### Requirement 22: Evaluasi dan Benchmark Terbuka

**User Story:** Sebagai peneliti, saya ingin menerbitkan hasil evaluasi yang transparan,
sehingga peneliti lain dapat membandingkan metode mereka secara adil.

#### Acceptance Criteria

1. THE SignBridge SHALL mengevaluasi model video menggunakan dua protokol: Split SD (60/10/30,
   Top-1 dan Top-5) dan Split SI (5-fold LOSO, Top-1 mean ± std).
2. THE SignBridge SHALL membandingkan performa dengan minimal tiga baseline: (a) CNN+LSTM
   MediaPipe, (b) I3D tunggal tanpa fusion, (c) ST-GCN tunggal tanpa fusion.
3. THE SignBridge SHALL menjalankan ablasi: Stream_A saja, Stream_B saja, fusion concat vs
   gated, dan model lengkap E5 + Fonologi_Head.
4. THE SignBridge SHALL menyimpan semua skrip evaluasi dan konfigurasi sehingga dapat
   direproduksi dengan: `python evaluate.py --config configs/eval_bisindo.yaml`.
5. THE SignBridge SHALL merilis model ONNX terbaik, kode sumber, dan dataset di bawah lisensi
   CC BY 4.0 tanpa gating akses.
6. THE SignBridge SHALL menghasilkan tabel Markdown: Metode, Top-1 (%), Top-5 (%), WER (%),
   BLEU-4, Ukuran Model (MB), Latensi (ms) — siap disalin ke paper penelitian.

---

### Requirement 23: Keterbacaan dan Reprodusibilitas Kode

**User Story:** Sebagai peneliti dan pengembang lain, saya ingin kode yang terdokumentasi
dengan baik, sehingga penelitian ini dapat direproduksi dan dikembangkan lebih lanjut.

#### Acceptance Criteria

1. THE SignBridge SHALL menyediakan `README.md` dalam Bahasa Indonesia dan Bahasa Inggris
   dengan seksi: instalasi, persiapan data, training, evaluasi, deployment, dalam ≤15 langkah
   per seksi.
2. THE SignBridge SHALL menyertakan `requirements.txt` (Python, versi terpatok) dan
   `package.json` (JavaScript, versi terpatok).
3. THE SignBridge SHALL menyediakan `setup.sh` / `setup.bat` yang menginstal semua dependensi
   dan mencetak "Setup complete. Run `python smoke_test.py` to verify." dengan exit code 0.
4. THE SignBridge SHALL menyediakan parameter `seed` terpusat (default: 42) yang diterapkan
   pada semua operasi stokastik (inisialisasi bobot, shuffle, augmentasi).
5. WHEN training dimulai, THE SignBridge SHALL menyimpan konfigurasi eksperimen ke
   `experiment_config.yaml` di direktori eksperimen sebelum training dimulai.

---

### Requirement 24: Kontribusi Dataset dan Kemitraan Komunitas

**User Story:** Sebagai peneliti yang peduli SDG, saya ingin berkontribusi pada dataset terbuka
dan menjalin kemitraan dengan GERKATIN/SLB, sehingga penelitian ini memberi dampak nyata.

#### Acceptance Criteria

1. THE SignBridge SHALL merilis dataset SignBridge-Kelas di Kaggle dan Hugging Face Datasets
   di bawah lisensi CC BY 4.0 tanpa gating akses.
2. THE SignBridge SHALL menyertakan `DATA_CARD.md` dengan: sumber data, proses pengumpulan,
   informasi persetujuan, potensi bias, dan batasan penggunaan.
3. THE SignBridge SHALL mendokumentasikan kemitraan dengan GERKATIN atau SLB dalam laporan
   penelitian, termasuk validasi gloss oleh minimal 2 anggota komunitas Tuli.
4. THE SignBridge SHALL menyediakan `CONTRIBUTING_DATA.md` dalam Bahasa Indonesia yang
   menjelaskan cara kontributor pihak ketiga dapat menyumbangkan video baru.
5. WHEN dataset baru diterima dari kontributor, THE SignBridge SHALL memvalidasi: format
   MP4/AVI/WAV, resolusi ≥ 480p, FPS ≥ 25, durasi 1–10 detik, MediaPipe dapat mengekstrak
   86 keypoint.
6. IF validasi gagal, THEN THE SignBridge SHALL menolak penggabungan, mempertahankan dataset
   utama tidak berubah, dan mengirim laporan kegagalan dengan kriteria spesifik yang tidak
   terpenuhi.
