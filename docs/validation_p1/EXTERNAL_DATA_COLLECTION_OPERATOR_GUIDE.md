# PANDUAN OPERATOR PENGAMBILAN DATASET EKSTERNAL BISINDO (780 FOTO)

> **Dokumen**: `docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md`  
> **Modul**: Modality Image I1 — BISINDO Alphabet Fingerspelling (SignBridge ASEAN)  
> **Target**: 3 Penutur Baru $\times$ 26 Huruf (A–Z) $\times$ 10 Foto = **780 Foto**  
> **Sasaran Pengguna**: Operator Lapangan / Enumerator Riset SignBridge  
> **Status Dokumen**: **`OPERATOR GUIDE READY`**

---

## 1. PENDAHULUAN & TUJUAN OPERATOR

Panduan ini disusun untuk memandu operator lapangan dalam mengumpulkan data citra gestur abjad BISINDO dari 3 penutur baru (`EXT_S01`, `EXT_S02`, `EXT_S03`). Tujuan pengumpulan data ini adalah untuk **menguji kemampuan generalisasi subjek independen (*Subject-Independent Generalization*)** dari model MobileNetV3-Small (I1-P1).

> [!IMPORTANT]
> **Data harus berasal dari partisipan manusia nyata yang belum pernah terlibat dalam dataset pelatihan Mendeley Data**. Dilarang menggunakan data sintetis, foto internet anonim tanpa izin, atau duplikasi data lama.

---

## 2. PENETAPAN ID ANONIM PARTISIPAN (*SIGNER ID*)

Identitas asli partisipan (nama lengkap, kontak, institusi) tidak boleh dicantumkan pada nama file atau file manifest publik. Gunakan kode penomoran anonim terstandar:

| Kode Signer | Profil Partisipan | Peran dalam Validasi |
|:---:|---|---|
| **`EXT_S01`** | Mahasiswa / Partisipan Umum Baru | Menguji performa model pada penutur pemula / variasi umum. |
| **`EXT_S02`** | Mahasiswa / Anggota Komunitas Teman Tuli | Menguji performa model pada penutur isyarat aktif sehari-hari. |
| **`EXT_S03`** | Guru SLB / Instruktur / Pengkaji BISINDO | Menguji performa model pada gestur baku dengan kepatuhan fonologis tinggi. |

---

## 3. PROSEDUR INFORMED CONSENT & PRIVASI

Sebelum pemotretan dimulai, operator **WAJIB** menjalankan tahapan etika berikut:

1. **Pemberian Informasi Penelitian**:
   - Jelaskan kepada calon partisipan bahwa foto tangan mereka akan digunakan untuk melatih dan menguji sistem penerjemah bahasa isyarat kecerdasan buatan (SignBridge ASEAN).
   - Jelaskan bahwa partisipasi bersifat sukarela dan partisipan berhak menghentikan sesi kapan saja.
2. **Penandatanganan Formulir Persetujuan**:
   - Pastikan partisipan menandatangani lembar persetujuan (*informed consent form*).
   - Status pada kolom manifest diisi: `CONSENT_SIGNED`.
   - Jika partisipan tidak bersedia menandatangani, pemotretan DILARANG dilakukan.
3. **Perlindungan Privasi Wajah (*Facial Anonymization*)**:
   - Atur bingkai kamera terfokus pada area **bahu, dada, dan tangan**.
   - Hindari memasukkan wajah penuh ke dalam bingkai pemotretan.
   - Apabila wajah tidak sengaja terekam, operator wajib melakukan pemburaman (*blurring / anonymization masking*) sebelum file dimasukkan ke folder dataset.

---

## 4. VERIFIKASI ACUAN BENTUK GESTUR BISINDO (BUKAN ASL!)

> [!CAUTION]
> **DILARANG MENGGUNAKAN ACUAN AMERICAN SIGN LANGUAGE (ASL) ATAU FILIPINO SIGN LANGUAGE (FSL)!**
> 
> Alfabet manual BISINDO memiliki karakteristik fonologis unik Indonesia. Operator wajib menyediakan poster cetak atau kartu acuan alfabet BISINDO resmi (merujuk pada standardisasi Pusbisindo / GERKATIN):
> - **Huruf G**: Mengarah horizontal dengan telunjuk dan ibu jari sejajar khas BISINDO.
> - **Huruf P**: Bentuk jari telunjuk dengan lingkaran ibu jari mengarah ke bawah.
> - **Huruf D**: Jari telunjuk tegak lurus ke atas dengan ibu jari dan jari tengah membentuk lingkaran.
> - **Huruf M vs N**: Periksa lipatan jari di atas jempol: M melipat 3 jari (telunjuk, tengah, manis); N melipat 2 jari (telunjuk, tengah).

