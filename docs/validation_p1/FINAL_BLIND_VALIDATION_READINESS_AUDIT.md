# LAPORAN AUDIT FINAL KESIAPAN STIMULUS VALIDASI BUTA
## Image Modality I1-P1 (BISINDO Alphabet Fingerspelling) — SignBridge ASEAN
### Final Read-Only Audit: Stimulus Verification, Leakage Prevention, & Protocol Robustness

**Dokumen**: `docs/validation_p1/FINAL_BLIND_VALIDATION_READINESS_AUDIT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (MobileNetV3-Small I1-P1)  
**Dokumen Instrumen yang Diaudit**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)  
**Dokumen Protokol Lapangan yang Diaudit**: [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md)  
**Dokumen Laporan Metodologis Acuan**: [`docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md)  
**Tanggal Audit**: 16 November 2026  
**Auditor**: Senior Research Methodologist, Dataset Quality Auditor, & Senior ML Engineer  
**Sifat Audit**: **READ-ONLY INSPECTION (Nol Modifikasi Kode, Model, atau Dataset)**  
**Status Kesiapan (*Readiness Verdict*)**: **`READY_WITH_LIMITATIONS`**  
**Status Operasional Verifikasi**: **`PENDING VALIDATOR`** (Menunggu Pelaksanaan Sesi Faktual)  
**Status Operasional Pilot Lapangan**: **`PILOT_HOLD`** (Pengambilan Foto Ditangguhkan)  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Audit independen read-only ini dilaksanakan untuk memverifikasi kesiapan operasional set stimulus citra dan protokol sesi validasi buta (*blind validation*) sebelum diujikan kepada penutur asli Tuli (*native Deaf signers*) atau instruktur BISINDO.

Pemeriksaan mencakup verifikasi integritas fisik 7 berkas citra stimulus, audit potensi kebocoran informasi (*information leakage*), audit alur pengungkapan label (*label disclosure*), evaluasi ketahanan protokol multi-validator, batasan metodologis stimulus, serta verifikasi integritas kriptografis repositori.

### Hasil Utama Audit:
1. **Integritas Berkas Stimulus (100% Verified)**: Ketujuh berkas citra stimulus benar-benar tersedia di disk, dapat dibuka tanpa galat, beresolusi $224 \times 224$ piksel (format JPEG, mode RGB), memiliki hash SHA-256 yang unik (bebas duplikat), dan terbebas dari metadata EXIF yang dapat membocorkan informasi.
2. **Pencegahan Kebocoran Informasi (Verified with Operational Safeguards)**: Protokol lapangan telah merancang penyembunyian nama file, folder kelas, dan label aktual. Namun, auditor menemukan bahwa urutan pengkodean bawaan membentuk pola selang-seling target-pembanding ($A \to B \to A \to C \to A \to D \to A$); oleh karena itu, pengacakan urutan presentasi (*randomized display order*) menjadi mitigasi operasional wajib.
3. **Pemisahan Kolom Respon (Verified)**: Respon observasi buta (*pre-disclosure*) dan respon pasca-pengungkapan label (*post-disclosure*) dicatat pada kolom terpisah dan respon awal dikunci sebelum label diungkapkan.
4. **Verifikasi Integritas Sistem (100% Untouched)**: Checkpoint PyTorch dan model ONNX terbukti 100% identik secara kriptografis (SHA-256 match), manifest aktual tetap bersih (0 baris data fiktif), dan tidak ada modifikasi pada berkas terlacak Git.
5. **Kesimpulan Kesiapan**: Instrumen dinyatakan **`READY_WITH_LIMITATIONS`** untuk digunakan dalam sesi lapangan terpandu. Belum ada sesi validator yang dilaksanakan; status operasional tetap **`PENDING VALIDATOR`** dan **`PILOT_HOLD`**.

---

## 2. AUDIT VERIFIKASI TUJUH FILE STIMULUS GAMBAR

Pemeriksaan fisik dilakukan secara langsung menggunakan modul `PIL.Image` dan algoritma kriptografi SHA-256 terhadap 7 berkas yang terdaftar dalam instrumen verifikasi:

| Kode Stimulus | Path Berkas Asli di Repository | Kelas Target | Ukuran Berkas | Format & Mode | Resolusi | Hash SHA-256 (64-bit Hex) | Integritas Baca |
|:---:|---|:---:|:---:|:---:|:---:|---|:---:|
| `IMG_BLD_01` | `data/raw/image/bisindo_alphabet/A/A _Hitam_Iphone_14Pro.jpg` | **A** | 5.404 Bytes | JPEG, RGB | $224 \times 224$ | `87d8bef129d4c728e235a9c9bfd5d718b958cfa997ff9db7aa155e42bfbb4787` | **VALID ✅** |
| `IMG_BLD_02` | `data/raw/image/bisindo_alphabet/B/20240509_182924.jpg` | **B** (Pembanding) | 4.390 Bytes | JPEG, RGB | $224 \times 224$ | `bffea6d2d09a0665971481284a1e9c20a4b33ec8138ee685741e1df595b1695e` | **VALID ✅** |
| `IMG_BLD_03` | `data/raw/image/bisindo_alphabet/A/A_ Polos Terang_Xiaomi _Note 8 Pro.jpg` | **A** | 6.112 Bytes | JPEG, RGB | $224 \times 224$ | `dfbca33198031d279761eb1ae7256191c28c89cba4542d46eeb318f72ff27549` | **VALID ✅** |
| `IMG_BLD_04` | `data/raw/image/bisindo_alphabet/C/20240509_183146.jpg` | **C** (Pembanding) | 3.508 Bytes | JPEG, RGB | $224 \times 224$ | `64af582ba349fe1c1a25db8cc38965f97330fb3fc784e2ae864be7c87c943ea6` | **VALID ✅** |
| `IMG_BLD_05` | `data/raw/image/bisindo_alphabet/A/20240509_182656.jpg` | **A** | 4.044 Bytes | JPEG, RGB | $224 \times 224$ | `6558180808f9d5118b76fb0d7a049d5bf183f3d132ce47ce23ebfa5064c5885c` | **VALID ✅** |
| `IMG_BLD_06` | `data/raw/image/bisindo_alphabet/D/20240509_183310.jpg` | **D** (Pembanding) | 4.818 Bytes | JPEG, RGB | $224 \times 224$ | `344bdac12eaf8f44ff52136e0766fead06b3e7ff7d3e09d57a916a4198305c65` | **VALID ✅** |
| `IMG_BLD_07` | `data/raw/image/bisindo_alphabet/A/A_Background Baju (Garis)_Samsung_A53 5G.jpg` | **A** | 11.583 Bytes | JPEG, RGB | $224 \times 224$ | `7c00f34a8c9b2f694e9f54fcbaee251ec41d2e18585f8f8f04df5ec2cfa4d922` | **VALID ✅** |

### Temuan Audit Fisik Berkas:
1. **Ketersediaan & Keterbacaan**: Seluruh 7 berkas ada secara fisik di direktori dataset, dapat dibaca oleh library pengolahan citra standar tanpa exception, dan tidak ada berkas rusak (*corrupt file*) atau berukuran 0 byte.
2. **Kesesuaian Resolusi & Format**: Seluruh citra berdimensi seragam $224 \times 224$ piksel dengan 3 kanal warna (RGB, 8-bit per kanal).
3. **Uji Duplikasi Kriptografis**: Ketujuh berkas menghasilkan nilai hash SHA-256 yang berbeda satu sama lain ($7/7$ unik). Tidak ada duplikasi yang tidak disengaja.
4. **Audit Metadata EXIF**: Pemeriksaan tag EXIF membuktikan bahwa **seluruh citra memiliki 0 metadata EXIF** (jumlah tag EXIF = 0). Tidak ada informasi model kamera, tanggal pemotretan, atau nama perangkat yang bocor melalui header file.
5. **Catatan Kehati-hatian**: Auditor menegaskan bahwa keberadaan fisik dan keterbacaan gambar ini **bukan merupakan bukti keabsahan linguistik**. Verifikasi linguistik sepenuhnya bergantung pada hasil wawancara lapangan.

---

## 3. AUDIT PENCEGAHAN KEBOCORAN INFORMASI (BLIND PRESENTATION LEAKAGE AUDIT)

Pemeriksaan dilakukan terhadap potensi kebocoran identitas kelas kepada validator:

### A. Evaluasi Vektor Kebocoran Informasi

