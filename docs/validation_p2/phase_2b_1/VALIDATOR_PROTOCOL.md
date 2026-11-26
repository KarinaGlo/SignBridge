# PROTOKOL OPERASIONAL VALIDASI BUTA BISINDO (VALIDATOR PROTOCOL)
## Modul Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Tujuan Validasi (Validation Objectives)
1. Memverifikasi keabsahan linguistik dan kualitas visual dari 36 sampel representatif fingerspelling BISINDO secara objektif tanpa bias kecerdasan buatan (*double-blind review*).
2. Mengidentifikasi dan mendokumentasikan potensi kesalahan label (*label noise*) pada data mentah warisan Mendeley.
3. Menilai keterbacaan gestur pada citra dengan anomali pemotongan batas (*border clipping*), pencahayaan ekstrem, dan kekaburan (*motion blur*).
4. Menetapkan konsensus komunitas Tuli mengenai representasi citra diam untuk huruf dinamis J dan Z.

---

## 2. Kualifikasi Validator yang Dibutuhkan (Validator Qualifications)
Untuk memastikan validitas metodologi dan etika komunitas Tuli, validator wajib memenuhi kriteria berikut:
1. **Penutur Asli / Fasih BISINDO**: Individu Tuli (*Deaf*) atau juru bahasa isyarat tersertifikasi yang menggunakan BISINDO sebagai bahasa komunikasi utama harian.
2. **Keahlian Linguistik / Pedagogis**: Memiliki pengalaman sebagai pengajar BISINDO, pemerhati bahasa isyarat, atau pengurus organisasi Tuli (seperti GERKATIN atau Pusat Bahasa Isyarat Indonesia / PUSBISINDO).
3. **Independensi Riset**: Bukan anggota tim pengembang model SignBridge, tidak terlibat dalam proses pelatihan model P1, dan tidak memiliki konflik kepentingan komersial.
4. **Jumlah Penilai**: **Minimal 2 (dua) orang validator independen** (Validator A dan Validator B) yang bekerja secara terpisah tanpa saling berkomunikasi selama pengisian instrumen.

---

## 3. Instruksi Penilaian Langkah-demi-Langkah (Scoring Instructions)
1. Validator menerima formulir `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` dan folder citra stimulus `stimulus_images/`.
2. Untuk setiap baris sampel (`VAL-REV-001` s/d `VAL-REV-036`):
   - Buka citra stimulus yang bersangkutan.
   - Periksa konfigurasi jari, orientasi telapak tangan, dan sudut pandang.
   - Tentukan keputusan:
     - **[1] Benar**: Gestur tangan valid, jelas, dan sesuai kaidah BISINDO.
     - **[2] Salah**: Gestur tangan salah peragaan atau memperagakan huruf lain. Validator wajib menuliskan huruf aktual pada kolom *Correct Letter*.
     - **[3] Ambigu**: Gestur tidak jelas, berada di antara dua huruf, atau tidak lengkap.
     - **[4] Tidak Dapat Menentukan**: Citra rusak, gelap total, atau terpotong parah sehingga jari penting tidak terlihat.
3. Catat variasi daerah jika gestur tersebut merupakan bentuk lokal (misal variasi Jawa, Sumatera, Bali) pada kolom *Regional / Dialect Variation*.
4. Bubuhkan tanda tangan dan tanggal setelah menyelesaikan seluruh 36 sampel.

---

## 4. Mekanisme Penanganan Perbedaan Pendapat & Adjudikasi (Disagreement & Adjudication)
1. **Perhitungan Inter-Rater Reliability**:
   - Setelah Validator A dan Validator B menyelesaikan evaluasi, tim peneliti menghitung nilai kesepakatan Cohen's Kappa ($\kappa$).
   - Kategori kesepakatan: $\kappa \ge 0,80$ (Hampir Sempurna), $0,60 \le \kappa < 0,80$ (Substansial), $\kappa < 0,60$ (Rendah / Butuh Adjudikasi).
2. **Mekanisme Adjudikasi (Third-Party Adjudication)**:
   - Jika terdapat sampel di mana Validator A dan Validator B memilih kategori yang berbeda (misalnya Validator A menyatakan [1] Benar dan Validator B menyatakan [2] Salah):
     - Sampel dimasukkan ke dalam daftar sengketa (*disputed samples*).
     - Dihadirkan **Validator C (Adjudicator Senior PUSBISINDO)** untuk melakukan tinjauan penentu.
     - Keputusan akhir diambil berdasarkan konsensus mayoritas (2 dari 3 suara) atau keputusan adjudicator senior disertai catatan tertulis.

---

## 5. Larangan Keras & Perlindungan Kerahasiaan (Strict Prohibitions)
1. **Larangan Kebocoran Informasi Model**:
   - Validator **dilarang keras** diperlihatkan prediksi model, skor probabilitas confidence, arsitektur model (MobileNetV3), maupun nama split (train, validation, test).
   - Peneliti yang mendampingi sesi dilarang memberikan petunjuk lisan atau isyarat mengenai jawaban yang "diharapkan" oleh model AI.
2. **Perlindungan Data & Etika Peserta**:
   - Identitas nama validator dapat dianonimkan menjadi kode `VAL-USR-01` dan `VAL-USR-02` pada laporan publik jika diminta oleh penilai.
   - Formulir persetujuan etika (*Informed Consent*) ditandatangani sebelum sesi dimulai.

---

## 6. Pemisahan Tata Kelola Hasil: Train Cohort vs Test Diagnostic
Hasil penilaian validator dikelola secara terpisah dengan aturan tegas:
1. **Sampel Kohort Latihan & Anomali Visual (17 sampel)**:
   - Memberikan umpan balik mengenai toleransi noise pada data latihan dan batas pemotongan tepi (*border clipping*).
   - Dapat digunakan untuk memperbaiki strategi data cleaning dan data augmentation pada P2.
2. **Sampel Diagnostik Data Uji (19 sampel)**:
   - Berstatus **`TEST_SET_DIAGNOSTIC_ONLY`**.
   - Digunakan semata-mata untuk mengukur apakah kesalahan model P1 ($38,8\%$) disebabkan oleh kegagalan arsitektur AI ataukah karena label pada dataset mentah memang salah sejak awal.
   - **DILARANG KERAS**: Mengubah label pada test set P1 atau menggunakan koreksi sampel uji ini untuk menaikkan skor akurasi P2 (*anti-data-leakage policy*).

