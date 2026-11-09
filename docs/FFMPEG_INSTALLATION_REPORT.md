# LAPORAN INSTALASI DAN VERIFIKASI DECODER FFMPEG (TAHAP A.2.4.1)

**Tanggal:** 7 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Lokasi Instalasi Lokal:** `C:\Tools\ffmpeg\`  
**Status Evaluasi:** `PASS`

---

## 1. Latar Belakang dan Izin Pengguna

Pada audit Tahap A.2.4 sebelumnya, proses audit decode penuh terhadap 1.600 video WL-BISINDO berstatus `BLOCKED` karena ketiadaan video decoder (seperti FFmpeg, FFprobe, atau OpenCV `cv2`) pada environment Windows.

Pengguna telah memberikan izin eksplisit untuk mengunduh dan memasang FFmpeg serta FFprobe pada direktori lokal mandiri tanpa mengubah PATH sistem secara global, tanpa mengubah virtual environment Python, dan tanpa mengubah package proyek SignBridge.

---

## 2. Informasi Sumber dan Verifikasi Integritas

| Parameter | Detail Teknis | Status |
|---|---|:---:|
| **Distributor / Publisher** | Gyan Doshi (distributor resmi Windows build yang direferensikan langsung oleh situs resmi [ffmpeg.org](https://ffmpeg.org/download.html#build-windows)) | `PASS` |
| **URL Sumber Unduhan** | `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip` | `PASS` |
| **URL Checksum Resmi** | `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256` | `PASS` |
| **Ukuran Arsip ZIP** | `114.768.076` bytes (~109,45 MB) | `PASS` |
| **SHA-256 Resmi** | `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` | `PASS` |
| **SHA-256 Terhitung** | `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` | `PASS (100% MATCH)` |
| **Arsip Temporer** | Berkas ZIP temporer langsung dihapus pasca-ekstraksi | `PASS` |

---

## 3. Detail Binary dan Lokasi Eksekusi

Binary diekstrak secara minimal dan terisolasi ke direktori alat lokal:
- **Direktori Root:** `C:\Tools\ffmpeg\`
- **Direktori Binary:** `C:\Tools\ffmpeg\bin\`
  - `ffmpeg.exe` (Ukuran: `105.423.872` bytes)
  - `ffprobe.exe` (Ukuran: `105.221.120` bytes)

### Output Verifikasi Versi

#### FFmpeg:
```text
ffmpeg version 9.0.2-essentials_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
built with gcc 16.2.0 (Rev3, Built by MSYS2 project)
```

#### FFprobe:
```text
ffprobe version 9.0.2-essentials_build-www.gyan.dev Copyright (c) 2007-2026 the FFmpeg developers
built with gcc 16.2.0 (Rev3, Built by MSYS2 project)
```

---

## 4. Verifikasi Dukungan Codec HEVC dan AVC

Pengujian `ffmpeg.exe -decoders` memverifikasi ketersediaan decoder kompresi video yang dibutuhkan dataset WL-BISINDO:

```text
 VFS..D h264                 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10
 V....D h264_qsv             H264 video (Intel Quick Sync Video acceleration)
 V..... h264_amf             H264 AMD AMF video decoder
 V..... h264_cuvid           Nvidia CUVID H264 decoder
 VFS..D hevc                 HEVC (High Efficiency Video Coding)
 V....D hevc_qsv             HEVC video (Intel Quick Sync Video acceleration)
 V..... hevc_amf             HEVC AMD AMF video decoder
 V..... hevc_cuvid           Nvidia CUVID HEVC decoder
```

- **Dukungan H.264 / AVC:** `VFS..D h264` aktif (Direct Software Decoding + Hardware Acceleration).
- **Dukungan H.265 / HEVC:** `VFS..D hevc` aktif (Direct Software Decoding + Hardware Acceleration).
- **Format MP4 Kontainer:** Didukung secara bawaan melalui `libavformat`.

---

## 5. Kesimpulan Kesiapan Decoder

1. FFmpeg dan FFprobe versi 9.0.2 berhasil terpasang dan siap digunakan via absolute path (`C:\Tools\ffmpeg\bin\ffmpeg.exe`).
2. Decoder software dan hardware untuk format HEVC (1.483 video WL-BISINDO) dan AVC (117 video WL-BISINDO) tersedia penuh.
3. Lingkungan telah siap untuk melanjutkan ke **Tahap Kedua: Pilot Decode** dan **Tahap Ketiga: Full Decode 1.600 Video**.