Operator wajib memverifikasi gestur partisipan sebelum menekan tombol rana kamera.

---

## 5. PROTOKOL PEMOTRETAN (10 FOTO PER HURUF)

Untuk setiap huruf (A sampai Z), ambil tepat **10 foto** dengan variasi terencana sesuai tabel berikut:

| No. Foto | Jarak Kamera | Sudut (*Camera Angle*) | Pencahayaan (*Lighting*) | Latar Belakang (*Background*) |
|:---:|:---:|:---:|:---:|:---|
| **01** | Dekat ($0,5\text{ m}$) | Frontal Datar (*Eye-level*) | Terang ($>300\text{ lux}$) | Dinding Polos Terang |
| **02** | Dekat ($0,5\text{ m}$) | Miring Kanan ($+15^\circ$) | Terang ($>300\text{ lux}$) | Dinding Polos Terang |
| **03** | Sedang ($1,0\text{ m}$) | Frontal Datar (*Eye-level*) | Cahaya Alami Siang Hari (*Daylight*) | Latar Alami Ruangan |
| **04** | Sedang ($1,0\text{ m}$) | Miring Kiri ($-15^\circ$) | Cahaya Alami Siang Hari | Latar Alami Ruangan |
| **05** | Sedang ($1,0\text{ m}$) | Sedikit dari Atas ($+15^\circ$) | Lampu Meja Samping | Kain / Tirai Bertekstur |
| **06** | Sedang ($1,0\text{ m}$) | Sedikit dari Bawah ($-15^\circ$) | Lampu Meja Samping | Kain / Tirai Bertekstur |
| **07** | Jauh ($1,5\text{ m}$) | Frontal Datar (*Eye-level*) | Redup / Hangat ($150\text{ lux}$) | Pakaian Gelap / Kontras |
| **08** | Jauh ($1,5\text{ m}$) | Sedikit Miring ($+10^\circ$) | Redup / Hangat ($150\text{ lux}$) | Pakaian Gelap / Kontras |
| **09** | Bebas ($0,8\text{ m}$) | Alami / Spontan | Pencahayaan Campuran | Meja Belajar / Kelas |
| **10** | Bebas ($0,8\text{ m}$) | Alami / Spontan | Pencahayaan Campuran | Meja Belajar / Kelas |

---

## 6. MENGHINDARI FOTO BURAM & JARI TERPOTONG

1. **Pencegahan Motion Blur (Buram Gerak)**:
   - Minta partisipan menahan pose stabil selama $1\text{--}2$ detik sebelum foto diambil.
   - Kunci titik fokus kamera (*AF/AE Lock*) pada punggung telapak tangan.
   - Pastikan pencahayaan cukup agar kamera smartphone tidak menaikkan waktu eksposur secara berlebihan.
2. **Pencegahan Jari Terpotong (*Framing Margin*)**:
   - Sisakan ruang kosong (*margin*) minimal $15\%$ di sekeliling tangan pada jendela bidik kamera.
   - Ujung kuku jari, pangkal pergelangan tangan, dan rentang jempol harus sepenuhnya berada di dalam frame.
3. **Pemeriksaan Instan Lapangan**:
   - Setiap kali selesai mengambil 10 foto untuk satu huruf, lakukan *pinch-to-zoom* pada layar HP untuk memastikan tidak ada foto yang kabur. Jika buram, ulangi pemotretan saat itu juga.

---

## 7. PERLAKUAN KHUSUS HURUF STATIS DAN DINAMIS (I DAN J)

