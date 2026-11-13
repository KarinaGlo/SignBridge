# LAPORAN EKSTRAKSI DAN VALIDASI FISIK DATASET WL-BISINDO (TAHAP A.2.3)

**Proyek:** SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Workspace Aktif:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif:** `feature/dataset-acquisition` (`HEAD: b38b4da`)  
**Tanggal:** 7 November 2026  
**Peran:** Senior Data Engineer, Machine Learning Engineer, dan Dataset Integrity Auditor  
**Strategi Pemodelan:** **OPSI A** (Seluruh 1.600 video dari 32 kelas dipertahankan untuk pretraining representasi video BISINDO; 10 kelas overlap digunakan untuk adaptasi/fine-tuning berikutnya).

---

## 1. Identitas Dataset

- **Nama Dataset:** WL-BISINDO (*Word-Level Bahasa Isyarat Indonesia*)
- **Domain:** Pengenalan Bahasa Isyarat Indonesia tingkat kata (*word-level sign recognition*)
- **Bahasa Isyarat:** BISINDO (Bahasa Isyarat Indonesia — terpisah secara tegas dari FSL dan ASL)
- **Modalitas:** Video (.mp4)
- **Jumlah Kelas Asli:** 32 kelas (`label0` sampai `label31`)
- **Jumlah Signer:** 5 penutur isyarat manusia (`signer0` sampai `signer4`)
- **Total Klip Video:** 1.600 berkas video MP4

---

## 2. Sumber Arsip dan Lisensi

- **Sumber Resmi:** Kaggle (`glennleonali/wl-bisindo`) & GitHub (`AceKinnn/WL-BISINDO`)
- **Peneliti / Pembuat:** Grace Oktaviani Kindy, Glenn Leonali, Henry Lucky (2025)
- **Lisensi Resmi:** **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**
- **Ketentuan Lisensi:** Penggunaan **non-komersial** (*non-commercial use only*) dengan **atribusi wajib**. Tidak bebas digunakan untuk tujuan komersial atau monetisasi komersial.

---

## 3. SHA-256 dan Integritas ZIP Sebelum Ekstraksi

Pemeriksaan kriptografis penuh sebelum ekstraksi:

| Parameter | Nilai Terverifikasi | Status |
|---|---|:---:|
| **Lokasi Arsip Sumber** | `data/raw/video/wl_bisindo/archive.zip` | FOUND |
| **Ukuran Arsip (Byte)** | `2.126.878.088` bytes (`2.028,35 MiB` / `1,981 GiB`) | VALID |
| **SHA-256 ZIP Sebelum Ekstraksi** | `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095` | **MATCH 100%** |
| **Pemeriksaan Direktori Target** | `data/raw/video/wl_bisindo/videos/` belum ada sebelum ekstraksi (0 risiko overwrite) | **SAFE** |
| **Pemeriksaan Keamanan Path ZIP** | 0 path traversal (`..`), 0 absolute path, 0 tabrakan nama case-insensitive | **PASSED** |

---

## 4. Ukuran ZIP dan Hasil Ekstraksi

| Atribut | Sebelum Ekstraksi (ZIP) | Setelah Ekstraksi (Direktori Fisik) | Selisih / Rasio Kompresi |
|---|---:|---:|---:|
| **Ukuran Total (Bytes)** | `2.126.878.088` B | `2.164.708.443` B | $+37.830.355$ B ($1,78\%$) |
| **Ukuran Total (MiB / GiB)** | `2.028,35 MiB` / `1,981 GiB` | `2.064,43 MiB` / `2,016 GiB` | Rasio $\approx 0,982$ (video MP4 telah terkompresi H.264) |
| **Jumlah File** | 1 arsip `.zip` | 1.600 berkas fisik `.mp4` | Tepat 1.600 file |

---

## 5. Waktu dan Metode Ekstraksi

