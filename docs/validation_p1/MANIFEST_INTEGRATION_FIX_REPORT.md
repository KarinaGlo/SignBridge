# LAPORAN IMPLEMENTASI PERBAIKAN INTEGRASI MANIFEST
## GAP-01, GAP-02, DAN GAP-03 (BISINDO I1-P1)

**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md`  
**Tanggal**: 16 November 2026  
**Status Implementasi**: `VERIFIED & FULLY RESOLVED`  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)

---

## 1. RINGKASAN EKSEKUTIF

Berdasarkan rekomendasi pada [`docs/validation_p1/MANIFEST_INTEGRATION_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/MANIFEST_INTEGRATION_AUDIT.md), seluruh perbaikan GAP-01, GAP-02, dan GAP-03 telah berhasil diimplementasikan secara terstruktur, non-destruktif, dan diverifikasi dengan suite pengujian otomatis menyeluruh.

### Ringkasan Pencapaian:
1. **GAP-01 (Multi-Fallback Path Resolution pada Tracker)**: Fungsi `resolve_image_path(raw_path, data_dir)` diterapkan pada [`track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py). Kini mendukung tiga format path:
   - Relatif terhadap direktori dataset: `A/EXT_S01_A_01.jpg` (Prioritas utama path relatif).
   - Relatif terhadap root repository: `data/external/bisindo_validation/A/EXT_S01_A_01.jpg`.
   - Absolute path: `D:/.../A/EXT_S01_A_01.jpg`.
2. **GAP-02 (Transparansi Manifest Aktual vs Template)**: Tracker kini secara tegas membedakan manifest aktual (`external_manifest.csv`) dengan template referensi fallback (`external_manifest_template.csv`). Laporan Markdown dan JSON secara transparan mencantumkan status `external_manifest.csv — BELUM DIBUAT ⏳` dan `DIGUNAKAN SEBAGAI FALLBACK REFERENSI ⚪`, sehingga tidak lagi menimbulkan kesan salah bahwa template adalah manifest operasional.
3. **GAP-03 (Konsistensi Path Evaluator)**: Fungsi `resolve_image_path()` yang identik diterapkan pada [`evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py). Pipeline inferensi tetap mempertahankan consent gate `CONSENT_SIGNED`, validasi signer/label, dan pencegahan duplikasi.
4. **Verifikasi Pengujian**: Seluruh 21 unit test (10 test tracker/GAP fix + 11 test evaluator) **lulus 100% (21 passed in 23.13s)**.
5. **Integritas Status**: Eksekusi aktual pada repository mengonfirmasi status tetap **`NOT STARTED` (0 / 780 foto, defisit 780)**. Seluruh hash model dan Git HEAD terbukti steril 100%.

---

## 2. FILE YANG DIUBAH DAN DITAMBAHKAN

| No | File Path | Tipe Perubahan | Rincian Perubahan |
|---|---|---|---|
| 1 | [`scripts/validation_p1/track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py) | **Diperbarui** | • Menambahkan fungsi [`resolve_image_path()`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L70-L108) dengan prioritas dataset-relative -> root-relative -> candidate fallback.<br>• Memisahkan logika `actual_manifest_path`, `template_manifest_path`, dan `manifest_mode`.<br>• Menambahkan banner transparansi status manifest pada laporan Markdown dan field `manifest_info` pada JSON. |
| 2 | [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) | **Diperbarui** | • Menambahkan fungsi [`resolve_image_path()`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L53-L86) yang konsisten.<br>• Mendukung parameter opsional `data_dir` pada evaluasi inferensi.<br>• Mempertahankan seluruh gerbang consent, preprocessing, dan validasi label/signer. |
| 3 | [`tests/test_track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_track_external_collection.py) | **Diperbarui** | 10 unit test komprehensif mencakup path relatif dataset, root, absolute, unresolved fallback, prioritas data_dir, manifest aktual vs template fallback, sample line ignoring, empty manifest, dan konsistensi evaluator-tracker. |
| 4 | [`docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md) | **Diperbarui** | Laporan progres aktual yang telah memuat banner transparansi status manifest `BELUM DIBUAT ⏳`. |
| 5 | [`docs/validation_p1/external_collection_progress.json`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/external_collection_progress.json) | **Diperbarui** | Metadata terstruktur JSON dengan blok `manifest_info`. |
| 6 | [`docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/MANIFEST_INTEGRATION_FIX_REPORT.md) | **Baru** | Dokumen verifikasi implementasi perbaikan ini. |

