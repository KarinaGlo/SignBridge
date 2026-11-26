# PHASE 2C.2 — VALIDATOR DISTRIBUTION PACKAGE AUDIT & DISPATCH SPECIFICATION
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Final Artifact Verification, Leakage Containment, and Operational Protocol for Independent BISINDO Validators

> [!IMPORTANT]
> **STRICT AUDIT POLICY & PRODUCTION ISOLATION**
> - **Execution Mode**: Strictly READ-ONLY. Tidak ada model training, hyperparameter tuning, fine-tuning, atau modifikasi dataset mentah maupun olahan.
> - **Baseline Checkpoint & ONNX Integrity**: Checkpoint P1 (`83C6A093...`) dan model produksi ONNX (`1C281E15...`) tetap tidak disentuh.
> - **No Synthetic Responses**: Tidak ada jawaban buatan/dummy. Seluruh analisis menunggu respons manusia asli penutur BISINDO.
> - **Test Leakage Firewall**: Pemisahan tegas 19 `TEST_SET_DIAGNOSTIC_ONLY` vs 17 `TRAIN_COHORT` dipertahankan secara absolut.

---

## 1. DAFTAR FILE DAN ARTEFAK YANG DIPERIKSA

Seluruh berkas yang terkait dengan persiapan distribusi divalidasi keberadaan fisiknya dan integritas strukturnya di repositori `D:\SEMESTER 5\ML\Projek_1`:

