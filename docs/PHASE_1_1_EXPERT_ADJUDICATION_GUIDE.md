# PHASE 1.1 — EXPERT ADJUDICATION GUIDE (BISINDO ALPHABET)
## SignBridge ID–PH (BISINDO ↔ FSL)

Panduan ini ditujukan bagi **ahli bahasa isyarat BISINDO / penutur asli tersertifikasi** untuk menyelesaikan **25 sampel** yang belum sepakat/belum tuntas pada [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) serta melakukan *sign-off* akhir terhadap seluruh 36 sampel.

---

## 1. Struktur Lembar Kerja Adjudikasi

Ahli bekerja pada [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) yang memuat kolom:
- **Identitas & Referensi Gambar (Read-Only)**: `sample_id`, `stimulus_image_path`, `original_filename`
- **Respons Validator (Read-Only — Dilarang Diubah)**: `validator_A_decision`, `validator_A_letter`, `validator_B_decision`, `validator_B_letter`, `adjudication_required`
- **Kolom Keputusan Ahli (Diisi oleh Ahli)**:
  - `expert_final_letter`: Huruf A–Z jika `expert_final_decision == IDENTIFIED`; kosongkan jika `AMBIGUOUS` atau `UNDETERMINABLE`.
  - `expert_final_decision`: Pilih tepat satu: `IDENTIFIED`, `AMBIGUOUS`, atau `UNDETERMINABLE`.
  - `adjudication_reason`: Alasan linguistik atau visual yang ringkas dan spesifik.
  - `adjudicator_id`: Kode/inisial resmi ahli (mis. `EXP-BISINDO-01`).
  - `adjudication_date`: Tanggal keputusan format `YYYY-MM-DD`.
- **Status QC (Diperbarui setelah adjudikasi selesai)**: `final_ground_truth_eligible`, `final_qc_status`.

---

## 2. Prosedur Peninjauan Gambar

1. **Buka Gambar Stimulus**: Gunakan jalur pada `stimulus_image_path` (resolusi `224x224` RGB, bebas EXIF) dan tinjau tanpa memperbesar secara berlebihan atau melakukan filter manipulatif.
2. **Evaluasi Mandiri Terlebih Dahulu**: Amati bentuk tangan (*handshape*), orientasi telapak/pergelangan, jumlah tangan (1 vs 2 tangan), serta kejelasan latar/pencahayaan sebelum membandingkan dengan `validator_A_*` dan `validator_B_*`.
3. **Periksa Catatan Validator**: Tinjau `A_notes` dan `B_notes` pada [`VALIDATOR_COMPARISON.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_COMPARISON.csv) (misalnya keluhan pencahayaan gelap, sudut kamera miring, atau gambar terpotong).
4. **Waspadai Huruf Dinamis (`J` dan `Z`)**: Dalam BISINDO, `J` dan `Z` melibatkan lintasan gerak. Pada foto diam (*static image*), nilai apakah pose diam tersebut cukup merepresentasikan huruf secara tak terbantahkan atau justru `AMBIGUOUS` / `UNDETERMINABLE`.

---

## 3. Aturan Penentuan Keputusan (`expert_final_decision`)

| Keputusan | Kriteria Penentuan | Pengisian `expert_final_letter` |
| :--- | :--- | :--- |
| **`IDENTIFIED`** | Konfigurasi jari, orientasi tangan, dan posisi dua tangan (jika relevan) **jelas dan tak terbantahkan** merepresentasikan satu huruf abjad BISINDO (termasuk variasi regional yang sah). | Wajib diisi huruf `A`–`Z`. |
| **`AMBIGUOUS`** | Tangan terlihat cukup jelas, namun bentuk/sudut/rotasi kamera membuat pose **menyerupai lebih dari satu huruf** (mis. `K` vs `P`, `E` vs `W`, `D` vs `O`) atau posisi tidak standar (mis. terbalik). | **Kosongkan** (jangan memaksa tebakan). |
| **`UNDETERMINABLE`** | Kualitas visual terlalu buruk untuk dibaca secara reliabel: sangat gelap, buram gerak parah, jari terpotong (*clipping*), atau pose bukan gestur abjad BISINDO yang dikenali. | **Kosongkan**. |

---

## 4. Penanganan Variasi Regional BISINDO

- BISINDO memiliki variasi dialek antar daerah (misalnya Jakarta, Yogyakarta, Surabaya, dan daerah lain).
- Jika suatu gambar menampilkan bentuk huruf yang berbeda dari varian yang paling umum, **tetap terima sebagai `IDENTIFIED`** apabila bentuk tersebut merupakan **varian regional BISINDO yang sah dan diakui** secara linguistik.
- Dokumentasikan nama/indikasi variasi regional tersebut pada kolom `adjudication_reason` (contoh: `"IDENTIFIED sebagai O — varian regional valid dengan 3 jari terbuka"`).
- Jangan menolak varian regional yang sah hanya karena berbeda dari satu standar daerah tertentu; sebaliknya, jangan menganggap kesalahan posisi/sudut kamera sebagai variasi regional tanpa dasar linguistik.

---

## 5. Dokumentasi Alasan & Penanganan Ketidakpastian

1. **Wajib Mengisi `adjudication_reason`**:
   - Untuk kasus `IDENTIFIED` yang sebelumnya disengketakan: jelaskan mengapa pembacaan tersebut sah dan mengapa perbedaan antar validator terjadi (mis. *"Bentuk C jelas; label asal R pada Mendeley tidak sesuai visual"*).
   - Untuk kasus `AMBIGUOUS` atau `UNDETERMINABLE`: sebutkan bukti visual spesifik yang diamati (mis. *"Pencahayaan sangat gelap pada latar hitam, batas jari tidak terlihat"* atau *"Foto diam gestur dinamis Z terpotong di bagian pergelangan"*).
2. **Prinsip Konservatif saat Ragu**:
   - Jika ahli masih ragu antara dua huruf setelah meninjau gambar, **pilih `AMBIGUOUS`**, bukan menebak.
   - Jika suatu sampel dinilai tidak dapat diputuskan oleh satu ahli, tandai untuk **panel konsensus dua ahli** dan catat di `adjudication_reason`.
   - **Dilarang** mengandalkan `original_filename` untuk memaksakan label jika isi visual gambar tidak mendukung huruf tersebut.