- **Waktu Ekstraksi:** 7 November 2026, durasi: **89,71 detik**
- **Metode Ekstraksi:**
  - Ekstraksi *stream-based* per entri melalui Python `zipfile` dengan verifikasi **CRC-32 per file secara real-time**.
  - Penulisan berkas dengan *chunked binary I/O* langsung ke direktori target:
    `data/raw/video/wl_bisindo/videos/`
  - Struktur nama file asli (`signer<S>_label<L>_sample<K>.mp4`) dan ekstensi `.mp4` dipertahankan 100% tanpa kompresi ulang, tanpa resize, dan tanpa transcode.
  - Arsip asli `archive.zip` tetap dipertahankan utuh di tempatnya.

---

## 6. Jumlah Video yang Diekstrak

- **Total Video yang Berhasil Diekstrak:** **1.600 berkas video `.mp4`**
- **Total Video yang Gagal Diekstrak:** **0 berkas**
- **Direktori Output:** [`data/raw/video/wl_bisindo/videos/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/videos/)

---

## 7. Jumlah File Rusak dan File Kosong

- **Jumlah File Kosong (0 Byte):** **0 berkas** (ukuran file minimum: `460.698 B`, maksimum: `6.234.157 B`, rata-rata: `1.352.942,8 B`).
- **Jumlah File Rusak / Header Tidak Valid:** **0 berkas** (seluruh 1.600 berkas memiliki kontainer ISO BMFF `ftyp` dan `moov` yang valid).
- **Status Validasi Header:** **`1600 / 1600 HEADER_VALID (PASS)`**

---

## 8. Jumlah SHA-256 Unik dan Duplikasi

- **Perhitungan Hash:** SHA-256 dihitung secara independen pada setiap file fisik di disk setelah ekstraksi selesai.
- **Jumlah SHA-256 Unik:** **1.600 unik dari 1.600 berkas**
- **Duplikat Dalam Kelas:** **0 duplikat**
- **Duplikat Lintas Kelas:** **0 duplikat**
- **Status Integritas Kriptografis:** **`PASS (0 Duplikat)`**

---

## 9. Distribusi 32 Kelas (Label 0 sampai 31)

Setiap kelas memiliki **tepat 50 video** (seimbang sempurna: $32 \times 50 = 1.600$):

| ID | Gloss Resmi WL-BISINDO | Jumlah Video | Status Overlap SignBridge |
|---:|---|---:|:---:|
| 0 | AIR | 50 | Non-overlap |
| 1 | BELAJAR | 50 | **OVERLAP (`C15`)** |
| 2 | CARI | 50 | Non-overlap |
| 3 | HARI | 50 | Non-overlap |
| 4 | INGAT | 50 | Non-overlap |
| 5 | LAGI | 50 | Non-overlap |
| 6 | MAAF | 50 | **OVERLAP (`C03`)** |
| 7 | MAKAN | 50 | Non-overlap |
| 8 | MOTOR | 50 | Non-overlap |
| 9 | SAYA | 50 | **OVERLAP (`C05`)** |
| 10 | TERIMA_KASIH | 50 | **OVERLAP (`C02`)** |
| 11 | TULI | 50 | Non-overlap |
| 12 | APA | 50 | **OVERLAP (`C25`)** |
| 13 | SIAPA | 50 | **OVERLAP (`C26`)** |
| 14 | KAPAN | 50 | **OVERLAP (`C28`)** |
| 15 | DIMANA | 50 | **OVERLAP (`C27`)** |
| 16 | MENGAPA | 50 | Non-overlap |
| 17 | BAGAIMANA | 50 | **OVERLAP (`C29`)** |
| 18 | MERAH | 50 | Non-overlap |
| 19 | KUNING | 50 | Non-overlap |
| 20 | HIJAU | 50 | Non-overlap |
| 21 | HITAM | 50 | Non-overlap |
| 22 | DENGAR | 50 | Non-overlap |
| 23 | BERANGKAT | 50 | Non-overlap |
| 24 | DATANG | 50 | Non-overlap |
| 25 | TEMAN | 50 | **OVERLAP (`C08`)** |
| 26 | KELUARGA | 50 | Non-overlap |
| 27 | RUMAH | 50 | Non-overlap |
| 28 | PAGI | 50 | Non-overlap |
| 29 | SIANG | 50 | Non-overlap |
| 30 | SORE | 50 | Non-overlap |
| 31 | MALAM | 50 | Non-overlap |
| **Total** | **32 Kelas** | **1.600** | **10 Overlap / 22 Non-overlap** |

---

## 10. Distribusi Lima Signer

Jumlah klip video per penutur isyarat (*signer*):

| Signer ID | Jumlah Video | Persentase | Cakupan Kelas | Keterangan Distribusi |
|---|---:|---:|---|---|
| `SIGNER0` | 120 | $7,50\%$ | 12 kelas (`label0`..`label11`) | 10 klip per label untuk 12 kelas pertama; **tidak ada** klip pada label 12–31. |
| `SIGNER1` | 420 | $26,25\%$ | 32 kelas lengkap | 10 klip/label (label 0–11) + 15 klip/label (label 12–31). |
| `SIGNER2` | 420 | $26,25\%$ | 32 kelas lengkap | 10 klip/label (label 0–11) + 15 klip/label (label 12–31). |
| `SIGNER3` | 320 | $20,00\%$ | 32 kelas lengkap | 10 klip/label untuk seluruh 32 kelas. |
| `SIGNER4` | 320 | $20,00\%$ | 32 kelas lengkap | 10 klip/label untuk seluruh 32 kelas. |
| **Total** | **1.600** | **$100,00\%$** | — | **5 Signer** |

---

## 11. Tabel Signer $\times$ Label (Distribusi Aktual 1.600 Video)

| Label ID | Gloss | SIGNER0 | SIGNER1 | SIGNER2 | SIGNER3 | SIGNER4 | Total per Label |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `0` | AIR | 10 | 10 | 10 | 10 | 10 | 50 |
| `1` | BELAJAR | 10 | 10 | 10 | 10 | 10 | 50 |
| `2` | CARI | 10 | 10 | 10 | 10 | 10 | 50 |
| `3` | HARI | 10 | 10 | 10 | 10 | 10 | 50 |
| `4` | INGAT | 10 | 10 | 10 | 10 | 10 | 50 |
| `5` | LAGI | 10 | 10 | 10 | 10 | 10 | 50 |
| `6` | MAAF | 10 | 10 | 10 | 10 | 10 | 50 |
| `7` | MAKAN | 10 | 10 | 10 | 10 | 10 | 50 |
| `8` | MOTOR | 10 | 10 | 10 | 10 | 10 | 50 |
| `9` | SAYA | 10 | 10 | 10 | 10 | 10 | 50 |
| `10` | TERIMA_KASIH | 10 | 10 | 10 | 10 | 10 | 50 |
| `11` | TULI | 10 | 10 | 10 | 10 | 10 | 50 |
| `12` | APA | 0 | 15 | 15 | 10 | 10 | 50 |
| `13` | SIAPA | 0 | 15 | 15 | 10 | 10 | 50 |
| `14` | KAPAN | 0 | 15 | 15 | 10 | 10 | 50 |
| `15` | DIMANA | 0 | 15 | 15 | 10 | 10 | 50 |
| `16` | MENGAPA | 0 | 15 | 15 | 10 | 10 | 50 |
| `17` | BAGAIMANA | 0 | 15 | 15 | 10 | 10 | 50 |
| `18` | MERAH | 0 | 15 | 15 | 10 | 10 | 50 |
| `19` | KUNING | 0 | 15 | 15 | 10 | 10 | 50 |
| `20` | HIJAU | 0 | 15 | 15 | 10 | 10 | 50 |
| `21` | HITAM | 0 | 15 | 15 | 10 | 10 | 50 |
| `22` | DENGAR | 0 | 15 | 15 | 10 | 10 | 50 |
| `23` | BERANGKAT | 0 | 15 | 15 | 10 | 10 | 50 |
| `24` | DATANG | 0 | 15 | 15 | 10 | 10 | 50 |
| `25` | TEMAN | 0 | 15 | 15 | 10 | 10 | 50 |
| `26` | KELUARGA | 0 | 15 | 15 | 10 | 10 | 50 |
| `27` | RUMAH | 0 | 15 | 15 | 10 | 10 | 50 |
| `28` | PAGI | 0 | 15 | 15 | 10 | 10 | 50 |
| `29` | SIANG | 0 | 15 | 15 | 10 | 10 | 50 |
| `30` | SORE | 0 | 15 | 15 | 10 | 10 | 50 |
| `31` | MALAM | 0 | 15 | 15 | 10 | 10 | 50 |
| **Total** | — | **120** | **420** | **420** | **320** | **320** | **1.600** |

---

## 12. Hasil Validasi Properti Video (Resolusi dan Durasi)

Parsing biner atom ISO BMFF (`ftyp`, `moov`, `mvhd`, `trak`, `tkhd`) dilakukan langsung pada seluruh 1.600 file:

- **Distribusi Resolusi Spasial ($W \times H$):**
  - **$1920 \times 1080$ (Full HD 1080p):** **1.353 video** ($84,56\%$)
  - **$1280 \times 720$ (HD 720p):** **247 video** ($15,44\%$)
- **Statistik Durasi Video ($n = 1.600$ video):**
  - **Minimum:** `1,400 detik`
  - **Maksimum:** `5,853 detik`
  - **Rata-rata:** `2,166 detik`
  - **Total Durasi Koleksi:** $\approx 3.465,6$ detik ($\approx 57,76$ menit)

---

## 13. Hasil Validasi Decoding

- **Status Pustaka Decoder:**
  - OpenCV (`cv2`): **NOT AVAILABLE** (belum terpasang di `Python311`).
  - FFprobe / FFmpeg: **NOT AVAILABLE** (tidak terpasang di sistem `PATH`).
- **Pemeriksaan Kontainer Biner:**
  - `header_validation_status`: **`1600 / 1600 HEADER_VALID`** (struktur atom kontainer ISO BMFF valid).
- **Pengujian Decode Frame Penuh:**
  - `decode_validation_status`: **`NOT_TESTED (NO_DECODER)`**
- **Catatan Auditor:** Sesuai batasan protokol audit, integritas kontainer video terbukti valid, tetapi validasi *frame-by-frame decoding* penuh baru dapat dievaluasi setelah dependency decoder (`opencv-python` atau `mediapipe`) dipasang pada tahap berikutnya.

---

## 14. Analisis 10 Kelas Overlap dan 22 Kelas Non-Overlap (Opsi A)

Strategi **Opsi A** mempertahankan seluruh 1.600 video dari 32 kelas sebagai dataset sumber:

### 14.1 Sepuluh Kelas Beririsan Langsung dengan Konsep SignBridge (`500` Video)

| No | Gloss WL-BISINDO | ID Konsep SignBridge | Kategori Konsep | Video Overlap | Jumlah Signer |
|:---:|---|:---:|---|:---:|:---:|
| 1 | `BELAJAR` | `C15` | Aktivitas | 50 | 5 (`S0`..`S4`) |
| 2 | `MAAF` | `C03` | Sapaan | 50 | 5 (`S0`..`S4`) |
| 3 | `SAYA` | `C05` | Subjek | 50 | 5 (`S0`..`S4`) |
| 4 | `TERIMA_KASIH` | `C02` | Sapaan | 50 | 5 (`S0`..`S4`) |
| 5 | `APA` | `C25` | Tanya | 50 | 4 (`S1`..`S4`) |
| 6 | `SIAPA` | `C26` | Tanya | 50 | 4 (`S1`..`S4`) |
| 7 | `KAPAN` | `C28` | Tanya | 50 | 4 (`S1`..`S4`) |
| 8 | `DIMANA` | `C27` | Tanya | 50 | 4 (`S1`..`S4`) |
| 9 | `BAGAIMANA` | `C29` | Tanya | 50 | 4 (`S1`..`S4`) |
| 10 | `TEMAN` | `C08` | Subjek | 50 | 4 (`S1`..`S4`) |
| **Total** | **10 Kelas Overlap** | — | — | **500 Video** | — |

### 14.2 Dua Puluh Dua Kelas Non-Overlap (`1.100` Video)
Dipertahankan sebagai data representasi dasar video BISINDO:
`AIR` (50), `BERANGKAT` (50), `CARI` (50), `DATANG` (50), `DENGAR` (50), `HARI` (50), `HIJAU` (50), `HITAM` (50), `INGAT` (50), `KELUARGA` (50), `KUNING` (50), `LAGI` (50), `MAKAN` (50), `MALAM` (50), `MENGAPA` (50), `MERAH` (50), `MOTOR` (50), `PAGI` (50), `RUMAH` (50), `SIANG` (50), `SORE` (50), `TULI` (50).

### 14.3 Dua Puluh Dua Konsep Kelas SignBridge yang Belum Tersedia di WL-BISINDO
22 konsep ruang kelas berikut **tidak ada** di dalam WL-BISINDO dan dialokasikan untuk pemenuhan dataset `SignBridge-Kelas` (rekaman mandiri tim):
`ADA`, `BACA`, `BAIK`, `BELUM`, `BENAR`, `BISA`, `BUKU`, `GURU`, `HALO`, `JAWAB`, `KAMU`, `KELAS`, `MAU`, `PAHAM`, `SALAH`, `SEKOLAH`, `SUDAH`, `TANYA`, `TIDAK`, `TOLONG`, `TUGAS`, `TULIS`.

---

## 15. Lokasi Manifest dan Ringkasan Teknis

1. **Manifest Ekstraksi Video WL-BISINDO:**
   [`data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv)  
   Berisi 1.600 baris dengan 15 kolom lengkap:
   `relative_path,filename,source,source_label_id,source_gloss,signer_id,sample_id,file_size_bytes,sha256,extension,validation_status,header_validation_status,decode_validation_status,overlap_with_signbridge,license`
