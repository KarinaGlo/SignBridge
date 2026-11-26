# PROTOKOL & SPESIFIKASI DATASET MULTIMODAL SIGNBRIDGE (TASK P0-B)
**Proyek:** SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge  
**Fokus Arsitektur:** M6 — Four-Modality Multimodal Fusion Network  
**Lokasi Direktori:** `D:\SEMESTER 5\ML\Projek_1`  
**Tanggal:** 20 November 2026  
**Status Audit & Protokol:** FINAL SPECIFICATION — ACUAN RESMI P0-C & P0-D  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Tahap **P0-B (Dataset Protocol Audit & Specification)** bertujuan untuk mengaudit kondisi faktual data dan menetapkan spesifikasi dataset multimodal berpasangan (*paired dataset*) 4 modalitas (Video, Image, Audio, Text) yang kompatibel 100% dengan model M6 di repository SignBridge.

### Temuan Faktual Kunci dari Audit:
1. **Model M6 Membutuhkan Data Berpasangan (Paired) yang Saat Ini Nol:**  
   Arsitektur M6 (`signbridge/models/multimodal.py`) memproses 4 modalitas secara simultan dalam satu jendela waktu 2,5 detik. Saat ini, repository memiliki 8.620 gambar statis Mendeley, 1.600 entri manifest WL-BISINDO (tanpa file `.npz` di disk), 3.613 metadata FLEURS (tanpa file `.wav` di disk), dan ribuan kalimat Tatoeba terisolasi. **Jumlah sampel yang menggabungkan 4 modalitas berpasangan secara simultan adalah 0 (NOL).**
2. **Dua Sistem Kosakata yang Berbeda (Duality of Vocabularies):**  
   Audit menemukan inkonsistensi mendasar antara dokumentasi dan kode:
   - **Vocabulary Set A (32 Konsep Kelas Pedagogis):** Terdaftar di `data/bridge/concepts.csv`, `data/phonology.csv`, `server/database.py` (`SignConcept`), dan `data/text/train.tsv` (`HALO`, `GURU`, `BUKU`, `TUGAS`, `KELAS`, dll.).
   - **Vocabulary Set B (32 Benchmark WL-BISINDO):** Terdaftar di `signbridge/constants.py` (`BISINDO_32_GLOSSES`), `web/model/labels.json`, `web/js/config.js`, dan dievaluasi langsung oleh model M6 (`AIR`, `BELAJAR`, `CARI`, `HARI`, `INGAT`, `MAKAN`, dll.).
   - **Keputusan P0-B:** Pipeline M6, loader dataset, dan manifest builder saat ini **hanya menerima Set B**. Setiap rekaman baru harus mengikuti Set B jika ingin diproses oleh M6 tanpa memodifikasi arsitektur model.
3. **Risiko Kebocoran Teks (Text Shortcut Leakage):**  
   Fungsi auto-fill pada antarmuka web recorder (`web/js/app.js:1044`) otomatis mengisi kolom kalimat dengan kata target yang sama persis (misal isyarat `MAKAN` $\to$ kalimat `"Makan."`). Protokol P0-B mewajibkan teks berkedudukan sebagai **kalimat konteks percakapan kelas** (bukan label isyarat).

---

## 2. HASIL AUDIT IMPLEMENTASI M6

Berdasarkan investigasi kode sumber aktual pada `signbridge/models/multimodal.py`, `signbridge/multimodal/constants.py`, dan `signbridge/multimodal/features.py`:

| Modalitas | Input Aktual M6 | Bentuk/Dimensi Tensor | Preprocessing Pipeline | Format Sumber yang Dibutuhkan | Status Kompatibilitas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Video** | `pose` (float32) | `[B, 64, 86, 3]` | `pose_from_sequence`: trim frame diam $\to$ normalisasi pusat bahu $\to$ resample linear 64 frame. Linear velocity dihitung di encoder ($86 \times 3 \times 2 = 516 \to 128$). | File `.json` (MediaPipe 86 koordinat $x,y,z$) atau file video mentah `.mp4` (30 FPS). | **READY** |
| **Image** | `image` (float32) | `[B, 3, 112, 112]` | `load_image`: square center-crop $\to$ resize $112 \times 112 \to$ normalisasi ImageNet mean/std $\to$ channel transpose $(C, H, W)$. | File `.jpg`/`.png` crop telapak tangan utama (resolusi $\ge 112 \times 112$). | **READY** |
| **Audio** | `audio` (float32) | `[B, 64, 248]` | `load_audio`: read WAV PCM 16-bit $\to$ resample linear ke 16 kHz $\to$ potong/pad ke 40.000 sampel $\to$ log-mel filterbank (64 bin, FFT 400, hop 160) $\to$ standarisasi per-klip. | File audio `.wav` mono 16-bit PCM (durasi 2,5 detik, sampling rate $\ge 16 \text{ kHz}$). | **READY** |
| **Text** | `text` (int64) | `[B, 64]` | `encode_text`: lowercased $\to$ tokenisasi level karakter (vocab 49) $\to$ pad dengan 0 hingga panjang 64. | Kalimat string UTF-8 konteks percakapan/dialog kelas inklusi. | **READY** |
| **Mask** | `modality_mask` (float32) | `[B, 4]` | Vector biner `[has_pose, has_img, has_audio, has_text]`. Nilai 0 memicu attention masking (`key_padding_mask`) & score $-10.000$ pada gating. | Dihitung otomatis oleh dataset loader berdasarkan ketersediaan file. | **READY** |

---

## 3. PROTOKOL LABEL DAN GLOSS (LABEL RECONCILIATION)

### A. Temuan Diskrepansi Kosakata
Repository SignBridge memiliki 2 definisi kamus 32 kelas yang berbeda:

1. **Kamus A (Pedagogis / Jembatan Kelas ASEAN):**  
   `['HALO', 'TERIMA_KASIH', 'MAAF', 'TOLONG', 'SAYA', 'KAMU', 'GURU', 'TEMAN', 'MAU', 'SUDAH', 'BELUM', 'BISA', 'TIDAK', 'ADA', 'BELAJAR', 'PAHAM', 'TANYA', 'BACA', 'TULIS', 'JAWAB', 'BUKU', 'TUGAS', 'KELAS', 'SEKOLAH', 'APA', 'SIAPA', 'DIMANA', 'KAPAN', 'BAGAIMANA', 'BAIK', 'BENAR', 'SALAH']`  
   *(Lokasi: `data/bridge/concepts.csv`, `data/phonology.csv`, `server/database.py`)*.
2. **Kamus B (WL-BISINDO Benchmark):**  
   `['AIR', 'BELAJAR', 'CARI', 'HARI', 'INGAT', 'LAGI', 'MAAF', 'MAKAN', 'MOTOR', 'SAYA', 'TERIMA_KASIH', 'TULI', 'APA', 'SIAPA', 'KAPAN', 'DIMANA', 'MENGAPA', 'BAGAIMANA', 'MERAH', 'KUNING', 'HIJAU', 'HITAM', 'DENGAR', 'BERANGKAT', 'DATANG', 'TEMAN', 'KELUARGA', 'RUMAH', 'PAGI', 'SIANG', 'SORE', 'MALAM']`  
   *(Lokasi: `signbridge/constants.py:162`, `web/model/labels.json`, `web/js/config.js:46`, `signbridge/train_multimodal.py:289`)*.

### B. Keputusan Teknis Protokol Label (P0-B Decision)
- **Keputusan:** Model M6 dan seluruh pipeline validasi manifest (`scripts/build_multimodal_manifest.py:66`) saat ini **menggunakan Kamus B (`GLOSS_TO_ID`)**.
- Jika pengumpulan data menggunakan kata di luar Kamus B (misalnya `HALO` atau `BUKU`), baris data tersebut **akan dibuang otomatis** oleh `scripts/build_multimodal_manifest.py` saat membangun dataset M6.
- **Rekomendasi Pemilihan Kosakata Pilot 20 Kelas (P0-B Pilot):**  
  Pilihlah 20 kata dari **Kamus B** yang memiliki irisan makna sosial/kelas tertinggi:
  
