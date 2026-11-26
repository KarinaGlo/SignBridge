# LEMBAR PENILAIAN VALIDATOR BUTA BISINDO (VALIDATOR PARTICIPANT REVIEW SHEET)
## Modul Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)
#### Standar Metodologi: BLINDED_VALIDATOR_REVIEW (Phase 2C.8 Blind Letter Identification)

---

### PANDUAN PENGISIAN UNTUK VALIDATOR (PARTICIPANT INSTRUCTIONS)

1. **Tujuan Penilaian**:
   Lembar kerja ini disusun untuk mengumpulkan penilaian mandiri dari validator Tuli BISINDO berkualifikasi mengenai keabsahan visual, keterbacaan gestur, dan identifikasi huruf alfabet BISINDO pada 36 sampel citra diam (*stimulus images*).

2. **Prosedur Validasi Buta (BLINDED_VALIDATOR_REVIEW)**:
   - Evaluasi ini menggunakan metodologi **BLINDED_VALIDATOR_REVIEW** (Penilaian Buta Mandiri). Penilaian dilakukan secara independen dan blinded. Validator tidak diberi tahu label asli, prediksi model, maupun skor model. Tim peneliti tetap menyimpan mapping internal untuk keperluan audit dan adjudikasi.
   - Validator menilai keabsahan gestur murni berdasarkan pengetahuan alami BISINDO dan bukti visual secara independen tanpa petunjuk jawaban.
   - Identitas sampel disamarkan menggunakan kode anonim (`VAL-REV-001` sampai `VAL-REV-036`).

3. **Paradigma Identifikasi Huruf Buta (Blind Letter Identification)**:
   Validator diminta mengisi tiga aspek utama untuk setiap foto stimulus:
   - **Huruf Teridentifikasi (`identified_letter`)**: Tuliskan satu huruf kapital (A–Z) yang diperagakan. Jika isyarat tidak terbaca sama sekali atau rusak, kosongkan kolom ini.
   - **Kejelasan Isyarat (`decision`)**:
     - `IDENTIFIED`: Konfigurasi tangan, jari, dan orientasi telapak tangan **sah, jelas, wajar, dan pasti** membentuk satu huruf.
     - `AMBIGUOUS`: Konfigurasi jari meragukan, **berada di antara dua bentuk huruf**, atau sudut kamera menyamarkan pose.
     - `UNDETERMINABLE`: Kualitas visual tidak memungkinkan pembacaan (foto terlalu gelap, silau, blur parah, atau jari kunci terpotong oleh bingkai foto).
   - **Variasi Regional (`regional_variation`)**: `YES` (ragam daerah), `NO` (standar nasional), atau `UNSURE` (tidak yakin).
   - **Catatan / Notes**: Tuliskan keterangan singkat jika ada ragam daerah, ambiguitas, atau kerusakan foto.

4. **Media Pengisian yang Tersedia**:
   - **Sangat Disarankan**: Gunakan buku kerja interaktif **`VALIDATOR_B_WORKBOOK.xlsx`** yang memuat pratinjau gambar 96x96 piksel langsung di samping baris isian, dropdown pilihan, dan pemantau progres otomatis.
   - **Alternatif**: Isi formulir CSV **`VALIDATOR_B_RESPONSE_TEMPLATE.csv`** dengan melihat foto di folder `stimulus_images/`.
   - **Alternatif Cetak**: Gunakan tabel di bawah ini sebagai lembar kerja cetak fisik jika diperlukan.

5. **Perhatian Khusus Huruf Dinamis (J dan Z)**:
   - Penilaian menggunakan stimulus foto statis.
   - Keputusan `IDENTIFIED` hanya menunjukkan bahwa pose statis dapat dikenali sebagai representasi awal/akhir huruf oleh validator.
   - Penilaian foto statis **tidak membuktikan ketepatan lintasan gerakan dinamis**.
   - Jika pose tidak cukup informatif atau membingungkan dengan huruf lain, pilih `AMBIGUOUS` atau `UNDETERMINABLE`.

---

### INFORMASI VALIDATOR
- **Validator Code (Kode Anonim Penilai)**: `VAL-B`
- **Tanggal Penilaian (Review Date)**: `____________________`
- **Tanda Tangan / Verifikasi**: `____________________`

---

