# PANDUAN PENILAIAN VALIDATOR BISINDO (INDEPENDENT VALIDATOR BRIEF)
## Proyek Riset SignBridge ASEAN — Modul Image I1 (Alfabet Jari BISINDO A–Z)
### Panduan Ramah Tuli & Petunjuk Operasional Evaluasi Kualitas Visual Gestur (Phase 2C.8 Standard)

---

### SALAM DAN PENGANTAR

Halo Rekan Validator BISINDO,

Terima kasih sebesar-besarnya atas kesediaan Anda meluangkan waktu dan keahlian linguistik bahasa isyarat untuk mendukung riset **SignBridge ASEAN** (*Multimodal Classroom Bridge*). 

Tujuan evaluasi ini adalah untuk **menilai keabsahan linguistik dan keterbacaan visual 36 foto isyarat alfabet BISINDO** secara murni dan objektif. Kami ingin memastikan bahwa sistem kecerdasan buatan (*AI*) yang dikembangkan benar-benar belajar dari peragaan bahasa isyarat yang sah, wajar, dan sesuai dengan kaidah komunikasi komunitas Tuli di Indonesia.

---

### METODOLOGI PENILAIAN BUTA (BLINDED_VALIDATOR_REVIEW)

Evaluasi ini menggunakan metodologi **BLINDED_VALIDATOR_REVIEW** (Penilaian Buta Mandiri).

> **Pernyataan Metodologi Resmi**:
> Penilaian dilakukan secara independen dan blinded. Validator tidak diberi tahu label asli, prediksi model, maupun skor model. Tim peneliti tetap menyimpan mapping internal untuk keperluan audit dan adjudikasi.

1. **Mandiri & Terpisah**: Anda diminta menilai seluruh sampel secara mandiri tanpa berdiskusi, berkonsultasi, atau membandingkan isian dengan validator lain.
2. **Tanpa Petunjuk & Tanpa Pengaruh AI**: Anda tidak diberitahu tebakan komputer, tingkat keyakinan model, maupun label awal berkas. Penilaian Anda murni didasarkan pada pengetahuan alami BISINDO dan bukti visual yang terlihat.
3. **Objektivitas Visual**: Nilailah gestur berdasarkan apa yang nyata terlihat pada foto. Jangan menebak apa yang kira-kira ingin diperagakan jika bentuk jarinya tidak terlihat jelas atau terpotong.

---

### PARADIGMA PENILAIAN: IDENTIFIKASI HURUF BUTA (BLIND LETTER IDENTIFICATION)

Berbeda dari model evaluasi lama yang menanyakan apakah foto "Benar" atau "Salah" terhadap suatu kunci jawaban yang disembunyikan, pada paradigma **Blind Letter Identification** ini tugas Anda sangat intuitif dan alamiah:

1. **Tentukan Huruf yang Diperagakan (`identified_letter`)**:
   - Huruf alfabet apa (A sampai Z) yang diperagakan oleh gestur tangan pada foto tersebut?
   - Ketikkan satu huruf kapital (A–Z) yang Anda kenali. Jika gestur tidak terbaca sama sekali atau rusak total, kosongkan kolom ini.
2. **Tentukan Tingkat Kejelasan Gestur (`decision`)**:
   - Pilih satu dari tiga kategori kejelasan gestur (lihat tabel panduan di bawah).
3. **Tandai Variasi Daerah (`regional_variation`)**:
   - Apakah gestur ini merupakan ragam/dialek daerah tertentu? (`YES`, `NO`, atau `UNSURE`).
4. **Catatan Tambahan (`notes`)**:
   - Tuliskan alasan singkat jika isyarat ambigu, terpotong, atau jika ada ragam daerah tertentu (misal: "Variasi Yogyakarta", "Mirip huruf V", "Jari kelingking terpotong").

---

### DEFINISI OPERASIONAL TIGA KATEGORI KEJELASAN (`decision`)

