# Panduan Kontribusi Data — SignBridge BISINDO

Terima kasih atas minat Anda untuk berkontribusi pada dataset WL-BISINDO!
Kontribusi data dari signer baru sangat membantu meningkatkan keterwakilan komunitas Tuli Indonesia
dan kualitas model pengenalan bahasa isyarat.

---

## Daftar Isi

1. [Siapa yang Dapat Berkontribusi?](#1-siapa-yang-dapat-berkontribusi)
2. [Persiapan Sebelum Merekam](#2-persiapan-sebelum-merekam)
3. [Proses Persetujuan Data (Consent Form)](#3-proses-persetujuan-data-consent-form)
4. [Cara Merekam Data](#4-cara-merekam-data)
5. [Persyaratan Teknis Video](#5-persyaratan-teknis-video)
6. [Cara Mengirim Kontribusi](#6-cara-mengirim-kontribusi)
7. [Proses Validasi](#7-proses-validasi)
8. [Pertanyaan Umum](#8-pertanyaan-umum)
9. [Kontak](#9-kontak)

---

## 1. Siapa yang Dapat Berkontribusi?

Kami menerima kontribusi dari:

- **Anggota komunitas Tuli Indonesia** yang menggunakan BISINDO sebagai bahasa utama.
- **Juru bahasa isyarat** yang bersertifikat atau berpengalaman dalam BISINDO.
- **Guru SLB (Sekolah Luar Biasa)** dengan penguasaan BISINDO yang terverifikasi.
- **Peneliti** atau mahasiswa dengan persetujuan dari lembaga masing-masing.

**Penting:** Kontributor harus berusia minimal 18 tahun atau memiliki izin dari wali/orang tua.

---

## 2. Persiapan Sebelum Merekam

Sebelum memulai sesi perekaman, pastikan Anda telah:

1. Membaca dan memahami panduan ini secara lengkap.
2. Menyiapkan perangkat dengan webcam yang berfungsi (minimal 640×480 piksel, 30 FPS).
3. Memilih lokasi dengan pencahayaan yang cukup dan latar belakang yang tidak terlalu ramai.
4. Mengenakan pakaian yang kontras dengan latar belakang (hindari pakaian dengan banyak pola).
5. Memastikan ruangan cukup terang — cahaya dari depan lebih baik daripada dari belakang.
6. Membaca dan menandatangani **consent form** (lihat Bagian 3).

---

## 3. Proses Persetujuan Data (Consent Form)

Sebelum data Anda dapat direkam dan digunakan, Anda **wajib** menandatangani consent form.

### Isi Consent Form

Dengan menandatangani consent form, Anda menyatakan bahwa:

- Anda memberikan izin penggunaan video rekaman Anda untuk keperluan **penelitian ilmiah** bahasa isyarat Indonesia.
- Data Anda akan dirilis di bawah lisensi **Creative Commons CC BY 4.0** — dapat digunakan bebas dengan atribusi.
- Identitas Anda akan **dianonimkan** — hanya ID anonim (mis. `S006`) yang disimpan, bukan nama asli.
- Anda dapat **menarik persetujuan** kapan saja sebelum dataset dirilis publik dengan menghubungi tim peneliti.
- Anda memahami bahwa wajah Anda akan terlihat dalam video dan tidak akan diblur.

### Cara Mendapatkan Consent Form

Jalankan skrip perekaman — consent form akan ditampilkan dan harus ditandatangani secara digital
**sebelum** sesi perekaman dimulai:

```bash
python scripts/record_dataset.py --signer-id S006 --output-dir data/wl-bisindo/raw
```

Sertifikat persetujuan dalam format PDF akan dibuat secara otomatis setelah penandatanganan.

---

## 4. Cara Merekam Data

### 4.1 Menggunakan Skrip Perekaman

```bash
python scripts/record_dataset.py \
  --gloss MAKAN \
  --signer-id S006 \
  --output-dir data/wl-bisindo/raw \
  --fps 30 \
  --resolution 640x480
```

**Parameter:**

| Parameter | Keterangan | Default |
|---|---|---|
| `--gloss` | Gloss yang akan direkam | Wajib |
| `--signer-id` | ID signer Anda (dapatkan dari tim peneliti) | Wajib |
| `--output-dir` | Direktori output video | `data/wl-bisindo/raw` |
| `--fps` | Frame rate perekaman | `30` |
| `--resolution` | Resolusi video (minimum 640×480) | `640x480` |

### 4.2 Alur Perekaman

1. Skrip akan menampilkan instruksi gloss dalam **Bahasa Indonesia** di layar.
2. Pastikan posisi tubuh Anda benar sesuai panduan di layar.
3. Hitung mundur **3 detik** akan ditampilkan sebelum perekaman dimulai.
4. Lakukan tanda isyarat untuk gloss tersebut selama **2–5 detik**.
5. Skrip akan menyimpan video secara otomatis.
6. Ulangi untuk setiap gloss yang ingin Anda rekam.

### 4.3 Panduan Posisi Tubuh

- Posisikan tubuh Anda **menghadap kamera** secara langsung.
- Pastikan **kedua tangan dan tubuh bagian atas** terlihat penuh dalam frame.
- Jaga **jarak 50–100 cm** dari kamera.
- Hindari gerakan kamera atau badan yang tidak perlu selama perekaman.

---

## 5. Persyaratan Teknis Video

Untuk memastikan video dapat diterima dalam proses validasi:

| Persyaratan | Nilai Minimum |
|---|---|
| Format | MP4 atau AVI |
| Resolusi | 480p (640×480) atau lebih tinggi |
| Frame Rate | 25 FPS atau lebih tinggi |
| Durasi per Klip | 1–10 detik |
| Deteksi Keypoint | MediaPipe harus dapat mengekstrak 543 keypoint |

**Video akan ditolak secara otomatis jika:**
- Format bukan MP4 atau AVI
- Resolusi di bawah 480p
- FPS di bawah 25
- Durasi kurang dari 1 detik atau lebih dari 10 detik
- MediaPipe tidak dapat mendeteksi keypoint pada mayoritas frame

---

## 6. Cara Mengirim Kontribusi

### Opsi A: Melalui Skrip (Direkomendasikan)

Skrip `record_dataset.py` secara otomatis menyimpan video ke struktur direktori yang benar
dan memasukkannya ke split `train`.

### Opsi B: Upload Manual

Jika Anda merekam video sendiri dan ingin mengirimkannya:

1. Pastikan video memenuhi persyaratan teknis di Bagian 5.
2. Namai file dengan format: `<SIGNER_ID>_<GLOSS>_<NOMOR>.mp4`
   - Contoh: `S006_MAKAN_001.mp4`
3. Kirim file ke alamat email tim peneliti (lihat Bagian 9).
4. Sertakan consent form yang telah ditandatangani.

### Struktur Direktori yang Diharapkan

```
data/wl-bisindo/raw/
└── <GLOSS>/
    └── <SIGNER_ID>_<GLOSS>_<NOMOR>.mp4
```

Contoh:
```
data/wl-bisindo/raw/
└── MAKAN/
    ├── S001_MAKAN_001.mp4
    ├── S001_MAKAN_002.mp4
    └── S006_MAKAN_001.mp4   ← kontribusi baru
```

---

## 7. Proses Validasi

Setelah video diterima, tim peneliti akan menjalankan validasi otomatis:

1. **Validasi format** — cek format, resolusi, FPS, dan durasi.
2. **Validasi keypoint** — cek apakah MediaPipe dapat mengekstrak 543 keypoint.
3. **Tinjauan manual** — peneliti memeriksa kualitas isyarat secara visual.
4. **Notifikasi** — Anda akan mendapat konfirmasi penerimaan atau laporan penolakan
   beserta alasan spesifik.

Video yang ditolak tidak akan memengaruhi dataset utama yang sudah ada.

---

## 8. Pertanyaan Umum

**Apakah data saya akan digunakan secara komersial?**
Data dirilis di bawah CC BY 4.0 yang memungkinkan penggunaan komersial oleh pihak ketiga
selama atribusi diberikan. Jika Anda tidak setuju, jangan mengirim kontribusi.

**Apakah wajah saya akan muncul di dataset publik?**
Ya, wajah terlihat dalam video karena diperlukan untuk ekstraksi keypoint wajah MediaPipe.
Identitas Anda dianonimkan menggunakan ID signer.

**Berapa banyak gloss yang harus saya rekam?**
Idealnya semua 32 gloss, tetapi kontribusi parsial (misalnya 10 gloss) juga diterima.

**Apakah saya mendapat kredit atas kontribusi?**
Ya — dataset akan mencantumkan jumlah signer dalam metadata, dan kontribusi Anda diakui
dalam makalah penelitian (tanpa menyebut nama asli jika Anda memilih anonim).

**Bagaimana jika webcam saya tidak berfungsi?**
Skrip akan menampilkan pesan error dalam Bahasa Indonesia. Pastikan webcam terhubung dan
izin kamera telah diberikan ke aplikasi/browser.

---

## 9. Kontak

Untuk pertanyaan, masalah teknis, atau penarikan persetujuan:

- **Email:** *(sesuaikan dengan email peneliti)*
- **GitHub Issues:** <https://github.com/signbridge/signbridge-bisindo/issues>
- **Hugging Face:** <https://huggingface.co/datasets/signbridge/wl-bisindo-extended>

---

*Terima kasih atas kontribusi Anda untuk kemajuan teknologi aksesibilitas bahasa isyarat Indonesia!*
*— Tim Peneliti SignBridge*
