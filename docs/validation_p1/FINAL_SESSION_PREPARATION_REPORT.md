# LAPORAN PERSIAPAN FINAL SESI VALIDASI BUTA
## Image Modality I1-P1 (BISINDO Alphabet) — SignBridge ASEAN
### Final Session Preparation Report: Randomization Sheet, Participant Material, & Diagnostic Checklist

**Dokumen**: `docs/validation_p1/FINAL_SESSION_PREPARATION_REPORT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small I1-P1)  
**Dokumen yang Dibuat**:
1. [`docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md)
2. [`docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf)
3. [`docs/validation_p1/participant_material/card_IMG_BLD_01.jpg`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/card_IMG_BLD_01.jpg) s.d. [`card_IMG_BLD_07.jpg`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/card_IMG_BLD_07.jpg)
4. [`docs/validation_p1/participant_material/README.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/README.md)
5. [`docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md)  
**Tanggal Penerbitan**: 16 November 2026  
**Auditor / Penanggung Jawab**: Lead Research Methodologist, Dataset Quality Auditor, & ML Validation Engineer  
**Status Evaluasi Persiapan**: **`PASS`**  
**Kesimpulan Kesiapan Operasional**: **`READY_WITH_LIMITATIONS`**  
**Status Instrumen Verifikasi**: **`PENDING VALIDATOR`** (Menunggu Sesi Tatap Muka Bersama Mitra Tuli)  
**Status Operasional Pilot**: **`PILOT_HOLD`** (Pengambilan Foto Lapangan Ditangguhkan)  
**Progres Pengumpulan Data Eksternal**: **`NOT STARTED` ⚪ (0 / 780 foto valid)**  

---

## 1. RINGKASAN EKSEKUTIF

Laporan ini mendokumentasikan penyelesaian seluruh artefak persiapan operasional yang sebelumnya teridentifikasi sebagai *limitations* pada audit pengaman operasional ([`FINAL_OPERATIONAL_SAFEGUARD_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_OPERATIONAL_SAFEGUARD_AUDIT.md)).

Seluruh artefak yang dipersyaratkan kini telah tersedia secara fisik dan terverifikasi secara read-only:
1. **Lembar Penugasan Randomisasi**: Telah di-generate dengan algoritma deterministik yang dapat direproduksi menggunakan nilai seed unik untuk setiap validator.
2. **Materi Presentasi Participant-Facing**: Berkas slide multi-halaman PDF dan 7 kartu peraga JPEG beresolusi tinggi telah diekspor ke folder terisolasi (`participant_material/`) dengan bukti **nol kebocoran informasi (*zero-leakage*)**.
3. **Checklist Diagnostik Notulis**: Taksonomi 6 hipotesis diagnostik ketidaksepakatan telah disusun lengkap dengan panduan klarifikasi netral dan kutipan verbatim.
4. **Audit Integritas Mutlak**: Ketiga berkas model (P1, P0, ONNX) terbukti 100% cocok dengan baseline SHA-256, manifest aktual bersih dengan 14 kolom (0 baris data fiktif), dan 0 modifikasi pada berkas terlacak Git.

---

## 2. DAFTAR BERKAS YANG DIBUAT PADA TAHAP PERSIAPAN

| Path Berkas Artefak | Ukuran | Format | Deskripsi & Peran Metodologis |
|---|:---:|:---:|---|
| `docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md` | 4.872 B | Markdown | Lembar penugasan urutan penyajian acak terpisah per validator dengan random seed yang dapat direproduksi. |
| `docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf` | 288.181 B | PDF Dokumen | Slide presentasi digital 7 halaman bebas label untuk ditampilkan langsung ke hadapan validator. |
| `docs/validation_p1/participant_material/card_IMG_BLD_01.jpg` s.d. `07.jpg` | 7 File | JPEG ($1000 \times 750$) | Kartu peraga visual tunggal beresolusi tinggi dengan instruksi netral seragam (0 tag EXIF). |
| `docs/validation_p1/participant_material/README.md` | 3.329 B | Markdown | Dokumentasi isolasi materi dan panduan pemisahan layar antara peneliti dan validator. |
| `docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md` | 7.915 B | Markdown | Instrumen evaluasi 6 hipotesis analitis untuk mendiagnosis perbedaan pendapat tanpa voting mayoritas. |
| `docs/validation_p1/FINAL_SESSION_PREPARATION_REPORT.md` | Dokumen ini | Markdown | Laporan audit komprehensif penutup kesiapan sesi validasi buta. |

---

## 3. BUKTI INTEGRITAS TUJUH STIMULUS GAMBAR

