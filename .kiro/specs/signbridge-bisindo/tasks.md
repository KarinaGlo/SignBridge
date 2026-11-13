# Implementation Plan: SignBridge BISINDO — Sistem Multimodal 4 Jalur

## Overview

Rencana implementasi ini menguraikan langkah-langkah pembangunan **SignBridge**: sistem pengenalan bahasa isyarat Indonesia (BISINDO) berbasis arsitektur multimodal 4 jalur (Pose Keypoint · RGB Video · Ejaan Jari · ASR Audio) dengan pipeline teks BISINDO→Indonesia dan jembatan antarmodal (FSL, MT, animasi isyarat).

**Tim Pelaksana:**
- **Farrel** — Data Engineer: pipeline keypoint, RGB token, abjad, teks, audio, dataset sendiri
- **Jonnathan** — Modeling: eksperimen E0–E7, I1–I3, Optuna, FSL X1–X4
- **Gloria** — Evaluasi & Deployment: evaluasi lengkap, Whisper ASR, penyusun kalimat, Docker, Azure, jembatan MT

Bahasa implementasi: **Python** (backend, model, training) + **JavaScript/HTML** (web inference).

---

## Tasks

---

### FASE 1 — Setup Proyek & Infrastruktur

- [ ] **1. Setup Proyek, Konfigurasi, dan Struktur Direktori**
  - Buat struktur direktori proyek: `data/`, `configs/`, `src/`, `tests/`, `scripts/`, `web/`, `notebooks/`
  - Buat `requirements.txt` dengan semua dependensi Python bertanda versi terpatok
  - Buat `package.json` dengan dependensi JavaScript terpatok (onnxruntime-web, mediapipe JS)
  - Buat file konfigurasi terpusat `configs/train_bisindo.yaml` dan `configs/eval_bisindo.yaml`
  - Buat `configs/graph_config.yaml` untuk topologi KeypointGraph (86 node, edge spasial/temporal/simetri)
  - Buat `configs/phonological_annotations.yaml` dengan anotasi fonologis (handshape, lokasi, arah_gerak)
  - Buat `setup.sh` / `setup.bat` yang menginstal semua dependensi dan mencetak "Setup complete."
  - Buat `DATA_CARD.md` dan `DATA_FORMAT.md` dengan skema keypoint 86 node dan anotasi
  - _Requirements: 1.7, 4.3, 11.2, 15.6, 20.1, 20.2, 20.3_
  - **PJ: Jonnathan (lead), semua anggota**

  - [ ] 1.1 Inisialisasi repo Git dan struktur direktori inti
    - Inisialisasi repo dengan `.gitignore`, `README_draft.md`, branching strategy
    - Buat seluruh struktur direktori: `data/raw`, `data/processed`, `data/keypoints`, `configs/`, `src/`, `tests/`, `scripts/`, `web/`, `notebooks/`
    - _Requirements: 20.1, 20.2_
    - **PJ: Jonnathan**

  - [ ] 1.2 Buat file konfigurasi inti (YAML, requirements)
    - Buat `requirements.txt` (PyTorch, MediaPipe, FastAPI, ONNX Runtime, Hypothesis, Whisper, transformers, optuna, dll.) dengan versi terpatok
    - Buat `configs/train_bisindo.yaml`: T_max=64, 86 node, split SD 60/10/30 dan split SI 5-fold
    - Buat `configs/eval_bisindo.yaml`: metrik Top-1/5, WER, CER, RTF, BLEU, chrF
    - Buat `configs/graph_config.yaml`: 86 keypoint (21 tangan kiri + 21 tangan kanan + 33 pose + 11 wajah selektif), edge spasial/temporal/simetri
    - Buat `configs/phonological_annotations.yaml` dengan anotasi handshape/lokasi/arah_gerak tiap gloss
    - _Requirements: 4.3, 11.2, 20.2, 20.3_
    - **PJ: Jonnathan**

  - [ ] 1.3 Buat dokumentasi data dan setup script
    - Buat `DATA_CARD.md` dan `DATA_FORMAT.md` (skema keypoint, format ONNX input/output)
    - Buat `CONTRIBUTING_DATA.md` dalam Bahasa Indonesia
    - Buat `setup.sh` / `setup.bat` dengan exit code 0 jika berhasil
    - Buat `smoke_test.py` awal untuk verifikasi impor semua modul
    - _Requirements: 15.6, 20.1, 20.3_
    - **PJ: Semua anggota**

- [x] **Checkpoint Fase 1:** Repo aktif, semua konfigurasi YAML valid, `smoke_test.py` berjalan tanpa error.

---

### FASE 2 — Data Pipeline (Farrel)

