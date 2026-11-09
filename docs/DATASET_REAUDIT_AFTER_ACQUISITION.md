# LAPORAN RE-AUDIT DATASET SETELAH AKUISISI TAMBAHAN (TAHAP A.2.1)

**Proyek:** SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Workspace Aktif:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif:** `feature/dataset-acquisition` (`HEAD: b38b4da`)  
**Tanggal Re-Audit:** 7 November 2026  
**Ruang Lingkup:** Verifikasi ulang ketersediaan fisik, integritas kriptografis (SHA-256 & CRC-32), struktur kontainer, duplikasi lintas kelas/split, konsistensi kosakata/label, dan kompatibilitas loader pada seluruh modalitas dataset setelah penambahan data baru oleh pengguna, tanpa menjalankan ekstraksi arsip, preprocessing massal, maupun training.

---

## 1. Ringkasan Dataset Sebelum dan Sesudah Penambahan

Tabel berikut membandingkan kondisi fisik dataset pada audit sebelumnya (`docs/DATASET_GAP_ANALYSIS.md` & laporan Tahap A.2) dengan kondisi fisik terkini di workspace `C:\Users\PC\Downloads\Semester 5\ML`:

| Modality / Bahasa Isyarat | Dataset | Kondisi Sebelumnya (Tahap 1–4 / A.2) | Kondisi Terkini (Tahap A.2.1 — Terverifikasi Fisik) | Perubahan Status |
|---|---|---|---|---|
| **Video — BISINDO** | **WL-BISINDO** (`data/raw/video/wl_bisindo/`) | `BLOCKED` (`0` berkas video fisik) | **DITEMUKAN:** [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip) (`2.126.878.088` byte / `1,981 GiB`), berisi **`1.600` video `.mp4` utuh** (`CRC-32 100% OK`, belum diekstrak) | **BARU DITEMUKAN & TERVERIFIKASI (`+1.600` video `.mp4` di dalam ZIP)** |
| **Video — BISINDO** | **SignBridge-Kelas** ($3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ klip}$, target gabungan $\ge 3.000$) | `NOT AVAILABLE` (`0` berkas video fisik) | **`NOT FOUND`** (`0` berkas video fisik) | Tidak berubah (`NOT FOUND`) |
| **Video — BISINDO & FSL** | **Video Referensi Jembatan** (`data/ref_signs/bisindo/*.mp4` & `fsl/*.mp4`) | `NOT AVAILABLE` (`0 / 64` video fisik) | **`NOT FOUND`** (`0 / 64` berkas video fisik) | Tidak berubah (`NOT FOUND`) |
| **Video — FSL** *(Terpisah dari BISINDO)* | **FSL-105** (`data/raw/video/fsl_105/`) | `clips.zip` + `2.130` video `.MOV` (`105` kelas) + `labels.csv`, `train.csv`, `test.csv` | Utuh: `1` ZIP (`379.081.783 B`) + **`2.130` berkas `.MOV`** (`390.121.532 B`) + `3` CSV + `1` JSON | Tetap tersedia & utuh *(ditemukan `4` pasang duplikat SHA-256 bawaan sumber)* |
| **Video — ASL** *(Pretraining, terpisah dari BISINDO)* | **WLASL-300** (`data/raw/video/wlasl_300/`) | Manifest JSON saja (`WLASL_v0.3.json`, `WLASL_300_manifest.json`), `0` video fisik | **`NOT FOUND` untuk berkas video** (`0` berkas `.mp4`/`.mov`/`.webm`; hanya `2` berkas JSON manifest) | Tidak berubah (`0` video fisik) |
| **Image — BISINDO** | **BISINDO Alphabet A–Z** (`data/raw/image/bisindo_alphabet/`) | `4.466` citra RGB (`4.154` `.jpg` + `312` `.jpeg`, `26` kelas `A–Z`) | Utuh: **`4.466` citra RGB** (`29.054.822 B`) di `26` subfolder `A`–`Z` + `1` CSV hash + `2` JSON metadata | Tetap tersedia & 100% utuh *(ditemukan `2` pasang duplikat lintas kelas bawaan Mendeley)* |
| **Audio — Bahasa Indonesia (`id_id`)** | **Google FLEURS (`id_id`)** (`data/audio/fleurs/id_id/`) | `dev.tar.gz` + `350` berkas `.wav` (`dev`) + `3` berkas TSV (`train`/`dev`/`test`) | Utuh: `1` `dev.tar.gz` (`220.586.217 B`) + **`350` berkas `.wav`** (`267.099.980 B`, `4.173,12 dtk`) + `3` TSV (`3.616` baris total). `train.tar.gz` & `test.tar.gz` **`NOT FOUND`**. | Tetap tersedia pada split `dev` (`350` WAV); `train`/`test` audio masih `NOT FOUND` |
| **Audio — Rekaman Kelas (`id` & `fil`)** | **Suara Kelas SignBridge** (`data/audio/wavs/` & `data/audio/wavs_fil/`) | Metadata CSV saja (`metadata.csv` 60 baris, `metadata_fil.csv` 24 baris), `0` WAV fisik | **`NOT FOUND` untuk berkas WAV** (`0 / 60` WAV Indonesia & `0 / 24` WAV Filipino; hanya `2` berkas CSV metadata) | Tidak berubah (`0` WAV kelas fisik) |
| **Text — Bahasa Indonesia** | **Tatoeba (`ind`) + Korpus Kelas SignBridge** (`data/text/`) | `ind_sentences.tsv.bz2` + `ind_sentences.tsv` (`28.418`), `kelas_sentences.txt` (`200`), `train.tsv` (`170`), `val.tsv` (`30`), `test_manual.tsv` (`105`) | Utuh 100%: `1` `.bz2` + `4` `.tsv` + `1` `.txt` (`0` perubahan SHA-256, `0` kebocoran split) | Tetap tersedia & 100% utuh |
| **Fitur Terproses & Manifest Utama** | `data/keypoints/`, `data/rgb_feats/`, `data/manifest.csv` | Belum dibuat | **`NOT FOUND`** (ketiga lokasi belum ada di disk) | Tidak berubah (`NOT FOUND`) |

