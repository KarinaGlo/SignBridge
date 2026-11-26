# LAPORAN PEMERIKSAAN AKHIR (FINAL REVIEW)
## PIPELINE EVALUASI EKSTERNAL BISINDO I1-P1

**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/FINAL_EXTERNAL_PIPELINE_REVIEW.md`  
**Tanggal Pemeriksaan**: 16 November 2026  
**Status Evaluasi**: `READY FOR PHYSICAL DATA COLLECTION` (Data aktual: 0 / 780)  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)

---

## 1. RINGKASAN EKSEKUTIF

Pemeriksaan akhir (*final review*) ini dilakukan untuk mengaudit secara menyeluruh kesiapan pipeline validasi eksternal model **MobileNetV3-Small (I1-P1)**, mengklarifikasi representasi dokumentasi, mengevaluasi potensi risiko pada pemetaan identitas penutur, dan memverifikasi integritas sistem sebelum pengumpulan data fisik di lapangan dimulai.

### Hasil Utama Pemeriksaan:
1. **Klarifikasi Contoh JSON**: Contoh JSON pada laporan hardening telah diverifikasi murni sebagai skema struktural fiktif dan kini telah diberi label peringatan tegas `ILLUSTRATIVE EXAMPLE — NOT REAL EVALUATION RESULT`.
2. **Audit Fungsi `resolve_signer_id()`**: Terbukti mengutamakan `signer_id`, fallback `subject_id` bebas dari duplikasi penghitungan (*zero double counting*). Risiko fallback `"UNKNOWN_SIGNER"` telah diidentifikasi dan dianalisis secara mendalam.
3. **Verifikasi Gerbang Informed Consent**: Data tanpa status persis `CONSENT_SIGNED` terbukti secara mutlak tidak pernah masuk ke tahap pembacaan citra disk, preprocessing, maupun inferensi model.
4. **Verifikasi Suite Pengujian**: Seluruh 11 unit test pada [`tests/test_evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_evaluate_external_images.py) dieksekusi ulang dan **100% Lulus (11 passed in 22.92s)**.
5. **Integritas Status Data Fisik**: Terkonfirmasi secara fisik bahwa belum ada foto eksternal di repository (**0 / 780 foto**). Tidak ada klaim akurasi eksternal buatan atau evaluasi fiktif.

---

## 2. FILE YANG DIPERIKSA

