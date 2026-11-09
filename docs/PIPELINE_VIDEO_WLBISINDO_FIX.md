# LAPORAN PERBAIKAN PIPELINE VIDEO WL-BISINDO & FSL-105 (TAHAP A.2.2)

**Proyek:** SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Workspace Aktif:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif:** `feature/dataset-acquisition` (`HEAD: b38b4da`)  
**Tanggal:** 7 November 2026  
**Peran:** Senior Machine Learning Engineer, Computer Vision Engineer, dan Dataset Pipeline Auditor  

---

## 1. Masalah Awal

Berdasarkan audit fisik Tahap A.2.1 (`docs/DATASET_REAUDIT_AFTER_ACQUISITION.md`), dataset video BISINDO **WL-BISINDO** telah tersedia di workspace dalam bentuk arsip [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip) (`2.126.878.088` byte, SHA-256 `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095`), berisi `1.600` video `.mp4` utuh (32 kelas $\times$ 50 klip, 5 signer, CRC-32 100% OK, 0 duplikat). Namun pipeline video SignBridge mengalami 4 kendala utama:

1. **Bug Regex Signer:** `extract_signer_id()` pada `scripts/extract_keypoints.py` gagal membaca signer dari nama berkas `signer0_label0_sample1.mp4` dan mengembalikan `'unannotated'`.
2. **Ketiadaan Dukungan Label Numerik WL-BISINDO:** `resolve_video_gloss_and_label()` hanya mengasumsikan folder bersarang dengan nama gloss ruang kelas (`concepts.csv`). Berkas flat `signer<S>_label<L>_sample<K>.mp4` langsung melempar `ValueError`.
3. **Pencampuran / Pemaksaan Label Space:** Kosakata resmi 32 kelas WL-BISINDO berbeda dengan 32 konsep ruang kelas SignBridge (`data/bridge/concepts.csv`); hanya 10 gloss yang beririsan langsung. Memaksa label WL-BISINDO ke dalam `concepts.csv` akan merusak integritas semantik dataset asli.
4. **Kebocoran Duplikat Konten FSL-105 Antar-Split:** Pada FSL-105 (`2.130` klip `.MOV`, 105 kelas), terdapat 4 pasang klip dengan SHA-256 identik lintas kelas bawaan Mendeley. Dua pasang di antaranya bocor antara `train.csv` dan `test.csv` resmi.

---

## 2. Penyebab Bug Regex Signer & Solusi

### 2.1 Analisis Bug
Pola regex lama pada `scripts/extract_keypoints.py`:
```python
re.search(r"\b(s\d{1,3}|signer[_-]?\d{1,3})\b", token, flags=re.IGNORECASE)
```
Karakter batas kata (`\b`) dalam regex Python mendefinisikan transisi antara karakter kata (`\w`: huruf, angka, underscore) dan non-kata (`\W`). Pada nama berkas `signer0_label0_sample1`:
- Karakter setelah `0` adalah underscore (`_`).
- Karena angka `0` adalah `\w` dan `_` juga adalah `\w`, **tidak ada transisi batas kata `\b`**.
- Akibatnya, `\b` di akhir pola gagal cocok, dan fungsi mengembalikan `'unannotated'`.

### 2.2 Solusi Perbaikan
Pola diganti menggunakan *lookaround assertions* eksplisit pada [`signbridge/data/video_metadata.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py):
```python
_SIGNER_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(signer[_-]?\d{1,3}|s\d{1,3})(?![0-9])",
    flags=re.IGNORECASE,
)
```
- `(?<![A-Za-z0-9])`: Token tidak didahului oleh karakter alfanumerik.
- `(?![0-9])`: Angka signer tidak langsung diikuti oleh angka lain. Karakter `_`, `-`, titik, spasi, atau batas string menjadi pemisah yang valid.
- Hasil pengujian:
  - `signer0_label0_sample1.mp4` $\rightarrow$ `SIGNER0`
  - `signer1_label12_sample15.mp4` $\rightarrow$ `SIGNER1`
  - `signer2_label31_sample10.mp4` $\rightarrow$ `SIGNER2`
  - `signer3_label5_sample1.mp4` $\rightarrow$ `SIGNER3`
  - `signer4_label20_sample10.mp4` $\rightarrow$ `SIGNER4`
  - `S01_video.mp4` $\rightarrow$ `S01`
  - `s1_video.mp4` $\rightarrow$ `S1`
  - Token tanpa penanda signer eksplisit (mis. `clips/0/0.MOV`, `random.mp4`) tetap mengembalikan `'unannotated'` secara jujur (tanpa mengarang signer palsu dari urutan atau modulo indeks).

---

## 3. Perubahan Parsing Label Numerik WL-BISINDO

Dibuat parser pola berkas `signer<ID>_label<ID>_sample<ID>.<ext>` melalui fungsi `parse_wlbisindo_filename()` dan `is_wlbisindo_filename()` di [`signbridge/data/video_metadata.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py):

