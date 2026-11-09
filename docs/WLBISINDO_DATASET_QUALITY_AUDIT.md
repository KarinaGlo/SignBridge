# LAPORAN AUDIT KUALITAS MENYELURUH DATASET WL-BISINDO (TAHAP A.3.4)

| Metadata Dokumen | Nilai |
|---|---|
| **Tanggal Audit** | 2026-11-08 |
| **Proyek** | SignBridge ASEAN (BISINDO ↔ FSL) |
| **Tahap** | TAHAP A.3.4 — Comprehensive Dataset Quality Audit WL-BISINDO |
| **Branch Git** | `feature/dataset-acquisition` |
| **Git HEAD** | `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` |
| **Auditor** | Senior ML Engineer, Computer Vision Engineer & Dataset Quality Auditor |
| **Status Kesiapan** | **READY FOR BASELINE TRAINING** |

---

## 1. RINGKASAN EKSEKUTIF

Audit kualitas menyeluruh (Comprehensive Dataset Quality Audit) telah dilakukan secara independen terhadap seluruh **1.600 berkas keypoint `.npz`** dataset WL-BISINDO yang diekstraksi pada Tahap A.3.3. Audit mencakup verifikasi integritas fisik, struktur tensor, keberadaan valid mask, distribusi koordinat spasial, stabilitas normalisasi geometris, dinamika temporal, keaslian konten (deduplikasi), serta kesiapan data loader `SignDataset` lintas split.

### Ringkasan Statistik Kunci

| Metrik Audit | Nilai Aktual | Keterangan |
|---|---:|---|
| **Total Sampel Dievaluasi** | **1.600** / 1.600 | 100% sampel berhasil diaudit tanpa error |
| **Total Kelas (Glosses)** | **32** kelas | 100% kelas WL-BISINDO tercakup |
| **Total Signer** | **5** signer | `SIGNER0` (120), `SIGNER1` (420), `SIGNER2` (420), `SIGNER3` (320), `SIGNER4` (320) |
| **Struktur Tensor** | `[64, 86, 3]` float32 | Sesuai Kontrak 1 & Kontrak 3 SignBridge |
| **Valid Mask** | `[64, 86]` bool | Bit-mask temporal-spasial valid |
| **Deteksi Pose (9 landmark)** | **100,00%** | Sempurna di seluruh frame aktif |
| **Deteksi Wajah (35 landmark)** | **99,99%** | Nyaris sempurna di seluruh frame aktif |
| **Deteksi Tangan Kanan (21 landmark)** | **92,23%** | Tangan dominan aktif di seluruh signer |
| **Deteksi Tangan Kiri (21 landmark)** | **18,68%** | Asimetris alami sesuai tipologi leksikal BISINDO |
| **Rata-rata Validitas Total** | **78,24%** | 0% NaN, 0% Inf, 100% finite coordinates |
| **Kategori HIGH** | **1.546 sampel (96,62%)** | Validitas tinggi, temporal stabil, gesture lengkap |
| **Kategori MEDIUM** | **51 sampel (3,19%)** | Validitas memadai, hand presence cukup |
| **Kategori LOW** | **3 sampel (0,19%)** | Deteksi tangan singkat namun bebas NaN/Inf |
| **Kategori INVALID** | **0 sampel (0,00%)** | **Nol sampel rusak/cacat** |
| **Duplikasi File/Video/Fitur** | **0 duplikat** | Seluruh 1.600 sampel memiliki SHA-256 unik |
| **Kebocoran Lintas Split (Leakage)** | **0 kebocoran** | Split SD (960 train / 180 val / 460 test) steril |
| **SignDataset End-to-End Loading** | **100% Sukses** | 32/32 kelas terwakili pada setiap split |

---

## 2. METODOLOGI & KRITERIA KUALITAS (QUALITY SCORING)

Setiap sampel dievaluasi berdasarkan kriteria kuantitatif berikut:

```
[64 frames, 86 landmarks, 3 coordinates (x,y,z)]
 ├── Pose:       Indices [0:9]   (9 nodes)
 ├── Left Hand:  Indices [9:30]  (21 nodes)
 ├── Right Hand: Indices [30:51] (21 nodes)
 └── Face:       Indices [51:86] (35 nodes)
```