| No | Path File | Status | Tujuan Pemeriksaan |
|---|---|---|---|
| 1 | [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) | Verified | Memeriksa alur gerbang consent, resolusi ID penutur, dan isolasi proses inferensi. |
| 2 | [`tests/test_evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_evaluate_external_images.py) | Verified | Memverifikasi cakupan 11 test case terhadap skenario consent, penolakan, dan grouping. |
| 3 | [`docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md) | Updated | Memastikan pelabelan eksplisit ilustrasi JSON agar tidak menimbulkan kesalahpahaman. |
| 4 | [`data/external/bisindo_validation/external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv) | Verified | Memastikan header template (14 kolom) sesuai dengan parser script evaluasi. |
| 5 | `data/external/bisindo_validation/` | Verified | Memastikan jumlah file citra fisik eksternal saat ini tepat 0. |

---

## 3. HASIL AUDIT RINCI BERDASARKAN FOKUS PEMERIKSAAN

### A. Klarifikasi Contoh JSON pada Dokumen Laporan Hardening
- **Temuan**: Pada bagian 3.C di `docs/validation_p1/EXTERNAL_VALIDATION_SCRIPT_HARDENING_REPORT.md`, cuplikan JSON memuat angka `780` total rows, `750` evaluated samples, `30` rejected samples, dan akurasi `92.4%`.
- **Status Tindakan**: Telah ditambahkan banner peringatan resmi bertanda:
  > **[!IMPORTANT]**  
  > **ILLUSTRATIVE EXAMPLE — NOT REAL EVALUATION RESULT**  
  > Cuplikan JSON di bawah ini **HANYA skema contoh/ilustrasi struktural** untuk menunjukkan format field penolakan data (`rejected_counts`). Data fisik eksternal aktual saat ini masih **0 / 780 foto** dan evaluasi nyata **BELUM PERNAH dieksekusi**. Angka 780/750/30/92.4% murni ilustrasi fiktif sintaksis.

### B. Audit Mendalam Fungsi `resolve_signer_id()`

Implementasi pada [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L42-L50):
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

1. **Prioritas Identitas Utama**:
   - Jika baris manifest memiliki nilai `signer_id` (misalnya `"EXT_S01"`), nilai tersebut langsung digunakan. Kolom `subject_id` diabaikan sepenuhnya.
   - Terbukti memenuhi spesifikasi: `signer_id` adalah identitas utama.
2. **Pencegahan Duplikasi (Zero Double Counting)**:
   - Fungsi mengembalikan nilai tunggal (*single string*), bukan list atau tuple.
   - Dalam loop evaluasi, setiap sampel diregistrasikan ke dalam dictionary metrik per penutur tepat satu kali:
     ```python
     signer_data[sid]["true"].append(r["true_label"])
     signer_data[sid]["pred"].append(r["pred_label"])
     ```
   - Total sampel pada ringkasan evaluasi selalu sama dengan jumlah seluruh sampel per penutur: $\sum \text{samples}(sid) = \text{total\_evaluated\_samples}$.
3. **Evaluasi Risiko Fallback `"UNKNOWN_SIGNER"`**:
   - **Risiko Teridentifikasi**: Jika seorang operator mengunggah data dari beberapa penutur baru namun lupa mengisi kolom `signer_id` maupun `subject_id` (atau membiarkannya kosong/spasi), seluruh sampel dari penutur-penutur yang berbeda tersebut akan digabungkan ke dalam satu grup metrik bernama `"UNKNOWN_SIGNER"`.
   - **Konsekuensi Ilmiah**: Penggabungan sampel dari subjek berbeda ke dalam satu grup merusak kemampuan model auditor untuk menganalisis variansi performa per penutur (*inter-signer generalization variance*).
   - **Rekomendasi**:
     - *Rekomendasi 1 (Prosedural/Operator)*: Panduan operator [`docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md) telah mewajibkan pengisian `signer_id` dengan kode alokasi resmi (`EXT_S01`, `EXT_S02`, `EXT_S03`).
     - *Rekomendasi 2 (Peningkatan Proteksi Teknis di Masa Depan)*: Jika pengguna menghendaki penegakan metadata yang lebih ketat, script dapat dimutakhirkan untuk menolak baris dengan `signer_id` kosong sebagai kategori penolakan baru: `rejected_counts["missing_signer_id"]`. Saat ini, fungsi tetap mempertahankan `"UNKNOWN_SIGNER"` agar aman dan tidak memutus evaluasi jika terdapat data warisan (*legacy data*).

### C. Verifikasi Isolasi Data Tanpa Consent

