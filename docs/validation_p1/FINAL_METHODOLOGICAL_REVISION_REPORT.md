# LAPORAN REVISI METODOLOGIS FINAL INSTRUMEN VERIFIKASI GESTUR BISINDO KELAS A
## Image Modality I1-P1 (MobileNetV3-Small) — SignBridge ASEAN
### Laporan Tim Multidisiplin: Metodologi, Linguistik Isyarat, Budaya Tuli, Kualitas Dataset, & Machine Learning

**Dokumen**: `docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling (I1-P1)  
**Dokumen yang Direvisi**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)  
**Panduan Lapangan Baru**: [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md)  
**Dokumen Audit Acuan**: [`docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md)  
**Dokumen Pilot Acuan**: [`docs/validation_p1/PILOT_COLLECTION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/PILOT_COLLECTION_REPORT.md)  
**Tanggal Evaluasi & Finalisasi**: 16 November 2026  
**Tim Evaluator Multidisiplin**:
1. Senior Research Methodologist
2. Sign Language Linguist / Sociolinguistic Researcher
3. Deaf Community Research Advisor
4. Dataset Quality and Validation Auditor
5. Senior Machine Learning Engineer  
**Status Operasional Dokumen**: **`DOCUMENT_REVISION_COMPLETE`**  
**Status Verifikasi Instrumen**: **`PENDING VALIDATOR`** (Menunggu Pelaksanaan Sesi Wawancara Nyata)  
**Status Tahap Pilot Lapangan**: **`HOLD (AWAITING GESTURE REFERENCE VERIFICATION)`**  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Revisi metodologis final ini dilakukan untuk mentransformasi instrumen verifikasi referensi gestur BISINDO Kelas A dari formulir konfirmasi yang berpotensi memiliki *confirmation bias* menjadi **instrumen penyelidikan ilmiah yang objektif, netral, berakar pada penghormatan sosiolinguistik budaya Tuli, dan kokoh secara metodologis**.

Berdasarkan audit dataset, 172 citra Kelas A pada korpus Mendeley proyek ini secara visual konsisten memperlihatkan bentuk dua tangan menyerupai segitiga. Namun, tim multidisiplin menegaskan bahwa **fakta konsistensi dataset pelatihan komputer tidak boleh secara otomatis dianggap sebagai bukti keabsahan bahasa alami BISINDO ataupun kelayakan instan sebagai ground truth evaluasi eksternal**. Bentuk gestur tersebut harus diuji secara empiris melalui sesi verifikasi lapangan yang bebas dari pengaruh peneliti.

Seluruh template isian jawaban validator, profil validator, tanggal sesi, hasil keputusan (*verdict*), dan lembar informed consent **tetap dibiarkan 100% kosong (unfilled)**. Status pilot pengumpulan 10 foto penutur EXT_S01 tetap berada dalam status **`HOLD`**.

---

## 2. TEMUAN MASALAH METODOLOGIS PADA INSTRUMEN SEBELUMNYA

Audit mendalam oleh tim multidisiplin mengidentifikasi 8 kelemahan kritis pada versi instrumen terdahulu:

1. **Bias Konfirmasi Akibat Pengungkapan Label di Awal (*Premature Label Disclosure Bias*)**:
   Pada draf sebelumnya, validator langsung diperlihatkan gambar dengan judul "BISINDO Kelas A" dan deskripsi peneliti ("bentuk segitiga"). Hal ini menggiring validator secara psikologis untuk membenarkan label tersebut, alih-alih memberikan interpretasi bebas berdasarkan pengalaman komunikasi aslinya.
2. **Ketiadaan Citra Kontrol / Pembanding (*Absence of Contrastive Distractors*)**:
   Instrumen sebelumnya hanya menyajikan citra Kelas A tanpa menyertakan sampel kelas lain sebagai pembanding (*distractor controls*), sehingga tidak dapat menguji sensitivitas diskriminasi fonologis gestur.
3. **Pencampuran Konseptual Sistem Isyarat yang Berbeda**:
   SIBI (sistem isyarat buatan berbasis tata bahasa Indonesia lisan), ASL (bahasa isyarat alami Amerika), dan International Sign (sistem komunikasi kontak internasional) sempat digabungkan atau disamakan, mengabaikan konteks sosiolinguistik masing-masing dalam komunitas Tuli Indonesia.
4. **Pertanyaan Menggiring pada Konfigurasi Telapak Terbuka**:
   Pertanyaan mengenai telapak tangan terbuka mengasumsikan bentuk tersebut "pasti salah/bukan huruf A di semua sistem" dan menyodorkan opsi angka 5 atau sapaan sebelum validator berbicara, merusak objektivitas data kualitatif.
5. **Hambatan Elitisme Sertifikasi (*Certification Barrier*)**:
   Kriteria kualifikasi awal terlalu menekankan sertifikat formal (misal PUSBISINDO), yang berisiko menyingkirkan penutur asli Tuli (*native generational Deaf signers*) yang menguasai BISINDO secara organik dalam keluarga atau pergaulan komunitasnya.
6. **Ketiadaan Protokol Multi-Validator & Bahaya Over-Generalisasi**:
   Instrumen belum memiliki protokol formal untuk mengelola partisipasi lebih dari satu validator serta belum memberikan peringatan bahwa data dari satu validator tidak dapat diklaim sebagai standar nasional BISINDO seluruh Indonesia.
7. **Pencatatan Respon Tunggal Tanpa Pelacakan Perubahan Sikap**:
   Instrumen lama tidak menyediakan pemisahan kolom antara respon murni sebelum mengetahui label (*blind interpretation*) dan respon kritis setelah label diungkapkan (*post-disclosure assessment*).
8. **Kategori Keputusan Biner Tanpa Gradasi**:
   Pilihan keputusan awal hanya biner (Sah vs Ditolak), tidak menyediakan kategori ilmiah untuk mengakomodasi variasi dialektal atau kebutuhan kajian lintas-wilayah.

---

## 3. PERUBAHAN METODOLOGIS YANG DITERAPKAN (CHANGES IMPLEMENTED)

Untuk mengatasi seluruh kelemahan di atas, tim multidisiplin menerapkan 8 revisi struktural:

1. **Implementasi Protokol Dua Tahap (Two-Phase Protocol)**:
   - **Tahap A (Blind Observation)**: Citra disajikan tanpa label kelas, tanpa nama file asli, diacak urutannya, dan dicampur dengan citra pembanding. Validator menjawab pertanyaan terbuka murni.
   - **Tahap B (Label Disclosure)**: Label kelas diungkapkan secara transparan setelah Tahap A dikunci, untuk mengevaluasi kesesuaian label tanpa menghapus catatan Tahap A.
2. **Penyusunan Set Citra Uji Kontras (Contrastive Image Set)**:
   Menyusun 7 sampel citra anonim (`IMG_BLD_01` s.d. `IMG_BLD_07`) yang memadukan 4 sampel Kelas A dan 3 sampel pembanding (Kelas B, C, D) yang bersumber dari citra nyata di repository.
3. **Pemisahan Konseptual 4 Sistem Bahasa Isyarat**:
   Menyusun modul pertanyaan terpisah dan independen untuk: (1) BISINDO alami, (2) SIBI dalam konteks pendidikan SLB, (3) ASL dalam konteks istilah asing/medsos, dan (4) International Sign dalam konteks global.
4. **Netralisasi Pertanyaan Telapak Terbuka**:
   Menghilangkan seluruh opsi menggiring; pertanyaan diformulasikan secara terbuka untuk menggali fungsi dan makna konfigurasi telapak tangan terbuka 5 jari berdasarkan pengalaman hidup validator.
5. **Inklusivitas Kualifikasi Validator**:
   Menegaskan bahwa sertifikasi formal **TIDAK WAJIB** apabila kompetensi validator didasari oleh pengalaman hidup (*lived experience*) sebagai penutur primer Tuli dan keaktifan dalam komunitas Tuli.
6. **Protokol Multi-Validator & Peringatan Batasan Wilayah**:
   Menargetkan minimal 2 validator independen, melarang pemungutan suara mayoritas (*voting*) jika terjadi perbedaan pendapat, serta mencantumkan peringatan resmi bahwa data satu validator tidak merepresentasikan standar nasional seluruh Indonesia.
7. **Penambahan Kolom Alasan & Bukti yang Mendasari**:
   Setiap butir modul pertanyaan kini menyediakan kolom eksplisit untuk merekam argumentasi kualitatif dan dasar bukti rujukan validator (misal kamus daerah, kurikulum isyarat, tradisi komunitas).
8. **Kerangka Keputusan Tiga Dimensi & 5 Kategori Verdict Terstandar**:
   Memisahkan dimensi konsistensi dataset, keabsahan bahasa, dan kelayakan ground truth, dengan 5 kategori keputusan resmi: `CONFIRMED_WITHIN_VALIDATOR_SCOPE`, `CONFIRMED_WITH_LIMITATIONS`, `NEEDS_CROSS_REGIONAL_REVIEW`, `REJECTED_WITH_EVIDENCE`, dan `INCONCLUSIVE`.

---

## 4. MATRIKS PERBANDINGAN SEBELUM DAN SESUDAH REVISI

| Aspek Metodologis | Kondisi Sebelum Revisi | Kondisi Setelah Revisi (Versi Final) |
|---|---|---|
| **Penyajian Gambar** | Label kelas dan deskripsi "huruf A segitiga" ditampilkan sejak awal. | **Blind Presentation**: Nama file, kelas, dan deskripsi disembunyikan; gambar diacak dengan kode `IMG_BLD_...`. |
| **Gambar Pembanding** | Tidak ada; hanya menampilkan citra Kelas A. | **Ada**: Menyertakan 3 citra pembanding relevan (Kelas B, C, D) dari repository nyata dengan visual sebanding. |
| **Sistem Isyarat** | SIBI dan ASL digabung; diasumsikan sebagai "non-BISINDO". | **Dipisahkan tuntas**: Modul independen untuk BISINDO, SIBI, ASL, dan International Sign dengan pertanyaan netral. |
| **Pertanyaan Telapak Terbuka** | Asumsi pasti bukan huruf A; menyodorkan opsi angka 5 / sapaan. | **Terbuka & Netral**: Menanyakan makna dan fungsi apa pun yang dipahami validator tanpa contoh menggiring. |
| **Format Pencatatan Respon** | Kolom jawaban tunggal bercampur. | **Kolom Terpisah**: `Blind Interpretation` (Tahap 1) dan `Post-Disclosure Assessment` (Tahap 2) terpisah tegas. |
| **Alasan & Bukti** | Hanya ada catatan variasi umum. | **Sub-kolom Wajib**: Kolom *Alasan & Argumen* serta kolom *Bukti/Rujukan yang Mendasari* di setiap pertanyaan. |
| **Kualifikasi Validator** | Sangat menekankan sertifikat formal. | **Inklusif & Realistis**: Pengalaman hidup penutur asli Tuli dan keaktifan komunitas diakui setara tanpa wajib sertifikat. |
| **Jumlah Validator** | Tidak ada aturan jika n=1 atau n>1. | **Protokol Multi-Validator**: Rekomendasi n≥2; jika n=1 dibatasi sebagai studi pendahuluan non-nasional. |
| **Pilihan Keputusan (Verdict)** | Opsi biner terbatas (Sah vs Ditolak). | **5 Kategori Terstandar**: Mencakup keterbatasan dialek, tinjauan lintas-wilayah, dan kesimpulan inkonklusif. |
| **Etika Informed Consent** | Satu checkbox consent umum. | **Consent Granular**: Persetujuan wawancara, perekaman video, dan anonimitas dipisahkan secara sukarela. |
| **Panduan Lapangan** | Belum ada panduan operasional sesi. | **Diterbitkan**: [`BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md) siap digunakan enumerator. |

