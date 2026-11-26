# LAPORAN KEMAJUAN PROYEK (PROGRES MINGGU 1)
## SignBridge ID–PH: Jembatan Komunikasi Multimodal Real-Time Bahasa Isyarat Indonesia (BISINDO) & Filipina (FSL) Berbasis Browser Edge

* **Mata Kuliah:** Machine Learning (Semester 5) — Projek 1
* **Program Studi:** Teknik Informatika / Ilmu Komputer
* **Branch Git Aktif:** `feature/field-test-readiness` (Commit: `3a99e96`)
* **Tim Pengembang:**
  1. **Farrel** — *Lead Data & Preprocessing*
  2. **Jonnathan** — *Lead Model Architecture & Training*
  3. **Gloria (KarinaGlo)** — *Lead Systems, Evaluation, ONNX & Frontend PWA*

---

## RINGKASAN EKSEKUTIF

Laporan ini mendokumentasikan hasil pekerjaan, evaluasi teknis, dan capaian rekayasa minggu pertama pengembangan sistem **SignBridge ID–PH**. Fokus utama proyek ini adalah membangun sistem penerjemahan bahasa isyarat dua arah berbasis peramban web (*browser-first edge inference*) yang beroperasi secara mandiri tanpa memerlukan instalasi aplikasi native maupun ketergantungan pada server GPU cloud eksternal.

Pada minggu pertama, tim telah berhasil menyelesaikan:
1. **Arsitektur Sistem & Kontrak Antarmuka:** Penetapan 6 Kontrak Antarmuka ketat yang menjamin paritas komputasi $100\%$ antara Python dan JavaScript di browser.
2. **Pipeline Ekstraksi Fitur:** Seleksi 86 titik fungsional dari 543 landmark MediaPipe Holistic, algoritma normalisasi bahu (*shoulder normalization*), dan interpolasi temporal seragam menjadi 64 frame.
3. **Pelatihan Model Baseline Isyarat Video:** Keberhasilan pelatihan model **M0 (Student Pose Transformer, 1,33 juta parameter)** dan **M1 (ST-GCN, 1,48 juta parameter)** dengan akurasi uji awal mencapai $99.13\%$ pada skema *Signer-Dependent*.
4. **Ekspor & Deployment Browser:** Konversi model M0 ke format ONNX Runtime Web (5,46 MB) dengan latensi inferensi sangat rendah sebesar **11,2 ms** di browser dan total latensi pipeline end-to-end sebesar **34,4 ms (~29.1 FPS)**.
5. **Audit Integritas ML:** Mengidentifikasi masalah kebocoran data penutur (*signer leakage*) pada evaluasi awal dan kegagalan konvergensi model abjad konvolusional ($3.85\%$), yang langsung dijadwalkan untuk diremediasi melalui pelatihan *Leave-One-Signer-Out (LOSO)* pada minggu kedua.

---

## BAB I: PENDAHULUAN

### 1.1 Latar Belakang
Bahasa isyarat merupakan bahasa alami utama bagi komunitas Tuli dan tunarungu. Di lingkungan pendidikan inklusif, siswa Tuli kerap menghadapi tantangan komunikasi dua arah dengan guru dan rekan dengar akibat keterbatasan ketersediaan Juru Bahasa Isyarat (JBI) berdedikasi. Solusi penerjemah berbasis kecerdasan buatan (AI) yang ada saat ini umumnya mengandalkan server GPU berbasis cloud, yang menimbulkan tiga kendala fundamental:
* **Latensi Tinggi:** Transmisi video kontinu melalui jaringan internet menimbulkan latensi $> 300\text{ ms}$, mengganggu kelancaran percakapan.
* **Biaya Server Mahal:** Pemrosesan video deep learning pada GPU cloud memerlukan biaya infrastruktur tinggi yang sulit diadopsi sekolah luar biasa (SLB) atau sekolah inklusif berbiaya rendah.
* **Isu Privasi Siswa:** Pengiriman data rekaman wajah dan tubuh siswa ke server eksternal rentan melanggar regulasi perlindungan privasi data anak.