---

## 3. RINCIAN IMPLEMENTASI TEKNIS

### A. GAP-01: Multi-Fallback Path Resolver

Implementasi pada [`track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L70-L108):
```python
def resolve_image_path(raw_path: str, data_dir: Path) -> Path:
    raw_str = raw_path.strip()
    p = Path(raw_str)

    # 1. Absolute path: gunakan langsung
    if p.is_absolute():
        return p.resolve()

    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir

    # 2. Prioritas 1 untuk path relatif: cek terhadap data_dir (misal: "A/EXT_S01_A_01.jpg")
    cand_data = data_dir / p
    if cand_data.exists():
        return cand_data.resolve()

    # 3. Prioritas 2 untuk path relatif: cek terhadap ROOT repository (misal: "data/external/.../A/...")
    cand_root = ROOT / p
    if cand_root.exists():
        return cand_root.resolve()

    # 4. Fallback jika file belum ada di kedua lokasi (tentukan kandidat berdasarkan konvensi)
    clean_posix = p.as_posix()
    if clean_posix.startswith("data/"):
        return cand_root.resolve()
    return cand_data.resolve()
```

### B. GAP-02: Transparansi Manifest Aktual vs Template

Pemisahan variabel dan penentuan mode pada [`track_external_collection.py#L125-L148`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L125-L148):
- `actual_manifest_path = data_dir / "external_manifest.csv"`
- `template_manifest_path = data_dir / "external_manifest_template.csv"`
- Mode:
  - `ACTUAL_MANIFEST`: Jika `external_manifest.csv` ditemukan.
  - `TEMPLATE_FALLBACK`: Jika `external_manifest.csv` belum ada (menggunakan template murni sebagai referensi skema).
  - `EXPLICIT_CLI`: Jika path ditentukan manual via `--manifest`.

Penyajian pada Header Laporan Markdown:
```markdown
### Identifikasi File Manifest
- **Manifest aktual**: `data/external/bisindo_validation/external_manifest.csv` — **`BELUM DIBUAT ⏳`**
- **Template referensi**: `data/external/bisindo_validation/external_manifest_template.csv` — **`DIGUNAKAN SEBAGAI FALLBACK REFERENSI ⚪`**
- **File yang dibaca saat ini**: `.../external_manifest_template.csv` (Mode: `TEMPLATE_FALLBACK`)

> [!IMPORTANT]
> **MANIFEST AKTUAL: `external_manifest.csv` BELUM DIBUAT**  
> Sistem saat ini membaca `external_manifest_template.csv` murni sebagai fallback referensi skema.
```

### C. GAP-03: Konsistensi Path Evaluator

Fungsi resolver yang identik disematkan pada [`evaluate_external_images.py#L53-L86`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L53-L86) dan dipanggil di dalam loop evaluasi:
```python
p = resolve_image_path(raw_p, data_dir=data_dir)
if not p.exists():
    logger.warning("Citra tidak ditemukan di disk pada baris %d: %s", idx, p)
    rejected_counts["file_not_found"] += 1
    continue
```
Menjamin bahwa operator dapat mengisi manifest menggunakan path `A/EXT_S01_A_01.jpg` maupun `data/external/bisindo_validation/A/EXT_S01_A_01.jpg`, dan keduanya terbaca dengan benar tanpa perbedaan antara alat pelacak dan script evaluasi.

---

## 4. HASIL PENGUJIAN UNIT TEST LENGKAP

Perintah eksekusi:
```powershell
python -m pytest tests/test_track_external_collection.py tests/test_evaluate_external_images.py -v
```

### Rincian Hasil 21 Test Case:

| No | Modul / Test Function | Fokus Verifikasi | Status |
|---|---|---|:---:|
| 1 | `test_resolve_image_path_dataset_relative` | Format `A/EXT_S01_A_01.jpg` terselesaikan ke `data_dir` | **PASSED** |
| 2 | `test_resolve_image_path_root_relative` | Format `data/external/.../A/EXT_S01_A_01.jpg` terselesaikan ke `ROOT` | **PASSED** |
| 3 | `test_resolve_image_path_absolute` | Absolute path dinormalisasi dan digunakan langsung | **PASSED** |
| 4 | `test_resolve_image_path_not_found_both` | File tidak ditemukan di kedua lokasi diarahkan ke kandidat kanonikal | **PASSED** |
| 5 | `test_resolve_image_path_priority_data_dir` | Prioritas `data_dir` terbukti jika file ada di kedua lokasi | **PASSED** |
| 6 | `test_manifest_actual_available` | `external_manifest.csv` dikenali sebagai `ACTUAL_MANIFEST` | **PASSED** |
| 7 | `test_manifest_template_fallback_transparent` | Template fallback ditandai transparan dengan status `BELUM DIBUAT` | **PASSED** |
| 8 | `test_template_sample_line_ignored` | Baris contoh template diawali `#` diabaikan, sampel valid tetap 0 | **PASSED** |
| 9 | `test_empty_manifest_still_not_started` | Manifest kosong menghasilkan `NOT STARTED` (0/780, defisit 780) | **PASSED** |
| 10 | `test_evaluator_and_tracker_consistent_path_rules` | Tracker dan Evaluator menyelesaikan path dataset-relative secara identik | **PASSED** |
| 11 | `test_resolve_signer_id_precedence` | `signer_id` diprioritaskan di atas `subject_id` | **PASSED** |
| 12 | `test_resolve_signer_id_fallback` | Fallback ke `subject_id` jika `signer_id` kosong | **PASSED** |
| 13 | `test_resolve_signer_id_unknown` | Fallback ke `UNKNOWN_SIGNER` jika keduanya kosong | **PASSED** |
| 14 | `test_valid_consent_included_in_inference` | Data `CONSENT_SIGNED` diproses ke model inferensi | **PASSED** |
| 15 | `test_empty_consent_rejected_never_inferred` | Consent kosong ditolak sebelum inferensi (`call_count == 0`) | **PASSED** |
| 16 | `test_refused_consent_rejected_never_inferred` | Non-`CONSENT_SIGNED` ditolak sebelum inferensi (`call_count == 0`) | **PASSED** |
| 17 | `test_missing_consent_column_rejected_never_inferred` | Manifest tanpa kolom consent ditolak (`call_count == 0`) | **PASSED** |
| 18 | `test_strict_unconsented_data_gating_mixed_manifest` | Manifest campuran 5 baris hanya memanggil model 2× (data sah) | **PASSED** |
| 19 | `test_signer_id_grouping_and_output` | Agregasi per penutur tepat tanpa duplikasi data | **PASSED** |
| 20 | `test_empty_manifest_files` | Manifest kosong menghasilkan `PENDING EXTERNAL DATA` | **PASSED** |
| 21 | `test_invalid_label_rejected` | Label di luar A–Z ditolak sebelum inferensi | **PASSED** |

**Ringkasan Hasil**: **`21 passed in 23.13s (100% SUCCESS, 0 FAILED)`**

---

## 5. AUDIT INTEGRITAS SISTEM & DATA AKTUAL

### A. Eksekusi Tracker pada Direktori Aktual Repository
```powershell
python scripts/validation_p1/track_external_collection.py --data-dir data/external/bisindo_validation --output-report docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md --output-json docs/validation_p1/external_collection_progress.json
```
- **Status Progres**: **`NOT STARTED` ⚪**
- **Total Valid Terkumpul**: **`0 / 780` (0.0%)**
- **Defisit Target**: **780 foto**
- **Status Manifest**:
  - `external_manifest.csv` — **`BELUM DIBUAT ⏳`**
  - `external_manifest_template.csv` — **`DIGUNAKAN SEBAGAI FALLBACK REFERENSI ⚪`**
- **Jumlah Foto Fisik di Disk**: **0 foto** (Tidak ada foto sintetis/fiktif).

### B. Verifikasi SHA-256 Checkpoint Model & ONNX

| Artefak Model | SHA-256 Sebelum | SHA-256 Sesudah | Status |
|---|---|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% UTUH** |
| `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% UTUH** |
| `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% UTUH** |

### C. Verifikasi Git Repository
- **Commit HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (Tidak berubah)
- **Tracked files modified**: **0 file** (Tidak ada commit, push, merge, reset, clean, atau checkout).
- **Working Tree**: Seluruh modifikasi tersimpan aman pada working directory.

---

## 6. KESIMPULAN

Implementasi perbaikan GAP-01, GAP-02, dan GAP-03 telah selesai 100%. Sistem kini:
1. **Fleksibel & Konsisten**: Menerima path citra baik relatif terhadap folder dataset (`A/...`) maupun root repo (`data/...`).
2. **Transparan & Informatif**: Menegaskan bahwa manifest aktual belum dibuat dan template hanya referensi.
3. **Teruji Penuh**: Terbukti lolos 21 unit test tanpa regresi dan siap digunakan saat sesi pemotretan dimulai.

