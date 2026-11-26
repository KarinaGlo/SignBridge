# LAPORAN PENYEMPURNAAN METODOLOGIS INSTRUMEN VERIFIKASI FORMAL
## Gestur BISINDO Kelas A — Image Modality I1-P1 — SignBridge ASEAN

**Dokumen**: `docs/validation_p1/FORMAL_VERIFICATION_FORM_REVISION_REPORT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (MobileNetV3-Small I1-P1)  
**Dokumen Instrumen yang Direvisi**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)  
**Dokumen Audit Acuan**: [`docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md)  
**Dokumen Laporan Pilot**: [`docs/validation_p1/PILOT_COLLECTION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/PILOT_COLLECTION_REPORT.md)  
**Tanggal Evaluasi**: 16 November 2026  
**Auditor**: Senior Machine Learning Engineer, Dataset Auditor, & Research Validation Engineer  
**Status Instrumen Verifikasi**: **`PENDING VALIDATOR`** (Menunggu Pelaksanaan Sesi Wawancara Nyata Bersama Validator Kompeten)  
**Status Operasional Pilot**: **`HOLD (AWAITING GESTURE REFERENCE VERIFICATION)`**  

---

## 1. LATAR BELAKANG & TUJUAN PENYEMPURNAAN METODOLOGIS

Pada penyusunan draf awal instrumen verifikasi formal (`BISINDO_A_FORMAL_VERIFICATION_FORM.md`), ditemukan beberapa potensi bias metodologis yang perlu disempurnakan:
1. **Pertanyaan Menggiring (*Leading Questions*)**: Draf awal memuat pertanyaan yang mengasumsikan bahwa telapak tangan terbuka atau kepalan tinju satu tangan secara apriori "salah/bukan huruf A" di semua konteks, sehingga berisiko menekan objektivitas validator.
2. **Penggabungan SIBI dan ASL**: Draf awal mencampuradukkan sistem isyarat buatan pemerintah (SIBI) dengan bahasa isyarat alami Amerika (ASL), padahal keduanya memiliki konteks sosio-historis, dinamika penggunaan, dan peran yang berbeda dalam ekosistem Tuli Indonesia.
3. **Kerancuan Tiga Konsep Kunci**: Perlunya pemilahan eksplisit antara fakta dataset pelatihan komputer, keabsahan linguistik bahasa alami, dan keputusan penentuan ground truth penelitian.
4. **Peluang Pengakuan Penutur Alami Tanpa Sertifikat**: Kriteria kualifikasi awal terlalu formalistik (menekankan sertifikat), yang berpotensi memarginalkan penutur asli Tuli yang memperoleh bahasa isyarat secara organik dalam keluarga atau komunitasnya.
5. **Klaim Generalisasi Nasional**: Perlunya penegasan bahwa verifikasi oleh satu validator tidak dapat digeneralisasi sebagai standar mutlak seluruh Indonesia mengingat adanya variasi dialek regional.

Tujuan penyempurnaan ini adalah memastikan instrumen verifikasi bersifat **netral, eksploratif, ilmiah, bebas bias, dan menjunjung tinggi integritas sosiolinguistik komunitas Tuli Indonesia**.

---

## 2. MATRIKS PERUBAHAN METODOLOGIS & PENYEMPURNAAN INSTRUMEN

| No | Parameter Metodologis | Kondisi Draf Awal | Kondisi Setelah Penyempurnaan (Versi Revisi) |
|:---:|---|---|---|
| 1 | **Kerangka Tiga Dimensi** | Belum dipisahkan secara tegas; bercampur antara klaim dataset dan keabsahan bahasa. | **Dipisahkan secara eksplisit**: (1) Konsistensi label dataset training (fakta empiris 172 citra), (2) Keabsahan linguistik BISINDO (fakta sosiolinguistik), (3) Kelayakan sebagai ground truth penelitian (keputusan rekayasa AI). |
| 2 | **Batasan Generalisasi Nasional** | Belum dicantumkan peringatan keterbatasan lingkup geografis. | **Dicantumkan peringatan tegas**: Satu validator belum cukup untuk menarik kesimpulan standar seluruh Indonesia; hasil verifikasi mencerminkan wilayah dan komunitas asal validator. |
| 3 | **Format Pertanyaan (Netralitas)** | Pertanyaan 4 bersifat mengarahkan ("Penolakan Bentuk Non-BISINDO"). | **Dirombak total menjadi 4 pertanyaan netral & terbuka**: Menggali persepsi bentuk dua tangan, variasi regional, konteks SIBI, pengaruh ASL/internasional, dan pemaknaan telapak terbuka. |
| 4 | **Pemisahan SIBI vs ASL** | Digabungkan dalam satu opsi ("seperti pada SIBI/ASL"). | **Dipisahkan ke dalam pertanyaan independen**: Pertanyaan 3 secara khusus membahas SIBI (konteks SLB/formal), Pertanyaan 4 membahas ASL/International Sign (media sosial/istilah asing/generasi muda). |
| 5 | **Eksplorasi Telapak Terbuka** | Dianggap mutlak salah sejak awal pertanyaan. | **Dirumuskan secara terbuka (Pertanyaan 5)**: Menanyakan kepada validator makna leksikal atau fungsi apa yang paling tepat untuk mendeskripsikan gestur telapak terbuka 5 jari dalam komunikasi sehari-hari. |
| 6 | **Pencatatan Alasan & Bukti** | Hanya menyediakan kolom isian jawaban umum singkat. | **Ditambahkan sub-kolom terstruktur**: Setiap butir pertanyaan kini memiliki kolom *"Alasan & Argumen Validator"* dan kolom *"Bukti / Rujukan yang Mendasari"* (misal kamus lokal, tradisi komunitas, modul Pusbisindo). |
| 7 | **Kualifikasi Non-Sertifikasi** | Terkesan mengutamakan lisensi/sertifikasi resmi. | **Ditegaskan sertifikasi TIDAK wajib**: Pengalaman hidup (*lived experience*) penutur asli Tuli dan keaktifan di komunitas diakui secara sah dan setara. |
| 8 | **Profil Validator** | Hanya mencatat kode, peran, domisili, dan durasi umum. | **Diperluas mencakup profil linguistik utuh**: Bahasa ibu, usia mulai menggunakan isyarat, durasi pemakaian aktif, wilayah dialek yang dikuasai, organisasi komunitas, dan pengalaman mengajar/memfasilitasi. |
| 9 | **Status Isian Data** | Standby / Kosong. | **Tetap 100% KOSONG / BELUM TERISI**: Tidak ada jawaban, wawancara, atau keputusan validator yang dikarang. |

---

## 3. AUDIT KONSISTENSI DOKUMEN & INTEGRITAS SISTEM

Pemeriksaan konsistensi dilakukan di seluruh repositori untuk memastikan tidak ada kontradiksi antardokumen:

### A. Integritas Isian Instrumen (`BISINDO_A_FORMAL_VERIFICATION_FORM.md`)
- Tanggal Pelaksanaan: `[ BELUM DILAKSANAKAN — MENUNGGU SESI NYATA ]`
- Profil Validator: Seluruh kolom nama/peran/wilayah berstatus *unfilled* (`[ ... ]`).
- Pertanyaan 1 s.d. 6: Seluruh opsi checkbox tidak dicentang (`[ ]`), kolom alasan dan bukti berupa template kosong.
- Keputusan Akhir (*Final Verdict*): Seluruh pilihan checkbox berstatus *unfilled* (`[ ]`), status resmi tercatat: **`BELUM ADA KEPUTUSAN (MENUNGGU SESI NYATA)`**.
- Informed Consent: Berstatus *unfilled*, paraf/tanda tangan berstatus kosong.

### B. Hubungan Antardokumen Proyek
- [`docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md):  
  Telah diperbarui mencantumkan tautan ke formulir verifikasi formal revisi dengan status `PENDING VALIDATOR`.
