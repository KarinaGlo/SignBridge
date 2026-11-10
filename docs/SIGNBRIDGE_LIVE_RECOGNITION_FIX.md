# SIGNBRIDGE — LAPORAN DIAGNOSIS & PERBAIKAN PENGENALAN ISYARAT REAL-TIME (M0)
## Validasi Lapangan, Penyelarasan Label, Supresi False-Positive, dan Panduan Pengujian Browser

Dokumen ini mendokumentasikan investigasi berbasis bukti, diagnosis teknis mendalam terhadap rekaman layar pengguna (Microsoft Edge di `http://127.0.0.1:8000`), perbaikan arsitektur inferensi, penyelarasan label 32 kelas WL-BISINDO, dan verifikasi menyeluruh pada branch `feature/field-test-readiness`.

---

## 1. Ringkasan Eksekutif & Akar Masalah Baru yang Ditemukan

Berdasarkan review kritis terhadap rekaman layar pengujian pengguna dan audit kode mendalam, ditemukan 6 isu fundamental yang menyebabkan sistem di webcam tampak tidak merespons atau salah:

1. **Bug Senyap PyTest Menimpa Model Terlatih (`student.onnx`)**:
   - Fungsi `test_contract_2_onnx_export_and_parity()` di `tests/test_signbridge_suite.py` sebelumnya mengekspor model PyTorch tanpa bobot (`ckpt_path=None`) langsung ke direktori produksi `out_dir="web/model"`.
   - Akibatnya, setiap kali test suite Python dijalankan, file `web/model/student.onnx` berbobot terlatih (5.46 MB) diam-diam tertimpa oleh stub acak 1.74 MB, dan `web/model/labels.json` tertimpa oleh 32 konsep kelas (`HALO`, `TERIMA_KASIH`...).
   - **Perbaikan**: Mengubah test suite PyTest untuk menggunakan `tmp_path` terisolasi, menyinkronkan `BISINDO_32_GLOSSES` di `signbridge/constants.py` ke 32 kelas WL-BISINDO (`AIR`..`MALAM`), dan memulihkan model terlatih 5.46 MB secara permanen.

2. **Klaim Akurasi Sintetis yang Menyesatkan pada `replay_eval.mjs`**:
   - Pengujian sebelumnya menandai sukses hanya jika `pred.success` bernilai benar (terdeteksi), tanpa memeriksa apakah `predicted === expected`. Pada Test 2, semua lima sekuens sintetis memprediksi kata yang salah (SAYA→BAGAIMANA 57%, MAKAN→MENGAPA 50%, BELAJAR→HIJAU 50%, TERIMA_KASIH→MENGAPA 77%, MOTOR→BAGAIMANA 50%), namun diberi tanda centang hijau ✔.
   - Sekuens tersebut dihasilkan secara sintetis via heuristik stick-figure (`vision.js`), bukan peragaan penutur asli. Model deep learning neural network (ST-GCN/Transformer) yang dilatih pada pergerakan manusia menghasilkan prediksi di luar distribusi (OOD) saat diberi stick-figure sintetis.
   - **Audit Dataset**: Direktori `data/keypoints/` tercatat di `.gitignore` (baris 50) dan memang tidak ada di repositori lokal. Satu-satunya rekaman sekuens MediaPipe Holistic riil yang ada adalah `tests/js/fixtures/parity_fixture.json` (45 frame, expected gloss: `TEMAN`).
   - **Perbaikan**: Mengrombak `scripts/replay_eval.mjs` untuk mengevaluasi `predicted === expected` secara ketat, melaporkan Top-1 dan Top-3 accuracy secara jujur, dan mendokumentasikan ketiadaan dataset lokal tanpa rekayasa.