SignBridge dirancang untuk mengatasi hambatan tersebut dengan memindahkan seluruh komputasi machine learning langsung ke peramban (*client-side edge*) menggunakan **MediaPipe Holistic (WebGL 2.0)** dan **ONNX Runtime Web (WebAssembly SIMD)**.

### 1.2 Rumusan Masalah
1. Bagaimana merancang pipeline ekstraksi fitur gerak tubuh yang efisien sehingga dapat dieksekusi secara real-time pada CPU laptop sekolah tanpa kartu grafis dedicated?
2. Bagaimana membangun arsitektur model deep learning berukuran ringkas ($< 10\text{ MB}$) yang mampu mengenali kosakata isyarat dengan akurasi tinggi?
3. Bagaimana menjamin konsistensi numerik (paritas) antara algoritma pra-pemrosesan di Python saat pelatihan dan JavaScript saat inferensi langsung di browser?

### 1.3 Tujuan Proyek
* Mengembangkan aplikasi web Progressive Web App (PWA) penerjemah bahasa isyarat BISINDO secara real-time.
* Mengintegrasikan 4 modalitas interaksi kelas inklusif: Video kata isyarat, Citra ejaan jari, Audio suara guru (ASR), dan Teks kalimat alami.
* Menghasilkan model deep learning teroptimasi dengan latensi inferensi di bawah 50 milidetik.

### 1.4 Batasan Proyek & Target Spesifikasi Rekayasa
* **Target Latensi Total E2E:** $\le 50\text{ ms}$ ($\ge 20\text{ FPS}$).
* **Batas Ukuran Model ONNX:** $< 10\text{ MB}$ (target terkuantisasi: $\approx 1,4\text{ MB}$).
* **Toleransi Paritas Numerik:** $\|\text{PyTorch}(x) - \text{ONNX}(x)\|_{\infty} < 1\times 10^{-4}$.
* **Kosakata Isyarat Dinamis Awal:** 32 kata ruang kelas dari dataset WL-BISINDO.
* **Kosakata Ejaan Jari:** 26 huruf alfabet Latin (A–Z).

---

## BAB II: ARSITEKTUR SISTEM & METODOLOGI REKAYASA

### 2.1 Paradigma Browser-First Edge Computing
Berbeda dengan sistem cloud konvensional, SignBridge mengusung filosofi **Zero-Cloud-Inference**. Video webcam pengguna ditangkap pada resolusi 640x480 (30 FPS), diproses oleh engine WebGL MediaPipe untuk mengekstrak titik koordinat tubuh, dan langsung diumpankan ke model neural network melalui WebAssembly (WASM). Frame video tidak pernah dikirimkan keluar dari memori lokal perangkat pengguna.

### 2.2 Arsitektur Sistem Dua Lapis
Sistem dibagi menjadi dua domain fungsional:
1. **Lapis 1 — Client Browser Edge (PWA Frontend):**
   * *Sensory Acquisition:* Webcam input, Audio microphone input, dan Text input.
   * *Vision Front-End:* MediaPipe Holistic WASM/WebGL.
   * *Coordinate Normalizer:* Translasi titik tengah bahu dan penskalaan jarak bahu.
   * *Inference Engine:* ONNX Runtime Web (WASM SIMD 1-thread) mengeksekusi model M0.
   * *Decision Logic:* Two-tier thresholding dan batas ruang isyarat (*Signing Space Guard*).
   * *Multimodal Output:* Web Speech API (suara sintetis bahasa Indonesia) dan tampilan teks layar.
2. **Lapis 2 — Backend Relay & Jembatan ASEAN (FastAPI Server):**
   * REST API Fallback (`POST /predict` dan `POST /asr`).
   * WebSocket relay interaktif dua arah (`/ws/{room}`) dengan *rate-limiter* 60 request/menit.
   * Jembatan Konsep Semantik BISINDO ↔ FSL (`data/bridge/concepts.csv`).

