# Panduan Akuisisi Dataset Multimodal SignBridge (`docs/DATASET_ACQUISITION.md`)
**Branch Pengembangan**: `feature/dataset-acquisition`  
**Proyek**: SignBridge ID–PH (BISINDO $\leftrightarrow$ FSL)

---

## 1. Tujuan & Kebijakan Penyimpanan Git

Dokumen ini mendefinisikan prosedur standar akuisisi, validasi, ekstraksi *keypoint*, dan pencatatan metadata untuk keempat modalitas **SignBridge** (Video, Citra/Fingerspelling, Audio, dan Teks).

> [!IMPORTANT]
> **Aturan Kebersihan Repositori Git**:
> - Berkas media mentah berukuran besar (`*.mp4`, `*.webm`, `*.wav`, `*.npz`, `*.zip`, serta checkpoint `*.pt`) **dikecualikan** melalui [`.gitignore`](file:///d:/SEMESTER%205/ML/Projek_1/.gitignore) dan **dilarang** di-commit ke GitHub.
> - Hanya berkas manifes, kamus fonologi, skrip akuisisi/konversi, dan metadata ringan (`data/bridge/concepts.csv`, `data/phonology.csv`, `data/text/*.tsv`, `data/audio/metadata*.csv`) yang disimpan di dalam repositori Git.

---

## 2. Struktur Direktori Akuisisi Data Lokal

```text
data/
├── phonology.csv                # [Dilacak Git] 32 kata BISINDO/FSL & parameter Stokoe
├── PHONOLOGY_GUIDE.md           # [Dilacak Git] Panduan parameter anatomis isyarat
├── bridge/
│   └── concepts.csv             # [Dilacak Git] 32 konsep inti ID <-> FIL (C01..C32)
├── text/
│   ├── train.tsv                # [Dilacak Git] 170 pasangan latih (gloss -> kalimat)
│   ├── val.tsv                  # [Dilacak Git] 30 pasangan validasi
│   ├── test_manual.tsv          # [Dilacak Git] 105 pasangan uji manusia disjoint
│   └── kelas_sentences.txt      # [Dilacak Git] 200 kalimat ruang kelas inklusif
├── audio/
│   ├── metadata.csv             # [Dilacak Git] Metadata ucapan Bahasa Indonesia (60 baris)
│   ├── metadata_fil.csv         # [Dilacak Git] Metadata ucapan Bahasa Filipino (24 baris)
│   └── raw_wav/                 # [Diabaikan Git] Rekaman .wav 16kHz PCM mono
├── raw/                         # [Diabaikan Git] Video mentah (.mp4 / .webm) & citra (.jpg / .png)
│   ├── wl_bisindo/
│   ├── fsl_105/
│   ├── fingerspell_az/
│   └── selfrec/
└── keypoints/                   # [Diabaikan Git] Tensor keypoint 86 titik (.npz)
    └── selfrec/
```

---

## 3. Alur Akuisisi per Modalitas

### 3.1 Modalitas 1 — Video Isyarat (32 Kata BISINDO & FSL)
1. **Akuisisi Mandiri melalui Studio Web (`SignBridge-Kelas`)**:
   - Buka aplikasi pada tab **Rekam Dataset Mandiri** (`http://localhost:8080`).
   - Pilih ID Penutur (`S01`, `S02`, dst.), kategori (`Kata Isyarat 32 Gloss`), dan target kata.
   - Tekan **Simpan Klip ke Antrean**:
     - Aplikasi mengekstrak sekuens `[64, 86, 3]` dari kamera aktif dan otomatis mengirim metadata ke PostgreSQL melalui `POST /db/recordings` (tabel `dataset_recordings`).
   - Tekan **Unduh Paket Dataset (.zip)** untuk mengunduh bundel rekaman beserta `manifest.csv`.
   - Konversi bundel ke format `.npz` pelatihan menggunakan:
     ```bash
     python scripts/web_record_to_npz.py --input data/raw/selfrec --output data/keypoints/selfrec
     python scripts/merge_manifests.py --manifests data/keypoints/selfrec/manifest.csv --out data/manifest_combined.csv
     ```
2. **Akuisisi Dataset Eksternal (`WL-BISINDO`, `WLASL-300`, `FSL-105`)**:
   - Unduh korpus video ke `data/raw/<nama_dataset>/` dan jalankan ekstraktor MediaPipe Holistic 86 titik menuju `data/keypoints/`.

### 3.2 Modalitas 2 — Citra Ejaan Jari Statis (26 Abjad A–Z)
1. Tempatkan foto tangan per kelas huruf (`A`..`Z`) pada `data/raw/fingerspell_az/<HURUF>/`.
2. Pipeline pelatihan [`signbridge/image/train_image.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/train_image.py) menerapkan pemotongan kotak tangan persegi `+25%` ([`crop_and_resize_hand`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/image/crop.py#L48-L83)) ke ukuran `224x224` dan normalisasi ImageNet sebelum melatih `MobileNetV3-Small` (`I1`) dan mengekspor `web/model/fingerspell.onnx`.

### 3.3 Modalitas 3 — Audio Ucapan Ruang Kelas (ID & FIL)
1. Simpan berkas audio WAV PCM 16kHz mono pada `data/audio/raw_wav/` sesuai daftar nama berkas di [`data/audio/metadata.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/audio/metadata.csv) (`id`) dan [`data/audio/metadata_fil.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/audio/metadata_fil.csv) (`fil`).
2. Evaluasi WER, CER, dan RTF dijalankan melalui [`signbridge/audio/train_asr.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/audio/train_asr.py).

### 3.4 Modalitas 4 — Teks Gloss-ke-Kalimat & Jembatan Konsep
1. Pastikan seluruh penambahan pasangan kalimat pada [`data/text/train.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/train.tsv) tetap menjaga **0% tumpang-tindih kalimat** terhadap [`data/text/test_manual.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/test_manual.tsv) (diverifikasi otomatis oleh `test_text_modality_and_disjoint_manual_test` di [`tests/test_signbridge_suite.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_signbridge_suite.py#L230-L259)).

---

## 4. Pelacakan & Validasi di Database PostgreSQL (`dataset_recordings`)

Setiap rekaman yang diakuisisi dicatat di tabel `dataset_recordings` dengan atribut:
- `recording_code` (unik, contoh: `S01_GLOSS_HALO_001`)
- `signer_id`, `gloss`, `repetition`, `duration`
- `file_path` & `keypoint_path`
- `consent_status` (`approved` / `pending` / `revoked`)
- `validation_status` (`valid` / `pending` / `rejected`)

Verifikasi status rekaman dapat dilakukan kapan saja melalui endpoint `GET http://localhost:7860/db/recordings`.