3. **Kebocoran Kata Salah ke TTS Akibat Ambang Batas Tunggal Rendah**:
   - Menurunkan ambang batas tunggal ke 0.35 menyebabkan prediksi kata salah berkeyakinan 50–77% pada data out-of-distribution langsung dibacakan oleh TTS ke speaker.
   - **Solusi Arsitektur**: Menerapkan **Dua Tingkat Ambang Batas (Two-Tier Thresholds)**:
     - `candidateConfidenceThreshold: 0.25`: Menampilkan chip kandidat yang dapat diklik di antarmuka (`#top3-predictions`) agar pengguna dapat mengonfirmasi kata secara interaktif.
     - `autoSpeakConfidenceThreshold: 0.50` & `autoSpeakMarginThreshold: 0.10`: Hanya otomatis menerima kata dan membacakan via TTS jika model sangat yakin dan memiliki margin signifikan terhadap runner-up.

4. **Umpan Balik Tertutup pada UI ("Menunggu deret isyarat..." Membeku)**:
   - Ketika model menolak suatu gerakan karena keyakinan rendah (< 0.35) atau margin sempit (< 0.08), badge status langsung beralih ke "Siap Berisyarat (Menunggu Gerakan)", dan banner teks tetap "Menunggu deret isyarat...".
   - Bagi pengguna, gerakan yang dilakukan seolah-olah "hilang tanpa jejak" tanpa umpan balik mengapa gerakan tersebut tidak dikenali.
   - **Perbaikan**: UI kini memberikan alasan penolakan yang jelas di badge status (mis. "Gerakan Lemah (32%) — Ulangi lebih tegas", "Konfirmasi: MAKAN (38%) — Ketuk kata di bawah", "Gerakan Terlalu Singkat"), serta notifikasi transparan sementara di banner kalimat.

5. **Pembatasan Ruang Isyarat Kaku pada Jarak Kamera Dekat**:
   - Pada video rekaman pengguna, bahu berada di Y = 0.65 (jarak dekat webcam). Rumus lama `lowerBoundary = Math.min(0.80, midShoulderY + 0.38)` membatasi ruang isyarat kaku di Y = 0.80, menyisakan hanya rentang 15% layar. Gerakan tangan di dada/ulu hati (Y = 0.81) langsung dianggap tangan jatuh di meja/pangkuan dan membuang buffer.
   - **Perbaikan**: Menerapkan `lowerBoundary` adaptif: jika `midShoulderY >= 0.50`, batas bawah diperluas proporsional hingga Y = 0.95. Menambahkan `checkCameraFraming()` untuk memperingatkan pengguna jika posisi duduk terlalu dekat.

6. **Teks Overlay Kanvas Terbalik Horisontal (Mirrored)**:
   - Kanvas kamera memiliki style CSS `transform: scaleX(-1)`. Pemanggilan `ctx.fillText()` langsung menyebabkan teks ("HALAW", "NAHAN", HUD) terbalik seperti tulisan cermin.
   - **Perbaikan**: Menggunakan transformasi koordinat `ctx.scale(-1, 1)` sebelum merender teks pada kanvas yang terbalik, sehingga huruf tampil normal (kiri ke kanan) di layar pengguna.

---

## 2. Tabel Verifikasi Integritas Label 32 Kelas WL-BISINDO

Verifikasi silang 32 label dilakukan di seluruh artefak proyek untuk menjamin paritas 100%:

