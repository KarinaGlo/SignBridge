# DATA CARD — WL-BISINDO

> Dokumentasi dataset untuk **WL-BISINDO (Word-Level Bahasa Isyarat Indonesia)** yang digunakan
> dalam penelitian SignBridge.
> Requirement: 1.7

---

## 1. Ringkasan Dataset

| Atribut | Nilai |
|---|---|
| Nama | WL-BISINDO (Word-Level BISINDO) |
| Versi | 1.0 (asli) + SignBridge Extended (penelitian ini) |
| Jumlah Gloss | 32 |
| Jumlah Video | 1.600 (asli) + ≥96 (extended) |
| Sampel per Gloss | 10 per signer |
| Jumlah Signer | 5 (asli) + ≥3 (extended) |
| Format Video | MP4 |
| Resolusi Minimum | 640 × 480 piksel |
| Frame Rate | 30 FPS |
| Durasi per Klip | 2–5 detik |

---

## 2. Sumber dan Publikasi Asli

Dataset WL-BISINDO asli dipublikasikan bersamaan dengan makalah ilmiah berikut:

> **Penulis:** *(sesuaikan dengan nama peneliti WL-BISINDO asli)*
> **Judul:** "WL-BISINDO: A Word-Level Indonesian Sign Language Dataset"
> **Publikasi:** Procedia Computer Science, 2025
> **Platform:** Kaggle — `dataset/wl-bisindo`

Dataset WLASL yang digunakan untuk **pretraining**:

> Li, D., Rodriguez, C., Yu, X., & Li, H. (2020).
> "Word-Level Deep Sign Language Recognition from Video: A New Large-Scale Dataset and
> Methods Comparison."
> *Winter Conference on Applications of Computer Vision (WACV)*.
> Kaggle: `risangbaskoro/wlasl-processed`

---

## 3. Lisensi

| Dataset | Lisensi | Ketentuan Utama |
|---|---|---|
| WL-BISINDO (asli) | **CC BY 4.0** | Atribusi wajib; penggunaan komersial diizinkan |
| WL-BISINDO Extended (penelitian ini) | **CC BY 4.0** | Atribusi wajib; lihat Bagian 7 |
| WLASL | Lisensi Akademik (non-komersial) | Hanya untuk riset; lihat sumber asli |

Teks lisensi lengkap CC BY 4.0: <https://creativecommons.org/licenses/by/4.0/>

---

## 4. Cara Sitasi

### 4.1 Dataset WL-BISINDO Asli

```bibtex
@dataset{wl_bisindo_2025,
  title     = {{WL-BISINDO}: Word-Level Indonesian Sign Language Dataset},
  year      = {2025},
  publisher = {Kaggle},
  url       = {https://www.kaggle.com/datasets/dataset/wl-bisindo},
  license   = {CC BY 4.0}
}
```

### 4.2 Dataset WL-BISINDO Extended (SignBridge)

```bibtex
@dataset{signbridge_wl_bisindo_extended_2025,
  title     = {{WL-BISINDO Extended}: SignBridge Augmented Indonesian Sign Language Dataset},
  author    = {SignBridge Research Team},
  year      = {2025},
  publisher = {Kaggle / Hugging Face Datasets},
  url       = {https://huggingface.co/datasets/signbridge/wl-bisindo-extended},
  license   = {CC BY 4.0}
}
```

### 4.3 Makalah SignBridge

```bibtex
@inproceedings{signbridge2025,
  title     = {{SignBridge}: Two-Stream Cross-Attention Fusion for Real-Time {BISINDO} Recognition},
  author    = {SignBridge Research Team},
  booktitle = {Procedia Computer Science},
  year      = {2025},
  note      = {Submitted}
}
```

---

## 5. Deskripsi Konten Dataset

### 5.1 Daftar 32 Gloss

