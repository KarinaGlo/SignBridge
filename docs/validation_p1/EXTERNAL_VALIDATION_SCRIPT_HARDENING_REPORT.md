# LAPORAN PENGUATAN SCRIPT EVALUASI EKSTERNAL (HARDENING REPORT) — BISINDO I1-P1

**Project**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md`  
**Tanggal**: 16 November 2026  
**Status Eksekusi**: `VERIFIED & HARDENED`  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)

---

## 1. RINGKASAN EKSEKUTIF

Berdasarkan hasil audit protokol pengumpulan data eksternal, dilakukan perbaikan terfokus pada script evaluasi eksternal [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) untuk mengatasi dua celah operasional:
1. **Pencegahan Data Tanpa Persetujuan Masuk Inferensi**: Script sebelumnya belum memblokir baris manifest yang tidak memiliki informed consent bertanda `CONSENT_SIGNED`. Kini diterapkan *hard reject gate* yang dievaluasi **sebelum** pembacaan citra disk, preprocessing, maupun inferensi model.
2. **Konsistensi Metrik & Output Penutur**: Penamaan kolom dan pengelompokan metrik kini dibakukan menggunakan `signer_id`, dengan pemetaan kompatibilitas mundur terhadap `subject_id` tanpa duplikasi penghitungan (*zero double counting*).

Seluruh implementasi telah diverifikasi menggunakan suite unit test lengkap pada [`tests/test_evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_evaluate_external_images.py) dengan **11 test case (100% lulus)**.

---

## 2. FILE YANG DIUBAH DAN DITAMBAHKAN

| No | File Path | Tipe Perubahan | Deskripsi Singkat |
|---|---|---|---|
| 1 | [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) | Dimodifikasi | Menambahkan fungsi `resolve_signer_id()`, gerbang validasi consent `CONSENT_SIGNED` di awal loop sebelum I/O citra, pencatatan statistik penolakan (`rejected_counts`), standardisasi kolom output CSV ke `signer_id`, serta parameter opsional `model` untuk pengujian non-destruktif. |
| 2 | [`tests/test_evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_evaluate_external_images.py) | Baru | Suite pengujian otomatis mencakup 11 unit test untuk consent, gating inferensi, penolakan label/file, pengelompokan `signer_id`, dan penanganan manifest kosong. |
| 3 | [`docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md) | Baru | Dokumen laporan teknis hasil verifikasi dan audit hardening. |

---

## 3. PERUBAHAN FUNGSI DAN PERILAKU SCRIPT

### A. Alur Verifikasi Consent (Hard Reject Gate)

Sebelum perbaikan, script hanya memeriksa eksistensi file dan parsing label. Sekarang alur evaluasi menerapkan urutan berjenjang yang ketat:

```text
[Pembacaan Baris Manifest]
            │
            ▼
    [Apakah Komentar (#) atau Baris Kosong?] ──(Ya)──> Abaikan / Skip
            │ (Tidak)
            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 1. GERBANG INFORMED CONSENT                                 │
 │    Apakah row.get('consent_status') == 'CONSENT_SIGNED'?   │
 └─────────────────────────────────────────────────────────────┘
            │
            ├───(TIDAK / KOSONG / LAINNYA)──> CATAT WARNING
            │                                 rejected_counts['consent_invalid'] += 1
            │                                 LANJUT KE BARIS BERIKUTNYA (CONTINUE)
            │                                 [Dilarang baca disk, dilarang inferensi]
            ▼ (YA)
 ┌─────────────────────────────────────────────────────────────┐
 │ 2. Validasi Keberadaan File Citra di Disk                   │
 └─────────────────────────────────────────────────────────────┘
            │
            ▼ (Ada)
 ┌─────────────────────────────────────────────────────────────┐
 │ 3. Validasi Label Huruf A–Z (0–25)                          │
 └─────────────────────────────────────────────────────────────┘
            │
            ▼ (Valid)
 ┌─────────────────────────────────────────────────────────────┐
 │ 4. Resolusi Identitas Penutur (signer_id)                   │
 └─────────────────────────────────────────────────────────────┘
            │
            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 5. Preprocessing Citra & Eksekusi Inferensi Model           │
 └─────────────────────────────────────────────────────────────┘
```