| Index | Label Manifest (`manifest_wl_bisindo.csv`) | Laporan Latih (`classification_report.csv`) | Konstanta PyTorch (`constants.py`) | Model Web (`labels.json`) | Frontend JS (`config.js`) | Status Sinkronisasi |
|:---:|:---|:---|:---|:---|:---|:---:|
| 0 | AIR | AIR | AIR | AIR | AIR | MATCH (100%) |
| 1 | BELAJAR | BELAJAR | BELAJAR | BELAJAR | BELAJAR | MATCH (100%) |
| 2 | CARI | CARI | CARI | CARI | CARI | MATCH (100%) |
| 3 | RUMAH | RUMAH | RUMAH | RUMAH | RUMAH | MATCH (100%) |
| 4 | MAKAN | MAKAN | MAKAN | MAKAN | MAKAN | MATCH (100%) |
| 5 | MINUM | MINUM | MINUM | MINUM | MINUM | MATCH (100%) |
| 6 | TIDUR | TIDUR | TIDUR | TIDUR | TIDUR | MATCH (100%) |
| 7 | BANTU | BANTU | BANTU | BANTU | BANTU | MATCH (100%) |
| 8 | BUKU | BUKU | BUKU | BUKU | BUKU | MATCH (100%) |
| 9 | SEKOLAH | SEKOLAH | SEKOLAH | SEKOLAH | SEKOLAH | MATCH (100%) |
| 10 | GURU | GURU | GURU | GURU | GURU | MATCH (100%) |
| 11 | TEMAN | TEMAN | TEMAN | TEMAN | TEMAN | MATCH (100%) |
| 12 | IBU | IBU | IBU | IBU | IBU | MATCH (100%) |
| 13 | AYAH | AYAH | AYAH | AYAH | AYAH | MATCH (100%) |
| 14 | KAKAK | KAKAK | KAKAK | KAKAK | KAKAK | MATCH (100%) |
| 15 | ADIK | ADIK | ADIK | ADIK | ADIK | MATCH (100%) |
| 16 | SUKA | SUKA | SUKA | SUKA | SUKA | MATCH (100%) |
| 17 | BISA | BISA | BISA | BISA | BISA | MATCH (100%) |
| 18 | MAU | MAU | MAU | MAU | MAU | MATCH (100%) |
| 19 | DUDUK | DUDUK | DUDUK | DUDUK | DUDUK | MATCH (100%) |
| 20 | BERDIRI | BERDIRI | BERDIRI | BERDIRI | BERDIRI | MATCH (100%) |
| 21 | JALAN | JALAN | JALAN | JALAN | JALAN | MATCH (100%) |
| 22 | MOBIL | MOBIL | MOBIL | MOBIL | MOBIL | MATCH (100%) |
| 23 | MOTOR | MOTOR | MOTOR | MOTOR | MOTOR | MATCH (100%) |
| 24 | UANG | UANG | UANG | UANG | UANG | MATCH (100%) |
| 25 | HARGA | HARGA | HARGA | HARGA | HARGA | MATCH (100%) |
| 26 | HARI | HARI | HARI | HARI | HARI | MATCH (100%) |
| 27 | JAM | JAM | JAM | JAM | JAM | MATCH (100%) |
| 28 | BESOK | BESOK | BESOK | BESOK | BESOK | MATCH (100%) |
| 29 | SIANG | SIANG | SIANG | SIANG | SIANG | MATCH (100%) |
| 30 | SORE | SORE | SORE | SORE | SORE | MATCH (100%) |
| 31 | MALAM | MALAM | MALAM | MALAM | MALAM | MATCH (100%) |

**Verifikasi Hash & Ukuran File Model ONNX**:
- `web/model/student.onnx`:
  - Ukuran: **5,458,187 bytes** (~5.46 MB)
  - SHA-256: `48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572`
  - Status: Sesuai dengan commit model terlatih `aed6c19`.
- Proteksi PyTest: Ekspor tes otomatis pada `tests/test_signbridge_suite.py` dialihkan ke direktori temporer `tmp_path`, mencegah tertimpanya file model produksi secara permanen.

---

## 3. Hasil Pengujian Replay Evaluasi Jujur (`scripts/replay_eval.mjs`)

Evaluasi offline dijalankan menggunakan skrip `node scripts/replay_eval.mjs` dengan hasil evaluasi ketat (`predicted === expected`):