Untuk setiap foto stimulus (`VAL-REV-001` s/d `VAL-REV-036`), pilih **SATU** kategori keputusan:

| Pilihan Kejelasan | Kode Resmi | Kapan Harus Memilih Opsi Ini? | Pengisian Kolom Huruf |
| :--- | :---: | :--- | :--- |
| **[1] Jelas Teridentifikasi** | `IDENTIFIED` | Konfigurasi jari, orientasi telapak tangan, dan bentuk gestur **sah, jelas, wajar, dan pasti** membentuk satu huruf alfabet BISINDO. | **Wajib mengisi** kolom `identified_letter` dengan satu huruf (A–Z). |
| **[2] Ambigu / Samar** | `AMBIGUOUS` | Konfigurasi jari meragukan, **berada di antara dua bentuk huruf**, sudut kamera membuat pose sulit dibedakan, atau pose bisa diartikan sebagai dua huruf berbeda. | Boleh mengisi dugaan huruf terdekat atau dikosongkan jika ragu. Dianjurkan menulis catatan di kolom `notes`. |
| **[3] Tak Tentu / Rusak** | `UNDETERMINABLE` | **Kualitas visual tidak memungkinkan pembacaan**: foto terlalu gelap, silau ekstrem, kabur total (*heavy blur*), atau jari-jari kunci terpotong di tepi foto (*border clipping*). | Kolom `identified_letter` dikosongkan. Tuliskan kondisi kerusakan pada kolom `notes`. |

---

### PILIHAN VARIASI REGIONAL / DIALEK DAERAH (`regional_variation`)

Komunitas Tuli di berbagai wilayah Indonesia memiliki kekayaan dialek lokal. Tandai kolom variasi regional sebagai berikut:
- **`YES`**: Isyarat ini menggunakan bentuk dialek lokal/daerah (misal ragam Jakarta, Yogyakarta, Jawa Timur, Bali, dll.). Tuliskan nama daerahnya pada kolom `notes`.
- **`NO`**: Isyarat ini menggunakan bentuk fingerspelling standar umum / nasional.
- **`UNSURE`**: Anda tidak yakin apakah perbedaan pose disebabkan dialek daerah atau gaya peraga pribadi.

---

### PERHATIAN KHUSUS UNTUK HURUF J DAN Z (GERAKAN VS FOTO DIAM)

Dalam BISINDO, huruf **J** dan **Z** sejatinya menggunakan gerakan dinamis di udara (lintasan gerak melengkung untuk J, dan goresan huruf Z di udara).

Aturan metodologis penilaian pada foto diam (statis):
1. **Stimulus Foto Statis**: Penilaian menggunakan stimulus foto diam (*single static frame*).
2. **Makna Kategori IDENTIFIED**: Keputusan `IDENTIFIED` pada huruf J atau Z hanya menunjukkan bahwa pose statis tersebut sudah lumrah dan dapat dikenali bentuk awalnya oleh validator sebagai representasi huruf tersebut.
3. **Batas Pengujian Statis**: Penilaian foto statis **tidak membuktikan ketepatan lintasan gerakan dinamis**.
4. **Fleksibilitas Ambigu / Tak Tentu**: Jika pose diam tersebut meragukan, kurang informatif, atau membingungkan karena persis seperti huruf lain (misalnya pose J diam mirip I, atau pose Z diam mirip D), validator **sangat dianjurkan memilih `AMBIGUOUS` atau `UNDETERMINABLE`** sesuai bukti visual yang nyata.
5. **Jangan Memaksakan Pilihan**: Jangan memaksakan memilih `IDENTIFIED` jika bukti visual tidak memadai tanpa gerakan.

---

### PRINSIP PENILAIAN LINGUISTIK: BUKAN KONTES FOTOGRAFI

