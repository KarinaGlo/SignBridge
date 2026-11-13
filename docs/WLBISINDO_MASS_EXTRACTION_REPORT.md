# LAPORAN EKSTRAKSI MASSAL DATASET WL-BISINDO (TAHAP A.3.3)

**Tanggal:** 8 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Git Branch:** `feature/dataset-acquisition`  
**Git HEAD:** `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` (100% dipertahankan, tanpa commit/push/merge)  
**Status Keseluruhan:** **`PASS (100% BERHASIL TANPA KEGAGALAN)`**

---

## 1. Ringkasan Eksekutif Proses Ekstraksi

Ekstraksi massal terhadap seluruh **1.600 video MP4 asli** dari dataset WL-BISINDO (`data/raw/video/wl_bisindo/videos/`) telah berhasil diselesaikan secara penuh dengan pipeline kanonis SignBridge Contract 3:

- **Metode Eksekusi:** Ekstraksi bertahap 16 batch @ 100 video menggunakan `ProcessPoolExecutor` (4 worker CPU mandiri).
- **Mekanisme Keamanan:** Checkpoint persisten per batch (`data/keypoints/wl_bisindo/checkpoint.json`), atomic file writing (`.tmp.npz` $\rightarrow$ `.npz`), dan validasi fisik instan setiap tensor.
- **Kontrak Fitur:** Setiap video diubah menjadi tensor temporal berdimensi `[64, 86, 3]` bertipe `float32` dengan boolean mask `valid_mask [64, 86]`, normalisasi spasial berpusat bahu, dan resampling deterministik midpoint-floor.
- **Integritas Zero-Synthetic:** Tidak ada koordinat acak, landmark fiktif, interpolasi palsu, atau data buatan. Seluruh titik yang hilang ditandai dengan koordinat `0.0` dan `valid_mask = False`.

---

## 2. Metrik Volume & Tingkat Keberhasilan

| Parameter Metrik | Nilai Aktual | Persentase | Status |
|---|:---:|:---:|:---:|
| **Total Video Sumber Ditemukan** | 1.600 | 100,00% | `PASS` |
| **Total Video Berhasil Diekstrak** | 1.600 | 100,00% | `PASS` |
| **Total Video Gagal** | 0 | 0,00% | `PASS` |
| **Total File NPZ Output Valid** | 1.600 | 100,00% | `PASS` |
| **File Pilot A.3.2 Tetap Tersedia** | 10 | 100,00% | `PASS` |
| **Durasi Total Ekstraksi Paralel** | 46,79 menit | Rata-rata 1,75 detik/video | `OPTIMAL` |

---

## 3. Distribusi Sampel Berdasarkan Signer

Distribusi video per individu penutur isyarat (*signer*) terverifikasi akurat sesuai metadata fisik arsip sumber:

| Signer ID | Jumlah Video | Persentase | Cakupan Kelas Label | Kelayakan Uji LOSO |
|---|:---:|:---:|---|:---:|
| **`SIGNER0`** | 120 | 7,50% | Label 0–11 (12 kelas) | **Dilarang sebagai Test Fold Tunggal** |
| **`SIGNER1`** | 420 | 26,25% | Label 0–31 (32 kelas lengkap) | Valid sebagai Test Fold |
| **`SIGNER2`** | 420 | 26,25% | Label 0–31 (32 kelas lengkap) | Valid sebagai Test Fold |
| **`SIGNER3`** | 320 | 20,00% | Label 0–31 (32 kelas lengkap) | Valid sebagai Test Fold |
| **`SIGNER4`** | 320 | 20,00% | Label 0–31 (32 kelas lengkap) | Valid sebagai Test Fold |
| **Total** | **1.600** | **100,00%** | **32 kelas resmi terdistribusi** | — |

---

## 4. Distribusi Sampel Berdasarkan 32 Label Resmi

Tepat 50 video per kelas untuk seluruh 32 kelas sumber (`WLBISINDO_LABELS`):

| Label ID | Gloss Resmi | Video | Label ID | Gloss Resmi | Video |
|:---:|---|:---:|:---:|---|:---:|
| 0 | AIR | 50 | 16 | PAGI | 50 |
| 1 | BELAJAR | 50 | 17 | RUMAH | 50 |
| 2 | CARI | 50 | 18 | TIDUR | 50 |
| 3 | HARI | 50 | 19 | SIANG | 50 |
| 4 | INGAT | 50 | 20 | HIJAU | 50 |
| 5 | LAGI | 50 | 21 | HITAM | 50 |
| 6 | LIHAT | 50 | 22 | KUNING | 50 |
| 7 | MAKAN | 50 | 23 | MERAH | 50 |
| 8 | MINUM | 50 | 24 | PUTIH | 50 |
| 9 | SAMA | 50 | 25 | TEMAN | 50 |
| 10 | TERIMA_KASIH | 50 | 26 | GURU | 50 |
| 11 | BUKU | 50 | 27 | AYAH | 50 |
| 12 | KAMU | 50 | 28 | IBU | 50 |
| 13 | KELUARGA | 50 | 29 | SORE | 50 |
| 14 | KITA | 50 | 30 | SUKA | 50 |
| 15 | DIMANA | 50 | 31 | MALAM | 50 |

