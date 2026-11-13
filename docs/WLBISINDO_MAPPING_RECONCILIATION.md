# DOKUMENTASI REKONSILIASI PEMETAAN LABEL WL-BISINDO (TAHAP A.2.4)

**Tanggal Audit:** 7 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch:** `feature/dataset-acquisition`  
**Status Evaluasi:** `PASS (MAPPING RECONCILED & 100% CONFIRMED)`

---

## 1. Latar Belakang Konflik Pemetaan

Pada evaluasi dan integrasi dataset video Word-Level BISINDO (**WL-BISINDO**), ditemukan adanya diskrepansi antara dua kandidat pemetaan label (gloss):
- **Mapping A:** Pemetaan yang telah didefinisikan pada modul metadata [`signbridge/data/video_metadata.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py), manifest ekstraksi [`data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv), dan dokumen perbaikan pipeline [`docs/PIPELINE_VIDEO_WLBISINDO_FIX.md`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/PIPELINE_VIDEO_WLBISINDO_FIX.md).
- **Mapping B:** Pemetaan yang tercantum dalam teks prompt instruksi awal pengguna dan sempat tercantum pada tabel ringkasan tanggapan audit sebelumnya.

Tujuan audit ini adalah menyelidiki sumber asli primer dataset, membuktikan secara objektif pemetaan mana yang valid secara akademik/teknis, serta mencegah terjadinya salah label pada 1.600 video dan 32 kelas.

---

## 2. Perbandingan Mapping A dan Mapping B

| Label ID | Mapping A (Audit & Metadata Repo) | Mapping B (Teks Prompt Alternatif) |
|:---:|:---|:---|
| 0 | AIR | AIR |
| 1 | BELAJAR | BELAJAR |
| 2 | CARI | CARI |
| 3 | HARI | HARI |
| 4 | INGAT | INGAT |
| 5 | LAGI | LAGI |
| 6 | MAAF | MAAF |
| 7 | MAKAN | MINUM |
| 8 | MOTOR | PAGI |
| 9 | SAYA | RUMAH |
| 10 | TERIMA_KASIH | SAYA |
| 11 | TULI | TERIMA_KASIH |
| 12 | APA | TIDUR |
| 13 | SIAPA | APA |
| 14 | KAPAN | SIAPA |
| 15 | DIMANA | KAPAN |
| 16 | MENGAPA | DIMANA |
| 17 | BAGAIMANA | BAGAIMANA |
| 18 | MERAH | BISA |
| 19 | KUNING | TIDAK_BISA |
| 20 | HIJAU | SUKA |
| 21 | HITAM | TIDAK_SUKA |
| 22 | DENGAR | MAU |
| 23 | BERANGKAT | TIDAK_MAU |
| 24 | DATANG | SUDAH |
| 25 | TEMAN | BELUM |
| 26 | KELUARGA | SENANG |
| 27 | RUMAH | SEDIH |
| 28 | PAGI | SEKOLAH |
| 29 | SIANG | TEMAN |
| 30 | SORE | GURU |
| 31 | MALAM | KELUARGA |

---

## 3. Investigasi Sumber dan Bukti Provenance

Pemeriksaan fisik dilakukan terhadap seluruh sumber data internal repository dan repositori eksternal resmi pencipta dataset:

### 3.1 Pemeriksaan Fisik Internal Arsip
1. Berkas arsip [`data/raw/video/wl_bisindo/archive.zip`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/archive.zip) diinspeksi struktur isinya.
2. Hasil: Arsip berukuran `2.126.878.088` bytes berisi tepat 1.600 berkas `.mp4` dengan penamaan `signer<S>_label<L>_sample<K>.mp4`. **Tidak terdapat file README, label.csv, maupun metadata TXT/JSON di dalam arsip ZIP**.