- [ ] **2. Akuisisi & Validasi Dataset**
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.4, 2.5_
  - **PJ: Farrel**

  - [ ] 2.1 Download dan validasi dataset WL-BISINDO dan FSL-105
    - Implementasi `download_wl_bisindo(kaggle_identifier, output_dir)` dengan retry logic
    - Download FSL-105 (Filipino Sign Language, 105 kelas) sebagai dataset sekunder
    - Catat file gagal ke log; hentikan jika < 80% file berhasil
    - Verifikasi integritas: jumlah video per gloss, signer, dan split
    - _Requirements: 1.1, 2.1, 2.4, 2.5_
    - **PJ: Farrel**

  - [ ] 2.2 Implementasi `DatasetSplitter` dengan dua strategi split
    - **Split SD (Signer-Dependent):** rasio 60/10/30 (train/val/test), stratifikasi per gloss
    - **Split SI (Signer-Independent):** leave-one-signer-out 5-fold cross-validation
    - Simpan metadata tiap video ke `.jsonl`: `path`, `gloss`, `signer_id`, `split`, `fold`, `duration_sec`, `fps`
    - Verifikasi tidak ada signer leakage antar split (SI)
    - _Requirements: 1.4, 1.5, 2.3_
    - **PJ: Farrel**

  - [ ] 2.3 Implementasi `AnnotationParser` dan `AnnotationSerializer`
    - `load(path)` dengan validasi field wajib; raise `SchemaValidationError` jika field hilang
    - `save(records, path)` yang menghasilkan valid JSON Lines
    - _Requirements: 1.5, 15.2, 15.3, 15.4_
    - **PJ: Farrel**

- [ ] **3. Ekstraksi Keypoint 86 Node**
  - _Requirements: 3.1–3.6_
  - **PJ: Farrel**

  - [ ] 3.1 Implementasi `KeypointExtractor86` dengan MediaPipe Holistic
    - Ekstrak **86 keypoint per frame**: 21 tangan kiri + 21 tangan kanan + 33 pose + 11 wajah selektif (bukan 543 node penuh)
    - Simpan array `[T, 86, 3]` dtype float32 ke `.npy` dan confidence `[T, 86, 1]` ke `_conf.npy`
    - Implementasi interpolasi linear dari frame valid dalam jendela ±5 frame
    - Zero-pad jika tidak ada frame valid dalam jendela; catat ke log
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_
    - **PJ: Farrel**

  - [ ] 3.2 Normalisasi koordinat keypoint dan batch extraction
    - Normalisasi relatif terhadap bounding box tubuh per frame ke [-1, 1]
    - Fallback ke bounding box frame sebelumnya yang valid jika width/height = 0
    - Batch processing paralel dengan `num_workers` (default: 4), progress bar tqdm
    - Clip temporal ke T_max=64 frame (uniform sampling); zero-pad jika T < 64
    - _Requirements: 3.5, 4.4_
    - **PJ: Farrel**

  - [ ] 3.3 Implementasi `KeypointGraphBuilder` — konstruksi graf dari YAML
    - Load `configs/graph_config.yaml`, validasi semua node index ∈ [0, 85]
    - Periksa tidak ada isolated node; raise `GraphConfigError` jika ditemukan
    - _Requirements: 4.1, 4.2, 4.3, 4.5_
    - **PJ: Farrel**

  - [ ] 3.4 Anotasi fonologis per gloss
    - Buat/lengkapi `configs/phonological_annotations.yaml` dengan label handshape, lokasi, arah_gerak tiap gloss
    - Implementasi `PhonologicalAnnotationLoader` untuk load dan validasi anotasi
    - _Requirements: 11.1, 11.2_
    - **PJ: Farrel**

- [ ] **4. RGB Token VideoMAE**
  - _Requirements: pipeline Stream_B_
  - **PJ: Farrel**

  - [ ] 4.1 Implementasi ekstraksi frame RGB untuk VideoMAE
    - Ekstrak frame pada FPS asli, uniform sampling ke T_max=64 frame
    - Resize ke 224×224, normalisasi dengan mean/std ImageNet
    - Simpan sebagai `[64, 3, 224, 224]` float32 tensor per video
    - _Requirements: Stream_B input_
    - **PJ: Farrel**

  - [ ] 4.2 Implementasi `VideoMAETokenizer` — ekstraksi token RGB
    - Load VideoMAE pretrained (ViT-B/16, patch 16×16), freeze encoder
    - Ekstrak token sequence `[N_tokens, 768]` per video clip
    - Simpan token ke disk untuk efisiensi training (cached features)
    - _Requirements: Stream_B, 7.3_
    - **PJ: Farrel**