2. **Ringkasan JSON Metadata:**
   [`data/raw/video/wl_bisindo/extraction_summary.json`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/extraction_summary.json)  
   Berisi ringkasan statistik ukuran, resolusi, durasi, dan matriks signer $\times$ label.

---

## 16. Masalah yang Ditemukan

1. **Struktur Matriks Signer Asimetris:** `signer0` hanya merekam 12 kelas (`label0`..`label11`), sedangkan `signer1`..`signer4` merekam ke-32 kelas. Hal ini mewajibkan pembagian Signer-Independent (SI) menggunakan `signer1`, `signer2`, `signer3`, atau `signer4` sebagai test signer agar evaluasi mencakup ke-32 kelas.
2. **Ketiadaan Decoder di Lingkungan Python Saat Ini:** `cv2` dan `ffprobe` belum terpasang di sistem, sehingga decode frame aktual ditandai sebagai `NOT_TESTED (NO_DECODER)`.

---

## 17. Keterbatasan Validasi

1. Validasi saat ini membuktikan keberadaan fisik berkas, ukuran aktual, keutuhan kontainer ISO BMFF (`ftyp`, `moov`, `mvhd`), konsistensi penamaan, dan keunikan SHA-256 (0 duplikat).
2. Decoding per-frame dan ekstraksi koordinat pose keypoint 86 simpul MediaPipe belum dijalankan pada tahap ini sesuai batasan larangan preprocessing massal.

