# Panduan Anotasi Fonologi Bahasa Isyarat (BISINDO — 32 Gloss Ruang Kelas)

Dokumen ini mendefinisikan skema anotasi fonologi multitask (Stokoe, 1960; Brentari, 1998) yang digunakan oleh cabang fonologi `PhonologyMultitaskHead` pada model **M1 (ST-GCN)** dan **M4 (2-Stream Teacher)** di `data/phonology.csv`.

## 1. Struktur Kolom `data/phonology.csv`

| Kolom | Tipe | Rentang Kelas | Deskripsi |
|---|---|---|---|
| `gloss` | `string` | 32 kosakata | Nama kanonis gloss BISINDO (huruf kapital) |
| `handshape` | `int` | `0..7` (8 kelas) | Konfigurasi jari tangan dominan |
| `location` | `int` | `0..4` (5 kelas) | Lokasi artikulasi utama relatif terhadap tubuh |
| `movement` | `int` | `0..4` (5 kelas) | Arah atau pola lintasan gerak tangan |
| `two_handed` | `int` | `0..1` (2 kelas) | `0` = satu tangan dominan, `1` = dua tangan aktif/simetris |

> **Catatan Loss Multitask**: Apabila suatu gloss memiliki atribut yang ambigu atau belum dianotasi, isi dengan `-1`. Fungsi loss `F.cross_entropy(..., ignore_index=-1)` secara otomatis mengabaikan entri `-1` tanpa memengaruhi gradien atribut lain.

## 2. Definisi Kelas Atribut

### A. `handshape` (Bentuk Tangan — 8 Kelas)
- `0` (**Telapak Terbuka / B-Hand**): Kelima jari rapat atau sedikit renggang terbuka (`HALO`, `TERIMA_KASIH`, `MAAF`, `BUKU`, `BACA`).
- `1` (**Telunjuk Menunjuk / 1-Hand**): Jari telunjuk lurus menunjuk, jari lain menggenggam (`SAYA`, `KAMU`, `SIAPA`, `DIMANA`).
- `2` (**Kepalan / A-Hand / S-Hand**): Tangan mengepal dengan ibu jari di samping/depan (`BISA`, `SUDAH`, `SEKOLAH`).
- `3` (**Jempol Tegak / Thumbs-Up**): Ibu jari terangkat (`BAIK`, `BENAR`).
- `4` (**Cubit / Menulis / F-Hand**): Ibu jari dan telunjuk bertemu seperti memegang pena (`TULIS`, `TUGAS`).
- `5` (**Jari Melengkung / C-Hand / 5-Claw**): Jari-jari terbuka melengkung (`MAU`, `TANYA`, `APA`, `BAGAIMANA`).
- `6` (**Dua Jari / V-Hand / U-Hand**): Telunjuk dan jari tengah terentang (`LIHAT`, `JAWAB`, `KAPAN`).
- `7` (**Silang / Y-Hand / Lainnya**): Konfigurasi khusus seperti kelingking-jempol atau silang (`SALAH`, `BELUM`, `TIDAK`).

### B. `location` (Lokasi Artikulasi — 5 Kelas)
- `0` (**Kepala / Dahi / Pelipis**): Sekitar dahi atau pelipis (`PAHAM`, `BELAJAR`, `GURU`).
- `1` (**Wajah / Mulut / Dagu**): Sekitar bibir, mulut, atau dagu (`TERIMA_KASIH`, `TANYA`, `JAWAB`, `SIAPA`).
- `2` (**Dada / Bahu**): Menyentuh atau di depan dada (`SAYA`, `MAAF`, `MAU`).
- `3` (**Ruang Netral Depan Tubuh**): Ruang artikulasi di depan torso (`HALO`, `KAMU`, `BACA`, `TULIS`, `BUKU`, `KELAS`).
- `4` (**Telapak Tangan Non-Dominan**): Tangan dominan berinteraksi di atas tangan kiri (`TOLONG`, `TUGAS`, `SEKOLAH`).

### C. `movement` (Arah / Pola Gerak — 5 Kelas)
- `0` (**Statis / Tahan Singkat**): Perubahan orientasi minimal (`SAYA`, `KAMU`, `BAIK`).
- `1` (**Maju / Menjauh dari Tubuh**): Gerak lurus ke arah lawan bicara (`TERIMA_KASIH`, `TANYA`, `JAWAB`, `TOLONG`).
- `2` (**Mendatar / Ayun Samping**): Gerak mengayun kiri-kanan (`HALO`, `TIDAK`, `BELUM`, `APA`, `DIMANA`).
- `3` (**Vertikal / Naik-Turun**): Gerak ketukan atau turun-naik (`BISA`, `SUDAH`, `ADA`, `BENAR`, `SEKOLAH`).
- `4` (**Melingkar / Membuka-Menutup**): Gerak melingkar atau lipatan buku (`MAAF`, `BELAJAR`, `BUKU`, `KELAS`, `BAGAIMANA`).

### D. `two_handed` (Keterlibatan Dua Tangan — 2 Kelas)
- `0` (**Satu Tangan Dominan**): Artikulasi cukup dengan tangan kanan (`HALO`, `SAYA`, `KAMU`, `TERIMA_KASIH`).
- `1` (**Dua Tangan**): Membutuhkan kedua tangan (`BUKU`, `BACA`, `TULIS`, `TOLONG`, `KELAS`, `SEKOLAH`, `TEMAN`).