- [ ] **5. Dataset Ejaan Jari (Fingerspell)**
  - _Requirements: fingerspell pipeline_
  - **PJ: Farrel**

  - [ ] 5.1 Akuisisi dan preprocessing gambar ejaan jari
    - Kumpulkan/augmentasi gambar ejaan jari A–Z (26 kelas)
    - Preprocessing: resize 224×224, normalisasi ImageNet, augmentasi (flip, rotasi, color jitter)
    - Buat split 70/15/15 (train/val/test) stratified per huruf
    - _Requirements: fingerspell I1-I3_
    - **PJ: Farrel**

  - [ ] 5.2 Validasi dataset ejaan jari
    - Verifikasi ≥ N sampel per huruf (target ≥ 100 per kelas)
    - Simpan metadata ke `data/fingerspell/metadata.jsonl`
    - _Requirements: fingerspell I1-I3_
    - **PJ: Farrel**

- [ ] **6. Korpus Teks BISINDO**
  - _Requirements: teks B0, T1–T3_
  - **PJ: Farrel**

  - [ ] 6.1 Kumpulkan dan preprocessing korpus teks BISINDO→Indonesia
    - Kumpulkan pasangan kalimat BISINDO (urutan gloss) → kalimat Indonesia
    - Tokenisasi dan simpan ke `data/text/corpus.jsonl`
    - _Requirements: B0, T1_
    - **PJ: Farrel**

  - [ ] 6.2 Buat vocabulary dan tokenizer untuk model teks
    - Buat vocabulary gloss (dari seluruh label training)
    - Integrasikan tokenizer IndoT5/mT5 untuk model transformer
    - _Requirements: T2, T3_
    - **PJ: Farrel**

- [ ] **7. Rekaman Audio & Dataset Sendiri**
  - _Requirements: ASR A1–A3, dataset sendiri_
  - **PJ: Farrel**

  - [ ] 7.1 Rekam korpus audio kelas BISINDO
    - Rekam audio pengucapan label tiap gloss (Bahasa Indonesia) untuk pasangan ASR
    - Format: WAV 16 kHz mono; simpan ke `data/audio/`
    - _Requirements: A1, A2, A3_
    - **PJ: Farrel**

  - [ ] 7.2 Bangun dataset sendiri ≥3000 sampel multimodal
    - **Target:** 58 kelas × 3 perekam × 18 pengulangan = ≥3132 sampel multimodal
    - Rekam video RGB + audio serentak; ekstrak keypoint 86 node
    - Simpan dalam struktur direktori standar WL-BISINDO
    - Implementasi form persetujuan data (consent) dan sertifikat PDF
    - _Requirements: 6.1–6.7, 21.4, 21.5_
    - **PJ: Farrel**

  - [ ] 7.3 Validasi dataset sendiri dan integrasi ke pipeline
    - Validasi format (MP4/AVI), resolusi ≥ 480p, FPS ≥ 25, durasi 1–10 detik
    - Verifikasi MediaPipe dapat mengekstrak 86 keypoint
    - Tolak video gagal; pertahankan dataset utama tidak berubah
    - Integrasikan ke split training utama
    - _Requirements: 21.5, 21.6_
    - **PJ: Farrel**

  - [ ] 7.4 Validasi dan preprocessing FSL-105
    - Ekstrak keypoint 86 node untuk seluruh FSL-105
    - Simpan metadata ke `data/fsl105/metadata.jsonl`
    - _Requirements: X1–X4 (FSL)_
    - **PJ: Farrel**

- [x] **Checkpoint Fase 2:**
  - Keypoint 86 node tervalidasi untuk seluruh dataset
  - RGB token VideoMAE tersimpan (cached features)
  - Dataset ejaan jari, korpus teks, dan audio siap
  - Dataset sendiri ≥3132 sampel selesai direkam dan divalidasi
  - FSL-105 siap untuk eksperimen FSL

---

### FASE 3 — Modeling (Jonnathan)

- [ ] **8. Augmentasi Data**
  - _Requirements: 5.1–5.6_
  - **PJ: Jonnathan**

  - [ ] 8.1 Implementasi `TemporalAugmenter`
    - Speed perturbation 0.7×–1.3×, random frame dropping ≤ 20%, temporal jitter ±3 frame
    - _Requirements: 5.1_
    - **PJ: Jonnathan**

  - [ ] 8.2 Implementasi `SpatialKeypointAugmenter`
    - Horizontal flipping dengan swap tangan kiri/kanan konsisten
    - Rotasi 2D ±15°, Gaussian noise std ≤ 0.02
    - _Requirements: 5.2, 5.4_
    - **PJ: Jonnathan**

  - [ ] 8.3 Implementasi `SpatialRGBAugmenter`
    - Horizontal flipping sinkron dengan keypoint, random crop 0.8–1.0, color jitter ±0.2
    - _Requirements: 5.3_
    - **PJ: Jonnathan**

  - [ ] 8.4 Implementasi `AugmentationPipeline` — orkestrasi
    - Val/test: hanya normalisasi standar. Train: semua augmentasi aktif.
    - _Requirements: 5.5, 5.6_
    - **PJ: Jonnathan**

