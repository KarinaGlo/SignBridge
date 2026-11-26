# PHASE 2C.3.2 — VALIDATOR DOCUMENT METHODOLOGY CORRECTION REPORT
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Blinded Validator Protocol Sanitization, Dynamic Gestures (J & Z) Clarification, and Package Consistency Audit

> [!IMPORTANT]
> **GOVERNANCE & STRICT EXECUTION MODE**
> - **Scope of Modifications**: HANYA berkas dokumen di dalam folder distribusi peserta (`distribution/validator_A/` dan `distribution/validator_B/`).
> - **Source Document Invariance**: Berkas riset orisinal di repositori internal (`docs/validation_p2/phase_2b_1/`, `phase_2b_2/`, `phase_2c/`) **tetap utuh dan tidak diubah**.
> - **Zero Mutations on Production**: Dataset mentah, dataset olahan, checkpoint P1, model ONNX, script preprocessing, API, dan kode produksi **tidak disentuh**.
> - **No Automatic Dispatch**: Tidak ada pengiriman berkas secara otomatis kepada validator. Penyerahan materi dilakukan secara manual oleh peneliti.

---

## 1. EXECUTIVE SUMMARY

| Dimensi Pemeriksaan | Status Verifikasi | Ringkasan Tindakan & Temuan |
| :--- | :---: | :--- |
| **Koreksi Terminologi Blind Review** | **`CORRECTED & CERTIFIED`** | Seluruh klaim *double-blind* telah diganti menjadi **`BLINDED_VALIDATOR_REVIEW`** dengan justifikasi metodologis yang transparan. |
| **Klarifikasi Tujuan Label Noise** | **`CLARIFIED`** | Ditegaskan bahwa validator menilai keabsahan gestur secara independen tanpa dibocorkan label asli, prediksi model, atau petunjuk jawaban. |
| **Klarifikasi Gestur Dinamis (J & Z)** | **`EXPLICIT & STANDARDIZED`** | Ditambahkan 5 klausul evaluasi foto diam: pose statis $\ne$ bukti lintasan gerak dinamis; validator bebas memilih `AMBIGUOUS` atau `UNDETERMINABLE`. |
| **Konsistensi Paket A dan B** | **`100% IDENTICAL`** | Seluruh 3 berkas markdown (`PANDUAN`, `REVIEW_SHEET`, `PROTOCOL`) identik biner (*SHA-256 match*) antara Paket A dan Paket B. |
| **Integritas Template CSV** | **`VERIFIED (36 IDs, BLANK)`** | Memuat tepat 36 sample ID unik (`VAL-REV-001` s/d `VAL-REV-036`), status keputusan murni kosong, kode `VAL-A` pada Paket A dan `VAL-B` pada Paket B. |
| **Audit Kebocoran Informasi** | **`0 LEAKS DETECTED`** | Pemindaian regex mengonfirmasi nihil penyebutan model, split data, confidence, maupun label asli. |
| **Status Akhir Kelayakan** | **`PASS — READY FOR MANUAL DISTRIBUTION`** | Seluruh koreksi metodologis selesai; paket siap diserahkan secara manual kepada validator. |

---

## 2. DAFTAR FILE YANG DIUBAH

Perubahan dilakukan secara terbatas dan simetris hanya pada berkas-berkas di dalam subdirektori distribusi peserta:

1. `docs/validation_p2/phase_2c/distribution/validator_A/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`
2. `docs/validation_p2/phase_2c/distribution/validator_B/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`
3. `docs/validation_p2/phase_2c/distribution/validator_A/VALIDATOR_PROTOCOL.md`
4. `docs/validation_p2/phase_2c/distribution/validator_B/VALIDATOR_PROTOCOL.md`
5. `docs/validation_p2/phase_2c/distribution/validator_A/PANDUAN_VALIDATOR_BISINDO.md`
6. `docs/validation_p2/phase_2c/distribution/validator_B/PANDUAN_VALIDATOR_BISINDO.md`

