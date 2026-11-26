# RINGKASAN MATERI PRESENTASI MINGGU 1 (SIAP COPY-PASTE KE SLIDE)
**Proyek:** SignBridge ID–PH (BISINDO ↔ FSL Multimodal Classroom Bridge)  
**Mata Kuliah:** Machine Learning (Semester 5) — Projek 1  
**Format:** Teks Ringkas, Poin Inti, dan Tabel Siap Salin ke PowerPoint / Canva / Google Slides

---

## SLIDE 1: JUDUL & ANGGOTA TIM

* **Judul Proyek:** SignBridge ID–PH
* **Sub-judul:** Jembatan Komunikasi Multimodal Real-Time Bahasa Isyarat Indonesia (BISINDO) & Filipina (FSL) Berbasis Browser Edge
* **Mata Kuliah:** Machine Learning — Semester 5 (Projek 1)
* **Tim Pengembang:**
  1. **Farrel** — *Lead Data & Preprocessing (Kontrak 1, 3, & 4)*
  2. **Jonnathan** — *Lead Model Architecture & Training (M0, M1, I1)*
  3. **Gloria (KarinaGlo)** — *Lead Systems, Evaluation, ONNX & Frontend PWA (Kontrak 2, 5, 6)*

---

## SLIDE 2: LATAR BELAKANG & MASALAH

* **Tiga Masalah Utama:**
  1. **Hambatan Komunikasi Kelas Inklusif:** Kurangnya juru bahasa isyarat di sekolah reguler membatasi interaksi dua arah siswa Tuli dengan guru dan teman dengar (Target SDG 4.5 & 4.a).
  2. **Kelemahan AI Cloud Konvensional:** Mengirim video mentah ke server GPU eksternal memicu latensi tinggi (>300 ms), biaya sewa server mahal, dan risiko privasi video siswa.
  3. **Isolasi Isyarat Regional ASEAN:** Belum ada sistem translasi antarnegara yang menghubungkan BISINDO (Indonesia) dan FSL (Filipino Sign Language).
* **Solusi SignBridge:** Memindahkan seluruh inferensi AI langsung ke peramban (*client-side browser edge*) menggunakan MediaPipe Holistic + ONNX WebAssembly tanpa server GPU.

---

## SLIDE 3: TUJUAN & TARGET SPESIFIKASI TEKNIS

* **Tujuan Utama:**
  * Membangun aplikasi web penerjemah isyarat 2-arah real-time yang ringan dan berjalan tanpa instalasi.
  * Menghilangkan ketergantungan server GPU dengan inferensi lokal di browser via ONNX Runtime Web.
  * Menjamin paritas matematis 100% antara preprocessing Python dan inferensi JavaScript.
* **Target Spesifikasi Rekayasa (Engineering Targets):**
  * **Latensi Inferensi Web:** $\le 50\text{ ms}$ (setara $\ge 20\text{ FPS}$ real-time).
  * **Ukuran File Model ONNX:** $< 10\text{ MB}$ (ramah koneksi internet sekolah).
  * **Toleransi Paritas Numerik:** Selisih output PyTorch vs JavaScript $< 1\times 10^{-4}$.
  * **Cakupan Input:** 4 Modalitas (Video, Citra, Suara, Teks).

---

## SLIDE 4: DIAGRAM ARSITEKTUR SISTEM (2 LAPIS)

* **Lapis 1 — Client Browser Edge (PWA — Zero Cloud Inference):**
  * Input: Kamera (30 FPS), Mikrofon (Audio), Teks.
  * Vision Front-End: MediaPipe Holistic (543 landmark WebGL 2.0).
  * Preprocessing: Normalisasi bahu & resampling seragam 64 frame.
  * Model Engine: ONNX Runtime Web (WASM SIMD) menjalankan model M0 (5,46 MB).
  * Output: Web Speech API (TTS Suara id-ID) dan tampilan teks layar.
* **Lapis 2 — Backend Relay & Jembatan ASEAN (FastAPI Server):**
  * REST API Fallback (`POST /predict` & `POST /asr`).
  * WebSocket Room (`/ws/{room}`): Relay interaksi kelas 2-arah (Rate limited 60 req/menit).
  * Jembatan BISINDO ↔ FSL: Lapis 1 Kamus Konsep Semantik (`concepts.csv`).

---

## SLIDE 5: DIAGRAM PIPELINE KOMPUTASI ML DETAIL

