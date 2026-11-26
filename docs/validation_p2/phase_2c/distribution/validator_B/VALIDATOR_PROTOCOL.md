# PROTOKOL OPERASIONAL VALIDASI BUTA BISINDO (VALIDATOR PROTOCOL)
## Modul Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)
#### Standar Operasional: BLINDED_VALIDATOR_REVIEW & BLIND LETTER IDENTIFICATION (Phase 2C.8)

---

## 1. Tujuan Validasi (Validation Objectives)

1. **Verifikasi Linguistik Independen**: Memverifikasi keabsahan linguistik dan kualitas visual 36 sampel representatif fingerspelling BISINDO secara objektif menggunakan metodologi **BLINDED_VALIDATOR_REVIEW**. Penilaian dilakukan secara independen dan blinded. Validator tidak diberi tahu label asli, prediksi model, maupun skor model. Tim peneliti tetap menyimpan mapping internal untuk keperluan audit dan adjudikasi.
2. **Identifikasi Huruf Mandiri (Blind Letter Identification)**: Mengumpulkan data identifikasi huruf alami dari penutur asli BISINDO secara buta tanpa bias konfirmasi dari label bawaan atau rekomendasi AI.
3. **Audit Kualitas Visual & Kebisingan Label (*Label Noise*)**: Mengukur keterbacaan gestur pada sampel dengan variasi pencahayaan ekstrem, kekaburan (*motion blur*), dan pemotongan tepi bingkai (*border clipping*).
4. **Penetapan Batas Representasi Huruf Dinamis (J dan Z)**: Penilaian menggunakan stimulus foto statis. Keputusan `IDENTIFIED` hanya menunjukkan bahwa pose statis dapat dikenali sebagai representasi awal/akhir huruf oleh validator. Penilaian foto statis **tidak membuktikan ketepatan lintasan gerakan dinamis**. Jika pose tidak cukup informatif atau meragukan, validator berhak memilih `AMBIGUOUS` atau `UNDETERMINABLE` sesuai kondisi bukti visual nyata tanpa memaksakan pilihan `IDENTIFIED`.

---

## 2. Kualifikasi Validator yang Dibutuhkan (Validator Qualifications)

Untuk menjamin validitas metodologis dan etika komunitas Tuli, validator wajib memenuhi kriteria berikut:
1. **Penutur Asli / Fasih BISINDO**: Individu Tuli (*Deaf*) atau juru bahasa isyarat tersertifikasi yang menggunakan BISINDO sebagai sarana komunikasi utama harian.
2. **Keahlian Linguistik / Pedagogis**: Memiliki pengalaman sebagai instruktur BISINDO, pemerhati bahasa isyarat, atau pengurus organisasi Tuli (seperti GERKATIN atau Pusat Bahasa Isyarat Indonesia / PUSBISINDO).
3. **Independensi Riset**: Bukan anggota tim pengembang model SignBridge, tidak terlibat dalam proses pelatihan model P1, dan tidak memiliki konflik kepentingan komersial.
4. **Pemisahan Pengujian**: **Minimal 2 (dua) validator independen** (Validator A dan Validator B) yang bekerja secara terpisah dan terisolasi tanpa saling berkomunikasi selama pengisian instrumen.

---

## 3. Instruksi Penilaian Langkah-demi-Langkah (Scoring Instructions)

