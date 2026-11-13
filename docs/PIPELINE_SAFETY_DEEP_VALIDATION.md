# Laporan Validasi Mendalam Keamanan Pipeline — SignBridge (Tahap A.1)

- **Tanggal Validasi**: 7 November 2026
- **Workspace**: `C:\Users\PC\Downloads\Semester 5\ML`
- **Branch Git**: `feature/dataset-acquisition`
- **Cakupan Audit**: Validasi mendalam (*Deep Validation*) terhadap seluruh perubahan Tahap A (*Pipeline Safety Audit & Synthetic Fallback Removal*), mencakup integritas data fisik, penghapusan *silent fallback*, pencegahan kebocoran antar-split (*data/split/signer/vocabulary leakage*), dan pemisahan bahasa isyarat pada empat modalitas (`Image`, `Audio`, `Video`, `Text`).

---

## 1. File yang Diperiksa dan Diperkeras

| No | Modalitas / Kategori | Berkas yang Diperiksa | Peran dalam Pipeline | Status Audit Kode |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Image** | [`scripts/crop_hands.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py) | Penemuan citra A–Z, validasi landmark / *pre-centered square crop*, deduplikasi SHA-256 lintas kelas/split, pembuatan manifest | **PASS (Hardened)** |
| 2 | **Image** | [`signbridge/image/train_image.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/image/train_image.py) | `FingerspellDataset`, `crop_and_resize_hand()`, dan runner eksperimen I1/I2/I3 | **PASS (Hardened)** |
| 3 | **Audio** | [`signbridge/audio/train_asr.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py) | `load_wav_waveform()`, `load_audio_dataset_records()`, `verify_audio_splits_disjoint()`, `WhisperASRWrapper` | **PASS (Hardened)** |
| 4 | **Audio** | [`scripts/prepare_kelas_audio.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/prepare_kelas_audio.py) | Pemeriksaan ketersediaan fisik 60 berkas `.wav` suara kelas (`data/audio/metadata.csv`) | **PASS (Hardened)** |
| 5 | **Audio** | [`signbridge/audio/finetune_whisper.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/finetune_whisper.py) | Runner CLI untuk konfigurasi ASR A1–A4 | **PASS** |
| 6 | **Audio** | [`configs/audio_a1_whisper_tiny_zs.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a1_whisper_tiny_zs.yaml), [`configs/audio_a2_whisper_tiny_ft.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a2_whisper_tiny_ft.yaml), [`configs/audio_a3_whisper_base_ft.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a3_whisper_base_ft.yaml), [`configs/audio_a4_whisper_fil.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a4_whisper_fil.yaml) | Konfigurasi eksperimen ASR Bahasa Indonesia (`id_id`) & Filipino (`fil_ph`) | **PASS** |
| 7 | **Video** | [`scripts/extract_keypoints.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py) | Penemuan video `.mp4`/`.webm`/`.MOV`, pemetaan label resmi, pemisahan BISINDO vs FSL-105, pelestarian split resmi & signer | **PASS (Hardened)** |
| 8 | **Video** | [`signbridge/data/dataset.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py) | `SignDataset` (pose keypoints `.npz`/`.npy`, RGB tokens `.npy`, `phonology.csv`, protokol SD & SI/LOSO) | **PASS (Hardened)** |
| 9 | **Video** | [`scripts/extract_rgb_features.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_rgb_features.py) | Ekstraksi offline token RGB VideoMAE `[8, 768]` | **PASS (Hardened)** |
| 10 | **Video** | [`configs/b1_bilstm.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/b1_bilstm.yaml), [`configs/m1_stgcn_proto_phon.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/m1_stgcn_proto_phon.yaml), [`configs/m2_bilstm_attn.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/m2_bilstm_attn.yaml), [`configs/m5_fsl_bisindo_transfer.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/m5_fsl_bisindo_transfer.yaml) | Konfigurasi eksperimen video BISINDO & transfer lintas bahasa FSL-105 | **PASS** |
| 11 | **Text** | [`signbridge/text/train_text.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py) | `_load_tsv_pairs()`, `load_monolingual_tatoeba_tsv()`, `load_and_verify_text_splits()`, `build_text_vocabulary()`, `encode_pairs_with_vocab()` | **PASS (Hardened)** |
| 12 | **Text** | [`scripts/build_text_corpus.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/build_text_corpus.py) | Verifikasi integritas korpus teks paralel & monolingual (`verify_existing_text_corpus()`) | **PASS** |
| 13 | **Text** | [`configs/text_t0_rules.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/text_t0_rules.yaml), [`configs/text_t1_gru.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/text_t1_gru.yaml), [`configs/text_t2_indot5.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/text_t2_indot5.yaml), [`configs/text_t3_mt5.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/text_t3_mt5.yaml) | Konfigurasi model *Gloss-to-Sentence* (B0, T1, T2, T3) | **PASS** |
| 14 | **Test Suite** | [`tests/test_pipeline_safety_audit.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/tests/test_pipeline_safety_audit.py) | Rangkaian 18 pengujian otomatis untuk Tahap A & Tahap A.1 | **PASS (18/18 OK)** |

---

## 2. Temuan Mendalam pada Setiap Modalitas

### 2.1. Image Pipeline (`scripts/crop_hands.py`, `signbridge/image/train_image.py`)
1. **Pembacaan Gambar RGB Asli A–Z**:
   - Seluruh `4.466` citra dibaca langsung dari `data/raw/image/bisindo_alphabet/<A..Z>/` (26 kelas lengkap) dan diverifikasi pikselnya identik 100% dengan citra JPEG sumber.
   - Berkas asli tidak pernah ditimpa; [`run_crop_hands`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L281-L424) menolak eksekusi (`ValueError`) apabila `in_dir == out_dir`.
2. **Audit `hand_lm` pada `crop_and_resize_hand()` & Pemisahan Mode Pre-Centered**:
   - *Temuan Tahap A.1*: Pada Tahap A sebelumnya, `run_crop_hands()` sempat mengirimkan array kosong `np.zeros((0, 3))` ke `crop_and_resize_hand()` untuk memicu pemotongan tengah pada citra Mendeley yang sudah terpusat (`224×224`). Hal ini berisiko menyembunyikan kegagalan deteksi landmark bila kelak MediaPipe digunakan pada citra mentah yang belum terpusat.
   - *Perbaikan Tahap A.1*:
     - Ditambahkan [`validate_hand_landmarks()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L51-L78) dan [`detect_hand_landmarks_strict()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L171-L198). Dalam mode landmark (`use_mediapipe=True`), landmark yang `None`, memiliki `< 21` titik, mengandung `NaN`/`Inf`, atau memiliki rentang *bounding box* nol langsung ditolak dengan `ValueError` (tidak pernah menghasilkan *crop* palsu).
     - Untuk dataset citra yang sudah terpusat dari sumbernya (`224×224×3` seperti Mendeley BISINDO Alphabet), disediakan jalur eksplisit [`prepare_precentered_hand_image()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L201-L223) yang dicatat pada kolom manifest `crop_mode="precentered_square"`.
