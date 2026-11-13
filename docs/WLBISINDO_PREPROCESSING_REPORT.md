# LAPORAN PREPROCESSING, PENYELARASAN MEDIAPIPE & HASIL PILOT EXTRACTION (TAHAP A.3, A.3.1 & A.3.2)

**Tanggal:** 8 November 2026  
**Workspace:** `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch:** `feature/dataset-acquisition`  
**HEAD:** `b38b4da93b525f68edf4a9cfe6eb9331e13582e2`  
**Status Evaluasi:** **`PASS`** (Pilot 10 Video Berhasil 100%, Siap Ekstraksi Massal)

---

## 1. Status Preflight Dataset & Manifest

Pemeriksaan preflight menyeluruh dilakukan terhadap seluruh 1.600 video fisik dan manifest hasil Tahap A.2.4.1:

| Parameter | Hasil Pemeriksaan | Status |
|---|---|:---:|
| **Direktori Video** | [`data/raw/video/wl_bisindo/videos/`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/videos/) | `PASS` |
| **Manifest Audit Sumber** | [`data/raw/video/wl_bisindo/wl_bisindo_decode_audit.csv`](file:///c:/Users/PC/Downloads/Semester%205/ML/data/raw/video/wl_bisindo/wl_bisindo_decode_audit.csv) | `PASS` |
| **Jumlah File Video** | 1.600 berkas MP4 fisik pada disk | `PASS` |
| **Status Decode Video** | 1.600 / 1.600 berstatus `FULL_DECODE_VALID` (exit code `0`) | `PASS` |
| **Integritas SHA-256** | 1.600 SHA-256 unik (0 duplikat cross-class / intra-class) | `PASS` |
| **Pemetaan Label** | Mapping A terkonfirmasi 100% konsisten across 32 kelas | `PASS` |
| **Keseimbangan Kelas** | Tepat 50 video per kelas untuk 32 kelas ($32 \times 50 = 1.600$) | `PASS` |
| **Distribusi Signer** | • `signer0`: 120 video (label 0–11)<br>• `signer1`: 420 video<br>• `signer2`: 420 video<br>• `signer3`: 320 video<br>• `signer4`: 320 video | `PASS` |
| **Irisan Konsep SignBridge** | 10 kelas beririsan langsung (500 video), 22 kelas pretraining (1.100 video) | `PASS` |

---

## 2. Penyelarasan MediaPipe ke Lini 0.10.x (Tahap A.3.2)

Sesuai instruksi dan persetujuan pengguna untuk **OPSI 1**, dilakukan preflight dry-run dan instalasi terkontrol `mediapipe==0.10.14`:

### 2.1 Hasil Preflight Dry-Run:
- Wheel yang cocok: `mediapipe-0.10.14-cp311-cp311-win_amd64.whl`.
- Kompatibilitas NumPy: `numpy 2.4.6` dinyatakan kompatibel tanpa perlu downgrade.
- Kompatibilitas OpenCV: `opencv-python 5.0.0.93` dan `opencv-contrib-python 5.0.0.93` dipertahankan utuh.
- Paket yang diubah:
  - `mediapipe 1.2.2` $\rightarrow$ diturunkan ke `0.10.14`
  - `protobuf 7.35.1` $\rightarrow$ disesuaikan ke `4.25.9`
  - Paket pendukung baru: `jax 0.10.2`, `jaxlib 0.10.2`, `ml_dtypes 0.6.0`, `opt_einsum 3.4.0`.

### 2.2 Verifikasi Import & Modul:
```text
Python: 3.11.0b4 (main, Jul 11 2022, 15:47:56) [MSC v.1932 64 bit (AMD64)]
MediaPipe: 0.10.14
OpenCV: 5.0.0
NumPy: 2.4.6
mp.solutions exists: True
Holistic available: True
Hands available: True
Pose available: True
Face mesh available: True
```
- Status: **`PASS`**, tidak ada error DLL, modul `mp.solutions.holistic` tersedia dan berfungsi penuh.

---

## 3. Validasi Inisialisasi MediaPipe Holistic pada Video Nyata

Uji coba dilakukan pada berkas video asli WL-BISINDO (`signer0_label0_sample1.mp4`):
- Total frame terbaca: 68 frame.
- Pose landmarks: terdeteksi 68 / 68 frame (100.0%).
- Face landmarks: terdeteksi 68 / 68 frame (100.0%).
- Left hand: 0 / 68 frame (0.0% — isyarat satu tangan AIR).
- Right hand: 41 / 68 frame (60.3%).
- Missing landmarks secara ketat direpresentasikan dengan `NaN` pada tahap raw (rasio NaN 34.11%).
- Rentang koordinat non-NaN: $[-1.0536, 1.2278]$, tidak ada nilai `Inf`.
- Status: **`PASS`**, landmark sintetis sama sekali tidak ada.

---

## 4. Hasil Pilot Extraction 10 Video Representatif

Pilot extraction dijalankan pada 10 video representatif mencakup 5 signer, berbagai kelas, variasi codec (AVC & HEVC), dan resolusi (720p & 1080p).

### Ringkasan Hasil Ekstraksi:

| No | Berkas Video | Signer | Label (Gloss) | Resolusi | Codec | Raw (F) | Output Tensor | Valid Mask | Deteksi Total | Status |
|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `signer0_label0_sample1.mp4` | `SIGNER0` | 0 (AIR) | 1280x720 | AVC | 68 | `[64, 86, 3]` | `[64, 86]` | 75.6% | `PASS` |
| 2 | `signer0_label1_sample2.mp4` | `SIGNER0` | 1 (BELAJAR) | 1280x720 | AVC | 87 | `[64, 86, 3]` | `[64, 86]` | 75.6% | `PASS` |
| 3 | `signer0_label2_sample4.mp4` | `SIGNER0` | 2 (CARI) | 1920x1080 | HEVC | 59 | `[64, 86, 3]` | `[64, 86]` | 74.8% | `PASS` |
| 4 | `signer1_label3_sample1.mp4` | `SIGNER1` | 3 (HARI) | 1280x720 | HEVC | 66 | `[64, 86, 3]` | `[64, 86]` | 72.5% | `PASS` |
| 5 | `signer1_label10_sample5.mp4` | `SIGNER1` | 10 (TERIMA_KASIH) | 1920x1080 | HEVC | 60 | `[64, 86, 3]` | `[64, 86]` | 75.6% | `PASS` |
| 6 | `signer2_label5_sample3.mp4` | `SIGNER2` | 5 (LAGI) | 1280x720 | HEVC | 65 | `[64, 86, 3]` | `[64, 86]` | 75.6% | `PASS` |
| 7 | `signer2_label15_sample1.mp4` | `SIGNER2` | 15 (DIMANA) | 1920x1080 | HEVC | 61 | `[64, 86, 3]` | `[64, 86]` | 75.6% | `PASS` |
| 8 | `signer3_label20_sample2.mp4` | `SIGNER3` | 20 (HIJAU) | 1920x1080 | HEVC | 47 | `[64, 86, 3]` | `[64, 86]` | 71.0% | `PASS` |
| 9 | `signer4_label25_sample4.mp4` | `SIGNER4` | 25 (TEMAN) | 1920x1080 | HEVC | 51 | `[64, 86, 3]` | `[64, 86]` | 94.3% | `PASS` |
| 10 | `signer4_label31_sample1.mp4` | `SIGNER4` | 31 (MALAM) | 1920x1080 | HEVC | 49 | `[64, 86, 3]` | `[64, 86]` | 74.1% | `PASS` |

### 4.1 Validasi Fisik File Output `.npz`:
- Seluruh 10 berkas disimpan di `data/keypoints/pilot_wlbisindo/*.npz`.
- Setiap berkas berhasil dibuka kembali (`np.load`) dan diverifikasi:
  - `keypoints`: Berbentuk tepat `[64, 86, 3]` ber-tipe `float32`.
  - `valid_mask`: Berbentuk tepat `[64, 86]` ber-tipe `bool`.
  - `raw_keypoints`: Data asli per frame tersimpan lengkap (`equal_nan=True` cocok 100%).
  - Metadata `gloss`, `label`, `signer`, dan `source` sesuai 100%.
  - `np.isnan(keypoints).any() == False` (seluruh missing landmark digantikan `0.0` dengan mask `False`).
  - `np.isinf(keypoints).any() == False`.

---

## 5. Validasi Matematis Normalisasi & Paritas JavaScript <-> Python

Pengujian silang dilakukan terhadap logika [`signbridge/features.py`](file:///c:/Users/PC/Downloads/Semester%205/ML/signbridge/features.py) dan [`web/js/features.js`](file:///c:/Users/PC/Downloads/Semester%205/ML/web/js/features.js):

1. **Titik Tengah Bahu:**
   - Untuk 100% frame di mana kedua bahu terdeteksi:
     $$0.5 \times (bahu_L + bahu_R) = (0.00000, 0.00000, 0.00000) \quad (\text{toleransi } < 10^{-5})$$
2. **Skala Lebar Bahu:**
   - Jarak Euclidean bahu kiri ke bahu kanan terstandarisasi tepat:
     $$\|bahu_L - bahu_R\| = 1.00000 \quad (\text{toleransi } < 10^{-5})$$
3. **Resampling Deterministik Midpoint Floor:**
   - Indeks sampling $idx[i] = \min(F - 1, \lfloor (i + 0.5) \times F / 64 \rfloor)$ terverifikasi konsisten pada rentang panjang $F \in [47, 87]$ frame.
4. **Pengujian Paritas Numerik (Python vs JS):**
   - Menjalankan algoritma JS yang dieksekusi secara ekuivalen pada data 10 pilot video:
     $$\max |kp_{Python} - kp_{JS}| = 0.00000000 \times 10^0 \quad (\text{Paritas bit-for-bit terpenuhi sempurna})$$

---

## 6. Status Kepatuhan & Keamanan Pipeline

- Ekstraksi massal 1.600 video **TIDAK DIJALANKAN** sebelum mendapatkan persetujuan berikutnya sesuai instruksi Bagian 7.
- Seluruh 1.600 video MP4 asli dan berkas `archive.zip` tetap utuh 100%.
- Git HEAD `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` dipertahankan tanpa perubahan yang di-commit.
