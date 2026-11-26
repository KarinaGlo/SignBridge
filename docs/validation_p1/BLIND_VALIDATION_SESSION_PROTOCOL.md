# PANDUAN LAPANGAN PELAKSANAAN SESI VALIDASI BUTA
## Blind Validation Session Protocol — Gestur BISINDO Kelas A
### Proyek: SignBridge ASEAN | Modality Image I1-P1

**Dokumen**: `docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`  
**Sasaran Pengguna**: Pewawancara Riset, Juru Bahasa Isyarat (JBI) Pendamping, Notulis Data  
**Dokumen Instrumen Acuan**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)  
**Tanggal Penerbitan**: 16 November 2026  
**Status Protokol**: **`READY FOR FIELD OPERATION (PENDING VALIDATOR RECRUITMENT)`**  

---

## 1. TUJUAN & PRINSIP DASAR SESI

Protokol ini disusun untuk memastikan bahwa wawancara verifikasi gestur bersama penutur asli Tuli atau instruktur BISINDO berjalan **terstandar, etis, netral, dan sepenuhnya bebas dari bias konfirmasi (*free of confirmation bias*)**.

### Prinsip Utama Pewawancara:
1. **Dilarang Menggiring (*Zero Leading*)**: Jangan pernah menyebutkan huruf, nama sistem, atau bentuk (misal: *"Ini huruf A kan?"*, *"Apakah ini segitiga?"*, *"Bukan SIBI kan?"*) sebelum validator memberikan interpretasi murninya.
2. **Hormati Budaya & Kenyamanan Bahasa**: Gunakan bahasa isyarat yang alami dan nyaman bagi validator. Libatkan Juru Bahasa Isyarat (JBI) bersertifikat atau fasilitator Tuli jika pewawancara bukan penutur fasih.
3. **Keterpisahan Dua Tahap**: Informasi label kelas dataset **HARAM DIBERIKAN** sebelum seluruh respon pada Tahap 1 (Blind Observation) selesai dicatat dan dikunci.
4. **Pencatatan Objektif**: Catat keraguan, jeda berpikir, atau ekspresi wajah yang relevan secara jujur. Jangan memaksakan keseragaman jawaban.

---

## 2. PERSIAPAN SEBELUM SESI (PRE-SESSION CHECKLIST)

