# PHASE 2C — VALIDATOR DISTRIBUTION EXECUTION LOG
## SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)
### Modality: Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
#### Status Validasi: WAITING_FOR_HUMAN_VALIDATION | Standard: Phase 2C.8 (Blind Letter Identification)

> [!IMPORTANT]
> **GOVERNANCE & AUDIT TRAIL MANDATE**
> Dokumen ini mencatat log eksekusi distribusi paket stimulus kepada dua validator independen BISINDO (`VAL-A` dan `VAL-B`).
> Seluruh proses distribusi dan pengumpulan wajib mematuhi protokol pembutaan (*blinded review*), pemisahan peran fasilitator, dan penjagaan ketat terhadap firewall data uji.
> **CATATAN AUDIT**: Jangan mengisi tanggal, jam, identitas personal, atau bukti pelaksanaan sebelum tindakan nyata di lapangan dilakukan oleh fasilitator manusia.

---

## 1. INFORMASI UMUM & IDENTITAS DISTRIBUSI

| Parameter | Nilai / Spesifikasi | Status Audit |
| :--- | :--- | :---: |
| **Proyek** | SignBridge ASEAN — Multimodal Classroom Bridge | Verified |
| **Modul** | Modul I1 (Citra Diam Alfabet BISINDO A–Z) | Verified |
| **Fase Validasi** | Phase 2C.8 — Blind Letter Identification & Validator Workbook | Verified |
| **Status Pelaksanaan** | **`READY_FOR_MANUAL_HANDOFF`** | Menunggu Serah Terima Fisik |
| **Status Training P2** | **`STRICT HOLD`** | Tidak Ada Retraining/Tuning |
| **Jumlah Validator Utama** | 2 Orang Independen (`VAL-A`, `VAL-B`) | Menunggu Penugasan Lapangan |
| **Validator Adjudikasi** | 1 Orang Independen (`VAL-C`) | *Standby* (Hanya jika divergensi) |
| **Jumlah Stimulus** | 36 Citra Anonim (`VAL-REV-001` s/d `036`) | 17 Train + 19 Test Diagnostic |
| **Metode Distribusi** | Penyerahan Langsung / Media Penyimpanan Offline Aman | Terisolasi dari Repo Publik |

---

## 2. SPESIFIKASI & CHECKSUM PAKET PRA-DISTRIBUSI

| Komponen Paket | Paket Validator A (`VAL-A`) | Paket Validator B (`VAL-B`) | Status Verifikasi |
| :--- | :---: | :---: | :---: |
| **Direktori Sumber** | `docs/validation_p2/phase_2c/distribution/validator_A/` | `docs/validation_p2/phase_2c/distribution/validator_B/` | **VERIFIED** |
| **Jumlah File per Paket** | Tepat 41 Berkas (36 JPG + 3 MD + 1 CSV + 1 XLSX) | Tepat 41 Berkas (36 JPG + 3 MD + 1 CSV + 1 XLSX) | **VERIFIED (41/41)** |
| **Integritas 36 Stimulus** | 36/36 Hash SHA-256 Cocok Master Manifest | 36/36 Hash SHA-256 Cocok Master Manifest | **100% MATCH** |
| **Kesetaraan Biner Citra** | Byte-for-byte identik dengan Paket B | Byte-for-byte identik dengan Paket A | **0 Difference** |
| **Dokumen Metodologi** | 3 Dokumen (`PANDUAN`, `SHEET`, `PROTOCOL`) | 3 Dokumen (`PANDUAN`, `SHEET`, `PROTOCOL`) | **Lengkap & Terverifikasi** |
| **Buku Kerja Interaktif** | `VALIDATOR_A_WORKBOOK.xlsx` (358 KB) | `VALIDATOR_B_WORKBOOK.xlsx` (358 KB) | **3 Sheets, Dropdown, Previews** |
| **SHA-256 Workbook** | `3a1238ef5bd0106a1cdfe6b7cabec12e5b54fa8a9ec6c9379989f073650e4932` | `5de5ae5a415eb04482e1d17c319fd331e61caa5b50b20b5a66a788b5333be447` | **VERIFIED BASELINE** |
| **File Template CSV (V2)** | `VALIDATOR_A_RESPONSE_TEMPLATE.csv` | `VALIDATOR_B_RESPONSE_TEMPLATE.csv` | **Blank (36 Baris)** |
| **SHA-256 Template CSV** | `6aadd6341dc0968a4014f52ea5ed13b1228974538bfed2c2dc5e8692e0c4277a` | `e8e45aa829d974d6286d904363d005b9fcc5804c4c074f79a8f4393696686014` | **VERIFIED BASELINE** |
| **Isolasi Data Rahasia** | 0 label asli, 0 prediksi model, 0 skor model | 0 label asli, 0 prediksi model, 0 skor model | **SECURE (0 Leak)** |