3. **Temuan Duplikat SHA-256 Lintas Kelas & Pencegahan Kebocoran Split**:
   - *Temuan Audit Fisik*: Dari pemeriksaan hash SHA-256 seluruh `4.466` citra Mendeley (`data/raw/image/bisindo_alphabet/file_hashes_sha256.csv`), ditemukan `4.464` hash unik dan **2 pasang citra yang identik byte-for-byte di dua kelas berbeda**:
     1. `99c4a1565f4c49c05be9badc4be2836d9353e35acd49fe2e76dc08aa86d46e53`: muncul di `B/B_polos gelap_Iphone_13promax.jpg` **dan** `E/E_polos gelap_Iphone_13promax.jpg`.
     2. `a99273b2ca82794cb612bc3ace480521ae73d2cb41d6f406bbc14d586d095aa0`: muncul di `D/D_Polos Gelap_iPhone_XR.jpeg` **dan** `P/P_Polos Gelap_iPhone_XR.jpeg`.
   - Selain itu, pembagian split dengan pola selang-seling (`i % 5`) berisiko memisahkan foto berurutan dari sesi pemotretan yang sama ke `train` dan `test`.
   - *Perbaikan Tahap A.1*:
     - [`run_crop_hands(..., deduplicate_sha256=True)`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L310-L345) menyaring duplikat SHA-256 lintas kelas maupun dalam kelas sebelum pembagian split, serta membagi split secara **blok kontigu per kelas** (`60% train`, `20% val`, `20% test`) agar tangkapan layar berurutan berada pada blok yang sama.
     - [`verify_image_manifest_no_leakage()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/crop_hands.py#L226-L278) dan [`FingerspellDataset.__init__`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/image/train_image.py#L140-L195) memverifikasi bahwa tidak ada `sha256`, `source_path`, atau `path` yang bocor antar-split `train`, `val`, dan `test`.

### 2.2. Audio Pipeline (`signbridge/audio/train_asr.py`, `scripts/prepare_kelas_audio.py`)
1. **Validasi Waveform, Sample Rate 16 kHz, dan Transkripsi**:
   - [`load_wav_waveform(wav_path, expected_sr=16000)`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py#L160-L247) membaca RIFF WAVE PCM 16/32-bit maupun IEEE float 32-bit (`fmt_tag=3` pada FLEURS `id_id`), serta melempar `ValueError` jika `sample_rate != 16000`.
   - [`load_audio_dataset_records()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py#L295-L415) memetakan berkas WAV ke transkripsi berdasarkan kolom `file_name` / `file` secara eksak dan melempar `ValueError` apabila terdapat berkas WAV dengan transkripsi kosong.
2. **Penghapusan Transkripsi Dummy pada `WhisperASRWrapper`**:
   - *Temuan Tahap A.1*: Pada [`WhisperASRWrapper.transcribe_waveform()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py#L508-L526), meskipun spektrogram telah dihitung dari waveform asli, baris akhir masih mengembalikan kalimat hardcoded `"Selamat pagi anak-anak hari ini kita belajar..."` bila dekoder penuh tidak dimuat.
   - *Perbaikan Tahap A.1*: Kalimat dummy tersebut **dihapus sepenuhnya**. Apabila `decoder_fn` belum dimuat untuk inferensi transkripsi penuh, `transcribe_waveform()` kini melempar `RuntimeError` eksplisit dan menolak mengembalikan teks palsu.
3. **Kejujuran Status Split & Pencegahan Kebocoran Split Audio**:
   - Ditambahkan [`verify_audio_splits_disjoint()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/audio/train_asr.py#L418-L474) yang menolak irisan berkas WAV antara `train`, `val` (`dev`), dan `test`.
   - Konfigurasi [`configs/audio_a2_whisper_tiny_ft.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a2_whisper_tiny_ft.yaml) dan [`configs/audio_a3_whisper_base_ft.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a3_whisper_base_ft.yaml) masih mengarah ke `data/audio/metadata.csv` (60 rekaman suara kelas yang status fisiknya `NOT AVAILABLE`) dan `data/audio/fleurs_id/train.tsv` (sedangkan di disk baru tersedia `data/audio/fleurs/id_id/audio/dev/` sebanyak 350 WAV). Loader secara jujur menghentikan eksekusi dengan `FileNotFoundError (STATUS: NOT AVAILABLE)` dan tidak pernah menggunakan `dev.tsv` sebagai pengganti diam-diam untuk `train` dan `test` secara bersamaan.

### 2.3. Video Pipeline (`scripts/extract_keypoints.py`, `signbridge/data/dataset.py`, `scripts/extract_rgb_features.py`)
1. **Penghapusan *Silent Synthetic Fallback* Tersembunyi di `SignDataset` dan `extract_rgb_features.py`**:
   - *Temuan Kritis Tahap A.1*:
     - Di dalam [`SignDataset._filter_split()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L196-L198) versi sebelumnya, terdapat blok `if not selected and rows: selected = list(rows)` yang secara diam-diam **menyalin seluruh data `train` menjadi `val`/`test`** bila split yang diminta kosong!
     - Di dalam [`SignDataset._load_kp()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L247-L258) dan [`SignDataset._load_rgb()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L267-L270) versi sebelumnya, jika berkas `.npz`/`.npy` tidak ditemukan di disk, loader secara diam-diam membangkitkan keypoint sinusoidal sintetis dan token RGB `np.sin(... + label * 0.4)` yang **membocorkan label ground-truth ke dalam fitur input**!
     - Di dalam [`scripts/extract_rgb_features.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_rgb_features.py#L27-L45) versi sebelumnya, skrip memanggil `ensure_demo_dataset()` dan membuat token acak `rng.standard_normal` ditambah sinyal kelas `tokens[:, (label * 16)...] += 1.25`.
   - *Perbaikan Tahap A.1*:
     - Seluruh *fallback* sintetis di [`SignDataset._load_kp()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L374-L398), [`SignDataset._load_rgb()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L400-L418), [`SignDataset._filter_split()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L326-L330), dan [`scripts/extract_rgb_features.py`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_rgb_features.py#L22-L85) **dihapus total**.
     - Ketidaktersediaan berkas `.npz`/`.npy` atau split yang kosong kini langsung melempar `FileNotFoundError` / `ValueError`.
     - Untuk model yang hanya menggunakan cabang pose (`rgb_path=""`), `_load_rgb()` mengembalikan tensor nol netral `np.zeros((8, 768))` tanpa kebocoran label.
2. **Pemisahan Ketat `FSL-105` dan `BISINDO`**:
   - [`resolve_video_gloss_and_label()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py#L121-L173) menolak penggunaan `labels.csv` non-BISINDO ketika `source="bisindo"`, dan mewajibkan `labels.csv` ketika `source="fsl"`.
   - [`SignDataset._read_manifest()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/data/dataset.py#L156-L185) menolak manifest yang mencampur lebih dari satu `source` (mis. `bisindo` dan `fsl`) kecuali diberikan `source_filter` eksplisit.
3. **Pelestarian Split Resmi & Signer Metadata**:
   - [`load_official_split_map()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py#L176-L211) membaca `train.csv` (`1.704` video) dan `test.csv` (`426` video) resmi dari `FSL-105` (`1.704 + 426 = 2.130` video `.MOV`, 0 irisan) alih-alih membagi ulang secara sembarang.
   - [`extract_signer_id()`](file:///C:/Users/PC/Downloads/Semester%205/ML/scripts/extract_keypoints.py#L214-L227) tidak lagi mengarang signer `S01..S06` dengan `idx % 6`; bila nama berkas tidak memuat ID signer (seperti `FSL-105`), nilai yang disimpan adalah `"unannotated"`, dan protokol *Signer-Independent* (`protocol="si"`) di `SignDataset` menolak berjalan pada dataset `"unannotated"`.

### 2.4. Text Pipeline (`signbridge/text/train_text.py`, `scripts/build_text_corpus.py`)
1. **Validasi Pasangan Paralel & Penolakan Tatoeba Monolingual**:
   - [`_load_tsv_pairs()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py#L206-L260) mewajibkan kolom `gloss` dan `kalimat` (atau `sentence`), serta menolak `data/text/tatoeba/ind_sentences.tsv` (`28.418` kalimat monolingual) dengan `ValueError` eksplisit.
2. **Pencegahan Kebocoran Dua Arah (`gloss` dan `kalimat`)**:
   - [`load_and_verify_text_splits()`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py#L307-L372) kini memeriksa irisan antara `test_manual.tsv` terhadap `train.tsv` dan `val.tsv` baik pada **kalimat target (`kalimat`)** maupun **urutan gloss sumber (`gloss`)**, serta memeriksa irisan kalimat antara `train.tsv` dan `val.tsv`.
   - Verifikasi pada data fisik SignBridge saat ini (`170` train, `30` val, `105` test_manual) menunjukkan **0 irisan kalimat** dan **0 irisan gloss** antara `test_manual.tsv` dengan `train.tsv`/`val.tsv`.
3. **Pembentukan Vocabulary Eksklusif dari `train.tsv`**:
   - Ditambahkan [`build_text_vocabulary(train_pairs)`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py#L375-L395) dan [`encode_pairs_with_vocab(pairs, vocab)`](file:///C:/Users/PC/Downloads/Semester%205/ML/signbridge/text/train_text.py#L398-L426) sehingga kamus token hanya di-*fit* pada `train_pairs`; kata yang hanya muncul di `val` atau `test_manual` dipetakan ke `<unk>` (`3`).

---

## 3. Pengujian Otomatis yang Dijalankan (`tests/test_pipeline_safety_audit.py`)

Perintah pengujian yang dijalankan:
```powershell
python -m unittest tests/test_pipeline_safety_audit.py -v
```
Seluruh **18 unit test** lulus (`Ran 18 tests in 2.816s — OK`):

| ID Test | Nama Fungsi Test | Cakupan Validasi | Hasil |
| :--- | :--- | :--- | :--- |
| **Test 01** | `test_01_video_no_synthetic_fallback_and_empty_dir_error` | `ensure_demo_dataset` tidak diimpor di `extract_keypoints.py`; folder hilang/kosong melempar `FileNotFoundError` | **PASS** |
| **Test 02** | `test_02_video_extensions_mov_case_insensitive_and_fsl105_discovery` | Deteksi `.MOV`/`.mov`/`.mp4`/`.MP4`/`.webm`/`.WEBM`, abaikan `._*`, temukan `2.130` `.MOV` & `105` kelas `FSL-105` | **PASS** |
| **Test 03** | `test_03_video_unknown_gloss_and_missing_dependency_errors` | Video 0-byte melempar `ValueError`; ketiadaan `cv2`/`mediapipe` melempar `RuntimeError` jelas | **PASS** |
| **Test 04** | `test_04_image_empty_and_corrupt_input_errors` | Folder gambar kosong, file JPEG rusak, dan manifest hilang ditolak eksplisit | **PASS** |
| **Test 05** | `test_05_image_crops_match_real_source_rgb_pixels` | `4.466` citra A–Z Mendeley ditemukan; piksel `.npy` identik 100% dengan JPEG sumber | **PASS** |
| **Test 06** | `test_06_audio_no_synthetic_sine_and_reports_not_available` | `write_sine_wav` dihapus; 60 audio kelas dilaporkan `NOT AVAILABLE` tanpa mengubah `metadata.csv` | **PASS** |
| **Test 07** | `test_07_audio_reads_real_fleurs_id_id_wavs` | Membaca WAV IEEE float 32-bit `16.000 Hz` asli dari Google FLEURS `id_id` & menghitung spektrogram 80-mel | **PASS** |
| **Test 08** | `test_08_text_loads_real_tsv_and_rejects_tatoeba_as_gloss_pairs` | Membaca TSV paralel asli (`170`/`30`/`105`) dan menolak Tatoeba (`28.418` baris) sebagai pasangan paralel | **PASS** |
| **Test 09** | `test_09_text_prevents_test_set_leakage_into_train_or_val` | Kebocoran kalimat `test_manual.tsv` ke `train.tsv` langsung melempar `ValueError` | **PASS** |
| **Test 10** | `test_10_image_without_valid_landmarks_rejected` | Landmark `None`, kosong `(0,3)`, `<21` titik, `NaN`, atau bbox kolaps ditolak dengan `ValueError` | **PASS** |
| **Test 11** | `test_11_image_duplicate_across_splits_and_cross_class_sha256_filtered` | Duplikat gambar (`sha256` / `source_path`) lintas split ditolak oleh `verify_image_manifest_no_leakage` & `FingerspellDataset` | **PASS** |
| **Test 12** | `test_12_audio_wav_without_transcription_and_split_leakage_rejected` | WAV tanpa transkripsi ditolak (`ValueError`), kebocoran WAV lintas split ditolak, dan transkripsi dummy Whisper dihapus (`RuntimeError`) | **PASS** |
| **Test 13** | `test_13_audio_wav_with_wrong_sample_rate_rejected` | WAV dengan sample rate `8.000 Hz` dan `44.100 Hz` ditolak oleh `load_wav_waveform(..., expected_sr=16000)` | **PASS** |
| **Test 14** | `test_14_video_corrupt_or_missing_keypoints_and_rgb_rejected_in_signdataset` | `SignDataset` menolak `.npz` hilang (`FileNotFoundError`) atau seluruhnya `NaN` (`ValueError`); `extract_rgb_features` menolak membuat demo dataset | **PASS** |
| **Test 15** | `test_15_video_unknown_label_and_empty_split_rejected` | Video dengan label tidak dikenal dan manifest dengan split kosong ditolak (`ValueError`) | **PASS** |
| **Test 16** | `test_16_video_fsl_and_bisindo_separation_enforced` | Pencampuran `FSL-105` dan `BISINDO` ditolak di `extract_keypoints` & `SignDataset`; split resmi `FSL-105` (`1.704` train, `426` test) terverifikasi | **PASS** |
| **Test 17** | `test_17_text_train_test_leakage_both_gloss_and_sentence` | Kebocoran urutan `gloss` dari `test` ke `train` (meskipun kalimat berbeda) terdeteksi dan ditolak (`ValueError`) | **PASS** |
| **Test 18** | `test_18_text_vocabulary_fitted_strictly_without_test_set` | `build_text_vocabulary` hanya memuat kata dari `train_pairs`; kata eksklusif `test` dipetakan ke `<unk>` (`3`) | **PASS** |

---

## 4. Ringkasan Status per Modalitas (`PASS` / `FAIL` / `BLOCKED`)

| Modalitas | Keamanan Kode & Loader (Tahap A.1) | Kesiapan Eksekusi Preprocessing & Training pada Environment Lokal | Detail Status |
| :--- | :---: | :---: | :--- |
| **1. IMAGE (BISINDO Alphabet A–Z)** | **PASS** | **READY FOR PREPROCESSING (`crop_hands.py`)** / **TRAINING BLOCKED BY `torch`** | `4.466` citra RGB (`4.462` setelah deduplikasi 2 pasang SHA-256 lintas kelas) siap diproses dengan `scripts/crop_hands.py` karena hanya membutuhkan `numpy` + `Pillow` (sudah terpasang). Pelatihan `train_image.py` membutuhkan instalasi `torch`. |
| **2. TEXT (Gloss-to-Sentence & Tatoeba)** | **PASS** | **READY FOR B0 RULES** / **NEURAL T1–T3 BLOCKED BY `torch`** | `train.tsv` (`170`), `val.tsv` (`30`), `test_manual.tsv` (`105`), dan `ind_sentences.tsv` (`28.418`) tersedia dan bebas bocor. Baseline aturan `B0` dapat dijalankan sekarang; model neural `T1`/`T2`/`T3` membutuhkan `torch` (dan `transformers` untuk IndoT5/mT5). |
| **3. AUDIO (FLEURS `id_id` & Kelas)** | **PASS** | **PARTIAL (`dev` 350 WAV tersedia)** / **FINE-TUNING BLOCKED** | `350` berkas `.wav` `16 kHz` di `data/audio/fleurs/id_id/audio/dev/` siap dibaca untuk evaluasi prototipe. Namun `train.tar.gz`/`test.tar.gz` FLEURS belum diunduh, `60` berkas `.wav` suara kelas masih `NOT AVAILABLE`, dan `torch`/`transformers` belum terpasang. |
| **4. VIDEO (`FSL-105`, `WL-BISINDO`, `WLASL-300`, `SignBridge-Kelas`)** | **PASS** | **BLOCKED BY DEPENDENCIES (`cv2`, `mediapipe`, `torch`) & BISINDO VIDEO DATA** | `FSL-105` (`2.130` `.MOV`, `train.csv` `1.704`, `test.csv` `426`) tersedia secara fisik di disk, tetapi ekstraksi keypoint 86-node membutuhkan `pip install opencv-python mediapipe`. Dataset video utama Bahasa Indonesia (`WL-BISINDO` & `SignBridge-Kelas`) serta video fisik `WLASL-300` masih `BLOCKED` / `NOT AVAILABLE`. |

---

## 5. Risiko yang Masih Tersisa

1. **Ketergantungan Paket Python yang Belum Terpasang di Environment Lokal**:
   - Environment Python `3.11.0b4` saat ini baru memiliki `numpy`, `Pillow`, dan `PyYAML`. Paket `opencv-python`, `mediapipe`, `torch`, dan `transformers` belum terpasang, sehingga ekstraksi keypoint video (`scripts/extract_keypoints.py`) dan pelatihan jaringan saraf akan berhenti dengan pesan error dependency eksplisit.
2. **Ketidaklengkapan Dataset Fisik pada Modalitas Video BISINDO dan Audio Kelas**:
   - **Video BISINDO**: `WL-BISINDO` (target ~1.600 video, 32 gloss) masih `BLOCKED` oleh kredensial Kaggle, dan `SignBridge-Kelas` (target 960–3.000 video) masih `NOT AVAILABLE` (membutuhkan perekaman).
   - **Audio Kelas & FLEURS Train/Test**: `60` berkas `.wav` di `data/audio/metadata.csv` masih `NOT AVAILABLE`, dan arsip audio `train.tar.gz` (`2.579` kalimat) serta `test.tar.gz` (`687` kalimat) Google FLEURS `id_id` belum diunduh (baru tersedia `dev/` `350` WAV).
3. **Ketidaksesuaian Path Default pada Beberapa Berkas Konfigurasi YAML Lama**:
   - [`configs/audio_a1_whisper_tiny_zs.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/audio_a1_whisper_tiny_zs.yaml) mengacu ke `data/audio/fleurs_id/test.tsv` (sedangkan path aktual di disk adalah `data/audio/fleurs/id_id/dev.tsv` dan `test.tsv`).
   - [`configs/m5_fsl_bisindo_transfer.yaml`](file:///C:/Users/PC/Downloads/Semester%205/ML/configs/m5_fsl_bisindo_transfer.yaml) menggunakan `source_filter: [bisindo, fsl]` pada satu `data/manifest.csv` gabungan; dengan guard keamanan baru di `SignDataset`, penggunaan `source_filter` multi-bahasa wajib disetel dengan `allow_mixed_sources=True` hanya pada tahap *joint pretraining*, atau menggunakan dua manifest terpisah (`manifest_fsl105.csv` untuk pretraining lalu `manifest_bisindo.csv` untuk fine-tuning).
4. **Ketiadaan Metadata Signer pada `FSL-105`**:
   - Berkas video `FSL-105` (`clips/<0..104>/<id>.MOV`) tidak menyertakan identitas signer per klip, sehingga dicatat sebagai `signer="unannotated"`. Oleh karena itu, `FSL-105` hanya boleh dievaluasi dengan split resmi `train.csv` / `test.csv` (`protocol="sd"`), dan tidak boleh dijalankan dengan protokol *Leave-One-Signer-Out* (`protocol="si"`).

---

## 6. Perbaikan yang Wajib Dilakukan Sebelum Preprocessing & Training Dimulai

1. **Instalasi Dependency Wajib pada Environment Python**:
   - Pasang `opencv-python`, `mediapipe`, dan `torch` sebelum menjalankan ekstraksi keypoint video atau pelatihan model.
2. **Jangan Menjalankan Preprocessing Video BISINDO atau Audio Kelas Sebelum Berkas Fisiknya Tersedia**:
   - Hanya jalankan preprocessing pada dataset yang berkas fisiknya sudah 100% terverifikasi di disk:
     - **Image**: `data/raw/image/bisindo_alphabet/` (`4.466` JPEG A–Z) -> siap diproses ke `data/images/mendeley_crops/`.
     - **Video (Eksperimen Lintas Bahasa FSL)**: `data/raw/video/fsl_105/clips/` (`2.130` `.MOV`) -> siap diekstrak ke `data/keypoints/fsl_105/` **setelah** `opencv-python` dan `mediapipe` dipasang.
     - **Text**: `data/text/train.tsv`, `val.tsv`, `test_manual.tsv` -> sudah siap tanpa preprocessing tambahan.

---

## 7. Perintah yang Aman untuk Tahap Berikutnya

Berikut adalah urutan perintah yang **aman** dijalankan pada tahap berikutnya (setelah mendapat persetujuan Anda):

### A. Menjalankan Ulang Pengujian Keamanan Pipeline (Aman dijalankan kapan saja)
```powershell
python -m unittest tests/test_pipeline_safety_audit.py -v
```

### B. Preprocessing Modalitas Image — BISINDO Alphabet A–Z (Dapat dijalankan sekarang tanpa dependency tambahan)
Memproses `4.466` citra RGB asli dari Mendeley (`data/raw/image/bisindo_alphabet`), menyaring 2 pasang duplikat SHA-256 lintas kelas (`4.462` citra bersih), dan menulis hasil `.npy` `[224, 224, 3]` beserta manifest bebas bocor:
```powershell
python scripts/crop_hands.py --in data/raw/image/bisindo_alphabet --out data/images/mendeley_crops --manifest data/images/manifest_images_mendeley.csv --require-all-classes
```

### C. Evaluasi Baseline Aturan Teks `B0` pada `test_manual.tsv` (Dapat dijalankan sekarang tanpa `torch`)
```powershell
python -m signbridge.text.train_text --config configs/text_t0_rules.yaml
```

### D. Instalasi Dependency Sebelum Ekstraksi Keypoint Video `FSL-105`
```powershell
pip install opencv-python mediapipe torch
```
Setelah terpasang, ekstraksi keypoint 86-node untuk `FSL-105` (`2.130` `.MOV` dengan split resmi `train.csv` `1.704` & `test.csv` `426`) dapat dijalankan secara terpisah dari BISINDO:
```powershell
python scripts/extract_keypoints.py --raw-dir data/raw/video/fsl_105/clips --out-dir data/keypoints/fsl_105 --manifest data/manifest_fsl105.csv --source fsl --labels-csv data/raw/video/fsl_105/labels.csv
```