- [ ] **9. Arsitektur Model — Eksperimen E0 hingga E7**
  - _Requirements: 7.1–7.5, 10.1–10.5, 11.1–11.5, 14.1–14.7_
  - **PJ: Jonnathan**

  - [ ] 9.1 E0 — Student Baseline (keypoint saja, GRU/LSTM)
    - Bangun model student sederhana: ST-GCN ringan atau GRU atas 86 keypoint
    - Training dari nol, evaluasi Top-1 SD dan SI sebagai baseline
    - _Requirements: E0_
    - **PJ: Jonnathan**

  - [ ] 9.2 E1 — ST-GCN full pada 86 keypoint
    - Implementasi `StreamA` (ST-GCN) dengan input `[B, T_max, 86, 3]`
    - Training dari nol; evaluasi Top-1/5 SD dan SI
    - _Requirements: E1, 7.1_
    - **PJ: Jonnathan**

  - [ ] 9.3 E2 — ST-GCN + Transfer Learning dari WLASL/ASL
    - Pretrain ST-GCN pada dataset WLASL (atau ASL publik), fine-tune ke WL-BISINDO
    - Learning rate diferensial: lapisan pretrained × 0.1
    - _Requirements: E2, 12.1–12.3_
    - **PJ: Jonnathan**

  - [ ] 9.4 E3 — ST-GCN + Transfer + Fonologis Head
    - Tambahkan `FonologisHead` (handshape, lokasi, arah_gerak) ke arsitektur E2
    - Loss total: L_total = L_gloss + λ₁·L_handshape + λ₂·L_lokasi + λ₃·L_gerak
    - _Requirements: E3, 11.1–11.5_
    - **PJ: Jonnathan**

  - [ ] 9.5 E4 — Fusion Concat (Pose + RGB)
    - Implementasi `StreamB` (VideoMAE, frozen) dengan input `[B, 64, 3, 224, 224]`
    - Implementasi `FusionModule` concatenation: concat([feat_A, feat_B]) → FC → logits
    - Evaluasi kontribusi setiap stream
    - _Requirements: E4, 7.2, 7.3_
    - **PJ: Jonnathan**

  - [ ] 9.6 E5 — Cross-Attention Fusion (Pose ↔ RGB)
    - Implementasi `FusionModule` Bidirectional Cross-Attention
    - feat_A attend to feat_B dan sebaliknya; output digabungkan → GlossHead
    - _Requirements: E5, 7.4_
    - **PJ: Jonnathan**

  - [ ] 9.7 E6 — Student Distilasi dari Teacher (E5)
    - Implementasi `StudentModel` (lebih kecil) dan `DistillationTrainer`
    - L_distil = α·KL(soft_targets) + (1-α)·CE(hard_labels), α=0.7, T=4.0
    - Target: student Top-1 ≥ 78% dengan ukuran ≤ setengah teacher
    - _Requirements: E6, 14.1–14.3, 14.7_
    - **PJ: Jonnathan**

  - [ ] 9.8 E7 — Ekspor ONNX dan Kuantisasi
    - Ekspor `StudentModel` ke ONNX opset 17
    - Input: `[1, 64, 86, 3]` → Output: `[1, 32]` (atau jumlah kelas)
    - Kuantisasi INT8; ukuran file ≤ 10 MB
    - Implementasi `ONNXValidator`: toleransi perbedaan probabilitas ≤ 1e-4
    - _Requirements: E7, 14.4–14.6_
    - **PJ: Jonnathan**

- [ ] **10. Model Ejaan Jari (I1–I3)**
  - _Requirements: fingerspell I1–I3_
  - **PJ: Jonnathan**

  - [ ] 10.1 I1 — CNN Baseline untuk ejaan jari
    - MobileNetV3-small fine-tune pada dataset ejaan jari (26 kelas, A–Z)
    - Evaluasi Top-1 accuracy
    - _Requirements: I1_
    - **PJ: Jonnathan**

  - [ ] 10.2 I2 — ResNet/EfficientNet fine-tune
    - Fine-tune EfficientNet-B0 pada dataset ejaan jari
    - Bandingkan dengan I1
    - _Requirements: I2_
    - **PJ: Jonnathan**

  - [ ] 10.3 I3 — Ekspor ONNX model ejaan jari
    - Ekspor model terbaik (I1 atau I2) ke ONNX
    - Input: `[1, 3, 224, 224]` → Output: `[1, 26]`
    - _Requirements: I3_
    - **PJ: Jonnathan**

- [ ] **11. Hyperparameter Tuning dengan Optuna**
  - _Requirements: Optuna tuning_
  - **PJ: Jonnathan**

  - [ ] 11.1 Optuna tuning untuk model video (E-series)
    - 20 trial: cari learning rate, hidden_dim, num_heads, λ fonologis, α distilasi
    - Simpan hasil studi ke `configs/optuna_video_study.pkl`
    - _Requirements: Optuna 20 trial video_
    - **PJ: Jonnathan**

  - [ ] 11.2 Optuna tuning untuk model ejaan jari (I-series)
    - 12 trial: cari learning rate, weight decay, dropout
    - Simpan hasil studi ke `configs/optuna_fingerspell_study.pkl`
    - _Requirements: Optuna 12 trial gambar_
    - **PJ: Jonnathan**