| Class ID | Gloss Resmi | Kategori Konsep | Padanan FSL (Bridge) | Contoh Konteks Kalimat Dialog |
| :---: | :--- | :--- | :--- | :--- |
| `0` | `AIR` | Kebutuhan Dasar | WATER | "Tenggorokan saya kering saat jam pelajaran." |
| `1` | `BELAJAR` | Aktivitas | STUDY | "Mari kita buka materi pelajaran hari ini." |
| `2` | `CARI` | Aktivitas | FIND | "Di mana kamu meletakkan pensilmu?" |
| `3` | `HARI` | Waktu | DAY | "Jadwal pelajaran apa yang kita ikuti?" |
| `4` | `INGAT` | Kognisi | REMEMBER | "Apakah kalian masih mencatat rumus kemarin?" |
| `5` | `LAGI` | Kuantitas/Sifat | AGAIN | "Bisakah penjelasannya diulangi sekali lagi?" |
| `6` | `MAAF` | Sapaan/Etika | SORRY | "Permisi, saya tadi datang terlambat." |
| `7` | `MAKAN` | Kebutuhan Dasar | EAT | "Jam istirahat siang sudah dimulai di kantin." |
| `8` | `MOTOR` | Transportasi | MOTORCYCLE | "Saya diantar orang tua ke sekolah." |
| `9` | `SAYA` | Pronomina | ME | "Izin bertanya mengenai tugas kelompok." |
| `10` | `TERIMA_KASIH` | Sapaan/Etika | THANK YOU | "Bantuan bapak dan ibu sangat bermanfaat." |
| `11` | `TULI` | Identitas Budaya | DEAF | "Komunitas teman tuli belajar bersama di kelas." |
| `12` | `APA` | Kata Tanya | WHAT | "Buku apa yang harus kita baca hari ini?" |
| `13` | `SIAPA` | Kata Tanya | WHO | "Siapa yang bertugas membersihkan papan tulis?" |
| `14` | `KAPAN` | Kata Tanya | WHEN | "Kapan batas akhir pengumpulan tugas ini?" |
| `15` | `DIMANA` | Kata Tanya | WHERE | "Di mana ruang laboratorium komputer berada?" |
| `16` | `MENGAPA` | Kata Tanya | WHY | "Mengapa kamu tidak masuk kelas kemarin?" |
| `17` | `BAGAIMANA` | Kata Tanya | HOW | "Bagaimana langkah menyelesaikan soal nomor dua?" |
| `25` | `TEMAN` | Relasi | FRIEND | "Ayo kita kerjakan tugas bersama-sama." |
| `27` | `RUMAH` | Tempat | HOUSE | "Saya mengerjakan pekerjaan rumah bersama keluarga." |

---

## 4. PROTOKOL IDENTITAS SIGNER

Untuk menjamin evaluasi generalisasi model yang objektif (*Signer-Independent Evaluation*), data signer diatur dengan ketentuan:

1. **Format Signer ID Anonim:**  
   Format penamaan signer: `SIGNER_<ID>` (misal: `SIGNER_01`, `SIGNER_02`, `SIGNER_03`) atau kode singkat `S01`, `S02`, `S03`. **Nama asli dilarang disimpan di manifest atau file storage.**
2. **Metadata Profil Signer:**  
   Disimpan pada tabel terpisah atau berkas `data/signers_metadata.json`:
   - `signer_id`: string unik (misal: `S01`).
   - `native_language`: BISINDO (Jakarta / Yogyakarta / dll).
   - `dominant_hand`: RIGHT / LEFT / AMBIDEXTROUS.
   - `experience_years`: durasi aktif berbahasa isyarat.
   - `consent_status`: `granted` (surat persetujuan etik penelitian ditandatangani).
   - `created_at`: tanggal registrasi profil.
3. **Aturan Pembagian Split Signer (LOSO / SI):**
   - **Test Set:** Signer `S03` dialokasikan secara eksklusif untuk pengujian *Leave-One-Signer-Out* (LOSO).
   - **Train & Val Set:** Signer `S01` dan `S02` dialokasikan untuk training (85%) dan validasi (15%).
   - Dengan pembagian ini, model diuji kemampuannya membaca isyarat dari orang yang **belum pernah dilihat sama sekali** selama proses pelatihan.

