# LAPORAN VERIFIKASI SILSILAH DATA PELATIHAN HISTORIS (FINAL TRAINING DATA LINEAGE VERIFICATION)
## SignBridge ASEAN — Modality Image I1-P1 & I1-P0

> **Dokumen**: `docs/validation_p1/FINAL_TRAINING_DATA_LINEAGE_VERIFICATION.md`  
> **Tipe Evaluasi**: Historical Data Lineage, Checkpoint Provenance, & Timestamp Forensic Audit  
> **Target Verifikasi**: Konfirmasi Historis Eksklusi 4 Citra Klon Lintas-Kelas pada Pelatihan P0 dan P1  
> **Tanggal Audit**: 17 November 2026  
> **Auditor**: Senior Machine Learning Auditor, Computer Vision Engineer, & Data Quality Analyst  
> **Status Klasifikasi**: **`TRAINING_LINEAGE_VERIFIED_CLEAN`**

---

## 1. EXECUTIVE SUMMARY

Investigasi forensik silsilah data (*data lineage audit*) telah dilakukan untuk memverifikasi secara independen dan berbasis bukti historis apakah dataset yang benar-benar digunakan saat pelatihan checkpoint baseline **P0** (`runs/image_i1_mobilenetv3_p0/best.pt`) dan **P1** (`runs/image_i1_mobilenetv3_p1/best.pt`) telah mengeksklusi empat citra duplikat biner lintas-kelas:
1. `data/raw/image/bisindo_alphabet/D/D_Polos Gelap_iPhone_XR.jpeg`
2. `data/raw/image/bisindo_alphabet/P/P_Polos Gelap_iPhone_XR.jpeg`
   *(SHA-256: `a99273b2ca82794cb612bc3ace480521ae73d2cb41d6f406bbc14d586d095aa0`)*
3. `data/raw/image/bisindo_alphabet/B/B_polos gelap_Iphone_13promax.jpg`
4. `data/raw/image/bisindo_alphabet/E/E_polos gelap_Iphone_13promax.jpg`
   *(SHA-256: `99c4a1565f4c49c05be9badc4be2836d9353e35acd49fe2e76dc08aa86d46e53`)*

### Ringkasan Temuan Faktual:
- **Konfirmasi Bukti Historis**: Eksklusi keempat citra duplikat biner tersebut terbukti secara historis telah terjadi **sebelum** proses pelatihan P0 dan P1 dimulai pada tanggal **13 November 2026**.
- **Kronologi Timestamp yang Terkunci**: Dataset manifest terproses (`manifest.csv`) dibuat pada pukul **17:01:32 WIB** dan tidak pernah diubah sejak saat itu. Pelatihan P0 dimulai pukul **17:11 WIB**, dan pelatihan P1 dimulai pukul **18:22 WIB**.
- **Metadata Biner Checkpoint**: Konfigurasi yang tersimpan di dalam bobot checkpoint PyTorch (`best.pt`) untuk P0 dan P1 secara eksplisit merekam path `manifest.csv` dan `preprocessing_audit_manifest.csv`.
- **Paritas Sampel Pembagi**: Ringkasan pelatihan historis (`training_summary.json`) dari P0 dan P1 mencatat total sampel $N = 4.462$ (Train: 3.123, Val: 669, Test: 670), yang secara matematis merefleksikan $4.466 - 4 = 4.462$. Nilai penyebut akurasi validasi pada checkpoint P1 ($403 / 669 = 0,60239$) membuktikan jumlah sampel validasi tepat 669 sampel.
- **Kesimpulan Klasifikasi**: Status resmi ditetapkan sebagai **`TRAINING_LINEAGE_VERIFIED_CLEAN`**.

---

## 2. MANIFEST & KONFIGURASI YANG DIGUNAKAN P0 (TASK 2 & TASK 4)

Pelatihan baseline P0 dijalankan menggunakan skrip `scripts/train_and_evaluate_p0.py` dan konfigurasi tersimpan `runs/image_i1_mobilenetv3_p0/training_config.yaml`.

### Konfigurasi Data yang Terekam:
```yaml
data:
  manifest: data/processed/bisindo_alphabet/manifest.csv
  audit_manifest: data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv
  num_classes: 26
  image_size: 224
```

