# LAPORAN QUALITY GATE FINAL PRA-SESI VALIDASI BUTA I1-P1
## Final Pre-Session Quality Gate Report — BISINDO Kelas A
### Proyek: SignBridge ASEAN | Image Modality I1-P1 (MobileNetV3-Small)

**Dokumen**: `docs/validation_p1/FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling (I1-P1)  
**Dokumen Acuan yang Diaudit Fisik**:
1. [`docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/BLIND_STIMULUS_DECK.pdf)
2. [`docs/validation_p1/participant_material/card_IMG_BLD_01.jpg`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/card_IMG_BLD_01.jpg) s.d. [`card_IMG_BLD_07.jpg`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/participant_material/card_IMG_BLD_07.jpg)
3. [`docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md)
4. [`docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/VALIDATOR_DISAGREEMENT_DIAGNOSTIC_CHECKLIST.md)
5. [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)
6. [`data/external/bisindo_validation/external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv)  
**Tanggal Audit**: 16 November 2026  
**Auditor**: Senior Quality Gate Auditor, Dataset Quality Auditor, & ML Validation Engineer  
**Sifat Audit**: **READ-ONLY INSPECTION (Tanpa Modifikasi Kode, Dataset, Model, Manifest, atau Konfigurasi)**  
**Kesimpulan Quality Gate**: **`READY_WITH_LIMITATIONS`**  
**Rekomendasi Operasional Sesi**: **`CONDITIONAL_GO_FOR_HUMAN_SESSIONS`** (Siap Eksekusi Lapangan dengan Safeguards Terpenuhi)  
**Status Instrumen Verifikasi**: **`PENDING VALIDATOR`**  
**Status Operasional Pilot**: **`PILOT_HOLD`**  
**Progres Pengumpulan Data Eksternal**: **`NOT STARTED` ⚪ (0 / 780 foto valid)**  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Audit *Final Pre-Session Quality Gate* ini dilakukan secara independen terhadap berkas fisik aktual yang ada di repositori untuk memastikan kesiapan operasional sebelum sesi validasi buta tatap muka bersama mitra Tuli diselenggarakan.

Pemeriksaan membuktikan:
1. **Fisik Materi Participant-Facing**: Berkas `BLIND_STIMULUS_DECK.pdf` (7 halaman) dan 7 berkas kartu JPEG dapat dibuka, dirender tanpa galat, dan terverifikasi berstatus **`NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT`** dalam batasan pengujian visual dan metadata.
2. **Reproduksibilitas Randomisasi**: Algoritma randomisasi terbukti deterministik dan dapat direproduksi. Klaim awal bahwa "pola target-pembanding dipecah tuntas" dikoreksi secara ilmiah: kemunculan target A yang berdampingan adalah konsekuensi wajar dari proporsi 4 target berbanding 3 distractor.
3. **Audit Biner Manifest**: Berkas manifest aktual diverifikasi memiliki ukuran **163 bytes** (161 bytes teks 14 kolom + 2 bytes newline `\n\n`) dengan **0 baris data fiktif**. Perbedaan terhadap klaim historis 172 bytes ditandai secara objektif sebagai **`UNVERIFIED_HISTORICAL_CAUSE`** karena tidak ada berkas fisik 172 bytes di Git.
4. **Kesiapan Etika & Anonimitas**: Alur informed consent, pemisahan izin rekaman video vs wawancara, dan proteksi kode anonim terverifikasi terstandar tanpa ada data rekaan.
5. **Integritas Kriptografis Model**: Ketiga artefak model (P1, P0, ONNX) terbukti **100% cocok dengan baseline SHA-256**.

---

## 2. TASK 1 — AUDIT FISIK PDF & PARTICIPANT-FACING MATERIAL

Audit dilakukan secara komparatif menggunakan library parsing PDF (`PyMuPDF / fitz`) dan analisis citra (`PIL.Image`):

### A. Tabel Hasil Verifikasi per Halaman PDF (`BLIND_STIMULUS_DECK.pdf`)

| Halaman | Dimensi Kanvas | Kode Stimulus | Path Berkas Sumber | Kelas Aktual (Peneliti) | Kesesuaian Citra (MAE) | Teks Terdeteksi pada Kanvas | Status Kebocoran Label |
|:---:|:---:|:---:|---|:---:|:---:|---|:---:|
| **1** | $720 \times 540$ pt | `IMG_BLD_01` | `data/raw/image/.../A/A _Hitam_Iphone_14Pro.jpg` | **A** | MAE: 1,05 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **2** | $720 \times 540$ pt | `IMG_BLD_02` | `data/raw/image/.../B/20240509_182924.jpg` | **B** | MAE: 0,84 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **3** | $720 \times 540$ pt | `IMG_BLD_03` | `data/raw/image/.../A/A_ Polos Terang_Xiaomi...` | **A** | MAE: 1,14 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **4** | $720 \times 540$ pt | `IMG_BLD_04` | `data/raw/image/.../C/20240509_183146.jpg` | **C** | MAE: 0,68 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **5** | $720 \times 540$ pt | `IMG_BLD_05` | `data/raw/image/.../A/20240509_182656.jpg` | **A** | MAE: 0,79 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **6** | $720 \times 540$ pt | `IMG_BLD_06` | `data/raw/image/.../D/20240509_183310.jpg` | **D** | MAE: 0,94 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |
| **7** | $720 \times 540$ pt | `IMG_BLD_07` | `data/raw/image/.../A/A_Background Baju (Garis)...`| **A** | MAE: 1,91 (Cocok) | Kode anonim & instruksi netral | `NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT` |

### B. Audit Metadata PDF & Berkas JPEG:
1. **Metadata Kamus PDF**:
   - `Title`: `BLIND_STIMULUS_DECK`
   - `Author`: `''` (Kosong)
   - `Subject`: `''` (Kosong)
   - `Keywords`: `''` (Kosong)
   - `Creator`: `''` (Kosong)
   - `Producer`: `''` (Kosong)
   - `Encryption`: `None`
2. **Metadata Kartu JPEG (`card_IMG_BLD_01.jpg` s.d. `07.jpg`)**:
   - `EXIF (APP1)`: None (0 tag)
   - `XMP (APP1)`: None
   - `IPTC (APP13)`: None
   - `Comments (COM)`: None
   - `ICC Profile (APP2)`: None
3. **Pemeriksaan Watermark, Teks Tersembunyi, & Thumbnail**:
   - Tidak ditemukan layer watermark tersembunyi.
   - Text stream PDF kosong (`[]`), seluruh teks dirender sebagai grafik raster bitmap terpadu pada resolusi kanvas $1000 \times 750$.
   - Citra stimulus di tengah kanvas berukuran $450 \times 450$ piksel, memiliki kontras tajam, dan memadai untuk observasi visual manusia.
4. **Batasan Pemeriksaan Kebocoran**:
   Status pengujian ditetapkan sebagai **`NO_KNOWN_LABEL_LEAKAGE_AFTER_AUDIT`**. Batasan pemeriksaan ini mencakup inspeksi visual, ekstraksi objek biner PyMuPDF, pemindaian teks kanvas, dan audit metadata JPEG/PDF. Pemeriksaan ini tidak mencakup persepsi kognitif subjektif di luar materi fisik yang diaudit.

*Status Task 1*: **`PASS_WITH_LIMITATION`**

---

## 3. TASK 2 — AUDIT RANDOMISASI URUTAN STIMULUS

Pemeriksaan terhadap [`BLIND_VALIDATION_RANDOMIZATION_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md) mengonfirmasi:

1. **Kelengkapan Kode**: Setiap urutan memuat tepat 7 kode stimulus tanpa pengulangan dan tanpa ada stimulus yang hilang (permutasi $7/7$).
2. **Reproduksibilitas Eksekusi Ulang**: Eksekusi ulang script generator dengan seed baseline menghasilkan urutan yang 100% identik:
   - `Seed 20261101` (`VAL_01`): `02 -> 03 -> 05 -> 04 -> 07 -> 01 -> 06`
   - `Seed 20261102` (`VAL_02`): `03 -> 07 -> 06 -> 02 -> 04 -> 01 -> 05`
   - `Seed 20261103` (`VAL_03`): `04 -> 03 -> 07 -> 05 -> 06 -> 02 -> 01`
   - `Seed 20261104` (`VAL_04`): `01 -> 04 -> 05 -> 03 -> 02 -> 07 -> 06`
3. **Variasi Antarvalidator**: Keempat urutan validator berbeda satu sama lain.
4. **Pemisahan Mapping Peneliti**: Tabel penugasan enumerator terbebas dari label kelas asli; mapping kelas disimpan pada bagian terpisah khusus peneliti.
5. **Koreksi Ilmiah Klaim "Pola Dipecah Tuntas"**:
   - Auditor mengoreksi klaim pada laporan sebelumnya: proporsi set stimulus terdiri dari 4 sampel Kelas A (57,1%) dan 3 distractor (42,9%).
   - Dalam ruang permutasi acak, **kemunculan dua stimulus target Kelas A secara berurutan adalah keniscayaan matematis** (misal pada `VAL_01`: `03` & `05` berdekatan, `07` & `01` berdekatan; pada `VAL_02`: `03` & `07` berdekatan).
   - Pengacakan berhasil memecah ritme selang-seling teratur ($A \to B \to A \to C \to A \to D \to A$), tetapi **TIDAK menjamin pemisahan sempurna antartarget**.