---

## 5. PROTOKOL SPESIFIKASI EMPAT MODALITAS

### A. Video (BISINDO Dynamic Motion)
- **Resolusi Sumber:** $1280 \times 720$ piksel (720p) atau $1920 \times 1080$ piksel (1080p).
- **Frame Rate:** 30 FPS konstan (hindari variabel framerate/VFR).
- **Format Kontainer:** MP4 (Video Codec: H.264 / AVC).
- **Durasi Klip:** 2,5 detik tetap (75 frame pada 30 FPS) yang mencakup fase *preparation*, *stroke* (puncak isyarat), dan *retraction*.
- **Framing & Jarak Kamera:** Jarak 1,2 – 1,5 meter dari kamera web, orientasi lanskap (*landscape*). Framing tubuh atas dari kepala hingga pinggang terlihat jelas (*medium shot*), kedua lengan bebas bergerak di dalam *signing space*.
- **Pencahayaan & Latar Belakang:** Pencahayaan depan merata ($\ge 300 \text{ lux}$), tidak *backlight*, latar belakang polos atau ruang kelas rapi tanpa orang lain melintas di belakang.
- **Ekstraksi Keypoint:** 86 koordinat MediaPipe Holistic ternormalisasi $(x, y, z)$ disimpan sebagai deret array float32 `[F, 86, 3]` di file `*_kp.json` atau `*_kp.npz`.

