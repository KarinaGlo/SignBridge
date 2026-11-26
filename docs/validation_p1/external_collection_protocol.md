# PROTOKOL PENGAMBILAN DATASET EKSTERNAL BISINDO (780 FOTO)

> **Dokumen**: `docs/validation_p1/external_collection_protocol.md`  
> **Modul**: Modality Image I1 — BISINDO Alphabet Fingerspelling  
> **Target Pengumpulan**: 3 Penutur Baru $\times$ 26 Huruf (A–Z) $\times$ 10 Foto = **780 Foto**  
> **Tujuan**: Uji Generalisasi Subjek Independen (*Subject-Independent Generalization*)  
> **Status**: **`READY FOR EXECUTION`**

---

## 1. TARGET & ALOKASI SAMPEL

$$\text{Total Target} = 3 \text{ Penutur} \times 26 \text{ Huruf (A–Z)} \times 10 \text{ Repetisi} = \mathbf{780 \text{ Foto}}$$

| Penutur (Signer ID) | Kategori Partisipan | Jumlah Huruf | Foto per Huruf | Subtotal Foto |
|---|---|:---:|:---:|:---:|
| **`EXT_S01`** | Mahasiswa / Penutur Pemula Baru | 26 (A–Z) | 10 foto | 260 foto |
| **`EXT_S02`** | Mahasiswa / Komunitas Isyarat | 26 (A–Z) | 10 foto | 260 foto |
| **`EXT_S03`** | Pengajar / Penutur Fasih BISINDO | 26 (A–Z) | 10 foto | 260 foto |
| **TOTAL GABUNGAN** | **3 Penutur Independen** | **26 Kelas** | **30 foto/kelas** | **780 FOTO** |

---

## 2. SPESIFIKASI VARIASI PEMOTRETAN (10 FOTO PER HURUF)

Untuk setiap huruf yang diperagakan oleh masing-masing penutur, 10 foto harus diambil dengan variasi terkontrol:

| No. Foto | Variasi Jarak Kamera | Sudut Pengambilan (*Angle*) | Kondisi Pencahayaan | Latar Belakang (*Background*) |
|:---:|:---:|:---:|:---:|:---|
| **01** | Jarak Dekat ($0,5\text{ m}$) | Frontal Datar (*Eye-level*) | Lampu Ruangan Terang ($>300\text{ lux}$) | Dinding Polos Terang |
| **02** | Jarak Dekat ($0,5\text{ m}$) | Miring Sedikit Kanan ($+15^\circ$) | Lampu Ruangan Terang | Dinding Polos Terang |
| **03** | Jarak Sedang ($1,0\text{ m}$) | Frontal Datar (*Eye-level*) | Cahaya Alami Siang Hari (*Daylight*) | Latar Belakang Alami Ruangan |
| **04** | Jarak Sedang ($1,0\text{ m}$) | Miring Sedikit Kiri ($-15^\circ$) | Cahaya Alami Siang Hari | Latar Belakang Alami Ruangan |
| **05** | Jarak Sedang ($1,0\text{ m}$) | Sedikit dari Atas ($+15^\circ$ Elevasi) | Lampu Meja Samping | Kain / Tirai Bertekstur |
| **06** | Jarak Sedang ($1,0\text{ m}$) | Sedikit dari Bawah ($-15^\circ$ Elevasi) | Lampu Meja Samping | Kain / Tirai Bertekstur |
| **07** | Jarak Jauh ($1,5\text{ m}$) | Frontal Datar (*Eye-level*) | Pencahayaan Redup / Hangat ($150\text{ lux}$) | Pakaian Gelap / Kontras |
| **08** | Jarak Jauh ($1,5\text{ m}$) | Sedikit Miring ($+10^\circ$) | Pencahayaan Redup / Hangat | Pakaian Gelap / Kontras |
| **09** | Jarak Bebas ($0,8\text{ m}$) | Bebas Alami | Pencahayaan Campuran | Meja Belajar / Ruang Kelas |
| **10** | Jarak Bebas ($0,8\text{ m}$) | Bebas Alami | Pencahayaan Campuran | Meja Belajar / Ruang Kelas |

---

## 3. PANDUAN TEKNIS PENGAMBILAN CITRA

1. **Kejelasan Gestur**:
   - Seluruh telapak tangan dan jari yang membentuk isyarat harus terlihat utuh di dalam jendela bidik kamera.
   - Tidak boleh ada jari yang terpotong oleh tepi frame kamera.
   - Tangan kanan diutamakan (atau tangan dominan penutur dicatat pada kolom `notes`).
2. **Kualitas Citra**:
   - Resolusi kamera minimal $1080 \times 1920$ (Full HD) atau setara kamera smartphone standar.
   - Fokus tajam pada tangan (*hand focus lock*), hindari foto buram (*motion blur*).
   - DILARANG menggunakan filter kecantikan (*beauty/smooth filter*), efek HDR berlebihan, atau manipulasi AI yang mengubah bentuk kontur jari.
3. **Perlakuan Khusus Huruf I dan J**:
   - **Huruf I**: Pose statis kelingking tegak lurus ke atas.
   - **Huruf J**: Karena J melibatkan gerakan melengkung ke bawah, rekam 5 foto pada fase awal gerakan (kelingking atas) dan 5 foto pada fase akhir sapuan (mata kail). Catat fase ini pada kolom `notes` manifest.
4. **Perlakuan Khusus Pasangan Mirip (D vs P, M vs N)**:
   - Pastikan penutur memperagakan orientasi sudut jempol dan telunjuk sesuai standar kamus BISINDO resmi agar tidak ambigu.

---

## 4. ETIKA PENELITIAN & PERLINDUNGAN PRIVASI

1. **Informed Consent (Persetujuan Partisipan)**:
   - Partisipan wajib membaca lembar informasi penelitian dan menandatangani formulir persetujuan (*informed consent form*).
   - Partisipan berhak menarik diri sewaktu-waktu tanpa konsekuensi.
2. **Anonimisasi Subjek**:
   - Nama asli penutur tidak boleh dicantumkan pada nama berkas atau manifest publik.
   - Gunakan ID anonim: `EXT_S01`, `EXT_S02`, dan `EXT_S03`.
3. **Perlindungan Wajah (*Facial Privacy*)**:
   - Foto yang disimpan diutamakan dipotong (*cropped*) terfokus pada area dada dan tangan.
   - Jika wajah penutur masuk ke dalam frame foto, wajib dilakukan pemburaman (*blurring / anonymization masking*) sebelum dataset dipublikasikan.
4. **Penyimpanan Aman**:
   - Seluruh data mentah disimpan pada penyimpanan terenkripsi internal proyek `data/external/bisindo_validation/` dan tidak diunggah ke repositori Git publik tanpa persetujuan komite etika.