### Ambang Batas Klasifikasi Kualitas

1. **`INVALID` (Reject)**:
   - Terdapat nilai `NaN` atau `Inf`.
   - Dimensi tensor tidak tepat `[64, 86, 3]` atau valid mask bukan `[64, 86]`.
   - Tidak ada tangan terdeteksi sama sekali sepanjang klip (`frames_either_hand == 0`).
   - Tingkat validitas total < 20%.
   - *Hasil aktual*: **0 sampel (0,00%)**.

2. **`HIGH` (Optimal for Training)**:
   - Tingkat validitas total $\ge 70\%$.
   - Tangan aktif terdeteksi $\ge 40$ frame (dari 64 frame total, $\ge 62,5\%$).
   - Tidak mengalami lonjakan temporal ekstrem (`max_interframe_jump < 4.0`).
   - Tidak mengalami static freeze temporal (`is_static_frozen == False`).
   - Frame kosong $\le 5$ frame.
   - *Hasil aktual*: **1.546 sampel (96,62%)**.

3. **`MEDIUM` (Acceptable for Training)**:
   - Tingkat validitas total $\ge 45\%$.
   - Tangan aktif terdeteksi $\ge 20$ frame.
   - Bebas dari NaN/Inf dan deformasi geometris.
   - *Hasil aktual*: **51 sampel (3,19%)**.

4. **`LOW` (Marginal Quality)**:
   - Sampel valid secara struktural (bebas NaN/Inf), namun tangan aktif terdeteksi < 20 frame.
   - *Hasil aktual*: **3 sampel (0,19%)**.
   - Catatan: Sesuai komitmen, **ketiga sampel ini tidak dihapus**, melainkan ditandai untuk analisis sensitivitas model.

---

## 3. INVESTIGASI MENDALAM ASIMETRI TANGAN (HAND DETECTION ASYMMETRY)

Salah satu temuan paling menonjol pada pra-audit adalah rasio deteksi tangan:
- **Tangan Kanan**: **92,23%** (rata-rata 59,02 frame aktif per sampel).
- **Tangan Kiri**: **18,68%** (rata-rata 11,95 frame aktif per sampel).

### Analisis Hipotesis: Kesalahan Pipeline vs Sifat Leksikal Alami

Untuk membuktikan apakah asimetri ini disebabkan oleh bug/kegagalan deteksi MediaPipe atau merupakan sifat linguistik alami dari kosakata WL-BISINDO, dilakukan audit per-kelas terhadap seluruh 32 kelas.

#### Tabel Karakterisasi Gestur per Kelas (32 Kelas)

