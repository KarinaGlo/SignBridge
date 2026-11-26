# PHASE 2C.3 — EXTERNAL VALIDATOR DISTRIBUTION PACKAGE REPORT
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Final Packaging, Confidentiality Sanitization, and Distribution Integrity Verification

> [!IMPORTANT]
> **GOVERNANCE & PRODUCTION RESTRICTIONS ENFORCED**
> - **Execution Mode**: Strictly READ-ONLY regarding original research artifacts, production pipelines, datasets, checkpoints, and models.
> - **Distribution Packages Isolated**: Dua paket terpisah dan mandiri telah dibuat di folder distribusi tanpa memodifikasi aset orisinal di repositori riset.
> - **Zero AI / Model Leaks**: Seluruh materi peserta telah disanitasi secara ketat; 0 penyebutan arsitektur AI, skor probabilitas confidence, nama split (train/test), atau label asli.
> - **Manual Dispatch Requirement**: Distribusi fisik/digital kepada validator wajib dilakukan secara manual oleh peneliti setelah persetujuan formal; tidak ada pengiriman otomatis.

---

## 1. STRUKTUR DAN DAFTAR BERKAS PAKET DISTRIBUSI

Dua paket distribusi terisolasi dan mandiri telah disiapkan:
- **Paket Validator A**: [`docs/validation_p2/phase_2c/distribution/validator_A/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_A/)
- **Paket Validator B**: [`docs/validation_p2/phase_2c/distribution/validator_B/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_B/)

### Rincian Inventaris Berkas per Paket:

| Komponen Berkas | Paket Validator A (`validator_A/`) | Paket Validator B (`validator_B/`) | Format | Status Integritas |
| :--- | :---: | :---: | :---: | :---: |
| **Folder Citra Stimulus** | `stimulus_images/` (36 berkas JPG) | `stimulus_images/` (36 berkas JPG) | JPG 224x224 | **100% Identik Biner** |
| **Panduan Ramah Tuli** | `PANDUAN_VALIDATOR_BISINDO.md` | `PANDUAN_VALIDATOR_BISINDO.md` | Markdown | **Identik** |
| **Lembar Review Peserta** | `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` | `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` | Markdown | **Identik** |
| **Protokol Operasional Peserta**| `VALIDATOR_PROTOCOL.md` (Sanitized) | `VALIDATOR_PROTOCOL.md` (Sanitized) | Markdown | **Identik (Sanitasi)** |
| **Template CSV Respons** | `VALIDATOR_A_RESPONSE_TEMPLATE.csv` | `VALIDATOR_B_RESPONSE_TEMPLATE.csv` | CSV (UTF-8) | **Khusus per Validator** |
| **Total Berkas dalam Paket** | **40 berkas** | **40 berkas** | - | **Lengkap & Terverifikasi** |

---

## 2. HASIL VERIFIKASI HASH KRIPTOGRAFIS SHA-256

Pemeriksaan integritas biner dilakukan terhadap seluruh 36 citra stimulus di dalam masing-masing paket distribusi dibandingkan dengan master manifest [`STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv):

| Parameter Verifikasi | Paket Validator A | Paket Validator B | Standar Toleransi |
| :--- | :---: | :---: | :---: |
| **Jumlah Citra Stimulus** | 36 / 36 | 36 / 36 | Tepat 36 |
| **Kecocokan SHA-256 vs Manifest** | **36 / 36 (100.0% MATCH)** | **36 / 36 (100.0% MATCH)** | 0 toleransi selisih |
| **Ketidakcocokan Hash (*Mismatches*)**| **0 (Nihil)** | **0 (Nihil)** | Harus 0 |
| **Berkas Hilang (*Missing Files*)** | **0 (Nihil)** | **0 (Nihil)** | Harus 0 |
| **Resolusi Citra** | 224 $\times$ 224 piksel RGB | 224 $\times$ 224 piksel RGB | Seragam |
| **Pembersihan EXIF Metadata** | Bersih (*Stripped*) | Bersih (*Stripped*) | Tanpa metadata |

---

## 3. KESETARAAN STIMULUS ANTAR-VALIDATOR (A/B EQUALITY AUDIT)

Audit komparasi *byte-by-byte* dilakukan antara berkas citra di folder `validator_A/stimulus_images/` dan `validator_B/stimulus_images/`:
- **Jumlah Pasangan Berkas**: 36 pasang.
- **Perbedaan Biner ($A \ne B$)**: **0 (Nol)**.
- **Urutan Penomoran**: Keduanya menggunakan urutan pseudo-random identik (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
- **Kesimpulan**: Validator A dan Validator B dijamin menerima **konten visual dan urutan stimulus yang sama persis**, menjamin validitas pengujian reliabilitas antar-penilai (*Inter-Rater Reliability*).

---

## 4. AUDIT KERAHASIAAN DAN PENCEGAHAN KEBOCORAN (*CONFIDENTIALITY AUDIT*)

Pemindaian teks mendalam (*deep regular expression scan*) dijalankan pada seluruh berkas dokumentasi dan template CSV di dalam kedua paket distribusi:

| Pola Informasi Terlarang | Hasil Pemindaian Paket A | Hasil Pemindaian Paket B | Keterangan & Tindakan Pengamanan |
| :--- | :---: | :---: | :--- |
| `INTERNAL_SAMPLE_MAPPING` | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Kunci enkripsi tersimpan eksklusif di repositori riset. |
| `TEST_SET_DIAGNOSTIC_ONLY` | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Tidak ada penanda split test/train pada paket peserta. |
| `TRAIN_COHORT` | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Tidak ada penanda kohort latihan pada paket peserta. |
| `MobileNet` | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Telah disanitasi dari judul dan teks protokol. |
| `confidence` & persentase skor | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Telah disanitasi dari teks protokol. |
| Nama Perangkat Mentah (iPhone, dll.)| **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Tidak ada nama kamera/ponsel sumber dataset mentah. |
| Pola Nama Berkas Mentah Asli | **0 temuan (CLEAN)** | **0 temuan (CLEAN)** | Seluruh citra murni menggunakan ID anonim `VAL-REV-xxx`. |

### Tindakan Sanitasi yang Dilakukan pada Paket Distribusi:
1. **Pemisahan Bagian Protokol**: Bagian 6 dari `VALIDATOR_PROTOCOL.md` yang memuat rincian tata kelola internal riset (17 train cohort vs 19 test diagnostic) **dikecualikan** dari berkas distribusi peserta.
2. **Sanitasi Penyebutan AI**: Penyebutan nama model `MobileNetV3` dan kata `confidence` pada `VALIDATOR_PROTOCOL.md` paket distribusi telah disanitasi menjadi pernyataan evaluasi buta mandiri (*blinded review*).
3. **Invariansi Berkas Asli**: Berkas orisinal di repositori internal ([`docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md)) **tetap utuh dan tidak diubah**.

