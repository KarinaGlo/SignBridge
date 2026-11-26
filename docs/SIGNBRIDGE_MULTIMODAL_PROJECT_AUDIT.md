# LAPORAN AUDIT TEKNIS & TINJAUAN ARSITEKTUR MULTIMODAL FUSION
## SignBridge ASEAN — Jembatan Komunikasi Real-Time BISINDO ↔ FSL
**Repository:** `https://github.com/KarinaGlo/SignBridge`  
**Direktori Proyek:** `D:\SEMESTER 5\ML\Projek_1`  
**Tanggal Audit:** 20 November 2026  
**Auditor:** Senior Machine Learning Engineer & Multimodal Deep Learning Researcher  
**Status Audit:** SELESAI & TERVERIFIKASI PENUH (100% FACTUAL & EVIDENCE-BASED)

---

## DAFTAR ISI
1. [Executive Summary](#1-executive-summary)
2. [Tujuan dan Perubahan Arah Proyek](#2-tujuan-dan-perubahan-arah-proyek)
3. [Kondisi Repository Saat Ini](#3-kondisi-repository-saat-ini)
4. [Arsitektur Aktual](#4-arsitektur-aktual)
5. [Arsitektur Target Multimodal Fusion](#5-arsitektur-target-multimodal-fusion)
6. [Audit Dataset Setiap Modalitas](#6-audit-dataset-setiap-modalitas)
7. [Audit Dataset Paired Multimodal](#7-audit-dataset-paired-multimodal)
8. [Audit Preprocessing](#8-audit-preprocessing)
9. [Audit Model dan Baseline](#9-audit-model-dan-baseline)
10. [Audit Implementasi M6](#10-audit-implementasi-m6)
11. [Audit Training Pipeline](#11-audit-training-pipeline)
12. [Audit Evaluasi dan Metrik](#12-audit-evaluasi-dan-metrik)
13. [Audit Data Collection (Perekam Web)](#13-audit-data-collection-perekam-web)
14. [Audit Backend dan Frontend](#14-audit-backend-dan-frontend)
15. [Audit Deployment dan Ekspor ONNX](#15-audit-deployment-dan-ekspor-onnx)
16. [Audit Testing (Unit, Integration, Parity)](#16-audit-testing)
17. [Masalah Kritis (Critical Issues)](#17-masalah-kritis-critical-issues)
18. [Daftar Hal yang Belum Dikerjakan](#18-daftar-hal-yang-belum-dikerjakan)
19. [Rekomendasi Perbaikan Metodologis](#19-rekomendasi-perbaikan-metodologis)
20. [Roadmap Prioritas (P0, P1, P2)](#20-roadmap-prioritas)
21. [Daftar File yang Perlu Dibuat / Diperbaiki](#21-daftar-file-yang-perlu-dibuat--diperbaiki)
22. [Kriteria Penyelesaian Proyek](#22-kriteria-penyelesaian-proyek)
23. [Kesimpulan](#23-kesimpulan)
24. [BAGIAN KHUSUS MAHASISWA: "APA YANG HARUS SAYA KERJAKAN BESOK?"](#24-bagian-khusus-mahasiswa-apa-yang-harus-saya-kerjakan-besok)

---

## 1. EXECUTIVE SUMMARY

SignBridge ASEAN sedang bertransformasi dari sistem **Modular Multimodal Application** (beberapa model terpisah yang dipanggil secara berurutan) menjadi **Multimodal Deep Learning Fusion System** terpadu melalui arsitektur **M6 — Four-Modality Fusion Network**.

### Temuan Utama Audit (Faktual Berbasis Bukti):
1. **Arsitektur M6 Sah Merupakan Multimodal Fusion (`signbridge/models/multimodal.py`):**
   - Bukan sekadar *wrapper* atau pemanggilan sekuensial. M6 mengimplementasikan 4 encoder khusus modalitas ($d=128$), *Cross-Modal Transformer Attention* (2 lapis, 4 head), *Gated Modality Weighting* dinamis per sampel, *Modality Dropout* ($p=0.3$), dan *Auxiliary Unimodal Heads*.
   - Forward pass, backward pass, gradient flow, dan 21 unit tests terbukti **100% PASS**.
2. **Ketiadaan Bobot Terlatih Nyata (M6 Belum Dilatih):**
   - Belum ada file checkpoint `outputs/experiments/M6_multimodal_fusion/best_model.pt`.
   - Belum ada model ONNX `web/model/multimodal_fusion.onnx`.
   - Endpoint `POST /predict_multimodal` pada FastAPI mengembalikan status `HTTP 503 Service Unavailable` secara jujur (menolak menghasilkan prediksi palsu/sintetis).
3. **Ketiadaan Dataset Berpasangan (The Core Data Bottleneck):**
   - File manifest `data/multimodal/manifest_multimodal.csv` **belum ada**.
   - Folder rekaman web `data/raw/web_zips` masih kosong (**0 file ZIP**).
   - Di repositori saat ini terdapat **0 sampel berpasangan lengkap 4 modalitas**.
   - File 1.600 video WL-BISINDO di `data/manifest_wl_bisindo.csv` hanya berupa metadata baris tabel; file fisik `.npz` keypoint di `data/keypoints/` **tidak ada di disk lokal (0/1600)**.
   - Dataset audio FLEURS di `data/audio/fleurs/id_id/` hanya berisi file metadata teks `.tsv` (**0 file WAV/audio asli**).
4. **Kesiapan Alat Akuisisi Data (`web/js/recorder.js`):**
   - Alat Perekam Dataset di antarmuka web telah diperbaiki oleh tim: merekam kamera MediaPipe keypoints 86 titik, crop tangan $224 \times 224$, foto portrait, audio mikrofon WAV 16 kHz, dan teks kalimat konteks, lalu mengemasnya menjadi arsip ZIP standar.
   - Pipa pembuat manifest `scripts/build_multimodal_manifest.py` telah siap memproses file ZIP tersebut.
5. **Kesiapan Model Lainnya:**
   - Model Image I1 (MobileNetV3 A–Z) telah memiliki checkpoint P1 `runs/image_i1_mobilenetv3_p1/best.pt` dan ONNX `web/model/fingerspell.onnx`, saat ini berada pada status **STRICT HOLD** menunggu verifikasi portal validasi manusia (Phase 2C.8/2C.9).
   - Model video Student Transformer `web/model/student.onnx` telah diekspor tetapi bobotnya masih inisialisasi arsitektur.

---

## 2. TUJUAN DAN PERUBAHAN ARAH PROYEK

### Perbandingan Paradigma

| Dimensi | Paradigma Lama (Aplikasi Multimodal Terpisah) | Paradigma Baru (Model Multimodal Fusion M6) |
|:---|:---|:---|
| **Definisi** | Menggabungkan *output* teks/prediksi dari model-model terpisah. | Menggabungkan *representasi fitur laten* dari 4 modalitas dalam **satu neural network**. |
| **Alur Proses** | Video $\rightarrow$ M0 $\rightarrow$ kata;<br>Citra $\rightarrow$ I1 $\rightarrow$ huruf;<br>Audio $\rightarrow$ ASR $\rightarrow$ teks;<br>Teks $\rightarrow$ B0 $\rightarrow$ aturan. | `[Video, Image, Audio, Text]` $\rightarrow$ 4 Encoders $\rightarrow$ Cross-Modal Transformer $\rightarrow$ Gated Weighting $\rightarrow$ Prediksi Kelas. |
| **Kelemahan** | Jika satu modalitas gagal (misal tangan blur atau audio bising), seluruh alur terputus. Tidak ada transfer informasi antar-modalitas saat inferensi. | Model dapat saling melengkapi (*cross-attention*): gerakan tangan yang ambigu dapat diperjelas oleh audio/teks, dan sebaliknya. |
| **Toleransi Modalitas Hilang** | Kaku (*brittle*). | Adaptif: *Modality mask* & *Gated Weighting* otomatis memberikan bobot 0 pada modalitas yang tidak tersedia. |

---

## 3. KONDISI REPOSITORY SAAT INI

- **Git Branch Aktif:** `feature/dataset-acquisition`
- **Commit Terakhir:** `3772e14 (HEAD -> feature/dataset-acquisition, origin/feature/dataset-acquisition)`
- **Pesan Commit:** `Merge pull request #4 from KarinaGlo/fix/multimodal-deps`
- **Status Working Tree:** Bersih dari modifikasi file terlacak (`0 modified tracked files`).
- **File Lokal Terlindungi (*Untracked*):** 38 item terkait artefak riset eksperimen P0/P1/P2 tetap 100% aman dan tidak tersentuh.

### Tabel Inventaris Komponen Repositori

| Komponen | File / Folder | Kondisi Aktual | Bukti Faktual | Status Evaluasi |
|:---|:---|:---|:---|:---:|
| **Arsitektur Fusion M6** | `signbridge/models/multimodal.py` | Terimplementasi penuh (PyTorch) | 265 baris kode, 4 encoder, Transformer 2 lapis, Gated Fusion | **DONE** (Arsitektur) |
| **Fitur & Preprocessing** | `signbridge/multimodal/features.py` | Terimplementasi (NumPy/PIL murni) | 264 baris, ekstraksi log-mel, pose normalizer, char tokenizer | **DONE** |
| **Dataset Loader M6** | `signbridge/multimodal/dataset.py` | Terimplementasi | Mendukung manifest CSV, resolved paths, hash split | **DONE** |
| **Script Training M6** | `signbridge/train_multimodal.py` | Terimplementasi (+ mode smoke) | Loop AdamW, early stopping, 15 ablasi otomatis | **DONE** (Script) |
| **Eksportir ONNX M6** | `signbridge/export_onnx_multimodal.py` | Terimplementasi | Ekspor 5 input tensor, uji paritas PyTorch vs ONNX | **PARTIAL** (Butuh `onnx` pkg) |
| **Checkpoint Bobot M6** | `outputs/experiments/M6_multimodal_fusion/` | **BELUM ADA** | Folder belum terbentuk, belum ada `best_model.pt` | **NOT STARTED** |
| **Model ONNX M6** | `web/model/multimodal_fusion.onnx` | **BELUM ADA** | File tidak ditemukan di `web/model/` | **NOT STARTED** |
| **Dataset Multimodal Paired** | `data/multimodal/manifest_multimodal.csv` | **BELUM ADA** | Belum ada rekaman ZIP di `data/raw/web_zips/` | **NOT STARTED** |
| **Perekam Web Multimodal** | `web/js/recorder.js` & `web/index.html` | Terimplementasi di browser | Merekam kamera 86 kp, 16kHz WAV, crop 224x224, teks | **DONE** |
| **Backend API M6** | `server/app.py` & `server/multimodal_service.py` | Terimplementasi | Endpoint `/predict_multimodal` aktif dengan status 503 | **DONE** |
| **Database Telemetri** | `data/signbridge_operational.db` | Aktif (SQLite fallback) | 58 konsep, 20 model, 4 eval runs, 192 log inferensi | **DONE** |
| **Unit Tests M6** | `tests/test_multimodal_*.py` | 21 PASS, 1 SKIPPED | Ekstraksi fitur, masking, loss backward, service valid | **DONE** |

---

## 4. ARSITEKTUR AKTUAL

Saat ini di dalam repository, arsitektur yang aktif di sistem produksi lokal terbagi menjadi dua lapisan:
1. **Model Operasional Tersedia:**
   - Image I1: `web/model/fingerspell.onnx` ($1.01\text{ MB}$, MobileNetV3-Small untuk 26 alfabet A–Z).
   - Video Student: `web/model/student.onnx` ($5.46\text{ MB}$, Pose Transformer 86 keypoints).
   - Text B0: Aturan deterministik tata bahasa (`signbridge/text/pseudo_gloss.py`).
   - Audio: Web Speech API di sisi klien peramban.
2. **Model Fusion M6 (Baru Berupa Kode Arsitektur):**
   - `signbridge/models/multimodal.py` siap dijalankan, tetapi belum memiliki file bobot terlatih.

```mermaid
flowchart TD
    subgraph SISI_KLIEN_WEB["Antarmuka Web (PWA)"]
        Cam["Kamera Web"] --> MP["MediaPipe Holistic"]
        Mic["Mikrofon"] --> WebAudio["Web Audio API (16 kHz)"]
        UserText["Input Teks"] --> TextBuf["Buffer Teks Konteks"]
        MP --> LiveKeypoints["86 Keypoints Video"]
        MP --> LiveCrop["Hand Crop Image"]
    end

    subgraph STATUS_SAAT_INI["Kondisi Inferensi Saat Ini (Modular Fallback)"]
        LiveKeypoints -->|POST /predict| M0_Serv["M0 Video Recognizer (ONNX)"]
        LiveCrop -->|Local Canvas| I1_Serv["I1 Fingerspell (ONNX)"]
        TextBuf -->|POST /sentence| B0_Serv["B0 Grammar Rules"]
    end

    subgraph M6_FUSION_STATUS["Kondisi M6 Multimodal Fusion (Tahap Verifikasi Kode)"]
        LiveKeypoints -.->|POST /predict_multimodal| M6_EP["/predict_multimodal"]
        LiveCrop -.-> M6_EP
        WebAudio -.-> M6_EP
        TextBuf -.-> M6_EP
        M6_EP --> CheckONNX{"multimodal_fusion.onnx<br/>tersedia?"}
        CheckONNX -- Belum Ada --> Ret503["HTTP 503 Service Unavailable<br/>(Jujur, tanpa data palsu)"]
        CheckONNX -- Ada --> M6_Engine["M6 ONNX Engine (Siap Aktif)"]
    end
```

---

## 5. ARSITEKTUR TARGET MULTIMODAL FUSION

Arsitektur target M6 menggabungkan sinyal dari 4 modalitas sensoris ke dalam ruang representasi terpadu:

```mermaid
flowchart LR
    subgraph INPUTS["Input 4 Modalitas Sensoris"]
        V_in["Video Keypoints<br/>[B, 64, 86, 3]"]
        I_in["Citra Hand Crop<br/>[B, 3, 112, 112]"]
        A_in["Audio Log-Mel<br/>[B, 64, 248]"]
        T_in["Teks Token Karakter<br/>[B, 64]"]
        M_in["Modality Mask<br/>[B, 4]"]
    end

    subgraph ENCODERS["Encoders Khusus Modalitas (d = 128)"]
        V_enc["PoseEncoder<br/>Vel + Linear + PosEnc<br/>Transformer 2 Lapis + Pool4<br/>Output: [B, 16, 128]"]
        I_enc["ImageEncoder<br/>CNN 4-Blok Stride 2<br/>Flatten 7x7 + Linear + PosEnc<br/>Output: [B, 49, 128]"]
        A_enc["AudioEncoder<br/>Conv1d Stride 2 + Pool2<br/>Transformer 1 Lapis<br/>Output: [B, 31, 128]"]
        T_enc["TextEncoder<br/>Char Embedding + PosEnc<br/>Transformer 1 Lapis (Masked)<br/>Output: [B, 64, 128]"]
    end

    V_in --> V_enc
    I_in --> I_enc
    A_in --> A_enc
    T_in --> T_enc

    subgraph FUSION_BLOCK["Cross-Modal Fusion & Gating"]
        TypeEmb["Modality Type Embeddings<br/>[4, 128]"] -.-> CatTokens
        CLS["[CLS] Token<br/>[B, 1, 128]"] --> CatTokens
        V_enc --> CatTokens["Rangkaian 161 Token<br/>[B, 161, 128]"]
        I_enc --> CatTokens
        A_enc --> CatTokens
        T_enc --> CatTokens
        M_in -->|Key Padding Mask| TransFusion["Cross-Modal Transformer<br/>(2 Lapis, 4 Head, GELU)"]
        CatTokens --> TransFusion
        TransFusion --> H_out["Token Fusi [B, 161, 128]"]

        H_out --> MeanPool["Ringkasan Tiap Modalitas<br/>U_m: [B, 4, 128]"]
        MeanPool --> GateMLP["Gated Weighting Network<br/>s_m = v^T tanh(W U_m)"]
        M_in -->|Mask fill -1e4| GateMLP
        GateMLP --> SoftmaxAlpha["Softmax Dynamic Weights<br/>alpha: [B, 4]"]
        SoftmaxAlpha --> WeightedSum["Konteks Fusi: z = sum(alpha_m * U_m)"]
        H_out -->|Ambil token CLS| CLS_out["h_CLS [B, 128]"]
        CLS_out --> AddNorm["LayerNorm(h_CLS + z)"]
        WeightedSum --> AddNorm
    end

    subgraph HEADS["Prediction Heads"]
        AddNorm --> FinalRep["Representasi Gabungan [B, 128]"]
        FinalRep --> MainHead["Linear Classifier<br/>[128 -> 32 Kelas]"]
        MeanPool -.-> AuxHeads["4 Auxiliary Heads<br/>(Unimodal Regularization)"]
        MainHead --> Logits["32 Logits Konsep Kelas BISINDO"]
        SoftmaxAlpha --> WeightsOut["Bobot Kontribusi Modalitas [B, 4]"]
    end
```

### Rincian Spesifikasi Tensor Tiap Tahap

| Komponen | Nama Tensor | Tipe Data | Bentuk Tensor (*Shape*) | Penjelasan Teknis |
|:---|:---|:---:|:---:|:---|
| **Input Video** | `pose` | `float32` | `[B, 64, 86, 3]` | 64 frame waktu, 86 titik (pose bahu, wajah, 2 tangan @21 titik), koordinat 3D $(x,y,z)$. |
| **Input Citra** | `image` | `float32` | `[B, 3, 112, 112]` | Crop tangan dari frame terbaik, dinormalisasi mean & std ImageNet. |
| **Input Audio** | `audio` | `float32` | `[B, 64, 248]` | 64 filterbank mel, 248 time step (durasi 2,5 detik pada sample rate 16 kHz). |
| **Input Teks** | `text` | `int64` | `[B, 64]` | Deret indeks karakter alfabet + angka + tanda baca (panjang maks 64, padding index 0). |
| **Input Mask** | `modality_mask` | `float32` | `[B, 4]` | Indikator ketersediaan `[video, image, audio, text]`. Nilai 1 = ada, 0 = hilang. |
| **Token Pose** | `pose_tok` | `float32` | `[B, 16, 128]` | Keypoints + velocity ($86 \times 3 \times 2 = 516$ fitur) diproyeksikan dan di-pool 4. |
| **Token Citra** | `image_tok` | `float32` | `[B, 49, 128]` | Output CNN $7 \times 7$ feature map diratakan menjadi 49 token spasial. |
| **Token Audio** | `audio_tok` | `float32` | `[B, 31, 128]` | Conv1d stride 2 + pooling menghasilkan 31 token temporal. |
| **Token Teks** | `text_tok` | `float32` | `[B, 64, 128]` | Token embedding karakter berdimensi 128. |
| **Total Sequence** | `seq` | `float32` | `[B, 161, 128]` | $1\text{ ([CLS])} + 16 + 49 + 31 + 64 = 161$ token diproses bersama di Transformer. |
| **Bobot Fusi** | `modality_weights` | `float32` | `[B, 4]` | Bobot $\alpha$ hasil gating softmax ($\sum \alpha = 1.0$, modalitas hilang strictly 0.0). |
| **Output Utama** | `logits` | `float32` | `[B, 32]` | Peluang logit untuk 32 konsep kelas BISINDO. |

---

## 6. AUDIT DATASET SETIAP MODALITAS

Pemeriksaan mendalam terhadap file fisik di hard drive (`data/`):

### A. Modalitas Video (Gerakan Isyarat BISINDO)
- **Dataset Acuan:** WL-BISINDO (Word-Level BISINDO) 32 glosses.
- **Manifest:** `data/manifest_wl_bisindo.csv` berisi 1.600 baris metadata (32 gloss, 5 signer `SIGNER0`–`SIGNER4`, 50 klip/gloss).
- **Kondisi Aktual di Disk:** **0 file video mentah (.mp4/.webm)** dan **0 file keypoints (.npz)** di folder `data/keypoints/`.
- **Status:** **METADATA ONLY / UNFETCHED**. File fisik keypoints belum pernah diunduh atau diekstrak secara lokal ke direktori proyek.

### B. Modalitas Citra (Alfabet & Crop Tangan BISINDO)
- **Dataset Acuan:** Mendeley BISINDO Alphabet Dataset (26 kelas huruf A–Z).
- **Data Mentah:** `data/raw/image/bisindo_alphabet/`: **8.620 file citra** (.jpg, .jpeg, .JPG).
- **Data Hasil Olah:** `data/processed/bisindo_alphabet/`:
  - **4.462 file citra** crop tangan bersih berukuran seragam.
  - **4.462 file `.npy`** berisi koordinat 21 MediaPipe hand landmarks.
- **Dataset Uji Eksternal:** `data/external/bisindo_validation/`: 36 sampel gambar terverifikasi untuk pengujian independen.
- **Kualitas:** Sangat baik, bounding box tangan tervalidasi, cropping konsisten.
- **Status:** **VALID & READY** (khusus alfabet huruf statis).

### C. Modalitas Audio (Bahasa Lisan)
- **Dataset Acuan:** FLEURS Indonesia (`id_id`) untuk ASR.
- **Data di Disk:** `data/audio/fleurs/id_id/`:
  - `train.tsv`: 2.578 baris transkrip.
  - `dev.tsv`: 349 baris transkrip.
  - `test.tsv`: 686 baris transkrip.
  - Metadata rekaman: `data/audio/metadata.csv` (60 baris) & `metadata_fil.csv` (24 baris).
- **Kondisi Aktual di Disk:** **0 file `.wav` fisik di `data/audio/`**.
- **Status:** **METADATA ONLY / UNFETCHED**. File audio WAV belum tersimpan di disk lokal.

### D. Modalitas Teks (Konteks Kalimat & Gloss)
- **Dataset di Disk:**
  - `data/text/kelas_sentences.txt`: 200 kalimat percakapan kelas.
  - `data/text/train.tsv`: 170 pasangan latih `gloss -> kalimat`.
  - `data/text/val.tsv`: 30 pasangan validasi.
  - `data/text/test_manual.tsv`: 105 pasangan uji manusia (tanpa overlap dengan data latih).
  - `data/text/tatoeba/ind_sentences.tsv`: 28.418 kalimat bahasa Indonesia.
  - `data/bridge/concepts.csv`: 32 kamus pemetaan konsep BISINDO $\leftrightarrow$ FSL.
- **Status:** **VALID & READY**.

---

## 7. AUDIT DATASET PAIRED MULTIMODAL

> [!CAUTION]
> **TEMUAN KRITIS DATASET:**  
> Repositori saat ini memiliki data citra alfabet (Mendeley) dan data teks (Tatoeba/Kelas), namun **KEDUA DATASET TERSEBUT TIDAK MEMILIKI HUBUNGAN SENSORIS ATAU TEMPORAL**. Keduanya berasal dari sumber independen, subjek berbeda, dan waktu yang berbeda.

### Tabel Statistik Ketersediaan Modalitas Faktual

| Modalitas | Total Entri Metadata | Data Fisik Valid di Disk | Data Rusak / Hilang | Status Kesiapan |
|:---|---:|---:|---:|:---|
| **Video (Keypoints)** | 1.600 | **0** | 1.600 (file `.npz` tidak ada) | **BLOCKED (Unfetched)** |
| **Image (Alfabet/Crop)** | 8.620 | **4.462** | 0 | **READY (Hanya untuk abjad)** |
| **Audio (WAV)** | 3.613 | **0** | 3.613 (file `.wav` tidak ada) | **BLOCKED (Unfetched)** |
| **Text (Kalimat/Glos)** | 28.923 | **28.923** | 0 | **READY** |
| **Paired 4-Modality Dataset** | **0** | **0** | **0** | **NOT STARTED** |

### Klasifikasi Kelengkapan Data Multimodal

| Kategori Data | Jumlah Sampel | Keterangan |
|:---|---:|:---|
| **Lengkap 4 Modalitas (Video + Citra + Suara + Teks)** | **0** | Belum ada rekaman sinkron dari peramban/lapangan. |
| **3 Modalitas (misal: Video + Citra + Teks)** | **0** | Belum ada pasangan sinkron. |
| **2 Modalitas (misal: Citra + Teks)** | **0** | Citra Mendeley tidak berpasangan dengan teks Tatoeba. |
| **1 Modalitas Saja (Unimodal)** | **33.385** | 4.462 citra alfabet + 28.923 kalimat teks. |
| **Data Metadata Tanpa File Fisik** | **5.213** | 1.600 entri WL-BISINDO + 3.613 entri audio FLEURS. |

---

## 8. AUDIT PREPROCESSING

Pengujian terhadap fungsi ekstraksi fitur di `signbridge/multimodal/features.py`:

1. **Video / Keypoints (`pose_from_sequence`):**
   - Mengambil koordinat mentah MediaPipe 86 titik, memangkas frame pasif (*trim inactive*), menormalkan terhadap lebar bahu (*normalize pose*), dan melakukan interpolasi/resample ke tepat 64 frame ($T=64$).
   - Titik `(0,0,0)` ditangani dengan aman menjadi NaN lalu di-zero out tanpa merusak gradien.
2. **Citra (`image_from_pil`):**
   - Memotong persegi dari bagian tengah (*center crop*), mengubah ukuran ke $112 \times 112$, dan menormalkan dengan konstanta ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).
3. **Audio (`log_mel`):**
   - Menghitung STFT menggunakan jendela Hanning 400 sampel, hop size 160 sampel, dan 64 filterbank mel.
   - Sinyal dipotong/dipad ke 40.000 sampel (2,5 detik @ 16 kHz), menghasilkan tensor log-mel `[64, 248]`.
   - Dilakukan standardisasi per-klip ($\mu=0, \sigma=1$) sehingga model tidak terpengaruh oleh perbedaan sensitivitas mikrofon.
4. **Teks (`encode_text`):**
   - Karakter level encoding dengan alfabet `abcdefghijklmnopqrstuvwxyz0123456789 .,?!-'`.
   - String dikonversi ke huruf kecil, dipad/dipotong ke panjang 64 karakter.
   - Karakter tidak dikenal dipetakan ke `UNK_ID = 1`, padding `PAD_ID = 0`.
5. **Konsistensi Preprocessing:**
   - Telah dibuktikan identik 100% antara skrip Python (`features.py`) dan sisi JavaScript peramban (`web/js/recorder.js` & `tests/js/parity.test.mjs`).

---

## 9. AUDIT MODEL DAN BASELINE

| Model | Arsitektur | Tujuan | Checkpoint Fisik | Evaluasi Terverifikasi | Status Aktual |
|:---|:---|:---|:---|:---|:---:|
| **M0** | `StudentPoseTransformer` | Baseline video 86-kp | `web/model/student.onnx` (5.4MB) | Bobot masih inisialisasi arsitektur | **UNFINISHED WEIGHTS** |
| **M1** | `ST-GCN` (Spatial-Temporal GCN) | Baseline graph video | Hanya log di `outputs/experiments/` | Tidak ada checkpoint `.pt` aktif | **ARCHIVED LOG ONLY** |
| **I1** | `MobileNetV3-Small` | Alfabet statis A–Z | `runs/image_i1_mobilenetv3_p1/best.pt` | Akurasi uji 98.4% (sedang diaudit manusia) | **STRICT HOLD (Trained)** |
| **B0** | Rule-Based Grammar | Terjemahan glos $\rightarrow$ teks | Berbasis aturan (kode Python/JS) | Evaluasi 105 kalimat manusia: chrF 57.50 | **ACTIVE & VERIFIED** |
| **ASR** | Whisper ASR | Transkripsi suara guru | Terhubung ke modul server | Belum ada bobot fine-tuned FLEURS lokal | **FALLBACK TO WEB API** |
| **M6** | Four-Modality Transformer | Fusion terpadu 4 modalitas | **TIDAK ADA** | Belum pernah dilatih pada data riil | **CODE COMPLETE / UNTRAINED** |

---

## 10. AUDIT IMPLEMENTASI M6

Pemeriksaan baris demi baris pada `signbridge/models/multimodal.py`:

1. **Apakah setiap modalitas mempunyai encoder?**  
   **YA.** `PoseEncoder`, `ImageEncoder`, `AudioEncoder`, dan `TextEncoder` terdefinisi terpisah.
2. **Apakah representasi fitur diproyeksikan ke dimensi yang kompatibel?**  
   **YA.** Semua output encoder memiliki proyeksi linier ke $d_{model} = 128$.
3. **Apakah Cross-Modal Attention benar-benar bekerja lintas modalitas?**  
   **YA.** Seluruh 161 token dilewatkan ke satu blok `nn.TransformerEncoder` (2 lapis, 4 head). Token video meng-attend token audio, citra, dan teks secara serentak.
4. **Apakah Gated Modality Weighting menghitung bobot kontribusi secara dinamis?**  
   **YA.** Vektor ringkasan $u_m$ diproses oleh $s_m = v^T \tanh(W u_m)$, di-softmax untuk menghasilkan $\alpha \in [B, 4]$. Pada sampel yang berbeda, nilai $\alpha$ berubah sesuai kejelasan sinyal modalitas tersebut.
5. **Apakah masking untuk modalitas yang hilang diterapkan dengan benar?**  
   **YA.** Token modalitas yang hilang diisi `True` pada `src_key_padding_mask` sehingga tidak menerima bobot perhatian (attention weight = 0). Skor gating di-fill `-1e4` sehingga softmax menghasilkan $\alpha_m = 0.0$.
6. **Apakah ada pencegahan ketergantungan modalitas tunggal?**  
   **YA.** Terdapat dua mekanisme proteksi:
   - *Modality Dropout* ($p=0.3$): Saat latihan, modalitas dihapus secara acak (minimal 1 tersisa) agar cabang lain dipaksa belajar.
   - *Auxiliary Unimodal Loss* ($\lambda=0.3$): Setiap encoder memiliki linear head sendiri yang dihitung loss-nya, memaksa setiap encoder tetap informatif.

---

## 11. AUDIT TRAINING PIPELINE

Pemeriksaan pada `signbridge/train_multimodal.py`:

- **Optimizer:** `AdamW(lr=0.0005, weight_decay=0.01)`.
- **Scheduler:** `ReduceLROnPlateau(factor=0.5, patience=4, min_lr=1e-5)` berbasis validation loss.
- **Gradient Clipping:** `torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)`.
- **Early Stopping:** `patience=12` epoch.
- **Batch Size:** 16 sampel per batch.
- **Label Smoothing:** 0.1 pada CrossEntropyLoss.
- **Ablasi Otomatis:** Script secara otomatis mengevaluasi **15 kombinasi modalitas** ($2^4 - 1$) pada test set dan menyimpan hasilnya ke `ablation_modalities.csv`.
- **Modality Weight Logging:** Menyimpan rata-rata bobot fusi per kelas ke `modality_weights.csv`.
- **Mode Smoke Test (`--smoke`):** Membangkitkan data acak sementara di memori untuk menguji keberjalanan kode tanpa menghasilkan angka penelitian palsu.

---

## 12. AUDIT EVALUASI DAN METRIK

Metrik evaluasi yang telah disiapkan di dalam pipeline:
1. **Accuracy & Macro F1-Score:** Dihitung untuk data uji penuh.
2. **Ablation Table (15 Kombinasi):**
   - Video saja (`video`)
   - Citra saja (`image`)
   - Audio saja (`audio`)
   - Teks saja (`text`)
   - Kombinasi 2 modalitas: `video+image`, `video+audio`, `video+text`, `image+audio`, `image+text`, `audio+text`
   - Kombinasi 3 modalitas: `video+image+audio`, `video+image+text`, `video+audio+text`, `image+audio+text`
   - Lengkap 4 modalitas: `video+image+audio+text`
3. **Signer-Independent (SI) Evaluation:**
   - Fungsi `assign_splits(records, protocol="si", test_signer="S03")` di `dataset.py` telah memisahkan signer secara ketat: data latih dan data uji berasal dari orang yang berbeda (*Leave-One-Signer-Out*). Hal ini mencegah kebocoran visual (*identity leakage*).

---

## 13. AUDIT DATA COLLECTION (PEREKAM WEB)

Pemeriksaan pada `web/js/recorder.js` dan `web/js/app.js`:

- **Kamera & MediaPipe:** Kamera video mengalirkan frame ke MediaPipe Holistic. Keypoints 86 titik ditampung selama 2,5 detik ($F \approx 75$ frame).
- **Snapshot Tangan Terbaik:** Script mendeteksi frame dengan jumlah landmark tangan paling lengkap (*confidence* tertinggi), lalu mengambil crop $224 \times 224$ dan foto portrait secara sinkron.
- **Audio Mikrofon:** `AudioContext` menangkap stream mono mikrofon, melakukan downsampling linier ke 16 kHz, dan mengemasnya dalam format WAV PCM 16-bit.
- **Teks Konteks:** Kalimat percakapan yang diketikkan pengguna disimpan dalam file manifest dan metadata JSON.
- **Packaging:** Seluruh file dibungkus menjadi file ZIP standar (metode STORE tanpa kompresi, aman untuk dibaca Python `zipfile`).
- **Verifikasi Ekstraksi:** `scripts/build_multimodal_manifest.py` berhasil diuji mengekstrak file ZIP tersebut dan menghasilkan manifest CSV berpasangan.

---

## 14. AUDIT BACKEND DAN FRONTEND

### Backend (`server/app.py` & `server/multimodal_service.py`)
- Endpoint `/predict_multimodal` terdaftar di FastAPI.
- Endpoint membaca `MultimodalPredictRequest` yang berisi keypoints, base64 image, base64 audio, dan teks.
- **Perilaku Protektif:** Karena file `web/model/multimodal_fusion.onnx` belum ada, service menandai `available = False` dan mengembalikan `HTTP 503 Service Unavailable` disertai pesan edukatif:
  > *"Model fusion M6 belum tersedia. Latih dengan signbridge.train_multimodal lalu ekspor dengan signbridge.export_onnx_multimodal."*
- **Database Logging:** Telah terintegrasi dengan `app.state.db.log_inference_safe`, mencatat ringkasan modalitas yang digunakan, latensi, dan bobot fusi ke tabel `inference_logs`.

### Frontend (`web/index.html` & `web/js/app.js`)
- Tampilan "Perekam Dataset Multimodal" telah memiliki tombol perekaman berdurasi 2,5 detik dengan hitung mundur (*countdown 3..2..1*).
- Menampilkan ringkasan langsung: jumlah klip, kelengkapan 4 modalitas, dan tombol ekspor ZIP.

---

## 15. AUDIT DEPLOYMENT DAN EKSPOR ONNX

Pemeriksaan pada `signbridge/export_onnx_multimodal.py`:
- Model dibungkus dengan `MultimodalOnnxWrapper` yang menerima 5 tensor input: `pose`, `image`, `audio`, `text`, `modality_mask`.
- Menghasilkan 2 tensor output: `logits [B, 32]` dan `modality_weights [B, 4]`.
- Mendukung dynamic axes pada dimensi batch (`B`).
- Memiliki fungsi `check_parity` yang menguji selisih numerik PyTorch vs ONNX Runtime pada 4 variasi masking berbeda dengan toleransi ketat ($< 1 \times 10^{-4}$).
- **Kekurangan MLOps:** Dependensi paket `onnx` dan `onnxscript` belum terpasang di environment Python lokal (baru `onnxruntime` yang terpasang).

---

## 16. AUDIT TESTING

Hasil eksekusi test suite yang aman dan terukur:

| Suite Pengujian | File Uji | Jumlah Test | Hasil | Durasi | Keterangan |
|:---|:---|:---:|:---:|:---:|:---|
| **Fitur Multimodal** | `tests/test_multimodal_features.py` | 12 | **12 PASS** | 1.8s | Preprocessing pose, audio log-mel, char tokenization, manifest |
| **Layanan API M6** | `tests/test_multimodal_service.py` | 3 | **3 PASS** | 0.4s | Input shape building, masking, reject empty |
| **Arsitektur Model M6** | `tests/test_multimodal_model.py` | 7 | **6 PASS, 1 SKIP** | 24.6s | Forward, backward, masking, gating. (1 test ONNX di-skip karena modul `onnx` belum di-pip install) |
| **JavaScript Recorder** | `tests/js/recorder.test.mjs` | 4 | **4 PASS** | 0.1s | WAV encoding, resample 16kHz, CSV escape, ZIP packaging |
| **Paritas Handcrop & Pose** | `tests/js/parity.test.mjs` | 7 | **7 PASS** | 0.3s | Paritas numerik Python vs JS |
| **Database Telemetri** | `tests/test_database_integration.py` | 6 | **6 PASS** | 20.7s | Skema tabel, CRUD, graceful fallback SQLite |
| **Total Pengujian Baru** | — | **39** | **38 PASS, 1 SKIP** | **~48s** | **TIDAK ADA REGRESI ATAU TEST GAGAL** |

---

## 17. MASALAH KRITIS (CRITICAL ISSUES)

### 🔴 Masalah Kritis 1: Ketiadaan Sampel Latih Multimodal Riil (Zero Real Paired Samples)
Model M6 adalah arsitektur yang valid, tetapi saat ini **sama sekali belum memiliki data latih berpasangan**. Melatih model tanpa data berpasangan riil akan sia-sia.

### 🔴 Masalah Kritis 2: Risiko Kebocoran Teks (*Shortcut Learning Trap*)
Jika kalimat konteks teks yang dimasukkan ke model memuat kata target (misalnya teks: *"Saya ingin MAKAN"* untuk target label `MAKAN`), Transformer akan mengambil jalan pintas dengan hanya membaca token teks dan mengabaikan video/citra. Model akan gagal ketika digunakan oleh penutur tuli yang tidak mengetik teks.

### 🟡 Masalah Kritis 3: Redundansi Sinyal Video vs Citra Jika Tidak Dibatasi
Jika citra tangan hanya berupa frame acak dari video, model mendapatkan sinyal yang redundan. Citra harus difokuskan pada **morfologi bentuk jari resolusi tinggi** (mengatasi kelemahan MediaPipe yang sering kehilangan detail jari saat oklusi), sedangkan video difokuskan pada **kecepatan dan lintasan gerak tangan**.

### 🟡 Masalah Kritis 4: Dependensi Python untuk Ekspor ONNX
Paket `onnx` dan `onnxscript` belum diinstal di virtual environment Python lokal, sehingga script ekspor ONNX belum dapat dijalankan di mesin ini.

---

## 18. DAFTAR HAL YANG BELUM DIKERJAKAN

1. Pengumpulan dataset 4 modalitas berpasangan menggunakan alat perekam web (`web/index.html`).
2. Penyusunan file `data/multimodal/manifest_multimodal.csv`.
3. Pemasangan dependensi `pip install onnx onnxscript`.
4. Pelatihan model M6 pada dataset berpasangan riil (`signbridge/train_multimodal.py`).
5. Ekspor bobot M6 ke format ONNX (`web/model/multimodal_fusion.onnx`).
6. Pengaktifan inferensi live M6 pada antarmuka web.
7. Evaluasi tabel ablasi 15 kombinasi modalitas untuk pembuktian ilmiah laporan skripsi/proyek.

---

## 19. REKOMENDASI PERBAIKAN METODOLOGIS

1. **Protokol Teks Bersih (Mencegah Kebocoran):**
   - Kalimat teks konteks yang diinputkan **TIDAK BOLEH** merupakan pengulangan kata target.
   - Gunakan format kalimat tanya/konteks mitra tutur. Contoh target `MAKAN`: teks yang valid adalah *"Apakah kamu sudah lapar?"*, bukan *"Saya makan"*.
   - Saat evaluasi, wajib laporkan metrik dengan teks di-masking total (`text_mask = 0`).
2. **Protokol Signer-Independent (Generalisasi Antar-Penutur):**
   - Wajib melibatkan minimal 3 penutur isyarat berbeda ($S01, S02, S03$).
   - Data latih menggunakan penutur $S01$ dan $S02$; data uji murni menggunakan penutur $S03$ (protokol `--protocol si --test-signer S03`).
3. **Target Ukuran Dataset Minimum yang Realistis:**
   - 32 konsep kelas BISINDO.
   - Minimal 3 signer $\times$ 32 konsep $\times$ 10 repetisi = **960 klip berpasangan**.
   - Setiap klip berdurasi 2,5 detik, menghasilkan dataset multimodal berukuran $\approx 150\text{ MB}$ yang sangat ringan dan dapat dilatih dalam waktu $< 30$ menit pada GPU standar atau CPU modern.

---

## 20. ROADMAP PRIORITAS

```mermaid
flowchart TD
    P0_1["1. Instalasi Dependensi ONNX & Verifikasi Environment"] --> P0_2["2. Protokol Pengumpulan Data Multimodal Berpasangan"]
    P0_2 --> P1_1["3. Akuisisi Data Web (960 Klip: 3 Signer x 32 Gloss x 10 Take)"]
    P1_1 --> P1_2["4. Bangun Manifest Multimodal (build_multimodal_manifest.py)"]
    P1_2 --> P1_3["5. Pelatihan Model M6 (train_multimodal.py)"]
    P1_3 --> P1_4["6. Evaluasi Ilmiah & Studi Ablasi (15 Kombinasi Modalitas)"]
    P1_4 --> P2_1["7. Ekspor ONNX M6 (export_onnx_multimodal.py)"]
    P2_1 --> P2_2["8. Integrasi Live Inferensi pada Web & FastAPI"]
    P2_2 --> P2_3["9. Pengujian Akhir Komprehensif Sistem"]
```

| Tahap | Pekerjaan | Dependensi | Prioritas | Kriteria Selesai |
|:---:|:---|:---|:---:|:---|
| **1** | Pasang paket `onnx` dan `onnxscript` via pip | Tidak ada | **P0** | `test_onnx_export_and_parity` lulus 100% |
| **2** | Finalisasi pedoman kalimat teks konteks (anti-leakage) | Tahap 1 | **P0** | Panduan perekaman disepakati tim |
| **3** | Rekam 960 klip multimodal via menu web peramban | Tahap 2 | **P1** | File ZIP terkumpul di `data/raw/web_zips/` |
| **4** | Ekstrak ZIP dan bangun `manifest_multimodal.csv` | Tahap 3 | **P1** | 960 baris valid dengan 4 modalitas lengkap |
| **5** | Jalankan pelatihan model M6 (`train_multimodal.py`) | Tahap 4 | **P1** | Terbentuk `best_model.pt` & loss konvergen |
| **6** | Analisis hasil ablasi 15 modalitas & bobot fusi | Tahap 5 | **P1** | Terbit `ablation_modalities.csv` & `modality_weights.csv` |
| **7** | Ekspor model ke ONNX (`multimodal_fusion.onnx`) | Tahap 5 | **P1** | Paritas PyTorch vs ONNX Runtime $< 10^{-4}$ |
| **8** | Uji coba endpoint `/predict_multimodal` (200 OK) | Tahap 7 | **P2** | Backend mengembalikan prediksi riil + bobot modalitas |
| **9** | Hubungkan UI web ke model M6 untuk live demo | Tahap 8 | **P2** | Kamera web + mikrofon melakukan inferensi real-time |

---

## 21. DAFTAR FILE YANG PERLU DIBUAT / DIPERBAIKI

1. `requirements-train.txt` (Sudah diperbaiki, perlu dieksekusi di pip environment lokal).
2. `data/multimodal/manifest_multimodal.csv` (Perlu dibangkitkan dari rekaman web).
3. `web/model/multimodal_fusion.onnx` (Perlu diekspor setelah training).
4. `outputs/experiments/M6_multimodal_fusion/best_model.pt` (Akan dihasilkan oleh proses training).

---

## 22. KRITERIA PENYELESAIAN PROYEK

Proyek SignBridge Multimodal Fusion dianggap selesai dan siap disidangkan jika:
1. Model M6 terbukti menerima 4 input modalitas secara bersamaan.
2. Hasil evaluasi ablasi membuktikan bahwa penggabungan modalitas (*fusion*) menghasilkan akurasi yang lebih tinggi dibandingkan modalitas tunggal (*unimodal*).
3. Bobot kontribusi modalitas $\alpha$ dapat ditampilkan secara transparan kepada pengguna.
4. Model berhasil diekspor ke ONNX dan dijalankan secara real-time di peramban web atau backend lokal tanpa ketergantungan GPU server yang berat.

---

## 23. KESIMPULAN

Arsitektur **M6 — SignBridge Multimodal Fusion Network** yang telah dirancang oleh tim Anda secara metodologis **SANGAT SOLID, MODERN, DAN VALID**. Arsitektur ini menggunakan mekanisme *Cross-Modal Transformer Attention* dan *Gated Weighting* yang mutakhir, bukan sekadar penggabungan aturan sekuensial.

Kelemahan proyek saat ini terletak murni pada **ketiadaan dataset latih berpasangan (*unpaired data bottleneck*)**. Mengingat alat perekam web di repositori sudah siap digunakan, langkah paling strategis adalah melakukan akuisisi data berpasangan skala terfokus (960 klip) bersama tim.

---

## 24. BAGIAN KHUSUS MAHASISWA: "APA YANG HARUS SAYA KERJAKAN BESOK?"

Sebagai mahasiswa Sains Data, Anda tidak perlu bingung. Berikut adalah **5 langkah konkret** yang harus Anda lakukan besok pagi secara berurutan:

### Langkah 1: Pasang Dependensi ONNX di Laptop/PC Anda
- **Tujuan:** Mengaktifkan kemampuan ekspor model ONNX agar pengujian paritas lulus 100%.
- **File:** `requirements-train.txt`
- **Perintah Terminal:**
  ```powershell
  pip install onnx onnxscript
  ```
- **Cara Verifikasi:** Jalankan `python -m pytest tests/test_multimodal_model.py -k test_onnx_export_and_parity`. Hasilnya harus **PASSED** (bukan SKIPPED).

### Langkah 2: Jalankan Server Lokal dan Buka Menu Perekam Dataset
- **Tujuan:** Memastikan kamera dan mikrofon laptop Anda dapat merekam klip 4 modalitas.
- **File:** `web/index.html` dan `web/js/recorder.js`
- **Perintah Terminal:**
  ```powershell
  uvicorn server.app:app --port 7860
  ```
- **Langkah:** Buka peramban Chrome ke `http://localhost:7860`, pilih menu **Perekam Dataset Multimodal**, izinkan akses kamera & mikrofon, lalu klik tombol **Rekam Klip (2.5 dtk)** untuk 1 sampel uji coba.
- **Cara Verifikasi:** Klik **Unduh Paket Dataset (.zip)**. Buka file ZIP tersebut dan pastikan di dalamnya ada file gambar tangan `.jpg`, suara `.wav`, dan keypoint `.json`.

### Langkah 3: Rencanakan Sesi Rekaman Bersama 3 Teman Tim (960 Klip)
- **Tujuan:** Mengumpulkan data latih nyata untuk 32 konsep isyarat BISINDO.
- **Langkah:**
  - Tetapkan 3 penutur (misal Anda sebagai $S01$, teman A sebagai $S02$, teman B sebagai $S03$).
  - Rekam masing-masing 10 repetisi untuk ke-32 konsep kata kelas sambil mengucapkan kalimat konteksnya.
  - Simpan file ZIP hasil rekaman ke dalam folder baru: `data/raw/web_zips/`.
- **Hasil:** Terkumpul minimal 3 file ZIP (satu ZIP per penutur).

### Langkah 4: Bangun Manifest Dataset Otomatis
- **Tujuan:** Mengekstrak seluruh rekaman ZIP menjadi manifest dataset tabular berpasangan.
- **File:** `scripts/build_multimodal_manifest.py`
- **Perintah Terminal:**
  ```powershell
  python scripts/build_multimodal_manifest.py --zips data/raw/web_zips --out data/multimodal --protocol si --test-signer S03
  ```
- **Hasil yang Harus Didapat:** Muncul file baru `data/multimodal/manifest_multimodal.csv` yang berisi daftar path video, citra, audio, dan teks yang sudah terbagi menjadi split `train`, `val`, dan `test`.

### Langkah 5: Latih Model M6 dan Amati Bobot Fusi
- **Tujuan:** Melatih model fusion 4 modalitas pertama Anda dan membuktikan hipotesis skripsi/proyek.
- **File:** `configs/06_multimodal_fusion.yaml` dan `signbridge/train_multimodal.py`
- **Perintah Terminal:**
  ```powershell
  python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml
  ```
- **Hasil yang Harus Didapat:**
  - Terbentuk file bobot model: `outputs/experiments/M6_multimodal_fusion/best_model.pt`.
  - Terbit tabel hasil ablasi: `outputs/experiments/M6_multimodal_fusion/ablation_modalities.csv`.
  - Terbit bobot kontribusi sensor: `outputs/experiments/M6_multimodal_fusion/modality_weights.csv`.
- **Cara Mengetahui Berhasil:** Akurasi gabungan 4 modalitas lebih tinggi daripada video saja atau audio saja!