| Label | Gloss | Tipe Gestur | Validitas Tangan Kanan (%) | Validitas Tangan Kiri (%) | Frame Kedua Tangan Aktif (rerata/64) |
|---:|---|---|---:|---:|---:|
| 0 | AIR | ONE_HANDED_RIGHT | 94,06% | 7,00% | 3,60 |
| 1 | BELAJAR | ONE_HANDED_RIGHT | 91,63% | 0,00% | 0,00 |
| 2 | CARI | ONE_HANDED_RIGHT | 94,31% | 19,81% | 11,80 |
| 3 | HARI | ONE_HANDED_RIGHT | 85,84% | 19,50% | 9,72 |
| 4 | INGAT | ONE_HANDED_RIGHT | 95,53% | 13,56% | 7,50 |
| 5 | LAGI | ONE_HANDED_RIGHT | 96,00% | 0,00% | 0,00 |
| 6 | MAAF | ONE_HANDED_RIGHT | 96,63% | 1,16% | 0,70 |
| 7 | MAKAN | ONE_HANDED_RIGHT | 88,88% | 13,38% | 6,88 |
| **8** | **MOTOR** | **TWO_HANDED_SYMMETRIC** | **93,38%** | **87,34%** | **52,76** |
| 9 | SAYA | ONE_HANDED_RIGHT | 97,97% | 20,00% | 11,94 |
| 10 | TERIMA_KASIH | ONE_HANDED_RIGHT | 98,16% | 20,00% | 11,86 |
| 11 | TULI | ONE_HANDED_RIGHT | 96,28% | 19,56% | 10,96 |
| 12 | APA | ONE_HANDED_RIGHT | 77,25% | 19,03% | 11,78 |
| 13 | SIAPA | ONE_HANDED_RIGHT | 93,13% | 20,00% | 11,12 |
| 14 | KAPAN | ONE_HANDED_RIGHT | 94,88% | 20,00% | 11,74 |
| 15 | DIMANA | ONE_HANDED_RIGHT | 87,75% | 20,00% | 11,90 |
| 16 | MENGAPA | ONE_HANDED_RIGHT | 92,31% | 20,00% | 10,56 |
| **17** | **BAGAIMANA** | **TWO_HANDED_SYMMETRIC** | **83,03%** | **82,16%** | **46,08** |
| 18 | MERAH | ONE_HANDED_RIGHT | 95,56% | 20,00% | 11,42 |
| 19 | KUNING | ONE_HANDED_RIGHT | 92,06% | 0,00% | 0,00 |
| 20 | HIJAU | ONE_HANDED_RIGHT | 94,53% | 0,00% | 0,00 |
| 21 | HITAM | ONE_HANDED_RIGHT | 92,78% | 0,00% | 0,00 |
| 22 | DENGAR | ONE_HANDED_RIGHT | 94,03% | 0,00% | 0,00 |
| 23 | BERANGKAT | ONE_HANDED_RIGHT | 95,50% | 0,00% | 0,00 |
| 24 | DATANG | ONE_HANDED_RIGHT | 94,63% | 0,03% | 0,02 |
| **25** | **TEMAN** | **TWO_HANDED_SYMMETRIC** | **91,56%** | **88,91%** | **52,88** |
| 26 | KELUARGA | ONE_HANDED_RIGHT | 93,06% | 0,03% | 0,02 |
| **27** | **RUMAH** | **TWO_HANDED_SYMMETRIC** | **76,16%** | **85,47%** | **44,50** |
| 28 | PAGI | ONE_HANDED_RIGHT | 94,06% | 0,16% | 0,04 |
| 29 | SIANG | ONE_HANDED_RIGHT | 91,59% | 0,00% | 0,00 |
| 30 | SORE | ONE_HANDED_RIGHT | 94,25% | 0,50% | 0,28 |
| 31 | MALAM | ONE_HANDED_RIGHT | 94,44% | 0,13% | 0,08 |

### Kesimpulan Investigasi Asimetri

1. **Bukan Kegagalan MediaPipe**: MediaPipe Holistic mampu mendeteksi tangan kiri hingga **87–89%** pada isyarat yang memang dua tangan (*two-handed signs*), seperti `MOTOR` (label 8), `BAGAIMANA` (label 17), `TEMAN` (label 25), dan `RUMAH` (label 27).
2. **Karakteristik Linguistik Kosakata**: Sebanyak **28 dari 32 kelas (87,5%)** dalam dataset WL-BISINDO merupakan isyarat satu tangan dominan (*one-handed dominant signs*). Kelima signer yang direkam dalam dataset ini menggunakan tangan kanan sebagai tangan dominan, sementara tangan kiri berada di bawah area pandang kamera atau pasif di pangkuan.
3. **Valid Mask Berfungsi Sempurna**: Ketika tangan kiri pasif/tidak terlihat, pipeline secara konsisten mengisi koordinat tangan kiri dengan `(0.0, 0.0, 0.0)` dan menetapkan `valid_mask = False`. Model Spatio-Temporal Graph Convolutional Network (GCN) dan Transformer yang menggunakan *masked attention* atau *keypoint mask* akan memproses kondisi ini secara alami tanpa bias noise.

---

## 4. VALIDASI GEOMETRIS & NORMALISASI

Kontrak 3 SignBridge mensyaratkan:
- Titik tengah bahu: $\mathbf{c} = 0.5 \times (\mathbf{bahu}_L + \mathbf{bahu}_R) \approx (0, 0, 0)$
- Jarak antar bahu: $d = \|\mathbf{bahu}_L - \mathbf{bahu}_R\| \approx 1.0$

### Hasil Pengujian Geometris Seluruh 1.600 Sampel