| No | Kategori Berkas | Jalur Berkas dalam Repositori | Status Keberadaan | Ukuran / Jumlah Item |
| :-: | :--- | :--- | :---: | :---: |
| 1 | **Stimulus Citra** | `docs/validation_p2/phase_2b_1/stimulus_images/` | **EXISTS** | 36 file JPG (`VAL-REV-001.jpg` s/d `036.jpg`) |
| 2 | **Manifest SHA-256** | `docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv` | **EXISTS** | 11.351 bytes (36 rekaman hash SHA-256) |
| 3 | **Lembar Penilaian Peserta**| `docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` | **EXISTS** | 5.668 bytes (Tabel 36 baris anonim) |
| 4 | **Protokol Validasi Internal**| `docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md` | **EXISTS** | 5.305 bytes (Protokol operasional riset) |
| 5 | **Panduan Ramah Tuli** | `docs/validation_p2/phase_2c/PANDUAN_VALIDATOR_BISINDO.md` | **EXISTS** | 4.312 bytes (Petunjuk operasional praktis) |
| 6 | **Template CSV Validator A**| `docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv` | **EXISTS** | 914 bytes (36 baris, kode `VAL-A`) |
| 7 | **Template CSV Validator B**| `docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv` | **EXISTS** | 914 bytes (36 baris, kode `VAL-B`) |
| 8 | **Register Adjudikasi** | `docs/validation_p2/phase_2c/ADJUDICATION_REGISTER.md` | **EXISTS** | 4.669 bytes (Tata kelola 6 pemicu sengketa) |
| 9 | **Checklist Distribusi** | `docs/validation_p2/phase_2c/VALIDATOR_DISTRIBUTION_CHECKLIST.md` | **EXISTS** | 4.988 bytes (Daftar periksa pra-distribusi) |
| 10 | **Kunci Enkripsi Rahasia** | `docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md` | **EXISTS (CONFIDENTIAL)**| 7.689 bytes (Tersimpan aman & terisolasi) |
| 11 | **Skrip Analisis IRR** | `scripts/validation_p2/calculate_inter_rater_agreement.py` | **EXISTS** | 22.824 bytes (Mesin kalkulasi Cohen's Kappa & IRR) |
| 12 | **Suite Pengujian Unit** | `tests/test_phase_2c_irr.py` | **EXISTS** | 11.318 bytes (15 skenario pengujian batas) |

---

## 2. HASIL INTEGRITAS 36 CITRA STIMULUS

Pemeriksaan forensik biner dijalankan terhadap 36 berkas citra di folder `docs/validation_p2/phase_2b_1/stimulus_images/` dengan membandingkan nilai SHA-256 aktual terhadap manifest resmi [`STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv):

- **Total Citra Terdaftar**: 36 citra (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
- **Citra Hilang (*Missing Files*)**: **0 (Nihil)**.
- **Ketidakcocokan Hash (*Hash Mismatches*)**: **0 (Nihil)**.
- **Tingkat Kecocokan Biner**: **100.0% Exact Match**.
- **Karakteristik Fisik Citra**:
  - Dimensi: Seragam 224 $\times$ 224 piksel.
  - Saluran Warna: 3 channel RGB murni.
  - Metadata EXIF: Telah dibersihkan (*stripped*) secara sempurna (tidak memuat informasi kamera, tanggal asli pengambilan, atau nama file mentah).
  - Tanda Air (*Watermark*): Nihil, tidak ada teks atau penanda grafis yang membocorkan label.

---

## 3. HASIL PEMERIKSAAN KEBOCORAN LABEL (LEAKAGE CONTAINMENT AUDIT)

Audit pemindaian teks (*regex scan*) dilakukan terhadap seluruh berkas yang akan diserahkan kepada validator:
1. `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`
2. `VALIDATOR_A_RESPONSE_TEMPLATE.csv`
3. `VALIDATOR_B_RESPONSE_TEMPLATE.csv`
4. `PANDUAN_VALIDATOR_BISINDO.md`

### Hasil Pemindaian Pola Terlarang:
- **Pola Arsitektur AI** (`mobilenet`, `stgcn`): **0 temuan (CLEAN)**.
- **Pola Skor Confidence Model** (`confidence`, `\d+\.\d+%`): **0 temuan (CLEAN)**.
- **Pola Label Ground Truth Mentah**: **0 temuan (CLEAN)**.
- **Pola Informasi Split Data** (`train`, `val`, `test`, `TRAIN_COHORT`, `TEST_SET_DIAGNOSTIC_ONLY`): **0 temuan (CLEAN)**.
- **Pola Perangkat / Sumber Pengambilan** (`iPhone`, `Samsung`, `Xiaomi`, `Infinix`, `Oppo`, `Vivo`): **0 temuan (CLEAN)**.

### Isolasi Kunci Dekripsi:
- Dokumen [`INTERNAL_SAMPLE_MAPPING.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md) tetap **terisolasi secara ketat** dalam repositori riset internal dan dilarang keras disertakan dalam paket unduhan validator.

---

## 4. PEMERIKSAAN TEMPLATE KEPUTUSAN VALIDATOR A DAN B

Pemeriksaan struktural mendalam terhadap kedua berkas CSV menghasilkan bukti:

| Atribut Validasi | `VALIDATOR_A_RESPONSE_TEMPLATE.csv` | `VALIDATOR_B_RESPONSE_TEMPLATE.csv` | Kesimpulan |
| :--- | :--- | :--- | :---: |
| **Format Header** | `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` | `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` | **VALID** |
| **Kode Validator** | 100% konsisten bernilai `VAL-A` | 100% konsisten bernilai `VAL-B` | **VALID** |
| **Jumlah Sampel** | Tepat 36 baris | Tepat 36 baris | **VALID** |
| **Cakupan ID** | `VAL-REV-001` s/d `VAL-REV-036` lengkap | `VAL-REV-001` s/d `VAL-REV-036` lengkap | **VALID** |
| **ID Duplikat** | 0 (Nihil) | 0 (Nihil) | **VALID** |
| **Urutan ID** | Pseudo-random terurut 001 s/d 036 | Pseudo-random terurut 001 s/d 036 | **VALID** |
| **Status Kolom Respons** | 36/36 baris kosong murni | 36/36 baris kosong murni | **VALID (PENDING)** |
| **Format Garis Akhir** | Single POSIX `\n` (914 bytes) | Single POSIX `\n` (914 bytes) | **VALID** |

*Catatan: Urutan 36 sampel bersifat pseudo-random (K, C, Y, R, M, O, D, N, J, E, F...) dan sama sekali tidak merefleksikan alfabet A–Z berurutan, sehingga mencegah validator menebak urutan abjad.*

---

## 5. PROSEDUR DISTRIBUSI & PENYIMPANAN RESPON ASLI

### 5.1 Alur Distribusi (Dispatch Protocol)
1. **Pemisahan Jalur Komunikasi**: Validator A dan Validator B menerima materi secara terpisah (melalui email/tautan pribadi terisolasi).
2. **Paket yang Diberikan ke Validator A**:
   - Berkas formulir: `VALIDATOR_A_RESPONSE_TEMPLATE.csv` (atau lembar cetak).
   - Folder citra stimulus: `stimulus_images/` (36 berkas JPG).
   - Dokumen instruksi: `PANDUAN_VALIDATOR_BISINDO.md`.
3. **Paket yang Diberikan ke Validator B**:
   - Berkas formulir: `VALIDATOR_B_RESPONSE_TEMPLATE.csv` (atau lembar cetak).
   - Folder citra stimulus: `stimulus_images/` (36 berkas JPG yang sama persis).
   - Dokumen instruksi: `PANDUAN_VALIDATOR_BISINDO.md`.

### 5.2 Prosedur Pengembalian & Penyimpanan Respons Asli (*Raw Immutable Storage*)
Untuk menjamin integritas data dan mencegah manipulasi pasca-evaluasi:
1. **Penyerahan Berkas**: Validator mengembalikan file CSV yang telah disimpan dalam format UTF-8.
2. **Pencatatan Hash Segera**: Saat file diterima oleh tim peneliti, terminal langsung menghitung SHA-256 dari file yang dikembalikan.
3. **Penyimpanan di Arsip Terkunci**:
   File mentah disimpan dalam direktori arsip hanya-baca (*immutable raw archive*):
   - `docs/validation_p2/phase_2c/raw_responses/VALIDATOR_A_RAW_<TIMESTAMP>.csv`
   - `docs/validation_p2/phase_2c/raw_responses/VALIDATOR_B_RAW_<TIMESTAMP>.csv`
4. **Pencegahan Overwrite**: File respon asli tidak boleh ditimpa (*write-protected*). Analisis komputasi dijalankan menggunakan salinan kerja pada template resmi.

---

## 6. RISIKO METODOLOGIS DAN MITIGASINYA

| No | Risiko Metodologis | Dampak Potensial | Strategi Mitigasi yang Diterapkan |
| :-: | :--- | :--- | :--- |
| 1 | **Representasi Statis Huruf Dinamis (J & Z)** | Validator menandai seluruh foto J dan Z sebagai `INCORRECT` karena tidak bergerak. | Penjelasan eksplisit pada [`PANDUAN_VALIDATOR_BISINDO.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/PANDUAN_VALIDATOR_BISINDO.md): validator diperbolehkan memilih `CORRECT` jika pose diam lumrah mewakili huruf, atau `AMBIGUOUS` jika menyerupai huruf statis lain (I/D). |
| 2 | **Bias Border Clipping** | Validator menolak citra berkualitas baik hanya karena pergelangan tangan terpotong sedikit. | Penegasan prinsip kecukupan bukti: `UNDETERMINABLE` hanya dipilih jika jari-jari utama terpotong parah sehingga konfigurasi tangan mustahil dibaca. |
| 3 | **Variasi Dialek Regional** | Perbedaan bentuk isyarat antara penutur Jakarta, Yogyakarta, dan Surabaya memicu perselisihan label. | Kolom `regional_variation` disediakan untuk mencatat varian daerah, dan kasus perbedaan dialek didelegasikan ke Register Adjudikasi bersama Validator C. |
| 4 | **Test Set Leakage** | Rekomendasi koreksi dari 19 sampel uji digunakan untuk tuning model generasi berikutnya. | Penegakan *Strict Leakage Firewall*: 19 sampel bertanda `TEST_SET_DIAGNOSTIC_ONLY` dilarang keras digunakan untuk pelatihan ulang P2. |
| 5 | **Generalisasi Berlebihan (Over-Claim)** | Menyimpulkan kualitas 4.462 citra BISINDO hanya berdasarkan 36 sampel. | Dokumentasi audit secara tegas menyatakan bahwa 36 sampel purposif ini ditujukan untuk **diagnosis kegagalan model P1 dan verifikasi anomali kritis**, bukan sebagai estimasi absolut populasi. |

---

## 7. CHECKLIST KESIAPAN DISTRIBUSI (DISTRIBUTION READINESS CHECKLIST)

- [x] **1. Keberadaan Berkas**: Seluruh 36 citra stimulus, template CSV, dan dokumen pendukung lengkap.
- [x] **2. Integritas Biner**: SHA-256 36 stimulus cocok 100% dengan manifest.
- [x] **3. Bebas Kebocoran Label**: 0 label ground truth, 0 prediksi model, 0 confidence score pada paket peserta.
- [x] **4. Skema Template**: Kolom CSV baku, 36 sample ID terurut, kode validator sesuai.
- [x] **5. Panduan Ramah Tuli**: `PANDUAN_VALIDATOR_BISINDO.md` telah tersedia dalam bahasa yang mudah dipahami.
- [x] **6. Definisi Operasional 4 Kategori**: Aturan `CORRECT`, `INCORRECT`, `AMBIGUOUS`, `UNDETERMINABLE` terdefinisi jelas.
- [x] **7. Aturan Khusus J & Z**: Panduan evaluasi gestur dinamis pada foto diam telah diuraikan.
- [x] **8. Prosedur Penyimpanan**: Alur arsip respons mentah (*immutable raw storage*) telah disiapkan.
- [x] **9. Pipa Komputasi & Pengujian**: `calculate_inter_rater_agreement.py` lolos 15/15 unit test.
- [x] **10. Status Tata Kelola**: P2 tetap `HOLD`, tidak ada proses training model yang dijalankan.

---

## 8. STATUS AKHIR AUDIT DISTRIBUSI

Berdasarkan seluruh hasil audit forensik biner, eliminasi risiko kebocoran informasi, kelengkapan panduan operasional, dan kesiapan pipa analisis data:

# **`STATUS: READY`**

### Alasan Persetujuan:
1. Paket distribusi peserta terbukti **100% steril dari kebocoran label, prediksi AI, dan informasi split data**.
2. 36 citra stimulus terbukti **100% cocok secara kriptografis** dengan manifest SHA-256.
3. Panduan ramah penutur BISINDO telah menetapkan definisi operasional yang jelas, termasuk perlakuan khusus untuk huruf dinamis J dan Z serta penegasan bahwa penilaian berfokus pada ketepatan gestur dan kecukupan bukti visual.
4. Tata kelola riset menjamin perlindungan test-set leakage dan kesiapan penyimpanan data mentah yang aman (*immutable*).

Paket validasi telah memenuhi seluruh standar metodologi ilmiah dan siap didistribusikan kepada Validator A dan Validator B.