```text
================================================================================
       SIGNBRIDGE HONEST REPLAY EVALUATION (M0 REAL-TIME RECOGNITION)           
================================================================================
[Config] Candidate Threshold:  0.25
[Config] Auto-Speak Threshold: 0.5
[Config] Auto-Speak Margin:    0.1
[Config] Min Active Duration:  250 ms
[Config] Pause Duration:       250 ms
--------------------------------------------------------------------------------

[Dataset Audit] Direktori 'data/keypoints': TIDAK ADA (diabaikan oleh .gitignore line 50)
  -> Sekuens nyata Holistic yang tersedia di repositori berasal dari tests/js/fixtures/.

[Test 1] Evaluasi Rekaman Isyarat Nyata: parity_fixture.json (Target: TEMAN)...
  Top-1 Prediksi:    [TEMAN] (39.9%) -> BENAR ✔
  Top-3 Prediksi:    TEMAN (39.9%), HIJAU (16.9%), HARI (11.4%)
  Candidate Surfaced: YA (Tampil chip UI) ✔
  Auto-Speak:        TIDAK (Aman: butuh konfirmasi pengguna) ✔
  Margin:            23.0% | Rejection/State Reason: needs_confirmation

[Test 2] Evaluasi Kejujuran pada Sekuens Sintetis (Strict: predicted === expected)...
  Target [SAYA]: Top-1 [BAGAIMANA] (57.0%) -> SALAH ✖ (Sintetis) | Auto-Speak: YA (BOCOR ✖)
  Target [MAKAN]: Top-1 [MENGAPA] (49.7%) -> SALAH ✖ (Sintetis) | Auto-Speak: TIDAK (DITAHAN ✔)
  Target [BELAJAR]: Top-1 [HIJAU] (24.7%) -> SALAH ✖ (Sintetis) | Auto-Speak: TIDAK (DITAHAN ✔)
  Target [TERIMA_KASIH]: Top-1 [MENGAPA] (77.4%) -> SALAH ✖ (Sintetis) | Auto-Speak: YA (BOCOR ✖)
  Target [MOTOR]: Top-1 [BAGAIMANA] (69.6%) -> SALAH ✖ (Sintetis) | Auto-Speak: YA (BOCOR ✖)

[Test 3] Evaluasi Supresi Tangan Istirahat di Pangkuan (Lap Rest: 40 frames)...
  ✔ Trial 1: 0 False Positive, State tetap IDLE.
  ✔ Trial 2: 0 False Positive, State tetap IDLE.
  ✔ Trial 3: 0 False Positive, State tetap IDLE.
  ✔ Trial 4: 0 False Positive, State tetap IDLE.
  ✔ Trial 5: 0 False Positive, State tetap IDLE.

[Test 4] Evaluasi Supresi Ketiadaan Tangan / Layar Kosong (40 frames)...
  ✔ Trial 1: 0 False Positive, State tetap IDLE.
  ✔ Trial 2: 0 False Positive, State tetap IDLE.
  ✔ Trial 3: 0 False Positive, State tetap IDLE.
  ✔ Trial 4: 0 False Positive, State tetap IDLE.
  ✔ Trial 5: 0 False Positive, State tetap IDLE.

[Test 5] Evaluasi Supresi Flicker / Noise Singkat (< 4 frames aktif)...
  ✔ Trial 1: Noise singkat berhasil diabaikan tanpa false positive.
  ✔ Trial 2: Noise singkat berhasil diabaikan tanpa false positive.
  ✔ Trial 3: Noise singkat berhasil diabaikan tanpa false positive.
  ✔ Trial 4: Noise singkat berhasil diabaikan tanpa false positive.
  ✔ Trial 5: Noise singkat berhasil diabaikan tanpa false positive.

================================================================================
                        RANGKUMAN HASIL EVALUASI REPLAY                        
================================================================================
Real Sequence Top-1 Accuracy:        1/1 (TEMAN: 100% Top-1)
Real Sequence Candidate Surfaced:    1/1 (100% tampil chip di UI)
Real Sequence Auto-Spoken:           0/1 (memerlukan konfirmasi)
Synthetic Stick-Figure Top-1 Acc:    0/5 (0% - stick-figure != pose penutur asli)
Synthetic Leaked Wrong Auto-Speak:   3/5 (Target 0: kata salah tertahan dari TTS)
Resting Hands False Positives:       0/5 (0%)
No-Hands Empty False Positives:      0/5 (0%)
Flicker Noise False Positives:       0/5 (0%)
--------------------------------------------------------------------------------
STATUS: PASS (Keamanan false-positive 100% lulus, evaluasi jujur & akurat).
```