Fokus utama penilaian adalah **keabsahan konfigurasi tangan (*handshape*) dan keterbacaan bahasa isyarat**:
- **Abaikan Faktor Sekunder**: Abaikan warna dinding latar belakang, pakaian peraga, atau warna kulit peraga.
- **Fokus Konfigurasi Jari**: Periksa apakah jempol, telunjuk, tengah, manis, dan kelingking terbuka/tertutup/bersilang sesuai kaidah huruf.
- **Kecukupan Bukti Visual**: Jika jari penting terpotong di luar bingkai foto sehingga Anda harus "menebak", jangan menebak! Pilihlah `UNDETERMINABLE`.

---

### PILIHAN INSTRUMEN PENILAIAN (DUA PILIHAN PRAKTIS)

Anda dapat memilih media yang paling nyaman untuk Anda gunakan:

#### Pilihan 1: Buku Kerja Excel Interaktif (Sangat Direkomendasikan)
Gunakan berkas Excel resmi yang telah disiapkan di dalam paket:
- Validator A: `VALIDATOR_A_WORKBOOK.xlsx`
- Validator B: `VALIDATOR_B_WORKBOOK.xlsx`

**Keunggulan & Fitur Buku Kerja Excel**:
1. **Sheet 1: Panduan & Petunjuk**: Berisi ringkasan panduan penilaian ramah Tuli.
2. **Sheet 2: Lembar Penilaian**:
   - Memuat pratinjau gambar stimulus (96x96 piksel) langsung di samping baris isian sehingga Anda tidak perlu repot berpindah-pindah jendela aplikasi.
   - Menu Dropdown (*Data Validation*) untuk memudahkan memilih:
     - Huruf Teridentifikasi (A–Z atau kosong)
     - Kejelasan Isyarat (`IDENTIFIED`, `AMBIGUOUS`, `UNDETERMINABLE`)
     - Variasi Regional (`YES`, `NO`, `UNSURE`)
   - Baris judul tetap beku (*frozen header*) saat digulir ke bawah.
3. **Sheet 3: Ringkasan Progres**:
   - Menghitung persentase progres penyelesaian 36 sampel secara otomatis secara *real-time*.
   - Menampilkan ringkasan distribusi kategori keputusan dan variasi regional.

#### Pilihan 2: Berkas CSV Standar & Foto Resolusi Tinggi
Jika Anda lebih terbiasa menggunakan spreadsheet CSV:
1. Buka formulir CSV:
   - Validator A: `VALIDATOR_A_RESPONSE_TEMPLATE.csv`
   - Validator B: `VALIDATOR_B_RESPONSE_TEMPLATE.csv`
2. Buka foto beresolusi penuh dari folder `stimulus_images/` (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
3. Isi kolom `identified_letter`, `decision`, `regional_variation`, `notes`, dan `review_date`.
4. Simpan berkas CSV dengan enkoding UTF-8.

*(Catatan: Lembar cetak fisik atau Markdown `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` juga tersedia sebagai opsi alternatif bagi validator yang memilih pengisian dokumen terpisah).*

---

### PROSEDUR PENERIMAAN DATA & PENJAMINAN INTEGRITAS ASLI

Setelah berkas pengisian (baik `.xlsx` maupun `.csv`) diserahkan kepada fasilitator riset:
1. Fasilitator akan **seketika menghitung nilai hash kriptografis SHA-256** dari berkas yang Anda serahkan sebelum berkas dibuka.
2. Berkas asli Anda disimpan ke dalam arsip mentah permanen (*raw immutable repository*) dengan atribut baca-saja (*read-only*).
3. Tim peneliti tidak akan pernah mengubah atau memanipulasi penilaian yang telah Anda berikan. Seluruh analisis statistik reliabilitas inter-rater akan membaca data asli Anda secara transparan dan terverifikasi.

Jika ada pertanyaan, kendala visual, atau kebutuhan klarifikasi teknis, fasilitator pendamping siap membantu Anda.

Terima kasih atas dedikasi dan kontribusi berharga Anda dalam memajukan aksesibilitas dan inklusi digital bagi komunitas Tuli!