### Bukti Internal Checkpoint P0 (`runs/image_i1_mobilenetv3_p0/best.pt`):
Pemeriksaan struktur dictionary biner PyTorch checkpoint P0 (ukuran 3.272.237 bytes, SHA-256: `39B26F97...`) mengungkapkan metadata yang tersimpan:
- `epoch`: 12
- `val_acc`: `0.11210762331838565` ($75 / 669 \approx 0,112108$)
- `val_f1`: `0.11211700402960312`
- `config`: Memuat dictionary konfigurasi lengkap yang merujuk langsung ke `data/processed/bisindo_alphabet/manifest.csv`.

*Catatan Checkpoint P0 Legacy*: Checkpoint lama di `runs/image_i1_mobilenetv3/best.pt` (tertanggal 6 November 2026, SHA-256: `6767DCAA...`) adalah model inisialisasi prototipe awal yang dilatih pada folder `data/fingerspelling_crops` (sebelum dataset Mendeley diunduh). Checkpoint ini tidak menggunakan data Mendeley.

---

## 3. MANIFEST & KONFIGURASI YANG DIGUNAKAN P1 (TASK 3 & TASK 4)

Pelatihan transfer learning P1 dijalankan menggunakan skrip `scripts/train_and_evaluate_p1.py` dan konfigurasi tersimpan `runs/image_i1_mobilenetv3_p1/training_config.yaml`.

### Konfigurasi Data yang Terekam:
```yaml
data:
  manifest: data/processed/bisindo_alphabet/manifest.csv
  audit_manifest: data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv
  num_classes: 26
  image_size: 224
```

### Bukti Internal Checkpoint P1 (`runs/image_i1_mobilenetv3_p1/best.pt`):
Pemeriksaan struktur dictionary biner PyTorch checkpoint P1 (ukuran 6.302.825 bytes, SHA-256: `83C6A093...`) mengungkapkan metadata yang tersimpan:
- `epoch`: 18
- `stage`: `stage2`
- `val_acc`: `0.6023916292974589` ($403 / 669 \approx 0,602392$)
- `val_f1`: `0.5958015813833096`
- `config`: Memuat konfigurasi lengkap dengan path manifest terikat ke `data/processed/bisindo_alphabet/manifest.csv`.

---

## 4. VERIFIKASI EMPAT EXACT DUPLICATE PADA SELURUH SUMBER DATA TRAINING (TASK 6)

Dilakukan pencarian menyeluruh terhadap hash SHA-256 dan nama file keempat citra duplikat pada seluruh artefak pelatihan:

| Artefak / Sumber Data | Jumlah Baris Data | Pencarian Target Hash SHA-256 | Pencarian Target Nama File | Status Keberadaan |
|---|:---:|:---:|:---:|:---:|
| **Processed Manifest (`manifest.csv`)** | 4.462 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Split Training (Train)** | 3.123 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Split Validation (Val)** | 669 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Split Testing (Test)** | 670 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **P1 Predictions CSV (`predictions.csv`)** | 670 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Storage Citra JPG Processed** | 4.462 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Storage Array NPY Processed** | 4.462 | **0 Cocok** | **0 Cocok** | **BERSIH (ABSENT)** |
| **Audit Manifest (`preprocessing_audit_manifest.csv`)** | 4.466 | **4 Cocok (EXCLUDED)** | **4 Cocok (EXCLUDED)** | **TERCATAT SEBAGAI EKSKLUSI** |

### Detail Entri Eksklusi pada Audit Manifest:
Keempat file ditemukan secara eksklusif pada `preprocessing_audit_manifest.csv` dengan metadata penanda:
1. `B_polos gelap_Iphone_13promax.jpg` $\to$ `split: excluded`, `preprocessing_status: EXCLUDED`, `reason: CROSS_CLASS_DUPLICATE (B vs E): sha256=99c4a1565f4c49c0`
2. `D_Polos Gelap_iPhone_XR.jpeg` $\to$ `split: excluded`, `preprocessing_status: EXCLUDED`, `reason: CROSS_CLASS_DUPLICATE (D vs P): sha256=a99273b2ca82794c`
3. `E_polos gelap_Iphone_13promax.jpg` $\to$ `split: excluded`, `preprocessing_status: EXCLUDED`, `reason: CROSS_CLASS_DUPLICATE (B vs E): sha256=99c4a1565f4c49c0`
4. `P_Polos Gelap_iPhone_XR.jpeg` $\to$ `split: excluded`, `preprocessing_status: EXCLUDED`, `reason: CROSS_CLASS_DUPLICATE (D vs P): sha256=a99273b2ca82794c`