### 2.3 Empat Modalitas Ruang Kelas
* **Modalitas 1 (Video):** 32 kata isyarat dinamis berbasis rangkaian sendi tubuh skeletal.
* **Modalitas 2 (Citra):** 26 huruf ejaan jari statis (fingerspelling A–Z) dari pemotongan kotak tangan (*hand crop*) 224x224 piksel.
* **Modalitas 3 (Audio):** Penangkapan instruksi suara guru menggunakan Web Speech API dan fine-tuning Whisper ASR.
* **Modalitas 4 (Teks):** Rekonstruksi deretan kata isyarat menjadi kalimat alami bahasa Indonesia.

### 2.4 Standarisasi 6 Kontrak Antarmuka Tim
Untuk menjamin kode dari seluruh anggota tim terintegrasi tanpa konflik, diterapkan 6 kontrak ketat:
* **Kontrak 1 (Topologi 86 Node):** Mengurangi 543 titik MediaPipe menjadi 86 node terstandarisasi (`signbridge/constants.py`).
* **Kontrak 2 (I/O Model Video ONNX):** Input wajib `float32 [1, 64, 86, 3]` dan output logits `float32 [1, 32]` (`web/model/student.onnx`).
* **Kontrak 3 (Paritas Preprocessing):** Rumus normalisasi dan resampling 64 frame di `features.py` (Python) wajib identik dengan `features.js` (JavaScript) dengan toleransi selisih $< 1\times 10^{-5}$.
* **Kontrak 4 (Paritas Hand Crop):** Pemotongan kotak tangan dengan padding persegi 25% ke ukuran 224x224 (`crop.py` ≡ `handcrop.js`).
* **Kontrak 5 (Model Citra Abjad ONNX):** Input citra `float32 [1, 3, 224, 224]` dan output 26 kelas abjad (`web/model/fingerspell.onnx`).
* **Kontrak 6 (Backend Hibrida FastAPI):** Spesifikasi endpoint `/predict`, `/asr`, dan relay `/ws/{kode}` di `server/app.py`.

---

## BAB III: MANAJEMEN DATASET & PIPELINE PREPROCESSING

### 3.1 Inventarisasi Dataset Riil
Audit fisik pada repositori memvalidasi status dataset berikut:

| Kategori Data | Nama Dataset & Jalur | Sampel Terkatalog | Keterangan & Karakteristik Data |
| :--- | :--- | :--- | :--- |
| **Video Kata** | WL-BISINDO (`data/manifest_wl_bisindo.csv`) | 1.600 klip video | 32 kelas kosakata, persis 50 klip/kelas, 5 penutur (`SIGNER0`–`4`). |
| **Citra Abjad** | Mendeley BISINDO (`data/raw/image/`) | 4.466 citra | 26 kelas abjad statis A–Z untuk ejaan jari. |
| **Audio Transkrip**| FLEURS ID (`data/audio/fleurs/id_id/`) | 3.616 rekaman | Manifest teks transkripsi percakapan bahasa Indonesia. |
| **Teks Paralel** | Parallel Corpus (`data/text/parallel_sentences/`) | 305 pasang | Pasangan sekuens gloss isyarat terhadap kalimat bahasa Indonesia. |
| **Teks Monolingual**| Tatoeba (`data/text/monolingual/ind_sentences.tsv`) | 28.418 kalimat | Korpus kalimat bahasa Indonesia untuk ekspansi data sintetis. |

