# Laporan Audit Keamanan Pipeline & Penghapusan Synthetic Fallback (`docs/PIPELINE_SAFETY_AUDIT.md`)

**Proyek**: SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Working Directory**: `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch Aktif**: `feature/dataset-acquisition`  
**Tahap**: **Tahap A — Pipeline Safety Audit & Synthetic Fallback Removal**  
**Tanggal Eksekusi**: 7 November 2026

---

## 1. Daftar Masalah Awal (Temuan Audit Sebelum Perbaikan)

Sebelum perbaikan pada Tahap A, ditemukan **7 celah keamanan pipeline (*silent synthetic fallbacks*)** yang menyebabkan pipeline SignBridge diam-diam menghasilkan data sintetis/acak ketika dataset fisik tidak ditemukan atau dependency belum terpasang:

| No | File & Lokasi Awal | Masalah Keamanan Pipeline (*Silent Synthetic Fallback*) | Risiko terhadap Integritas Eksperimen |
| :---: | :--- | :--- | :--- |
| **1** | `scripts/extract_keypoints.py` (baris 36–81) | Blok `try: import cv2, mediapipe ... except Exception: pass` menangkap semua kegagalan impor maupun pembacaan video secara diam-diam, lalu mengembalikan array koordinat acak `rng.uniform(0.15, 0.85, size=(64, 86, 3))`. | Jika `opencv-python` atau `mediapipe` belum terpasang (seperti pada environment lokal saat ini) atau video rusak, seluruh berkas `.npz` yang dihasilkan berisi angka acak tanpa satu pun peringatan error. |
| **2** | `scripts/extract_keypoints.py` (baris 93–97 & 104–107) | 1) Hanya memindai `*.mp4` dan `*.webm` (tidak mengenali `.MOV`/`.mov` pada `FSL-105`).<br>2) Jika folder kosong, otomatis memanggil `ensure_demo_dataset()` yang membuat data sintetis.<br>3) Jika nama folder tidak ada di `BISINDO_32_GLOSSES`, melabeli video secara modulo `BISINDO_32_GLOSSES[idx % 32]`.<br>4) `labels.csv` ber-BOM UTF-8 (`\ufeffid`) pada `FSL-105` gagal dibaca dengan encoding `utf-8` biasa. | 2.130 video `.MOV` `FSL-105` terabaikan sepenuhnya dan digantikan oleh dataset demo sintetis; atau jika dipaksakan masuk, dilabeli secara salah ke 32 gloss BISINDO. |
| **3** | `scripts/crop_hands.py` (baris 23–57) | Fungsi `run_crop_hands(in_dir, out_dir, manifest_path)` **sama sekali tidak membaca parameter `in_dir`**, melainkan langsung membuat 78 citra acak `dummy_img = rng.integers(20, 235, size=(256, 256, 3))` dan landmark acak `hand_lm = rng.uniform(0.25, 0.75, size=(21, 3))`. | Seluruh **4.466 citra RGB asli** BISINDO Alphabet (`A–Z`) di `data/raw/image/bisindo_alphabet/` diabaikan total dan ditimpa oleh noise piksel acak. |
| **4** | `signbridge/image/train_image.py` (`FingerspellDataset`, baris 191–239) | Jika `manifest_path` tidak ditemukan atau berkas gambar gagal dibuka (`except Exception: pass`), `FingerspellDataset` otomatis membuat 78 baris kosong dan membangkitkan citra gelombang sinus `np.sin(freq_x * x_grid) * np.cos(freq_y * y_grid)`. | Model klasifikasi abjad `I1–I3` dapat terlatih pada pola gelombang sinus sintetis tanpa disadari apabila jalur manifest salah. |
| **5** | `scripts/prepare_kelas_audio.py` (baris 23–51) | Fungsi `write_sine_wav()` membuat 12 berkas audio gelombang sinus `300–575 Hz` palsu jika berkas `.wav` di `data/audio/metadata.csv` tidak ditemukan, serta memanggil `build_all_text_and_audio_data()` yang berisiko menimpa metadata. | Menyembunyikan fakta bahwa 60 berkas rekaman suara kelas (`data/audio/wavs/id_001.wav`..`id_060.wav`) masih berstatus `NOT AVAILABLE`. |
| **6** | `signbridge/audio/train_asr.py` (baris 182, 218–233, 236–284) | Menggunakan `mel = torch.randn(1, 80, n_frames)`, melatih model pada `mel = torch.randn(4, 80, 100)` dan `targets = torch.randint(0, 128, (4, 50))`, mengukur RTF pada `dummy_audio = rng.normal(...)`, serta menghitung WER/CER dari array string *hardcoded*. *(Catatan: berkas `signbridge/audio/finetune_whisper.py` tidak ada di repositori; seluruh logika ASR berada di `signbridge/audio/train_asr.py` dan `scripts/prepare_kelas_audio.py`).* | Eksperimen ASR berjalan di atas tensor acak dan teks *hardcoded* tanpa membaca berkas `.wav` fisik (`Google FLEURS id_id` maupun audio kelas). |
| **7** | `signbridge/text/train_text.py` (baris 206–224 & 285–292) & `scripts/build_text_corpus.py` | 1) `_load_tsv_pairs()` mengembalikan 5 kalimat *hardcoded* jika berkas TSV tidak ditemukan.<br>2) Melatih `GRUAttentionSeq2Seq` pada token acak `torch.randint(1, 256, (4, 8))`.<br>3) Belum ada penjaga otomatis yang menolak korpus monolingual Tatoeba (`ind_sentences.tsv`) sebagai pasangan `gloss-to-sentence` atau memeriksa kebocoran `test_manual.tsv` ke `train.tsv`/`val.tsv`. | Model teks T1 berlatih pada token acak, dan ketiadaan berkas TSV atau kesalahan penunjukan berkas Tatoeba tidak terdeteksi. |

---

## 2. Daftar Berkas yang Diperbaiki & Perubahan yang Dilakukan

| No | Berkas yang Diperbaiki / Ditambahkan | Ringkasan Perubahan Keamanan Pipeline |
| :---: | :--- | :--- |
| 1 | `scripts/extract_keypoints.py` | - Menghapus import dan pemanggilan otomatis `ensure_demo_dataset()` serta menghapus pembuatan keypoint acak `rng.uniform(0.15, 0.85, ...)`.<br>- Menambahkan `check_video_dependencies()` yang melempar `RuntimeError` eksplisit (`pip install opencv-python mediapipe`) jika `cv2` atau `mediapipe` belum terpasang.<br>- Menambahkan `discover_video_files()` yang mendukung `.mp4`, `.webm`, dan `.mov` secara *case-insensitive* (`.MOV`, `.MP4`, `.WEBM`), mengabaikan berkas tersembunyi `._*`, dan melempar `FileNotFoundError` jika folder kosong.<br>- Menambahkan `load_optional_labels_csv()` (dengan dukungan `utf-8-sig` untuk menangani BOM pada `FSL-105/labels.csv`) dan `resolve_video_gloss_and_label()` yang menolak folder gloss tak dikenal dengan `ValueError` (tanpa modulo `idx % 32`). |
| 2 | `scripts/crop_hands.py` | - Menghapus seluruh kode pembuatan citra dummy (`rng.integers`) dan landmark acak (`rng.uniform`).<br>- Menambahkan `load_rgb_image()` menggunakan `PIL.Image` (`verify()` + `convert("RGB")`) yang menolak berkas hilang (`FileNotFoundError`), 0-byte, atau gambar rusak (`ValueError`).<br>- Menambahkan `discover_alphabet_images()` yang memindai folder kelas `A–Z` di `in_dir` (default diarahkan ke `data/raw/image/bisindo_alphabet`), memelihara pemetaan `FINGERSPELL_26_LABELS` (`0..25`), dan menolak jika `in_dir == out_dir` agar berkas sumber tidak pernah tertimpa. |
| 3 | `signbridge/image/train_image.py` | - Menghapus fallback pembuatan 78 sampel kosong dan pola gelombang sinus `np.sin(...) * np.cos(...)` pada `FingerspellDataset`.<br>- Menambahkan `load_normalized_chw()` yang mewajibkan berkas `.npy` atau `.jpg`/`.png` fisik benar-benar ada di disk dan melemparkan `FileNotFoundError` / `ValueError` jika manifest atau citra tidak valid. |
| 4 | `scripts/prepare_kelas_audio.py` | - Menghapus fungsi `write_sine_wav()` dan pemanggilan otomatis `build_all_text_and_audio_data()` yang dapat menimpa `metadata.csv`.<br>- Menambahkan `inspect_kelas_audio_status()` dan memperbarui `prepare_audio_files()` agar memeriksa keberadaan fisik setiap berkas `.wav` pada `data/audio/metadata.csv`, melaporkan `STATUS: NOT AVAILABLE` secara eksplisit, dan melempar `FileNotFoundError` tanpa membuat berkas `.wav` palsu. |
| 5 | `signbridge/audio/train_asr.py` | - Menambahkan `load_wav_waveform()` yang memvalidasi header RIFF/WAVE fisik serta mendukung format PCM 16/32-bit (`fmt_tag=1`) maupun IEEE Float 32-bit (`fmt_tag=3` pada `Google FLEURS id_id`).<br>- Menambahkan `compute_log_mel_spectrogram()` berbasis FFT nyata dari waveform audio dan `load_audio_dataset_records()` yang memverifikasi berkas `.wav` fisik dari CSV kelas maupun TSV FLEURS.<br>- Menghapus seluruh penggunaan `torch.randn`, `torch.randint`, `dummy_audio`, dan daftar kalimat *hardcoded* pada `WhisperASRWrapper` dan `run_asr_experiment()`. |
| 6 | `signbridge/text/train_text.py` | - Menghapus fallback 5 pasangan kalimat *hardcoded* pada `_load_tsv_pairs()` serta menghapus token acak `torch.randint(1, 256, ...)` pada pelatihan GRU.<br>- Menambahkan deteksi eksplisit pada `_load_tsv_pairs()` untuk menolak korpus monolingual Tatoeba (`ind_sentences.tsv`) bila diberikan sebagai pasangan `gloss-to-sentence`, dan menyediakan `load_monolingual_tatoeba_tsv()` secara terpisah.<br>- Menambahkan `load_and_verify_text_splits()` yang memvalidasi `train.tsv`, `val.tsv`, dan `test_manual.tsv` serta melempar `ValueError` jika terdapat kebocoran kalimat dari `test_manual.tsv` ke `train.tsv` atau `val.tsv`.<br>- Menambahkan `encode_pairs_from_vocab()` untuk menokenisasi pasangan asli dari `train.tsv`. |
| 7 | `scripts/build_text_corpus.py` | - Menambahkan `verify_existing_text_corpus()` dan parameter `overwrite: bool = False` (default) pada `build_all_text_and_audio_data()` sehingga berkas `train.tsv`, `val.tsv`, `test_manual.tsv`, `kelas_sentences.txt`, dan `metadata.csv` yang sudah ada terlindungi dari penimpaan tidak sengaja. |
| 8 | `tests/test_pipeline_safety_audit.py` | - Suite pengujian otomatis (9 test case komprehensif) yang memverifikasi seluruh persyaratan keamanan pipeline pada Tahap A. |

---

## 3. Pengujian yang Dijalankan & Hasil `PASS` / `FAIL`

Perintah pengujian yang dijalankan:
```powershell
python -m unittest tests/test_pipeline_safety_audit.py -v
```

| ID Test | Nama Fungsi Pengujian | Skenario yang Diuji | Hasil |
| :---: | :--- | :--- | :---: |
| **T01** | `test_01_video_no_synthetic_fallback_and_empty_dir_error` | Memastikan `ensure_demo_dataset` telah dihapus dari `scripts/extract_keypoints.py` dan direktori kosong/hilang melempar `FileNotFoundError`. | **PASS (`ok`)** |
| **T02** | `test_02_video_extensions_mov_case_insensitive_and_fsl105_discovery` | Memastikan ekstensi `.MOV`, `.mov`, `.mp4`, `.MP4`, `.webm`, `.WEBM` terdeteksi, berkas `._*` diabaikan, serta **2.130 berkas `.MOV`** dan **105 kelas `labels.csv`** pada dataset asli `FSL-105` terbaca 100%. | **PASS (`ok`)** |
| **T03** | `test_03_video_unknown_gloss_and_missing_dependency_errors` | Memastikan folder gloss tidak dikenal ditolak dengan `ValueError` (bukan modulo `idx % 32`), berkas 0-byte ditolak, dan ketiadaan `cv2`/`mediapipe` melempar `RuntimeError` yang menyebutkan `pip install opencv-python mediapipe`. | **PASS (`ok`)** |
| **T04** | `test_04_image_empty_and_corrupt_input_errors` | Memastikan `crop_hands.py` dan `FingerspellDataset` menolak folder kosong (`FileNotFoundError`), manifest hilang (`FileNotFoundError`), dan berkas JPEG rusak (`ValueError`). | **PASS (`ok`)** |
| **T05** | `test_05_image_crops_match_real_source_rgb_pixels` | Memastikan seluruh **4.466 citra RGB** di 26 kelas `A–Z` (`data/raw/image/bisindo_alphabet`) ditemukan, berkas asli tidak berubah, dan array `.npy` hasil `run_crop_hands` 100% identik (`np.testing.assert_array_equal`) dengan piksel citra RGB sumber asli. | **PASS (`ok`)** |
| **T06** | `test_06_audio_no_synthetic_sine_and_reports_not_available` | Memastikan `write_sine_wav` tidak ada lagi di `prepare_kelas_audio.py`, status `data/audio/metadata.csv` dilaporkan sebagai `NOT AVAILABLE` (`60/60` file `.wav` belum ada), melempar `FileNotFoundError`, dan tidak membuat folder `data/audio/wavs/`. | **PASS (`ok`)** |
| **T07** | `test_07_audio_reads_real_fleurs_id_id_wavs` | Memastikan `load_audio_dataset_records` dan `load_wav_waveform` berhasil membaca berkas `.wav` IEEE float 16 kHz asli dari `data/audio/fleurs/id_id/dev.tsv` dan menghasilkan spektrogram log-mel hingga 80 kanal yang valid (`isfinite`). | **PASS (`ok`)** |
| **T08** | `test_08_text_loads_real_tsv_and_rejects_tatoeba_as_gloss_pairs` | Memastikan `_load_tsv_pairs` menolak berkas hilang (`FileNotFoundError`), menolak `ind_sentences.tsv` Tatoeba (`28.418` baris monolingual) dengan `ValueError` jika dimuat sebagai `gloss-to-sentence`, serta memuat split asli (`170` train, `30` val, `105` test). | **PASS (`ok`)** |
| **T09** | `test_09_text_prevents_test_set_leakage_into_train_or_val` | Memastikan `load_and_verify_text_splits` melempar `ValueError` seketika apabila ada satu saja kalimat dari `test_manual.tsv` yang bocor ke `train.tsv` atau `val.tsv`, serta `verify_existing_text_corpus()` lulus 100%. | **PASS (`ok`)** |

**Total Hasil Pengujian**: **9 / 9 PASS (`Ran 9 tests in 2.414s — OK`)**.

---

## 4. Masalah yang Belum Selesai (Di Luar Cakupan Tahap A)

1. **Instalasi Dependency Ekstraksi Video & Deep Learning pada Environment Lokal**:
   - Paket `opencv-python` (`cv2`), `mediapipe`, dan `torch` belum terpasang pada instalasi Python lokal (`Python 3.11.0b4`). Kini ketiadaan paket tersebut sudah ditangkap dengan aman dan menghasilkan pesan instruksi instalasi yang jelas (`RuntimeError`).
2. **Ketersediaan Fisik Dataset yang Masih `BLOCKED` / `NOT AVAILABLE`**:
   - **WL-BISINDO** ($\approx 1.600$ video) & **WLASL-300** ($5.117$ entri video) masih `BLOCKED` menunggu konfigurasi `~/.kaggle/kaggle.json`.
   - **SignBridge-Kelas** ($960$ video rekaman tim) & **Rekaman Suara Kelas** ($60$ berkas `.wav` di `data/audio/wavs/`) masih berstatus `NOT AVAILABLE` menunggu perekaman fisik.
3. **Skrip Lain di Repositori yang Belum Masuk Daftar Tahap A**:
   - `scripts/extract_rgb_features.py` dan `signbridge/data/dataset.py` (`SignDataset._load_kp` / `_load_rgb`) belum diubah pada Tahap A agar perubahan tetap terfokus pada daftar file yang diinstruksikan; keduanya dapat dibersihkan pada tahap integrasi preprocessing berikutnya jika disetujui.

---

## 5. Konfirmasi Kepatuhan Batasan Tahap A

- **Tidak ada model training yang dijalankan** (`0` proses training dieksekusi).
- **Tidak ada preprocessing dataset secara massal yang dijalankan** (pengujian hanya dilakukan pada sampel terbatas di direktori sementara `tempfile.mkdtemp` yang langsung dihapus saat `tearDown`).
- **Tidak ada berkas dataset asli yang diubah atau dihapus** (`train.tsv`, `val.tsv`, `test_manual.tsv`, `kelas_sentences.txt`, `metadata.csv`, `metadata_fil.csv`, `ind_sentences.tsv`, `fleurs`, `bisindo_alphabet`, dan `fsl_105` tetap 100% utuh).
- **Tidak ada arsitektur model, kontrak API, maupun skema database yang diubah**.
- **Tidak ada commit atau push ke GitHub yang dilakukan**.