* **Alur Transformasi Data (Total Waktu: 34,4 ms / ~29 FPS):**
  1. **Video Stream:** Kamera laptop 640x480 pada 30 FPS.
  2. **MediaPipe Holistic:** Ekstraksi 543 titik skeletal mentah (Pose, Hand, Face).
  3. **Filter 86 Node (Kontrak 1):** 11 torso atas, 21 tangan kiri, 21 tangan kanan, 33 wajah ekspresif.
  4. **Normalisasi Bahu (Kontrak 3):** Translasi titik tengah bahu & skala jarak antar-bahu:
     $$\mathbf{x}_{\text{norm}} = \frac{\mathbf{x} - \frac{1}{2}(\text{bahu}_L + \text{bahu}_R)}{\max(\|\text{bahu}_L - \text{bahu}_R\|_2, 10^{-6})}$$
  5. **Temporal Resampling:** Sliding buffer diinterpolasi linear ke ukuran tepat $[1, 64, 86, 3]$.
  6. **Inferensi ONNX Web (Kontrak 2):** Model M0 Student Transformer memproses logits $[1, 32]$ dalam **11,2 ms**.
  7. **Decision Boundary:** Pengecekan batas ruang isyarat (Signing Space), Top-1 Conf $\ge 0.45$, Margin $\ge 0.10$.
  8. **Output:** Teks kata akumulatif & Text-to-Speech otomatis.
  *(Jalur alternatif: Tangan diam dialihkan ke Hand Crop 224x224 [Kontrak 4] $\to$ Model Abjad A–Z [Kontrak 5]).*

---

## SLIDE 6: ARSITEKTUR 4 MODALITAS INPUT

1. **Modalitas 1 (Video):** Isyarat kata dinamis (32 kata WL-BISINDO) via sekuens 86 koordinat tubuh (Model: M0 Student Transformer & M1 ST-GCN).
2. **Modalitas 2 (Citra):** Ejaan abjad statis (26 huruf A–Z) via crop tangan 224x224 piksel (Model: MobileNetV3 I1 & Heuristik Geometri).
3. **Modalitas 3 (Audio):** Pengenalan suara guru (ASR) via Web Speech API & Whisper.
4. **Modalitas 4 (Teks):** Rekonstruksi kata isyarat menjadi kalimat alami bahasa Indonesia via Rule Template & IndoT5.

---

## SLIDE 7: 6 KONTRAK ANTARMUKA TIM

* **Kontrak 1 (Topologi 86 Node):** Reduksi 543 titik MediaPipe menjadi 86 node fungsional (`signbridge/constants.py`).
* **Kontrak 2 (I/O Model ONNX):** Input `[B, 64, 86, 3]` float32 $\to$ Logits `[B, 32]`, ukuran biner $< 10\text{ MB}$.
* **Kontrak 3 (Paritas Preprocessing):** Rumus normalisasi bahu dan resampling Python ≡ JavaScript (selisih $< 1\times 10^{-5}$).
* **Kontrak 4 (Paritas Hand Crop):** Pemotongan kotak tangan padding 25% ke 224x224 piksel.
* **Kontrak 5 (Model Citra Abjad):** Input citra `[B, 3, 224, 224]` float32 $\to$ Logits 26 abjad.
* **Kontrak 6 (Backend Hibrida):** Endpoint REST API fallback dan WebSocket relay kelas dengan pembatas laju.

---

## SLIDE 8: INVENTARIS DATASET MINGGU 1

| Kategori Data | Nama Dataset | Jumlah Sampel | Status Riil di Disk |
| :--- | :--- | :--- | :--- |
| **Video Isyarat** | WL-BISINDO Video | 1.600 klip (32 kata, 50 klip/kata) | Manifest CSV valid; 5 Signer (`SIGNER0`–`4`) |
| **Citra Abjad** | Mendeley BISINDO Alphabet | 4.466 gambar (A–Z) | Dataset citra tangan ejaan jari |
| **Audio Suara** | FLEURS Indonesian | 3.616 metadata ucapan | Korpus suara percakapan Indonesia |
| **Teks Kalimat** | Parallel Gloss-to-Sentence | 305 pasang kalimat | 170 train, 30 val, 105 test manual |
| **Korpus Teks** | Tatoeba Indonesian | 28.418 kalimat | Teks monolingual untuk sintesis kalimat |

---

## SLIDE 9: CAPAIAN & DELIVERABLES MINGGU 1

1. **Fondasi Repositori & Testing Paritas:** Setup repositori Git bersih dengan CI testing (`pytest` 18/18 lulus, paritas JavaScript 100% lulus).
2. **Pelatihan 2 Model Baseline Isyarat Video:**
   * Model M0 (Student Pose Transformer, 1,33 juta parameter) berhasil dilatih.
   * Model M1 (Spatial-Temporal GCN 4-blok, 1,48 juta parameter) berhasil dilatih.
3. **Ekspor & Validasi ONNX Runtime Web:** Model M0 sukses diekspor ke `student.onnx` (5,46 MB) dengan perbedaan terhadap PyTorch hanya $2.4\times 10^{-6}$.
4. **Prototipe Web PWA Berjalan:** Aplikasi web live terintegrasi MediaPipe WASM, WebGL 2.0, ONNX Web, dan TTS otomatis berjalan lancar di browser lokal pada kecepatan 30 FPS.

---

## SLIDE 10: HASIL EKSPERIMEN & LATENSI BROWSER

* **Tabel Perbandingan Kinerja Model:**

