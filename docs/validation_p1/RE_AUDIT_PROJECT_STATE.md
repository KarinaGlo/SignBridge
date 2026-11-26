# LAPORAN INDEPENDENT RE-AUDIT: STATUS REPOSITORY & INVENTARIS ARTIFAK
## SignBridge ASEAN — Modality Image I1-P1 (BISINDO Alphabet Fingerspelling)

> **Dokumen**: `docs/validation_p1/RE_AUDIT_PROJECT_STATE.md`  
> **Tipe Evaluasi**: Independent Technical Re-Audit & Artifact Verification  
> **Tanggal Audit**: 17 November 2026  
> **Auditor**: Senior Machine Learning Auditor, Computer Vision Engineer, & Data Quality Analyst  
> **Status Keseluruhan**: **`VERIFIED_WITH_LIMITATIONS`**

---

## 1. SCOPE & TUJUAN RE-AUDIT

Re-audit independen ini dilaksanakan untuk memverifikasi secara menyeluruh, skeptis, dan berbasis bukti empiris seluruh artefak, konfigurasi, log, dan kesimpulan teknis yang dihasilkan pada audit sebelumnya di repositori `D:\SEMESTER 5\ML\Projek_1`.

Audit berfokus pada:
1. Verifikasi keberadaan fisik, integritas, dan keterbacaan seluruh artefak (Task 1).
2. Investigasi mendalam terhadap perintah-perintah terminal yang mengalami exit code 1 pada sesi sebelumnya (Task 2).
3. Verifikasi hash kriptografis SHA-256 untuk baseline checkpoint P0, P1, dan model ONNX produksi (Task 6).
4. Verifikasi status Git dan kepatuhan terhadap aturan keselamatan read-only.

---

## 2. TABEL INVENTARISASI DAN VERIFIKASI ARTIFAK (TASK 1)

Setiap artefak diperiksa langsung dari disk sistem, termasuk ukuran file, format data, dan kemampuan parsing (bukan sekadar keberadaan nama file):

