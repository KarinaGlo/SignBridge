# NASKAH & DOKUMEN PRESENTASI PROGRES MINGGU 1
**SignBridge ID–PH (BISINDO ↔ FSL Multimodal Classroom Bridge)**  
*Mata Kuliah: Machine Learning (Semester 5) — Projek 1*  
*Format: Slide Deck, Visual Content, Speaker Notes, & Q&A Defense Guide*

---

## DAFTAR ISI SLIDE (14 SLIDE LENGKAP)

1. [Slide 1: Judul Proyek & Identitas Tim](#slide-1-judul-proyek--identitas-tim)
2. [Slide 2: Latar Belakang & Motivasi](#slide-2-latar-belakang--motivasi)
3. [Slide 3: Rumusan Masalah & Spesifikasi Teknis](#slide-3-rumusan-masalah--spesifikasi-teknis)
4. [Slide 4: DIAGRAM ARSITEKTUR SISTEM TINGKAT TINGGI (High-Level Architecture)](#slide-4-diagram-arsitektur-sistem-tingkat-tinggi)
5. [Slide 5: DIAGRAM PIPELINE KOMPUTASI ML DETAIL (End-to-End Feature & Inference Pipeline)](#slide-5-diagram-pipeline-komputasi-ml-detail)
6. [Slide 6: Arsitektur 4 Modalitas Input Ruang Kelas](#slide-6-arsitektur-4-modalitas-input-ruang-kelas)
7. [Slide 7: 6 Kontrak Antarmuka Rekayasa Tim](#slide-7-6-kontrak-antarmuka-rekayasa-tim)
8. [Slide 8: Manajemen Dataset & Ekstraksi 86 Titik](#slide-8-manajemen-dataset--ekstraksi-86-titik)
9. [Slide 9: Capaian & Deliverables Minggu Pertama](#slide-9-capaian--deliverables-minggu-pertama)
10. [Slide 10: Hasil Eksperimen Baseline (M0 & M1)](#slide-10-hasil-eksperimen-baseline-m0--m1)
11. [Slide 11: Temuan Masalah Kritis & Audit Integritas ML](#slide-11-temuan-masalah-kritis--audit-integritas-ml)
12. [Slide 12: Rencana Kerja & Roadmap Minggu Kedua (Remedi P0)](#slide-12-rencana-kerja--roadmap-minggu-kedua-remedi-p0)
13. [Slide 13: Pembagian Peran Anggota Tim](#slide-13-pembagian-peran-anggota-tim)
14. [Slide 14: Kesimpulan & Sesi Tanya Jawab](#slide-14-kesimpulan--sesi-tanya-jawab)
15. [Panduan Pertahanan Ujian / Antisipasi Tanya Jawab Dosen](#panduan-pertahanan-ujian--antisipasi-tanya-jawab-dosen)

---

### Slide 1: Judul Proyek & Identitas Tim

#### Konten Visual Slide:
* **Judul Utama:** SignBridge ID–PH
* **Sub-judul:** Jembatan Komunikasi Multimodal Real-Time Bahasa Isyarat Indonesia (BISINDO) & Filipina (FSL) Berbasis Browser Edge
* **Mata Kuliah:** Machine Learning — Semester 5 (Projek 1)
* **Susunan Tim Pengembang:**
  * **Farrel** — *Lead Data & Preprocessing (Kontrak 1, 3, & 4)*
  * **Jonnathan** — *Lead Model Architecture & Training (M0, M1, I1)*
  * **Gloria (KarinaGlo)** — *Lead Systems, Evaluation, ONNX & Frontend PWA (Kontrak 2, 5, 6, Whisper, IndoT5)*
* **Target Repositori:** `feature/field-test-readiness` (Clean branch, Git verified)

#### Speaker Notes (Naskah Presenter):
> *"Selamat pagi/siang kepada Bapak/Ibu dosen dan rekan-rekan sekalian. Hari ini kami dari kelompok projek Machine Learning Semester 5 ingin mempresentasikan progres Minggu Pertama dari proyek kami yang berjudul **SignBridge ID–PH: Jembatan Komunikasi Multimodal Real-Time BISINDO dan FSL Berbasis Browser Edge**. Tim pengembang kami beranggotakan tiga orang dengan pembagian peran yang terstandarisasi, yaitu Farrel di bidang data dan preprocessing, Jonnathan di arsitektur dan pelatihan model, serta Gloria di evaluasi model, ekspor ONNX, backend FastAPI, dan integrasi frontend web PWA. Pada minggu pertama ini, kami telah membangun fondasi rekayasa perangkat lunak, pipeline ekstraksi data 86 titik, eksperimen model baseline, serta prototipe inferensi langsung di peramban."*

---

### Slide 2: Latar Belakang & Motivasi

#### Konten Visual Slide:
* **Tiga Masalah Utama:**
  1. **Barrier Komunikasi Kelas Inklusif:** Kurangnya juru bahasa isyarat di ruang kelas reguler menyebabkan siswa Tuli kesulitan berinteraksi dua arah dengan pengajar dan rekan dengar (Mendukung SDG 4.5 & 4.a).
  2. **Ketergantungan Komputasi Awan (Cloud GPU):** Mayoritas sistem AI penerjemah isyarat membutuhkan transmisi video mentah ke cloud server GPU, menimbulkan latensi tinggi (>300 ms), biaya langganan server yang mahal, dan kekhawatiran privasi video siswa.
  3. **Isolasi Isyarat Regional ASEAN:** Belum tersedianya sistem yang menjembatani bahasa isyarat antarnegara tetangga (BISINDO Indonesia dan FSL Filipina) untuk kolaborasi pendidikan internasional.
* **Peluang Inovasi:** Membangun inferensi *client-side browser-first* berbasis MediaPipe Holistic dan ONNX Runtime WebAssembly yang berjalan langsung di laptop/Chromebook standar sekolah tanpa instalasi apa pun.

#### Speaker Notes (Naskah Presenter):
> *"Latar belakang penelitian kami berangkat dari realitas di sekolah inklusif. Di satu sisi, siswa Tuli membutuhkan media komunikasi yang lancar, namun di sisi lain, solusi AI yang ada saat ini umumnya berbasis cloud yang lambat, mahal, dan membutuhkan server GPU eksternal. SignBridge hadir dengan pendekatan baru: **browser-first edge inference**. Sistem kami memproses seluruh data penglihatan komputer langsung di dalam browser pengguna menggunakan WebAssembly dan WebGL, sehingga data video tidak pernah meninggalkan perangkat lokal siswa, tidak ada biaya server GPU, dan latensi dapat ditekan hingga di bawah 50 milidetik."*

---

### Slide 3: Rumusan Masalah & Spesifikasi Teknis

#### Konten Visual Slide:
* **Rumusan Masalah:** Bagaimana merancang sistem pengenalan bahasa isyarat multimodal yang akurat, berlatensi rendah (< 50 ms), dan beroperasi secara independen di peramban web tanpa memerlukan instalasi aplikasi native atau server GPU?
* **Spesifikasi Rekayasa (Engineering Specs):**
  * **Latensi Inferensi Web:** $\le 50\text{ ms}$ (minimal setara 20 FPS real-time).
  * **Ukuran Bobot Model (ONNX):** $< 10\text{ MB}$ (ramah koneksi internet sekolah).
  * **Toleransi Paritas Numerik:** Perbedaan mutlak output Python vs JavaScript $< 1\times 10^{-4}$.
  * **Cakupan Input:** 4 Modalitas Ruang Kelas (Video, Citra, Suara, dan Teks).

#### Speaker Notes (Naskah Presenter):
> *"Berdasarkan masalah tersebut, fokus kami adalah merumuskan arsitektur yang sangat efisien. Kami menetapkan parameter rekayasa yang ketat: latensi inferensi total harus di bawah 50 milidetik agar penerjemahan terasa instan, ukuran file model ONNX harus di bawah 10 MB agar cepat diunduh saat pertama kali membuka web, dan yang terpenting: harus ada jaminan paritas matematika penuh antara preprocessing di Python saat pelatihan dan JavaScript di browser saat inferensi."*

---

### Slide 4: DIAGRAM ARSITEKTUR SISTEM TINGKAT TINGGI

#### Konten Visual Slide:
```
+---------------------------------------------------------------------------------------------------+
|                        LAPIS 1: CLIENT BROWSER (PWA EDGE — ZERO CLOUD INFERENCE)                  |
|                                                                                                   |
|  [Input Modalitas]               [Vision Front-End]             [Preprocessing]                   |
|   • Webcam (30 FPS)      -->    MediaPipe Holistic WASM  -->   Normalisasi Bahu &                 |
|   • Mic Audio (Guru)            (543 Keypoints WebGL)         Resampling Linear 64 Frame          |
|   • Teks Keyboard                    [Kontrak 1 & 4]                [Kontrak 3]                   |
|                                                                     |                             |
|  [Multimodal Output]               [Decision Boundary]              v                             |
|   • Web Speech Audio TTS <--     Top-1 Conf >= 0.45      <--   ONNX Runtime Web                   |
|   • Teks Layar / Log            Margin >= 0.10 & Guard        (M0 Transformer WASM SIMD 11.2ms)   |
|                                                                     [Kontrak 2 & 5]               |
+---------------------------------------------------------------------------------------------------+
                                                ^
                                                | Protokol: REST API Fallback & WebSocket Ruang Kelas
                                                v
+---------------------------------------------------------------------------------------------------+
|                     LAPIS 2: BACKEND RELAY & JEMBATAN ASEAN (FASTAPI SERVER)                      |
|                                                                                                   |
|     [REST Fallback API]              [Relay WebSocket]              [Jembatan BISINDO ↔ FSL]     |
|   /predict & /asr (Rate Limit)     /ws/{room} Interaksi Kelas      L1: Kamus Konsep (concepts.csv)|
|          [Kontrak 6]                      [Kontrak 6]              L2: Neural Translation         |
+---------------------------------------------------------------------------------------------------+
```

#### Speaker Notes (Naskah Presenter):
> *"Bapak/Ibu dosen sekalian, ini adalah diagram arsitektur tingkat tinggi dari SignBridge. Sistem kami memisahkan tanggung jawab menjadi dua lapis yang sangat tegas:*
> 
> *Lapis pertama adalah **Client Browser PWA**. Seluruh pemrosesan pengenalan bahasa isyarat berjalan 100% di sisi klien. Mulai dari tangkapan webcam, deteksi 543 titik skeletal via MediaPipe Holistic, normalisasi titik bahu, hingga eksekusi neural network model M0 via ONNX Runtime WebAssembly SIMD. Output langsung disuarakan melalui Web Speech API secara instan.*
> 
> *Lapis kedua adalah **Backend FastAPI Server**. Server ini tidak digunakan untuk komputasi video berat, melainkan sebagai relay komunikasi ruang kelas dua arah melalui WebSocket `/ws/{room}` dan jembatan translasi semantik BISINDO ke FSL. Dengan arsitektur dua lapis ini, server sekolah yang murah sekalipun dapat melayani puluhan siswa sekaligus tanpa membebani GPU."*

---

### Slide 5: DIAGRAM PIPELINE KOMPUTASI ML DETAIL

#### Konten Visual Slide:
```
[1. Video Stream]       -->  [2. MediaPipe Holistic]   -->  [3. Filter 86 Node]    -->  [4. Normalisasi Bahu]
 Webcam 640x480               543 Titik Raw                11 Tubuh, 42 Tangan,          Center = (bahu_L+R)/2
 30 FPS Real-time             (WebGL 2.0 Engine)           33 Wajah Ekspresif            Scale = ||bahu_L - bahu_R||
                                                            [Kontrak 1]                  [Kontrak 3]
                                                                                               |
                                                                                               v
[8. Output Multimodal]  <--  [7. Two-Tier Decision]    <--  [6. ONNX Web Runtime]  <--  [5. Resampling 64 Frame]
 Web Speech TTS (id-ID)       Top-1 Conf >= 0.45            M0 Student Transformer       Sliding Window Buffer
 Teks Kalimat Alami           Top-2 Margin >= 0.10          Logits [1, 32] (11.2 ms)     Tensor [1, 64, 86, 3]
                             & Signing Space Guard         [Kontrak 2]

*Catatan Waktu Komputasi: MediaPipe (22,4 ms) + Preprocessing (0,8 ms) + ONNX (11,2 ms) = 34,4 ms (~29 FPS)
*Jalur Alternatif: Gerakan tangan statis dialihkan ke Hand Crop 224x224 [Kontrak 4] -> Model Abjad A-Z [Kontrak 5]
```

#### Speaker Notes (Naskah Presenter):
> *"Pada slide ini, kami memperlihatkan pipeline komputasi machine learning end-to-end secara detail dari input frame mentah hingga keluaran suara:*
> 
> 1. *Frame video 640x480 ditangkap pada kecepatan 30 FPS.*
> 2. *MediaPipe Holistic mengekstrak 543 koordinat landmark.*
> 3. *Melalui Kontrak 1, kami memfilter titik-titik tersebut dan hanya mengambil **86 node fungsional**: 11 titik torso atas, 21 titik tangan kiri, 21 titik tangan kanan, dan 33 titik wajah ekspresif.*
> 4. *Koordinat dinormalisasi (Kontrak 3) menggunakan titik tengah bahu sebagai pusat koordinat (center invariance) dan jarak antar-bahu sebagai faktor skala (scale invariance).*
> 5. *Buffer geser temporal menampung sekuens gerak dan meresample-nya secara linear menjadi tepat 64 frame.*
> 6. *Tensor `[1, 64, 86, 3]` dieksekusi oleh model M0 Student Pose Transformer di ONNX WebAssembly hanya dalam 11,2 milidetik.*
> 7. *Keputusan melewati Two-Tier Decision Boundary: verifikasi bahwa tangan berada di ruang isyarat (Signing Space Guard), nilai konfidensi $\ge 0.45$, dan selisih probabilitas top-1 vs top-2 $\ge 0.10$.*
> 8. *Jika valid, kata dimasukkan ke accumulator kalimat dan disuarakan via speech synthesis lokal.*
> 
> *Total waktu satu siklus inferensi adalah **34,4 milidetik**, yang membuktikan bahwa sistem kami berjalan mulus pada 29 frame per detik."*

---

### Slide 6: Arsitektur 4 Modalitas Input Ruang Kelas

#### Konten Visual Slide:
* **Modalitas 1 — Video Gerakan Dinamis (WL-BISINDO):** 32 kata isyarat percakapan kelas berbasis pergerakan 86 koordinat tubuh skeletal (64 frame) menggunakan Student Pose Transformer (M0) & ST-GCN (M1).
* **Modalitas 2 — Citra Bentuk Tangan Statis (Fingerspelling):** 26 abjad ejaan jari (A–Z) dari crop bounding box tangan 224x224 piksel menggunakan MobileNetV3-Small (I1) + Heuristik Geometri.
* **Modalitas 3 — Audio Ucapan Guru (ASR):** Menangkap suara guru/teman dengar dan mengubahnya menjadi teks transkripsi via Web Speech API & Whisper.
* **Modalitas 4 — Teks & Rekonstruksi Kalimat (NLP):** Mengubah rangkaian kata gloss isyarat menjadi kalimat alami bahasa Indonesia/Tagalog yang terstruktur rapi via Rule-Based Template (B0) & IndoT5.

#### Speaker Notes (Naskah Presenter):
> *"Keempat modalitas ini saling melengkapi di ruang kelas: kata-kata umum ditangani oleh modalitas video dinamis, ejaan nama orang atau istilah teknis ditangani oleh modalitas ejaan jari huruf demi huruf, instruksi lisan guru ditangkap oleh modalitas suara, dan rangkaian kata dirangkai menjadi kalimat gramatikal oleh modalitas teks."*

---

### Slide 7: 6 Kontrak Antarmuka Rekayasa Tim

#### Konten Visual Slide:
* **Tujuan Kontrak:** Mencegah terjadinya *training-serving skew* dan perbedaan kalkulasi antar-anggota tim (*software engineering best practices*).
  1. **Kontrak 1 — Skema 86 Node (`signbridge/constants.py`):** Mereduksi 543 titik MediaPipe Holistic menjadi 86 titik kanonis: 11 tubuh atas, 21 tangan kiri, 21 tangan kanan, 33 ekspresi wajah.
  2. **Kontrak 2 — Model Video ONNX (`student.onnx`):** Input wajib `[B, 64, 86, 3]` float32 $\to$ Output logits `[B, 32]`. Ukuran model $< 10\text{ MB}$.
  3. **Kontrak 3 — Paritas Preprocessing (`features.py` ≡ `features.js`):** Operasi normalisasi bahu dan resampling temporal 64 frame diverifikasi identik numerik (diff $< 1\times 10^{-5}$).
  4. **Kontrak 4 — Paritas Hand Crop (`crop.py` ≡ `handcrop.js`):** Pemotongan kotak tangan persegi dengan padding 25% ke ukuran 224x224 piksel.
  5. **Kontrak 5 — Model Citra ONNX (`fingerspell.onnx`):** Input citra `[B, 3, 224, 224]` float32 $\to$ Output 26 kelas abjad.
  6. **Kontrak 6 — Server FastAPI (`server/app.py`):** REST API fallback dan WebSocket relay interaksi kelas 2-arah dengan pembatas laju 60 req/menit.

#### Speaker Notes (Naskah Presenter):
> *"Dengan 6 kontrak ini, seluruh pipeline yang ada di diagram sebelumnya dijamin konsistensinya. Kami memiliki automated test di Python (`pytest`) dan Node.js (`node --test`). Jika ada anggota tim yang mengubah logika normalisasi di Python tanpa memperbarui modul JavaScript di frontend, pipeline integrasi kami akan otomatis menolak perubahan tersebut."*

---

### Slide 8: Manajemen Dataset & Ekstraksi 86 Titik

#### Konten Visual Slide:
* **Tabel Inventaris Dataset:**
  * **Video WL-BISINDO:** 1.600 klip video (32 kelas, 50 klip/kelas) dari 5 signer native (`SIGNER0`–`4`).
  * **Citra Abjad Mendeley:** 4.466 gambar tangan abjad A–Z.
  * **Audio FLEURS:** 3.616 metadata transkripsi ucapan bahasa Indonesia.
  * **Teks Paralel:** 305 pasang kalimat gloss-ke-teks.
* **Pipeline Ekstraksi Spasial-Temporal:**
  $$\mathbf{x}_{\text{norm}} = \frac{\mathbf{x} - \frac{1}{2}(\text{bahu}_L + \text{bahu}_R)}{\max(\|\text{bahu}_L - \text{bahu}_R\|_2, 10^{-6})}$$

#### Speaker Notes (Naskah Presenter):
> *"Dari sisi data, pada modalitas video kami menggunakan 1.600 klip WL-BISINDO dengan 32 kata percakapan kelas dari 5 orang penutur isyarat. Normalisasi bahu memastikan bahwa posisi duduk pengguna dekat atau jauh dari webcam tidak akan mengubah koordinat relatif sendi tubuh."*

---

### Slide 9: Capaian & Deliverables Minggu Pertama

#### Konten Visual Slide:
* **Deliverables Selesai:**
  1. *Testing Otomatis CI:* Repositori terstandarisasi pada branch `feature/field-test-readiness` dengan suite pengujian otomatis (`pytest` 18/18 lulus, paritas JavaScript 100% lulus).
  2. *Pelatihan Baseline Isyarat Video:*
     * Model M0 (Student Pose Transformer, 1,33 juta parameter) berhasil dilatih.
     * Model M1 (ST-GCN 4-blok, 1,48 juta parameter) berhasil dilatih.
  3. *Ekspor & Validasi ONNX Web:* Ekspor M0 ke `web/model/student.onnx` (5,46 MB) dengan selisih numerik terhadap PyTorch hanya $2.4\times 10^{-6}$.
  4. *Prototipe Web Aktif:* Frontend HTML5/JavaScript terintegrasi MediaPipe WASM, WebGL 2.0, ONNX Runtime Web, dan Text-to-Speech otomatis telah berjalan di browser lokal.

#### Speaker Notes (Naskah Presenter):
> *"Capaian minggu pertama membuktikan kelayakan teknis: pipeline pengujian otomatis lulus 100%, dua model baseline berhasil dilatih, ekspor ONNX terverifikasi presisi tinggi, dan prototipe web live telah dapat diuji coba langsung."*

---

### Slide 10: Hasil Eksperimen Baseline (M0 & M1)

#### Konten Visual Slide:
* **Tabel Perbandingan Kinerja Model:**

| Parameter Evaluasi | M0: Student Transformer | M1: ST-GCN Baseline |
| :--- | :--- | :--- |
| **Arsitektur** | Linear Proj (128) + 2x Transformer Enc | 4-Blok Spatial-Temporal Graph Conv |
| **Jumlah Parameter** | 1.335.872 (1,33 M) | 1.481.248 (1,48 M) |
| **Epoch Pelatihan** | 48 epoch (Early stop) | 79 epoch |
| **SD Validation Accuracy**| **97.78%** | **98.89%** |
| **SD Test Accuracy** | **99.13%** (456/460 benar) | **99.13%** (456/460 benar) |
| **Latensi Inferensi Web**| **11,2 ms** (Sangat Cepat) | 18,5 ms (Est.) |
| **Total Latensi E2E** | **34,4 ms** ($\approx 29.1\text{ FPS}$) | $\approx 42\text{ ms}$ |

#### Speaker Notes (Naskah Presenter):
> *"Kedua model mencapai akurasi data uji 99.13% pada 460 sampel uji. Model M0 Student Transformer menjadi model pilihan utama kami untuk browser karena arsitektur self-attention liniernya dieksekusi sangat efisien dalam 11,2 milidetik pada WebAssembly, melampaui target spesifikasi di bawah 50 milidetik."*

---

### Slide 11: Temuan Masalah Kritis & Audit Integritas ML

#### Konten Visual Slide:
* **Tiga Temuan Audit Internal:**
  1. **Signer Leakage (Data Split):** Akurasi 99.13% diperoleh dari partisi *Signer-Dependent*, di mana kelima penutur isyarat tersebar di data latih dan uji. Model cenderung menghafal proporsi tubuh subjek latih, sehingga saat dicoba oleh pengguna baru via webcam terjadi penurunan akurasi (*domain shift*).
  2. **Kegagalan Pelatihan Abjad MobileNetV3 (I1):** Model abjad menghasilkan akurasi uji hanya **3.85%** (tebakan acak $1/26$). Saat ini frontend mengandalkan aturan heuristik geometri sendi jari.
  3. **Kuantisasi Belum Sempurna & Rule NLP:** File `student_int8.onnx` masih berupa salinan FP32 (5,46 MB, belum terkompresi ke ~1,4 MB), dan pembentukan kalimat masih menggunakan aturan kamus kaku dengan WER 62.3%.

#### Speaker Notes (Naskah Presenter):
> *"Sebagai peneliti machine learning, kami bersikap transparan: akurasi 99% ini berasal dari data latih yang memiliki penutur yang sama dengan data uji. Begitu dicoba oleh orang baru di webcam, terjadi domain shift. Selain itu model konvolusi abjad kami mengalami training collapse (3.85%). Temuan audit inilah yang menjadi dasar rencana perbaikan prioritas kami di minggu kedua."*

---

### Slide 12: Rencana Kerja & Roadmap Minggu Kedua (Remedi P0)

#### Konten Visual Slide:
* **Roadmap Pelatihan & Remedi (Prioritas P0 & P1):**
  * **Minggu 2 (Remedi Kritis P0):**
    * Partisi ulang dataset menjadi **Leave-One-Signer-Out (LOSO)**: Signer 1–3 train, Signer 0 val, dan Signer 4 sebagai unseen test set.
    * Augmentasi 3D skeletal (*random scaling*, *joint coordinate jitter*, *temporal speed stretching*).
    * Retraining model M0 pada skema LOSO (target akurasi Signer-Independent $\ge 82\%$).
    * Retraining MobileNetV3 untuk abjad A–Z (target akurasi $\ge 88\%$).
  * **Minggu 3 (Peningkatan Mutu P1):** Kuantisasi dinamis nyata INT8 (~1,4 MB) dan sintesis 5.000 pasang kalimat untuk IndoT5.
  * **Minggu 4 (Validasi Lapangan):** Pengujian langsung pada siswa Tuli dan integrasi leksikon FSL.

#### Speaker Notes (Naskah Presenter):
> *"Fokus minggu kedua adalah melatih ulang model M0 pada partisi LOSO yang diperkuat dengan augmentasi koordinat 3D, serta melatih ulang model abjad MobileNetV3. Di minggu ketiga, kami menerapkan kuantisasi INT8 nyata dan ekspansi korpus kalimat untuk model IndoT5."*

---

### Slide 13: Pembagian Peran Anggota Tim

#### Konten Visual Slide:
* **Farrel (Data & Preprocessing Lead):** Ekstraksi keypoint MediaPipe Holistic, pemeliharaan Kontrak 1 & 4, modul augmentasi 3D, crop kotak tangan 224x224, dan kurasi dataset teks paralel.
* **Jonnathan (Architecture & Training Lead):** Desain & pelatihan ulang model M0 (LOSO), eksperimen ST-GCN M1, pelatihan ulang MobileNetV3 abjad, serta optimasi fungsi loss dan scheduler.
* **Gloria (KarinaGlo) (Systems, Evaluation, ONNX & Frontend Lead):** Benchmarking paritas ONNX INT8, integrasi runtime ONNX Web WASM dan MediaPipe di browser, pengembangan frontend PWA interaktif, server FastAPI & WebSocket, serta modul Speech/NLP (Whisper & IndoT5).

#### Speaker Notes (Naskah Presenter):
> *"Pembagian kerja tim pengembang kami terstruktur rapi dan komprehensif: Farrel menangani rekayasa data dan preprocessing 86 titik, Jonnathan menangani arsitektur dan pelatihan model deep learning, sedangkan Gloria memimpin evaluasi model, kuantisasi ONNX, pengembangan backend FastAPI, serta orkestrasi integrasi aplikasi web PWA."*

---

### Slide 14: Kesimpulan & Sesi Tanya Jawab

#### Konten Visual Slide:
* **Kesimpulan:** Arsitektur dasar inferensi browser edge telah terbukti berjalan lancar pada kecepatan **30 FPS (34,4 ms)** dengan kepatuhan kontrak antarmuka 100%.
* **Fokus Selanjutnya:** Mengatasi *signer domain shift* melalui skema evaluasi LOSO dan memperbaiki model neural abjad.
* **Akses Prototipe Live:** Server lokal aktif di port 8000 dan siap didemonstrasikan.
* **Sesi Tanya Jawab:** Kami membuka sesi diskusi dan menyambut masukan dari Bapak/Ibu dosen.

#### Speaker Notes (Naskah Presenter):
> *"Kami telah membuktikan bahwa sistem pengenalan isyarat real-time 30 FPS langsung di browser tanpa server GPU dapat diwujudkan. Dengan pembenahan LOSO di minggu kedua, SignBridge siap menjadi jembatan komunikasi inklusif yang andal. Terima kasih, kami membuka sesi tanya jawab."*

---
*Dokumen presentasi ini telah disinkronkan dengan file slide interaktif di `docs/presentations/presentasi_minggu_1.html`.*