| Parameter Evaluasi | M0: Student Transformer | M1: ST-GCN Baseline |
| :--- | :--- | :--- |
| **Arsitektur Model** | 2-Layer Transformer Encoder | 4-Blok Spatio-Temporal Graph Conv |
| **Jumlah Parameter** | 1.335.872 (1,33 Juta) | 1.481.248 (1,48 Juta) |
| **Epoch Pelatihan** | 48 Epoch (Early stop) | 79 Epoch |
| **SD Validation Accuracy** | **97.78%** | **98.89%** |
| **SD Test Accuracy** | **99.13%** (456/460 benar) | **99.13%** (456/460 benar) |
| **Latensi Inferensi Web** | **11,2 ms** (Sangat Cepat) | ~18,5 ms (Est.) |
| **Total Waktu Pipeline E2E** | **34,4 ms (~29.1 FPS)** | ~42 ms (~24 FPS) |

* **Profil Waktu Eksekusi Web M0:** MediaPipe (22,4 ms) + Preprocessing (0,8 ms) + ONNX WASM (11,2 ms) + Post-Processing (< 0,5 ms) = **34,4 ms**.

---

## SLIDE 11: TEMUAN KRITIS & AUDIT INTEGRITAS ML

*Tunjukkan transparansi ilmiah dan kedewasaan analisis tim:*
1. **Signer Leakage (Data Split):** Akurasi 99.13% berasal dari *Signer-Dependent split* di mana kelima penutur isyarat yang sama muncul di train dan test. Model menghafal ciri fisik penutur sehingga performa menurun saat dicoba pengguna baru via webcam (*domain shift*).
2. **Kegagalan Model Abjad (I1 MobileNetV3):** Model konvolusi abjad menghasilkan akurasi uji **3.85%** (tebakan acak $1/26$) akibat training collapse. Frontend saat ini menggunakan safety fallback berupa heuristik geometri sendi jari.
3. **Kuantisasi Nyata & Korpus Teks:** File `student_int8.onnx` masih berupa salinan FP32 (5,46 MB, belum terkompresi ke ~1,4 MB), dan data kalimat paralel masih minim (305 pasang).

---

## SLIDE 12: ROADMAP & RENCANA AKSI MINGGU 2 (P0)

* **Prioritas P0 (Remedi Kritis Minggu 2):**
  * Menerapkan partisi **Leave-One-Signer-Out (LOSO)**: Signer 1–3 train, Signer 0 val, Signer 4 sebagai unseen test set.
  * Menambahkan **Augmentasi Koordinat 3D**: Random scaling (85%–115%), joint coordinate jitter, rotasi bahu $\pm 10^\circ$, dan temporal speed perturbation.
  * Melatih ulang M0 pada skema LOSO (target akurasi Signer-Independent nyata $\ge 82\%$).
  * Melatih ulang MobileNetV3 untuk abjad A–Z dengan AdamW dan learning rate stabil (target akurasi $\ge 88\%$).
* **Prioritas P1 (Minggu 3):** Kuantisasi dinamis INT8 nyata (~1,4 MB) dan sintesis 5.000 korpus kalimat untuk fine-tuning IndoT5.
* **Prioritas P2 & P3 (Minggu 4+):** Uji coba langsung pada siswa Tuli dan integrasi leksikon FSL.

---

## SLIDE 13: PEMBAGIAN TUGAS TIM PENGEMBANG

* **Farrel (Lead Data & Preprocessing):**
  * Ekstraksi massal keypoint MediaPipe Holistic ke format NPZ.
  * Pemeliharaan Kontrak 1 (Topologi 86 node) dan Kontrak 4 (Hand Crop 224x224).
  * Pengembangan modul augmentasi spasial-temporal 3D dan normalisasi bahu (Kontrak 3).
  * Kurasi korpus teks paralel dan metadata fonologi isyarat.
* **Jonnathan (Lead Model Architecture & Training):**
  * Pelatihan ulang model M0 Student Transformer pada skema partisi LOSO.
  * Eksperimen dan optimasi model M1 ST-GCN.
  * Pelatihan ulang model citra abjad MobileNetV3 (I1).
  * Optimasi loss function label smoothing dan learning rate scheduler.
* **Gloria (KarinaGlo) (Lead Systems, Evaluation, ONNX & Frontend PWA):**
  * Benchmarking paritas numerik PyTorch vs ONNX Runtime (Kontrak 2 & 3).
  * Penerapan kuantisasi INT8 dynamic pada model ONNX.
  * Integrasi runtime ONNX Web WASM dan MediaPipe WebGL 2.0 di browser.
  * Pengembangan antarmuka web PWA responsif ruang kelas 2-arah.
  * Server backend FastAPI, WebSocket relay (Kontrak 6), dan modul Speech/NLP (Whisper & IndoT5).

---

## SLIDE 14: KESIMPULAN & PENUTUP

* **Kesimpulan:** Fondasi rekayasa perangkat lunak, testing otomatis paritas Python-JS, dan arsitektur browser murni telah berhasil dibangun dengan performa **30 FPS real-time**.
* **Langkah Selanjutnya:** Menyelesaikan retraining model M0 dengan skema LOSO dan memperbaiki model abjad agar siap diuji langsung di ruang kelas nyata.
* **Demo Prototipe:** Sistem web lokal aktif di port 8000 dan siap didemonstrasikan.
* **Sesi Diskusi:** Membuka ruang tanya jawab dan masukan dari dosen penilai.