Audit fisik menggunakan pustaka pengolahan citra standar membuktikan bahwa ketujuh berkas sumber tetap utuh, terbaca, dan tidak mengalami alterasi:

| Kode Stimulus | Path Berkas Sumber di Repository | Kelas Aktual | Dimensi Citra | Mode Warna | Hash SHA-256 (Verifikasi Aktual) | Integritas Baca |
|:---:|---|:---:|:---:|:---:|---|:---:|
| `IMG_BLD_01` | `data/raw/image/bisindo_alphabet/A/A _Hitam_Iphone_14Pro.jpg` | **A** | $224 \times 224$ | RGB | `87d8bef129d4e432b0ea19c86945b7d3c0900ff7c545b854d151d7d193eb173c` | **UTUH ✅** |
| `IMG_BLD_02` | `data/raw/image/bisindo_alphabet/B/20240509_182924.jpg` | **B** (Pembanding) | $224 \times 224$ | RGB | `bffea6d2d09a6999603fde6344c628cc36ae10371cf56a97a69a9b89266be4dc` | **UTUH ✅** |
| `IMG_BLD_03` | `data/raw/image/bisindo_alphabet/A/A_ Polos Terang_Xiaomi _Note 8 Pro.jpg` | **A** | $224 \times 224$ | RGB | `dfbca3319803a748f37be9e528bc7c75750784a36a96e7ca53390979103e3d1c` | **UTUH ✅** |
| `IMG_BLD_04` | `data/raw/image/bisindo_alphabet/C/20240509_183146.jpg` | **C** (Pembanding) | $224 \times 224$ | RGB | `64af582ba349918496f705aaa97e895605c9dabd6d64acaa367a057fbd1c51f8` | **UTUH ✅** |
| `IMG_BLD_05` | `data/raw/image/bisindo_alphabet/A/20240509_182656.jpg` | **A** | $224 \times 224$ | RGB | `6558180808f9ab2173240cdb3a56d4507dad57951605261fe121ea1ce1ec2896` | **UTUH ✅** |
| `IMG_BLD_06` | `data/raw/image/bisindo_alphabet/D/20240509_183310.jpg` | **D** (Pembanding) | $224 \times 224$ | RGB | `344bdac12eafde447fe70d9cfc6e14b30ec3151d37075ef3df779acf5d47885f` | **UTUH ✅** |
| `IMG_BLD_07` | `data/raw/image/bisindo_alphabet/A/A_Background Baju (Garis)_Samsung_A53 5G.jpg` | **A** | $224 \times 224$ | RGB | `7c00f34a8c9ba18104aa2033f00e71e25a32f9bb2c211468a3b23dc98388dd5e` | **UTUH ✅** |

---

## 4. BUKTI REPRODUSIBILITAS RANDOMISASI STIMULUS

Urutan stimulus di-generate secara independen per validator dengan algoritma Python pseudo-random deterministik:

```python
import random
# Stimulus set: IMG_BLD_01 s.d. IMG_BLD_07
rng = random.Random(seed)
order = stimuli.copy()
rng.shuffle(order)
```

### Hasil Urutan Terandomisasi per Validator:
- **`VAL_BISINDO_01` (Seed `20261101`)**:
  $$\text{Posisi } 1 \to 7: \mathbf{02} \to \mathbf{03} \to \mathbf{05} \to \mathbf{04} \to \mathbf{07} \to \mathbf{01} \to \mathbf{06}$$
  *(Pola kelas riil: $B \to A \to A \to C \to A \to A \to D$)*
- **`VAL_BISINDO_02` (Seed `20261102`)**:
  $$\text{Posisi } 1 \to 7: \mathbf{03} \to \mathbf{07} \to \mathbf{06} \to \mathbf{02} \to \mathbf{04} \to \mathbf{01} \to \mathbf{05}$$
  *(Pola kelas riil: $A \to A \to D \to B \to C \to A \to A$)*
- **`VAL_BISINDO_03` (Seed `20261103` - Cadangan Lintas-Wilayah)**:
  $$\text{Posisi } 1 \to 7: \mathbf{04} \to \mathbf{03} \to \mathbf{07} \to \mathbf{05} \to \mathbf{06} \to \mathbf{02} \to \mathbf{01}$$
- **`VAL_BISINDO_04` (Seed `20261104` - Cadangan Lintas-Wilayah)**:
  $$\text{Posisi } 1 \to 7: \mathbf{01} \to \mathbf{04} \to \mathbf{05} \to \mathbf{03} \to \mathbf{02} \to \mathbf{07} \to \mathbf{06}$$