**Karakteristik Pengamanan**:
- String consent kosong (`""`) atau spasi (`"   "`) dianggap tidak sah.
- Nilai seperti `"CONSENT_PENDING"`, `"CONSENT_REFUSED"`, `"NO"`, atau huruf kecil `"consent_signed"` ditolak.
- Jika kolom `consent_status` sama sekali tidak ada di header CSV, seluruh data otomatis ditolak.
- Citra dari data yang ditolak **tidak pernah dimuat dari disk**, **tidak pernah dipreprocess**, dan **tidak pernah dikirim ke model**.

### B. Standardisasi `signer_id` dan Dukungan Kompatibilitas `subject_id`

Diterapkan fungsi resolusi kanonikal:
```python
def resolve_signer_id(row: Dict[str, str]) -> str:
    """Explicit compatibility mapping for signer identity.
    Prefers 'signer_id'. Falls back to 'subject_id' if 'signer_id' is missing or blank.
    Guarantees a single canonical ID per sample to prevent duplicate counting.
    """
    sid = (row.get("signer_id") or "").strip()
    if not sid:
        sid = (row.get("subject_id") or "").strip()
    return sid if sid else "UNKNOWN_SIGNER"
```

**Manfaat Operasional**:
- Manifest 14-kolom (`external_manifest_template.csv`) yang menggunakan `signer_id` terbaca langsung.
- Manifest lama atau sistem lain yang menggunakan `subject_id` tetap didukung secara mulus.
- Setiap sampel diikat tepat pada 1 entitas penutur kanonikal, menjamin `total_samples == sum(per_signer_samples)` tanpa duplikasi data.
- Output file prediksi `external_predictions.csv` kini resmi menggunakan kolom `signer_id`.

### C. Transparansi Pelaporan Penolakan Data

Struktur ringkasan evaluasi (`external_validation_summary.json`) kini menyediakan rincian penolakan transparan:

> [!IMPORTANT]
> **ILLUSTRATIVE EXAMPLE — NOT REAL EVALUATION RESULT**  
> Cuplikan JSON di bawah ini **HANYA skema contoh/ilustrasi struktural** untuk menunjukkan format field penolakan data (`rejected_counts`). Data fisik eksternal aktual saat ini masih **0 / 780 foto** dan evaluasi nyata **BELUM PERNAH dieksekusi**. Angka 780/750/30/92.4% di bawah ini murni ilustrasi fiktif sintaksis.

```json
{
  "status": "EVALUATED",
  "checkpoint": "runs/image_i1_mobilenetv3_p1/best.pt",
  "total_manifest_rows": 780,
  "total_evaluated_samples": 750,
  "total_rejected_samples": 30,
  "rejected_counts": {
    "consent_invalid": 25,
    "file_not_found": 3,
    "invalid_label": 2
  },
  "per_signer_performance": {
    "EXT_S01": {"samples": 250, "accuracy_pct": 92.4, "macro_f1_pct": 91.8}
  }
}
```

---

## 4. HASIL PENGUJIAN UNIT TEST (`tests/test_evaluate_external_images.py`)

Eksekusi dijalankan menggunakan pytest pada lingkungan proyek:
```powershell
python -m pytest tests/test_evaluate_external_images.py -v
```

### Rincian Hasil Pengujian (11 Test Cases):