---

## 2. Dataset Baru yang Ditemukan

Pemindaian menyeluruh pada workspace menemukan **1 dataset fisik baru** yang sebelumnya berstatus `BLOCKED` (`0` video):

1. **[`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip)**
   - **Jenis Dataset:** Dataset video **WL-BISINDO** (*Word-Level Bahasa Isyarat Indonesia* — Grace Oktaviani Kindy, Glenn Leonali, & Henry Lucky; Kaggle `glennleonali/wl-bisindo` / GitHub `AceKinnn/WL-BISINDO`).
   - **Bahasa Isyarat:** **BISINDO** (Bahasa Isyarat Indonesia — terpisah dari FSL dan ASL).
   - **Ukuran Arsip Terkompresi:** `2.126.878.088` byte (`2.028,35 MiB` / `1,981 GiB`).
   - **Ukuran Total Tidak Terkompresi di Dalam ZIP:** `2.164.708.443` byte (`2.064,43 MiB` / `2,016 GiB`).
   - **SHA-256 Arsip:** `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095`
   - **Isi Arsip:** Tepat **`1.600` berkas video `.mp4`** (`32` kelas $\times$ `50` sampel per kelas, diperagakan oleh `5` signer: `signer0` s/d `signer4`).
   - **Status Ekstraksi:** **Belum diekstrak** di disk (`data/raw/video/wl_bisindo/` hanya berisi `archive.zip`). Sesuai instruksi audit, arsip dipertahankan utuh dan tidak diekstrak sebelum persetujuan pengguna.
   - **Catatan Lisensi Penting:** Berdasarkan repositori resmi `AceKinnn/WL-BISINDO` dan halaman Kaggle `glennleonali/wl-bisindo`, lisensi resmi dataset **WL-BISINDO** adalah **CC BY-NC 4.0** (*Attribution-NonCommercial 4.0 International* — hanya penggunaan non-komersial dengan atribusi wajib). Catatan pada [`DATA_CARD.md`](file:///C:/Users/PC/Downloads/Semester%205/ML/DATA_CARD.md#L47-L53) bawaan repositori yang menulis `CC BY 4.0` tidak sesuai dengan lisensi sumber asli dan perlu dicatat agar tidak melanggar ketentuan non-komersial.

Tidak ada dataset baru lain yang ditambahkan pada `data/audio/`, `data/raw/image/`, `data/raw/video/wlasl_300/`, `data/keypoints/`, `data/rgb_feats/`, maupun `data/manifest.csv`.

---

## 3. Jumlah File Fisik per Modality (Inventarisasi Terkini)

Inventarisasi seluruh berkas fisik pada direktori target (`ZIP`, `MP4`, `MOV`, `WEBM`, `WAV`, `JPG`, `JPEG`, `PNG`, `NPZ`, `CSV`, `TSV`, `JSON`, `TXT`, `BZ2`, `TAR.GZ`):

### 3.1 Pemeriksaan Direktori Wajib

| Lokasi yang Diperiksa | Status Keberadaan | Rincian File Fisik Berdasarkan Ekstensi |
|---|---|---|
| [`data/raw/video/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video) | **FOUND** (`3` subfolder: `wl_bisindo`, `fsl_105`, `wlasl_300`) | `2` `.zip` (`wl_bisindo/archive.zip`, `fsl_105/clips.zip`), `2.130` `.MOV` (terekstrak di `fsl_105/clips/`), `0` `.mp4` di luar ZIP (`1.600` `.mp4` berada di dalam `wl_bisindo/archive.zip`), `0` `.webm`, `3` `.csv`, `3` `.json` |
| [`data/raw/image/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/image) | **FOUND** (`bisindo_alphabet/A..Z`) | `4.154` `.jpg`, `312` `.jpeg` (**total `4.466` citra RGB**), `0` `.png`, `1` `.csv` (`file_hashes_sha256.csv`), `2` `.json` |
| [`data/audio/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio) | **FOUND** (`metadata.csv`, `metadata_fil.csv`, `fleurs/id_id/`) | `350` `.wav` (di `fleurs/id_id/audio/dev/`), `0` `.wav` rekaman kelas (`data/audio/wavs/` **`NOT FOUND`**), `1` `.tar.gz` (`dev.tar.gz`), `2` `.csv`, `3` `.tsv` |
| [`data/text/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/text) | **FOUND** (`train.tsv`, `val.tsv`, `test_manual.tsv`, `kelas_sentences.txt`, `tatoeba/`) | `4` `.tsv`, `1` `.txt`, `1` `.bz2` (`ind_sentences.tsv.bz2`) |
| [`data/bridge/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/bridge) & root `data/` | **FOUND** | `3` `.csv` (`concepts.csv`, `phonology.csv`, `DATASET_DOWNLOAD_MANIFEST.csv`), `1` `.md` (`PHONOLOGY_GUIDE.md`), `1` `.gitkeep` |
| `data/keypoints/` | **`NOT FOUND`** | `0` berkas `.npz` / `.npy` (direktori belum ada) |
| `data/rgb_feats/` | **`NOT FOUND`** | `0` berkas `.npz` / `.npy` (direktori belum ada) |
| `data/manifest.csv` | **`NOT FOUND`** | Berkas belum ada |