### 3.2 Seleksi Topologi 86 Titik Kanonis
Output bawaan MediaPipe Holistic menghasilkan 543 titik yang terlalu berat untuk diproses berulang pada memori browser. Tim mereduksinya menjadi 86 titik fungsional:
* **Tubuh Bagian Atas (11 Titik):** Hidung (0), Bahu Kiri/Kanan (11, 12), Siku (13, 14), Pergelangan Tangan (15, 16), Pinggul (23, 24), dan Titik Jari Pose (17, 18). Titik kaki dan lutut dibuang.
* **Tangan Kiri (21 Titik):** Seluruh sendi jari tangan kiri (0–20).
* **Tangan Kanan (21 Titik):** Seluruh sendi jari tangan kanan (0–20).
* **Wajah Ekspresif (33 Titik):** Kontur bibir, alis, dan mata yang berfungsi sebagai penanda gramatikal non-manual (*Non-Manual Markers* / NMM).

Total fitur per frame: $86 \times 3\text{ dimensi } (X, Y, Z) = 258\text{ nilai floating-point}$.

### 3.3 Normalisasi Spasial & Resampling Temporal
1. **Translasi Pusat Bahu:**
   $$\text{center} = \frac{\mathbf{p}_{\text{bahu\_kiri}} + \mathbf{p}_{\text{bahu\_kanan}}}{2}, \quad \mathbf{p}' = \mathbf{p} - \text{center}$$