- [ ] **12. Few-Shot Learning — FSL X1–X4**
  - _Requirements: X1–X4 FSL_
  - **PJ: Jonnathan**

  - [ ] 12.1 X1 — Prototypical Networks pada fitur keypoint
    - Implementasi Prototypical Network menggunakan embedding ST-GCN (E3)
    - Evaluasi N-way K-shot pada FSL-105
    - _Requirements: X1_
    - **PJ: Jonnathan**

  - [ ] 12.2 X2 — MAML (Model-Agnostic Meta-Learning)
    - Implementasi MAML first-order pada model video
    - Evaluasi pada FSL-105 N-way K-shot
    - _Requirements: X2_
    - **PJ: Jonnathan**

  - [ ] 12.3 X3 — Metric Learning (Triplet Loss)
    - Tambahkan triplet loss head ke model E3/E5
    - Evaluasi retrieval accuracy pada FSL-105
    - _Requirements: X3_
    - **PJ: Jonnathan**

  - [ ] 12.4 X4 — Evaluasi lintas-dataset FSL (BISINDO ↔ FSL-105)
    - Zero-shot/few-shot transfer BISINDO → FSL-105 dan sebaliknya
    - Laporkan accuracy N=5-way, K=1/5-shot
    - _Requirements: X4_
    - **PJ: Jonnathan**

- [x] **Checkpoint Fase 3:**
  - E0–E7 selesai; semua hasil training terdokumentasi
  - I1–I3 selesai; ONNX ejaan jari valid
  - Optuna studi tersimpan
  - X1–X4 selesai; hasil FSL terlaporkan
  - Semua ONNX tervalidasi (perbedaan ≤ 1e-4)

---

### FASE 4 — Evaluasi & Deployment (Gloria)

- [ ] **13. Evaluasi Lengkap Model Video**
  - _Requirements: 19.1–19.6_
  - **PJ: Gloria**

  - [ ] 13.1 Evaluasi SD (Signer-Dependent) dan SI (Signer-Independent)
    - Jalankan `evaluate.py --config configs/eval_bisindo.yaml --split SD`
    - Jalankan leave-one-signer-out 5-fold CV: laporkan mean ± std Top-1 dan Top-5
    - _Requirements: 19.1, 19.4_
    - **PJ: Gloria**

  - [ ] 13.2 Studi Ablasi 4 varian
    - Ablasi: (1) Stream_A saja (keypoint), (2) Stream_B saja (RGB), (3) Fusion concat, (4) Model lengkap cross-attention
    - Hasilkan tabel Markdown: Metode | Top-1 SD | Top-1 SI | Ukuran (MB) | Latensi (ms)
    - _Requirements: 19.2, 19.3_
    - **PJ: Gloria**

  - [ ] 13.3 Analisis error dan retraining
    - Confusion matrix per gloss; identifikasi kelas bermasalah
    - Analisis error: pola salah klasifikasi, korelasi fonologis
    - Jika diperlukan: retrain dengan bobot kelas atau tambahan data augmentasi
    - _Requirements: 19.5_
    - **PJ: Gloria**

  - [ ] 13.4 Validasi ONNX multi-platform
    - Jalankan `ONNXValidator` pada CPU/GPU; verifikasi konsistensi output
    - Uji ONNX pada perangkat mobile (Android/iOS emulator jika tersedia)
    - _Requirements: 14.6_
    - **PJ: Gloria**

- [ ] **14. Web Deploy — GitHub Pages & FastAPI**
  - _Requirements: 16.1–16.8, 17.1–17.6, 18.1–18.6_
  - **PJ: Gloria**

  - [ ] 14.1 Implementasi endpoint FastAPI lengkap
    - `/predict`: terima video, kembalikan `{gloss, confidence, top5, inference_time_ms}`
    - `/asr`: terima audio WAV, kembalikan transkrip
    - `/sentence`: terima sequence gloss, kembalikan kalimat Indonesia
    - `/translate`: terima teks Indonesia, kembalikan gloss sequence
    - `/ws`: WebSocket real-time inference
    - HTTP 400 untuk input tidak valid; HTTP 429 rate limit 60 req/menit/IP dengan `Retry-After`
    - _Requirements: 17.1–17.6_
    - **PJ: Gloria**

  - [ ] 14.2 Implementasi antarmuka web (HTML/JS) — GitHub Pages
    - Mode webcam (ONNX Runtime Web) + mode upload video (FastAPI)
    - Minta izin kamera `getUserMedia`; tampilkan prediksi + confidence di atas webcam feed
    - Jika confidence < 0.5: tampilkan indikator "tidak yakin"
    - Daftar 32+ gloss + ilustrasi; ringkasan sesi; tombol unduh log CSV
    - Antarmuka Bahasa Indonesia; label prototipe penelitian
    - _Requirements: 16.1–16.8, 18.1–18.6_
    - **PJ: Gloria**

  - [ ] 14.3 Deploy ke GitHub Pages
    - Build web static; push ke `gh-pages` branch
    - Uji multi-perangkat: Chrome ≥ 90, Firefox ≥ 88, Edge ≥ 90, mobile browser
    - _Requirements: 18.1_
    - **PJ: Gloria**