- **Ekstrak Komponen:**
  - `signer_index`: integer $\ge 0$ (mis. `0` $\rightarrow$ `signer_id = "SIGNER0"`).
  - `source_label_id`: integer pada rentang resmi `0..31`.
  - `source_gloss`: gloss sumber resmi dari kamus `WLBISINDO_LABELS`.
  - `sample_id`: nomor sampel klip (mis. `1`).
  - `source`: `"wl_bisindo"`.
- **Validasi Ketat:**
  - Label di luar rentang `0..31` (mis. label `-1`, `32`, `100`) langsung melempar `ValueError` dengan pesan yang jelas.
  - Nama berkas dengan format menyimpang atau ekstensi di luar video (`.mp4`, `.webm`, `.mov`) langsung ditolak.
  - Nama berkas ganda (*case-insensitive*) dicegah agar tidak terjadi overwrite diam-diam.

---

## 4. Pemisahan Label Space WL-BISINDO dan `concepts.csv`

Label space **WL-BISINDO** didefinisikan secara independen di `WLBISINDO_LABELS` (32 kelas):

```python
WLBISINDO_LABELS = {
    0: "AIR", 1: "BELAJAR", 2: "CARI", 3: "HARI", 4: "INGAT",
    5: "LAGI", 6: "MAAF", 7: "MAKAN", 8: "MOTOR", 9: "SAYA",
    10: "TERIMA_KASIH", 11: "TULI", 12: "APA", 13: "SIAPA", 14: "KAPAN",
    15: "DIMANA", 16: "MENGAPA", 17: "BAGAIMANA", 18: "MERAH", 19: "KUNING",
    20: "HIJAU", 21: "HITAM", 22: "DENGAR", 23: "BERANGKAT", 24: "DATANG",
    25: "TEMAN", 26: "KELUARGA", 27: "RUMAH", 28: "PAGI", 29: "SIANG",
    30: "SORE", 31: "MALAM"
}
```

### Isolasi dan Perlindungan Semantik
1. **Tidak Memaksa Pemetaan ke `concepts.csv`:**
   - Hanya 10 gloss yang beririsan langsung (`BELAJAR`, `MAAF`, `SAYA`, `TERIMA_KASIH`, `APA`, `SIAPA`, `KAPAN`, `DIMANA`, `BAGAIMANA`, `TEMAN`).
   - 22 gloss lainnya tetap mempertahankan identitas aslinya (mis. `AIR` = 0, `MALAM` = 31).
2. **`data/bridge/concepts.csv` Tidak Disentuh:**
   - File `concepts.csv` tetap utuh 100% dengan SHA-256 aslinya (`d3d0907642b8039411058d1ab378d15d6ab9ed929f743838a190bd68ffce9005`).
3. **Pencegahan Pencampuran Dataset:**
   - Pemanggilan `resolve_video_gloss_and_label(..., source="wl_bisindo")` dengan `labels.csv` eksternal (mis. FSL-105) ditolak keras dengan `ValueError`.
   - Pemanggilan `source="bisindo"` (konsep kelas SignBridge) tetap mewajibkan folder berlabel `BISINDO_32_GLOSSES` dan menolak berkas flat WL-BISINDO.
4. **Lisensi Terverifikasi:**
   - Lisensi WL-BISINDO dicatat secara konsisten sebagai **`CC BY-NC 4.0`** (*Attribution-NonCommercial 4.0 International*).

---

## 5. Penanganan Duplikasi dan Pencegahan Kebocoran FSL-105