2. **Penskalaan Jarak Bahu (Scale Invariance):**
   $$\text{scale} = \|\mathbf{p}_{\text{bahu\_kiri}} - \mathbf{p}_{\text{bahu\_kanan}}\|_2, \quad \mathbf{p}_{\text{norm}} = \frac{\mathbf{p}'}{\max(\text{scale}, 10^{-6})}$$
3. **Resampling Temporal Seragam:** Sekuens gerakan dinamis dengan durasi variabel diinterpolasi secara linear menjadi tepat **64 frame** seragam, menghasilkan tensor siap model berdimensi $[1, 64, 86, 3]$.

---

## BAB IV: HASIL EKSPERIMEN BASELINE & EVALUASI

### 4.1 Pelatihan Model Baseline Isyarat Video
Pada minggu pertama, dua arsitektur deep learning dilatih untuk klasifikasi 32 kata isyarat:
1. **Model M0 (Student Pose Transformer):** Proyeksi linear 258 ke 128 dimensi, sinusoidal positional encoding, 2 layer Transformer Encoder (4 attention heads, feedforward dimension 256), global pooling temporal, dan linear classifier 32 kelas. Total parameter: **1.335.872 (1,33 M)**.
2. **Model M1 (Spatial-Temporal Graph ConvNet / ST-GCN):** 4 blok konvolusi graf spasial-temporal berbasis graf anatomis 86 titik dengan matriks ketetanggaan 3-partisi. Total parameter: **1.481.248 (1,48 M)**.

### 4.2 Perbandingan Metrik Evaluasi

| Parameter Metrik | M0: Student Pose Transformer | M1: ST-GCN Baseline |
| :--- | :--- | :--- |
| **Total Parameter** | 1.335.872 parameter | 1.481.248 parameter |
| **Ukuran File Bobot (FP32)** | 5,46 MB | ~5,9 MB |
| **Epoch Pelatihan** | 48 Epoch (Early stopping) | 79 Epoch |
| **Validation Loss** | 0.0812 | 0.0744 |
| **Validation Accuracy (SD)** | **97.78%** | **98.89%** |
| **Test Accuracy (SD)** | **99.13%** (456/460 benar) | **99.13%** (456/460 benar) |
| **Latensi Inferensi Web** | **11,2 ms** | ~18,5 ms |

### 4.3 Profil Latensi Riil di Web Browser (Chrome Desktop / Intel CPU)
Pengukuran profil waktu eksekusi langsung pada browser menunjukkan efisiensi luar biasa dari model M0:
* **Ekstraksi MediaPipe Holistic (WebGL 2.0):** $22,4\text{ ms} \pm 3,1\text{ ms}$
* **Normalisasi Bahu & Sliding Buffer:** $0,8\text{ ms}$
* **Inferensi ONNX WebAssembly (SIMD):** $11,2\text{ ms} \pm 1,8\text{ ms}$
* **Post-Processing & Decision Boundary:** $< 0,5\text{ ms}$
* **Total Latensi Satu Siklus:** **$34,4\text{ ms}$ ($\approx 29.1\text{ FPS}$)** $\to$ Melebihi target spesifikasi rekayasa ($\le 50\text{ ms}$).

### 4.4 Verifikasi Ekspor ONNX & Paritas Numerik
Model M0 berhasil diekspor ke `web/model/student.onnx`. Melalui script uji otomatis `tests/test_contract_2_model_io.py`, verifikasi paritas membuktikan bahwa selisih absolut maksimum antara output logits PyTorch dan output ONNX Runtime berada di angka $2.4\times 10^{-6}$ (jauh di bawah batas toleransi $1\times 10^{-4}$).

---

## BAB V: AUDIT INTEGRITAS ML & TEMUAN KRITIS

Sebagai bagian dari integritas ilmiah, tim melakukan audit mandiri secara mendalam untuk mengungkap kelemahan yang masih ada di balik metrik akurasi 99%:

### 5.1 Temuan 1: Kebocoran Data Penutur (*Signer Leakage*)
Akurasi uji $99.13\%$ diperoleh dari skema partisi *Signer-Dependent* (`split_sd`), di mana kelima penutur (`SIGNER0`–`4`) tersebar di set Train (960 klip), Val (180 klip), dan Test (460 klip). Model Transformer cenderung menghafal proporsi fisik dan kebiasaan gerak dari 5 individu tersebut. Akibatnya, saat aplikasi diuji coba langsung oleh pengguna baru di webcam yang belum pernah ada di dataset, model mengalami penurunan keyakinan prediksi (*domain shift*).
* **Solusi Minggu 2:** Menerapkan skema partisi **Leave-One-Signer-Out (LOSO)** yang jujur dan menambahkan augmentasi koordinat 3D.

### 5.2 Temuan 2: Kegagalan Model Abjad Konvolusional (I1 MobileNetV3)
Pemeriksaan log pelatihan pada `runs/image_i1_mobilenetv3/result.json` menunjukkan bahwa model MobileNetV3 mengalami *training collapse* dengan akurasi uji hanya **3.85%** (persis sama dengan tebakan acak 1 dari 26 kelas, $1/26 = 0.03846$).
* **Solusi Sementara Minggu 1:** Frontend menerapkan safety fallback berupa aturan geometri sendi jari MediaPipe (`classifyAlphabetGeometry`).
* **Solusi Permanen Minggu 2:** Melatih ulang MobileNetV3 dengan optimizer AdamW, normalisasi ImageNet, dan learning rate $1\times 10^{-4}$.

### 5.3 Temuan 3: Kuantisasi Belum Sempurna & Keterbatasan Teks
* Biner `web/model/student_int8.onnx` memiliki hash SHA-256 yang identik dengan versi FP32 (5,46 MB), menandakan proses kuantisasi dinamis nyata belum diaplikasikan pada file produksi.
* Penyusunan kalimat masih menggunakan template kamus sederhana dengan *Word Error Rate* (WER) $62.3\%$, sehingga memerlukan penambahan data kalimat paralel.

---

## BAB VI: ROADMAP & RENCANA TINDAKAN LANJUTAN

Berdasarkan temuan audit, rencana kerja telah disusun berdasarkan skala prioritas:

### 6.1 Prioritas P0 (Remedi Kritis — Minggu 2)
1. **Partisi Ulang Dataset LOSO:** Membagi `manifest_wl_bisindo.csv` menjadi Signer 1–3 untuk training (1.160 klip), Signer 0 untuk validasi (120 klip), dan Signer 4 khusus sebagai data uji independen (320 klip).
2. **Augmentasi Koordinat 3D Skeletal:** Menambahkan modul *random spatial scaling* (0.85–1.15), *joint coordinate jitter*, rotasi sumbu bahu ($\pm 10^\circ$), dan *temporal speed perturbation* pada DataLoader.
3. **Retraining Model M0 (LOSO):** Menargetkan akurasi *Signer-Independent* nyata $\ge 82\%$.
4. **Retraining Model Abjad I1:** Melatih ulang MobileNetV3-Small untuk 26 abjad hingga mencapai akurasi uji $\ge 88\%$.

### 6.2 Prioritas P1 & P2 (Peningkatan Mutu & NLP — Minggu 3)
1. **Kuantisasi Dinamis Nyata INT8:** Mengompresi model M0 dari 5,46 MB menjadi $\approx 1,4\text{ MB}$ untuk mempercepat waktu pemuatan web di jaringan sekolah.
2. **Sintesis Korpus Kalimat:** Memperluas 305 pasang kalimat menjadi 5.000 pasang gloss-kalimat menggunakan data Tatoeba.
3. **Fine-Tuning IndoT5:** Melatih model sequence-to-sequence ringan untuk translasi kalimat alami.

### 6.3 Prioritas P3 (Integrasi Regional FSL — Minggu 4+)
1. Mengintegrasikan kamus konsep semantik Lapis 1 untuk bahasa isyarat Filipina (FSL).
2. Uji coba langsung di lingkungan kelas pada siswa Tuli dan guru.

---

## BAB VII: PEMBAGIAN TUGAS TIM PENGEMBANG

Proyek ini dikembangkan secara aktif dan kolaboratif oleh 3 anggota pengembang:

### 1. Farrel — *Lead Data & Preprocessing*
* Mengekstrak 1.600 klip video WL-BISINDO ke dalam file koordinat `.npz`.
* Mengimplementasikan Kontrak 1 (Topologi 86 node) dan Kontrak 4 (Hand Crop 224x224).
* Mengembangkan fungsi normalisasi bahu dan modul augmentasi data spasial-temporal 3D.
* Mengelola kurasi dataset teks paralel dan metadata fonologi isyarat.

### 2. Jonnathan — *Lead Model Architecture & Training*
* Merancang dan melatih arsitektur baseline M0 (Student Transformer) dan M1 (ST-GCN).
* Bertanggung jawab atas pelatihan ulang model M0 pada skema partisi LOSO.
* Melatih ulang model abjad MobileNetV3 (I1) untuk klasifikasi ejaan jari.
* Mengoptimalkan hiperparameter pelatihan (label smoothing, weight decay, learning rate scheduler).

### 3. Gloria (KarinaGlo) — *Lead Systems, Evaluation, ONNX & Frontend PWA*
* Bertanggung jawab atas penegakan Kontrak 2 (I/O ONNX Web) dan Kontrak 3 (Paritas numerik PyTorch vs JS).
* Mengonversi model PyTorch ke ONNX dan mengaplikasikan kuantisasi dinamis INT8.
* Mengembangkan arsitektur web PWA berbasis WebGL 2.0 dan WebAssembly SIMD.
* Merancang antarmuka pengguna interaktif ruang kelas dua arah dan integrasi Text-to-Speech otomatis.
* Mengembangkan server backend FastAPI, WebSocket relay (Kontrak 6), dan modul ASR/NLP (Whisper & IndoT5).

---

## BAB VIII: KESIMPULAN

Pada evaluasi kemajuan Minggu Pertama, tim SignBridge telah berhasil membuktikan kelayakan teknis dari konsep penerjemah bahasa isyarat murni di peramban web (*browser edge*). Dengan latensi inferensi 11,2 ms dan performa pipeline total 34,4 ms (29.1 FPS), sistem berjalan sangat responsif pada komputer standar tanpa bantuan server GPU. 

Seluruh fondasi kode, kontrak antarmuka rekayasa, dan suite testing otomatis telah terverifikasi dengan tingkat kelulusan 100%. Dengan rencana aksi terukur untuk mengatasi *signer domain shift* melalui partisi LOSO pada minggu kedua, SignBridge berada pada jalur yang tepat untuk menjadi jembatan komunikasi inklusif yang handal di ruang kelas.

