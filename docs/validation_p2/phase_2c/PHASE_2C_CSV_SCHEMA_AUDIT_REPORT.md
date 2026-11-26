# PHASE 2C CSV VALIDATOR TEMPLATE AUDIT & SCHEMA NORMALIZATION REPORT
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Forensic CSV Inspection, Schema Validation, and Analysis Pipeline Hardening

> [!IMPORTANT]
> **GOVERNANCE & READ-ONLY ENFORCEMENT**
> - **Model Training**: STRICTLY PROHIBITED (Tidak ada proses training/fine-tuning model P2 yang dijalankan).
> - **Dataset Invariance**: Dataset mentah (*raw*), dataset olahan (*processed*), manifest utama, serta checkpoint baseline P0/P1 dan ONNX tidak dimodifikasi sama sekali.
> - **Integrity of Validator Data**: Tidak ada respon buatan (*synthetic/dummy answers*). Kolom keputusan dibiarkan kosong menunggu input nyata dari validator independen.

---

## A. EXECUTIVE SUMMARY

| Komponen Audit | Status Resmi | Keterangan Singkat |
| :--- | :---: | :--- |
| **Status Audit Menyeluruh** | **`AUDIT_PASSED`** | Seluruh pemeriksaan integritas biner, skema, dan semantik terpenuhi |
| **Status Template Validator A**| **`READY`** | 36 sampel anonim, skema 7 kolom baku, kode `VAL-A`, bersih dari anomali |
| **Status Template Validator B**| **`READY`** | 36 sampel anonim, skema 7 kolom baku, kode `VAL-B`, bersih dari anomali |
| **Kompatibilitas Skrip Analisis**| **`COMPATIBLE & HARDENED`** | `calculate_inter_rater_agreement.py` lolos seluruh uji unit edge-case |
| **Status Kesiapan Ingestion** | **`100% OPERATIONAL`** | Siap menerima file yang telah diisi tanpa risiko error parsing |
| **Status Retraining P2** | **`HOLD`** | Tetap tertahan hingga seluruh proses validasi dan adjudikasi selesai |
| **Status Akhir Distribusi** | **`READY_FOR_VALIDATOR_DISTRIBUTION`** | File aman dan siap didistribusikan ke validator independen |

---

## B. RAW CSV INSPECTION

Pemeriksaan fisik terhadap berkas CSV asli dilakukan secara langsung menggunakan parser biner dan `csv.DictReader` dalam lingkungan Python untuk mencegah bias visual dari antarmuka teks/chat.

### 1. Header dan Struktur Fisik Aktual

| Parameter Inspeksi | `VALIDATOR_A_RESPONSE_TEMPLATE.csv` | `VALIDATOR_B_RESPONSE_TEMPLATE.csv` | Status Kepatuhan |
| :--- | :--- | :--- | :---: |
| **Header Asli** | `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` | `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` | **EXACT MATCH** |
| **Encoding** | UTF-8 (tanpa BOM) | UTF-8 (tanpa BOM) | **PASSED** |
| **BOM Detection (`\xef\xbb\xbf`)** | False (Tidak ada BOM) | False (Tidak ada BOM) | **PASSED** |
| **Delimiter** | Koma murni (`,`) | Koma murni (`,`) | **PASSED** |
| **Line Terminator** | Standard POSIX LF (`\n`) | Standard POSIX LF (`\n`) | **PASSED** |
| **Jumlah Baris Terurai** | 36 data rows + 1 header = 37 baris | 36 data rows + 1 header = 37 baris | **PASSED** |
| **Jumlah Kolom Terurai** | 7 kolom | 7 kolom | **PASSED** |
| **Karakter Anomali** | Bebas dari `*`, HTML entities (`&#x72;`), maupun whitespace | Bebas dari `*`, HTML entities (`&#x72;`), maupun whitespace | **PASSED** |

### 2. Pemeriksaan Kolom Individual (Header Verification)
Setiap nama kolom diperiksa panjang karakter (*character length*) dan sifat alfanumerik + *underscore*:
- `validator_code` : 14 chars, alnum/underscore: True
- `sample_id` : 9 chars, alnum/underscore: True
- `decision` : 8 chars, alnum/underscore: True
- `correct_letter` : 14 chars, alnum/underscore: True
- `regional_variation` : 18 chars, alnum/underscore: True
- `notes` : 5 chars, alnum/underscore: True
- `review_date` : 11 chars, alnum/underscore: True

---

## C. STRUCTURAL INTEGRITY