### 5.1 Empat Pasang Duplikat SHA-256 Teridentifikasi
Audit fisik mengonfirmasi 4 pasang klip dengan SHA-256 identik pada FSL-105:
1. `clips/23/6.MOV` (`train`) $\equiv$ `clips/26/7.MOV` (`test`) — Hash: `2894410d8559ff07b0a2e17cf6d6189ce3faf2ed867e955825441e8ff8108845` (**BOCOR ANTAR-SPLIT!**)
2. `clips/23/8.MOV` (`test`) $\equiv$ `clips/26/9.MOV` (`train`) — Hash: `c329a443c221550baa104bfb20ca93fc1f13c2b191467a96f4c59b90137b8ca5` (**BOCOR ANTAR-SPLIT!**)
3. `clips/57/9.MOV` (`train`) $\equiv$ `clips/60/9.MOV` (`train`) — Hash: `8349f35b80868cafa419d753f28f87a137d975d7116a5889ff63b9dd16de8b87` (*Sesama train*)
4. `clips/58/6.MOV` (`train`) $\equiv$ `clips/61/6.MOV` (`train`) — Hash: `755a474858b2fc54641336d60c69a8026b7e33d65a4f2c86cae8a424d7865c17` (*Sesama train*)

### 5.2 Kebijakan Karantina Eksplisit (Bukan Keputusan Sepihak)
- **Sumber Asli Tidak Diubah:** Berkas `train.csv`, `test.csv`, `labels.csv`, maupun file video fisik di `clips/` **tidak diubah, tidak dipindahkan, dan tidak dihapus**.
- **Klasifikasi Status Duplikasi:**
  - `UNIQUE`: Konten unik, tidak memiliki duplikat.
  - `WITHIN_SPLIT_DUPLICATE`: Duplikat berada di split yang sama. Tetap `INCLUDED`, namun ditandai pada laporan.
  - `CROSS_SPLIT_DUPLICATE`: Duplikat melintasi split resmi (`train` vs `test`). Seluruh klip dalam grup ini diberi status `QUARANTINED_CROSS_SPLIT_DUPLICATE`.
- **Eksklusi dari Evaluasi Eksperimen:**
  - Manifest eksperimen yang digunakan untuk evaluasi model secara ketat hanya menyertakan klip berstatus `INCLUDED`.
  - Fungsi `assert_no_sha256_split_leakage()` menjamin secara matematis bahwa tidak ada satu pun hash SHA-256 yang muncul di lebih dari satu split.
  - Laporan duplikat lengkap dapat diekspor secara otomatis melalui `write_duplicate_report()`.

---

## 6. Strategi Split WL-BISINDO: SD vs SI

Dataset WL-BISINDO memiliki 5 signer dengan distribusi kelas yang tidak simetris:
- `SIGNER0`: **Hanya mencakup 12 kelas** (`label0` sampai `label11`, 10 video/kelas = 120 video).
- `SIGNER1`: **Mencakup 32 kelas lengkap** (420 video).
- `SIGNER2`: **Mencakup 32 kelas lengkap** (420 video).
- `SIGNER3`: **Mencakup 32 kelas lengkap** (320 video).
- `SIGNER4`: **Mencakup 32 kelas lengkap** (320 video).

### 6.1 Protokol Signer-Dependent (SD)
- Diimplementasikan oleh `assign_wlbisindo_sd_splits()`:
  - Setiap kelompok `(signer, label)` dibagi secara deterministik berdasarkan `sample_id` terurut dengan rasio 60% train, 10% val, 30% test (default).
  - Menghasilkan 100% cakupan 32 kelas pada seluruh split (`train`, `val`, `test`).
  - Kelima signer muncul di seluruh split secara seimbang.

### 6.2 Protokol Signer-Independent (SI / LOSO)
- Diimplementasikan oleh `build_wlbisindo_si_split()` dan divalidasi di `SignDataset`:
  - Seluruh klip dari `test_signers` dialokasikan ke split test, `val_signers` ke split val, dan signer lainnya ke train.
  - **Larangan Signer0 sebagai Test Tunggal:** Karena `signer0` hanya mencakup label 0..11, menjadikannya satu-satunya test signer akan menyebabkan 20 kelas hilang dari evaluasi test!
  - `validate_split_class_coverage()` memeriksa kelengkapan kelas pada setiap split. Jika ada kelas yang hilang, sistem melempar `ValueError` informatif dan menolak klaim evaluasi SI penuh (kecuali parameter `allow_partial_class_coverage=True` diset secara eksplisit dan didokumentasikan).
  - Pemilihan `SIGNER1`, `SIGNER2`, `SIGNER3`, atau `SIGNER4` sebagai held-out test signer menghasilkan cakupan 32 kelas lengkap yang valid.