1. Validator menerima paket instrumen yang terdiri dari:
   - Buku kerja interaktif `VALIDATOR_B_WORKBOOK.xlsx` (atau `VALIDATOR_A_WORKBOOK.xlsx`) sebagai media pengisian utama dengan pratinjau citra tersemat.
   - Folder stimulus mandiri `stimulus_images/` (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`) untuk peninjauan resolusi tinggi.
   - Dokumen pendukung `PANDUAN_VALIDATOR_BISINDO.md` dan `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`.
2. Untuk setiap baris sampel (`VAL-REV-001` s/d `VAL-REV-036`):
   - **Amati Citra Stimulus**: Periksa konfigurasi jari, orientasi telapak tangan, sudut pandang kamera, dan kelengkapan bukti visual.
   - **Identifikasi Huruf (`identified_letter`)**: Tuliskan satu huruf kapital (A–Z) yang diperagakan. Jika gestur tidak terbaca sama sekali atau rusak, kosongkan kolom ini.
   - **Tentukan Kejelasan Isyarat (`decision`)**:
     - **`IDENTIFIED`**: Konfigurasi tangan sah, jelas, wajar, dan pasti membentuk satu huruf alfabet BISINDO.
     - **`AMBIGUOUS`**: Konfigurasi jari meragukan, berada di antara dua bentuk huruf, atau sudut kamera menyamarkan pose.
     - **`UNDETERMINABLE`**: Kualitas foto rusak parah, terlalu gelap/silau, kabur total, atau jari kunci terpotong oleh bingkai foto sehingga tidak dapat dinilai secara objektif.
   - **Variasi Daerah (`regional_variation`)**: Pilih `YES` jika isyarat mencerminkan dialek daerah tertentu, `NO` jika bentuk standar umum/nasional, atau `UNSURE` jika ragu.
   - **Catatan (`notes`)**: Cantumkan rincian variasi daerah atau alasan teknis ketidakbacaan foto.
3. Setelah seluruh 36 sampel selesai dinilai, simpan buku kerja dan serahkan kepada fasilitator riset.

---

## 4. Analisis Reliabilitas & Penanganan Sengketa (Reliability & Adjudication)

1. **Perhitungan Reliabilitas Inter-Rater**:
   - Setelah respons Validator A dan B diterima, script analisis [`scripts/validation_p2/calculate_inter_rater_agreement.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p2/calculate_inter_rater_agreement.py) menghitung:
     - Persentase kesepakatan identifikasi huruf ($P_{o,\text{letter}}$).
     - Kesepakatan kejelasan gestur: Observed agreement ($P_{o,\text{clarity}}$), Cohen's Kappa ($\kappa_{\text{clarity}}$), Fleiss SE, dan 95% Selang Kepercayaan (Bootstrap CI) via Paired Bootstrap Resampling ($B=2000$, seed=42).
     - Tingkat kesepakatan variasi regional.
2. **Mekanisme Adjudikasi Pihak Ketiga (Validator C / VAL-C)**:
   - Sampel didaftarkan ke dalam [`ADJUDICATION_REGISTER.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/ADJUDICATION_REGISTER.md) jika memicu salah satu kondisi:
     - Perbedaan huruf teridentifikasi (`VAL-A` beda huruf dengan `VAL-B`).
     - Perbedaan keputusan kejelasan (`IDENTIFIED` vs `AMBIGUOUS`/`UNDETERMINABLE`).
     - Salah satu atau kedua validator menandai `AMBIGUOUS` atau `UNDETERMINABLE`.
     - Divergensi variasi daerah (`YES` vs `NO`).
   - **Validator C (Adjudicator Senior PUSBISINDO)** melakukan evaluasi penentu secara independen dalam kondisi *blinded* untuk menetapkan konsensus akhir.

---

## 5. Larangan Keras & Perlindungan Etika Partisipan (Strict Prohibitions & Ethics)

1. **Kerahasiaan Evaluasi & Nol Kebocoran Informasi (*Zero Leakage Mandate*)**:
   - Evaluasi ini bersifat mandiri dan buta (*blinded review*). Validator mengevaluasi gestur secara murni tanpa bantuan komputer, intervensi fasilitator, atau petunjuk jawaban apa pun.
   - Fasilitator dilarang memberikan petunjuk lisan, isyarat, atau ekspresi wajah yang mengarahkan penilaian validator.
2. **Perlindungan Data & Hak Partisipan**:
   - Hak privasi validator dilindungi sepenuhnya. Identitas validator dianonimkan menjadi kode `VAL-A` dan `VAL-B` pada seluruh laporan publik.
   - Formulir persetujuan etika (*Informed Consent*) ditandatangani sebelum instrumen dibuka.
   - Partisipasi bersifat sukarela dan validator berhak meminta jeda istirahat selama sesi penilaian.