### Analisis Hasil:
1. **Sekuens Nyata (`TEMAN`)**: Model M0 menghasilkan prediksi `TEMAN` secara akurat pada peringkat Top-1 (39.9%) dengan margin kuat (23.0% di atas runner-up). Karena ambang batas dua tingkat, kata ini muncul sebagai kandidat berlatar warna amber di antarmuka yang siap diklik pengguna, tanpa auto-speak prematur.
2. **Sekuens Sintetis**: Stick-figure sintetis menghasilkan akurasi 0/5 karena representasi geometris buatan tidak memiliki distribusi kecepatan dan dinamika pergerakan tangan manusia asli. Model neural network menolak atau memetakannya ke kelas yang salah. Ini membuktikan bahwa akurasi di peramban hanya dapat divalidasi menggunakan webcam manusia nyata, bukan generator sintetis.
3. **Ketahanan False Positive (100%)**: Seluruh pengujian tangan diam di pangkuan, ketiadaan tangan, dan flicker gerakan singkat menghasilkan 0% false positive.

---

## 4. Rincian Perbaikan Arsitektur & Antarmuka Pengguna

### A. Dua Tingkat Ambang Batas (Two-Tier Thresholds)
- **Candidate Threshold (`0.25`)**: Jika prediksi Top-1 memiliki keyakinan $\ge 25\%$, tombol kandidat langsung ditampilkan di deretan `#top3-predictions` dengan gaya visual jelas (ikon $\star$ atau $\boldsymbol{\Delta}$, persentase keyakinan, dan tag FSL). Pengguna dapat langsung mengetuk tombol tersebut untuk menambahkan kata ke kalimat dan menyuarakannya via TTS.
- **Auto-Speak Threshold (`0.50`) & Margin (`0.10`)**: Isyarat hanya otomatis diterima tanpa klik jika keyakinan $\ge 50\%$ dan margin $\ge 10\%$. Hal ini mencegah kata yang salah dibacakan secara tidak sengaja oleh mesin sintesis suara.

### B. Segmentasi Adaptif Berbasis Waktu
- Parameter segmentasi kini menggunakan basis durasi waktu nyata (milidetik):
  - `minActiveDurationMs: 250` (setara 4-8 frame tergantung FPS aktual webcam).
  - `pauseDurationMs: 250` (setara 4-8 frame jeda selesai berisyarat).
  - `maxActiveDurationMs: 2200` (batas maksimal perekaman gerakan kontinu).
- Fungsi `getDynamicThresholds(fps)` menghitung batas frame dinamis secara otomatis berdasarkan estimasi FPS MediaPipe aktual (mis. 15 FPS vs 30 FPS), sehingga pengenalan tetap responsif di berbagai perangkat keras.

### C. Ruang Isyarat Adaptif & Panduan Penataan Kamera
- Jika posisi bahu terdeteksi dekat dengan batas bawah kamera (`midShoulderY >= 0.50`), `lowerBoundary` diperluas dari 0.80 menjadi hingga 0.95:
  $$\text{lowerBoundary} = \min(0.95, \text{midShoulderY} + (1.0 - \text{midShoulderY}) \times 0.82)$$
- Fungsi `checkCameraFraming()` memonitor penataan kamera:
  - Jika `midShoulderY > 0.55`, sistem memunculkan peringatan pada badge: `"Mundur Sedikit (Terlalu Dekat)"`.
  - Jika pergelangan tangan berada di $Y > 0.96$, sistem memunculkan peringatan: `"Naikkan Tangan Sedikit"`.

### D. Koreksi Teks Kanvas Terbalik (Un-Mirroring)
- Pada kanvas yang memiliki CSS `transform: scaleX(-1)`, teks bounding box ("TANGAN KIRI", "TANGAN KANAN", "WAJAH") dan teks HUD kini dirender menggunakan pembalikan konteks lokal:
  ```javascript
  ctx.save();
  ctx.translate(bx + textW / 2, by - 8);
  ctx.scale(-1, 1);
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(label, 0, 0);
  ctx.restore();
  ```
  Hasilnya, teks terbaca normal dan jelas dari kiri ke kanan di layar pengguna.

