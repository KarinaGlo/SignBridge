# LAPORAN INVESTIGASI & PENINGKATAN AKURASI PENGENALAN REAL-TIME SIGNBRIDGE

**Proyek:** SignBridge (Sistem Penerjemahan Real-Time BISINDO & FSL Filipina)  
**Dokumen:** `docs/SIGNBRIDGE_RECOGNITION_ACCURACY_IMPROVEMENT.md`  
**Peran:** Senior Machine Learning Engineer, Computer Vision Engineer, & QA Specialist  
**Tanggal:** 9 November 2026  
**Status Audit:** **SELESAI & TERVERIFIKASI (PASS 12/12 JS Tests, 18/18 PyTests)**  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Keluhan utama pengguna saat pengujian webcam langsung adalah:
> *"Kok masih kacau ya yang real time-nya... saya belum gerak tapi sudah ngomong dan terus-menerus ganti kata."*

Investigasi mendalam berbasis bukti empiris dan bedah kode telah membongkar **3 akar masalah fundamental (Root Causes)**:

1. **Pemicu Isyarat Statis Prematur Tanpa Filter Ruang Isyarat (`holdBuffer`)**:
   Pada `web/js/recognizer.js`, setiap kali tangan terdeteksi di kamera dengan energi gerak rendah (< `motionStartThreshold`), sistem secara otomatis memasukkan frame ke `holdBuffer`. Setelah 10 frame diam (~333 ms), sistem langsung mengeksekusi inferensi ONNX. Karena pengguna sedang duduk di depan meja (tangan di keyboard/mouse/pangkuan), tangan diam ini berulang kali dikirim ke model neural.
2. **Ketiadaan Filter Ambang Keyakinan (Confidence Threshold Ignored)**:
   Meskipun `APP_CONFIG.confidenceThreshold = 0.55` telah didefinisikan, fungsi `classifySequence()` **tidak pernah memeriksa ambang tersebut**. Apapun hasil keluaran model (meskipun probabilitas acak hanya 20% - 38%), selalu dikembalikan dengan `success: true`. Hasil inferensi model pada frame diam (misalnya prediksi acak `SAYA` 38.5% atau `TEMAN` 74.1%) langsung dimasukkan ke kalimat dan disuarakan via Text-to-Speech (TTS) Web Speech API secara beruntun.
3. **Desinkronisasi `labels.json` dan Pembatasan Mode Hibrid**:
   Ditemukan inkonsistensi di mana `web/model/labels.json` sempat tertimpa konsep ruang kelas (indeks 0 = `HALO`) alih-alih 32 kelas WL-BISINDO (`AIR` s/d `MALAM`), menyebabkan pergeseran label keluaran model. Selain itu, mode `hybrid` pada `app.js` sebelumnya mengabaikan `FingerspellRecognizer` sehingga ejaan abjad jari 26 huruf (A–Z) tidak aktif secara default.

Seluruh akar masalah telah diperbaiki dengan implementasi arsitektur stabilisasi baru:
- **Spatial Signing Space Bounding (`isInSigningSpace`)**: Tangan di posisi istirahat (di bawah batas dada/di atas meja) tidak akan pernah memicu perekaman atau inferensi.
- **Enforced Confidence & Margin Gate**: Hasil prediksi di bawah ambang keyakinan (0.60) atau memiliki margin probabilitas tipis (< 0.12) ditolak dengan `success: false` dan `gloss: null`.
- **Speech Cooldown & De-duplication**: Pencegahan pengulangan suara TTS ganda dalam jeda singkat (< 1600 ms).
- **True Hybrid Routing**: Dukungan penuh pengenalan dinamis 32 isyarat WL-BISINDO dan pengenalan statis 26 abjad jari A–Z saat tangan terangkat stabil di ruang isyarat.

---

## 2. ROOT CAUSE ANALYSIS (ANALISIS AKAR MASALAH)

### A. Mengapa "Belum Gerak Tapi Sudah Ngomong"?
1. **Perilaku Model Neural pada Data Diam / Titik Nol**:
   Model Transformer Student M0 dilatih pada sekuens gerakan isyarat dinamis (64 frame ter-resample). Ketika diuji pada vektor nol atau postur duduk diam dengan tangan di pangkuan:
   - Input nol menghasilkan probabilitas tertinggi pada kelas `SAYA` (38.47%, logit 3.14).
   - Input tangan di pangkuan menghasilkan probabilitas `TEMAN` (74.16%, logit 4.50).