- [ ] **15. ASR — Whisper (A1–A3)**
  - _Requirements: A1–A3_
  - **PJ: Gloria**

  - [ ] 15.1 A1 — Whisper Zero-Shot (medium/large)
    - Jalankan Whisper medium/large-v3 tanpa fine-tuning pada audio kelas BISINDO
    - Hitung WER, CER, RTF
    - _Requirements: A1_
    - **PJ: Gloria**

  - [ ] 15.2 A2 — Whisper tiny fine-tune
    - Fine-tune Whisper-tiny pada korpus audio kelas
    - Evaluasi WER, CER, RTF; bandingkan dengan A1
    - _Requirements: A2_
    - **PJ: Gloria**

  - [ ] 15.3 A3 — Whisper base fine-tune
    - Fine-tune Whisper-base; evaluasi WER, CER, RTF
    - Pilih model terbaik (A1/A2/A3) untuk integrasi ke endpoint `/asr`
    - _Requirements: A3_
    - **PJ: Gloria**

- [ ] **16. Penyusun Kalimat BISINDO→Indonesia (B0, T1–T3)**
  - _Requirements: B0, T1–T3_
  - **PJ: Gloria**

  - [ ] 16.1 B0 — Penyusun berbasis aturan
    - Implementasi penyusun kalimat berdasarkan aturan tata bahasa BISINDO sederhana
    - Input: sequence gloss → Output: kalimat Indonesia
    - Evaluasi BLEU, chrF
    - _Requirements: B0_
    - **PJ: Gloria**

  - [ ] 16.2 T1 — GRU + Attention
    - Seq2seq GRU dengan mekanisme attention, train pada korpus teks
    - Evaluasi BLEU, chrF; bandingkan dengan B0
    - _Requirements: T1_
    - **PJ: Gloria**

  - [ ] 16.3 T2 — IndoT5-small fine-tune
    - Fine-tune IndoT5-small pada pasangan gloss→Indonesia
    - Evaluasi BLEU, chrF
    - _Requirements: T2_
    - **PJ: Gloria**

  - [ ] 16.4 T3 — mT5-small fine-tune
    - Fine-tune mT5-small; evaluasi BLEU, chrF
    - Pilih model terbaik (B0/T1/T2/T3) untuk integrasi ke endpoint `/sentence`
    - _Requirements: T3_
    - **PJ: Gloria**

- [ ] **17. Perbandingan 4 Modalitas**
  - _Requirements: evaluasi lintas-modal_
  - **PJ: Gloria**

  - [ ] 17.1 Buat tabel perbandingan 4 jalur (Pose, RGB, Fingerspell, ASR)
    - Metrik per modalitas: Top-1 (video), Accuracy huruf (fingerspell), WER/CER (ASR), BLEU/chrF (teks)
    - Laporkan latensi dan ukuran model tiap jalur
    - _Requirements: 19.6_
    - **PJ: Gloria**

  - [ ] 17.2 Analisis fusi lintas-modal
    - Uji kombinasi output 4 jalur (ensemble voting / confidence-weighted)
    - Laporkan apakah fusi meningkatkan akurasi dibanding modalitas tunggal terbaik
    - _Requirements: 19.3_
    - **PJ: Gloria**

- [ ] **18. Jembatan Antarmodal (MT0–MT3, A4, L1–L3)**
  - _Requirements: MT0–MT3, A4, L1–L3_
  - **PJ: Gloria**

  - [ ] 18.1 MT0 — Baseline machine translation (kamus bilingual)
    - Implementasi `L1_KamusTranslator`: gloss BISINDO → teks Indonesia via kamus
    - _Requirements: MT0, L1_
    - **PJ: Gloria**

  - [ ] 18.2 MT1–MT3 — NLLB-200 (Neural Machine Translation)
    - MT1: NLLB-200 distilled-600M zero-shot (BISINDO gloss → Indonesia)
    - MT2: Fine-tune NLLB-200 pada korpus paralel; evaluasi BLEU, chrF
    - MT3: NLLB-200 Indonesian → target bahasa isyarat lain (FSL, ASL) sebagai proof-of-concept
    - _Requirements: MT1–MT3, L2_
    - **PJ: Gloria**

  - [ ] 18.3 A4 — Whisper-Filipino untuk FSL-105
    - Integrasikan Whisper fine-tune Bahasa Filipina sebagai ASR untuk FSL-105
    - Evaluasi WER, CER, RTF pada audio Filipino
    - _Requirements: A4_
    - **PJ: Gloria**

  - [ ] 18.4 L3 — Animasi isyarat
    - Prototipe sederhana: render animasi/skeleton dari sequence gloss output model
    - _Requirements: L3_
    - **PJ: Gloria**