---

## 5. PEMERIKSAAN CACHE & INDEKS DATASET (TASK 5 & TASK 7)

Dilakukan inspeksi terhadap kode pemanggilan data pada `scripts/train_and_evaluate_p1.py` (kelas `FingerspellP1Dataset`) dan `signbridge/image/train_image.py` (kelas `FingerspellDataset`):

1. **Mekanisme Pembacaan**: Kedua skrip memuat data langsung dari file `manifest.csv` baris demi baris menggunakan `csv.DictReader`. Tidak ada file cache tersembunyi (*hidden cache file*), database index SQLite sekunder, atau binary pickle dump perantara yang digunakan saat pelatihan.
2. **Audit Leakage Otomatis saat Runtime**:
   Skrip `FingerspellP1Dataset` memvalidasi irisan antar-split pada waktu inisialisasi:
   ```python
   for s1, s2 in (("train", "val"), ("train", "test"), ("val", "test")):
       if split_paths[s1].intersection(split_paths[s2]):
           raise ValueError(f"Data leakage detected on path between {s1} and {s2}")
       if split_shas[s1].intersection(split_shas[s2]):
           raise ValueError(f"Data leakage detected on SHA-256 between {s1} and {s2}")
   ```
   Karena pelatihan berhasil diselesaikan tanpa memicu eksepsi `ValueError`, terbukti secara runtime bahwa tidak ada kebocoran hash SHA-256 maupun path lintas-split.
3. **Pencarian Duplikat dengan Nama Berbeda**:
   Pemindaian terhadap seluruh kolom `original_sha256` dan `sha256` pada 4.462 baris `manifest.csv` mengonfirmasi **0 baris** yang memiliki nilai hash `a99273b2...` maupun `99c4a156...`. Tidak ada salinan dengan nama samaran (*aliased copies*) yang menyusup ke dalam dataset terproses.

---

## 6. BUKTI HISTORIS TIMELINE PREPROCESSING & TRAINING (TASK 8)

Rekonstruksi forensik urutan waktu (*chronological timeline analysis*) berdasarkan timestamp sistem operasi (`LastWriteTime` pada filesystem NTFS):

```mermaid
timeline
    title Kronologi Forensik Preprocessing dan Pelatihan Baseline (13 November 2026)
    17:00:59 : Skrip Preprocessing Selesai Dibuat (scripts/preprocess_bisindo_alphabet.py)
    17:01:32 : Preprocessing Selesai Dijalankan (manifest.csv & audit_manifest.csv Diciptakan)
    17:11:23 : Pelatihan P0 Dimulai (runs/image_i1_mobilenetv3_p0/training_config.yaml Diciptakan)
    17:29:16 : P0 Checkpoint Terbaik Dihasilkan (runs/image_i1_mobilenetv3_p0/best.pt)
    17:57:45 : Pelatihan P0 Selesai (runs/image_i1_mobilenetv3_p0/training_summary.json)
    18:22:54 : Pelatihan P1 Dimulai (runs/image_i1_mobilenetv3_p1/training_config.yaml Diciptakan)
    18:41:37 : P1 Checkpoint Terbaik Dihasilkan (runs/image_i1_mobilenetv3_p1/best.pt)
    18:44:01 : Evaluasi Test Set P1 Selesai (predictions.csv & training_summary.json)
```

### Tabel Rincian Bukti Waktu (WIB / Local Time):