*Catatan: Berkas CSV (`VALIDATOR_A_RESPONSE_TEMPLATE.csv` dan `VALIDATOR_B_RESPONSE_TEMPLATE.csv`) serta 36 citra stimulus pada subfolder `stimulus_images/` TIDAK dimodifikasi sama sekali.*

---

## 3. RINCIAN PERUBAHAN SEBELUM DAN SESUDAH (BEFORE & AFTER)

### A. Koreksi Istilah Blind Review (Section B)
- **Sebelum**:
  - `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`: `"Evaluasi ini bersifat penilaian buta ganda (*double-blind*)."`
  - `VALIDATOR_PROTOCOL.md`: `"secara objektif tanpa bias kecerdasan buatan (*double-blind review*)."`
- **Sesudah**:
  - Diganti secara konsisten dengan metodologi **`BLINDED_VALIDATOR_REVIEW`** disertai klausul wajib:
    > *"Evaluasi ini menggunakan metodologi `BLINDED_VALIDATOR_REVIEW` (Penilaian Buta Mandiri). Penilaian dilakukan secara independen dan blinded. Validator tidak diberi tahu label asli, prediksi model, maupun skor model. Tim peneliti tetap menyimpan mapping internal untuk keperluan audit dan adjudikasi."*

### B. Klarifikasi Tujuan & Pendeteksian Label Noise (Section C)
- **Sebelum**:
  - `VALIDATOR_PROTOCOL.md`: `"Mengidentifikasi dan mendokumentasikan potensi kesalahan label (*label noise*) pada data mentah warisan Mendeley."`
- **Sesudah**:
  - `"Mengidentifikasi keabsahan gestur berdasarkan pengetahuan BISINDO dan bukti visual secara independen, guna mendeteksi apakah terdapat ketidaksesuaian peragaan (*label noise*). Tim peneliti tidak memberikan label asli, prediksi model, atau petunjuk jawaban apa pun kepada validator."`

### C. Standardisasi Pedoman Huruf Dinamis J dan Z (Section D)
- **Sebelum**:
  - Penjelasan J dan Z hanya menginstruksikan pilihan statis lumrah vs ambigu secara singkat tanpa penegasan batas bukti foto diam.
- **Sesudah**:
  - Ditambahkan 5 klausul metodologis baku pada `PANDUAN_VALIDATOR_BISINDO.md`, `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`, dan `VALIDATOR_PROTOCOL.md`:
    1. **Stimulus Foto Statis**: Penilaian menggunakan stimulus foto statis.
    2. **Makna Pilihan CORRECT**: Keputusan `CORRECT` hanya menunjukkan bahwa pose statis dapat dikenali sebagai representasi bentuk huruf oleh validator.
    3. **Batas Pengujian Statis**: Penilaian foto statis **tidak membuktikan ketepatan lintasan gerakan dinamis**.
    4. **Fleksibilitas Ambigu / Tak Tentu**: Jika pose tidak cukup informatif, meragukan, atau identik dengan huruf statis lain (misalnya pose J persis seperti I, atau pose Z persis seperti D), validator **sangat dianjurkan memilih `AMBIGUOUS` atau `UNDETERMINABLE`** sesuai kondisi bukti visual.
    5. **Jangan Memaksakan Pilihan**: **Jangan memaksakan keputusan `CORRECT` atau `INCORRECT`** jika informasi visual tidak memadai tanpa gerakan.

---

## 4. HASIL AUDIT KONSISTENSI PAKET A DAN PAKET B

Pemeriksaan integritas hash kriptografis dan komparasi baris antara Paket Validator A dan Paket Validator B menghasilkan:

| Berkas Dokumen Peserta | SHA-256 Paket Validator A | SHA-256 Paket Validator B | Status Konsistensi |
| :--- | :---: | :---: | :---: |
| `PANDUAN_VALIDATOR_BISINDO.md` | `f8bcd534a174f8c46006f6e80bca112dfd71c4c11b15103a0889f81df6f5a34e` | `f8bcd534a174f8c46006f6e80bca112dfd71c4c11b15103a0889f81df6f5a34e` | **100% IDENTIK** |
| `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` | `dca60af4bf5a92d8f4ff1929007f3ea2d89745db7cb96b306b8e3a21644784a9` | `dca60af4bf5a92d8f4ff1929007f3ea2d89745db7cb96b306b8e3a21644784a9` | **100% IDENTIK** |
| `VALIDATOR_PROTOCOL.md` | `1bf6753086eb293dfdf0a6125032fa6c72cfbe873327cbfeff7d05717cbcfef8` | `1bf6753086eb293dfdf0a6125032fa6c72cfbe873327cbfeff7d05717cbcfef8` | **100% IDENTIK** |
| `stimulus_images/` (36 berkas JPG) | 36 berkas cocok dengan manifest | 36 berkas cocok dengan manifest | **100% IDENTIK BINER** |

### Verifikasi Template CSV Respons:
- **Jumlah Baris**: Tepat 37 baris (1 baris header + 36 baris data).
- **Header**: `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` (Persis sama).
- **Kesesuaian Kode**: Paket A konsisten 100% menggunakan kode `VAL-A`, Paket B konsisten 100% menggunakan kode `VAL-B`.
- **Status Pengisian**: 36/36 keputusan masih kosong murni (status `PENDING`).

---

## 5. HASIL AUDIT PENCEGAHAN KEBOCORAN (CONFIDENTIALITY LEAKAGE AUDIT)

Pemindaian teks berbasis ekspresi reguler (*regex scan*) pada seluruh berkas paket peserta membuktikan:
- **Klaim `double-blind`**: **0 temuan (CLEAN)**.
- **Penyebutan Model AI (`MobileNet`, dll.)**: **0 temuan (CLEAN)**.
- **Penyebutan Skor Confidence & Persentase**: **0 temuan (CLEAN)**.
- **Penyebutan Split Data (`train`, `val`, `test`, `TRAIN_COHORT`, `TEST_SET_DIAGNOSTIC_ONLY`)**: **0 temuan (CLEAN)**.
- **Penyebutan Label Asli Mentah / Perangkat Sumber**: **0 temuan (CLEAN)**.
- **Penyertaan Kunci Dekripsi (`INTERNAL_SAMPLE_MAPPING.md`)**: **0 temuan (CLEAN - Terisolasi di repositori internal)**.

---

## 6. STATUS REPOSITORI GIT DAN INVARIANSI PRODUKSI

Pemeriksaan status Git (`git status`) mengonfirmasi bahwa:
1. **0 berkas terlacak (*tracked files*) yang dimodifikasi** (`git diff --stat` menghasilkan 0 perubahan).
2. Seluruh artefak produksi dan dataset riset tetap dalam kondisi utuh (*strictly invariant*):
   - `data/raw/` dan `data/processed/`: Tidak disentuh.
   - `docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md`: Tidak disentuh.
   - Baseline Checkpoint P1 (`83C6A093...`) & ONNX (`1C281E15...`): Tidak disentuh.
   - Pipeline inferensi, API, dan skrip pelatihan: Tidak disentuh.
3. Modifikasi dilakukan secara terisolasi pada berkas baru di `docs/validation_p2/phase_2c/distribution/`.

---

## 7. KESIMPULAN FORMAL AUDIT

Berdasarkan kepatuhan penuh terhadap standar metodologi sains komputer dan etika penelitian bahasa isyarat BISINDO:

# **`STATUS: PASS — READY FOR MANUAL DISTRIBUTION`**

### Rekomendasi Langkah Selanjutnya:
Peneliti dapat menyerahkan paket distribusi secara manual kepada masing-masing validator independen:
1. Paket Validator A: folder [`docs/validation_p2/phase_2c/distribution/validator_A/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_A/)
2. Paket Validator B: folder [`docs/validation_p2/phase_2c/distribution/validator_B/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_B/)

