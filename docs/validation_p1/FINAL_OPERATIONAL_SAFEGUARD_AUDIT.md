# LAPORAN AUDIT PENGAMAN OPERASIONAL FINAL (OPERATIONAL SAFEGUARD AUDIT)
## Sesi Validasi Buta BISINDO Kelas A — Image Modality I1-P1
### Proyek: SignBridge ASEAN | Dokumen Evaluasi Kesiapan Operasional Lapangan

**Dokumen**: `docs/validation_p1/FINAL_OPERATIONAL_SAFEGUARD_AUDIT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling (I1-P1)  
**Dokumen Acuan yang Diperiksa**:
1. [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)
2. [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md)
3. [`docs/validation_p1/FINAL_BLIND_VALIDATION_READINESS_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_BLIND_VALIDATION_READINESS_AUDIT.md)
4. [`docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md)  
**Tanggal Audit**: 16 November 2026  
**Auditor**: Lead Research Methodologist, Dataset Quality Auditor, & ML Validation Engineer  
**Sifat Audit**: **READ-ONLY INSPECTION (Nol Modifikasi Kode, Model, Dataset, & Manifest)**  
**Kesimpulan Kesiapan (*Overall Verdict*)**: **`READY_WITH_LIMITATIONS`**  
**Status Instrumen Verifikasi**: **`PENDING VALIDATOR`**  
**Status Operasional Pilot**: **`PILOT_HOLD`**  
**Progres Pengumpulan Data Eksternal**: **`NOT STARTED` (0 / 780 foto valid)**  

---

## 1. BUKTI BERKAS & BAGIAN DOKUMEN YANG DIPERIKSA

Pemeriksaan silang dilakukan secara teliti terhadap 4 dokumen metodologi dan implementasi operasional:

| Berkas Dokumen | Bagian / Bab yang Diperiksa | Fokus Verifikasi Pengaman Operasional |
|---|---|---|
| `BISINDO_A_FORMAL_VERIFICATION_FORM.md` | Bagian 1, 2, 3, 4, 5.A, 5.B, 5.E, 6, 7 | Kerangka tiga dimensi, isolasi kolom peneliti vs validator, struktur multi-validator, granularitas consent, format tabel pencatatan. |
| `BLIND_VALIDATION_SESSION_PROTOCOL.md` | Bagian 1, 2, 3 (Langkah 1–7), Bagian 4 | Urutan kronologis sesi, SOP pencegahan bias (*zero leading*), penguncian respon Tahap 1, pengacakan presentasi kartu, penanganan edge cases. |
| `FINAL_BLIND_VALIDATION_READINESS_AUDIT.md` | Bagian 2, 3, 4, 5, 6, 7, 8 | Verifikasi fisik 7 berkas stimulus (resolusi, format, SHA-256, EXIF), taksonomi 6 faktor perbedaan pendapat, audit batasan metodologis. |
| `FINAL_METHODOLOGICAL_REVISION_REPORT.md` | Bagian 1 s.d. 12 | Matriks perbandingan metodologi, integritas artefak kriptografis, batasan riset. |

---

## 2. MATRIKS EVALUASI PENGAMAN OPERASIONAL (OPERATIONAL SAFEGUARD MATRIX)

Setiap pilar pengaman operasional dievaluasi menggunakan tiga tingkatan status:
- **`PASS`**: Persyaratan metodologis dan pengaman operasional telah terpenuhi secara penuh dalam dokumentasi dan tata kelola.
- **`PASS_WITH_LIMITATION`**: Prinsip metodologis telah ditetapkan dengan baik, namun implementasi praktis di lapangan membutuhkan mitigasi/safeguard tambahan sebelum sesi tatap muka.
- **`NOT_READY`**: Terdapat kegagalan pengaman kritis yang berpotensi membatalkan validitas ilmiah atau melanggar etika riset.

```
+---------------------------------------------------------------------------------------------------------+
|                                    RINGKASAN STATUS PENGAMAN OPERASIONAL                                |
+----+--------------------------------------------+-----------------------+-------------------------------+
| No | Pilar Pengaman Operasional                 | Status Evaluasi       | Kategori Catatan              |
+----+--------------------------------------------+-----------------------+-------------------------------+
| 1  | Protokol Urutan Randomisasi Stimulus       | PASS_WITH_LIMITATION  | Prosedur Pengacakan Per Sesi  |
| 2  | Pencegahan Kebocoran Informasi (Leakage)   | PASS_WITH_LIMITATION  | Isolasi Materi Validator      |
| 3  | Tata Urut Kronologis Informed Consent      | PASS                  | Etika Terstandar (Granular)   |
| 4  | Taksonomi Perbedaan Pendapat Validator     | PASS_WITH_LIMITATION  | Hipotesis Analisis 6 Faktor   |
| 5  | Batasan Metodologis Stimulus & Korpus      | PASS                  | Definisi Batas Ilmiah Tegas   |
| 6  | Kepatuhan Status Operasional Proyek        | PASS                  | Nol Data Fiktif, Status Utuh  |
| 7  | Integritas Repositori, Kode, & Model       | PASS                  | 100% Read-Only, SHA-256 Cocok |
+----+--------------------------------------------+-----------------------+-------------------------------+
```

---

## 3. TEMUAN AUDIT RINCI BERDASARKAN PILAR EVALUASI

### A. Pilar 1: Protokol Urutan Randomisasi Stimulus (`PASS_WITH_LIMITATION`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Kode stimulus (`IMG_BLD_01` s.d. `IMG_BLD_07`) terbukti sepenuhnya netral tanpa label kelas (`A/B/C/D`).
  - Mapping kode anonim dan kelas aktual hanya tercatat pada master sheet peneliti (`BISINDO_A_FORMAL_VERIFICATION_FORM.md` Bagian 5.B).
  - Kolom `Display Order` disediakan secara eksplisit untuk mencatat nomor urut kemunculan aktual bagi masing-masing validator.
- **Keterbatasan Operasional (`LIMITATION`)**:
  - Urutan bawaan kode stimulus mencerminkan pola selang-seling target-pembanding ($A \to B \to A \to C \to A \to D \to A$).
  - Saat ini, pengacakan urutan masih berupa **instruksi prosedural tertulis** pada SOP lapangan (`BLIND_VALIDATION_SESSION_PROTOCOL.md` Bagian 2), belum diwujudkan dalam bentuk set pengacakan terstandardisasi per sesi (misal tabel seed pengacakan acak $V_1, V_2$). Jika enumerator lalai mengocok kartu peraga, ada risiko pola selang-seling terbaca oleh validator.

### B. Pilar 2: Pencegahan Kebocoran Informasi (Information Leakage) (`PASS_WITH_LIMITATION`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Berkas fisik citra terbukti bebas dari metadata EXIF (0 tag EXIF).
  - Nama file asli, struktur folder `/A/`, dan label aktual dihilangkan dari kartu uji.
  - Deskripsi morfologis ("segitiga", "dua tangan") dilarang diucapkan selama Tahap 1.
- **Keterbatasan Operasional (`LIMITATION`)**:
  - Terdapat perbedaan kritis antara:
    1. *Master Worksheet Peneliti*: Berkas `BISINDO_A_FORMAL_VERIFICATION_FORM.md` memuat kolom `Actual Class` dan `File Asli di Repository`.
    2. *Participant-Facing Stimulus Material*: Kartu atau slide visual yang langsung dilihat oleh validator.
  - Dalam repositori saat ini, set kartu presentasi yang terisolasi secara fisik/digital (misal PDF slide deck blind tanpa teks) belum diekspor ke folder khusus terpisah. Auditor menegaskan: **materi final yang benar-benar ditampilkan ke mata validator belum dapat diperiksa secara fisik di repositori**. Master worksheet dilarang keras diperlihatkan ke validator.

### C. Pilar 3: Tata Urut Kronologis Informed Consent (`PASS`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Urutan kronologis pada `BLIND_VALIDATION_SESSION_PROTOCOL.md` Langkah 1 s.d. 7 terverifikasi tepat dan etis:
    $$\text{Penyambutan \& Edukasi Hak} \longrightarrow \text{Persetujuan Informed Consent} \longrightarrow \text{Blind Observation} \longrightarrow \text{Locking} \longrightarrow \text{Label Disclosure} \longrightarrow \text{Post-Assessment} \longrightarrow \text{Penutupan}$$
  - Penandatanganan informed consent dilakukan pada **Langkah 1 (di awal sesi)**, BUKAN setelah jawaban dikumpulkan.
  - Persetujuan bersifat granular: Penolakan perekaman audio/video **TIDAK membatalkan partisipasi**; notulis beralih ke pencatatan tertulis penuh (`BISINDO_A_FORMAL_VERIFICATION_FORM.md` Bagian 5.E).

### D. Pilar 4: Taksonomi Perbedaan Pendapat Validator (`PASS_WITH_LIMITATION`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Ditetapkan larangan keras terhadap voting mayoritas untuk memaksakan keseragaman respon.
  - Perbedaan pendapat tidak otomatis disimpulkan sebagai variasi dialek regional semata.
  - Taksonomi 6 faktor telah dirumuskan pada `FINAL_BLIND_VALIDATION_READINESS_AUDIT.md` Bagian 5.
- **Keterbatasan Operasional (`LIMITATION`)**:
  - Enam faktor tersebut (variasi regional, latar pemerolehan bahasa, konteks situasi, pengaruh SIBI/ASL, kualitas gambar 2D, ketidakpastian subjektif) harus digunakan oleh peneliti sebagai **hipotesis analisis yang wajib dibuktikan dengan rekaman alasan/bukti**, bukan sebagai label otomatis.
  - Pada formulir master `BISINDO_A_FORMAL_VERIFICATION_FORM.md`, taksonomi ini belum dicantumkan sebagai checklist diagnostik bagi notulis saat sesi berlangsung (baru berada pada laporan audit).

### E. Pilar 5: Batasan Metodologis Stimulus & Korpus (`PASS`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Dokumen secara tegas memposisikan 7 citra sebagai stimulus eksplorasi kualitatif awal, bukan benchmark akurasi penutur Tuli.
  - Ditegaskan bahwa stimulus ini bukan bukti diskriminasi seluruh 26 huruf alfabet (A–Z) dan bukan bukti representativitas nasional BISINDO.
  - Evaluasi 780 foto eksternal diposisikan secara benar sebagai **pengujian generalisasi model komputasional**, bukan pembuktian otomatis validitas linguistik. Validitas linguistik tetap menjadi ranah komunitas Tuli dan pakar bahasa isyarat.

### F. Pilar 6: Kepatuhan Status Operasional Proyek (`PASS`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Status instrumen verifikasi: **`PENDING VALIDATOR`** (terpelihara konsisten).
  - Status tahap pilot lapangan: **`PILOT_HOLD`** (terpelihara konsisten).
  - Status progres pengumpulan data: **`NOT STARTED`** dengan capaian **`0 / 780 foto`** (terpelihara konsisten).
  - Tidak ada data fiktif, tidak ada simulasi wawancara, tidak ada nama validator rekaan, dan tidak ada verdict yang dicentang secara prematur.

### G. Pilar 7: Integritas Repositori, Kode, & Model (`PASS`)
- **Temuan yang Terpenuhi (`PASS`)**:
  - Audit dijalankan 100% read-only tanpa eksekusi training, inferensi, modifikasi script, database, maupun web application.
  - Tidak ada operasi Git destruktif.

---

## 4. RISIKO RESIDUAL YANG MASIH TERSISA (RESIDUAL RISKS)

Auditor mengidentifikasi 3 risiko residual tingkat operasional yang harus dimitigasi sebelum sesi tatap muka:

1. **Risiko Kebocoran Dokumen oleh Enumerator (*Human Operator Leakage Risk*)**:
   Jika pewawancara lapangan membuka file `BISINDO_A_FORMAL_VERIFICATION_FORM.md` di layar laptop yang juga menghadap ke validator, validator dapat membaca kolom `Actual Class`.  
   *Mitigasi*: Layar laptop pencatatan harus membelakangi validator, atau validator hanya disajikan kartu cetak fisik tanpa teks.
2. **Risiko Keterikatan Urutan Bawaan (*Order Habituation Risk*)**:
   Pewawancara lupa mengacak kartu dan menampilkan sesuai nomor kode $01 \to 07$, sehingga ritme target-pembanding terbaca.  
   *Mitigasi*: Penyusunan lembar urutan acak terpisah (*randomization assignment sheet*) sebelum sesi dimulai.
3. **Risiko Ambiguitas Citra 2D Statis (*Static Occlusion Risk*)**:
   Citra beresolusi $224 \times 224$ dapat menimbulkan keraguan pada artikulasi lipatan jari kelingking/manis bagi validator tertentu.  
   *Mitigasi*: Pewawancara wajib mencatat keraguan akibat sudut/kualitas citra pada faktor 5 (Kualitas & Ambiguitas Gambar), bukan menganggap validator tidak tahu bentuk isyaratnya.

---

## 5. CHECKLIST SEBELUM SESI NYATA (PRE-SESSION GO / NO-GO CHECKLIST)

Sebelum validator pertama (`VAL_BISINDO_01`) dipersilakan masuk ke ruang wawancara, penanggung jawab lapangan wajib memverifikasi checklist berikut:

```
[ ] 1. Lembar penjelasan penelitian dan informed consent cetak tersedia (terpisah untuk wawancara & rekaman).
[ ] 2. Kartu peraga fisik atau slide digital terisolasi telah siap TANPA teks nama file, TANPA kelas, dan TANPA deskripsi.
[ ] 3. Urutan penyajian untuk Validator 1 telah diacak secara formal dan nomor urut dicatat pada kolom 'Display Order'.
[ ] 4. Master worksheet peneliti berada dalam posisi tersembunyi dari pandangan validator.
[ ] 5. Juru Bahasa Isyarat (JBI) pendamping memahami protokol zero-leading (dilarang memberi petunjuk atau konfirmasi).
[ ] 6. Notulis memahami taksonomi 6 faktor untuk mencatat argumentasi validator secara verbatim.
[ ] 7. Konfirmasi bahwa sesi ini berstatus studi pendahuluan non-nasional dan tidak ada klaim standar mutlak.
```

---

## 6. AUDIT INTEGRITAS REPOSITORI & BUKTI KRIPTOGRAFIS

### A. Verifikasi Hash SHA-256 Artefak Model PyTorch & ONNX

Pemeriksaan hash SHA-256 membuktikan bahwa bobot model jaringan saraf tiruan dan model web runtime tetap **100% utuh dan tidak tersentuh**:

```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "runs/image_i1_mobilenetv3/best.pt", "web/model/fingerspell.onnx"
```

| Path Artefak Kritis | Algoritma | Hash Kriptografis Terverifikasi (SHA-256) | Integritas Fisik |
|---|:---:|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | SHA-256 | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% UTUH IDENTIK ✅** |
| `runs/image_i1_mobilenetv3/best.pt` | SHA-256 | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% UTUH IDENTIK ✅** |
| `web/model/fingerspell.onnx` | SHA-256 | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% UTUH IDENTIK ✅** |

### B. Status Git Working Tree Sebelum dan Sesudah Audit
- Output `git status --short`:
  - Modifikasi pada berkas terlacak (*tracked files*): **0 berkas**.
  - Berkas baru yang ditambahkan: hanya berkas laporan dokumentasi audit `docs/validation_p1/FINAL_OPERATIONAL_SAFEGUARD_AUDIT.md`.
  - Tidak ada eksekusi perintah destruktif Git (`git clean`, `git reset`, `git checkout`). Seluruh berkas lokal dan untracked terjaga utuh.

### C. Status Manifest Aktual & Progres Lapangan
- `data/external/bisindo_validation/external_manifest.csv`: **Tersedia (163 bytes)**, 14 kolom header resmi, **0 baris data fiktif**.
- `docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md`: **`NOT STARTED` ⚪ (0 / 780 foto valid)**, defisit pilot: 10 foto, defisit total: 780 foto.

---

## 7. KESIMPULAN AKHIR & STATUS OPERASIONAL RESMI

### A. Kesimpulan Kesiapan Pengaman (*Overall Readiness Verdict*)

$$\mathbf{FINAL\ SAFEGUARD\ VERDICT} = \mathbf{READY\_WITH\_LIMITATIONS}$$

**Justifikasi Keputusan**:  
Seluruh landasan metodologi, alur etika informed consent, isolasi kolom respon, dan pengujian fisik 7 berkas stimulus telah memenuhi standar kualitas riset (*PASS*). Status *READY_WITH_LIMITATIONS* diberikan karena kesiapan operasional lapangan masih memerlukan kepatuhan enumerator terhadap mitigasi kebocoran materi presentasi dan prosedur pengacakan urutan stimulus per validator sebelum sesi tatap muka diselenggarakan.

### B. Status Operasional Proyek
Audit ini menegaskan bahwa **sesi wawancara bersama validator BELUM dilaksanakan**. Status operasional proyek tetap berada pada status tunggu terkontrol:

| Parameter Operasional | Status Resmi Proyek | Keterangan Operasional |
|---|:---:|---|
| **Kesiapan Pengaman Sesi** | **`READY_WITH_LIMITATIONS` ⚠️** | Protokol siap dijalankan dengan kepatuhan terhadap checklist pra-sesi. |
| **Status Instrumen Verifikasi** | **`PENDING VALIDATOR` ⏳** | Seluruh kolom isian respon, profil, dan informed consent tetap 100% kosong (*unfilled*). |
| **Status Tahap Pilot Lapangan** | **`PILOT_HOLD` 🚫** | Pengambilan fisik 10 foto kelas A penutur EXT_S01 **DITANGGUHKAN MUTLAK** sampai sesi nyata selesai, data dicatat objektif, dan disetujui dalam *re-examination*. |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**, defisit: 780 foto. |

