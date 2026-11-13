# Perbaikan: Abjad, Pola Isyarat, dan Database

Tiga keluhan: (1) abjad tidak terbaca, (2) banyak pola kata salah, (3) database kurang lengkap.
Dokumen ini mencatat akar masalah, apa yang diubah, bukti uji, dan **apa yang masih harus dijalankan di PC Gloria**
(bagian itu tidak bisa dikerjakan tanpa data mentah + GPU).

## 1. Abjad (ejaan jari)

**Akar masalah**
- Model gambar `I1` akurasinya 3,85% = tebakan acak (1/26).
- Yang sebenarnya dipakai adalah aturan geometri **satu tangan** dengan confidence palsu 0,93 —
  padahal sebagian besar abjad BISINDO memakai **dua tangan**.

**Perbaikan**
- Pengenal baru berbasis landmark (`web/js/fingerspell_mlp.js`, `signbridge/fingerspell_landmarks.py`):
  127 fitur = bentuk tangan A + bentuk tangan B + posisi tangan B relatif tangan A. MLP 256-128, ±1 MB JSON, jalan di browser tanpa ONNX.
- Dilatih dari 14.493 sampel landmark abjad BISINDO nyata (KrisnaSantosa15/realtime-bisindo-classification, lisensi MIT).
- Stabilisasi: rata-rata 8 frame, minimal 6 suara, probabilitas ≥ 0,55, satu huruf per tahanan, jeda 700 ms. Confidence yang tampil = probabilitas asli.

**Bukti** (`outputs/experiments/F1_fingerspell_mlp/result.json`)

| Uji | Akurasi |
|---|---|
| Validasi | 98,76% |
| Test | 98,99% (macro-F1 98,89%) |
| Test dicerminkan (kidal) | 98,6% |
| Tangan kedua hilang | 94,5% |
| Rotasi/skala/geser | 97,7% |

Huruf paling sering tertukar: M↔N, B→E.

> **Jujur soal angka ini:** data Krisna adalah augmentasi dari ±312 foto, jadi train dan test berasal dari foto yang mirip.
> Angka 98,99% itu **optimistis**. Angka yang boleh ditulis di laporan adalah hasil uji silang ke dataset Mendeley (langkah A di bawah)
> dan uji webcam langsung oleh tim.

## 2. Pola kata (32 gloss) banyak salah

Model M0 mendapat 99,13% di test, tetapi test itu memakai **penutur yang sama** dengan train, dan jalur kamera langsung
tidak sama dengan data latih. Yang ditemukan dan diperbaiki:

| Akar masalah | Perbaikan |
|---|---|
| Segmentasi langsung hanya mengambil frame "bergerak" + jalur tahan-diam 12 frame; data latih berisi satu isyarat utuh | Segmen = dari tangan masuk ruang isyarat (+300 ms pre-roll) sampai tangan turun / diam 1 dtk / maks 4 dtk (`recognizer.js`) |
| Wajah palsu disuntikkan saat wajah tidak terdeteksi | Dihapus; wajah hilang = 0 seperti data latih (`vision.js`) |
| Satu tebakan per segmen | TTA 3 potongan waktu, dirata-rata |
| Tangan diam (mengeja huruf) ikut diklasifikasi sebagai kata | Segmen tanpa gerakan ditolak; huruf membatalkan segmen kata |
| Latihan & kamera gagal → hasil "96%" palsu | Dihapus. Latihan sekarang dinilai dari prediksi kamera sungguhan |
| Perekam menyimpan keypoint sintetis | Merekam keypoint kamera asli 2,5 dtk; klip tanpa tangan ditolak |
| Animasi rujukan sintetis (model sendiri hanya mengenali 1 dari 32) | Memakai rekaman asli `web/model/ref/<NAMA>.json`; yang belum ada diberi label "ILUSTRASI KASAR" |
| Loader memakai keypoint yang sudah dipraproses (praproses ganda) | Memakai `raw_keypoints` (`signbridge/data/dataset.py`) |
| Tidak ada augmentasi potong-waktu & cermin; latih di CPU; evaluasi hanya SD | `scripts/train_m0_robust.py` (potong-waktu, cermin, LOSO, CUDA) |