---

## 7. Unit Test dan Pengujian yang Ditambahkan

Dua berkas unit test baru dibuat untuk memvalidasi seluruh perbaikan secara independen:

1. **[`tests/test_wl_bisindo_pipeline.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_wl_bisindo_pipeline.py) (17 Test):**
   - `test_wlbisindo_signers_parsed`: Parsing `signer0`..`signer4` dari nama berkas flat.
   - `test_legacy_short_signer_formats`: Dukungan format lama `S01`, `s1`, `signer-02`.
   - `test_old_regex_bug_reproduced`: Pembuktian bug regex lama dengan `\b`.
   - `test_unannotated_is_not_invented`: Memastikan signer tidak dikarang sembarangan.
   - `test_label_space_is_official_and_separate`: Validasi 32 label resmi WL-BISINDO dan lisensi `CC BY-NC 4.0`.
   - `test_parse_all_labels_and_signers`: Parsing seluruh kombinasi 32 label dan 5 signer.
   - `test_resolve_video_gloss_and_label_wl_source`: Resolusi label untuk source `wl_bisindo`.
   - `test_out_of_range_and_invalid_names_rejected`: Penolakan label $<0$, $\ge 32$, dan nama tidak valid.
   - `test_duplicate_names_rejected`: Penolakan tabrakan nama berkas ganda.
   - `test_concepts_csv_untouched_by_label_space`: Verifikasi `concepts.csv` tidak berubah.
   - `test_signer_coverage`: Verifikasi signer0 (12 kelas) vs signer1-4 (32 kelas).
   - `test_si_signer0_only_test_rejected`: Penolakan klaim SI valid jika signer0 menjadi test tunggal.
   - `test_si_valid_split`: Pembagian SI valid dengan signer yang memiliki 32 kelas lengkap.
   - `test_sd_split_deterministic_and_complete`: Pembagian SD deterministik 60/10/30 dengan 32 kelas lengkap.
   - `test_real_archive_metadata_without_extraction`: Pemeriksaan central directory ZIP asli tanpa mengekstrak.
   - `test_signdataset_si_rejects_signer0_test`: Pengujian integrasi `SignDataset` pada protokol SI dengan signer tidak lengkap.
   - `test_signdataset_si_accepts_full_coverage_signer`: Pengujian integrasi `SignDataset` pada protokol SI dengan signer lengkap.

2. **[`tests/test_fsl_duplicate_leakage.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_fsl_duplicate_leakage.py) (4 Test):**
   - `test_official_fsl_csvs_unmodified`: Memastikan hash SHA-256 `train.csv`, `test.csv`, `labels.csv` FSL-105 asli 100% utuh.
   - `test_fsl_and_wlbisindo_label_spaces_isolated`: Isolasi ruang label FSL-105 vs WL-BISINDO vs concepts.csv.
   - `test_classify_sha256_duplicates_synthetic`: Uji klasifikasi duplikat dan karantina anti-kebocoran.
   - `test_real_fsl105_duplicates_and_quarantine`: Verifikasi fisik 4 pasang duplikat pada klip FSL-105 asli di disk dan karantina 4 klip lintas split.

---

## 8. Hasil Eksekusi Test Aktual

Semua pengujian unit test dan regression test dijalankan langsung pada environment workspace:

| Berkas Pengujian | Jenis Pengujian | Jumlah Test | Hasil | Durasi | Keterangan |
|---|---|---:|:---:|---:|---|
| [`tests/test_wl_bisindo_pipeline.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_wl_bisindo_pipeline.py) | Unit Test Baru (WL-BISINDO) | 17 | **`17/17 PASS`** | `0.571s` | Seluruh parsing signer, label 0..31, dan validasi SD/SI lulus 100%. |
| [`tests/test_fsl_duplicate_leakage.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_fsl_duplicate_leakage.py) | Unit Test Baru (FSL-105) | 4 | **`4/4 PASS`** | `0.029s` | Deteksi 4 pasang duplikat SHA-256 & karantina anti-kebocoran split lulus 100%. |
| [`tests/test_pipeline_safety_audit.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_pipeline_safety_audit.py) | Regression Test (Tahap A/A.1) | 18 | **`18/18 PASS`** | `2.993s` | Nol regresi pada 4 modalitas (Video, Image, Audio, Text). |
| `scratch/run_regression_audit.py` (`test_signbridge_suite.py`) | Regression Test Suite Inti | 8 | **`8/8 PASS`** | `0.180s` | Kontrak 1, Graf, Kontrak 3, Augmentasi, Dataset SD/SI, Audio, Teks, Bridge 3-Layer. |

**Total Test Terverifikasi Lulus:** **39 Test `PASS` (0 FAIL, 0 ERROR).**

---

## 9. File yang Diubah dan Dibuat

### Berkas Baru:
1. [`signbridge/data/video_metadata.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py): Modul metadata video terisolasi (WL-BISINDO 32 label, regex signer, FSL-105 duplikasi & karantina, validasi split SD/SI).
2. [`tests/test_wl_bisindo_pipeline.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_wl_bisindo_pipeline.py): 17 unit test untuk pipeline WL-BISINDO.
3. [`tests/test_fsl_duplicate_leakage.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_fsl_duplicate_leakage.py): 4 unit test untuk deteksi duplikasi dan karantina FSL-105.
4. [`docs/PIPELINE_VIDEO_WLBISINDO_FIX.md`](file:///C:/Users/PC/Downloads/Semester%205/ML/docs/PIPELINE_VIDEO_WLBISINDO_FIX.md): Dokumentasi teknis perbaikan pipeline Tahap A.2.2 ini.

### Berkas yang Dimodifikasi:
1. [`scripts/extract_keypoints.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py):
   - Integrasi `extract_signer_id_from_text()` untuk mengenali `signer0`..`signer4`.
   - Penambahan dukungan `source="wl_bisindo"` dengan resolusi ke `WLBISINDO_LABELS`.
   - Pemisahan tahap perencanaan murni `plan_extraction()` dan penulisan manifest sidecar (`_source_metadata.csv` & `_sha256_duplicates.csv`).
2. [`signbridge/data/dataset.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py):
   - Penambahan validasi kelengkapan kelas pada protokol Signer-Independent (`SI`).
   - Penolakan signer test dengan kelas tidak lengkap (`allow_partial_class_coverage=False`).
3. [`data/DATASET_DOWNLOAD_MANIFEST.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/DATASET_DOWNLOAD_MANIFEST.csv):
   - Penambahan baris entri `V1_WLBISINDO_ARCHIVE` dengan lisensi resmi **`CC BY-NC 4.0`** dan SHA-256 terverifikasi.

---

## 10. Risiko dan Rekomendasi Pekerjaan Lanjutan

### 10.1 Risiko yang Telah Dimitigasi
- **Tidak Ada Overwrite Berkas Asli:** Arsip `archive.zip` belum diekstrak. File CSV asli FSL-105 dan `concepts.csv` tidak disentuh.
- **Tidak Ada Kebocoran Data (Data Leakage):** Pasangan duplikat SHA-256 yang melintasi train/test FSL-105 otomatis dikarantina dari manifest eksperimen.
- **Tidak Ada Klaim SI Palsu:** Signer0 tidak dapat dijadikan held-out test signer tunggal untuk evaluasi 32 kelas karena hanya memiliki 12 kelas.

### 10.2 Rekomendasi Langkah Selanjutnya (Menunggu Persetujuan Pengguna)
1. **Pemasangan Dependency Environment:** Pasang dependency `torch`, `opencv-python`, `mediapipe`, `onnxruntime`, `pytest`, `fastapi`, `sqlalchemy` pada environment `Python311`.
2. **Ekstraksi Aman WL-BISINDO:** Setelah persetujuan diberikan, ekstrak `data/raw/video/wl_bisindo/archive.zip` ke subfolder `data/raw/video/wl_bisindo/videos/` (risiko overwrite 0%).
3. **Eksekusi Ekstraksi Keypoint:** Jalankan `scripts/extract_keypoints.py` dengan parameter `--source wl_bisindo` untuk menghasilkan array keypoint 86 simpul riil tanpa synthetic fallback.