Struktur kontrol pada loop utama [`evaluate_external_dataset()`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py#L137-L147):
```python
# 1. HARD REJECT: Informed Consent check BEFORE any image I/O or model inference
consent_status = (row.get("consent_status") or "").strip()
if consent_status != "CONSENT_SIGNED":
    logger.warning("Baris %d ditolak: consent_status ('%s') tidak valid...", idx, consent_status)
    rejected_counts["consent_invalid"] += 1
    continue  # <--- Bypasses file I/O, preprocessing, and model inference!

# 2. File check ...
# 5. Preprocessing & model inference ...
```
- **Analisis Alur Kontrol**: Pernyataan `continue` dieksekusi sebelum fungsi `Image.open`, `preprocess_image`, maupun `model(inp_tensor)` dipanggil.
- **Konfirmasi**: Data tanpa `consent_status == "CONSENT_SIGNED"` tidak memiliki jalur komputasi (*zero execution path*) menuju model inferensi.

---

## 4. HASIL AUDIT EKSEKUSI UNIT TEST

Suite unit test [`tests/test_evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_evaluate_external_images.py) dijalankan ulang secara langsung pada terminal proyek:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-8.2.2, pluggy-1.6.0
rootdir: D:\SEMESTER 5\ML\Projek_1
collected 11 items

tests/test_evaluate_external_images.py::test_resolve_signer_id_precedence PASSED          [  9%]
tests/test_evaluate_external_images.py::test_resolve_signer_id_fallback PASSED            [ 18%]
tests/test_evaluate_external_images.py::test_resolve_signer_id_unknown PASSED             [ 27%]
tests/test_evaluate_external_images.py::test_valid_consent_included_in_inference PASSED  [ 36%]
tests/test_evaluate_external_images.py::test_empty_consent_rejected_never_inferred PASSED [ 45%]
tests/test_evaluate_external_images.py::test_refused_consent_rejected_never_inferred PASSED [ 54%]
tests/test_evaluate_external_images.py::test_missing_consent_column_rejected_never_inferred PASSED [ 63%]
tests/test_evaluate_external_images.py::test_strict_unconsented_data_gating_mixed_manifest PASSED [ 72%]
tests/test_evaluate_external_images.py::test_signer_id_grouping_and_output PASSED        [ 81%]
tests/test_evaluate_external_images.py::test_empty_manifest_files PASSED                  [ 90%]
tests/test_evaluate_external_images.py::test_invalid_label_rejected PASSED               [100%]

============================= 11 passed in 22.92s =============================
```

### Pemetaan Bukti Test Case terhadap Klaim Laporan:
1. **Consent Valid**: `test_valid_consent_included_in_inference` membuktikan baris `CONSENT_SIGNED` sukses diproses dan model dipanggil tepat 1×.
2. **Consent Kosong**: `test_empty_consent_rejected_never_inferred` membuktikan string kosong `""` dan spasi `"   "` ditolak dengan `mock_model.call_count == 0`.
3. **Consent Ditolak / Tidak Standar**: `test_refused_consent_rejected_never_inferred` membuktikan `CONSENT_REFUSED`, `CONSENT_PENDING`, `NO`, dan huruf kecil `consent_signed` ditolak dengan `mock_model.call_count == 0`.
4. **Kolom Consent Tidak Ada**: `test_missing_consent_column_rejected_never_inferred` membuktikan manifest tanpa kolom `consent_status` ditolak dengan `mock_model.call_count == 0`.
5. **Gating Campuran**: `test_strict_unconsented_data_gating_mixed_manifest` membuktikan pada manifest campuran 5 baris, hanya 2 baris sah yang diproses ke model (`mock_model.call_count == 2`), sedangkan 3 baris tidak sah langsung dibuang.
6. **Pengelompokan `signer_id`**: `test_signer_id_grouping_and_output` membuktikan agregasi per subjek berjalan presisi tanpa duplikasi.
7. **Manifest Kosong & Template**: `test_empty_manifest_files` membuktikan berkas kosong menghasilkan status `PENDING EXTERNAL DATA` tanpa memicu model error.
8. **Label Tidak Valid**: `test_invalid_label_rejected` membuktikan label di luar A–Z ditolak sebelum inferensi.

---

## 5. STATUS DATA AKTUAL & PEMERIKSAAN INTEGRITAS

### A. Audit Fisik Direktori Data Eksternal
Pemeriksaan rekursif pada folder target:
```powershell
Get-ChildItem -Path "data/external/bisindo_validation" -Recurse -Include *.jpg,*.png,*.jpeg | Measure-Object
```
- **Jumlah file citra**: **0 file**
- **Status Pengumpulan**: **`0 / 780 FOTO (PENDING DATA COLLECTION)`**
- **Kesimpulan**: Belum ada data eksternal fisik nyata yang dikumpulkan. Seluruh evaluasi inferensi terhadap data nyata **belum pernah dijalankan**, sesuai dengan etika riset.

### B. Audit Integritas Checkpoint & Model Produksi (SHA-256)
Pemeriksaan hash kriptografis membuktikan bahwa seluruh artefak model tetap steril 100%:
- `runs/image_i1_mobilenetv3_p1/best.pt`: `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` (**UTUH**)
- `web/model/fingerspell.onnx`: `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` (**UTUH**)
- `runs/image_i1_mobilenetv3/best.pt`: `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` (**UTUH**)

### C. Status Git Repository
- **Commit HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (Tidak berubah)
- **Tracked files modified**: **0 file** (Tidak ada operasi commit, push, merge, reset, clean, atau checkout).

---

## 6. KESIMPULAN AKHIR

Pipeline evaluasi eksternal model BISINDO I1-P1 telah diaudit secara tuntas:
1. **Keamanan Etik Terjamin**: Data tanpa informed consent sah terbukti secara logis dan empiris tidak akan pernah masuk ke model inferensi.
2. **Kesesuaian Skema**: Penamaan metrik dan field output telah diselaraskan menggunakan `signer_id`.
3. **Dokumentasi Transparan**: Peringatan ilustrasi telah disematkan untuk menjamin tidak ada misleading informasi.
4. **Kesiapan Sistem**: Seluruh komponen script, template manifest, dan unit test telah berada dalam status **`READY FOR FIELD DATA COLLECTION`**. Validasi eksternal baru akan dieksekusi setelah 780 foto riil dikumpulkan oleh operator.

