# LAPORAN AUDIT READ-ONLY INTEGRASI MANIFEST
## FITUR EXTERNAL DATA COLLECTION TRACKER (I1-P1)

**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/MANIFEST_INTEGRATION_AUDIT.md`  
**Tanggal Audit**: 16 November 2026  
**Jenis Audit**: `READ-ONLY AUDIT & INTEGRITY CHECK` (Zero Code Modifications)  
**Target Komponen**: [`scripts/validation_p1/track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py)  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)

---

## 1. RINGKASAN EKSEKUTIF AUDIT

Audit *read-only* ini dilakukan untuk mengevaluasi secara kritis mekanisme integrasi file manifest pada script [`track_external_collection.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py) sebelum digunakan oleh operator lapangan untuk pengumpulan 780 foto eksternal penutur `EXT_S01`–`EXT_S03`.

### Hasil Ringkas Audit (7 Fokus Pemeriksaan):
1. **Pemilihan File Manifest**: Script saat ini membaca `external_manifest_template.csv` karena file aktual `external_manifest.csv` belum ada di disk. Script telah memiliki logika kondisional untuk otomatis beralih ke `external_manifest.csv` begitu file tersebut dibuat.
2. **Perlindungan Terhadap Template**: Template terbukti **tidak pernah dianggap sebagai manifest aktual berisi data**, karena baris contoh di template diawali karakter `#` dan otomatis diabaikan sebagai komentar.
3. **Kesiapan Pembacaan Manifest Aktual**: Terverifikasi siap. Tracker otomatis memprioritaskan `external_manifest.csv` jika file tersebut ada di direktori dataset.
4. **Resolusi Path Relatif**: **DITEMUKAN MASALAH POTENSIAL (Temuan #1)**. Script saat ini menyelesaikan path relatif terhadap `ROOT` repository (`D:\SEMESTER 5\ML\Projek_1`), bukan terhadap `data_dir` (`data/external/bisindo_validation`). Jika operator menulis path relatif dari folder dataset (misalnya `A/EXT_S01_A_01.jpg`), file akan gagal ditemukan dan salah ditandai sebagai hilang (*missing*).
5. **Deteksi Foto di Disk Belum Tercatat**: Terverifikasi bekerja sempurna. Seluruh file citra fisik di disk yang tidak tercatat di manifest atau memiliki consent tidak sah otomatis masuk ke `unregistered_disk_count` dan memicu status `NEEDS REVIEW`.
6. **Penanganan Manifest Kosong**: Terverifikasi mutlak menghasilkan status `NOT STARTED` (0/780, 0.0%) dan secara logika tidak mungkin menghasilkan status `COMPLETE`.
7. **Penyajian Lokasi Manifest pada Laporan**: **DITEMUKAN AMBIGUITAS (Temuan #2)**. Laporan saat ini menampilkan path `external_manifest_template.csv` sebagai file manifest aktif, yang dapat membingungkan operator lapangan mengenai file mana yang seharusnya diisi.

---

## 2. PEMBAHASAN MENDALAM 7 FOKUS PEMERIKSAAN

### Fokus 1: Apakah script membaca `external_manifest.csv` atau `external_manifest_template.csv`?

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L86-L94`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L86-L94)):
```python
# 2. Locate manifest file
if manifest_path is None:
    cand_manifest = data_dir / "external_manifest.csv"
    if cand_manifest.exists():
        manifest_path = cand_manifest
    else:
        cand_template = data_dir / "external_manifest_template.csv"
        manifest_path = cand_template if cand_template.exists() else cand_manifest
elif not manifest_path.is_absolute():
    manifest_path = ROOT / manifest_path
```

**Analisis**:
- Ketika opsi CLI `--manifest` tidak ditentukan (default `None`), script memeriksa keberadaan `cand_manifest` (`data/external/bisindo_validation/external_manifest.csv`).
- Karena `external_manifest.csv` belum dibuat secara fisik, kondisi `cand_manifest.exists()` bernilai `False`.
- Script kemudian beralih ke `cand_template` (`data/external/bisindo_validation/external_manifest_template.csv`).
- **Kesimpulan**: Saat ini tracker **masih membaca `external_manifest_template.csv`** sebagai fallback ketiadaan file manifest aktual.

---

### Fokus 2: Memastikan template tidak dianggap sebagai manifest aktual

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L121-L125`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L121-L125)):
```python
for idx, row in enumerate(manifest_rows):
    raw_p = (row.get("image_path") or row.get("path") or "").strip()
    if not raw_p or raw_p.startswith("#"):
        continue
    non_comment_rows += 1
```

**Analisis**:
- Isi file `external_manifest_template.csv` baris ke-2:
  `# CONTOH_PENGISIAN: data/external/bisindo_validation/A/EXT_S01_A_01.jpg,A,EXT_S01,...`
- Karena diawali karakter `#`, baris contoh tersebut diabaikan sepenuhnya (`continue`).
- Variabel `non_comment_rows` bernilai `0`, dan `valid_samples` kosong (`0`).
- Pada penentuan status ([baris 256](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L256)):
  `if total_valid == 0 and len(disk_images_map) == 0 and non_comment_rows == 0: overall_status = "NOT STARTED"`
- **Kesimpulan**: Template **aman dari kontaminasi data**. Tidak ada data contoh template yang dihitung sebagai sampel aktual.

---

### Fokus 3: Kesiapan tracker membaca manifest aktual setelah dibuat operator

**Analisis Alur**:
- Jika operator membuat file `data/external/bisindo_validation/external_manifest.csv`, pada eksekusi berikutnya `cand_manifest.exists()` akan bernilai `True`.
- `manifest_path` secara otomatis diisi dengan `external_manifest.csv`.
- Script juga mendukung argumen eksplisit CLI `--manifest data/external/bisindo_validation/external_manifest.csv`.
- **Kesimpulan**: Mekanisme deteksi otomatis sudah siap menyambut manifest aktual tanpa memerlukan konfigurasi manual tambahan.

---

### Fokus 4: Resolusi path relatif manifest terhadap direktori dataset

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L167-L170`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L167-L170)):
```python
# Resolve path and check existence on disk
p = Path(raw_p)
if not p.is_absolute():
    p = ROOT / p
resolved_p = p.resolve()
```

**Temuan Masalah (Temuan #1)**:
- Script mengasumsikan seluruh path relatif dihitung dari `ROOT` (`D:\SEMESTER 5\ML\Projek_1`).
- Pada panduan operator ([`EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md#L142`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md#L142)), operator diminta menulis:  
  `data/external/bisindo_validation/A/EXT_S01_A_01.jpg`.
- **Namun**, konvensi umum dataset sering kali menuliskan path relatif terhadap direktori dataset itu sendiri (misalnya `A/EXT_S01_A_01.jpg` atau `./A/EXT_S01_A_01.jpg`).
- Jika operator menulis `A/EXT_S01_A_01.jpg`, script akan mencari di `D:\SEMESTER 5\ML\Projek_1\A\EXT_S01_A_01.jpg` yang berakibat:
  1. File dianggap hilang (`missing_disk_records += 1`).
  2. File asli di `data/external/bisindo_validation/A/EXT_S01_A_01.jpg` dianggap belum terdaftar (`unregistered_disk_files += 1`).
- **Kesimpulan**: Script **belum fleksibel dan belum menyelesaikan path relatif secara konsisten terhadap direktori dataset (`data_dir`)**.

---

### Fokus 5: Deteksi foto di disk yang belum tercatat di manifest

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L223-L227`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L223-L227)):
```python
# 4. Check unregistered files on disk (files on disk not in seen_file_paths)
unregistered_disk_files: List[str] = []
for resolved_p, rel_p in disk_images_map.items():
    if resolved_p not in seen_file_paths:
        unregistered_disk_files.append(str(rel_p))
```

**Analisis**:
- `scan_disk_images()` memindai seluruh file berekstensi `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp` di dalam `data_dir` secara rekursif.
- Hanya foto yang **lolos seluruh validasi** (consent `CONSENT_SIGNED`, penutur valid, label valid, bukan duplikat) yang dimasukkan ke `seen_file_paths`.
- Seluruh file citra di disk yang tidak terdapat di `seen_file_paths` dimasukkan ke `unregistered_disk_files`.
- Jika `len(unregistered_disk_files) > 0`, sistem memicu flag `has_blocking_anomalies = True` sehingga status menjadi `NEEDS REVIEW`.
- Pengujian unit test `test_unregistered_disk_image_triggers_needs_review` membuktikan perilaku ini berjalan 100% akurat.
- **Kesimpulan**: Terverifikasi bekerja sempurna.

---

### Fokus 6: Manifest kosong menghasilkan `NOT STARTED`, bukan `COMPLETE`

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L256-L260`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L256-L260)):
```python
if total_valid == 0 and len(disk_images_map) == 0 and non_comment_rows == 0:
    overall_status = "NOT STARTED"
    status_description = "Belum ada foto eksternal fisik yang dikumpulkan maupun didaftarkan di manifest."
elif total_valid == TOTAL_TARGET and not has_blocking_anomalies:
    overall_status = "COMPLETE"
```