| Kriteria Integritas | Validator A | Validator B | Status |
| :--- | :---: | :---: | :---: |
| **Jumlah Sample ID** | Tepat 36 | Tepat 36 | **PASSED** |
| **Jangkauan ID** | `VAL-REV-001` s/d `VAL-REV-036` | `VAL-REV-001` s/d `VAL-REV-036` | **PASSED** |
| **Sample ID Duplikat** | 0 (Nihil) | 0 (Nihil) | **PASSED** |
| **Sample ID Hilang** | 0 (Nihil) | 0 (Nihil) | **PASSED** |
| **Urutan ID** | Monotonik terurut 001 s/d 036 | Monotonik terurut 001 s/d 036 | **PASSED** |
| **Konsistensi Validator Code**| 100% bernilai `VAL-A` | 100% bernilai `VAL-B` | **PASSED** |
| **Status Kolom Keputusan** | 36/36 Kosong (Pending) | 36/36 Kosong (Pending) | **PASSED** |
| **Keberadaan Data Dummy/Sintetis**| **Nihil / 0%** | **Nihil / 0%** | **PASSED** |

---

## D. SCHEMA COMPATIBILITY & DECISION ENUM AUDIT

### 1. Validasi Keputusan (Decision Enum Rules)
Setelah validator mengisi data, skema keputusan wajib memenuhi salah satu dari 4 opsi standar:
- **`CORRECT`**: Gestur valid dan standar. Kolom `correct_letter` opsional/kosong.
- **`INCORRECT`**: Gestur salah. Kolom `correct_letter` **wajib diisi** dengan abjad A–Z dan dilarang kosong.
- **`AMBIGUOUS`**: Gestur tidak jelas atau berada di antara dua pose. Catatan pada `notes` sangat dianjurkan.
- **`UNDETERMINABLE`**: Kualitas visual rusak/terpotong parah (*severe clipping*). Catatan pada `notes` sangat dianjurkan.

### 2. Kompatibilitas dengan Dokumen Protokol & Penilaian
- **Kesesuaian dengan [`VALIDATOR_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md)**: Sesuai 100%. Pilihan `[1] Benar`, `[2] Salah`, `[3] Ambigu`, dan `[4] Tidak Dapat Menentukan` secara langsung terpetakan ke enum bahasa Inggris tanpa distorsi arti.
- **Kesesuaian dengan [`VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md)**: Tabel 36 baris anonim memiliki ID yang selaras secara satu-ke-satu.

### 3. Penguatan Skrip Analisis (`calculate_inter_rater_agreement.py`)
Skrip telah diaudit dan diperkuat (*hardened*) untuk menangani seluruh kondisi batas (*edge cases*):
1. **Pendeteksian Respon Parsial**: Jika validator hanya mengisi sebagian baris (misal 35 dari 36), skrip mengeluarkan peringatan `PARTIALLY_FILLED_ERROR` dan mencantumkan sample ID yang belum terisi.
2. **Pendeteksian `INCORRECT` Tanpa Koreksi**: Jika keputusan `INCORRECT` namun `correct_letter` kosong, skrip menolak data dengan kode `MISSING_CORRECT_LETTER`.
3. **Penyelarasan ID Antar-Validator**: Skrip memverifikasi bahwa urutan dan pasangan ID antara Validator A dan B identik 100% (`SAMPLE_ALIGNMENT_ERROR`).
4. **Penanganan Kasus Tanpa Varians (Zero-Variance / Single-Class Agreement)**: Jika seluruh keputusan bernilai sama (misal semua `CORRECT`), kesepakatan $P_o = 100\%$, namun Cohen's Kappa secara matematis tidak terdefinisi ($P_e = 1.0 \implies 1 - P_e = 0$). Skrip menangani kondisi ini dengan status `UNDEFINED_ZERO_VARIANCE` tanpa crash atau peringatan `UndefinedMetricWarning`.

---

## E. NORMALIZATION LOG

Sesuai pedoman Section 4 (Safe Normalization — Conditional Only), dilakukan normalisasi minimal terhadap baris kosong di akhir berkas (*trailing empty line*) yang terdeteksi pada pemeriksaan biner:

| Berkas yang Dinormalisasi | Jalur Salinan Cadangan (Backup) | SHA-256 Sebelum Normalisasi | SHA-256 Sesudah Normalisasi | Perubahan Spesifik |
| :--- | :--- | :--- | :--- | :--- |
| `VALIDATOR_A_RESPONSE_TEMPLATE.csv` | `docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv.pre_audit_bak` | `c3878c5d8c87c555d0bedde55674477c4e5a264dacb0d98ce13143c49cd260d6` | `80d68a3c47f7ea9bf96964b3fc82c2c1e82994ab5a72793d89c99ea29c92db13` | Menghapus karakter newline berlebih (`\n\n` $\to$ `\n`), menyisakan tepat 37 baris POSIX tanpa baris kosong di akhir. |
| `VALIDATOR_B_RESPONSE_TEMPLATE.csv` | `docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv.pre_audit_bak` | `de3c2aece1c6a7f98595e02985a751ae468f84b876637c18b7ecc78412fdb4b3` | `55b35d922a087c2650c4b4fc2bbbfdca77edbde102db7f095754f1c2ce965e3c` | Menghapus karakter newline berlebih (`\n\n` $\to$ `\n`), menyisakan tepat 37 baris POSIX tanpa baris kosong di akhir. |