### 3.2 Rekapitulasi Jumlah File Media & Anotasi per Modality

| Modality | File Media Terekstrak di Disk | File Media di Dalam Arsip (Belum Diekstrak) | File Arsip | File Metadata / Split (`CSV`/`TSV`/`JSON`/`TXT`) | File Fitur (`NPZ`/`NPY`) |
|---|---:|---:|---:|---:|---:|
| **Video (BISINDO)** | `0` | **`1.600` `.mp4`** (di dalam `wl_bisindo/archive.zip`) | `1` (`.zip`) | `0` | `0` (`NOT FOUND`) |
| **Video (FSL)** | **`2.130` `.MOV`** | *(sudah diekstrak dari `clips.zip`)* | `1` (`.zip`) | `4` (`3` CSV + `1` JSON) | `0` (`NOT FOUND`) |
| **Video (ASL)** | `0` (`NOT FOUND`) | `0` (`NOT FOUND`) | `0` | `2` (`2` JSON manifest) | `0` (`NOT FOUND`) |
| **Image (BISINDO A–Z)** | **`4.466` citra** (`4.154` `.jpg` + `312` `.jpeg`) | `0` | `0` | `3` (`1` CSV + `2` JSON) | `0` |
| **Audio (`id_id` & Kelas)** | **`350` `.wav`** (FLEURS `dev`; WAV kelas `0` / `NOT FOUND`) | *(sudah diekstrak dari `dev.tar.gz`)* | `1` (`.tar.gz`) | `5` (`2` CSV + `3` TSV) | `0` |
| **Text (`id`)** | — | — | `1` (`.bz2`) | **`5`** (`4` TSV + `1` TXT) | — |
| **Lintas-Modality (`data/`)** | `0` (`ref_signs` `NOT FOUND`) | `0` | `0` | `3` (`concepts.csv`, `phonology.csv`, `DATASET_DOWNLOAD_MANIFEST.csv`) | `0` |

---

## 4. Jumlah Video BISINDO yang Benar-Benar Ditemukan

Pemisahan tegas dilakukan antara **BISINDO** (Bahasa Isyarat Indonesia), **FSL** (Filipino Sign Language), dan **ASL** (American Sign Language):

- **Total Video BISINDO Fisik yang Terverifikasi:** **`1.600` berkas video `.mp4`** (seluruhnya berada di dalam arsip [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip)).
- **Video BISINDO Terekstrak di Disk Saat Ini:** **`0` berkas** (arsip belum diekstrak).
- **Video BISINDO Rekaman Mandiri Tim (`SignBridge-Kelas`, target $3 \times 32 \times 10 = 960$ klip, total target modul $\ge 3.000$ data):** **`0` berkas (`NOT FOUND`)**.
- **Video Referensi BISINDO (`data/ref_signs/bisindo/*.mp4`):** **`0` berkas (`NOT FOUND`)**.
- **Video Non-BISINDO (TIDAK dihitung sebagai video BISINDO):**
  - **FSL-105 (Filipino Sign Language):** `2.130` berkas `.MOV` di `data/raw/video/fsl_105/clips/`.
  - **WLASL-300 (American Sign Language):** `0` berkas video fisik (`2` berkas manifest JSON saja).

---

## 5. Hasil Pemeriksaan Mendalam Arsip ZIP (`wl_bisindo/archive.zip`)

Seluruh `1.600` entri di dalam [`data/raw/video/wl_bisindo/archive.zip`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip) telah diaudit secara *streaming* di memori (tanpa menulis/mengekstrak ke disk):

| Parameter Pemeriksaan ZIP | Hasil Verifikasi Aktual | Status |
|---|---|---|
| **Path Berkas** | `data/raw/video/wl_bisindo/archive.zip` | **FOUND** |
| **Ukuran Arsip (Compressed)** | `2.126.878.088` byte (`2.028,35 MiB` / `1,981 GiB`) | **VALID** |
| **Ukuran Total Isi (Uncompressed)** | `2.164.708.443` byte (`2.064,43 MiB` / `2,016 GiB`) | **VALID** |
| **SHA-256 Arsip** | `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095` | **TERVERIFIKASI** |
| **Jumlah Total Entri ZIP** | `1.600` entri (`1.600` file, `0` entri direktori) | **VALID** |
| **Ekstensi File di Dalam ZIP** | `100%` `.mp4` (`{'.mp4': 1600}`), `0` file metadata/CSV/JSON di dalam arsip | **TERVERIFIKASI** |
| **Pemeriksaan CRC-32 & Dekompresi Penuh** | `1.600 / 1.600` file lulus dekompresi penuh & cocok CRC-32 (`0` error CRC) | **`PASS` (`0` Rusak)** |
| **Pemeriksaan File Kosong (`0` Byte)** | `0` file kosong (ukuran minimum `460.698 B`, maksimum `6.234.157 B`, rata-rata `1.352.942,8 B`) | **`PASS` (`0` Kosong)** |
| **Pemeriksaan Header Kontainer MP4 (`ftyp` / `mvhd` / `tkhd`)** | `1.600 / 1.600` file memiliki header ISO Base Media (`ftyp`) yang valid. Sampel terstratifikasi (`n = 191` klip) menunjukkan resolusi `1920x1080` (`136` klip) dan `1280x720` (`55` klip), serta durasi `1,47 dtk` s/d `5,85 dtk` (rata-rata `2,28 dtk`). | **`PASS`** |
| **Pemeriksaan Duplikasi SHA-256 di Dalam ZIP** | `1.600` hash SHA-256 unik dari `1.600` video (`0` duplikat dalam kelas, `0` duplikat lintas kelas) | **`PASS` (`0` Duplikat)** |
| **Struktur Folder & Pola Nama File** | **Flat di root arsip** (tanpa subfolder kelas). Seluruh `1.600` nama file mematuhi pola ketat `^signer(\d+)_label(\d+)_sample(\d+)\.mp4$` (`0` nama file menyimpang). Contoh: `signer0_label0_sample1.mp4` (`1.116.463 B`, CRC `98893502`). | **PERHATIAN PIPELINE** *(lihat Bagian 6 & 10)* |
| **Keamanan Ekstraksi & Risiko Overwrite** | `0` entri *path traversal* (`..`), `0` tabrakan nama file *case-insensitive* di dalam ZIP, dan direktori `data/raw/video/wl_bisindo/` saat ini hanya berisi `archive.zip` (`0` file `.mp4` eksisting $\rightarrow$ **risiko overwrite `0%`** jika diekstrak ke `data/raw/video/wl_bisindo/videos/`). | **AMAN UNTUK DIEKSTRAK SETELAH PERSETUJUAN** |