---

## 5. PROTOKOL PENYAJIAN CITRA BUTA & PENGUNGKAPAN LABEL

### A. Alur Kerja Pengujian Citra

```
+---------------------------------------------------------------------------------------------------------+
|                                    ALUR PENGUJIAN CITRA DUA TAHAP                                       |
+---------------------------------------------------------------------------------------------------------+
| [ TAHAP 1: BLIND OBSERVATION ]                                                                          |
| 1. Sajikan citra acak tanpa teks label (IMG_BLD_01 s.d. IMG_BLD_07).                                    |
| 2. Ajukan pertanyaan terbuka murni (Apa yang dilihat? Apakah dikenal? Apa maknanya? Konteksnya apa?).  |
| 3. Rekam respon verbatim pada kolom 'Blind Interpretation'.                                             |
| 4. KUNCI RESPON TAHAP 1 (Dilarang diubah/dihapus).                                                      |
|                                                                                                         |
| [ TAHAP 2: LABEL DISCLOSURE ]                                                                           |
| 5. Beritahukan kepada validator bahwa citra tertentu dilabeli sebagai Kelas A pada dataset AI.          |
| 6. Tanyakan tanggapan kritis: Apakah label cocok? Apakah ada perubahan pemikiran? Mengapa?              |
| 7. Rekam respon pada kolom 'Post-Disclosure Assessment'.                                                |
+---------------------------------------------------------------------------------------------------------+
```