- [`docs/validation_p1/PILOT_COLLECTION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/PILOT_COLLECTION_REPORT.md):  
  Status pilot konsisten: **`AWAITING GESTURE REFERENCE VERIFICATION` (HOLD)**, dengan referensi silang ke instrumen revisi.
- [`data/external/bisindo_validation/external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv):  
  Tetap bersih dengan header resmi 14 kolom tanpa ada baris data fiktif (0 baris data).
- Tracker Progres Pengumpulan ([`EXTERNAL_DATA_COLLECTION_PROGRESS.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md)):  
  Status: **`NOT STARTED` ⚪ (0 / 780 foto terkumpul)**.

### C. Verifikasi SHA-256 Checkpoint Model & ONNX
Pemeriksaan kriptografis memastikan bobot model tidak tersentuh selama audit dan revisi:
- `runs/image_i1_mobilenetv3_p1/best.pt`:  
  `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` (**100% UTUH**)
- `web/model/fingerspell.onnx`:  
  `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` (**100% UTUH**)
- `runs/image_i1_mobilenetv3/best.pt`:  
  `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` (**100% UTUH**)

### D. Integritas Git & Kode
- Tracked files modified: **0 berkas**.
- Tidak ada eksekusi git clean, reset, checkout, commit, atau push.
- Seluruh 21 unit test pada test suite validasi eksternal tetap lulus 100%.

---

## 4. KESIMPULAN & STATUS AKHIR

Penyempurnaan metodologis terhadap instrumen verifikasi formal telah selesai dilaksanakan dengan tingkat ketelitian ilmiah yang tinggi:
1. Instrumen verifikasi kini bersifat **objektif, netral, dan tidak menggiring**.
2. Perbedaan antara SIBI, ASL, dan BISINDO diperlakukan secara tepat sesuai konteks sosio-historisnya.
3. Kualifikasi validator inklusif terhadap penutur alami Tuli tanpa diskriminasi sertifikat.
4. Keterbatasan cakupan satu validator terhadap variasi nasional ditegaskan secara transparan.
5. **Seluruh isian data tetap kosong** dan tidak ada klaim keliru bahwa proses verifikasi telah selesai.

| Komponen | Status Operasional Resmi | Keterangan |
|---|:---:|---|
| **Instrumen Verifikasi Formal** | **`PENDING VALIDATOR`** ⏳ | Siap digunakan saat sesi wawancara nyata diselenggarakan. |
| **Tahap Pengambilan Foto Pilot** | **`HOLD` 🚫** | Pengambilan 10 foto fisik penutur EXT_S01 tetap ditangguhkan hingga sesi verifikasi nyata selesai dan diperiksa ulang (*re-examination*). |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**. |