| Parameter Kebocoran | Status Proteksi | Evaluasi & Bukti Audit |
|---|:---:|---|
| **Nama File Asli** | **TERLINDUNGI 🟢** | Nama file asli (misal `A _Hitam_Iphone_14Pro.jpg`) disubstitusi menjadi kode anonim `IMG_BLD_...`. |
| **Nama Folder Kelas** | **TERLINDUNGI 🟢** | Struktur folder (`/A/`, `/B/`, dst.) tidak ditampilkan pada kartu peraga visual maupun slide validator. |
| **Teks Label Kelas** | **TERLINDUNGI 🟢** | Tidak ada teks huruf (misal "Huruf A") pada tampilan gambar yang dilihat validator pada Tahap 1. |
| **Deskripsi Peneliti** | **TERLINDUNGI 🟢** | Deskripsi morfologis (misal "dua tangan segitiga") dilarang diucapkan oleh pewawancara pada Tahap 1. |
| **Metadata File EXIF** | **TERLINDUNGI 🟢** | 0 tag EXIF tersimpan dalam file JPEG (terkonfirmasi bersih). |
| **Pemisahan Lembar Kerja** | **DIPERLUKAN SAFEGUARD ⚠️** | Tabel pada instrumen `BISINDO_A_FORMAL_VERIFICATION_FORM.md` Bagian 5.B memuat kolom `Actual Class` dan `File Asli di Repository` untuk konteks peneliti. Lembar ini **DILARANG KERAS** diperlihatkan kepada validator saat sesi berlangsung. |
| **Pola Urutan Penyajian** | **DIPERLUKAN SAFEGUARD ⚠️** | Urutan kode bawaan membentuk ritme selang-seling teratur: $A \to B \to A \to C \to A \to D \to A$. |

### B. Tindakan Mitigasi Operasional Wajib:
1. **Pemisahan Fisik/Digital Materi Validator**: Materi yang dilihat validator **hanya berupa kartu cetak polos atau slide digital terisolasi** yang hanya memuat gambar dan kode `IMG_BLD_...`, sesuai ketentuan Bagian 2 pada `BLIND_VALIDATION_SESSION_PROTOCOL.md`. Validator tidak boleh melihat instrumen master peneliti.
2. **Pengacakan Urutan Presentasi (*Randomized Display Order*)**: Pewawancara wajib mengacak urutan kemunculan kartu gambar sebelum sesi dimulai (misal: $B \to A \to D \to A \to A \to C \to A$) dan mencatat nomor urut kemunculan aktual pada kolom `Display Order`. Hal ini memutus pola ritme selang-seling agar tidak dapat ditebak oleh validator.

---

## 4. AUDIT ALUR PENGUNGKAPAN LABEL (LABEL DISCLOSURE AUDIT)

Audit memeriksa integritas proses transisi antara Tahap 1 (Blind Observation) dan Tahap 2 (Label Disclosure):

1. **Penguncian Respon Awal (*Locking Mechanism*)**:
   - Protokol lapangan (`BLIND_VALIDATION_SESSION_PROTOCOL.md` Langkah 3) menetapkan bahwa sebelum pewawancara mengungkap label kelas, seluruh catatan pada Tahap 1 wajib diverifikasi lengkap dan dikunci (*locked*).
   - Terdapat jeda eksplisit sebelum transisi dilakukan.
2. **Keterpisahan Kolom Pencatatan**:
   - Instrumen menyediakan dua kolom independen pada tabel:
     - Kolom 1: `Blind Interpretation (Tahap 1 — Sebelum Tahu Label)`
     - Kolom 2: `Post-Disclosure Assessment (Tahap 2 — Setelah Tahu Label)`
   - Respon awal tidak ditimpa (*no overwriting*).
3. **Perlakuan Terhadap Perubahan Sikap Validator**:
   - Jika validator mengubah interpretasinya setelah mengetahui bahwa komputer melabeli citra sebagai huruf 'A', perubahan tersebut **diperlakukan sebagai data sosiolinguistik tentang penerimaan label (*label acceptability dynamics*)**, bukan dianggap sebagai kesalahan atau inkonsistensi validator.
   - Pewawancara diwajibkan menggali alasan perubahan tersebut melalui pertanyaan Modul B.

---

## 5. AUDIT PROTOKOL MULTI-VALIDATOR & DISAMBIGUASI PERBEDAAN PENDAPAT

### A. Evaluasi Mekanisme Multi-Validator Saat Ini
- Instrumen `BISINDO_A_FORMAL_VERIFICATION_FORM.md` telah menetapkan target minimal 2 validator independen (`VAL_01` dan `VAL_02`).
- Telah dicantumkan larangan tegas terhadap voting mayoritas untuk menyelesaikan perbedaan pendapat.
- Ditegaskan bahwa sesi validator tunggal ($n=1$) dibatasi sebagai studi pendahuluan non-nasional.