| Parameter Geometris | Nilai Maksimum Deviasi | Ambang Toleransi | Status |
|---|---:|---:|---|
| **Deviasi Titik Tengah Bahu terhadap (0,0,0)** | **0,000000** | $< 10^{-5}$ | **LULUS MUTLAK** |
| **Deviasi Skala Bahu terhadap 1.0** | **0,000000** | $< 10^{-5}$ | **LULUS MUTLAK** |
| **Jumlah Sampel Tervalidasi Sempurna** | **1.600 / 1.600** | 1.600 | **100,00%** |

### Batas Koordinat Spasial Global (Valid Keypoints)

| Sumbu Koordinat | Nilai Minimum | Nilai Maksimum | Rerata ($\mu$) | Standar Deviasi ($\sigma$) |
|---|---:|---:|---:|---:|
| **X (Horizontal)** | -1,8884 | +1,7811 | -0,0312 | 0,3842 |
| **Y (Vertikal)** | -3,1915 | +4,1024 | +0,2481 | 0,5915 |
| **Z (Kedalaman/Depth)** | -5,5749 | +2,7406 | +0,0854 | 0,4210 |

Semua nilai berada dalam rentang normalisasi tubuh manusia standar dan terbebas dari nilai pencilan numerik tak hingga.

---

## 5. DINAMIKA TEMPORAL & DETEKSI ANOMALI

| Metrik Dinamika | Nilai Teramati | Evaluasi |
|---|---:|---|
| **Rerata Lonjakan Antar-Frame ($\Delta t$)** | **0,0555** unit | Sangat mulus (gerakan alami) |
| **Maksimum Lonjakan Antar-Frame** | **3,5735** unit | Wajar untuk transisi gestur cepat (flick) |
| **Sampel Beku (Static Frozen)** | **0 sampel** | Tidak ditemukan video freeze atau frame duplikasi konstan |
| **Rerata Durasi Frame Mentah** | **68,4 frame** | Resampling ke $T=64$ mempertahankan fidelity temporal |

---

## 6. AUDIT DUPLIKASI DATA & KEBOCORAN SPLIT

Audit dilakukan menggunakan tiga lapisan hash independen:
1. **Raw Video SHA-256**: Hash berkas MP4 fisik.
2. **Keypoint `.npz` SHA-256**: Hash berkas biner ekstraksi.
3. **Feature Semantic Hash**: Hash representasi fitur koordinat yang dibulatkan (desimal 3).

### Hasil Audit Duplikasi

| Uji Integritas | Duplikat Ditemukan | Status |
|---|---:|---|
| **Duplikasi Video Mentah** | **0** | Seluruh 1.600 video berbeda fisik |
| **Duplikasi Berkas Keypoint** | **0** | Seluruh 1.600 berkas `.npz` unik |
| **Duplikasi Vektor Fitur Semantik** | **0** | Tidak ada rekaman kembar atau klon |
| **Kebocoran Lintas Split (Cross-Split Leakage)** | **0** | Train, Val, dan Test 100% terisolasi |

---

## 7. AUDIT DISTRIBUSI SPLIT & KESIAPAN SignDataset

Dataset menggunakan split Signer-Dependent (SD) resmi:

| Split | Jumlah Sampel | Persentase | Representasi Kelas |
|---|---:|---:|---:|
| **`train`** | 960 sampel | 60,00% | **32 / 32 kelas (100%)** |
| **`val`** | 180 sampel | 11,25% | **32 / 32 kelas (100%)** |
| **`test`** | 460 sampel | 28,75% | **32 / 32 kelas (100%)** |
| **Total** | **1.600 sampel** | **100,00%** | **32 / 32 kelas (100%)** |

### Verifikasi SignDataset

- Seluruh 1.600 sampel berhasil di-load melalui `SignDataset` pada `signbridge/data/dataset.py`.
- **Zero Synthetic Fallback**: Dataset memuat berkas fisik riil tanpa membangkitkan data sintetis.
- Valid mask dimuat dalam shape `[64, 86]` bertipe boolean.
- Tidak ditemukan `NaN` atau `Inf` pada tensor output `pose`.
- 39/39 regression tests lulus (`test_wl_bisindo_pipeline.py`, `test_fsl_duplicate_leakage.py`, `test_pipeline_safety_audit.py`).