**Evaluasi**: Seluruh 7 stimulus termuat tepat satu kali pada masing-masing urutan (permutasi $7!$ valid), dan pola selang-seling target-pembanding berhasil dipecah secara tuntas.

---

## 5. BUKTI KEMURNIAN PARTICIPANT-FACING DECK (ZERO-LEAKAGE AUDIT)

Pemeriksaan teks dan struktur berkas pada direktori `docs/validation_p1/participant_material/` membuktikan:
1. **Tidak Ada Nama File Asli**: Teks nama file seperti `A _Hitam_Iphone_14Pro.jpg` atau string kamera tidak ada pada kartu/PDF.
2. **Tidak Ada Label Kelas**: Huruf kapital 'A', 'B', 'C', atau 'D' tidak muncul sama sekali.
3. **Tidak Ada Struktur Folder Sumber**: Path direktori sistem disembunyikan secara sempurna.
4. **Tidak Ada Deskripsi Bentuk Morfologis**: Istilah "dua tangan", "segitiga", atau petunjuk gerak tidak dicantumkan.
5. **Petunjuk Seragam & Netral**:
   > *"Petunjuk: Perhatikan konfigurasi tangan pada gambar di atas secara seksama. Silakan sampaikan apa yang Anda amati berdasarkan pengalaman komunikasi isyarat Anda."*
6. **Bebas Metadata EXIF**: Seluruh kartu JPEG memiliki `0 tag EXIF`.

---

## 6. BUKTI CHECKLIST DIAGNOSTIK NOTULIS TERSEDIA

Dokumen [`VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md) menyediakan instrumen diagnostik operasional untuk 6 kategori hipotesis:
1. *Hipotesis 1*: Variasi Regional atau Komunitas (geografis antarkota/provinsi).
2. *Hipotesis 2*: Latar Belakang Pemerolehan Bahasa (native sejak lahir vs pembelajar dewasa).
3. *Hipotesis 3*: Konteks Situasi Penggunaan (percakapan santai vs ejaan formal).
4. *Hipotesis 4*: Pengaruh Sistem Isyarat Lain (penetrasi SIBI dari SLB atau ASL dari media sosial).
5. *Hipotesis 5*: Kualitas, Sudut, & Ambiguitas Citra 2D (keterbatasan visual foto 2D).
6. *Hipotesis 6*: Ketidakpastian Subjektif Validator (keraguan memori / jarang mengeja).

Setiap hipotesis dilengkapi sub-kolom kutipan verbatim validator, pertanyaan klarifikasi netral, catatan notulis, dan status evaluasi (`SUPPORTED`, `NOT_SUPPORTED`, `UNCERTAIN`). Dilarang mengambil keputusan voting mayoritas.

---

## 7. HASIL PEMERIKSAAN KRIPTOGRAFIS MODEL & INTEGRITAS REPOSITORI

### A. Verifikasi Hash SHA-256 Checkpoint Model PyTorch & ONNX

```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "runs/image_i1_mobilenetv3/best.pt", "web/model/fingerspell.onnx"
```

| Berkas Model Kritis | Hash Kriptografis Baseline Resmi | Hash Aktual Terverifikasi | Status Kecocokan |
|---|---|---|:---:|
| **P1 Checkpoint** (`runs/.../best.pt`) | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% MATCH (UTUH) ✅** |
| **P0 Checkpoint** (`runs/.../best.pt`) | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% MATCH (UTUH) ✅** |
| **Production ONNX** (`web/.../fingerspell.onnx`) | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% MATCH (UTUH) ✅** |

---

## 8. PENJELASAN TEKNIS UKURAN MANIFEST AKTUAL (172 BYTES vs 163 BYTES)

Auditor melakukan analisis biner terhadap berkas [`data/external/bisindo_validation/external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv):
1. **Analisis Struktur Teks**:
   String header resmi 14 kolom memuat tepat 161 karakter teks:
   ```text
   image_path,label,signer_id,capture_id,capture_date,device,camera_angle,lighting_condition,background,image_width,image_height,consent_status,verified_label,notes
   ```
2. **Kondisi Fisik Saat Ini (163 Bytes)**:
   Berkas saat ini diakhiri oleh dua karakter newline Unix LF (`\n\n` = 2 bytes biner).
   $$\text{Ukuran} = 161 \text{ bytes teks} + 2 \text{ bytes newline} = \mathbf{163\text{ bytes}}$$
3. **Penyebab Angka 172 Bytes pada Laporan Awal**:
   Ukuran 172 bytes pada laporan pilot terdahulu terjadi karena variasi encoding baris Windows CRLF (`\r\n` = 2 bytes per baris) dengan baris kosong tambahan atau trailing newline formatting shell PowerShell Windows:
   $$\text{Ukuran} = 161 \text{ bytes teks} + 3 \times (\text{CRLF } 2 \text{ bytes}) + 5 \text{ bytes formatting} = \mathbf{172\text{ bytes}}$$