- [ ] **19. Docker & Azure Deployment**
  - _Requirements: deployment Docker, Azure_
  - **PJ: Gloria**

  - [ ] 19.1 Buat `docker-compose.yml` (web:8080 + api:7860)
    - Service `web`: Nginx serve static GitHub Pages di port 8080
    - Service `api`: FastAPI + ONNX Runtime di port 7860
    - Verifikasi `docker compose up` berjalan tanpa error
    - _Requirements: deployment_
    - **PJ: Gloria**

  - [ ] 19.2 Deploy ke Azure (bonus)
    - Deploy docker compose ke Azure Container Apps atau Azure App Service
    - Konfigurasi domain, SSL, dan environment variable
    - _Requirements: Azure bonus_
    - **PJ: Gloria**

- [ ] **20. Notebook Final & Dokumentasi Evaluasi**
  - _Requirements: 19.6, 20.4, 20.5_
  - **PJ: Gloria**

  - [ ] 20.1 Susun notebook final "Run All"
    - Notebook Jupyter/Colab yang menjalankan seluruh pipeline: data → training → evaluasi → export
    - Pastikan dapat dijalankan end-to-end dengan satu klik "Run All"
    - _Requirements: 20.4, 20.5_
    - **PJ: Gloria**

  - [ ] 20.2 Rilis dataset, model, dan kode ke publik
    - Rilis dataset sendiri (58 kelas) di Kaggle dan Hugging Face Datasets (CC BY 4.0)
    - Rilis model checkpoint terbaik (teacher + student) dan kode sumber
    - _Requirements: 19.5, 21.1, 21.2_
    - **PJ: Gloria**

- [x] **Checkpoint Fase 4:**
  - Evaluasi SD/SI/ablasi/error analysis selesai dan terdokumentasi
  - GitHub Pages live; semua endpoint FastAPI berjalan
  - ONNX tervalidasi multi-platform
  - Whisper A1–A3 selesai; model terbaik terintegrasi ke `/asr`
  - Penyusun kalimat B0/T1–T3 selesai; model terbaik terintegrasi ke `/sentence`
  - Tabel perbandingan 4 modalitas tersedia
  - Jembatan MT0–MT3, A4, L1–L3 selesai
  - Docker compose berjalan; Azure (bonus) selesai
  - Notebook "Run All" berjalan end-to-end

---

### FASE 5 — Laporan & Presentasi

- [ ] **21. Laporan IEEE & Slide Presentasi**
  - **PJ: Semua anggota**

  - [ ] 21.1 Tulis laporan penelitian format IEEE
    - Abstrak, Pendahuluan, Related Work, Metodologi, Eksperimen & Hasil, Kesimpulan
    - Sertakan tabel ablasi, perbandingan 4 modalitas, dan kurva training
    - _Requirements: 19.6_
    - **PJ: Semua anggota**

  - [ ] 21.2 Buat slide presentasi demo
    - Demo live sistem (webcam → prediksi gloss → kalimat Indonesia)
    - Tampilkan hasil eksperimen utama (E0–E7, I1–I3, A1–A3, T1–T3)
    - **PJ: Semua anggota**

  - [ ] 21.3 Buat README.md final (Bahasa Indonesia dan Bahasa Inggris)
    - Seksi: instalasi, persiapan data, training, evaluasi, deployment
    - Dokumentasikan URL bobot pretrained, link GitHub Pages, link Docker Hub
    - _Requirements: 8.2, 20.1_
    - **PJ: Semua anggota**

- [x] **Checkpoint Final:**
  - Seluruh test suite (unit, integrasi, smoke test) pass
  - Notebook "Run All" selesai tanpa error
  - Laporan IEEE draft final selesai
  - Slide dan demo siap
  - Semua artefak (dataset, model, kode, notebook) dirilis publik

---

## Notes