| Artifact | Expected | Actual | Exists | Verified | Evidence / Verifikasi Faktual |
|---|---|---|:---:|:---:|---|
| **P1 Configuration** | YAML Config I1-P1 | File exists (977 B) | **YES** | **PASS** | `configs/image_i1_mobilenetv3_p1.yaml`, valid YAML, 26 kelas, arch `mobilenet_v3_small_pretrained` |
| **P0 Configuration** | YAML Config I1-P0 | File exists (568 B) | **YES** | **PASS** | `configs/image_i1_mobilenetv3_p0.yaml`, valid YAML |
| **Processed Manifest** | CSV Manifest 4.462 baris | File exists (1.109.843 B) | **YES** | **PASS** | `data/processed/bisindo_alphabet/manifest.csv`, 4.462 baris data, 15 kolom, 0 missing values kritis |
| **Audit Manifest** | CSV Audit Preprocessing | File exists (1.155.857 B) | **YES** | **PASS** | `data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv`, 4.466 baris, memuat 4 catatan eksklusi |
| **External Manifest** | CSV Manifest Eksternal | File exists (143 B) | **YES** | **PASS** | `data/external/bisindo_validation/external_manifest.csv`, 0 baris data (header saja), 14 kolom |
| **External Manifest Template** | CSV Template Eksternal | File exists (312 B) | **YES** | **PASS** | `data/external/bisindo_validation/external_manifest_template.csv`, 1 baris contoh, 14 kolom cocok 100% |
| **P1 Best Checkpoint** | PyTorch Checkpoint | File exists (6.302.825 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/best.pt`, SHA-256 cocok 100% dengan baseline |
| **P1 Last Checkpoint** | PyTorch Checkpoint | File exists (6.302.825 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/last.pt`, SHA-256: `4565B05EA2E774FA...` |
| **P0 Best Checkpoint** | PyTorch Checkpoint | File exists (6.302.825 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3/best.pt`, SHA-256 cocok 100% dengan baseline |
| **Production ONNX Model** | ONNX Runtime Model | File exists (6.111.968 B) | **YES** | **PASS** | `web/model/fingerspell.onnx`, SHA-256 cocok 100% dengan baseline |
| **P1 Predictions CSV** | CSV Prediksi Test Set | File exists (63.050 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/predictions.csv`, 670 baris, 8 kolom lengkap |
| **P1 Classification Report** | Text Report Sklearn | File exists (1.654 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/classification_report.txt`, 26 kelas + summary metrics |
| **P1 Confusion Matrix CSV** | CSV Matriks Konfusi | File exists (1.650 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/confusion_matrix.csv`, dimensi 26x26 baris/kolom |
| **P1 Training Summary** | JSON Metadata & Metrik | File exists (5.434 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/training_summary.json`, 15 top-level keys |
| **P1 Training History** | CSV History per Epoch | File exists (1.576 B) | **YES** | **PASS** | `runs/image_i1_mobilenetv3_p1/training_history.csv`, 20 epoch lengkap |
| **Project State Audit (Prev)** | Markdown Report | File exists (7.734 B) | **YES** | **PASS** | `docs/validation_p1/PROJECT_STATE_AUDIT.md` |
| **Internal Dataset EDA (Prev)** | Markdown Report | File exists (10.373 B) | **YES** | **PASS** | `docs/validation_p1/INTERNAL_DATASET_EDA_REPORT.md` (Catatan: minor split typo ditemukan) |
| **P1 Error Analysis (Prev)** | Markdown Report | File exists (13.566 B) | **YES** | **PASS** | `docs/validation_p1/P1_ERROR_ANALYSIS_REPORT.md` |
| **P2 Retraining Readiness (Prev)** | Markdown Report | File exists (12.536 B) | **YES** | **PASS** | `docs/validation_p1/P2_RETRAINING_READINESS.md` |
| **Blind Stimulus Deck PDF** | PDF Materi Partisipan | File exists (288.181 B) | **YES** | **PASS** | `docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf`, 7 halaman |
| **Blind Randomization Sheet** | Markdown Record | File exists (5.693 B) | **YES** | **PASS** | `docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md` |
| **Formal Verification Form** | Markdown Form | File exists (20.456 B) | **YES** | **PASS** | `docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md` |

---

## 3. INVESTIGASI KEGAGALAN PERINTAH SEBELUMNYA (TASK 2)

Pada sesi audit sebelumnya, tercatat beberapa pemanggilan perintah terminal berakhir dengan `Exit code 1`. Dilakukan pelacakan mendalam (*post-mortem trace*) melalui log transcript resmi repositori (`transcript.jsonl`):

| Audit Command | Exit Code | Root Cause (Akar Masalah Teknis) | Alternative Used | Alternative Verified | Final Status |
|---|:---:|---|---|:---:|:---:|
| `Check exclusions in audit manifest` (Step 4054) | 1 | **Script Error**: Pemanggilan `os.path.exists()` tanpa melakukan `import os` terlebih dahulu (`NameError: name 'os' is not defined`). | Script diperbaiki dengan menambahkan `import os` secara eksplisit pada command berikutnya. | **PASS** | `PASS` |
| `Audit processed images integrity and quality` (Step 4062) | 1 | **Data Format Mismatch**: Script mencoba mengeksekusi `PIL.Image.open()` terhadap kolom `row['processed_path']` yang berisi file format biner array NumPy (`.npy`), memicu `UnidentifiedImageError`. | Pemisahan logika audit: `PIL.Image.open()` untuk file citra visual (`.jpg` pada `image_path`) dan `np.load()` untuk file tensor array (`.npy` pada `processed_path`). | **PASS** | `PASS` |
| `Extract devices and backgrounds from filenames` (Step 4078) | 1 | **Script Error**: Pemanggilan `os.path.basename()` tanpa melakukan `import os` (`NameError: name 'os' is not defined`). | Script diperbaiki dengan mengimpor modul `os` sebelum iterasi path. | **PASS** | `PASS` |
| `Generate confusion matrix and per-class plots` (Step 4084) | 1 | **Parsing / Matplotlib Warning & TypeError**: `TypeError: 'float' object is not subscriptable` saat mencoba mem-parsing `classification_report_per_class` melalui `pd.read_json` secara naif. | Menggunakan pembacaan langsung dari `runs/image_i1_mobilenetv3_p1/classification_report.txt` dan `confusion_matrix.csv`. | **PASS** | `PASS` |
| `Analyze predictions data` (Step 4101) | 1 | **Incorrect Path Assumption**: Script berasumsi file prediksi berada pada `outputs/evaluation/predictions.csv` (`FileNotFoundError`). Folder `outputs/` adalah direktori eksperimen modalitas Landmark (M0/M1). | Memperbaiki jalur file ke lokasi aktual modalitas Image I1: `runs/image_i1_mobilenetv3_p1/predictions.csv`. | **PASS** | `PASS` |
| `Run detailed error analysis script` (Step 4115) | 1 | **Incorrect CSV Column Name**: Script mengasumsikan kolom path citra bernama `image_path` (`KeyError: "['image_path'] not in index"`). | Mengoreksi nama kolom ke struktur skema aktual `predictions.csv`: `path`, `true_char`, `pred_char`. | **PASS** | `PASS` |

### Evaluasi Dampak Kegagalan:
Seluruh kegagalan di atas bersifat **kesalahan sintaks/asumsi skrip inspeksi audit ad-hoc**, BUKAN kerusakan pada dataset repositori, bukan bug pada model PyTorch/ONNX, dan bukan korupsi file disk. Seluruh alternatif yang dijalankan setelahnya telah dieksekusi ulang secara independen dalam re-audit ini dan diverifikasi menghasilkan angka yang identik 100%.

---

## 4. VERIFIKASI INTEGRITAS BASELINE DAN HASH SHA-256 (TASK 6)

Dilakukan kalkulasi hash kriptografis SHA-256 independen pada seluruh file model dan konfigurasi utama:

| Artefak / Komponen | Path File Repositori | Hash SHA-256 Baseline Tercatat | Hash SHA-256 Hasil Re-Audit | Status Paritas |
|---|---|---|---|:---:|
| **Model P1 Checkpoint** | `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% IDENTIK ✅** |
| **Model P0 Checkpoint** | `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% IDENTIK ✅** |
| **Model ONNX Produksi** | `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% IDENTIK ✅** |
| **Stimulus Deck PDF** | `docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf` | `3448060DBBB3F5AF...` | `3448060DBBB3F5AF483731590203FFC5C2E0C1661B40531EC5E41FA71091D4CA` | **100% IDENTIK ✅** |
| **Konfigurasi P1** | `configs/image_i1_mobilenetv3_p1.yaml` | `876F00BD59793C8F...` | `876F00BD59793C8FB6C07E373498440A70D1061F475D76102C97064E3640CDDF` | **100% IDENTIK ✅** |
| **Konfigurasi P0** | `configs/image_i1_mobilenetv3_p0.yaml` | `B6A508A4DB61D647...` | `B6A508A4DB61D647187A777C4EA46434FEB041C0B5324957AB11AFD4DA6098E0` | **100% IDENTIK ✅** |

---

## 5. AUDIT STATUS GIT & SAFETY CONSTRAINTS

Pemeriksaan status Git (`git status --short`) mengonfirmasi:
1. **Tracked Files**: Tidak ada modifikasi liar pada file yang dilacak Git (`clean tracking tree`).
2. **Safety Rules Kepatuhan**: 
   - 0 checkpoint `.pt` dimodifikasi.
   - 0 model ONNX diubah.
   - 0 file dataset JPG/NPY diubah atau dihapus.
   - 0 konfigurasi YAML diubah.
   - Database PostgreSQL tidak disentuh.
3. Seluruh script ad-hoc eksekusi audit disimpan secara aman di folder scratch terisolasi (`C:\Users\asust\.gemini\antigravity\brain\ae82d8a7-d36a-4686-9ddb-4deaf431b810\scratch\`) di luar repositori proyek.

---

## 6. KESIMPULAN RE-AUDIT STATUS REPOSITORI

Repositori berada dalam **kondisi sehat, utuh, dan terlindungi secara integritas**. Seluruh kegagalan perintah pada audit sebelumnya telah teridentifikasi penyebabnya dan berhasil diatasi dengan metode alternatif yang menghasilkan nilai 100% konsisten. Baseline model P0, P1, dan model ONNX web terverifikasi tidak mengalami perubahan satu bit pun.

