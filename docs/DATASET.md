# Dokumentasi Dataset Multimodal (`docs/DATASET.md`)

## 1. Daftar Dataset Acuan & Sumber Eksternal
Sesuai `Modul Baru.pdf`, arsitektur SignBridge dirancang untuk memproses dataset berikut:

| Modalitas | Nama Dataset | Sumber | Lisensi / Akses | Kegunaan |
| :--- | :--- | :--- | :--- | :--- |
| **Video + Keypoint** | WL-BISINDO | Kaggle (`glennleonali/wl-bisindo`) | Akademik / Riset | Pengenalan kata isyarat BISINDO |
| **Video + Keypoint** | WLASL-300 | Kaggle / GitHub WLASL | Akademik Non-Komersial | Pretraining lintas-bahasa (X1, M4) |
| **Video + Keypoint** | FSL-105 | Mendeley Data | CC BY 4.0 | Eksperimen Bahasa Isyarat Filipina (X2–X4) |
| **Video + Keypoint** | `SignBridge-Kelas` | Rekaman Mandiri Tim | Internal Tim (dengan persetujuan) | Penambahan 3 signer baru $\times 32$ gloss $\times 10$ repetisi (target 960 klip baru; target total gabungan $\ge 3.000$ sampel) |
| **Gambar** | BISINDO Alphabet Image Data | Mendeley Data + Crop Tangan Tim | CC BY 4.0 | Klasifikasi Ejaan Jari Statis 26 Huruf (`A`–`Z`, $224 \times 224$) |
| **Audio** | Google FLEURS (`id_id`) + Rekaman Kelas | HuggingFace (`google/fleurs`) | CC BY 4.0 | Evaluasi & fine-tuning Whisper ASR (`A1`–`A3`) |
| **Teks** | Tatoeba Indonesian + Kalimat Kelas + `test_manual.tsv` | Tatoeba.org & Kurasi Tim | CC BY 2.0 FR / Internal | Pelatihan `GLOSS -> Kalimat` (`T1`–`T3`) & evaluasi uji manusia (`105` kalimat) |

---

## 2. Statistik Aktual Berkas Data yang Tersedia di Repository Saat Ini
Berdasarkan audit faktual pada folder [`data/`](file:///d:/SEMESTER%205/ML/Projek_1/data) di repository lokal saat ini:

| Berkas di Repository | Ukuran Aktual | Jumlah Baris / Sampel Aktual | Keterangan Verifikasi |
| :--- | :--- | :--- | :--- |
| [`data/bridge/concepts.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/bridge/concepts.csv) | `3.552 B` | **32 konsep** (`C01`–`C32`) | Sinkron 100% dengan [`web/model/labels.json`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/labels.json) |
| [`data/phonology.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/phonology.csv) | `496 B` | **32 baris gloss** | 4 atribut fonologi Stokoe (`handshape`, `location`, `movement`, `two_handed`), 0 nilai kosong |
| [`data/text/kelas_sentences.txt`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/kelas_sentences.txt) | `14.830 B` | **200 kalimat** | Kalimat domain kelas inklusif Indonesia & Filipina |
| [`data/text/train.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/train.tsv) | `22.565 B` | **170 pasangan** (`gloss`, `kalimat`) | Data latih penyusunan kalimat |
| [`data/text/val.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/val.tsv) | `4.483 B` | **30 pasangan** (`gloss`, `kalimat`) | Data validasi penyusunan kalimat |
| [`data/text/test_manual.tsv`](file:///d:/SEMESTER%205/ML/Projek_1/data/text/test_manual.tsv) | `6.727 B` | **105 pasangan** (`gloss`, `kalimat`) | Uji kurasi manusia; **0% tumpang-tindih (0 kebocoran data)** terhadap `train.tsv` |
| [`data/audio/metadata.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/audio/metadata.csv) | `5.334 B` | **60 baris metadata** | Metadata ucapan kelas Bahasa Indonesia |
| [`data/audio/metadata_fil.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/audio/metadata_fil.csv) | `1.849 B` | **24 baris metadata** | Metadata ucapan kelas Bahasa Filipino |
| [`web/model/fingerspell.json`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/fingerspell.json) | `211 B` | **26 label huruf** (`A`–`Z`) | Label model ejaan jari statis |

> **Catatan Kejujuran Data**: Dataset video mentah eksternal berukuran puluhan GB (WL-BISINDO, WLASL-300, FSL-105) dan rekaman penuh 960 klip `SignBridge-Kelas` belum diunduh ke dalam direktori lokal ini. Pipa konversi rekaman mandiri ([`scripts/web_record_to_npz.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/web_record_to_npz.py) dan [`scripts/merge_manifests.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/merge_manifests.py)) serta tabel metadata `dataset_recordings` di PostgreSQL telah siap digunakan untuk melacak setiap rekaman menuju target $\ge 3.000$ sampel.

---

## 3. Spesifikasi Preprocessing & Pembagian Split
1. **Video & Keypoint (Kontrak 1 & 3)**:
   - Ekstraksi 86 titik dari MediaPipe Holistic: `9` pose tubuh atas (`[0:9]`), `21` tangan kiri (`[9:30]`), `21` tangan kanan (`[30:51]`), dan `35` titik wajah (`[51:86]`).
   - Pemangkasan frame tidak aktif (`trim_inactive`), normalisasi berpusat pada titik tengah bahu & skala lebar bahu (`normalize_pose`), dan *resampling* linear ke `64` frame (`[64, 86, 3]`).
   - **Protokol Split**:
     - *Signer-Dependent (SD)*: `60% train / 10% val / 30% test`.
     - *Signer-Independent (SI / LOSO)*: *Leave-One-Signer-Out* melalui parameter `--protocol si --test-signer <signer_id>`.
2. **Gambar Ejaan Jari (Kontrak 4 & 5)**:
   - Pemotongan kotak persegi di sekitar 21 titik tangan dengan margin `+25%`, *resize* bilinear ke $224 \times 224$, dan normalisasi ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).