### B. Daftar Citra Uji Acuan Nyata di Repository

| Kode Uji Anonim | Path Berkas Asli di Repository | Kelas Aktual | Peran Citra dalam Protokol |
|:---:|---|:---:|---|
| `IMG_BLD_01` | `data/raw/image/bisindo_alphabet/A/A _Hitam_Iphone_14Pro.jpg` | **Kelas A** | Sampel target (Latar gelap, resolusi tinggi) |
| `IMG_BLD_02` | `data/raw/image/bisindo_alphabet/B/20240509_182924.jpg` | **Kelas B** | Sampel pembanding / distractor |
| `IMG_BLD_03` | `data/raw/image/bisindo_alphabet/A/A_ Polos Terang_Xiaomi _Note 8 Pro.jpg` | **Kelas A** | Sampel target (Latar terang, pencahayaan merata) |
| `IMG_BLD_04` | `data/raw/image/bisindo_alphabet/C/20240509_183146.jpg` | **Kelas C** | Sampel pembanding / distractor |
| `IMG_BLD_05` | `data/raw/image/bisindo_alphabet/A/20240509_182656.jpg` | **Kelas A** | Sampel target (Pencahayaan indoor wajar) |
| `IMG_BLD_06` | `data/raw/image/bisindo_alphabet/D/20240509_183310.jpg` | **Kelas D** | Sampel pembanding / distractor |
| `IMG_BLD_07` | `data/raw/image/bisindo_alphabet/A/A_Background Baju (Garis)_Samsung_A53 5G.jpg` | **Kelas A** | Sampel target (Latar baju bertekstur/pola) |