2. **Loop `holdBuffer` Tanpa Koordinat Spasial**:
   Sebelum perbaikan, `pushFrame()` hanya memeriksa `hasDetectedHands(kp86)`. MediaPipe Holistic selalu mendeteksi tangan meskipun tangan berada di tepi bawah layar. Karena pengguna belum bergerak, `energy < motionStartThreshold`, sistem masuk ke blok `holdBuffer` dan setelah 10 frame (~0.33 detik) langsung menjalankan `classifySequence(holdBuffer)`.

### B. Mengapa "Terus-Menerus Ganti Kata"?
1. **Fluktuasi Landmark Jitter**:
   Kamera 30 FPS memiliki noise mikroskopis pada estimasi koordinat MediaPipe. Noise ini menyebabkan deskriptor fonologi heuristik (`currentPhono.signature`) berganti-ganti (misalnya rasio bukaan jari melintasi batas 0.88), sehingga sistem menganggap ada isyarat baru dan memicu inferensi ulang setiap 1.4 detik.
2. **Ketiadaan Histeresis dan Margin Check**:
   Tanpa pengecekan selisih probabilitas (margin) antara Top-1 dan Top-2, jika model menghasilkan probabilitas 18% untuk kata A dan 17% untuk kata B, sistem akan langsung menerima kata A, lalu pada frame berikutnya beralih ke kata B, menyebabkan kata berganti tanpa henti di layar dan disuarakan beruntun.

---

## 3. AUDIT PIPELINE KOMPUTER VISION & MEDIAPIPE

| Komponen | Status Implementasi | Catatan & Temuan Audit |
| :--- | :--- | :--- |
| **MediaPipe Holistic** | AKTIF (Wasm SIMD WebGL) | Berjalan stabil pada resolusi kamera 640x480. Ekstraksi 86 keypoints kanonis. |
| **86 Landmark Node Mapping** | TEPAT & SESUAI SPESIFIKASI | Pose 0..8 (Hidung, Bahu, Siku, Pergelangan, Pinggul), Tangan Kiri 9..29, Tangan Kanan 30..50, Wajah 51..85. |
| **Spatial Bounding** | DITAMBAHKAN (`isInSigningSpace`) | Memvalidasi pergelangan tangan (wrist) berada di atas batas dada bawah (`y < midShoulderY + 0.35`). |
| **Motion Energy Tracking** | DIPERBAIKI (`computeHandMotionEnergy`) | Mengukur rerata pergeseran Euclidean L2 pada 42 landmark tangan aktif antar frame. |

---

## 4. AUDIT PREPROCESSING PARITY (TRAINING VS INFERENCE)

Uji paritas numerik antara Python (`signbridge/features.py`) dan JavaScript (`web/js/features.js`) telah diverifikasi melalui suite pengujian otomatis (`node --test tests/js/parity.test.mjs`):

1. **`selectFromHolistic`**: 86 titik dipilih dari format Holistic mentah. Delta absolut: **< 1e-6 (PASS)**.
2. **`trimInactive`**: Pemangkasan frame diam awal dan akhir berdasarkan ambang energi 0.005. Delta: **0 (PASS)**.
3. **`normalizePose`**: Centering pada titik tengah bahu (mid-shoulder) dan scaling terhadap lebar bahu (shoulder distance). Delta: **< 1e-5 (PASS)**.
4. **`resampleFrames(64)`**: Interpolasi linear temporal ke tepat 64 frame. Delta: **< 1e-5 (PASS)**.
5. **`preprocessKeypoints` (End-to-End)**: Seluruh pipeline preprocessing menghasilkan tensor `[1, 64, 86, 3]` yang identik antara Python dan JavaScript (< 1e-5).

---

## 5. AUDIT SEGMENTASI TEMPORAL & SLIDING WINDOW

| Parameter | Nilai Lama | Nilai Baru | Rasionalisasi Perubahan |
| :--- | :--- | :--- | :--- |
| `motionStartThreshold` | 0.012 | **0.015** | Mencegah jitter kamera kecil memicu mode perekaman gerakan secara tidak sengaja. |
| `motionStopThreshold` | 0.007 | **0.008** | Menentukan akhir gerakan isyarat dengan lebih tegas saat tangan berhenti. |
| `minActiveFrames` | 7 frame | **8 frame** | Mengeliminasi gerakan refleks singkat / kedipan tangan (< 0.26 detik). |
| `maxActiveFrames` | 36 frame | **48 frame** | Memberikan waktu cukup (~1.6 detik) bagi gerakan isyarat majemuk seperti `TERIMA_KASIH` dan `BERANGKAT`. |
| `pauseFramesToClassify` | 5 frame | **6 frame** | Memastikan fase stroke isyarat selesai sebelum memicu inferensi model. |
| `confidenceThreshold` | 0.55 (diabaikan) | **0.60 (ditegakkan)** | Wajib >= 60% untuk dapat diterima sebagai kata sah pada kalimat. |
| `marginThreshold` | Tidak ada | **0.12** | Selisih minimum Top-1 terhadap Top-2 sebesar 12% guna mencegah tebakan ambigu. |
| `speechCooldownMs` | Tidak ada | **1600 ms** | Menghindari spam suara TTS pada kata berulang. |