6. **Status Penggunaan**: Urutan ini **BELUM pernah digunakan dalam sesi nyata**.

*Status Task 2*: **`PASS_WITH_LIMITATION`**

---

## 4. TASK 3 — AUDIT BINER MANIFEST DATA EKSTERNAL

Pemeriksaan biner terhadap [`data/external/bisindo_validation/external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv) dalam mode read-only menunjukkan:

1. **Jumlah & Urutan Kolom**: Tepat 14 kolom resmi:
   ```text
   1. image_path
   2. label
   3. signer_id
   4. capture_id
   5. capture_date
   6. device
   7. camera_angle
   8. lighting_condition
   9. background
   10. image_width
   11. image_height
   12. consent_status
   13. verified_label
   14. notes
   ```
2. **Jumlah Baris Data**: **0 baris data fiktif**. Berkas hanya memuat baris header dan baris kosong penutup.
3. **Analisis Biner & Line Endings**:
   - Ukuran aktual: **163 bytes**.
   - Hex dump: Berakhir pada sequence `0a0a` (dua karakter Unix newline LF `\n\n`).
   - Panjang string header: 161 karakter teks UTF-8/ASCII.
   - Perhitungan biner: $161 \text{ bytes teks} + 2 \text{ bytes newline} = \mathbf{163 \text{ bytes}}$.
4. **Penetapan Status Perbedaan 172 Bytes vs 163 Bytes**:
   - Auditor memeriksa histori Git repositori (`git log --all -- external_manifest.csv`) dan mengonfirmasi bahwa berkas manifest belum pernah dicatat dalam riwayat commit (untracked).
   - Tidak ada berkas fisik berukuran 172 bytes yang dapat diperiksa secara biner di repositori saat ini.
   - Sesuai prinsip kehati-hatian ilmiah tanpa mengarang penjelasan, perbedaan ukuran ini diklasifikasikan secara resmi sebagai:
     $$\mathbf{STATUS:\ UNVERIFIED\_HISTORICAL\_CAUSE}$$
   - Konfirmasi integritas: Skema 14 kolom tetap 100% konsisten dan manifest **TIDAK DIUBAH**.

*Status Task 3*: **`PASS_WITH_LIMITATION`**

---

## 5. TASK 4 — KESIAPAN ETIKA & PROTOKOL VALIDATOR

Pemeriksaan terhadap instrumen [`BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md) dan panduan [`BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md) memastikan:

1. **Pemisahan Entitas & Peran**:
   - ID Penugasan Validator (`VAL_BISINDO_01`, `02`, dst.) terpisah dari identitas asli.
   - Status Rekrutmen terpisah (berstatus pending).
   - Kriteria Kompetensi mengakui penutur asli Tuli (*lived experience*) tanpa kewajiban sertifikat formal.
2. **Granularitas Persetujuan (*Informed Consent*)**:
   - Persetujuan wawancara terpisah dari persetujuan perekaman audio/video.
   - Penolakan perekaman video **TIDAK membatalkan partisipasi** (beralih ke pencatatan tertulis penuh).
3. **Tata Urut Prosedural Mutlak**:
   - Informed consent **WAJIB ditandatangani pada Langkah 1** sebelum observasi buta dimulai. Tidak ada penandatanganan di akhir sesi.
4. **Nol Data Fiktif**: Seluruh kolom nama validator, profil, tanggal sesi, pilihan respon, dan paraf dibiarkan 100% kosong (*unfilled*).

*Status Task 4*: **`PASS`**

---

## 6. TASK 5 — PRESERVASI INTEGRITAS REPOSITORI & MODEL

### A. Verifikasi Hash SHA-256 Artefak Model PyTorch & ONNX

```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "runs/image_i1_mobilenetv3/best.pt", "web/model/fingerspell.onnx"
```

| Berkas Model Kritis | Hash Kriptografis Baseline Resmi | Hash Aktual Terverifikasi | Status Integritas |
|---|---|---|:---:|
| **P1 Checkpoint** (`runs/.../best.pt`) | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% MATCH ✅** |
| **P0 Checkpoint** (`runs/.../best.pt`) | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% MATCH ✅** |
| **Production ONNX** (`web/.../fingerspell.onnx`) | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% MATCH ✅** |

### B. Preservasi Tujuh Berkas Sumber Stimulus:
Ketujuh berkas sumber di `data/raw/image/bisindo_alphabet/` terbukti 100% cocok dengan hash audit sebelumnya:
- `IMG_BLD_01`: `87d8bef129d4e432b0ea...` (**MATCH**)
- `IMG_BLD_02`: `bffea6d2d09a6999603f...` (**MATCH**)
- `IMG_BLD_03`: `dfbca3319803a748f37b...` (**MATCH**)
- `IMG_BLD_04`: `64af582ba349918496f7...` (**MATCH**)
- `IMG_BLD_05`: `6558180808f9ab217324...` (**MATCH**)
- `IMG_BLD_06`: `344bdac12eafde447fe7...` (**MATCH**)
- `IMG_BLD_07`: `7c00f34a8c9ba18104aa...` (**MATCH**)

### C. Status Git Working Tree (`git status --short`):
- **Tracked Modifications**: **0 berkas**. Pohon terlacak Git bersih dari modifikasi tidak sah.
- **Untracked Files**: Seluruh berkas konfigurasi, skrip audit, artefak run model, dan test suite lama tetap terjaga aman.
- **Berkas Baru Ditambahkan**: Hanya berkas laporan quality gate ini `docs/validation_p1/FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md`.
- Tidak ada operasi destruktif (`git clean`, `git reset`, `git checkout`).

*Status Task 5*: **`PASS`**

---

## 7. RISIKO RESIDUAL YANG MASIH TERSISA (RESIDUAL RISKS)

1. **Risiko Klaster Target Berurutan (*Target Clustering Effect*)**: Karena 4 dari 7 stimulus adalah Kelas A, validator akan melihat target Kelas A muncul berurutan (misal 2 kali berturut-turut). Notulis harus menyadari bahwa ini bukan kegagalan pengacakan, melainkan peluang menguji konsistensi respon validator.
2. **Risiko Oklusi Visual Kamera Ponsel**: Foto mentah bersumber dari kamera ponsel pengguna dengan sudut alami yang mungkin menimbulkan pertanyaan validator mengenai sudut jari kelingking/manis. Hal ini wajib dicatat pada Hipotesis 5 (Kualitas Gambar).
3. **Ketiadaan Pelaksanaan Sesi Manusia**: Kesiapan dokumen dan artefak digital bukanlah bukti selesainya verifikasi linguistik. Tanpa kehadiran penutur asli Tuli yang memberikan interpretasi bebas, bentuk gestur Kelas A belum terverifikasi secara sosiolinguistik.

---

## 8. REKOMENDASI OPERASIONAL & KESIMPULAN QUALITY GATE

### A. Evaluasi Status per Tugas:
- **Task 1 (PDF & Participant Material Audit)**: **`PASS_WITH_LIMITATION`**
- **Task 2 (Randomization Audit)**: **`PASS_WITH_LIMITATION`**
- **Task 3 (Manifest Byte Audit)**: **`PASS_WITH_LIMITATION`** (`UNVERIFIED_HISTORICAL_CAUSE`)
- **Task 4 (Validator & Ethics Readiness)**: **`PASS`**
- **Task 5 (Integrity Preservation)**: **`PASS`**

### B. Rekomendasi Sesi Lapangan:
$$\mathbf{OPERATIONAL\ RECOMMENDATION} = \mathbf{CONDITIONAL\_GO\_FOR\_HUMAN\_SESSIONS}$$

*Syarat Pelaksanaan (*Go Condition*)*:
Enumerator lapangan wajib mematuhi protokol: menyajikan hanya berkas `BLIND_STIMULUS_DECK.pdf` atau kartu JPEG tanpa teks, mengikuti urutan acak seed yang ditugaskan, menyembunyikan master worksheet peneliti, memperoleh informed consent sebelum observasi dimulai, dan mencatat respon secara verbatim.

### C. Status Operasional Resmi Proyek:

| Parameter Evaluasi | Status Resmi Proyek | Keterangan Operasional |
|---|:---:|---|
| **Quality Gate Kesiapan** | **`READY_WITH_LIMITATIONS` ⚠️** | Artefak digital, deck presentasi, acakan, dan checklist siap digunakan; pembuktian linguistik menunggu kehadiran manusia. |
| **Status Rekomendasi Sesi** | **`CONDITIONAL_GO_FOR_HUMAN_SESSIONS`** | Siap dieksekusi dengan protokol safeguards lapangan. |
| **Status Instrumen Verifikasi** | **`PENDING VALIDATOR` ⏳** | Seluruh kolom isian respon dan informed consent tetap 100% kosong (*unfilled*). |
| **Status Tahap Pilot Lapangan** | **`PILOT_HOLD` 🚫** | Pengambilan fisik 10 foto kelas A penutur EXT_S01 **DITANGGUHKAN MUTLAK** hingga sesi nyata selesai dan disetujui dalam *re-examination*. |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**, defisit: 780 foto. |