*Catatan: Tidak ada perubahan pada sample ID, validator code, urutan kolom, maupun baris data.*

---

## F. DRY-RUN EVIDENCE & TESTING

### 1. Uji Nyata pada Berkas Template Aktual
Perintah:
```powershell
python scripts/validation_p2/calculate_inter_rater_agreement.py
```
Output Aktual:
```text
================================================================================
 SIGNBRIDGE I1 — PHASE 2C INTER-RATER AGREEMENT ANALYZER
================================================================================
File Validator A: docs\validation_p2\phase_2c\VALIDATOR_A_RESPONSE_TEMPLATE.csv
File Validator B: docs\validation_p2\phase_2c\VALIDATOR_B_RESPONSE_TEMPLATE.csv

Status Validasi Integritas File:
- Validator A: STATUS_PENDING: Seluruh keputusan (36/36) masih kosong pada VALIDATOR_A_RESPONSE_TEMPLATE.csv
- Validator B: STATUS_PENDING: Seluruh keputusan (36/36) masih kosong pada VALIDATOR_B_RESPONSE_TEMPLATE.csv

[INFO] STATUS SISTEM: WAITING_FOR_VALIDATOR_RESPONSES
Template respon telah terverifikasi secara struktural dan siap diisi oleh validator.
Perhitungan metriks kesepakatan akan dijalankan secara otomatis setelah data tersedia.
```
- **Exit Code**: `0`
- **Status Sistem**: `WAITING_FOR_VALIDATOR_RESPONSES`

### 2. Uji Unit Skenario Batas (Edge Cases) pada Lingkungan Scratch Terisolasi
Seluruh skenario uji batas dijalankan pada direktori scratch sementara tanpa menyentuh template asli:
1. **Respon Terisi Sebagian (Partial Fill)**: Berhasil dideteksi (`PARTIALLY_FILLED_ERROR: 1/36 keputusan belum diisi...`).
2. **ID Duplikat (Duplicate ID)**: Berhasil dideteksi (`DUPLICATE_ID: Ditemukan sample_id duplikat...`).
3. **Enum Tidak Valid (Invalid Enum)**: Berhasil ditolak (`INVALID_ENUM_ERROR: Keputusan tidak valid: [{'sample_id': 'VAL-REV-001', 'decision': 'MAYBE'}]`).
4. **INCORRECT Tanpa Huruf Koreksi**: Berhasil ditolak (`MISSING_CORRECT_LETTER: Keputusan INCORRECT tanpa huruf koreksi pada sampel: ['VAL-REV-001']`).
5. **Zero-Variance Rating (All CORRECT)**: Berhasil ditangani (Agreement = 1.0, Kappa = None, Status = `UNDEFINED_ZERO_VARIANCE`).
6. **Sample ID Tidak Selaras (Misaligned IDs)**: Berhasil ditolak (`SAMPLE_ALIGNMENT_ERROR: Sample ID Validator A dan B tidak selaras!`).

---

## G. GOVERNANCE & TEST LEAKAGE FIREWALL VERIFICATION

Audit menegaskan kepatuhan penuh terhadap tata kelola riset SignBridge:
1. **Dataset Invariance**:
   - Direktori `data/raw/` dan `data/processed/` tidak tersentuh.
   - `preprocessing_audit_manifest.csv` dan `manifest.csv` tidak dimodifikasi.
2. **Stimulus Invariance**:
   - 36 citra stimulus pada `docs/validation_p2/phase_2b_1/stimulus_images/` memiliki hash SHA-256 yang tetap cocok 100% dengan `STIMULUS_SHA256_MANIFEST.csv`.
3. **Checkpoint & Model Integrity**:
   - Baseline P1 checkpoint (`83C6A093...`) dan model ONNX (`1C281E15...`) tidak diubah.
4. **P2 Training Prohibition**:
   - Tidak ada proses training yang dijalankan; status P2 tetap `HOLD`.
5. **Test Leakage Firewall**:
   - 19 sampel `TEST_SET_DIAGNOSTIC_ONLY` terisolasi ketat hanya untuk diagnosis kegagalan model P1, dilarang keras digunakan untuk re-training, hyperparameter tuning, atau pruning model berikutnya.

---

## H. FINAL STATUS

Berdasarkan seluruh hasil inspeksi biner, normalisasi aman, pengujian kompatibilitas skrip analisis, dan kepatuhan tata kelola data:

# **`READY_FOR_VALIDATOR_DISTRIBUTION`**

Berkas template CSV telah terverifikasi secara formal, bebas dari anomali struktural, dan siap didistribusikan kepada dua validator independen penutur asli BISINDO.