---

## 5. AUDIT BERKAS BERLEBIH ATAU HILANG (PACKAGE INVENTORY AUDIT)

Pemeriksaan daftar file menghasilkan:
- **Paket Validator A**: Tepat 40 berkas (36 citra JPG + 4 berkas teks/CSV: `PANDUAN_VALIDATOR_BISINDO.md`, `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`, `VALIDATOR_PROTOCOL.md`, `VALIDATOR_A_RESPONSE_TEMPLATE.csv`).
- **Paket Validator B**: Tepat 40 berkas (36 citra JPG + 4 berkas teks/CSV: `PANDUAN_VALIDATOR_BISINDO.md`, `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`, `VALIDATOR_PROTOCOL.md`, `VALIDATOR_B_RESPONSE_TEMPLATE.csv`).
- **Berkas Hilang (*Missing Files*)**: **0**.
- **Berkas Berlebih / Tidak Diizinkan (*Extraneous Files*)**: **0**.

---

## 6. KESIAPAN DISTRIBUSI DAN INSTRUKSI VALIDATOR

Kedua paket telah dilengkapi dokumen instruksi ramah penutur BISINDO ([`PANDUAN_VALIDATOR_BISINDO.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/PANDUAN_VALIDATOR_BISINDO.md)) yang memuat:
1. **Operasional 4 Kategori**: `CORRECT`, `INCORRECT`, `AMBIGUOUS`, `UNDETERMINABLE`.
2. **Kewajiban Huruf Koreksi**: Wajib mengisi `correct_letter` jika memilih `INCORRECT`.
3. **Konvensi Huruf Dinamis J dan Z**: Panduan jelas mengenai evaluasi bentuk statis yang lumrah vs ambigu tanpa gerakan.
4. **Independensi Penilaian**: Kewajiban menilai mandiri tanpa diskusi antara Validator A dan B.
5. **Prosedur Pengembalian Aman**: Instruksi penyimpanan UTF-8 dan alur penghitungan hash SHA-256 saat pengembalian.

---

## 7. GIT STATUS DAN INVARIANSI REPOSITORI

Pemeriksaan status repositori Git mengonfirmasi kepatuhan penuh terhadap kebijakan *Strict Read-Only*:
- **Tracked Modifications**: **0 files modified** (`git diff --stat` kosong).
- **Aset Orisinal Riset**:
  - `docs/validation_p2/phase_2b_1/stimulus_images/`: Tidak disentuh.
  - `docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md`: Tidak disentuh.
  - `docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv`: Tidak disentuh.
  - Baseline Checkpoint P1 & ONNX: Tidak disentuh.
- Seluruh paket distribusi baru berada di direktori khusus `docs/validation_p2/phase_2c/distribution/`.

---

## 8. KESIMPULAN DAN STATUS AKHIR

Berdasarkan seluruh hasil audit integritas biner, kesetaraan stimulus, eliminasi kebocoran label, dan kesiapan berkas operasional:

# **`STATUS: READY`**

Paket distribusi `validator_A` dan `validator_B` telah **100% siap secara fisik, teknis, dan etika metodologis**. Peneliti dapat melanjutkan proses penyerahan instrumen secara manual kepada masing-masing validator independen BISINDO.