---

## 6. SINKRONISASI DATABASE 32 KOSAKATA WL-BISINDO & 26 ABJAD A-Z

### A. 32 Kosakata Resmi Model M0 (Neuron Output [1, 32])
Sinkronisasi 100% antara `data/manifest_wl_bisindo.csv`, `web/model/labels.json`, dan `web/js/config.js`:
- Indeks 0..7: `AIR`, `BELAJAR`, `CARI`, `HARI`, `INGAT`, `LAGI`, `MAAF`, `MAKAN`
- Indeks 8..15: `MOTOR`, `SAYA`, `TERIMA_KASIH`, `TULI`, `APA`, `SIAPA`, `KAPAN`, `DIMANA`
- Indeks 16..23: `MENGAPA`, `BAGAIMANA`, `MERAH`, `KUNING`, `HIJAU`, `HITAM`, `DENGAR`, `BERANGKAT`
- Indeks 24..31: `DATANG`, `TEMAN`, `KELUARGA`, `RUMAH`, `PAGI`, `SIANG`, `SORE`, `MALAM`

### B. 26 Abjad Ejaan Jari (A-Z) Sesuai Database
Didukung penuh melalui `FINGERSPELL_DB` dan `classifyAlphabetGeometry(hand21)`:
- Setiap abjad dievaluasi dari 21 titik tangan MediaPipe (posisi ibu jari, ekstensi 4 jari, rasio pinch, dan orientasi telapak).
- Mengharuskan konsistensi bentuk jari minimal 7 dari 9 frame terakhir sebelum mengeluarkan huruf.
- Mode `hybrid` secara cerdas mengaktifkan deteksi huruf A–Z saat tangan ditahan statis di ruang isyarat tanpa gerakan dinamis.

---

## 7. FILE YANG DIUBAH & PENJELASAN TEKNIS

1. **`web/js/config.js`**:
   - Pembaruan konfigurasi `APP_CONFIG` (`confidenceThreshold: 0.60`, `marginThreshold: 0.12`, `speechCooldownMs: 1600`, `maxActiveFrames: 48`).
2. **`web/js/recognizer.js`**:
   - Penambahan fungsi ekspor `isInSigningSpace(kp86)`.
   - Perombakan logika `pushFrame()`: mengabaikan tangan di posisi istirahat (`hands-resting`), mencegah false-triggering saat diam.
   - Restriksi isyarat statis: hanya aktif jika tangan diangkat ke area dahi, mulut, atau dada (`currentPhono.location <= 2`).
   - Penegakan filter ambang keyakinan dan margin pada `classifySequence()`: jika < 0.60 atau margin < 0.12, mengembalikan `{ success: false, gloss: null }`.
3. **`web/js/fingerspell.js`**:
   - Perbaikan bug inisialisasi cooldown: `(this.lastEmitAt > 0 && now - this.lastEmitAt < 1300)` sehingga abjad pertama tidak terblokir saat startup.
4. **`web/js/app.js`**:
   - Integrasi routing mode Hibrid sejati: jika `recognizer.state === IDLE`, alirkan frame tangan ke `fingerspeller.pushHandFrame(activeHand)`.
   - Penjagaan `handleSignPrediction()`: hanya menambahkan kata dan membunyikan TTS jika `pred.success === true && pred.gloss !== null`.
   - Cooldown TTS `this.lastSpokenAt` untuk mencegah audio spamming.
   - Peningkatan teks status visual `#sign-state-badge` (menampilkan status istirahat dan jumlah frame rekam secara transparan).
5. **`web/model/labels.json`**:
   - Penulisan ulang 32 label resmi WL-BISINDO agar sinkron sempurna dengan output neuron model ONNX M0.
6. **`tests/js/recognizer_stability.test.mjs`**:
   - Pembuatan suite pengujian unit stabilitas: uji deteksi ruang isyarat, supresi posisi istirahat, filter confidence threshold, dan geometri abjad jari.

---

## 8. BUKTI VERIFIKASI PENGUJIAN (TEST EVIDENCE)