**Analisis**:
- Kasus 1 (Manifest kosong / hanya header / hanya komentar, folder kosong):
  - `total_valid = 0`
  - `len(disk_images_map) = 0`
  - `non_comment_rows = 0`
  - Status tepat: **`NOT STARTED`**.
- Status `COMPLETE` memiliki syarat mutlak:
  1. `total_valid == TOTAL_TARGET` (tepat 780 foto valid).
  2. `not has_blocking_anomalies` (0 missing, 0 unregistered, 0 unconsented, 0 duplicate, 0 invalid signer/label).
- Karena `0 == 780` adalah `False`, tidak ada celah logika di mana manifest kosong dapat menghasilkan `COMPLETE`.
- Pengujian unit test `test_empty_folder_and_empty_manifest_status_not_started` membuktikan status adalah `NOT STARTED` dengan defisit 780.
- **Kesimpulan**: Terverifikasi aman.

---

### Fokus 7: Penampilan lokasi manifest aktual pada laporan progres

**Kode Sumber** ([`scripts/validation_p1/track_external_collection.py#L324`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/track_external_collection.py#L324)):
```python
f"**File Manifest**: `{manifest_path.as_posix() if manifest_path else 'None'}`  "
```

**Temuan Masalah (Temuan #2)**:
- Pada dokumen laporan [`docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md#L7`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md#L7), teks yang tertulis saat ini adalah:
  `**File Manifest**: D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv`
- Header laporan tidak memberikan indikasi apakah file tersebut merupakan manifest riil atau sekadar template referensi.
- Operator yang membaca laporan tidak mendapatkan petunjuk eksplisit bahwa `external_manifest.csv` sebenarnya **belum dibuat**.
- **Kesimpulan**: Laporan belum membedakan antara manifest operasional riil dengan template referensi fallback.

---

## 3. TABEL DAFTAR TEMUAN MASALAH & REKOMENDASI

Sesuai instruksi audit, **tidak ada kode yang diubah pada tahap ini**. Berikut rincian temuan masalah, akar masalah, dampak, dan rekomendasi perbaikannya:

| ID | File & Baris Kode | Klasifikasi | Akar Masalah | Dampak Operasional | Rekomendasi Solusi |
|---|---|---|---|---|---|
| **GAP-01** | `scripts/validation_p1/track_external_collection.py`<br>Baris 167–170 | **Fungsionalitas / Kompatibilitas Path** | Resolusi path relatif hanya menguji `ROOT / p` (`D:\SEMESTER 5\ML\Projek_1\...`), mengabaikan direktori dataset `data_dir` (`data/external/bisindo_validation`). | Jika operator menulis path relatif dari folder dataset (misalnya `A/EXT_S01_A_01.jpg`), foto yang ada di disk akan salah ditandai sebagai hilang (*missing*) dan memicu anomali palsu. | Ubah logika resolusi menjadi *multi-fallback*: prioritaskan `(data_dir / p).exists()`, lalu `(ROOT / p).exists()`, sehingga kedua gaya penulisan didukung tanpa error. |
| **GAP-02** | `scripts/validation_p1/track_external_collection.py`<br>Baris 86–94 & Baris 324 | **Transparansi Status Manifest** | Fallback otomatis ke template menyamarkan ketiadaan file manifest aktual pada laporan markdown dan output JSON. | Operator mengira sistem sudah membaca manifest aktual atau terdorong untuk mengedit file template alih-alih membuat `external_manifest.csv`. | 1. Pisahkan variabel `manifest_path` (file aktual target) dan `is_template_fallback`.<br>2. Pada laporan, beri label tegas: `external_manifest.csv (BELUM DIBUAT — Menggunakan template referensi)`. |
| **GAP-03** | `scripts/validation_p1/evaluate_external_images.py`<br>Baris 170–173 | **Konsistensi Pipeline Evaluasi** | Script evaluasi inferensi juga menggunakan `p = ROOT / p` murni tanpa fallback ke `data_dir / p`. | Ketidakkonsistenan yang sama akan terjadi saat script evaluasi inferensi dijalankan nanti jika operator menggunakan path relatif dataset. | Samakan logika resolusi path *multi-fallback* antara script tracker dan script evaluasi inferensi. |

---

## 4. FORMULASI REKOMENDASI PERBAIKAN KODE

Rekomendasi teknis yang disiapkan untuk diimplementasikan setelah persetujuan pengguna:

### Usulan Perbaikan GAP-01 & GAP-03 (Resolusi Path Relatif Cerdas):
```python
def resolve_image_path(raw_path: str, data_dir: Path) -> Path:
    """Resolves relative image path against data_dir first, then ROOT."""
    p = Path(raw_path.strip())
    if p.is_absolute():
        return p
    # Prioritaskan path relatif terhadap folder dataset (e.g., "A/EXT_S01_A_01.jpg")
    if (data_dir / p).exists():
        return data_dir / p
    # Fallback path relatif terhadap root repo (e.g., "data/external/bisindo_validation/A/...")
    if (ROOT / p).exists():
        return ROOT / p
    # Default jika file belum ada di disk: pilih berdasarkan format string
    return ROOT / p if str(raw_path).startswith("data/") else data_dir / p
```

### Usulan Perbaikan GAP-02 (Transparansi Manifest pada Tracker):
```python
cand_manifest = data_dir / "external_manifest.csv"
if cand_manifest.exists():
    manifest_path = cand_manifest
    manifest_type = "ACTUAL_MANIFEST"
else:
    cand_template = data_dir / "external_manifest_template.csv"
    manifest_path = cand_template if cand_template.exists() else cand_manifest
    manifest_type = "TEMPLATE_REFERENCE (Actual external_manifest.csv not yet created)"
```

---

## 5. KESIMPULAN AUDIT

1. Integrasi manifest saat ini **sudah aman dari kebocoran data fiktif** (template diabaikan, manifest kosong tidak menghasilkan `COMPLETE`).
2. Terdapat **2 area perbaikan penting** (resolusi path dataset dan transparansi status file manifest) yang sangat disarankan untuk disempurnakan sebelum operator lapangan memulai pengisian data.
3. Seluruh integritas sistem (Git repository, checkpoint model, dan bobot inferensi) tetap **100% terjaga dan steril**.