---

## 18. Status Integritas Arsip ZIP dan Sumber Lainnya

- [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip): **UTUH & TIDAK DIUBAH** (`SHA-256: 12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095`).
- [`data/bridge/concepts.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/bridge/concepts.csv): **UTUH & TIDAK DIUBAH** (`SHA-256: d3d0907642b8039411058d1ab378d15d6ab9ed929f743838a190bd68ffce9005`).
- Berkas CSV resmi FSL-105 (`labels.csv`, `train.csv`, `test.csv`): **UTUH & TIDAK DIUBAH**.

---

## 19. Rekomendasi Tahap Selanjutnya

1. **Pemasangan Dependency Environment:** Pasang paket `opencv-python`, `mediapipe`, `torch`, `onnxruntime`, `fastapi`, `sqlalchemy` pada lingkungan `Python311` dengan izin pengguna.
2. **Ekstraksi Keypoint 86 Simpul:** Jalankan ekstraksi offline keypoint MediaPipe Holistic pada video `wl_bisindo/videos/` menggunakan `scripts/extract_keypoints.py --source wl_bisindo`.
3. **Penyelarasan Pretraining & Adaptasi:** Gunakan 1.600 video (32 kelas) untuk pretraining representasi spatio-temporal video BISINDO, dan manfaatkan 500 video (10 kelas overlap) bersama rekaman `SignBridge-Kelas` untuk adaptasi ke 32 konsep ruang kelas.