| No. | Gloss | Kategori |
|---|---|---|
| 1 | MAKAN | Aktivitas Sehari-hari |
| 2 | MINUM | Aktivitas Sehari-hari |
| 3 | TIDUR | Aktivitas Sehari-hari |
| 4 | BERJALAN | Aktivitas Sehari-hari |
| 5 | BERLARI | Aktivitas Sehari-hari |
| 6 | DUDUK | Aktivitas Sehari-hari |
| 7 | BERDIRI | Aktivitas Sehari-hari |
| 8 | MEMBACA | Aktivitas Sehari-hari |
| 9 | MENULIS | Aktivitas Sehari-hari |
| 10 | BELAJAR | Aktivitas Sehari-hari |
| 11 | AKU | Orang & Hubungan Sosial |
| 12 | KAMU | Orang & Hubungan Sosial |
| 13 | DIA | Orang & Hubungan Sosial |
| 14 | IBU | Orang & Hubungan Sosial |
| 15 | BAPAK | Orang & Hubungan Sosial |
| 16 | TEMAN | Orang & Hubungan Sosial |
| 17 | APA | Kata Tanya & Umum |
| 18 | SIAPA | Kata Tanya & Umum |
| 19 | DI_MANA | Kata Tanya & Umum |
| 20 | KAPAN | Kata Tanya & Umum |
| 21 | BAGAIMANA | Kata Tanya & Umum |
| 22 | BERAPA | Kata Tanya & Umum |
| 23 | SENANG | Emosi & Kondisi |
| 24 | SEDIH | Emosi & Kondisi |
| 25 | SAKIT | Emosi & Kondisi |
| 26 | SEHAT | Emosi & Kondisi |
| 27 | RUMAH | Tempat & Objek |
| 28 | SEKOLAH | Tempat & Objek |
| 29 | MASJID | Tempat & Objek |
| 30 | MOBIL | Tempat & Objek |
| 31 | YA | Konsep Dasar |
| 32 | TIDAK | Konsep Dasar |

### 5.2 Profil Signer

- Signer asli: 5 signer (anonim, ID: S001–S005)
- Signer extended: ≥3 signer baru (ID: S006+)
- Variasi: jenis kelamin, usia, latar belakang komunikasi BISINDO
- Persetujuan data: semua signer menandatangani consent form sebelum perekaman

### 5.3 Kondisi Perekaman

- Latar belakang: bervariasi (untuk ketahanan model)
- Pencahayaan: kondisi dalam ruangan yang memadai
- Peralatan: webcam standar (≥640×480, 30 FPS)
- Pakaian: tidak ada pembatasan warna

---

## 6. Struktur Direktori Dataset

```
data/
└── wl-bisindo/
    ├── raw/                          # Video MP4 asli
    │   ├── MAKAN/
    │   │   ├── S001_MAKAN_001.mp4
    │   │   └── ...
    │   └── ...
    ├── keypoints/                    # Array keypoint .npy
    │   ├── S001_MAKAN_001.npy        # shape: [T, 543, 3], float32
    │   └── S001_MAKAN_001_conf.npy   # shape: [T, 543, 1], float32
    ├── splits/
    │   ├── train.jsonl
    │   ├── val.jsonl
    │   └── test.jsonl
    └── validation_errors.txt         # Dibuat jika ada ketidaksesuaian
```

---

## 7. Pernyataan Etika dan Privasi

- Semua signer memberikan persetujuan tertulis (consent form PDF, Bahasa Indonesia).
- Wajah tidak diblur — diperlukan untuk ekstraksi keypoint wajah MediaPipe.
- Data tidak mengandung informasi identitas pribadi selain ID anonim.
- Penggunaan komersial diizinkan di bawah CC BY 4.0 dengan atribusi.
- Dataset tidak mengandung konten sensitif atau berbahaya.

---

## 8. Keterbatasan Dataset

- Hanya mencakup 32 gloss kata tunggal (word-level), bukan kalimat atau percakapan.
- Jumlah signer terbatas (5 asli) dapat menyebabkan bias signer.
- Variasi dialek BISINDO antar daerah belum terwakili sepenuhnya.
- Kondisi pencahayaan dan latar belakang terbatas pada rekaman kampus/laboratorium.

---

## 9. Kontak dan Kontribusi

Untuk pertanyaan tentang dataset atau kontribusi data baru, lihat `CONTRIBUTING_DATA.md`.

Kontak peneliti: *(sesuaikan dengan email/repositori penelitian)*
Repositori: <https://github.com/signbridge/signbridge-bisindo>
Hugging Face: <https://huggingface.co/datasets/signbridge/wl-bisindo-extended>