---

## 3. LOG EKSEKUSI PENYERAHAN & PENGEMBALIAN LAPANGAN

### Tabel Pelacakan Distribusi Resmi:

| Parameter Pelacakan | Validator A (`VAL-A`) | Validator B (`VAL-B`) |
| :--- | :--- | :--- |
| **Identitas Kode Validator** | `VAL-A` | `VAL-B` |
| **Identitas Paket Distribusi** | `PKG-VAL-A-36STIMULI-V2` | `PKG-VAL-B-36STIMULI-V2` |
| **SHA-256 Workbook Pra-Serah** | `3a1238ef5bd0106a1cdfe6b7cabec12e5b54fa8a9ec6c9379989f073650e4932` | `5de5ae5a415eb04482e1d17c319fd331e61caa5b50b20b5a66a788b5333be447` |
| **SHA-256 Template CSV Pra-Serah** | `6aadd6341dc0968a4014f52ea5ed13b1228974538bfed2c2dc5e8692e0c4277a` | `e8e45aa829d974d6286d904363d005b9fcc5804c4c074f79a8f4393696686014` |
| **Tanggal & Waktu Distribusi** | *[Diisi fasilitator saat serah terima]* | *[Diisi fasilitator saat serah terima]* |
| **Media Transfer Paket** | *[USB Terenkripsi / Media Offline]* | *[USB Terenkripsi / Media Offline]* |
| **Konfirmasi Informed Consent** | *[ ] Belum &nbsp;&nbsp; [ ] Ditandatangani (No Dok: _____)* | *[ ] Belum &nbsp;&nbsp; [ ] Ditandatangani (No Dok: _____)* |
| **Target Tanggal & Jam Kembali** | *[Target: H+3 dari tanggal distribusi]* | *[Target: H+3 dari tanggal distribusi]* |
| **Aktual Tanggal & Jam Kembali** | *[Diisi fasilitator saat berkas diterima]* | *[Diisi fasilitator saat berkas diterima]* |
| **SHA-256 File Respons Diterima** | *[Dihitung seketika sebelum berkas dibuka]* | *[Dihitung seketika sebelum berkas dibuka]* |
| **Status Validasi Integritas Skema** | `PENDING_DISTRIBUTION` | `PENDING_DISTRIBUTION` |
| **Tanda Tangan Fasilitator Penerima** | *[Tanda tangan manual saat terima]* | *[Tanda tangan manual saat terima]* |

---

## 4. CEKLIS KEPATUHAN FASILITATOR LAPANGAN

Sebelum dan selama penyerahan paket kepada validator, fasilitator wajib memverifikasi dan menandatangani ceklis operasional berikut:

- [ ] **Persetujuan Partisipan (*Informed Consent*)**:
  Fasilitator telah menjelaskan hak-hak partisipan, sifat sukarela evaluasi, transparansi tujuan riset, dan memperoleh lembar persetujuan tertulis (*informed consent*) yang sah sebelum paket evaluasi dibuka.
- [ ] **Independensi Evaluasi (*Blinded & Isolated Review*)**:
  Validator A dan Validator B melaksanakan evaluasi secara terpisah dan terisolasi, tanpa komunikasi, diskusi, konsultasi, atau pertukaran lembar jawaban satu sama lain.
- [ ] **Nol Kebocoran Label (*Zero Leakage Enforcement*)**:
  Fasilitator dilarang keras menyebutkan, mengisyaratkan, menampilkan, atau memberi petunjuk mengenai:
  - Label kelas asli (*ground truth*).
  - Prediksi model MobileNetV3-Small P1.
  - Skor keyakinan (*confidence score*).
  - Asal dataset (apakah sampel berasal dari set training atau set testing).
- [ ] **Ketiadaan Sugesti / Pembimbingan Jawaban (*Zero Biasing*)**:
  Fasilitator dilarang memberikan petunjuk lisan/non-lisan mengenai kebenaran gestur. Jika validator ragu, fasilitator hanya mengarahkan validator membaca kembali definisi kategori pada `PANDUAN_VALIDATOR_BISINDO.md`.
- [ ] **Integritas Penutupan Sesi (*Session Closeout*)**:
  Setelah pengisian selesai, berkas disalin langsung dari perangkat validator, dihitung nilai hash SHA-256 seketika sebelum dibuka, dan diarsipkan ke direktori penyimpanan *raw*.
