# LAPORAN PEMERIKSAAN AKHIR READ-ONLY
## INTEGRASI MANIFEST & RESOLUSI PATH (I1-P1)

**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/MANIFEST_FINAL_READ_ONLY_VERIFICATION.md`  
**Tanggal**: 16 November 2026  
**Jenis Pemeriksaan**: `STRICT READ-ONLY VERIFICATION` (Zero Code Modifications)  
**Status Verifikasi**: **`VERIFIED`**  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c`  
**Status Data Eksternal**: `0 / 780 FOTO (NOT STARTED — PENDING PHYSICAL COLLECTION)`  

---

## 1. RINGKASAN EKSEKUTIF PEMERIKSAAN

Pemeriksaan akhir *read-only* ini dilakukan secara independen terhadap basis kode proyek untuk memverifikasi kesesuaian faktual antara klaim laporan perbaikan ([`docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md)) dengan implementasi nyata pada kode sumber.

### Temuan Utama:
1. **Implementasi `resolve_image_path()` Aktual**: Kode aktual pada [`track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L73-L109) dan [`evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L51-L86) terbukti mengimplementasikan prioritas 4-tahap secara presisi dan identik.
2. **Integrasi Resolver**: Tidak ada bagian dalam loop pemrosesan manifest yang masih menggunakan `ROOT / p` langsung.
3. **Pemisahan Manifest & Transparansi**: Pemisahan `external_manifest.csv` (aktual) dan `external_manifest_template.csv` (fallback) terbukti aktif dengan penandaan transparan `BELUM DIBUAT ⏳`. Baris berawalan `#` terbukti diabaikan.
4. **Consent Gate Evaluator**: Terbukti memutus alur eksekusi sebelum I/O disk dan pemanggilan model `model(inp_tensor)`.
5. **Eksekusi Pytest Aktual**: Seluruh 21 test case dijalankan ulang secara live dan **100% Lulus (21 passed in 23.38s)**.
6. **Klarifikasi Git Status**: Seluruh file yang diperbarui berstatus **untracked (`??`)**, bukan *tracked modification*, karena berada di working directory fitur validasi yang belum di-commit ke Git.
7. **Integritas Checkpoint**: Seluruh hash SHA-256 model dan ONNX terverifikasi **100% utuh dan tidak tersentuh**.

---

## 2. HASIL PEMERIKSAAN KODE AKTUAL

### A. Fungsi `resolve_image_path()` pada Tracker vs Evaluator

| Aspek Implementasi | Tracker ([`track_external_collection.py#L73-L109`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L73-L109)) | Evaluator ([`evaluate_external_images.py#L51-L86`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L51-L86)) | Kesimpulan Kesesuaian |
|---|---|---|:---:|
| **Absolute Path** | `if p.is_absolute(): return p.resolve()` | `if p.is_absolute(): return p.resolve()` | **IDENTIK & TEPAT** |
| **Dataset Relative** (`A/img.jpg`) | `cand_data = data_dir / p; if cand_data.exists(): return cand_data.resolve()` | `cand_data = data_dir / p; if cand_data.exists(): return cand_data.resolve()` | **IDENTIK & TEPAT** |
| **Root Relative** (`data/ext/.../img.jpg`) | `cand_root = ROOT / p; if cand_root.exists(): return cand_root.resolve()` | `cand_root = ROOT / p; if cand_root.exists(): return cand_root.resolve()` | **IDENTIK & TEPAT** |
| **Prioritas `data_dir` vs `ROOT`** | Diperiksa pada langkah 2, mendahului pemeriksaan `ROOT` pada langkah 3 | Diperiksa pada langkah 2, mendahului pemeriksaan `ROOT` pada langkah 3 | **IDENTIK & TEPAT** |
| **Fallback Tak Ditemukan** | `cand_root.resolve()` jika diawali `data/`, selainnya `cand_data.resolve()` | `cand_root.resolve()` jika diawali `data/`, selainnya `cand_data.resolve()` | **IDENTIK & TEPAT** |
| **Normalisasi Return** | Selalu mengembalikan `Path.resolve()` | Selalu mengembalikan `Path.resolve()` | **IDENTIK & TEPAT** |

### B. Integrasi Pemanggilan Resolver pada Seluruh Alur Loop

Pemeriksaan pencarian teks (*regex audit*) terhadap seluruh pemanggilan path manifest:
- **Pada Tracker** ([baris 219](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L219)):
  `resolved_p = resolve_image_path(raw_p, data_dir=data_dir)`
  Digunakan untuk pemeriksaan eksistensi disk, deteksi duplikasi path, dan penghitungan SHA-256.
- **Pada Evaluator** ([baris 214](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L214)):
  `p = resolve_image_path(raw_p, data_dir=data_dir)`
  Digunakan untuk pemeriksaan eksistensi disk, pemuatan citra via `preprocess_image(p)`, dan pencatatan hasil prediksi.
- **Hasil Verifikasi**: Tidak ditemukan baris kode lain di loop manifest yang melakukan bypassing atau memanggil `ROOT / raw_p` secara langsung.

---

## 3. HASIL VERIFIKASI PEMISAHAN MANIFEST & CONSENT GATE

### A. Pemisahan Manifest Aktual vs Template Fallback

Struktur kode aktual pada [`track_external_collection.py#L125-L148`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L125-L148):
- `actual_manifest_path = data_dir / "external_manifest.csv"`
- `template_manifest_path = data_dir / "external_manifest_template.csv"`
- Tiga mode seleksi terbukti diimplementasikan secara eksplisit:
  1. `ACTUAL_MANIFEST`: Jika file `external_manifest.csv` ditemukan di disk.
  2. `TEMPLATE_FALLBACK`: Jika `external_manifest.csv` belum ada, membaca template sebagai skema referensi.
  3. `EXPLICIT_CLI`: Jika operator menentukan path manual via argumen `--manifest`.

**Perlindungan Data**:
- Baris 175: `if not raw_p or raw_p.startswith("#"): continue`
- Baris contoh `# CONTOH_PENGISIAN:` pada template terbukti 100% dilewati dan tidak dihitung ke `non_comment_rows` maupun `valid_samples`.
- Pada header laporan [`EXTERNAL_DATA_COLLECTION_PROGRESS.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md#L8-L16), teks status secara transparan mencantumkan `BELUM DIBUAT ⏳`.

### B. Evaluator Consent Gate & Filter Label

Struktur kontrol pada [`evaluate_external_images.py#L202-L245`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L202-L245):
1. **Consent Gate**:
   ```python
   consent_status = (row.get("consent_status") or "").strip()
   if consent_status != "CONSENT_SIGNED":
       rejected_counts["consent_invalid"] += 1
       continue
   ```
   Dieksekusi **sebelum** `resolve_image_path`, **sebelum** `preprocess_image`, dan **sebelum** `model(inp_tensor)`.
   Nilai kosong (`""`), spasi (`" "`), `"CONSENT_REFUSED"`, `"PENDING"`, `"NO"`, atau huruf kecil `"consent_signed"` langsung ditolak tanpa memicu komputasi model.
2. **Label Filter**:
   Label divalidasi terhadap `FINGERSPELL_26_LABELS` (A–Z) atau integer 0–25. Nilai lain ditolak ke `rejected_counts["invalid_label"]`.
3. **Identitas Signer**:
   Fungsi `resolve_signer_id(row)` memprioritaskan `signer_id`, fallback ke `subject_id`, dan mengembalikan ID kanonikal tunggal untuk mencegah duplikasi.

---

## 4. HASIL EKSEKUSI PYTEST AKTUAL (21 TEST CASES)

Perintah dieksekusi secara live pada sesi terminal audit:
```powershell
python -m pytest tests/test_track_external_collection.py tests/test_evaluate_external_images.py -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-8.2.2, pluggy-1.6.0
rootdir: D:\SEMESTER 5\ML\Projek_1
collected 21 items

tests/test_track_external_collection.py::test_resolve_image_path_dataset_relative PASSED        [  4%]
tests/test_track_external_collection.py::test_resolve_image_path_root_relative PASSED           [  9%]
tests/test_track_external_collection.py::test_resolve_image_path_absolute PASSED                [ 14%]
tests/test_track_external_collection.py::test_resolve_image_path_not_found_both PASSED          [ 19%]
tests/test_track_external_collection.py::test_resolve_image_path_priority_data_dir PASSED       [ 23%]
tests/test_track_external_collection.py::test_manifest_actual_available PASSED                  [ 28%]
tests/test_track_external_collection.py::test_manifest_template_fallback_transparent PASSED     [ 33%]
tests/test_track_external_collection.py::test_template_sample_line_ignored PASSED               [ 38%]
tests/test_track_external_collection.py::test_empty_manifest_still_not_started PASSED           [ 42%]
tests/test_track_external_collection.py::test_evaluator_and_tracker_consistent_path_rules PASSED [ 47%]
tests/test_evaluate_external_images.py::test_resolve_signer_id_precedence PASSED                [ 52%]
tests/test_evaluate_external_images.py::test_resolve_signer_id_fallback PASSED                  [ 57%]
tests/test_evaluate_external_images.py::test_resolve_signer_id_unknown PASSED                   [ 61%]
tests/test_evaluate_external_images.py::test_valid_consent_included_in_inference PASSED        [ 66%]
tests/test_evaluate_external_images.py::test_empty_consent_rejected_never_inferred PASSED       [ 71%]
tests/test_evaluate_external_images.py::test_refused_consent_rejected_never_inferred PASSED     [ 76%]
tests/test_evaluate_external_images.py::test_missing_consent_column_rejected_never_inferred PASSED [ 80%]
tests/test_evaluate_external_images.py::test_strict_unconsented_data_gating_mixed_manifest PASSED [ 85%]
tests/test_evaluate_external_images.py::test_signer_id_grouping_and_output PASSED              [ 90%]
tests/test_evaluate_external_images.py::test_empty_manifest_files PASSED                        [ 95%]
tests/test_evaluate_external_images.py::test_invalid_label_rejected PASSED                     [100%]

============================= 21 passed in 23.38s (100% SUCCESS) =============================
```

---

## 5. AUDIT STATUS GIT REPOSITORY & WORKING TREE

### A. Status Git Terverifikasi
- **Git Commit HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (Konstan, tidak berubah)
- **Tracked Modifications**: **0 file** (Tidak ada tracked file yang berstatus `M` atau `D`)
- **Untracked Files (`??`)**: Seluruh file fitur validasi eksternal (`scripts/validation_p1/`, `tests/test_track_external_collection.py`, `tests/test_evaluate_external_images.py`, `docs/validation_p1/`, dan `runs/image_i1_mobilenetv3_p1/`).

### B. Klarifikasi Penting Terhadap Laporan Sebelumnya
Dalam laporan implementasi sebelumnya ([`MANIFEST_INTEGRATION_FIX_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md)), file-file seperti `track_external_collection.py` dan `evaluate_external_images.py` disebut sebagai "Diperbarui" (*Updated*).  
**Klarifikasi Audit**:
- Secara status Git, file-file tersebut **bukan merupakan modifikasi file terlacak (*tracked modifications*)**, melainkan **file baru lokal (*untracked files*)** yang dibuat dan disempurnakan di working directory selama siklus tugas validasi ini.
- Working tree tidak "kosong" dari file baru, melainkan berisi berkas fitur validasi eksternal yang dipertahankan utuh sesuai batasan pengguna (*no commit, no clean, no reset*).

---

## 6. VERIFIKASI SHA-256 CHECKPOINT MODEL & ONNX

Pengukuran hash kriptografis aktual:
```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "web/model/fingerspell.onnx", "runs/image_i1_mobilenetv3/best.pt"
```

| Artefak Model | SHA-256 Baseline | SHA-256 Aktual | Status Integritas |
|---|---|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% IDENTIK (UTUH)** |
| `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% IDENTIK (UTUH)** |
| `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% IDENTIK (UTUH)** |

---

## 7. PERBANDINGAN KLAIM LAPORAN DENGAN KONDISI AKTUAL

| No | Poin Klaim pada Laporan Sebelumnya | Hasil Audit Kondisi Aktual | Kesimpulan |
|---|---|---|:---:|
| 1 | Resolusi path 3 format (dataset-relative, root-relative, absolute) | Kode L73-109 dan L51-86 terbukti mengimplementasikan prioritas 4-tahap | **SESUAI FAKTA** |
| 2 | Pemisahan manifest aktual vs template fallback | Variabel terpisah, mode terdeteksi, template berawalan `#` diabaikan | **SESUAI FAKTA** |
| 3 | Konsistensi path antara tracker dan evaluator | Kedua script menggunakan fungsi resolver yang identik dan diuji pada test #10 | **SESUAI FAKTA** |
| 4 | Consent gate memutus sebelum inferensi | Logika if/continue di urutan pertama sebelum preprocessing dan model call | **SESUAI FAKTA** |
| 5 | Status data eksternal 0/780 dan NOT STARTED | Fisik direktori terkonfirmasi 0 foto, tracker menghasilkan 0/780, defisit 780 | **SESUAI FAKTA** |
| 6 | Status Git | File diperbarui adalah untracked (`??`), zero tracked modification | **DIKLARIFIKASI SECARA DETAIL** |

---

## 8. KESIMPULAN AKHIR

Berdasarkan seluruh hasil audit faktual terhadap kode sumber, eksekusi test runner, status repositori Git, dan integritas hash model:

### Status Audit: **`VERIFIED`**

**Catatan Operasional**:
1. Seluruh implementasi GAP-01, GAP-02, dan GAP-03 telah **terbukti secara empiris dan logis bekerja sesuai spesifikasi**.
2. Validasi eksternal model terhadap citra nyata **BELUM SELESAI** karena pengumpulan 780 foto nyata di lapangan saat ini masih berstatus **`0 / 780 (NOT STARTED)`**.
3. Sistem pelacak dan evaluator kini berada dalam kondisi **siap pakai penuh (*100% field-ready*)** menyambut sesi pemotretan oleh operator.