> [!NOTE]
> **Keterbatasan Citra Tunggal 2D pada Huruf J**:
> - **Huruf I**: Isyarat statis murni (jari kelingking tegak lurus ke atas). Ambil 10 foto pada pose stabil ini.
> - **Huruf J**: Merupakan **isyarat dinamis** yang melibatkan gerakan melengkung ke bawah menyerupai kait (*hook stroke*).
> - **Aturan Pemotretan J**:
>   - Ambil 5 foto (foto 01–05) pada **fase awal pose** (kelingking mengacung ke atas).
>   - Ambil 5 foto (foto 06–10) pada **fase akhir pose** (ujung kelingking setelah sapuan kait).
>   - Catat pada kolom `notes`: `fase_awal_kelingking_atas` atau `fase_akhir_sapuan_kait`.
>   - **PENTING**: Dokumentasikan secara jujur bahwa 10 foto statis tidak merepresentasikan vektor pergerakan J secara utuh.

---

## 8. TATA CARA PENAMAAN FILE & PENEMPATAN DIREKTORI

Simpan setiap foto pada subfolder huruf yang sesuai di dalam `data/external/bisindo_validation/`:

```
data/external/bisindo_validation/
├── A/
│   ├── EXT_S01_A_01.jpg ... EXT_S01_A_10.jpg
│   ├── EXT_S02_A_01.jpg ... EXT_S02_A_10.jpg
│   └── EXT_S03_A_01.jpg ... EXT_S03_A_10.jpg  (Total 30 foto di folder A)
├── B/  (Total 30 foto di folder B)
...
└── Z/  (Total 30 foto di folder Z)
```

**Format Nama File Baku**:
```
[SIGNER_ID]_[LABEL]_[REPETISI].[ext]
```
Contoh: `EXT_S01_A_01.jpg`, `EXT_S02_M_08.jpg`, `EXT_S03_Z_10.jpg`.

---

## 9. PANDUAN PENGISIAN MANIFEST (14 KOLOM)

Setelah pemotretan, operator wajib mencatat setiap foto pada file CSV:  
`data/external/bisindo_validation/manifest.csv` (gunakan template [`external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv)).

| Kolom Manifest | Keterangan & Aturan Pengisian | Contoh Nilai Valid |
|---|---|---|
| `image_path` | Path relatif dari root repository | `data/external/bisindo_validation/A/EXT_S01_A_01.jpg` |
| `label` | Huruf target alfabet (Kapital `A`–`Z`) | `A` |
| `signer_id` | ID anonim penutur | `EXT_S01` |
| `capture_id` | Nomor urut sesi pemotretan | `CAP_001` |
| `capture_date` | Tanggal pemotretan (`YYYY-MM-DD`) | `2026-11-20` |
| `device` | Model perangkat kamera | `Samsung_Galaxy_A54` / `iPhone_13` |
| `camera_angle` | Sudut kamera | `eye_level_frontal` / `slight_above_15deg` |
| `lighting_condition` | Kondisi cahaya | `indoor_lamp_300lux` / `natural_daylight` |
| `background` | Kondisi latar belakang | `plain_white_wall` / `classroom_natural` |
| `image_width` | Lebar resolusi asli foto (piksel) | `1080` / `3024` |
| `image_height` | Tinggi resolusi asli foto (piksel) | `1920` / `4032` |
| `consent_status` | Status persetujuan partisipan | **`CONSENT_SIGNED`** |
| `verified_label` | Verifikasi oleh operator/ahli isyarat | `A` (harus cocok dengan kolom `label`) |
| `notes` | Catatan khusus pose atau tangan | `tangan_kanan_stabil` / `fase_awal_J` |

---

## 10. PEMERIKSAAN AKHIR KELENGKAPAN 780 FOTO

Sebelum menyerahkan dataset ke tim Machine Learning, operator wajib menjalankan checklist mandiri:

1. **Cek Kuantitas**:
   $$\text{Total Berkas Citra} = 26 \text{ Folder} \times 30 \text{ Foto} = \mathbf{780 \text{ Berkas JPG/PNG}}$$
2. **Cek Baris Manifest**:
   File `manifest.csv` harus memuat tepat **780 baris data** (di luar header).
3. **Cek Keutuhan Berkas**:
   Pastikan tidak ada foto yang berukuran 0 byte (rusak saat transfer dari HP).
4. **Cek Nilai Kosong**:
   Pastikan tidak ada kolom manifest yang kosong (*no empty cells*), khususnya pada `consent_status` dan `verified_label`.