- **Status tasks:** `[ ]` belum dikerjakan, `[~]` sedang berjalan, `[x]` selesai
- Setiap task merujuk ke requirements/eksperimen spesifik untuk keterlacakan
- **86 keypoint:** 21 tangan kiri + 21 tangan kanan + 33 pose + 11 wajah selektif (bukan 543 node penuh)
- **T_max = 64 frame** (uniform sampling); ONNX input video `[1, 64, 86, 3]`, output `[1, 32]`
- **Fingerspell ONNX:** input `[1, 3, 224, 224]` → output `[1, 26]`
- **Split SD:** 60/10/30 (train/val/test); **Split SI:** leave-one-signer-out 5-fold
- **Dataset sendiri:** 58 kelas × 3 perekam × 18 pengulangan = ≥3132 sampel multimodal
- **Optuna:** 20 trial untuk model video (E-series), 12 trial untuk ejaan jari (I-series)
- **Whisper:** A1 zero-shot, A2 tiny fine-tune, A3 base fine-tune; metrik WER, CER, RTF
- **Teks:** B0 aturan, T1 GRU+attention, T2 IndoT5-small, T3 mT5-small; metrik BLEU, chrF
- **Deployment:** docker compose (web:8080 + api:7860) + GitHub Pages + Azure (bonus)
- **FastAPI endpoints:** `/predict`, `/asr`, `/sentence`, `/translate`, `/ws`
- Seed (default: 42) diterapkan pada semua operasi stokastik untuk reprodusibilitas
- Konfigurasi terpusat via YAML — tidak ada parameter hardcoded di kode sumber

---

## Task Dependency Graph

```json
{
  "phases": [
    {
      "id": 0,
      "name": "Setup",
      "tasks": ["1.1", "1.2", "1.3"]
    },
    {
      "id": 1,
      "name": "Data — Akuisisi & Split",
      "depends_on": [0],
      "tasks": ["2.1", "2.2", "2.3"]
    },
    {
      "id": 2,
      "name": "Data — Keypoint 86 node",
      "depends_on": [1],
      "tasks": ["3.1", "3.2", "3.3", "3.4"]
    },
    {
      "id": 3,
      "name": "Data — RGB Token VideoMAE",
      "depends_on": [1],
      "tasks": ["4.1", "4.2"]
    },
    {
      "id": 4,
      "name": "Data — Ejaan Jari & Teks & Audio",
      "depends_on": [1],
      "tasks": ["5.1", "5.2", "6.1", "6.2", "7.1", "7.2", "7.3", "7.4"]
    },
    {
      "id": 5,
      "name": "Modeling — Augmentasi",
      "depends_on": [2, 3],
      "tasks": ["8.1", "8.2", "8.3", "8.4"]
    },
    {
      "id": 6,
      "name": "Modeling — E0–E3 (Pose)",
      "depends_on": [5],
      "tasks": ["9.1", "9.2", "9.3", "9.4"]
    },
    {
      "id": 7,
      "name": "Modeling — E4–E5 (Fusion)",
      "depends_on": [6, 3],
      "tasks": ["9.5", "9.6"]
    },
    {
      "id": 8,
      "name": "Modeling — E6–E7 (Distilasi & ONNX)",
      "depends_on": [7],
      "tasks": ["9.7", "9.8"]
    },
    {
      "id": 9,
      "name": "Modeling — Fingerspell I1–I3",
      "depends_on": [4],
      "tasks": ["10.1", "10.2", "10.3"]
    },
    {
      "id": 10,
      "name": "Modeling — Optuna Tuning",
      "depends_on": [6, 9],
      "tasks": ["11.1", "11.2"]
    },
    {
      "id": 11,
      "name": "Modeling — FSL X1–X4",
      "depends_on": [6, 4],
      "tasks": ["12.1", "12.2", "12.3", "12.4"]
    },
    {
      "id": 12,
      "name": "Eval — Video Model",
      "depends_on": [8, 10],
      "tasks": ["13.1", "13.2", "13.3", "13.4"]
    },
    {
      "id": 13,
      "name": "Deploy — FastAPI & Web",
      "depends_on": [8, 9],
      "tasks": ["14.1", "14.2", "14.3"]
    },
    {
      "id": 14,
      "name": "Eval — ASR Whisper",
      "depends_on": [4],
      "tasks": ["15.1", "15.2", "15.3"]
    },
    {
      "id": 15,
      "name": "Eval — Penyusun Kalimat",
      "depends_on": [4],
      "tasks": ["16.1", "16.2", "16.3", "16.4"]
    },
    {
      "id": 16,
      "name": "Eval — Perbandingan 4 Modalitas",
      "depends_on": [12, 13, 14, 15],
      "tasks": ["17.1", "17.2"]
    },
    {
      "id": 17,
      "name": "Jembatan Antarmodal",
      "depends_on": [15, 11],
      "tasks": ["18.1", "18.2", "18.3", "18.4"]
    },
    {
      "id": 18,
      "name": "Docker & Azure",
      "depends_on": [13],
      "tasks": ["19.1", "19.2"]
    },
    {
      "id": 19,
      "name": "Notebook Final & Rilis",
      "depends_on": [16, 17, 18],
      "tasks": ["20.1", "20.2"]
    },
    {
      "id": 20,
      "name": "Laporan & Presentasi",
      "depends_on": [19],
      "tasks": ["21.1", "21.2", "21.3"]
    }
  ]
}
```