| Komponen Artefak | Path File | Waktu Modifikasi Terakhir | Hubungan Temporal |
|---|---|:---:|---|
| **Skrip Preprocessing** | `scripts/preprocess_bisindo_alphabet.py` | 13/11/2026 17:00:59 | Precursor: Logika filter eksklusi dikompilasi |
| **Manifest Processed** | `data/processed/bisindo_alphabet/manifest.csv` | 13/11/2026 17:01:32 | **Baseline Data Terkunci (4.462 baris)** |
| **Audit Manifest** | `data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv` | 13/11/2026 17:01:32 | 4 file duplikat biner resmi dicatat sebagai `EXCLUDED` |
| **P0 Training Config** | `runs/image_i1_mobilenetv3_p0/training_config.yaml` | 13/11/2026 17:11:23 | Dibuat **9 menit 51 detik SETELAH** manifest terkunci |
| **P0 Best Checkpoint** | `runs/image_i1_mobilenetv3_p0/best.pt` | 13/11/2026 17:29:16 | Dibuat saat training epoch 12 P0 |
| **P0 Training Summary**| `runs/image_i1_mobilenetv3_p0/training_summary.json` | 13/11/2026 17:57:45 | P0 selesai melatih 25 epoch |
| **P1 Training Config** | `runs/image_i1_mobilenetv3_p1/training_config.yaml` | 13/11/2026 18:22:54 | Dibuat **1 jam 21 menit SETELAH** manifest terkunci |
| **P1 Best Checkpoint** | `runs/image_i1_mobilenetv3_p1/best.pt` | 13/11/2026 18:41:37 | Dibuat saat training epoch 18 P1 |
| **P1 Predictions CSV** | `runs/image_i1_mobilenetv3_p1/predictions.csv` | 13/11/2026 18:44:01 | Evaluasi Test Set P1 selesai |

*Integritas Timestamp*: Timestamp file `data/processed/bisindo_alphabet/manifest.csv` adalah **13/11/2026 17:01:32** dan **tidak pernah tersentuh modifikasi** sejak menit tersebut. Ini membuktikan bahwa file manifest yang ada saat ini adalah file yang persis sama dengan yang dibaca oleh script training P0 dan P1 pada tanggal 13 November 2026.

---

## 7. STATUS INTEGRITAS CHECKPOINT P0, P1, DAN ONNX PRODUKSI

Verifikasi hash SHA-256 pada seluruh model memastikan paritas kriptografis paripurna:

| Checkpoint Model | Lokasi File | Hash SHA-256 Terverifikasi | Status Paritas Baseline |
|---|---|---|:---:|
| **P1 Best Checkpoint** | `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% IDENTIK ✅** |
| **P0 Scratch Checkpoint** | `runs/image_i1_mobilenetv3_p0/best.pt` | `39B26F97A9916A9374567AA7FE25FE997CBB5BAA58C6B34D7DA5533A68E3990A` | **100% IDENTIK ✅** |
| **P0 Baseline (Legacy)** | `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% IDENTIK ✅** |
| **Production ONNX** | `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% IDENTIK ✅** |

---

## 8. KETERBATASAN BUKTI (LIMITATIONS)

Meskipun eksklusi empat citra duplikat biner terbukti secara historis, terdapat keterbatasan metodologis yang harus tetap dicatat:
1. **Ketiadaan Metadata Signer ID**: Eksklusi berhasil menghapus *exact binary duplicates*, namun ketiadaan metadata penutur pada dataset Mendeley berarti potensi *subject leakage* (penutur yang sama terdistribusi ke train, val, dan test) tetap menjadi risiko bawaan dataset Mendeley secara keseluruhan.
2. **Keterbatasan Exact Hash Matching**: Skrip preprocessing hanya memfilter citra dengan SHA-256 identik bit-by-bit. Jika pengunggah dataset asli mengambil foto beruntun (*burst shots*) dari pose yang sama dengan perbedaan piksel mikro, citra tersebut tidak akan terdeteksi oleh filter hash biner sederhana.

---

## 9. KESIMPULAN AKHIR KLASIFIKASI

Berdasarkan konvergensi bukti dari:
- Timestamp filesystem NTFS yang membuktikan preprocessing selesai sebelum pelatihan P0 dan P1 dimulai,
- Serialisasi dictionary konfigurasi di dalam file biner `.pt` checkpoint P0 dan P1,
- Paritas matematis jumlah sampel pada training summary ($N = 4.462 = 4.466 - 4$),
- Ketiadaan 100% hash target pada seluruh kolom manifest dan file prediksi,

Maka status silsilah data pelatihan resmi ditetapkan sebagai:

$$\mathbf{TRAINING\_LINEAGE\_VERIFIED\_CLEAN}$$