*(Informasi path dan kelas aktual pada tabel di atas **DISEMBUNYIKAN** dari validator selama Tahap 1 berlangsung)*.

---

## 6. PEMISAHAN KONSEPTUAL EMPAT SISTEM ISYARAT

1. **BISINDO (Bahasa Isyarat Indonesia)**:
   Bahasa alami yang hidup di kalangan komunitas Tuli Indonesia. Ejaan abjad mengadopsi alfabet manual dua tangan (pengaruh historis keluarga BANZSL) untuk sebagian besar huruf vokal dan beberapa konsonan. Eksplorasi difokuskan pada praktik nyata di komunitas lokal validator.
2. **SIBI (Sistem Isyarat Bahasa Indonesia)**:
   Sistem isyarat buatan (*man-made*) yang dibakukan oleh Kementerian Pendidikan untuk pembelajaran di SLB dengan tata bahasa meniru Bahasa Indonesia lisan. Ejaan jari mengadopsi alfabet satu tangan. Eksplorasi difokuskan pada bagaimana validator membedakan fungsi SIBI (di sekolah) dari BISINDO (di komunitas).
3. **ASL (American Sign Language)**:
   Bahasa isyarat alami Amerika Serikat yang memiliki sistem alfabet manual satu tangan. Eksplorasi difokuskan pada kemungkinan adopsi isyarat satu tangan ASL di kalangan generasi muda Tuli, di media sosial, atau saat mengeja kata serapan internasional.
4. **International Sign (IS)**:
   Sistem komunikasi kontak internasional yang fleksibel (*pidgin-like / contact sign*) yang digunakan dalam forum global (WFD, Deaflympics). Eksplorasi difokuskan pada pengalaman internasional validator tanpa menyamakannya dengan ASL.

---

## 7. PROTOKOL MULTI-VALIDATOR & PENGELOLAAN PERBEDAAN PENDAPAT