### B. Rekomendasi Framework Disambiguasi Perbedaan Pendapat (Audit Recommendation)
Auditor menemukan bahwa instrumen sebelumnya cenderung menyederhanakan perbedaan pendapat sebagai akibat dari variasi dialek atau pengaruh SLB. Dalam praktik linguistik isyarat, perbedaan interpretasi dapat bersumber dari faktor-faktor yang berbeda. 

Tim auditor merekomendasikan **Framework Taksonomi 6 Faktor** berikut untuk membedakan akar penyebab perbedaan pendapat antarvalidator saat analisis data dilakukan:

```
+---------------------------------------------------------------------------------------------------------+
|                                TAKSONOMI 6 FAKTOR DISAMBIGUASI PERBEDAAN                                |
+-----------------------------------+---------------------------------------------------------------------+
| Faktor Penyebab Perbedaan         | Indikator Diagnostik / Bukti Pengamatan                             |
+-----------------------------------+---------------------------------------------------------------------+
| 1. Variasi Regional / Geografis   | Bentuk berbeda digunakan secara konsisten oleh komunitas di kota    |
|                                   | atau provinsi asal validator (misal variasi Jawa vs Sumatra).       |
+-----------------------------------+---------------------------------------------------------------------+
| 2. Pengalaman & Pemerolehan Bahasa| Perbedaan antara penutur Tuli sejak lahir (native/generational) vs  |
|                                   | penutur yang baru belajar isyarat pada usia remaja/dewasa.          |
+-----------------------------------+---------------------------------------------------------------------+
| 3. Konteks Situasi Penggunaan     | Bentuk dipahami hanya pada situasi tertentu (misal percakapan santai|
|                                   | informal vs presentasi formal / ejaan nama orang).                  |
+-----------------------------------+---------------------------------------------------------------------+
| 4. Pengaruh Sistem Isyarat Lain   | Respon dipengaruhi oleh kebiasaan alfabet satu tangan SIBI dari SLB |
|                                   | atau adopsi alfabet satu tangan ASL dari media sosial.              |
+-----------------------------------+---------------------------------------------------------------------+
| 5. Kualitas & Ambiguitas Gambar   | Validator kesulitan mengidentifikasi karena sudut kamera (*angle*), |
|                                   | pencahayaan redup, atau oklusi jari pada foto 2D tertentu.          |
+-----------------------------------+---------------------------------------------------------------------+
| 6. Ketidakpastian Subjektif       | Validator menyatakan ragu-ragu, lupa, atau jarang mengeja huruf     |
|                                   | tertentu dalam interaksi sehari-hari.                               |
+-----------------------------------+---------------------------------------------------------------------+
```

> [!TIP]
> Notulis dan pewawancara disarankan menggunakan taksonomi di atas dalam mencatat argumentasi validator pada kolom *Alasan & Bukti yang Mendasari*, sehingga laporan akhir tidak otomatis menggeneralisasi setiap ketidaksepakatan sebagai variasi dialek semata.

---

## 6. AUDIT KETERBATASAN METODOLOGIS STIMULUS

Auditor memeriksa dan menegaskan kembali batasan ruang lingkup dari set 7 stimulus ini:

1. **Bukan Benchmark Akurasi Validator**: Sesi validasi buta ini bertujuan menguji keabsahan representasi dataset komputer, **bukan menguji kepintaran atau akurasi penutur Tuli**.
2. **Bukan Bukti Diskriminasi Seluruh Alfabet**: Tujuh citra ini hanya mengevaluasi Kelas A dan 3 pembanding terbatas (B, C, D). Sesi ini tidak membuktikan kemampuan model atau validator membedakan seluruh 26 huruf (A–Z).
3. **Bukan Bukti Representativitas Nasional BISINDO**: Hasil dari set stimulus ini tidak dapat diklaim sebagai gambaran lengkap konvensi isyarat di seluruh 38 provinsi di Indonesia.
4. **Bukan Bukti Final Validitas Ground Truth**: Pengakuan bentuk dua tangan segitiga oleh validator pada sesi ini merupakan verifikasi kualitatif awal dalam lingkup komunitas validator; pembuktian ground truth final memerlukan uji generalisasi kuantitatif pada 780 foto penutur eksternal.