Sebelum validator hadir, tim wajib memastikan:
- [ ] Formulir verifikasi fisik atau formulir digital [`BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md) telah disiapkan dalam kondisi kosong.
- [ ] Lembar penjelasan penelitian dan lembar *Informed Consent* cetak tersedia.
- [ ] Kartu peraga visual atau slide presentasi gambar telah disiapkan dengan ketentuan:
  - **Nama file asli disembunyikan** (nama file seperti `A _Hitam_Iphone_14Pro.jpg` diganti menjadi kode acak seperti `IMG_BLD_01`).
  - **Label kelas dihilangkan**.
  - **Urutan kemunculan telah diacak** (mencakup 4 sampel Kelas A dan 3 sampel pembanding Kelas B, C, D).
- [ ] Perangkat pencatatan / perekaman (kamera cadangan, alat tulis, laptop) telah diuji coba.

---

## 3. LANGKAH-LANGKAH PELAKSANAAN SESI (STEP-BY-STEP WORKFLOW)

```
+---------------------------------------------------------------------------------------------------+
|                                  ALUR KERJA SESI VALIDASI BUTA                                    |
+---------------------------------------------------------------------------------------------------+
| 1. Sambutan & Informed Consent -> Penjelasan etika, hak sukarela, penandatanganan consent         |
| 2. Tahap 1: Blind Observation   -> Peraga citra tanpa label acak, pertanyaan terbuka bebas bias   |
| 3. Penguncian Catatan Tahap 1  -> Verifikasi catatan awal sebelum label diungkapkan              |
| 4. Tahap 2: Label Disclosure    -> Pengungkapan label dataset, evaluasi kritis & perubahan respon |
| 5. Tahap 3: Pendalaman Sosio-Ling-> Eksplorasi BISINDO daerah, SIBI SLB, ASL medsos, telapak 5    |
| 6. Tahap 4: Ground Truth Review -> Rekomendasi kelayakan untuk machine learning SignBridge ASEAN  |
| 7. Penutupan & Arsip Dokumen   -> Verifikasi paraf, pemberian kompensasi etis, arsip aman         |
+---------------------------------------------------------------------------------------------------+
```

### Langkah 1: Penyambutan, Bina Suasana, & Informed Consent
1. Sambut partisipan dengan ramah dan penuh rasa hormat.
2. Jelaskan tujuan umum riset:
   > *"SignBridge ASEAN sedang meneliti pengenalan bahasa isyarat menggunakan kecerdasan buatan untuk membantu komunikasi. Kami ingin belajar dari pengalaman isyarat Anda mengenai bentuk-bentuk tangan yang ada di dalam kumpulan data kami."*
3. Tegaskan bahwa partisipasi bersifat sukarela, tidak ada jawaban "benar" atau "salah", dan validator berhak menolak menjawab atau menghentikan sesi sewaktu-waktu.
4. Minta validator membaca (atau diterjemahkan oleh JBI) lembar persetujuan (*informed consent*).
5. Catat status persetujuan (`CONSENT_SIGNED`) setelah lembar ditandatangani.

---

### Langkah 2: Tahap 1 — Pengamatan Buta (Blind Observation)
Tampilkan kartu gambar atau slide satu per satu secara berurutan sesuai urutan acak (`IMG_BLD_01` s.d. `IMG_BLD_07`).

Untuk setiap gambar yang ditampilkan, ajukan rangkaian pertanyaan terbuka berikut:
1. *"Apa yang Anda amati dari gambar tangan ini?"*
2. *"Apakah bentuk tangan seperti ini pernah Anda lihat atau Anda gunakan dalam komunikasi sehari-hari?"*
3. *"Jika pernah, apa makna, huruf, angka, atau isyarat yang Anda pahami dari bentuk ini?"*
4. *"Biasanya bentuk ini digunakan dalam konteks apa atau dengan siapa?"*
5. *"Seberapa yakin Anda dengan penjelasan ini? Apakah ada alasan atau rujukan tertentu?"*

> [!CAUTION]
> **ATURAN KETAT TAHAP 1**:
> - Jangan memberikan koreksi atau tanggapan seperti *"Salah"*, *"Benar"*, *"Bagus"*, atau *"Itu huruf A lho"*.
> - Jika validator tampak ragu, tanyakan: *"Bagian mana yang membuat Anda ragu? Apakah ada detail jari yang kurang jelas?"*
> - Notulis wajib mencatat respon secara verbatim (kata demi kata) pada kolom `Blind Interpretation`.

---

### Langkah 3: Penguncian Respon Tahap 1
Sebelum beralih ke Tahap 2, pastikan seluruh respon untuk ketujuh citra telah dicatat lengkap. Berikan jeda singkat 2 menit.

---

### Langkah 4: Tahap 2 — Pengungkapan Label Dataset (Label Disclosure)
Pewawancara menjelaskan kepada validator:
> *"Terima kasih atas penjelasan bebas Anda. Sekarang, kami ingin berbagi informasi mengenai bagaimana gambar-gambar ini dilabeli di dalam komputer kami. Komputer kami sedang dilatih menggunakan data ini, di mana beberapa gambar dilabeli sebagai huruf 'A'."*

Tunjukkan kembali masing-masing gambar Kelas A (`IMG_BLD_01`, `IMG_BLD_03`, `IMG_BLD_05`, `IMG_BLD_07`) dan sampaikan:
> *"Di dalam data komputer kami, gambar ini diberi label huruf 'A'."*

Ajukan pertanyaan evaluasi pasca-pengungkapan:
1. *"Setelah mengetahui bahwa gambar ini dilabeli sebagai huruf 'A', bagaimana tanggapan Anda? Apakah menurut Anda label ini cocok dan tepat?"*
2. *"Apakah ada perubahan dari penjelasan Anda tadi sebelum mengetahui label ini? Jika ada, apa yang membuat pandangan Anda berubah?"*

Catat seluruh respon pada kolom `Post-Disclosure Assessment` tanpa menghapus catatan Tahap 1.

---

### Langkah 5: Tahap 3 — Pendalaman Sosio-Linguistik & Sistem Isyarat
Lanjutkan dengan eksplorasi kualitatif mendalam:
1. **Konteks BISINDO**:
   - *"Bagaimana huruf A biasanya dieja di kota/daerah tempat tinggal Anda?"*
   - *"Apakah teman-teman Tuli di daerah lain (misalnya Jawa, Bali, Sumatra, dll.) menggunakan bentuk yang sama atau berbeda?"*
   - *"Apakah ada perbedaan antara generasi Tuli senior dan generasi muda?"*
2. **Konteks SIBI**:
   - *"Apakah Anda mengenal bentuk satu tangan mengepal dari SIBI atau pelajaran di SLB? Dalam situasi apa bentuk itu biasanya muncul?"*
3. **Konteks ASL & International Sign**:
   - *"Apakah di komunitas Anda ada yang memakai ejaan satu tangan ASL, misalnya saat mengeja istilah bahasa Inggris atau di media sosial?"*
   - *"Bagaimana dengan isyarat internasional (International Sign) yang dipakai di acara luar negeri?"*
4. **Konteks Telapak Tangan Terbuka**:
   - Tunjukkan atau peragakan telapak tangan terbuka 5 jari merenggang tegak: *"Jika ada orang memperagakan bentuk tangan seperti ini, apa artinya dalam percakapan isyarat yang biasa Anda gunakan? Pernahkah bentuk ini dipakai untuk mengeja huruf?"*

---

### Langkah 6: Tahap 4 — Penilaian Kelayakan Ground Truth Penelitian
Diskusikan aspek rekayasa sistem dengan validator:
1. *"Proyek SignBridge ASEAN ingin menguji komputer ini pada penutur baru (EXT_S01) dengan 10 foto. Menurut Anda, apakah adil dan tepat jika komputer mengharapkan penutur baru membentuk huruf A seperti gambar dua tangan segitiga ini?"*
2. *"Apa pesan atau saran penting dari Anda agar sistem kecerdasan buatan ini tidak keliru memahami budaya Tuli?"*

---

### Langkah 7: Penutupan Sesi & Pengarsipan Data
1. Ucapkan terima kasih yang tulus atas kontribusi berharga validator bagi riset aksesibilitas.
2. Berikan kompensasi waktu/transportasi sesuai standar etika riset.
3. Notulis dan pewawancara memeriksa kembali kelengkapan formulir.
4. Lembar instrumen ditandatangani/diparaf oleh penanggung jawab sesi.
5. Berkas fisik disimpan di arsip aman, dan data digital disalin ke repository sesuai protokol anonimitas.

---

## 4. PENANGANAN KONDISI KHUSUS (EDGE CASES)

| Skenario Lapangan | Tindakan yang Harus Diambil |
|---|---|
| **Validator bingung melihat gambar karena sudut/pencahayaan** | Catat sebagai catatan kualitas citra. Jangan mengarahkan atau menebakkan bentuk tangan. |
| **Validator menyatakan bentuk segitiga bukan huruf A** | Terima jawaban dengan hormat, catat alasan lengkap dan alternatif bentuk huruf A yang ditunjukkan validator. Dilarang mendebat! |
| **Dua validator memiliki pendapat yang bertolak belakang** | Catat kedua argumen secara lengkap. Jangan mencoba mendamaikan atau meminta salah satu pihak mengalah. Klasifikasikan sebagai `NEEDS_CROSS_REGIONAL_REVIEW`. |
| **Validator meminta identitasnya dirahasiakan sepenuhnya** | Pastikan kode anonim (`VAL_BISINDO_...`) diterapkan di seluruh berkas publik. Nama asli hanya tersimpan di lembar consent fisik terisolasi. |
| **Validator merasa lelah di tengah sesi** | Berikan waktu istirahat 10–15 menit atau jadwalkan sesi lanjutan jika diperlukan. |