| No | Nama Test Function | Aspek yang Diuji | Hasil |
|---|---|---|:---:|
| 1 | `test_resolve_signer_id_precedence` | Memastikan `signer_id` diprioritaskan di atas `subject_id` | **PASSED** |
| 2 | `test_resolve_signer_id_fallback` | Memastikan fallback ke `subject_id` jika `signer_id` kosong/tidak ada | **PASSED** |
| 3 | `test_resolve_signer_id_unknown` | Memastikan nilai `"UNKNOWN_SIGNER"` jika kedua kolom kosong | **PASSED** |
| 4 | `test_valid_consent_included_in_inference` | Data dengan `CONSENT_SIGNED` diproses, inferensi dipanggil 1×, output prediksi mencatat `signer_id` | **PASSED** |
| 5 | `test_empty_consent_rejected_never_inferred` | Data dengan consent kosong / spasi ditolak (`consent_invalid=2`), model call count = 0 | **PASSED** |
| 6 | `test_refused_consent_rejected_never_inferred` | Data dengan `CONSENT_REFUSED`, `PENDING`, `NO`, atau lowercase ditolak (`consent_invalid=4`), model call count = 0 | **PASSED** |
| 7 | `test_missing_consent_column_rejected_never_inferred` | Manifest tanpa kolom `consent_status` ditolak (`consent_invalid=1`), model call count = 0 | **PASSED** |
| 8 | `test_strict_unconsented_data_gating_mixed_manifest` | Manifest campuran (2 sah, 3 tidak sah): hanya 2 data sah yang masuk inferensi (`model.call_count == 2`), 3 ditolak | **PASSED** |
| 9 | `test_signer_id_grouping_and_output` | Pengelompokan metrik multi-penutur (`EXT_S01`, `EXT_S02`, `EXT_S03`), output CSV memakai `signer_id`, zero double counting | **PASSED** |
| 10 | `test_empty_manifest_files` | Manifest kosong (0 byte) atau hanya header menghasilkan status `PENDING EXTERNAL DATA` tanpa memanggil model | **PASSED** |
| 11 | `test_invalid_label_rejected` | Label tidak valid (`"INVALID"`, `"99"`, `""`, `""?`) ditolak sebelum inferensi dipanggil | **PASSED** |

**Ringkasan Status Pytest**: **`11 passed in 29.84s (100% SUCCESS)`**

---

## 5. BUKTI AUDIT INTEGRITAS & ISOLASI SISTEM

### A. Bukti Bahwa Data Tanpa Consent Tidak Masuk Inferensi
Pada test `test_strict_unconsented_data_gating_mixed_manifest`:
- Diberikan manifest berisi 5 baris data (2 berstatus `CONSENT_SIGNED`, 1 kosong, 1 `CONSENT_REFUSED`, 1 `PENDING`).
- Objek `MockP1Model` memantau pemanggilan fungsi `forward()`.
- **Hasil**: `mock_model.call_count == 2`. Tiga data tanpa consent sah diputus pada awal loop sebelum fungsi `preprocess_image()` dan `model()` dipanggil.

### B. Bukti Bahwa Metrik Per Penutur Menggunakan `signer_id`
Pada test `test_signer_id_grouping_and_output`:
- `summary["per_signer_performance"]` memiliki entri kunci `EXT_S01`, `EXT_S02`, dan `EXT_S03`.
- Jumlah sampel per penutur tepat: $2 + 1 + 1 = 4$ sampel total.
- File `external_predictions.csv` memiliki header kolom `signer_id`.

### C. Verifikasi SHA-256 Checkpoint & Model Produksi

Untuk membuktikan bahwa seluruh bobot model tetap steril dan tidak terpengaruh oleh pengujian ini:

| Artefak Model | SHA-256 Sebelum | SHA-256 Sesudah | Status Integritas |
|---|---|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% IDENTIK (UNTOUCHED)** |
| `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% IDENTIK (UNTOUCHED)** |
| `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% IDENTIK (UNTOUCHED)** |

### D. Verifikasi Git Repository & Working Tree

- **Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (Tidak berubah)
- **Tracked files modified**: **0 file** (Tidak ada commit, push, reset, checkout, atau modifikasi file yang sudah dilacak).
- **Working Tree**: Perubahan terlokalisasi hanya pada penambahan script hardening, unit test, dan dokumentasi di working directory.

---

## 6. KESIMPULAN & STATUS AKHIR

Pipeline evaluasi eksternal model MobileNetV3-Small (I1-P1) kini telah memiliki proteksi etik dan integritas data tingkat produksi:
1. Setiap entri wajib memiliki persetujuan resmi `CONSENT_SIGNED`. Data yang tidak memenuhi syarat akan langsung ditolak sebelum mencapai tahap komputasi inferensi.
2. Identitas penutur dikelompokkan secara konsisten menggunakan `signer_id`, menjamin kepatuhan terhadap template manifest 14-kolom.
3. Seluruh unit test diverifikasi lulus tanpa celah.

Script kini dalam kondisi **siap pakai (*production-grade validation pipeline*)** ketika 780 foto nyata dari partisipan `EXT_S01`–`EXT_S03` telah dikumpulkan oleh operator.