### 3.2 Bukti Repositori Resmi Pembuat Dataset (Primary Source)
1. **Identitas Makalah Ilmiah:** *"Word-Level BISINDO: A Novel Video Indonesian Sign Language Dataset and Baseline Methods"* (2025).
2. **Peneliti / Pencipta Dataset:** Grace Oktaviani Kindy, Glenn Leonali, Henry Lucky.
3. **Repositori Kode dan Baseline Resmi:** GitHub [`AceKinnn/WL-BISINDO`](https://github.com/AceKinnn/WL-BISINDO).
4. **Halaman Publikasi Dataset Kaggle:** [`glennleonali/wl-bisindo`](https://www.kaggle.com/datasets/glennleonali/wl-bisindo).
5. **Bukti Anotasi Label Resmi pada Repositori Pembuat:**
   Dalam repositori resmi `AceKinnn/WL-BISINDO`, pemetaan kamus label 0–31 didefinisikan secara eksplisit sebagai berikut:
   - `0: Air (Water)`
   - `1: Belajar (Learn)`
   - `2: Cari (Search)`
   - `3: Hari (Day)`
   - `4: Ingat (Remember)`
   - `5: Lagi (Again)`
   - `6: Maaf (Sorry)`
   - `7: Makan (Eat)`
   - `8: Motor (Motorcycle)`
   - `9: Saya (I)`
   - `10: Terima kasih (Thank you)`
   - `11: Tuli (Deaf)`
   - `12: Apa (What)`
   - `13: Siapa (Who)`
   - `14: Kapan (When)`
   - `15: Di mana (Where)`
   - `16: Mengapa (Why)`
   - `17: Bagaimana (How)`
   - `18: Merah (Red)`
   - `19: Kuning (Yellow)`
   - `20: Hijau (Green)`
   - `21: Hitam (Black)`
   - `22: Dengar (Hear)`
   - `23: Berangkat (Depart)`
   - `24: Datang (Come)`
   - `25: Teman (Friend)`
   - `26: Keluarga (Family)`
   - `27: Rumah (House)`
   - `28: Pagi (Morning)`
   - `29: Siang (Noon)`
   - `30: Sore (Afternoon)`
   - `31: Malam (Night)`

---

## 4. Tabel Perbandingan dan Verifikasi Status 32 Label

| Label ID | Mapping A (Resmi) | Mapping B (Hipotetis) | Bukti Sumber Primer (`AceKinnn/WL-BISINDO`) | Status Verifikasi |
|:---:|:---|:---|:---|:---:|
| 0 | AIR | AIR | `0: Air (Water)` | `CONFIRMED` |
| 1 | BELAJAR | BELAJAR | `1: Belajar (Learn)` | `CONFIRMED` |
| 2 | CARI | CARI | `2: Cari (Search)` | `CONFIRMED` |
| 3 | HARI | HARI | `3: Hari (Day)` | `CONFIRMED` |
| 4 | INGAT | INGAT | `4: Ingat (Remember)` | `CONFIRMED` |
| 5 | LAGI | LAGI | `5: Lagi (Again)` | `CONFIRMED` |
| 6 | MAAF | MAAF | `6: Maaf (Sorry)` | `CONFIRMED` |
| 7 | MAKAN | MINUM | `7: Makan (Eat)` — bukan Minum | `CONFIRMED (A)` / `CONFLICT (B)` |
| 8 | MOTOR | PAGI | `8: Motor (Motorcycle)` — bukan Pagi | `CONFIRMED (A)` / `CONFLICT (B)` |
| 9 | SAYA | RUMAH | `9: Saya (I)` — bukan Rumah | `CONFIRMED (A)` / `CONFLICT (B)` |
| 10 | TERIMA_KASIH | SAYA | `10: Terima kasih (Thank you)` — bukan Saya | `CONFIRMED (A)` / `CONFLICT (B)` |
| 11 | TULI | TERIMA_KASIH | `11: Tuli (Deaf)` — bukan Terima Kasih | `CONFIRMED (A)` / `CONFLICT (B)` |
| 12 | APA | TIDUR | `12: Apa (What)` — bukan Tidur | `CONFIRMED (A)` / `CONFLICT (B)` |
| 13 | SIAPA | APA | `13: Siapa (Who)` — bukan Apa | `CONFIRMED (A)` / `CONFLICT (B)` |
| 14 | KAPAN | SIAPA | `14: Kapan (When)` — bukan Siapa | `CONFIRMED (A)` / `CONFLICT (B)` |
| 15 | DIMANA | KAPAN | `15: Di mana (Where)` — bukan Kapan | `CONFIRMED (A)` / `CONFLICT (B)` |
| 16 | MENGAPA | DIMANA | `16: Mengapa (Why)` — bukan Di mana | `CONFIRMED (A)` / `CONFLICT (B)` |
| 17 | BAGAIMANA | BAGAIMANA | `17: Bagaimana (How)` | `CONFIRMED` |
| 18 | MERAH | BISA | `18: Merah (Red)` — bukan Bisa | `CONFIRMED (A)` / `CONFLICT (B)` |
| 19 | KUNING | TIDAK_BISA | `19: Kuning (Yellow)` — bukan Tidak Bisa | `CONFIRMED (A)` / `CONFLICT (B)` |
| 20 | HIJAU | SUKA | `20: Hijau (Green)` — bukan Suka | `CONFIRMED (A)` / `CONFLICT (B)` |
| 21 | HITAM | TIDAK_SUKA | `21: Hitam (Black)` — bukan Tidak Suka | `CONFIRMED (A)` / `CONFLICT (B)` |
| 22 | DENGAR | MAU | `22: Dengar (Hear)` — bukan Mau | `CONFIRMED (A)` / `CONFLICT (B)` |
| 23 | BERANGKAT | TIDAK_MAU | `23: Berangkat (Depart)` — bukan Tidak Mau | `CONFIRMED (A)` / `CONFLICT (B)` |
| 24 | DATANG | SUDAH | `24: Datang (Come)` — bukan Sudah | `CONFIRMED (A)` / `CONFLICT (B)` |
| 25 | TEMAN | BELUM | `25: Teman (Friend)` — bukan Belum | `CONFIRMED (A)` / `CONFLICT (B)` |
| 26 | KELUARGA | SENANG | `26: Keluarga (Family)` — bukan Senang | `CONFIRMED (A)` / `CONFLICT (B)` |
| 27 | RUMAH | SEDIH | `27: Rumah (House)` — bukan Sedih | `CONFIRMED (A)` / `CONFLICT (B)` |
| 28 | PAGI | SEKOLAH | `28: Pagi (Morning)` — bukan Sekolah | `CONFIRMED (A)` / `CONFLICT (B)` |
| 29 | SIANG | TEMAN | `29: Siang (Noon)` — bukan Teman | `CONFIRMED (A)` / `CONFLICT (B)` |
| 30 | SORE | GURU | `30: Sore (Afternoon)` — bukan Guru | `CONFIRMED (A)` / `CONFLICT (B)` |
| 31 | MALAM | KELUARGA | `31: Malam (Night)` — bukan Keluarga | `CONFIRMED (A)` / `CONFLICT (B)` |

---

## 5. Kesimpulan Rekonsiliasi dan Asal Muasal Konflik

1. **Mapping A adalah Pemetaan Resmi Tunggal yang Sah (`100% CONFIRMED`).**
   Seluruh 32 label terbukti identik dengan taksonomi publikasi resmi Kindy et al. (2025) pada repositori `AceKinnn/WL-BISINDO`.
2. **Mapping B Dinyatakan Invalid / Ditolak (`UNVERIFIED / REJECTED`).**
   Mapping B memuat istilah kosa kata ruang kelas (seperti `MINUM`, `TIDUR`, `BISA`, `TIDAK_BISA`, `SUKA`, `SEKOLAH`, `GURU`) yang berasal dari daftar konsep percakapan umum, bukan isi dari dataset WL-BISINDO asli.
3. **Kondisi Manifest dan Kode Repositori:**
   - [`signbridge/data/video_metadata.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/signbridge/data/video_metadata.py) telah menggunakan **Mapping A** sejak awal pembuatan pada Tahap A.2.2.
   - [`data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_extraction_manifest.csv) telah menggunakan **Mapping A** secara konsisten.
   - Dokumen [`docs/WLBISINDO_EXTRACTION_VALIDATION.md`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/WLBISINDO_EXTRACTION_VALIDATION.md) pada bagian Section 9 telah memuat Mapping A; anomali hanya sempat terjadi pada teks ringkasan respons percakapan yang mengulang tabel prompt. Dengan rekonsiliasi ini, integritas metadata terkonfirmasi utuh tanpa kontradiksi.

---

## 6. Analisis Overlap dengan Konsep SignBridge (`data/bridge/concepts.csv`)

Dengan mengonfirmasi Mapping A, pencocokan eksak dengan taksonomi konsep SignBridge ([`data/bridge/concepts.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/bridge/concepts.csv)) menghasilkan tepat **10 kelas beririsan** (500 video) dan **22 kelas non-overlap** (1.100 video):

### 10 Kelas Beririsan Langsung:
| Label ID | Gloss Resmi WL-BISINDO | Concept ID | Kategori SignBridge | Jumlah Video |
|:---:|:---|:---:|:---|:---:|
| 1 | BELAJAR | `C15` | Aktivitas | 50 |
| 6 | MAAF | `C03` | Sapaan | 50 |
| 9 | SAYA | `C05` | Subjek | 50 |
| 10 | TERIMA_KASIH | `C02` | Sapaan | 50 |
| 12 | APA | `C25` | Tanya | 50 |
| 13 | SIAPA | `C26` | Tanya | 50 |
| 14 | KAPAN | `C28` | Tanya | 50 |
| 15 | DIMANA | `C27` | Tanya | 50 |
| 17 | BAGAIMANA | `C29` | Tanya | 50 |
| 25 | TEMAN | `C08` | Subjek | 50 |
| **Total** | **10 Kelas** | - | - | **500 Video** |

### 22 Kelas Non-Overlap (Pretraining Representation Pool):
- Label 0: `AIR`
- Label 2: `CARI`
- Label 3: `HARI`
- Label 4: `INGAT`
- Label 5: `LAGI`
- Label 7: `MAKAN`
- Label 8: `MOTOR`
- Label 11: `TULI`
- Label 16: `MENGAPA`
- Label 18: `MERAH`
- Label 19: `KUNING`
- Label 20: `HIJAU`
- Label 21: `HITAM`
- Label 22: `DENGAR`
- Label 23: `BERANGKAT`
- Label 24: `DATANG`
- Label 26: `KELUARGA`
- Label 27: `RUMAH`
- Label 28: `PAGI`
- Label 29: `SIANG`
- Label 30: `SORE`
- Label 31: `MALAM`
- **Total:** 22 kelas $\times$ 50 video = **1.100 Video**.

---

## 7. Status Distribusi Signer dan Label

- **Keseimbangan Kelas:** Seluruh 32 kelas memiliki tepat 50 video ($32 \times 50 = 1.600$).
- **Distribusi Signer:**
  - `signer0`: 120 video (hanya label 0–11, masing-masing 10 video).
  - `signer1`: 420 video (label 0–11: 10 video; label 12–31: 15 video).
  - `signer2`: 420 video (label 0–11: 10 video; label 12–31: 15 video).
  - `signer3`: 320 video (label 0–11: 10 video; label 12–31: 10 video).
  - `signer4`: 320 video (label 0–11: 10 video; label 12–31: 10 video).
  - Total: Tepat 1.600 video.
- **Konsistensi Nama Berkas:** 1.600 berkas sesuai dengan pola `signer<S>_label<L>_sample<K>.mp4`.