---

## 8. ARTEFAK & BERKAS YANG DIHASILKAN

### Berkas Data Kualitas (`data/keypoints/wl_bisindo/`)
1. [`quality_audit_summary.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/quality_audit_summary.json): Ringkasan metrik kualitas dan status kesiapan.
2. [`quality_audit_per_sample.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/quality_audit_per_sample.csv): Metrik mendalam per sampel (1.600 baris).
3. [`quality_audit_per_class.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/quality_audit_per_class.csv): Agregasi metrik per kelas dan tipe gestur (32 baris).
4. [`quality_audit_per_signer.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/quality_audit_per_signer.csv): Agregasi per signer (5 baris).
5. [`duplicate_audit.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/duplicate_audit.csv): Log verifikasi deduplikasi dan integritas hash.
6. [`quality_categories.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/keypoints/wl_bisindo/quality_categories.csv): Label kualitas (HIGH/MEDIUM/LOW/INVALID) per sampel.

### Visualisasi & Figur (`docs/figures/wlbisindo_quality_audit/`)
1. [`dataset_validity_distribution.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/dataset_validity_distribution.png): Histogram validitas landmark dan deteksi tangan.
2. [`validity_by_signer.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/validity_by_signer.png): Diagram batang perbandingan validitas tiap komponen landmark per signer.
3. [`validity_by_class.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/validity_by_class.png): Perbandingan deteksi tangan kiri vs kanan di 32 kelas dengan highlight kelas 2 tangan.
4. [`left_vs_right_hand.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/left_vs_right_hand.png): Scatter plot asimetri tangan yang membuktikan dua klaster linguistik alami.
5. [`quality_category_distribution.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/quality_category_distribution.png): Diagram donat proporsi kategori kualitas dan komposisi per signer.
6. [`split_distribution.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/split_distribution.png): Distribusi sampel train, val, dan test.
7. [`skeleton_high_sample.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/skeleton_high_sample.png): Visualisasi rangka 2D sampel HIGH quality (`AIR`).
8. [`skeleton_two_handed.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/skeleton_two_handed.png): Visualisasi rangka 2D sampel 2 tangan simetris (`TEMAN`).
9. [`skeleton_one_handed.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/skeleton_one_handed.png): Visualisasi rangka 2D sampel 1 tangan dominan (`BELAJAR`).
10. [`skeleton_medium_sample.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/skeleton_medium_sample.png): Visualisasi rangka sampel MEDIUM quality.
11. [`skeleton_low_sample.png`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/figures/wlbisindo_quality_audit/skeleton_low_sample.png): Visualisasi rangka sampel LOW quality.

---

## 9. KESIMPULAN AKHIR & REKOMENDASI

### Status Kesiapan: **`READY FOR BASELINE TRAINING`**

Dataset keypoint WL-BISINDO telah memenuhi seluruh standar integritas kualitas data untuk pelatihan model baseline (M0 Video Representation Pretraining):
1. **0 Sampel Cacat (INVALID = 0)**.
2. **99,81% Sampel Berkualitas Baik** (96,62% HIGH + 3,19% MEDIUM).
3. **Normalisasi Geometris 100% Presisi**.
4. **Isolasi Lintas Split Terjamin 100%**.

### Rekomendasi untuk Tahap Pelatihan (M0):
- **Gunakan Masked Loss / Attention Mask**: Selalu manfaatkan `valid_mask` agar model tidak memaksakan prediksi koordinat pada tangan kiri yang pasif pada kelas satu tangan.
- **Jangan Buang Sampel LOW**: Tiga sampel berkategori LOW (`MAKAN` sample 5, `APA` sample 14, `APA` sample 4) tetap dipertahankan untuk menguji ketahanan model terhadap isyarat berdurasi singkat.
- **Pertahankan Protokol SD untuk Baseline**: Protokol Signer-Dependent mencakup seluruh 32 kelas di semua split. Untuk evaluasi Signer-Independent (SI/LOSO), hindari penggunaan `SIGNER0` sebagai *held-out test signer* tunggal karena hanya memiliki 12 kelas.