### TABEL PENILAIAN VALIDATOR (36 SAMPEL)

| No | Sample ID | Stimulus Image Path | Huruf Teridentifikasi (A–Z) | Kejelasan Isyarat (`IDENTIFIED` / `AMBIGUOUS` / `UNDETERMINABLE`) | Variasi Regional (`YES` / `NO` / `UNSURE`) | Catatan / Notes |
| :-: | :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `VAL-REV-001` | `stimulus_images/VAL-REV-001.jpg` | | | | |
| 2 | `VAL-REV-002` | `stimulus_images/VAL-REV-002.jpg` | | | | |
| 3 | `VAL-REV-003` | `stimulus_images/VAL-REV-003.jpg` | | | | |
| 4 | `VAL-REV-004` | `stimulus_images/VAL-REV-004.jpg` | | | | |
| 5 | `VAL-REV-005` | `stimulus_images/VAL-REV-005.jpg` | | | | |
| 6 | `VAL-REV-006` | `stimulus_images/VAL-REV-006.jpg` | | | | |
| 7 | `VAL-REV-007` | `stimulus_images/VAL-REV-007.jpg` | | | | |
| 8 | `VAL-REV-008` | `stimulus_images/VAL-REV-008.jpg` | | | | |
| 9 | `VAL-REV-009` | `stimulus_images/VAL-REV-009.jpg` | | | | |
| 10 | `VAL-REV-010` | `stimulus_images/VAL-REV-010.jpg` | | | | |
| 11 | `VAL-REV-011` | `stimulus_images/VAL-REV-011.jpg` | | | | |
| 12 | `VAL-REV-012` | `stimulus_images/VAL-REV-012.jpg` | | | | |
| 13 | `VAL-REV-013` | `stimulus_images/VAL-REV-013.jpg` | | | | |
| 14 | `VAL-REV-014` | `stimulus_images/VAL-REV-014.jpg` | | | | |
| 15 | `VAL-REV-015` | `stimulus_images/VAL-REV-015.jpg` | | | | |
| 16 | `VAL-REV-016` | `stimulus_images/VAL-REV-016.jpg` | | | | |
| 17 | `VAL-REV-017` | `stimulus_images/VAL-REV-017.jpg` | | | | |
| 18 | `VAL-REV-018` | `stimulus_images/VAL-REV-018.jpg` | | | | |
| 19 | `VAL-REV-019` | `stimulus_images/VAL-REV-019.jpg` | | | | |
| 20 | `VAL-REV-020` | `stimulus_images/VAL-REV-020.jpg` | | | | |
| 21 | `VAL-REV-021` | `stimulus_images/VAL-REV-021.jpg` | | | | |
| 22 | `VAL-REV-022` | `stimulus_images/VAL-REV-022.jpg` | | | | |
| 23 | `VAL-REV-023` | `stimulus_images/VAL-REV-023.jpg` | | | | |
| 24 | `VAL-REV-024` | `stimulus_images/VAL-REV-024.jpg` | | | | |
| 25 | `VAL-REV-025` | `stimulus_images/VAL-REV-025.jpg` | | | | |
| 26 | `VAL-REV-026` | `stimulus_images/VAL-REV-026.jpg` | | | | |
| 27 | `VAL-REV-027` | `stimulus_images/VAL-REV-027.jpg` | | | | |
| 28 | `VAL-REV-028` | `stimulus_images/VAL-REV-028.jpg` | | | | |
| 29 | `VAL-REV-029` | `stimulus_images/VAL-REV-029.jpg` | | | | |
| 30 | `VAL-REV-030` | `stimulus_images/VAL-REV-030.jpg` | | | | |
| 31 | `VAL-REV-031` | `stimulus_images/VAL-REV-031.jpg` | | | | |
| 32 | `VAL-REV-032` | `stimulus_images/VAL-REV-032.jpg` | | | | |
| 33 | `VAL-REV-033` | `stimulus_images/VAL-REV-033.jpg` | | | | |
| 34 | `VAL-REV-034` | `stimulus_images/VAL-REV-034.jpg` | | | | |
| 35 | `VAL-REV-035` | `stimulus_images/VAL-REV-035.jpg` | | | | |
| 36 | `VAL-REV-036` | `stimulus_images/VAL-REV-036.jpg` | | | | |