- **Struktur Evaluasi**: Disarankan melibatkan minimal dua validator (`VAL_BISINDO_01` dan `VAL_BISINDO_02`) dari kelompok komunitas atau daerah yang berbeda.
- **Manajemen Perbedaan Pendapat**:
  - Jika Validator 1 menyatakan bentuk segitiga dua tangan adalah huruf A sah, namun Validator 2 menyatakan bentuk satu tangan lebih lazim di daerahnya, tim **DILARANG** melakukan voting mayoritas untuk memenangkan salah satu pihak.
  - Perbedaan tersebut wajib dicatat sebagai temuan linguistik tentang variasi dialektal regional.
  - Keputusan dialihkan ke kategori **`NEEDS_CROSS_REGIONAL_REVIEW`** atau **`CONFIRMED_WITH_LIMITATIONS`**.
- **Keterbatasan Sesi Validator Tunggal**:
  - Jika hanya satu validator yang berhasil diwawancarai, status keputusan maksimal adalah `CONFIRMED_WITHIN_VALIDATOR_SCOPE`.
  - Dokumen wajib mencantumkan klausul pembatasan: *"Hasil ini mencerminkan variasi komunitas wilayah validator dan belum mencerminkan standar nasional BISINDO secara menyeluruh"*.

---

## 8. KEPATUHAN ETIKA RISET & PERLINDUNGAN PRIVASI

1. **Partisipasi Sukarela**: Validator dapat menolak menjawab pertanyaan tertentu atau membatalkan partisipasi kapan pun tanpa konsekuensi apa pun.
2. **Pemberian Informasi Sebelum Wawancara**: Tujuan penelitian dijelaskan di awal dengan bahasa isyarat yang mudah dipahami.
3. **Persetujuan Granular (Informed Consent)**:
   - Persetujuan wawancara dipisahkan dari persetujuan perekaman audio/video.
   - Penolakan perekaman video tidak membatalkan sesi (notulis beralih ke pencatatan tertulis penuh).
4. **Perlindungan Anonimitas Mutlak**:
   - Nama asli, alamat, dan kontak pribadi disimpan dalam lembar consent fisik terisolasi.
   - Seluruh berkas digital, repository, dan dokumen publik hanya menggunakan kode anonim (misal `VAL_BISINDO_01`).
5. **Integritas Respon**: Dilarang mengubah, menyunting, atau memperhalus jawaban validator agar sesuai dengan hipotesis penelitian.

---

## 9. KERANGKA KEPUTUSAN TIGA DIMENSI & KATEGORI VERDICT

Setiap keputusan kelayakan wajib mempertimbangkan sintesis tiga dimensi:
- **Dimensi 1 (Consistency)**: Apakah 172 citra dataset training konsisten?
- **Dimensi 2 (Linguistic Validity)**: Apakah bentuk tersebut diakui dalam praktik BISINDO nyata oleh validator?
- **Dimensi 3 (Ground Truth Suitability)**: Apakah bentuk tersebut adil dan representatif dijadikan tolok ukur pengujian model AI SignBridge ASEAN?

### Definisi 5 Kategori Keputusan (Verdict):
1. **`CONFIRMED_WITHIN_VALIDATOR_SCOPE`**: Bentuk dua tangan segitiga sah dan layak sebagai ground truth dalam batas wilayah/komunitas validator yang bersangkutan.
2. **`CONFIRMED_WITH_LIMITATIONS`**: Bentuk diakui sah, namun memiliki catatan artikulasi atau variasi minor yang harus diakomodasi model.
3. **`NEEDS_CROSS_REGIONAL_REVIEW`**: Terdapat indikasi variasi regional kuat atau perbedaan antarvalidator; status HOLD tetap berlaku hingga uji silang regional dilakukan.
4. **`REJECTED_WITH_EVIDENCE`**: Bentuk ditolak oleh bukti sosiolinguistik validator; status HOLD tetap berlaku dan tim peneliti mengajukan spesifikasi ulang model.
5. **`INCONCLUSIVE`**: Data wawancara belum memadai untuk menarik kesimpulan; status HOLD tetap berlaku.

---

## 10. AUDIT INTEGRITAS SISTEM & FILE REPOSITORY

Audit integritas memastikan pekerjaan ini hanya menyentuh aspek metodologi dan dokumentasi tanpa mengganggu kode, model, maupun dataset:

### A. SHA-256 Checkpoint Model PyTorch & ONNX (Sebelum vs Sesudah)

| Berkas Model / Artefak Kritis | SHA-256 Sebelum Pekerjaan | SHA-256 Sesudah Pekerjaan | Status Integritas |
|---|---|---|:---:|
| `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% UTUH IDENTIK ✅** |
| `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% UTUH IDENTIK ✅** |
| `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% UTUH IDENTIK ✅** |

### B. Daftar Berkas yang Diubah / Dibuat
1. `docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`: Diperbarui menyeluruh dengan protokol dua tahap, multi-validator, dan pertanyaan netral.
2. `docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`: Dokumen panduan lapangan baru yang siap digunakan pewawancara riset.
3. `docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`: Laporan evaluasi metodologis komprehensif ini.

### C. Daftar Komponen Kritis yang Dilarang Berubah & Terbukti Tidak Berubah
1. Dataset pelatihan mentah (`data/raw/image/bisindo_alphabet/`): **Tidak Berubah (172 citra kelas A utuh)**.
2. Dataset pelatihan terproses (`data/processed/bisindo_alphabet/`): **Tidak Berubah**.
3. Manifest aktual (`data/external/bisindo_validation/external_manifest.csv`): **Tidak Berubah (0 baris data fiktif)**.
4. Direktori data eksternal (`data/external/bisindo_validation/A/`): **Tidak Berubah (0 citra)**.
5. Kode pipeline evaluasi (`scripts/validation_p1/`): **Tidak Berubah**.
6. Checkpoint model & ONNX: **Tidak Berubah**.
7. Backend, frontend, database PostgreSQL, konfigurasi Docker: **Tidak Berubah**.

### D. Integritas Git Status
- Status `git status --short`: Tidak ada file terlacak (*tracked files*) yang dimodifikasi. Seluruh perubahan lokal terjaga aman.
- Tidak ada eksekusi perintah destruktif (`git clean`, `git reset`, `git checkout`).

---

## 11. KETERBATASAN METODOLOGIS YANG BELUM DAPAT DISELESAIKAN

Tim multidisiplin secara jujur mencatat keterbatasan metodologis yang masih ada:
1. **Belum Dilaksanakannya Sesi Wawancara Nyata**: Penyempurnaan instrumen ini baru berada pada tahap kesiapan metodologis (*methodological readiness*). Validitas empiris baru akan tercapai setelah sesi lapangan bersama partisipan Tuli diselenggarakan secara faktual.
2. **Keterbatasan Cakupan Korpus Nasional**: Penelitian ini belum memiliki sumber daya untuk menyelenggarakan studi korpus dialektal di seluruh 38 provinsi di Indonesia. Hasil verifikasi awal akan dibatasi pada lingkup dialek validator yang direkrut.
3. **Keterbatasan Modalitas Citra Statis**: Dataset I1-P1 berbasis citra statis 2D (*single frame RGB*), sehingga variasi transisi gerak dinamis saat penutur membentuk segitiga belum terekam dalam model ini.

---

## 12. STATUS OPERASIONAL AKHIR (FINAL OPERATIONAL STATUS)

Berdasarkan bukti aktual di repository:

| Entitas Evaluasi | Status Operasional Resmi | Keterangan |
|---|:---:|---|
| **Penyempurnaan Metodologi Dokumen** | **`DOCUMENT_REVISION_COMPLETE` ✅** | Seluruh 8 revisi struktural telah diterapkan tuntas pada instrumen dan panduan lapangan. |
| **Status Instrumen Verifikasi** | **`PENDING_VALIDATOR` ⏳** | Instrumen siap pakai, seluruh kolom isian respon tetap 100% kosong (*unfilled*), menunggu pelaksanaan sesi nyata. |
| **Status Tahap Pilot Lapangan** | **`PILOT_HOLD` 🚫** | Pengambilan fisik 10 foto kelas A penutur EXT_S01 **TIDAK DIIZINKAN** sampai sesi nyata selesai dan ditinjau ulang (*re-examination*). |
| **Progres Pengumpulan Data Eksternal** | **`NOT STARTED` ⚪** | Capaian valid: **0 / 780 foto (0.00%)**, defisit pilot: 10 foto, defisit total: 780 foto. |