---

## 6. Distribusi Kelas / Gloss dan Kesesuaian dengan `data/bridge/concepts.csv`

### 6.1 Distribusi Jumlah Video per Kelas & per Signer pada `WL-BISINDO`

Di dalam `archive.zip`, kelas dikodekan secara numerik sebagai `label0` s/d `label31` (**`32` kelas**) dan diperagakan oleh **`5` signer** (`signer0` s/d `signer4`):

- **Distribusi per Kelas (`label0` s/d `label31`):** **Seimbang sempurna — tepat `50` video per kelas** ($32 \times 50 = 1.600$ video).
  - **`label0` s/d `label11` (`12` kelas):** `signer0 = 10`, `signer1 = 10`, `signer2 = 10`, `signer3 = 10`, `signer4 = 10` (`sample1`..`sample10` per signer; total `50` video/kelas).
  - **`label12` s/d `label31` (`20` kelas):** `signer0 = 0`, `signer1 = 15` (`sample1`..`sample15`), `signer2 = 15` (`sample1`..`sample15`), `signer3 = 10` (`sample1`..`sample10`), `signer4 = 10` (`sample1`..`sample10`); total `50` video/kelas.
- **Distribusi Total per Signer:**
  - `signer0`: `120` video (`7,5%`)
  - `signer1`: `420` video (`26,25%`)
  - `signer2`: `420` video (`26,25%`)
  - `signer3`: `320` video (`20,0%`)
  - `signer4`: `320` video (`20,0%`)
  *(Catatan penting untuk protokol Signer-Independent `SI`: jika `signer0` dipilih sebagai test/val split, ia hanya mencakup 12 dari 32 kelas! Oleh karena itu, pemilihan signer untuk evaluasi `SI` wajib menggunakan `signer1`, `signer2`, `signer3`, atau `signer4` yang mencakup ke-32 kelas lengkap).*

### 6.2 Perbandingan 32 Gloss Resmi `WL-BISINDO` terhadap `data/bridge/concepts.csv`