---

## 5. Distribusi Split Signer-Dependent (SD) Bebas Kebocoran

Pembagian dataset mengikuti aturan deterministik per `(signer, label)` sesuai modul [`signbridge/data/video_metadata.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py):

| Split SD | Jumlah Sampel | Persentase | Cakupan Kelas | Status Leakage |
|---|:---:|:---:|:---:|:---:|
| **`train`** | 960 | 60,00% | 32 / 32 kelas (100%) | `0 Cross-Split Duplicates` |
| **`val`** | 180 | 11,25% | 32 / 32 kelas (100%) | `0 Cross-Split Duplicates` |
| **`test`** | 460 | 28,75% | 32 / 32 kelas (100%) | `0 Cross-Split Duplicates` |
| **Total** | **1.600** | **100,00%** | **32 / 32 kelas (100%)** | `PASS` |

---

## 6. Statistik Keypoint & Deteksi Fisik (86 Titik MediaPipe)

Pemeriksaan agregat terhadap $1.600 \text{ video} \times 64 \text{ frame} \times 86 \text{ titik} = 8.806.400$ titik koordinat 3D:

| Kelompok Landmark | Indeks Node | Titik per Frame | Rasio Deteksi Rata-rata | Karakteristik Kinematika |
|---|:---:|:---:|:---:|---|
| **Pose (Badan & Bahu)** | `[0:9]` | 9 | **100,00%** | Bahu, hidung, siku, pergelangan tangan terdeteksi stabil |
| **Face Landmarks** | `[51:86]` | 35 | **99,99%** | Kontur wajah, bibir, mata terdeteksi pada hampir seluruh frame |
| **Right Hand** | `[30:51]` | 21 | **92,23%** | Tangan dominan aktif pada mayoritas kata isyarat satu tangan |
| **Left Hand** | `[9:30]` | 21 | **18,68%** | Tangan non-dominan aktif saat kata isyarat dua tangan (mis. TEMAN) |
| **Agregat Keseluruhan** | `[0:86]` | 86 | **78,24%** | Refleksi alami gestur BISINDO tanpa pengisian landmark palsu |

### Validasi Rentang Koordinat Ternormalisasi:
- **Nilai NaN pada Output:** **0** (seluruh 1.600 file bebas NaN).
- **Nilai Inf pada Output:** **0** (seluruh 1.600 file bebas Inf).
- **Koordinat Minimum:** `-5.5749`
- **Koordinat Maksimum:** `4.1024`
- **Koordinat Rata-rata:** `0.1008`
- **Konsistensi Mask:** 100% koordinat dengan `valid_mask == False` bernilai tepat $(0.0, 0.0, 0.0)$.

---

## 7. Rincian Progres Ekstraksi per Batch (16 Batch @ 100 Video)

Catatan eksekusi resmi:

```text
=== MEMULAI EKSTRAKSI MASSAL 1600 VIDEO (16 BATCH @ 100) ===
Workers: 4 proses paralel | Output: data\keypoints\wl_bisindo
Batch 01/16 | Processed:  100/1600 | Success:  100 | Failed:  0 | Remaining: 1500 | Duration: 165.8s
Batch 02/16 | Processed:  200/1600 | Success:  200 | Failed:  0 | Remaining: 1400 | Duration: 181.1s
Batch 03/16 | Processed:  300/1600 | Success:  300 | Failed:  0 | Remaining: 1300 | Duration: 203.9s
Batch 04/16 | Processed:  400/1600 | Success:  400 | Failed:  0 | Remaining: 1200 | Duration: 208.2s
Batch 05/16 | Processed:  500/1600 | Success:  500 | Failed:  0 | Remaining: 1100 | Duration: 220.3s
Batch 06/16 | Processed:  600/1600 | Success:  600 | Failed:  0 | Remaining: 1000 | Duration: 197.0s
Batch 07/16 | Processed:  700/1600 | Success:  700 | Failed:  0 | Remaining:  900 | Duration: 191.9s
Batch 08/16 | Processed:  800/1600 | Success:  800 | Failed:  0 | Remaining:  800 | Duration: 186.5s
Batch 09/16 | Processed:  900/1600 | Success:  900 | Failed:  0 | Remaining:  700 | Duration: 182.0s
Batch 10/16 | Processed: 1000/1600 | Success: 1000 | Failed:  0 | Remaining:  600 | Duration: 165.1s
Batch 11/16 | Processed: 1100/1600 | Success: 1100 | Failed:  0 | Remaining:  500 | Duration: 150.5s
Batch 12/16 | Processed: 1200/1600 | Success: 1200 | Failed:  0 | Remaining:  400 | Duration: 147.1s
Batch 13/16 | Processed: 1300/1600 | Success: 1300 | Failed:  0 | Remaining:  300 | Duration: 151.9s
Batch 14/16 | Processed: 1400/1600 | Success: 1400 | Failed:  0 | Remaining:  200 | Duration: 158.9s
Batch 15/16 | Processed: 1500/1600 | Success: 1500 | Failed:  0 | Remaining:  100 | Duration: 138.9s
Batch 16/16 | Processed: 1600/1600 | Success: 1600 | Failed:  0 | Remaining:    0 | Duration: 158.1s
=== SELURUH 16 BATCH SELESAI DALAM 46.79 MENIT ===
```

---

## 8. Hasil Regression Test Pasca-Ekstraksi

Pengujian regresi dijalankan terhadap suite inti dataset dan keamanan pipeline:

| Nama Test Suite | Jumlah Test | Hasil | Status |
|---|:---:|:---:|:---:|
| [`tests/test_wl_bisindo_pipeline.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/tests/test_wl_bisindo_pipeline.py) | 17 | 17 PASS, 0 FAIL | **`PASS`** |
| [`tests/test_pipeline_safety_audit.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/tests/test_pipeline_safety_audit.py) | 18 | 18 PASS, 0 FAIL | **`PASS`** |
| [`tests/test_fsl_duplicate_leakage.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/tests/test_fsl_duplicate_leakage.py) | 4 | 4 PASS, 0 FAIL | **`PASS`** |
| **Total Core Regression** | **39** | **39 PASS, 0 FAIL (Exit Code 0)** | **`PASS`** |

