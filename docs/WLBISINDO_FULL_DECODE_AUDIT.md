# LAPORAN FULL VIDEO DECODE AUDIT WL-BISINDO (TAHAP A.2.4 & A.2.4.1)

**Tanggal Audit:** 7 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch:** `feature/dataset-acquisition`  
**Lokasi Decoder Executable:** `C:\Tools\ffmpeg\bin\`  
**Status Evaluasi Akhir:** **`PASS (100% FULL_DECODE_VALID)`**

---

## 1. Riwayat Status Audit

- **Audit A.2.4 Awal:** Berstatus `BLOCKED (DECODER NOT AVAILABLE)` karena modul `ffmpeg`, `ffprobe`, dan `opencv-python` belum terpasang pada environment Windows.
- **Audit A.2.4.1 Lanjutan:** Pengguna memberikan izin resmi untuk memasang binary FFmpeg 9.0.2 pada direktori lokal terisolasi (`C:\Tools\ffmpeg\bin\`). Seluruh 1.600 video berhasil didekode frame-by-frame hingga selesai dengan exit code 0. Status evaluasi dinaikkan menjadi **`PASS`**.

---

## 2. Tool Decoder dan Lingkungan Eksekusi

| Komponen | Spesifikasi & Versi | Status |
|---|---|:---:|
| **FFmpeg Executable** | `C:\Tools\ffmpeg\bin\ffmpeg.exe` (Versi: `9.0.2-essentials_build-www.gyan.dev`) | `PASS` |
| **FFprobe Executable** | `C:\Tools\ffmpeg\bin\ffprobe.exe` (Versi: `9.0.2-essentials_build-www.gyan.dev`) | `PASS` |
| **Sumber Instalasi** | `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip` | `PASS` |
| **SHA-256 Paket Unduhan** | `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` | `PASS` |
| **Dukungan H.264 / AVC** | `VFS..D h264` (Direct Software Decoding via libavcodec) | `PASS` |
| **Dukungan H.265 / HEVC** | `VFS..D hevc` (Direct Software Decoding via libavcodec) | `PASS` |

Dokumentasi lengkap proses instalasi dicatat pada:
[`docs/FFMPEG_INSTALLATION_REPORT.md`](file:///c:/Users/PC/Downloads/Semester%205/ML/docs/FFMPEG_INSTALLATION_REPORT.md).

---

## 3. Hasil Pilot Decode (10 Video Sampel Representatif)

Sebelum audit massal, dilakukan pilot decoding terhadap 10 sampel video yang bervariasi (mencakup AVC, HEVC, resolusi Full HD 1080p, HD 720p, berbagai signer, durasi pendek dan panjang):

| No | Nama Berkas | Codec | Resolusi | Signer | Durasi | Probe RC | Decode RC | Waktu | Status |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `signer0_label0_sample1.mp4` | `h264` | $1280 \times 720$ | Signer 0 | 2,28s | 0 | 0 | 0,189s | `PASS` |
| 2 | `signer0_label11_sample5.mp4` | `h264` | $1280 \times 720$ | Signer 0 | 2,78s | 0 | 0 | 0,148s | `PASS` |
| 3 | `signer0_label3_sample3.mp4` | `h264` | $1280 \times 720$ | Signer 0 | 2,19s | 0 | 0 | 0,147s | `PASS` |
| 4 | `signer0_label6_sample3.mp4` | `h264` | $1280 \times 720$ | Signer 0 | 2,37s | 0 | 0 | 0,117s | `PASS` |
| 5 | `signer0_label9_sample9.mp4` | `h264` | $1280 \times 720$ | Signer 0 | 2,30s | 0 | 0 | 0,149s | `PASS` |
| 6 | `signer0_label2_sample4.mp4` | `hevc` | $1920 \times 1080$ | Signer 0 | 1,97s | 0 | 0 | 0,206s | `PASS` |
| 7 | `signer1_label16_sample2.mp4` | `hevc` | $1920 \times 1080$ | Signer 1 | 2,45s | 0 | 0 | 0,391s | `PASS` |
| 8 | `signer1_label29_sample11.mp4` | `hevc` | $1920 \times 1080$ | Signer 1 | 2,00s | 0 | 0 | 0,216s | `PASS` |
| 9 | `signer2_label5_sample7.mp4` | `hevc` | $1280 \times 720$ | Signer 2 | 2,57s | 0 | 0 | 0,497s | `PASS` |
| 10 | `signer4_label9_sample9.mp4` | `hevc` | $1920 \times 1080$ | Signer 4 | 2,03s | 0 | 0 | 0,215s | `PASS` |

**Hasil Pilot:** Seluruh 10 video sampel lulus 100% tanpa satu pun error decoding.

---

## 4. Metode Full Decode 1.600 Video

Proses full decode dilakukan pada seluruh 1.600 video MP4 di direktori [`data/raw/video/wl_bisindo/videos/`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/videos/) menggunakan skrip terukur `scratch/full_decode_audit.py`:
- **Perintah Eksekusi:**
  `ffmpeg -v error -xerror -i "PATH_VIDEO" -map 0:v:0 -f null -progress pipe:1 NUL`
- **Pencegahan Beban Berlebih:** Menggunakan `ThreadPoolExecutor` dengan 2 worker threads terukur.
- **Pencatatan Frame Dekode:** Membaca indikator progres `frame=<N>` dari stream `pipe:1` secara deterministik sampai akhir video.
- **Ketahanan:** Checkpoint JSON disimpan secara periodik setiap 100 video.
- **Keamanan Data:** Decoding diarahkan ke null sink (`NUL`), tanpa re-encoding, tanpa transcode, dan tanpa menulis file video baru ke disk.

---

## 5. Hasil Kuantitatif Full Decode 1.600 Video

| Status Kategori | Jumlah Video | Persentase | Keterangan Evaluasi |
|---|---:|---:|---|
| **`FULL_DECODE_VALID`** | **1.600** | **100,00%** | Seluruh frame diproses sempurna hingga frame terakhir tanpa error (exit code 0). |
| **`PARTIAL_DECODE`** | **0** | **0,00%** | Tidak ada pemutusan decoding di tengah video. |
| **`DECODE_FAILED`** | **0** | **0,00%** | Tidak ada video yang gagal dibuka atau corrupt. |
| **`METADATA_INVALID`** | **0** | **0,00%** | Tidak ada metadata stream yang cacat. |
| **`HEADER_VALID_ONLY`** | **0** | **0,00%** | Seluruh 1.600 file telah ditingkatkan dari header check ke full pixel decode. |
| **`NOT_TESTED`** | **0** | **0,00%** | Tidak ada video yang terlewat. |
| **Total Video** | **1.600** | **100,00%** | - |

---

## 6. Statistik Decoder dan Karakteristik Video

Berdasarkan hasil parsing kontainer dan decoding aktual seluruh 1.600 video:

### 6.1 Distribusi Resolusi
- **$1920 \times 1080$ (Full HD 1080p):** **1.353 video (84,56%)**
- **$1280 \times 720$ (HD 720p):** **247 video (15,44%)**
- Resolusi anomali: **0 video**

### 6.2 Distribusi Codec Kompresi Video
- **HEVC / H.265 (`hvc1`):** **1.483 video (92,69%)** — 100% full decode valid
- **AVC / H.264 (`avc1`):** **117 video (7,31%)** — 100% full decode valid

### 6.3 Statistik Durasi dan Jumlah Frame Terdekode
- **Waktu Eksekusi Decoding Total:** **271,88 detik** (~4,53 menit untuk 1.600 video, rata-rata ~0,17 detik per video).
- **Durasi Video:**
  - Minimum: `1,400` detik
  - Rata-rata: `2,166` detik
  - Maksimum: `5,853` detik
- **Jumlah Frame Aktual Terdekode (`decoded_frame_count`):**
  - Minimum: `42` frame
  - Rata-rata: `64,9` frame
  - Maksimum: `173` frame
- **Distribusi Frame Rate (FPS):**
  - Constant Frame Rate ($30,0\text{ fps}$): **1.153 video (72,06%)**
  - Variable Frame Rate ($30,0 - 58,96\text{ fps}$): **447 video (27,94%)**

---

## 7. Daftar Video Bermasalah

- **Jumlah Video Bermasalah:** **0 berkas (0,00%)**
- **Daftar Berkas Korup / Rusak:** Tidak ada.
- **Exit Code Gagal:** Tidak ada (1.600 berkas keluar dengan returncode `0`).

---

## 8. Verifikasi Integritas SHA-256 Pasca-Decoding

Pemeriksaan SHA-256 dilakukan untuk memastikan decoding ke null sink tidak mengubah isi berkas asli:

| Berkas Uji | Lokasi Berkas | SHA-256 Sebelum Audit | SHA-256 Pasca-Audit | Status Integritas |
|---|---|---|---|:---:|
| **Arsip Asli** | `data/raw/video/wl_bisindo/archive.zip` | `12710ed31ee9...` | `12710ed31ee997503f904bf2061e743bb829fe315549af955de7cf6d0d905095` | `PASS (UNCHANGED)` |
| **1.600 Video MP4** | `data/raw/video/wl_bisindo/videos/*.mp4` | 1.600 hash unik | 1.600 hash identik (0 mismatch) | `PASS (UNCHANGED)` |
| **Taksonomi Konsep** | `data/bridge/concepts.csv` | `d3d0907642b8...` | `d3d0907642b8039411058d1ab378d15d6ab9ed929f743838a190bd68ffce9005` | `PASS (UNCHANGED)` |
| **FSL-105 Labels** | `data/raw/video/fsl_105/labels.csv` | `6074947fc905...` | `6074947fc905eecf20a341388551aeab0b32341928778a1f87d6c3bca073b630` | `PASS (UNCHANGED)` |
| **FSL-105 Train CSV** | `data/raw/video/fsl_105/train.csv` | `861a76cae835...` | `861a76cae835e284ac76ef37dc077ae0b6c793beb9c378eda1fce5f408dc609f` | `PASS (UNCHANGED)` |
| **FSL-105 Test CSV** | `data/raw/video/fsl_105/test.csv` | `3dd8e83294a6...` | `3dd8e83294a63b7c02fd1ee3ebd1d179aa4b0437ff9cfb3febab5d0e1da0ccf7` | `PASS (UNCHANGED)` |

---

## 9. Manifest dan Ringkasan yang Diperbarui

1. [`data/raw/video/wl_bisindo/wl_bisindo_decode_audit.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_decode_audit.csv)
   - Berisi tepat 1.601 baris (1 header + 1.600 data video).
   - Seluruh 1.600 baris memiliki:
     - `decode_status`: `FULL_DECODE_VALID`
     - `decode_exit_code`: `0`
     - `decode_error`: `""`
     - `decoded_frame_count`: terisi angka frame aktual
     - `decode_duration_sec`: terisi waktu eksekusi aktual
2. [`data/raw/video/wl_bisindo/wl_bisindo_decode_audit_summary.json`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_decode_audit_summary.json)
   - Ringkasan terstruktur agregat JSON.

---

## 10. Kesimpulan Kesiapan Memasuki Tahap A.3

1. **Integritas Video Terbukti 100%:** Seluruh 1.600 video WL-BISINDO telah berhasil didekode dari frame pertama hingga frame terakhir tanpa kegagalan decoder maupun frame korup.
2. **Kesesuaian Pemetaan:** Seluruh 32 label dan 10 kelas overlap SignBridge telah terbukti akurat menggunakan Mapping A.
3. **Kesiapan Ekstraksi Fitur:** Dataset WL-BISINDO dinyatakan **SIAP** memasuki **Tahap A.3 (Preprocessing Video / Ekstraksi Keypoint & Fitur Visual)**.