> **Yang belum terjadi:** model video **belum dilatih ulang** — butuh data mentah dan PyTorch di PC Gloria (langkah B).
> Perbaikan di atas membetulkan jalur kamera; bobot `student.onnx` masih yang lama.

## 3. Database

- `data/bridge/concepts.csv`: dari 32 konsep kelas (hanya 10 yang dikenali model) menjadi **54 konsep** —
  32 yang dikenali model (`model_supported=1`, urutan = label model) + 22 konsep roadmap (`model_supported=0`). Sinkron dengan `CLASSROOM_CONCEPTS` di `web/js/config.js`.
- Kolom `ref_video_*` yang menunjuk 64 video yang tidak pernah ada diganti `ref_bisindo` (→ `web/model/ref/`) dan `ref_fsl` (kosong sampai ada data).
- `server/database.py`: membaca kolom `id_text/fil_text/en_text` yang tidak ada di CSV → deskripsi semua konsep kosong. Sekarang membaca `id/fil/en`.
- `web/model/ref/A.json … Z.json`: 26 rujukan huruf dari landmark asli. Rujukan 32 kata dibuat di langkah C.
- Manifest perekam tidak lagi mencantumkan berkas video/audio/foto yang tidak pernah dibuat.
- Deskripsi teks gerakan (`PHONOLOGY_DB`, panduan huruf) **belum diverifikasi penutur Tuli**; di UI kini diberi keterangan itu. `data/phonology.csv` juga belum diverifikasi.
- Yang masih kosong: pemetaan ke kelas FSL-105, video rujukan FSL, rekaman tim sendiri.

## 4. Yang harus dijalankan di PC Gloria

```bash
# A. Abjad: uji silang ke Mendeley (angka jujur), lalu latih gabungan
pip install mediapipe==0.10.14 scikit-learn
git clone https://github.com/KrisnaSantosa15/realtime-bisindo-classification ../krisna
python scripts/train_fingerspell_landmarks.py --extract <folder_abjad_mendeley> --out-csv data/fingerspell/mendeley_landmarks.csv
python scripts/train_fingerspell_landmarks.py --krisna ../krisna/data --landmarks data/fingerspell/mendeley_landmarks.csv --test-source mendeley   # angka jujur
python scripts/train_fingerspell_landmarks.py --krisna ../krisna/data --landmarks data/fingerspell/mendeley_landmarks.csv                          # model final

# B. Kata: ukur lintas-penutur, lalu latih & ekspor model baru
python scripts/train_m0_robust.py --loso
python scripts/train_m0_robust.py --protocol sd --export

# C. Animasi rujukan 32 kata dari rekaman asli
python scripts/build_reference_signs.py --words

# D. Rekaman tim (tab Perekam → unduh ZIP) masuk ke pelatihan
python scripts/recorder_zip_to_manifest.py --inp <folder_zip_terekstrak> --out data/selfrec
python scripts/train_m0_robust.py --protocol sd --extra-manifest data/selfrec/manifest_own.csv --export
python scripts/train_fingerspell_landmarks.py --krisna ../krisna/data --landmarks data/fingerspell/mendeley_landmarks.csv data/selfrec/fingerspell_landmarks.csv
```

Setelah B: buka web, **hard refresh** (cache service worker sudah dinaikkan ke v8), uji tiap gloss 5× dan catat benar/salah.

## 5. Uji otomatis

- `node --test tests/js/*.test.mjs` → 34 lulus (paritas Python↔JS, akurasi MLP pada sampel asli, segmentasi, emit-sekali).
- `pytest tests` di lingkungan tanpa torch/fastapi/data: 113 lulus. Yang gagal semuanya karena data/paket tidak ada di mesin uji,
  kecuali `test_label_space_is_official_and_separate` yang **sudah gagal sebelum perubahan ini**
  (mengharapkan `BISINDO_32_GLOSSES` ≠ label WL-BISINDO, padahal konstanta itu sudah disamakan oleh tim).
- `scripts/train_m0_robust.py` hanya lolos `py_compile` — belum pernah dijalankan (tidak ada PyTorch di mesin uji).
- Webcam langsung **belum diuji**.