### B. Image (Hand Crop Appearance & Fine Geometry)
- **Resolusi Sumber:** Dipotong langsung dari frame video saat peragaan mencapai kepercayaan deteksi tangan tertinggi (*peak confidence* / *largest hand bounding box*).
- **Bounding Box Crop:** Kotak persegi di sekitar 21 titik tangan dengan margin bantalan **+25%** ([`web/js/handcrop.js:22`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/handcrop.js#L22)).
- **Resolusi File Simpanan:** $224 \times 224$ piksel, format JPEG (kualitas kompresi 90%).
- **Resolusi Masukan Model M6:** $112 \times 112$ piksel (di-resize otomatis oleh `signbridge/multimodal/features.py:96`).
- **Normalisasi Tensor:** ImageNet standard mean `[0.485, 0.456, 0.406]` dan std `[0.229, 0.224, 0.225]`.
- **Integritas Sampel:** Gambar crop tangan **wajib berasal dari klip video yang sama** (berpasangan), bukan mengambil gambar statis Mendeley yang berdiri sendiri, agar korelasi temporal-penampakan terjaga.

### C. Audio (Speech & Pronunciation)
- **Format File:** WAV PCM 16-bit, Little-Endian, Single Channel (Mono).
- **Sample Rate Sumber:** 16.000 Hz (16 kHz). Jika mikrofon peramban merekam di 44.1 kHz / 48 kHz, harus di-resample linear ke 16 kHz ([`web/js/recorder.js:130`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L130)).
- **Panjang Sinyal:** Tepat 40.000 sampel (durasi 2,5 detik pada 16 kHz).
- **Isi Suara:** Pengucapan lisan kalimat percakapan kelas oleh penutur/guru secara alami dan jelas saat gerakan isyarat diperagakan.
- **Representasi Spektrogram:** Log-mel spektrogram `[64, 248]` (64 mel filterbanks, window size 400 sampel / 25 ms, hop length 160 sampel / 10 ms).
- **Kondisi Akustik:** Rasio sinyal terhadap noise (SNR) $\ge 15 \text{ dB}$, bebas dari dengungan kipas angin atau gema ruangan ekstrem. Klip hening total (`RMS < 1e-4`) otomatis ditandai hilang.

### D. Text (Contextual Dialogue Sentence — Anti-Shortcut Protocol)
- **Bahasa:** Bahasa Indonesia baku/semi-formal ragam dialog kelas.
- **Format:** Kalimat lengkap 3–10 kata (maksimal 64 karakter).
- **Aturan Anti-Shortcut (SANGAT KRITIS):**
  - **DILARANG:** Menuliskan kata isyarat target secara telanjang di teks (misal: isyarat `MAKAN`, teks `"Makan."` atau `"Saya mau makan"`).
  - **DIIZINKAN:** Menuliskan kalimat pemicu pertanyaan atau konteks dialog situasional (misal: isyarat `MAKAN`, teks `"Apakah kamu sudah lapar sejak istirahat tadi?"`).
  - **DIIZINKAN:** Pertanyaan guru yang membutuhkan respon isyarat siswa (misal: isyarat `BELAJAR`, teks `"Apa yang sedang kita lakukan di ruang kelas?"`).
- **Tokenisasi:** Level karakter dengan kosakata 49 karakter (huruf `a-z`, angka `0-9`, spasi, dan tanda baca `.,?!-'`). Panjang tokenisasi tetap 64 integer.

---

## 6. PENETAPAN SAMPLE ID & DATA PAIRING PROTOCOL

Seluruh modalitas yang direkam dalam satu aksi fisik diikat oleh satu pengenal primer (**Primary Identifier**).

### A. Format Penamaan Sample ID Standar
```text
SB_<SIGNER_ID>_<GLOSS>_T<TAKE_ID>
Contoh: SB_S01_MAKAN_T01
```
- `SB`: Awalan resmi SignBridge.
- `S01`: Pengenal anonim penutur isyarat (Signer 1).
- `MAKAN`: Gloss target (huruf kapital).
- `T01`: Nomor repetisi / take (dua digit angka `01`–`20`).

### B. Struktur Bundel Berkas Berpasangan (Storage Bundle)
Setiap satu `sample_id` menghasilkan berkas terkait pada subdirektori terkoordinasi:
```text
data/raw/paired/
├── S01/
│   └── MAKAN/
│       ├── SB_S01_MAKAN_T01.mp4          # Video mentah kamera (720p, 2.5s)
│       ├── SB_S01_MAKAN_T01_kp.json      # Keypoint koordinat 86 titik (JSON)
│       ├── SB_S01_MAKAN_T01_hand.jpg     # Crop tangan resolusi 224x224
│       ├── SB_S01_MAKAN_T01.wav          # Audio ucapan mono 16 kHz
│       └── SB_S01_MAKAN_T01_meta.json    # Metadata rinci per klip
```

### C. Skema Metadata Klip (`SB_S01_MAKAN_T01_meta.json`)
```json
{
  "sample_id": "SB_S01_MAKAN_T01",
  "signer_id": "S01",
  "gloss": "MAKAN",
  "label": 7,
  "category": "gloss",
  "take": 1,
  "duration_seconds": 2.5,
  "num_frames": 75,
  "context_text": "Apakah kamu merasa lapar setelah olahraga?",
  "created_at": "2026-11-20T10:15:30Z",
  "consent_status": "granted",
  "files": {
    "video": "SB_S01_MAKAN_T01.mp4",
    "keypoint": "SB_S01_MAKAN_T01_kp.json",
    "image": "SB_S01_MAKAN_T01_hand.jpg",
    "audio": "SB_S01_MAKAN_T01.wav"
  },
  "modalities_present": {
    "video": true,
    "image": true,
    "audio": true,
    "text": true
  },
  "qc_status": "VALID"
}
```

---

## 7. SKEMA MANIFEST DATASET M6

Manifest utama yang dibaca langsung oleh `signbridge/train_multimodal.py` adalah:  
`data/multimodal/manifest_multimodal.csv`

### A. Kolom Wajib Manifest (Sesuai `signbridge/multimodal/constants.py:39-50`)
1. `clip_id`: ID unik sampel (contoh: `selfrec_S01:SB_S01_MAKAN_T01`).
2. `signer`: Kode anonim penutur isyarat (contoh: `S01`).
3. `category`: Kategori data (`gloss` untuk 32 konsep; `letter` untuk abjad).
4. `gloss`: Nama kata isyarat resmi (contoh: `MAKAN`).
5. `label`: Integer class ID $0 \dots 31$ (contoh: `7`).
6. `kp_path`: Path relatif atau absolut ke berkas keypoint `.json` atau `.npz`.
7. `image_path`: Path relatif atau absolut ke berkas crop tangan `.jpg`.
8. `audio_path`: Path relatif atau absolut ke berkas `.wav`.
9. `text`: Kalimat teks konteks (tanpa shortcut leksikal).
10. `split`: Pembagian evaluasi (`train`, `val`, atau `test`).

### B. Contoh Isi Baris Manifest Nyata
```csv
clip_id,signer,category,gloss,label,kp_path,image_path,audio_path,text,split
selfrec:SB_S01_MAKAN_T01,S01,gloss,MAKAN,7,raw/S01/MAKAN/SB_S01_MAKAN_T01_kp.json,raw/S01/MAKAN/SB_S01_MAKAN_T01_hand.jpg,raw/S01/MAKAN/SB_S01_MAKAN_T01.wav,Apakah kamu merasa lapar setelah olahraga?,train
selfrec:SB_S01_AIR_T01,S01,gloss,AIR,0,raw/S01/AIR/SB_S01_AIR_T01_kp.json,raw/S01/AIR/SB_S01_AIR_T01_hand.jpg,raw/S01/AIR/SB_S01_AIR_T01.wav,Tolong ambilkan gelas di atas meja guru.,train
selfrec:SB_S03_MAKAN_T01,S03,gloss,MAKAN,7,raw/S03/MAKAN/SB_S03_MAKAN_T01_kp.json,raw/S03/MAKAN/SB_S03_MAKAN_T01_hand.jpg,raw/S03/MAKAN/SB_S03_MAKAN_T01.wav,Waktunya menyantap bekal di istirahat siang.,test
```

---

## 8. STRUKTUR DIREKTORI & PENYIMPANAN DATA

Direktori dataset diatur secara terstruktur agar memisahkan antara media mentah, data terproses, dan berkas kontrol kualitas:

```text
data/
├── raw/
│   ├── web_zips/                  # Tempat menyimpan paket ZIP unduhan dari browser
│   └── paired/                    # Arsip hasil ekstraksi per signer dan kata
│       ├── S01/
│       ├── S02/
│       └── S03/
├── processed/
│   ├── multimodal_npz/            # Fitur keypoint terproses (64, 86, 3) siap latih
│   ├── hand_crops_112/            # Crop tangan resolusi tetap 112x112
│   └── audio_mel_64/              # Log-mel spektrogram tersimpan cepat (opsional)
├── multimodal/
│   ├── manifest_multimodal.csv    # Manifest resmi yang dibaca M6 PyTorch
│   ├── vocabulary_20.json         # Metadata taksonomi 20 kata pilot
│   └── signers_metadata.json      # Metadata demografi dan izin etik signer
└── qc/
    ├── qc_audit_report.json       # Laporan verifikasi otomatis integritas data
    └── rejected_samples.csv       # Daftar klip yang tidak memenuhi kriteria kualitas
```

---

## 9. PROTOKOL DATASET SPLIT & PENCEGAHAN DATA LEAKAGE

### A. Strategi Pembagian Split (Signer-Independent Primary)
1. **Aturan LOSO (Leave-One-Signer-Out):**
   - **Test Set:** 100% klip dari **Signer S03** (33,3% total data).
   - **Validation Set:** 15% klip acak deterministik dari **Signer S01 dan S02** (~10% total data).
   - **Training Set:** Sisa klip dari **Signer S01 dan S02** (~56,7% total data).
2. **Aturan Atomik Per Sampel:**
   Semua berkas dari satu `sample_id` (video, gambar, audio, teks) **harus selalu berada pada split yang sama**. Tidak boleh video di train tetapi audionya di test!

### B. Checklist Pencegahan Data Leakage
- [x] **No Duplicate Signer Across Train & Test:** Signer S03 tidak boleh memiliki satu pun klip di train/val.
- [x] **No Frame Leakage:** Gambar crop tangan diekstrak dari video yang sama dan mengikuti split video tersebut.
- [x] **No Lexical Target in Text:** Kalimat teks diperiksa secara otomatis; bila mengandung kata isyarat target (misal teks memuat kata `"makan"` saat label adalah `MAKAN`), klip ditandai `WARNING` atau teks diganti dengan konteks netral.
- [x] **No Stratification Shuffle Overlapping:** Pengacakan split menggunakan *hash deterministik* (`hashlib.sha256`) berdasarkan `clip_id`, bukan fungsi `random.shuffle()` yang berubah setiap eksekusi.

---

## 10. PROTOKOL DATA QUALITY CONTROL (QC)

Setiap sampel yang masuk dari perekam web harus melalui filter validasi otomatis sebelum dituliskan ke dalam manifest pelatihan.

### Kategori Status Validasi:

| Kategori Status | Kriteria Evaluasi | Aksi Pipeline |
| :--- | :--- | :--- |
| **`VALID`** | - Keypoint terdeteksi $\ge 8$ frame.<br>- Kedua tangan atau tangan dominan berada di signing space.<br>- File crop tangan ada dan tidak korup.<br>- Audio WAV memiliki durasi $2.3 - 2.7$ detik dan $\text{RMS} \ge 1 \times 10^{-4}$.<br>- Teks terisi $\ge 3$ kata dan tidak membocorkan label.<br>- `signer_id` dan `gloss` valid. | Diterima 100% ke manifest pelatihan. |
| **`WARNING`** | - Salah satu modalitas non-kritis hilang (misal audio hening, atau gambar agak buram).<br>- Teks mengandung kata yang mirip sinonim target.<br>- Frame keypoint antara 8 s.d. 20 frame. | Diterima sebagai sampel modalitas parsial (missing modality di-mask ke 0). |
| **`REJECTED`** | - Keypoint $< 8$ frame (tubuh tidak terdeteksi kamera).<br>- File WAV rusak atau tidak dapat di-decode oleh modul `wave`.<br>- Format base64 korup.<br>- `gloss` tidak terdaftar dalam `GLOSS_TO_ID`.<br>- Sampel duplikat persis (hash data identik). | Dibuang dari manifest, dicatat di `qc/rejected_samples.csv`. |

---

## 11. ANALISIS KETERSEDIAAN DATASET & GAP ANALYSIS

### A. Status Inventaris Data Faktual di Repository Saat Ini

| Sumber Dataset | Modalitas Asli | Status Fisik di Disk Lokal | Ketersediaan Pairing 4-Modalitas | Keterangan Faktual |
| :--- | :--- | :---: | :---: | :--- |
| **WL-BISINDO** | Video / Pose | Manifest ada (1.600 baris), berkas `.npz` = 0 | Tidak Ada | Dataset publik Kaggle belum diunduh ke folder `data/keypoints/`. |
| **BISINDO Alphabet** | Image Statis | 8.620 file `.jpg` & `.npy` ada di disk | Tidak Ada | Data gambar statis Mendeley untuk huruf A–Z (bukan isyarat kata). |
| **Google FLEURS** | Audio Ucapan | Metadata TSV ada (3.613 entri), berkas `.wav` = 0 | Tidak Ada | Audio pembacaan kalimat belum diunduh ke disk. |
| **Tatoeba Indonesian**| Teks Kalimat | 28.418 kalimat ada di disk (`.tsv.bz2`) | Tidak Ada | Korpus teks terisolasi tanpa relasi ke video isyarat. |
| **SignBridge Pilot** | 4-Modalitas | **0 Sampel** | **0 Sampel** | Belum ada rekaman berpasangan yang diambil. |

### B. Kesimpulan Kebutuhan Data (Gap Statement)
Data yang ada di repository saat ini **hanya cukup untuk pengujian pipeline sintaksis (smoke test)**, tetapi **BELUM CUKUP untuk melatih model M6 nyata**.  
Diperlukan akuisisi data baru sebanyak:
- **Pilot Phase (P0-B Target):** 20 Kelas $\times$ 15 Repetisi $\times$ 1 Signer = **300 Klip Berpasangan**.
- **Expansion Phase (Full Dataset Target):** 32 Kelas $\times$ 10 Repetisi $\times$ 3 Signer = **960 Klip Berpasangan**.

---

## 12. KEPUTUSAN TEKNIS SEBELUM IMPLEMENTASI RECORDER (P0-D)

Sebelum tim melangkah ke pembuatan / perbaikan Recorder pada tahap P0-D, 5 keputusan teknis berikut telah ditetapkan secara mengikat:

1. **Kosakata Perekam Dikunci ke 20 Kata Pilot (Subset Resmi Kamus B):**  
   Daftar dropdown target pada antarmuka web recorder **harus menampilkan 20 kata resmi** dari `GLOSS_TO_ID` agar tidak ada klip yang dibuang oleh `build_multimodal_manifest.py`.
2. **Penghapusan Auto-Fill Shortcut Kalimat:**  
   Logika auto-fill `sentenceEl.value = glossToSentenceLocal(...)` pada `web/js/app.js:1045` harus diganti dengan **bank template kalimat konteks pertanyaan/dialog**, atau dikosongkan agar diisi kalimat dialog alami oleh pengumpul data.
3. **Resolusi Crop Tangan:**  
   Perekam web tetap menyimpan crop tangan pada resolusi $224 \times 224$ piksel JPEG (agar kualitas arsip tinggi), dan pemangkasan ke $112 \times 112$ dilakukan secara konsisten oleh loader Python M6.
4. **Resampling Audio Linear di Web Worker:**  
   Perekam web harus memastikan audio diekspor dalam format WAV PCM 16-bit 16.000 Hz durasi 2,5 detik persis menggunakan fungsi `encodeWavPCM16` dan `resampleLinear` yang telah lulus uji unit JavaScript.
5. **Format ZIP Standar Tanpa Kompresi (Store ZIP):**  
   Paket unduhan peramban harus mempertahankan format ZIP standar metode *STORE* yang dapat diekstrak langsung oleh pustaka `zipfile` Python tanpa membutuhkan pustaka pihak ketiga.

---

## 13. DAFTAR FILE DAN BUKTI IMPLEMENTASI YANG DIPERIKSA

1. [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py) — Baris 5-28 (kontrak tensor), 59-75 (PoseEncoder), 77-94 (ImageEncoder), 96-113 (AudioEncoder), 115-130 (TextEncoder), 194-208 (Transformer sequence 161 token), 210-224 (Gating), 247-262 (Loss function).
2. [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py) — Baris 13-37 (dimensi tensor 4 modalitas), 39-50 (kolom manifest `MANIFEST_COLUMNS`).
3. [`signbridge/multimodal/features.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py) — Baris 40-57 (pose preprocessing), 89-119 (image preprocessing), 127-238 (audio log-mel), 251-260 (text character encoding).
4. [`signbridge/multimodal/dataset.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/dataset.py) — Baris 38-65 (`read_manifest`), 103-128 (`assign_splits` SD & SI), 139-169 (`MultimodalSampleLoader`).
5. [`signbridge/train_multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py) — Baris 45-56 (`DEFAULT_CFG`), 227 (`num_classes=32`), 289 (`BISINDO_32_GLOSSES`).
6. [`scripts/build_multimodal_manifest.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/build_multimodal_manifest.py) — Baris 39-55 (`unpack_zips`), 57-86 (`records_from_selfrec`), 66-67 (filter `gloss not in GLOSS_TO_ID`).
7. [`web/js/recorder.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js) — Baris 38-122 (`buildStoreZip`), 125-175 (`resampleLinear` & `encodeWavPCM16`), 197-260 (`MultimodalCapture`), 298-399 (`MultimodalRecorder`).
8. [`web/js/app.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js) — Baris 1015-1115 (`bindRecorderControls`), 1044-1046 (auto-fill kalimat shortcut).
9. [`server/database.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/database.py) — Baris 58-76 (`SignConcept`), 151-170 (`DatasetRecording`).
10. [`data/bridge/concepts.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/bridge/concepts.csv) — Baris 1-34 (32 konsep kelas pedagogis / Kamus A).
11. [`signbridge/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/constants.py) — Baris 162-196 (`BISINDO_32_GLOSSES` / Kamus B), 198 (`GLOSS_TO_ID`).