Arsip `archive.zip` **tidak menyertakan file `labels.csv`**. Berdasarkan dokumentasi resmi pembuat dataset **WL-BISINDO** (`AceKinnn/WL-BISINDO` / `glennleonali/wl-bisindo`), pemetaan `label0`–`label31` dibandingkan terhadap 32 konsep ruang kelas di [`data/bridge/concepts.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/bridge/concepts.csv) (`BISINDO_32_GLOSSES`) adalah sebagai berikut:

| Label ID WL-BISINDO | Gloss Resmi WL-BISINDO | Jumlah Video | Padanan di `data/bridge/concepts.csv` | Status Kecocokan Kosakata |
|---:|---|---:|---|---|
| `0` | `Air` | 50 | — | Tidak ada di `concepts.csv` |
| `1` | `Belajar` | 50 | `C15` — **`BELAJAR`** | **COCOK (`1/10`)** |
| `2` | `Cari` | 50 | — | Tidak ada di `concepts.csv` |
| `3` | `Hari` | 50 | — | Tidak ada di `concepts.csv` |
| `4` | `Ingat` | 50 | — | Tidak ada di `concepts.csv` |
| `5` | `Lagi` | 50 | — | Tidak ada di `concepts.csv` |
| `6` | `Maaf` | 50 | `C03` — **`MAAF`** | **COCOK (`2/10`)** |
| `7` | `Makan` | 50 | — | Tidak ada di `concepts.csv` |
| `8` | `Motor` | 50 | — | Tidak ada di `concepts.csv` |
| `9` | `Saya` | 50 | `C05` — **`SAYA`** | **COCOK (`3/10`)** |
| `10` | `Terima kasih` | 50 | `C02` — **`TERIMA_KASIH`** | **COCOK (`4/10`, normalisasi spasi $\rightarrow$ `_`)** |
| `11` | `Tuli` | 50 | — | Tidak ada di `concepts.csv` |
| `12` | `Apa` | 50 | `C25` — **`APA`** | **COCOK (`5/10`)** |
| `13` | `Siapa` | 50 | `C26` — **`SIAPA`** | **COCOK (`6/10`)** |
| `14` | `Kapan` | 50 | `C28` — **`KAPAN`** | **COCOK (`7/10`)** |
| `15` | `Di mana` | 50 | `C27` — **`DIMANA`** | **COCOK (`8/10`, normalisasi `Di mana` $\rightarrow$ `DIMANA`)** |
| `16` | `Mengapa` | 50 | — | Tidak ada di `concepts.csv` |
| `17` | `Bagaimana` | 50 | `C29` — **`BAGAIMANA`** | **COCOK (`9/10`)** |
| `18` | `Merah` | 50 | — | Tidak ada di `concepts.csv` |
| `19` | `Kuning` | 50 | — | Tidak ada di `concepts.csv` |
| `20` | `Hijau` | 50 | — | Tidak ada di `concepts.csv` |
| `21` | `Hitam` | 50 | — | Tidak ada di `concepts.csv` |
| `22` | `Dengar` | 50 | — | Tidak ada di `concepts.csv` |
| `23` | `Berangkat` | 50 | — | Tidak ada di `concepts.csv` |
| `24` | `Datang` | 50 | — | Tidak ada di `concepts.csv` |
| `25` | `Teman` | 50 | `C08` — **`TEMAN`** | **COCOK (`10/10`)** |
| `26` | `Keluarga` | 50 | — | Tidak ada di `concepts.csv` |
| `27` | `Rumah` | 50 | — | Tidak ada di `concepts.csv` |
| `28` | `Pagi` | 50 | — | Tidak ada di `concepts.csv` |
| `29` | `Siang` | 50 | — | Tidak ada di `concepts.csv` |
| `30` | `Sore` | 50 | — | Tidak ada di `concepts.csv` |
| `31` | `Malam` | 50 | — | Tidak ada di `concepts.csv` |

**Temuan Kritis Kosakata BISINDO:**
1. **Irisan Langsung (`10 / 32` gloss = `500` video):** Hanya **10 gloss** pada `WL-BISINDO` (`BELAJAR`, `MAAF`, `SAYA`, `TERIMA_KASIH`, `APA`, `SIAPA`, `KAPAN`, `DIMANA`, `BAGAIMANA`, `TEMAN`) yang beririsan langsung dengan 32 konsep kelas di [`data/bridge/concepts.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/bridge/concepts.csv).
2. **22 Gloss `WL-BISINDO` di Luar `concepts.csv` (`1.100` video):** `AIR`, `BERANGKAT`, `CARI`, `DATANG`, `DENGAR`, `HARI`, `HIJAU`, `HITAM`, `INGAT`, `KELUARGA`, `KUNING`, `LAGI`, `MAKAN`, `MALAM`, `MENGAPA`, `MERAH`, `MOTOR`, `PAGI`, `RUMAH`, `SIANG`, `SORE`, `TULI`.
3. **22 Konsep Kelas `concepts.csv` yang Belum Ada di `WL-BISINDO`:** `ADA`, `BACA`, `BAIK`, `BELUM`, `BENAR`, `BISA`, `BUKU`, `GURU`, `HALO`, `JAWAB`, `KAMU`, `KELAS`, `MAU`, `PAHAM`, `SALAH`, `SEKOLAH`, `SUDAH`, `TANYA`, `TIDAK`, `TOLONG`, `TUGAS`, `TULIS` (kosakata spesifik ruang kelas ini memang dirancang untuk dipenuhi melalui rekaman `SignBridge-Kelas` atau penyelarasan ruang label model).
4. *(Catatan tambahan: [`DATA_CARD.md`](file:///C:/Users/PC/Downloads/Semester%205/ML/DATA_CARD.md#L100-L136) di repositori juga memuat daftar 32 gloss ketiga yang berbeda lagi [`MAKAN`, `MINUM`, `TIDUR`, dst.], sehingga sumber kebenaran label `WL-BISINDO` wajib mengacu pada pemetaan `label0..label31` resmi pembuat dataset, bukan tabel di `DATA_CARD.md`).*

### 6.3 Ringkasan Distribusi Kelas Modalitas Lainnya

- **Image — BISINDO Alphabet (`data/raw/image/bisindo_alphabet/A..Z`):** Seluruh **`26` kelas huruf `A` s/d `Z`** tersedia lengkap (`4.466` citra RGB `224x224`, rentang `165` s/d `174` citra per kelas; rata-rata `171,8` citra/kelas).
- **Video — FSL-105 (`data/raw/video/fsl_105/` — Bahasa Isyarat Filipina):** **`105` kelas** (`id 0..104` di `labels.csv`, total `2.130` klip `.MOV`: `1.704` di `train.csv` dan `426` di `test.csv`).

---

## 7. Hasil Validasi Dataset Audio

Pemeriksaan ulang dilakukan terhadap seluruh berkas di [`data/audio/`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio):

1. **Google FLEURS Konfigurasi `id_id` (`data/audio/fleurs/id_id/`):**
   - **Metadata TSV:**
     - [`train.tsv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/fleurs/id_id/train.tsv): `1.499.201` byte | `2.579` baris unik | SHA-256 `5a4285ed00caff57f9dce155c7c1f636cfb9c322a795d55e04d98d4b7696fcec`
     - [`dev.tsv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/fleurs/id_id/dev.tsv): `200.236` byte | `350` baris unik | SHA-256 `8377bf6d8738491b7b0672de47e42123ce07b069a0db920ab6300e3ecce02c18`
     - [`test.tsv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/fleurs/id_id/test.tsv): `408.796` byte | `687` baris unik | SHA-256 `824cad6367283d95f545911eec051c488c182baa13a63227c6330af3c8f80741`
     - **Kebocoran Nama File Antar-Split TSV:** `0` overlap antara `train.tsv`, `dev.tsv`, dan `test.tsv`.
   - **Arsip & File WAV Fisik FLEURS:**
     - [`audio/dev.tar.gz`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/fleurs/id_id/audio/dev.tar.gz): **FOUND** (`220.586.217` byte, SHA-256 `74e5f1c8676a321dc4c34944b171846d40923dabe765a767d8dbc2f56cac3142`).
     - `audio/dev/*.wav`: **FOUND — tepat `350` berkas `.wav` fisik** (`267.099.980` byte total).
     - **Validasi Teknis Audio (`350 / 350` WAV):** Seluruh `350` file memiliki header `RIFF/WAVE` valid, `wFormatTag = 3` (`32-bit IEEE float`), **sample rate `16.000 Hz`** (`100%` seragam), **mono (`1` kanal)**, **`0` file kosong (`0` byte)**, **`0` file rusak**, **`0` duplikat SHA-256**, dan **durasi total `4.173,12 detik` (`69,55 menit`)**.
     - **Kesesuaian `dev.tsv` $\leftrightarrow$ WAV Fisik:** `350 / 350` nama file di `dev.tsv` cocok 100% dengan file `.wav` di `audio/dev/` (`missing = 0`, `extra = 0`).
     - `audio/train.tar.gz` (`2.579` klip) & `audio/test.tar.gz` (`687` klip): **`NOT FOUND`** (belum diunduh).

2. **Rekaman Audio Kelas Bahasa Indonesia ([`data/audio/metadata.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/metadata.csv)):**
   - **File CSV:** **FOUND** (`5.334` byte, SHA-256 `15025bf52801864631aaf90df9ebfc79d4863af955f338930d2dffee2e47460c`, utuh sesuai Git `HEAD`).
   - **Struktur Kolom:** `60` baris dengan kolom `['file', 'text', 'speaker']` (contoh: `wavs/id_001.wav`, speaker `S01`..`S03`). Tidak terdapat kolom eksplisit `language`, `sample_rate`, maupun `duration` di dalam CSV.
   - **Ketersediaan File WAV Fisik (`data/audio/wavs/id_001.wav`..`id_060.wav`):** **`NOT FOUND` (`0` ditemukan, `60` hilang)**.

3. **Rekaman Audio Kelas Bahasa Filipino ([`data/audio/metadata_fil.csv`](file:///C:/Users/PC/Downloads/Semester%205/ML/data/audio/metadata_fil.csv)):**
   - **File CSV:** **FOUND** (`1.849` byte, SHA-256 `72cb11744391bbe0497ed0c5a04ce5018d97778a90014de5ebfc6c8528536b6d`, utuh sesuai Git `HEAD`).
   - **Struktur Kolom:** `24` baris dengan kolom `['file', 'text', 'speaker']` (contoh: `wavs_fil/fil_001.wav`). Tidak terdapat kolom `language`, `sample_rate`, maupun `duration`.
   - **Ketersediaan File WAV Fisik (`data/audio/wavs_fil/fil_001.wav`..`fil_024.wav`):** **`NOT FOUND` (`0` ditemukan, `24` hilang)**.

---

## 8. Hasil Pemeriksaan Duplikasi, Integritas Kriptografis, dan Kebocoran Split

Pemeriksaan hash SHA-256 penuh dijalankan terhadap seluruh berkas media dan teks pada keempat modalitas:

| Dataset | Jumlah File Diperiksa | File Rusak / `0` Byte | Hash SHA-256 Unik | Duplikat Dalam Kelas | Duplikat Lintas Kelas | Kebocoran Antar-Split (`train`/`val`/`test`) |
|---|---:|---:|---:|---:|---:|---|
| **Video: `WL-BISINDO` (`archive.zip`)** | `1.600` `.mp4` | **`0`** | `1.600` | **`0`** | **`0`** | Belum memiliki file split; perhatian pada `signer0` (hanya ada di `label0..11`) |
| **Video: `FSL-105` (`clips/*.MOV`)** | `2.130` `.MOV` | **`0`** | `2.126` | **`0`** | **`4` pasang** (`8` file) | **`2` pasang bocor antara `train.csv` & `test.csv`** *(bawaan dataset Mendeley)* |
| **Image: `BISINDO Alphabet A–Z`** | `4.466` `.jpg`/`.jpeg` | **`0`** | `4.464` | **`0`** | **`2` pasang** (`4` file) | **`0` kebocoran di pipeline** (`scripts/crop_hands.py` otomatis menyaring `ambiguous_cross_class_shas`) |
| **Audio: `FLEURS id_id` (`dev`)** | `350` `.wav` | **`0`** | `350` | **`0`** | **`0`** | **`0` overlap** nama file antar `train.tsv`, `dev.tsv`, `test.tsv` |
| **Text: `train`/`val`/`test_manual`/`Tatoeba`** | `5` berkas teks (`28.723` baris kalimat) | **`0`** | Utuh 100% sesuai manifest | **`0`** | — | **`0` overlap** antara `train.tsv` (`170`), `val.tsv` (`30`), dan `test_manual.tsv` (`105`) |

### Rincian File Duplikat Lintas Kelas yang Teridentifikasi (Bawaan Sumber Publik)

1. **Pada `BISINDO Alphabet A–Z` (`2` pasang SHA-256 identik lintas kelas):**
   - **Pasangan 1 (`7.041 B`, SHA-256 `99c4a1565f4c49c05be9badc4be2836d9353e35acd49fe2e76dc08aa86d46e53`):**
     `B/B_polos gelap_Iphone_13promax.jpg` $\equiv$ `E/E_polos gelap_Iphone_13promax.jpg`
   - **Pasangan 2 (`5.119 B`, SHA-256 `a99273b2ca82794cb612bc3ace480521ae73d2cb41d6f406bbc14d586d095aa0`):**
     `D/D_Polos Gelap_iPhone_XR.jpeg` $\equiv$ `P/P_Polos Gelap_iPhone_XR.jpeg`
   *(Ditangani secara aman oleh [`scripts/crop_hands.py` baris 320–340](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L320-L340) yang mendeteksi `ambiguous_cross_class_shas` dan mengecualikan ke-4 file ambigu tersebut saat membangun manifest).*

2. **Pada `FSL-105` (`4` pasang SHA-256 identik lintas kelas, `2` di antaranya bocor `train` $\leftrightarrow$ `test`):**
   - **Pasangan 1 — BOCOR `train` vs `test`** (SHA-256 `2894410d8559ff07b0a2e17cf6d6189ce3faf2ed867e955825441e8ff8108845`):
     `clips/23/6.MOV` (`23 = FOUR`, `train.csv`) $\equiv$ `clips/26/7.MOV` (`26 = SEVEN`, `test.csv`)
   - **Pasangan 2 — BOCOR `test` vs `train`** (SHA-256 `c329a443c221550baa104bfb20ca93fc1f13c2b191467a96f4c59b90137b8ca5`):
     `clips/23/8.MOV` (`23 = FOUR`, `test.csv`) $\equiv$ `clips/26/9.MOV` (`26 = SEVEN`, `train.csv`)
   - **Pasangan 3 — Sesama `train.csv`** (SHA-256 `8349f35b80868cafa419d753f28f87a137d9753825889ff63b9dd16de8b87`):
     `clips/57/9.MOV` (`57 = GRANDMOTHER`, `train.csv`) $\equiv$ `clips/60/9.MOV` (`60 = COUSIN`, `train.csv`)
   - **Pasangan 4 — Sesama `train.csv`** (SHA-256 `755a474858b2fc54641336d60c69a8026b7e33d65a4f2c86cae8a424d7865c17`):
     `clips/58/6.MOV` (`58 = UNCLE`, `train.csv`) $\equiv$ `clips/61/6.MOV` (`61 = PARENTS`, `train.csv`)
   *(Sesuai batasan audit, tidak ada file atau CSV asli yang diubah; temuan ini wajib disaring di tingkat loader/ekstraktor saat eksperimen FSL dijalankan).*

---

## 9. Dataset dan Artefak yang Masih Belum Tersedia (`NOT FOUND`)

Berdasarkan pemeriksaan fisik aktual, daftar item yang masih **`NOT FOUND`** di workspace adalah:

1. **Video Rekaman Mandiri `SignBridge-Kelas` (`BISINDO`):** **`NOT FOUND`** (`0 / 960` klip rekaman tim $3\text{ signer} \times 32\text{ gloss} \times 10\text{ take}$; total video BISINDO saat ini `1.600` dari target modul $\ge 3.000$).
2. **Video Fisik `WLASL-300` (`ASL` Pretraining):** **`NOT FOUND`** (`0` berkas video fisik untuk `300` gloss / `5.117` entri pada `WLASL_300_manifest.json`).
3. **Video Referensi Jembatan (`data/ref_signs/bisindo/*.mp4` & `data/ref_signs/fsl/*.mp4`):** **`NOT FOUND`** (`0 / 64` berkas video referensi yang dirujuk oleh `data/bridge/concepts.csv`).
4. **File Audio WAV Rekaman Kelas Bahasa Indonesia (`data/audio/wavs/id_001.wav`..`id_060.wav`):** **`NOT FOUND`** (`0 / 60` berkas `.wav` fisik).
5. **File Audio WAV Rekaman Kelas Bahasa Filipino (`data/audio/wavs_fil/fil_001.wav`..`fil_024.wav`):** **`NOT FOUND`** (`0 / 24` berkas `.wav` fisik).
6. **Arsip Audio Split `train` & `test` Google FLEURS `id_id` (`audio/train.tar.gz` & `audio/test.tar.gz`):** **`NOT FOUND`** (baru `dev.tar.gz` / `350` WAV yang tersedia secara fisik; `2.579` WAV `train` dan `687` WAV `test` belum diunduh).
7. **Hasil Preprocessing & Manifest Video Utama (`data/keypoints/`, `data/rgb_feats/`, `data/manifest.csv`):** **`NOT FOUND`** (belum dijalankan karena preprocessing massal ditahan sesuai instruksi).

---

## 10. Kompatibilitas Dataset dengan Pipeline Saat Ini

Pengujian keterbacaan terhadap fungsi loader dan skrip preprocessing saat ini (tanpa mengubah kode) menunjukkan status berikut:

| Modality & Dataset | Loader / Skrip Saat Ini | Status Kompatibilitas | Temuan Teknis Spesifik |
|---|---|---|---|
| **Video — `WL-BISINDO` (`archive.zip`)** | [`scripts/extract_keypoints.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py) $\rightarrow$ [`SignDataset`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py) | **`BELUM KOMPATIBEL LANGSUNG` (3 Penghalang Teknis + 1 Keputusan Kosakata)** | 1. **Arsip belum diekstrak:** `discover_video_files()` hanya memindai `.mp4/.webm/.mov`, bukan isi `.zip`.<br>2. **Struktur flat & pemetaan `label0..31`:** `resolve_video_gloss_and_label()` pada baris 131–146 mewajibkan nama subfolder induk berupa salah satu dari `BISINDO_32_GLOSSES`. File flat `signer0_label0_sample1.mp4` langsung memicu `ValueError`. Selain itu, `22/32` gloss asli `WL-BISINDO` berada di luar `BISINDO_32_GLOSSES` (`concepts.csv`), yang saat ini ditolak oleh validasi baris 136–141.<br>3. **Bug Regex Batas Kata (`\b`) di `extract_signer_id()` (baris 224):** Pola `r"\b(s\d{1,3}|signer[_-]?\d{1,3})\b"` **gagal** mengenali `signer0` pada `signer0_label0_sample1.mp4` karena karakter `_` setelah `0` dianggap karakter kata (`\w`), sehingga tidak ada batas kata `\b`! Akibatnya `extract_signer_id()` mengembalikan `'unannotated'` alih-alih `'SIGNER0'`, yang akan merusak pembagian Signer-Independent (`SI`).<br>4. **Dependency belum terpasang:** `opencv-python` (`cv2`) dan `mediapipe` belum terpasang di `Python311`. |
| **Video — `FSL-105` (`clips/*.MOV`)** | [`scripts/extract_keypoints.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py) (`--source fsl`) | **`KOMPATIBEL STRUKTUR` (Perlu Penyaringan 4 Duplikat & Dependency)** | `discover_video_files()`, `load_optional_labels_csv()`, dan `load_official_split_map()` mendukung `.MOV`, `labels.csv` (`105` kelas), dan `train.csv`/`test.csv`. Namun perlu penyaringan SHA-256 agar 2 pasang video identik (`FOUR` vs `SEVEN`) tidak bocor antara `train` dan `test`, serta instalasi `cv2` + `mediapipe` + perbaikan `signbridge/train.py`. |
| **Image — `BISINDO Alphabet A–Z`** | [`scripts/crop_hands.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py) $\rightarrow$ [`FingerspellDataset`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/image/train_image.py) | **`KOMPATIBEL 100% (`READY`)`** | Teruji membaca struktur `A`..`Z` (`.jpg` & `.jpeg`), otomatis membuang 2 pasang duplikat lintas kelas (`B==E`, `D==P`), dan memvalidasi 0 kebocoran split. Hanya membutuhkan `torch` saat tahap training neural. |
| **Audio — `FLEURS id_id` (`dev`) & `metadata.csv`** | [`load_wav_waveform()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py) & `load_audio_dataset_records()` | **`KOMPATIBEL FORMAT WAV` / `PERLU ADAPTER TSV FLEURS`** | Uji langsung `load_wav_waveform()` pada WAV `32-bit IEEE float` (`fmt_tag=3`) milik FLEURS **BERHASIL (`PASS`, `shape=(136320,), dtype=float32, sr=16000`)**. Namun `configs/asr_*.yaml` saat ini menunjuk ke `data/audio/metadata.csv` (yang WAV kelasnya `NOT FOUND`), sedangkan FLEURS memakai format TSV 7 kolom tanpa header sehingga memerlukan konversi manifest CSV khusus FLEURS (tanpa menyentuh `metadata.csv` kelas). |
| **Text — `Tatoeba` & Korpus Kelas** | [`scripts/build_text_corpus.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/build_text_corpus.py) $\rightarrow$ [`signbridge/text/train_text.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py) | **`KOMPATIBEL 100% (`READY`)`** | Seluruh file `train.tsv`, `val.tsv`, `test_manual.tsv`, `kelas_sentences.txt`, dan `tatoeba/ind_sentences.tsv` langsung terbaca tanpa error dan bebas kebocoran split. |

---

## 11. Rekomendasi Langkah Selanjutnya

Sebelum menjalankan preprocessing atau pelatihan apa pun, disarankan urutan langkah berikut setelah mendapat persetujuan Anda:

1. **Keputusan Skema Kosakata Video BISINDO (`WL-BISINDO` vs `concepts.csv`):**
   - **Opsi A (Dua Tahap — Direkomendasikan sesuai arsitektur transfer learning):** Gunakan seluruh **`1.600` video (`32` kelas asli `WL-BISINDO`)** dengan manifest `labels_wlbisindo.csv` resmi (`source="wl_bisindo"`) untuk melatih representasi dasar video BISINDO nyata (dan protokol `SD` vs `SI` pada `signer0..signer4`), sementara **10 kelas irisan (`500` video)** + rekaman tim `SignBridge-Kelas` digunakan untuk fine-tuning pada 32 konsep kelas `concepts.csv`.
   - **Opsi B (Subset Irisan Kelas):** Ekstrak hanya `10` kelas `WL-BISINDO` (`500` video) yang cocok langsung dengan `concepts.csv`, sambil menunggu perekaman `22` konsep kelas sisanya.
2. **Perbaikan Kecil & Terarah pada Pipeline Sebelum Ekstraksi:**
   - Perbaiki regex `extract_signer_id()` di [`scripts/extract_keypoints.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py#L224) agar mengenali pola `signer0_label0_sample1.mp4` (`SIGNER0`..`SIGNER4`) secara akurat dan tambahkan dukungan pembacaan pola `label<ID>` + pengecekan anti-kebocoran SHA-256 lintas split (untuk menangani 2 pasang duplikat `FSL-105`).
   - Selesaikan perbaikan pre-existing yang telah diidentifikasi pada Audit Tahap A.2 (`signbridge/train.py` baris 268–278 & bug `this.recognizer.buffer` pada perekam web `web/js/app.js:754`).
3. **Ekstraksi Aman `WL-BISINDO`:**
   - Setelah disetujui, ekstrak `data/raw/video/wl_bisindo/archive.zip` ke subfolder terpisah `data/raw/video/wl_bisindo/videos/` tanpa menghapus `archive.zip` asli (`0%` risiko overwrite), serta tambahkan entri `WL-BISINDO` ke `data/DATASET_DOWNLOAD_MANIFEST.csv` dengan lisensi akurat **`CC BY-NC 4.0`**.
4. **Pemenuhan Lingkungan & Data Kelas yang Masih Kurang:**
   - Pasang dependency `torch`, `opencv-python`, `mediapipe`, `onnxruntime`, `pytest`, `fastapi`, `httpx`, `sqlalchemy`.
   - Unduh `train.tar.gz` dan `test.tar.gz` untuk `FLEURS id_id` jika ingin melatih ASR penuh pada FLEURS, serta lakukan perekaman suara kelas asli (`60` WAV Indonesia & `24` WAV Filipino) dan video `SignBridge-Kelas`.