---

## 7. AUDIT INTEGRITAS REPOSITORI & CHECKPOINT MODEL

Pemeriksaan integritas kriptografis dan status repositori dilakukan untuk memastikan bahwa pelaksanaan audit metodologis bersifat **100% read-only**:

### A. Verifikasi Hash SHA-256 Artefak Model PyTorch & ONNX

```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "runs/image_i1_mobilenetv3/best.pt", "web/model/fingerspell.onnx"
```

| Path Artefak Model | Algoritma | Hash Kriptografis Aktual (SHA-256) | Status Integritas |
|---|:---:|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | SHA-256 | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% IDENTIK (UTUH) ✅** |
| `runs/image_i1_mobilenetv3/best.pt` | SHA-256 | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% IDENTIK (UTUH) ✅** |
| `web/model/fingerspell.onnx` | SHA-256 | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% IDENTIK (UTUH) ✅** |

### B. Status Git Working Tree (`git status --short`)
- Tracked files modified: **0 berkas**.
- Tidak ada modifikasi tidak sah pada pipeline kode (`scripts/`), model (`signbridge/`), konfigurasi (`configs/`), maupun web application (`web/`).
- Seluruh berkas untracked terjaga aman tanpa adanya pembersihan destruktif.

### C. Keberadaan & Status Manifest Aktual
- Berkas `data/external/bisindo_validation/external_manifest.csv` terkonfirmasi tersedia secara fisik (ukuran: 163 bytes).
- Berkas memuat 14 kolom header resmi:
  ```csv
  image_path,label,signer_id,capture_id,capture_date,device,camera_angle,lighting_condition,background,image_width,image_height,consent_status,verified_label,notes
  ```
- **Jumlah Baris Data Aktual**: **0 baris data fiktif**. Manifest tetap bersih menunggu foto nyata diambil.

### D. Status Progres Pengumpulan Data Eksternal
- Berdasarkan [`docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md):
  - Status Keseluruhan: **`NOT STARTED` ⚪**
  - Capaian Valid: **0 / 780 foto (0.00%)**
  - Defisit Pilot (EXT_S01, Kelas A): **10 foto**
  - Defisit Total: **780 foto**

---

## 8. KESIMPULAN AUDIT & STATUS OPERASIONAL RESMI

### A. Keputusan Kesiapan (*Readiness Verdict*)
Berdasarkan hasil verifikasi menyeluruh terhadap 7 berkas stimulus, protokol pengamatan buta dua tahap, mitigasi kebocoran informasi, dan integritas sistem:

$$\mathbf{READINESS\ VERDICT} = \mathbf{READY\_WITH\_LIMITATIONS}$$

### Catatan Keterbatasan Operasional:
1. Sesi lapangan wajib menerapkan pengacakan urutan kemunculan gambar (*randomized display order*) untuk meniadakan pola selang-seling target-pembanding ($A \to B \to A \to C \to A \to D \to A$).
2. Lembar kerja master peneliti (`BISINDO_A_FORMAL_VERIFICATION_FORM.md`) wajib dipisahkan secara fisik/digital dari kartu peraga yang diperlihatkan kepada validator.
3. Analisis ketidaksepakatan antarvalidator wajib memanfaatkan taksonomi 6 faktor agar tidak menggeneralisasi setiap perbedaan sebagai dialek semata.

### B. Status Operasional Proyek
Audit ini menegaskan bahwa **sesi wawancara bersama validator BELUM dilaksanakan**. Status operasional proyek tetap berada pada kondisi tunggu yang aman:

| Parameter Operasional | Status Resmi | Keterangan |
|---|:---:|---|
| **Kesiapan Stimulus & Protokol** | **`READY_WITH_LIMITATIONS` ⚠️** | Stimulus fisik terverifikasi 100%, protokol siap digunakan dengan panduan safeguards lapangan. |
| **Status Instrumen Verifikasi** | **`PENDING VALIDATOR` ⏳** | Seluruh kolom isian respon, profil, dan informed consent tetap 100% kosong (*unfilled*). |
| **Status Tahap Pilot Lapangan** | **`PILOT_HOLD` 🚫** | Pengambilan fisik 10 foto kelas A penutur EXT_S01 **TIDAK DIIZINKAN** sampai sesi nyata selesai, ditinjau ulang, dan disetujui dalam *re-examination*. |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**, defisit: 780 foto. |