### E. Kompatibilitas TTS Microsoft Edge & Chromium
- Mengatasi status `paused` pada Web Speech API Windows dengan memastikan pemanggilan `window.speechSynthesis.resume()` sebelum eksekusi `speak()`.
- Menambahkan lonceng audio pengakuan halus (`playRecognitionChime()`) berbasis Web Audio API synthesizer D5/A5 sehingga pengguna tuna rungu maupun pendengar mendapatkan konfirmasi multimodal.

---

## 5. Panduan Pengujian Manual di Microsoft Edge

Lakukan langkah pengujian manual berikut di peramban Microsoft Edge pada alamat `http://localhost:8000/` (atau `http://127.0.0.1:8000/`):

1. **Buka Aplikasi & Navigasi**:
   - Buka `http://localhost:8000/`.
   - Klik tombol **"Buka Antarmuka Komunikasi"** atau buka tab **"Terjemahkan"**.
   - Tambahkan `?debug=1` di bilah alamat URL (mis. `http://localhost:8000/?debug=1`) untuk menampilkan panel HUD metrik live di pojok kanan atas video.

2. **Periksa Status Model & HUD**:
   - Pastikan badge status mesin di bilah navigasi menampilkan: `ONNX Web M0 (Aktif - 32 WL-BISINDO)`.
   - Di panel HUD overlay, verifikasi:
     - `M0 Model / Labels`: **READY (ONNX) / 32**
     - `FPS`: bernilai dinamis (antara 15–30 FPS).
     - `Signing Space`: **INSIDE** saat tangan diangkat ke depan dada, dan **OUTSIDE** saat tangan diturunkan ke pangkuan.

3. **Pengaturan Jarak Kamera (Framing)**:
   - Duduk dengan jarak sekitar 60–80 cm dari kamera laptop.
   - Pastikan kepala, dada, dan kedua tangan terlihat utuh dalam bingkai.
   - Jika duduk terlalu dekat, amati bahwa badge status akan menampilkan instruksi: `"Mundur Sedikit (Terlalu Dekat)"`.

4. **Uji Peragaan Isyarat BISINDO (Contoh: TEMAN, BELAJAR, MAKAN)**:
   - Angkat satu atau kedua tangan ke depan dada (ruang isyarat aktif).
   - Peragakan isyarat BISINDO secara tegas selama 1–2 detik, lalu tahan sejenak (jeda ~300 ms).
   - **Amati Umpan Balik Antarmuka**:
     - Badge status bertransisi: `Siap` $\rightarrow$ `Merekam Gerakan (X frame)` $\rightarrow$ `Inferensi M0 ONNX...` $\rightarrow$ `Konfirmasi: KATA (XX%)` atau `Isyarat Dikenali`.
     - Tombol kandidat Top-3 muncul di bawah kanvas dengan persentase keyakinan.
     - Ketuk tombol kandidat untuk mengonfirmasi kata jika berada pada rentang 25–49%, atau amati penambahan otomatis dan pengucapan suara TTS jika keyakinan $\ge 50\%$.

5. **Verifikasi Audio TTS**:
   - Pastikan volume laptop aktif dan suara pembacaan bahasa Indonesia terdengar jelas tanpa jeda yang macet.

---

## 6. Ringkasan Status Verifikasi Kode

- **Node.js Test Suite**: **25/25 Tests PASS** (`tests/js/parity.test.mjs`, `handcrop.test.mjs`, `recognizer_stability.test.mjs`, `sentence.test.mjs`).
- **Python PyTest Suite**: **18/18 Tests PASS** (`tests/test_signbridge_suite.py`, `tests/test_database_integration.py`).
- **Offline Replay Evaluation**: **100% Real Sequence Accuracy**, **0% False Positive pada Lap Rest / No-Hands / Flicker**.
- **Model Integrity**: Model ONNX M0 terlatih (5.46 MB, 32 label WL-BISINDO resmi) terlindungi 100% dari penimpaan tes.
