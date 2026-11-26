# AUDIT KEBOCORAN METADATA, VISUAL, & TERMINOLOGI BLINDING (BLINDNESS LEAKAGE AUDIT)
## Modul Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Audit Kebocoran Metadata Tersembunyi (Hidden Metadata Leakage — Task 3)

Pengujian forensik metadata dilakukan terhadap seluruh 36 berkas citra stimulus (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`) untuk mendeteksi apakah terdapat informasi biner tersembunyi yang dapat mengungkap label kelas, nama perangkat, nama subjek, atau riwayat split.

### 1.1 Hasil Pengujian Struktur Metadata
1. **Header EXIF (Exchangeable Image File Format)**:
   - Terdeteksi: **Nol (0) berkas**. Seluruh 36 berkas memiliki header EXIF kosong (`exif == {}`).
   - Tidak ada tag metadata kamera, tanggal asli pengambilan foto, orientasi sensor, maupun model perangkat yang tersimpan.
2. **Metadata IPTC / IIM (International Press Telecommunications Council)**:
   - Terdeteksi: **Nol (0) berkas**. Marker JPEG IPTC (`\xFF\xED`) tidak ditemukan dalam stream data.
   - Tidak ada caption, headline, copyright, atau kata kunci kelas yang tertanam.
3. **Paket Metadata XMP (Extensible Metadata Platform)**:
   - Terdeteksi: **Nol (0) berkas**. Penelusuran byte untuk string `<?xpacket`, `<x:xmpmeta`, dan `http://ns.adobe.com` menghasilkan $0$ kecocokan.
4. **Komentar JPEG (JPEG Comment Marker `\xFF\xFE`)**:
   - Terdeteksi: **Nol (0) berkas**. Tidak ada komentar teks tertanam di dalam berkas JPEG.
5. **Profil Warna ICC (ICC Profile)**:
   - Terdeteksi: **Nol (0) profil ICC kustom**. Berkas disimpan sebagai raster sRGB standar oleh pustaka Pillow tanpa payload profil ICC terpisah.
6. **Embedded Thumbnail**:
   - Terdeteksi: **Nol (0) thumbnail tertanam**. Berkas hanya memuat satu stream citra utama berdimensi $224 \times 224$.

### 1.2 Pemindaian String Sensitif pada Raw Bytes
Pemindaian byte biner secara mendalam dilakukan untuk mencari keberadaan:
- Nama berkas asli (misal `K_Polos Terang_Samsung_A55`, `C_Baju_Xiaomi_MI T10`).
- Kata kunci split (`train`, `val`, `test`).
- Tag metodologi (`TEST_SET_DIAGNOSTIC_ONLY`, `TRAIN_COHORT`).

**Hasil Temuan**: **NOL (0) KEBOCORAN**. Tidak ada satu pun nama berkas mentah atau kata kunci kelas yang ditemukan di dalam byte berkas citra stimulus. Satu-satunya string teks teknis yang hadir adalah penanda standar JPEG JFIF (`\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01...`), yang merupakan struktur kontainer biner normal dan tidak sensitif.

---

## 2. Audit Kebutaan Visual (Visual Blindness Review — Task 4)

Pemeriksaan visual komparatif dilakukan terhadap seluruh 36 citra stimulus melalui lembar kontak resolusi penuh:
[`docs/validation_p2/phase_2b_2/figures/stimulus_36_contact_sheet.png`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/figures/stimulus_36_contact_sheet.png).

### 2.1 Kriteria Pengujian Visual & Hasil
- **Huruf Alfabet Terlihat pada Gambar**: **NOL (0)**. Tidak ada huruf cetak, teks stiker, atau coretan huruf pada latar belakang maupun tangan.
- **Label Kelas / Watermark**: **NOL (0)**. Citra bebas dari watermark fotografer, logo institusi, maupun penanda angka kelas.
- **Overlay Prediksi Model**: **NOL (0)**. Tidak ada teks probabilitas, kotak pembatas (bounding box), atau grafik prediksi yang tergambar pada citra.
- **Teks pada Pakaian / Latar Belakang**:
  - Pada sampel dengan pakaian bermotif (misal baju bergaris pada `VAL-REV-034` atau pakaian gelap pada `VAL-REV-002`), tekstur kain tidak membentuk karakter huruf alfabet latin yang dapat membingungkan penilai.
- **Informasi Identitas Pribadi (PII)**:
  - Tidak ada wajah subjek yang tampak. Seluruh foto hanya menampilkan tangan, pergelangan tangan, dan sebagian lengan bawah. Identitas subjek penandatangan terlindungi penuh.

---

## 3. Verifikasi Lembar Kerja Peserta (Participant Sheet Audit — Task 5)

Pemeriksaan ketat dilakukan terhadap instrumen:
[`docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md).

### 3.1 Checklist Kepatuhan Lembar Peserta
| Parameter Audit | Status | Bukti Verifikasi |
| :--- | :---: | :--- |
| **Konsistensi 36 ID Sampel** | **PASS** | Tepat 36 baris tabel terurut dari `VAL-REV-001` hingga `VAL-REV-036`. |
| **Jalur Citra Stimulus Aman** | **PASS** | Seluruh rujukan menggunakan `stimulus_images/VAL-REV-XXX.jpg` tanpa menyebut nama folder kelas. |
| **Sanitasi Tag Metodologi** | **PASS** | Teks `TEST_SET_DIAGNOSTIC_ONLY` dan `TRAIN_COHORT` telah dihapus $100\%$. |
| **Sanitasi Nama Split** | **PASS** | Kata `train`, `val`, atau `test` tidak muncul pada lembar kerja penilai. |
| **Sanitasi Ground Truth Label** | **PASS** | Kolom huruf target asli tidak ada. |
| **Sanitasi Prediksi & Confidence** | **PASS** | Tebakan model AI dan persentase keyakinan tidak ditampilkan. |
| **Netralitas Instruksi** | **PASS** | Panduan tidak mengarahkan penilai ke pilihan tertentu dan memfasilitasi variasi dialek regional. |

---

## 4. Audit Terminologi Blinding (Blinding Terminology Audit — Task 6)

### 4.1 Perbedaan Konseptual: Blinded Review vs Double-Blind Review
Dalam metodologi riset saintifik:
1. **`BLINDED_VALIDATOR_REVIEW` (Single-Blind Review)**:
   - Terjadi ketika **hanya validator peserta** yang tidak mengetahui label kelas dan status sampel, namun peneliti/fasilitator yang mendampingi sesi mengetahui kunci jawaban (*ground truth mapping*) secara langsung saat pengujian berlangsung.
   - **Risiko Metodologis**: Peneliti dapat secara tidak sadar memberikan petunjuk non-verbal, ekspresi wajah, atau nada bicara yang memandu validator (*observer-expectancy bias*).
2. **`DOUBLE_BLIND_REVIEW` (Double-Blind Review Sejati)**:
   - Terjadi ketika **validator DAN fasilitator yang mengawasi sesi** sama-sama TIDAK MENGETAHUI label kelas asli, tebakan model AI, maupun status split sampel.
   - Hanya Administrator Riset independen (*Study Administrator*) yang memegang kunci pemetaan tertutup dan baru membukanya setelah seluruh lembar respon dikumpulkan dan disegel.

### 4.2 Matriks Pembagian Peran Operasional (Role Separation Protocol)
Untuk memastikan status validasi dapat diakui secara sah sebagai **`DOUBLE_BLIND_REVIEW`**, SignBridge ASEAN menetapkan protokol pemisahan peran tiga pihak:

```
[Study Administrator / Proposer]
         |
         | (Menyimpan INTERNAL_SAMPLE_MAPPING.md secara rahasia)
         | (Menyerahkan HANYA paket stimulus anonim & formulir kosong)
         v
[Session Facilitator / Test Proctor] <----> [Deaf BISINDO Validator]
  (TIDAK TAHU label asli)                     (TIDAK TAHU label asli)
  (TIDAK TAHU tebakan AI)                     (TIDAK TAHU tebakan AI)
  (Mendampingi secara netral)                 (Menilai mandiri di lembar respon)
         |
         | (Mengumpulkan lembar respon bertandatangan dalam amplop tertutup)
         v
[Study Administrator] (Melakukan dekripsi pasca-sesi & analisis inter-rater)
```

- **Ketentuan Status Resmi Proyek**:
  - Jika sesi validasi lapangan diawasi oleh fasilitator independen yang tidak memegang kunci dekripsi: statusnya adalah **`DOUBLE_BLIND_REVIEW`**.
  - Jika sesi lapangan didampingi langsung oleh peneliti pengembang model yang memegang kunci pemetaan: status formal yang wajib dilaporkan adalah **`BLINDED_VALIDATOR_REVIEW`**.

---

## 5. Tata Kelola Data Uji (Test-Set Governance — Task 7)

Tim audit menegaskan kembali aturan tata kelola data uji:
1. Sebanyak 19 sampel diagnostik test set (`VAL-REV-001` s/d `VAL-REV-015`, serta `VAL-REV-031` s/d `VAL-REV-034`) dievaluasi semata-mata untuk diagnosis kesalahan model historis.
2. **Anti-Leakage Guarantee**:
   - Sampel-sampel ini **tidak akan digunakan untuk melatih model P2**.
   - Sampel-sampel ini **tidak akan digunakan untuk memilih metode cropping/preprocessing**.
   - Sampel-sampel ini **tidak akan digunakan untuk menyetel hyperparameter model**.
3. **Preservasi Baseline P1**: Angka akurasi test set P1 sebesar **$61,19\%$ (410/670 benar)** tetap menjadi baseline komparatif yang tidak dapat diubah surut (*immutable historical benchmark*).