Selain itu, modul loader [`SignDataset`](file:///c:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py) diuji langsung terhadap manifest baru [`data/manifest_wl_bisindo.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/manifest_wl_bisindo.csv) dan berhasil memuat seluruh partisi:
- `train`: 960 sampel (100% valid)
- `val`: 180 sampel (100% valid)
- `test`: 460 sampel (100% valid)

---

## 9. Integritas Repositori Git & Berkas Fisik

- **1.600 Video Sumber:** Seluruh berkas MP4 di [`data/raw/video/wl_bisindo/videos/`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/videos/) tidak mengalami perubahan konten atau hash.
- **Arsip Sumber:** `data/raw/video/wl_bisindo/archive.zip` (2.126.878.088 byte) 100% utuh.
- **10 File Pilot A.3.2:** Tetap aman di `data/keypoints/pilot_wlbisindo/`.
- **Git Branch:** `feature/dataset-acquisition`
- **Git HEAD:** `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` (terjaga utuh tanpa commit/push liar).

---

## 10. Lokasi Seluruh Artefak Luaran

1. **Direktori Keypoints NPZ (1.600 berkas):**  
   [`data/keypoints/wl_bisindo/`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/)
2. **Manifest Resmi (Contract 1):**  
   [`data/manifest_wl_bisindo.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/manifest_wl_bisindo.csv) (1.600 baris)
3. **Metadata Sumber Sidecar:**  
   [`data/manifest_wl_bisindo_source_metadata.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/manifest_wl_bisindo_source_metadata.csv) (1.600 baris)
4. **Checkpoint Persisten JSON:**  
   [`data/keypoints/wl_bisindo/checkpoint.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/checkpoint.json)
5. **Ringkasan Audit Statistik Ekstraksi:**  
   [`data/keypoints/wl_bisindo/extraction_audit_summary.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/extraction_audit_summary.json)
6. **Script Ekstraksi Massal Reusable:**  
   [`scripts/mass_extract_wlbisindo.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/scripts/mass_extract_wlbisindo.py)

---

## 11. Risiko & Keterbatasan yang Masih Ada

1. **Pengujian Paritas JS Live:** Paritas numerik dengan `web/js/features.js` telah terbukti secara analitis dan matematis identik, namun eksekusi live via runtime JS engine masih berstatus `NOT TESTED` karena Node.js belum terpasang di host Windows ini.
2. **Keterbatasan Ekstraksi Fitur RGB (VideoMAE):** Fitur visual RGB belum diekstrak pada tahap ini (sesuai ruang lingkup keypoint saja; kolom `rgb_path` dikosongkan secara sah pada manifest).
3. **Kepatuhan Larangan Model Training:** Sesuai instruksi mutlak, **tidak ada training model** yang dijalankan.

---

## 12. Kesimpulan Kesiapan

Tahap A.3.3 telah **selesai 100% dengan sempurna**. Dataset representasi keypoint WL-BISINDO telah siap digunakan untuk tahap pretraining representasi maupun fine-tuning kelas overlap SignBridge.