### A. Pengujian JavaScript (Node.js Test Runner)
Perintah:
```powershell
node --test tests/js/parity.test.mjs tests/js/handcrop.test.mjs tests/js/recognizer_stability.test.mjs
```
Hasil:
```text
✔ Kontrak 4: computeHandCropBox (+25% margin) identik dengan Python (3.43ms)
✔ Kontrak 4 & 5: cropAndResizeHand dan normalizeImagenet identik dengan Python (< 1e-5) (5.18ms)
✔ Kontrak 1 & 3: selectFromHolistic identik dengan Python (< 1e-6) (2.65ms)
✔ Kontrak 3: trimInactive memangkas frame diam identik dengan Python (7.98ms)
✔ Kontrak 3: normalizePose (pusat bahu & lebar bahu) identik dengan Python (< 1e-5) (10.15ms)
✔ Kontrak 3: resampleFrames(64) identik dengan Python (< 1e-5) (6.63ms)
✔ Kontrak 3: preprocessKeypoints end-to-end identik dengan Python (< 1e-5) (14.61ms)
✔ isInSigningSpace: deteksi posisi tangan aktif vs istirahat (2.02ms)
✔ hasDetectedHands: validasi keberadaan tangan (0.53ms)
✔ SignRecognizer: supresi false positive saat tangan diam di posisi istirahat (2.83ms)
✔ SignRecognizer: supresi hasil berkeyakinan rendah (confidence threshold) (2.18ms)
✔ classifyAlphabetGeometry & FingerspellRecognizer: pengenalan bentuk abjad jari 21 titik (3.01ms)
ℹ tests 12 | pass 12 | fail 0 | cancelled 0 | skipped 0
```

### B. Pengujian Python (PyTest Suite)
Perintah:
```powershell
pytest tests/test_signbridge_suite.py tests/test_database_integration.py -q
```
Hasil:
```text
18 passed, 7 warnings in 21.85s
```

---

## 9. PANDUAN PENGUJIAN MANUAL DI BROWSER PENGGUNA

Untuk menguji langsung menggunakan webcam laptop/komputer:

1. **Jalankan Web Server Lokal** (jika belum berjalan):
   ```powershell
   python -m http.server 8000 --directory web
   ```
2. **Buka Browser**:
   Kunjungi URL: `http://localhost:8000` (disarankan menggunakan Google Chrome atau Microsoft Edge).
3. **Buka Tab Terjemahan Langsung**:
   Klik menu **"Terjemahan Langsung"** pada bilah navigasi sidebar.
4. **Nyalakan Kamera**:
   Klik tombol hijau **"Kamera Aktif"**. Berikan izin akses webcam pada prompt browser.
5. **Uji 1: Posisi Diam / Tangan Istirahat (Verifikasi Perbaikan)**:
   - Duduk rileks di depan kamera dengan tangan berada di atas meja atau di pangkuan.
   - **Ekspektasi**: Badge status menampilkan *"Posisi Netral (Tangan Istirahat)"* atau *"Siap Berisyarat (Menunggu Gerakan)"*.
   - **Hasil**: **TIDAK ADA kata yang muncul secara acak, dan TIDAK ADA suara TTS yang keluar sendiri!**
6. **Uji 2: Peragaan Isyarat Kata BISINDO (Dinamis)**:
   - Angkat satu atau kedua tangan ke depan dada (ruang isyarat).
   - Peragakan isyarat kata (contoh: `SAYA` dengan menunjuk dada, atau `MAKAN` dengan menguncupkan jari ke arah mulut).
   - Turunkan tangan sejenak setelah selesai.
   - **Ekspektasi**: Badge berubah ke *"Merekam Gerakan (N frame)"*, lalu *"Inferensi M0 ONNX..."*, dan kata muncul di pita kalimat dengan keyakinan >= 60%.
7. **Uji 3: Peragaan Abjad Ejaan Jari (Statis A-Z)**:
   - Angkat satu tangan di depan dada dan bentuk salah satu huruf (misalnya bentuk huruf `B` dengan 4 jari tegak, atau `Y` dengan jempol dan kelingking terbuka).
   - Tahan posisi selama ~0.4 detik.
   - **Ekspektasi**: Huruf terdeteksi pada panel ejaan jari dan dapat dirangkai menjadi kata.
8. **Uji 4: Ganti Mode Pengenalan**:
   - Gunakan menu pilihan mode di bagian kontrol untuk beralih antara:
     - **Hibrid (Isyarat & Abjad)** — Default rekomendasi.
     - **Isyarat Kata Saja (32 WL-BISINDO)**.
     - **Ejaan Abjad Jari Saja (A-Z)**.