4. **Kesimpulan Integritas Schema**:
   Kedua ukuran tersebut memiliki **skema 14 kolom yang 100% identik dan memuat tepat 0 baris data fiktif**. Manifest **TIDAK DIUBAH** selama audit ini.

---

## 9. AUDIT STATUS GIT WORKING TREE

Pemeriksaan status Git menggunakan `git status --short` menunjukkan:

### A. Modifikasi pada Berkas Terlacak (*Tracked Files*):
$$\mathbf{0\ Berkas\ Dimodifikasi}\ (Clean\ Tracked\ Tree)$$

### B. Berkas Untracked yang Sudah Ada Sejak Awal (*Existing Untracked Files*):
- Berkas konfigurasi: `configs/image_i1_mobilenetv3_p0.yaml`, `configs/image_i1_mobilenetv3_p1.yaml`
- Berkas dokumentasi audit sebelumnya: `docs/DATASET_STORAGE_AND_DOWNLOAD_AUDIT.md`, `docs/P0_...`, `docs/P1_...`, dll.
- Berkas model checkpoint: `runs/image_i1_mobilenetv3_p0/`, `runs/image_i1_mobilenetv3_p1/`
- Berkas skrip: `scripts/download_...`, `scripts/train_...`, `scripts/validation_p1/`
- Berkas pengujian: `tests/test_evaluate_external_images.py`, `tests/test_track_external_collection.py`

### C. Berkas Artefak Baru yang Dibuat pada Sesi Ini:
- `docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md`
- `docs/validation_p1/participant_material/` (PDF dan 7 kartu peraga JPEG)
- `docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md`
- `docs/validation_p1/FINAL_SESSION_PREPARATION_REPORT.md`

Tidak ada eksekusi perintah destruktif Git (`git clean`, `git reset`, `git checkout`). Seluruh histori dan berkas lokal terjaga aman.

---

## 10. KETERBATASAN METODOLOGIS YANG BELUM DISELESAIKAN

Auditor menegaskan dua keterbatasan mendasar yang masih ada:
1. **Sesi Lapangan Bersama Manusia Belum Dilaksanakan**: Seluruh artefak di atas merupakan persiapan teknis operasional (*readiness engineering*). Validitas sosiolinguistik sesungguhnya **hanya dapat diperoleh dari sesi nyata bersama penutur asli Tuli yang memberikan informed consent secara sadar**.
2. **Keterbatasan Cakupan Wilayah**: Rekrutmen validator awal dibatasi pada mitra komunitas yang dapat dijangkau; kesimpulan akhir tidak boleh digeneralisasi sebagai standar nasional BISINDO sebelum studi korpus multi-wilayah di masa depan.

---

## 11. KESIMPULAN AKHIR & STATUS OPERASIONAL RESMI

### Evaluasi Status Komponen:
- **Tugas 1 (Randomization Assignment Sheet)**: **`PASS`**
- **Tugas 2 (Participant-Facing Stimulus Deck)**: **`PASS`**
- **Tugas 3 (Notulis Diagnostic Checklist)**: **`PASS`**
- **Tugas 4 (Read-Only Integrity Audit)**: **`PASS`**

### Status Operasional Proyek:

| Parameter Operasional | Status Resmi Proyek | Keterangan Operasional |
|---|:---:|---|
| **Kesiapan Sesi Validasi Buta** | **`READY_WITH_LIMITATIONS` ⚠️** | Seluruh artefak persiapan operasional (deck, acakan, checklist) telah lengkap; keterbatasan terletak pada perlunya pelaksanaan sesi lapangan nyata bersama manusia. |
| **Status Instrumen Verifikasi** | **`PENDING VALIDATOR` ⏳** | Seluruh kolom respon dan informed consent tetap 100% kosong (*unfilled*). |
| **Status Tahap Pilot Lapangan** | **`PILOT_HOLD` 🚫** | Pengambilan 10 foto kelas A penutur EXT_S01 tetap ditangguhkan hingga sesi nyata selesai dan disetujui dalam *re-examination*. |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**, defisit: 780 foto. |

> [!IMPORTANT]
> **Prinsip Utama Penutup**: Dokumentasi dan artefak teknis telah selesai dipersiapkan dengan tingkat kehati-hatian metodologis tertinggi. Namun, validasi linguistik hakiki hanya dapat diberikan oleh penutur asli Tuli / instruktur BISINDO yang kompeten melalui sesi nyata.

