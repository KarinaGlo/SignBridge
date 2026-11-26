# LAPORAN UTAMA: AUDIT FISIK DATASET I1 & KESIAPAN VALIDASI EKSTERNAL (SIGNBRIDGE ASEAN)

> **Dokumen**: `docs/validation_p1/I1_DATASET_AND_EXTERNAL_VALIDATION_READINESS.md`  
> **Modul**: Modality Image I1 — BISINDO Alphabet Fingerspelling  
> **Target Dataset**: Mendeley BISINDO Alphabet (`ywnjpbcz8m`) & External Validation Suite  
> **Tanggal Pelaksanaan**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer, Dataset Auditor & Research Validation Engineer  
> **Status Kesiapan Akhir**:
> - **`DATASET READY`** : **TERVERIFIKASI FISIK PENUH** ($4.462$ citra preprocessed + $4.466$ citra mentah)
> - **`EXTERNAL COLLECTION READY`** : **SIAP EKSEKUSI** (Protokol 780 foto, etika, template manifest 14-kolom)
> - **`EXTERNAL VALIDATION READY`** : **SIAP EKSEKUSI** (Script evaluasi teruji, checkpoint P1 utuh, status eksekusi: PENDING DATA COLLECTION)

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Laporan ini menyajikan hasil audit fisik mendalam terhadap ketersediaan dataset citra abjad BISINDO (Modul Image I1) di seluruh media penyimpanan proyek SignBridge ASEAN, mengklarifikasi diskrepansi laporan sebelumnya, memvalidasi konsistensi checkpoint model, serta menetapkan protokol dan infrastruktur pengujian generalisasi eksternal (780 foto baru dari 3 penutur independen).

### Temuan Utama:
1. **Dataset Fisik Tersedia Nyata & Lengkap di Disk**:
   - Berbeda dari kekhawatiran audit awal (yang mencatat direktori `data/` hanya berukuran $\approx 4,64\text{ MB}$ saat dataset belum diunduh), audit fisik saat ini membuktikan bahwa **seluruh dataset telah terunduh dan terproses penuh**:
     - **Folder `data/` Total**: **$13.417$ berkas, $744,01\text{ MB}$**.
     - **Dataset Mentah (`data/raw/image/bisindo_alphabet/`)**: **$4.466$ citra mentah** ($44,11\text{ MB}$).
     - **Dataset Hasil Preprocessing (`data/processed/bisindo_alphabet/`)**: **$4.462$ citra JPG** ($224 \times 224$ RGB) dan **$4.462$ tensor NPY** ($224 \times 224 \times 3$, uint8), total $695,47\text{ MB}$.
     - **Berkas Rusak / 0-Byte**: **NOL ($0$)**. Seluruh citra terbaca normal.
2. **Rekonstruksi & Integritas Split Stratified**:
   - Pembagian data $4.462$ citra terbukti $100\%$ konsisten:
     - **Train**: $3.123$ citra ($70,00\%$).
     - **Validation**: $669$ citra ($15,00\%$).
     - **Test**: $670$ citra ($15,00\%$).
   - Tidak ada sampel yang tumpang tindih (*zero leakage* pada SHA-256 dan dHash 64-bit).
3. **Integritas Checkpoint Terjaga Penuh**:
   - Checkpoint `runs/image_i1_mobilenetv3_p1/best.pt` (SHA-256: `83c6a0933c8e1a2097ce6fa1198d8578826ed37731c18137c057fea129affee9`) berada dalam kondisi identik dengan baseline, berasal dari Epoch 18.
   - Model produksi `web/model/fingerspell.onnx` dan model baseline lama `runs/image_i1_mobilenetv3/best.pt` tetap utuh tanpa modifikasi.
4. **Kesiapan Validasi Eksternal**:
   - Struktur direktori `data/external/bisindo_validation/` (subfolder `A/` s.d. `Z/`), template manifest 14-atribut, protokol pemotretan 780 foto, pedoman etika/privasi, dan script evaluasi otomatis [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) telah siap digunakan.
   - Status evaluasi eksternal saat ini dinyatakan secara transparan dan jujur sebagai **`PENDING DATA COLLECTION`** (tidak ada fabrikasi data sintetis).

---

## 2. AUDIT FISIK DATASET I1 & KLARIFIKASI DOKUMENTASI

### A. Investigasi Diskrepansi Laporan Terdahulu
Pada audit awal repository, direktori `data/` dilaporkan hanya berukuran $\approx 4,64\text{ MB}$ karena pada saat itu repository baru memuat manifest teks, skrip jembatan, dan rekaman audio kelas. Dataset gambar Mendeley belum diunduh ke lingkungan lokal.

Proses pengunduhan resmi dieksekusi pada **Tahap 2 (Task P0)** langsung dari repositori Mendeley Data API (DOI: `10.17632/ywnjpbcz8m.1`), menghasilkan $4.466$ gambar mentah. Selanjutnya pada **Tahap 4 (Task P0)**, seluruh dataset diproses melalui deteksi kotak tangan MediaPipe, menghasilkan $4.462$ citra crop $224 \times 224$ (4 citra ambigu dari pasangan duplikat B vs E dan D vs P dieksklusi secara transparan).

Dengan demikian, **klaim bahwa dataset hilang atau tidak ada adalah KELIRU**. Dataset saat ini tersimpan utuh dan siap pakai di filesystem lokal.

---

## 3. LOKASI PENYIMPANAN DATA & INVENTARISASI BERKAS

Berikut inventarisasi fisik berkas yang berhasil diverifikasi pada disk:

| No | Lokasi Direktori Fisik | Tipe Berkas | Jumlah File | Ukuran Total | Status Integritas |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | `data/raw/image/bisindo_alphabet/*/*.jpg` | Raw JPEG Images | $4.154$ berkas | $40,85\text{ MB}$ | Terbaca normal ($100\%$) |
| 2 | `data/raw/image/bisindo_alphabet/*/*.jpeg` | Raw JPEG Images | $312$ berkas | $3,15\text{ MB}$ | Terbaca normal ($100\%$) |
| 3 | `data/processed/bisindo_alphabet/*/*.jpg` | Preprocessed Cropped JPG | $4.462$ berkas | $36,88\text{ MB}$ | Resolusi $224 \times 224$ RGB |
| 4 | `data/processed/bisindo_alphabet/*/*.npy` | Preprocessed Tensor Arrays | $4.462$ berkas | $658,59\text{ MB}$ | Shape $[224, 224, 3]$ uint8 |
| 5 | `data/processed/bisindo_alphabet/*.csv` | Manifest & Audit CSV | $2$ berkas | $0,81\text{ MB}$ | Utuh ($4.462$ baris valid) |
| 6 | `data/raw/image/bisindo_alphabet/*.*` | Metadata & Hash Checksum | $4$ berkas | $0,11\text{ MB}$ | Metadata Mendeley resmi |
| **TOTAL** | **Ekosistem Data Image I1** | **Citra + Tensor + Metadata** | **$13.396$ berkas** | **$740,39\text{ MB}$** | **BERKAS RUSAK: 0** |

Rincian file terdaftar pada artefak pendukung: [`docs/validation_p1/dataset_file_inventory.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/dataset_file_inventory.csv).

---

## 4. DISTRIBUSI KELAS ALFABET BISINDO (A–Z)

Seluruh 26 kelas huruf alfabet BISINDO terwakili secara seimbang di dalam dataset hasil preprocessing:

| Huruf | Indeks | Train ($70\%$) | Val ($15\%$) | Test ($15\%$) | Total Valid | Citra Mentah | Duplikat Dieksklusi |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 0 | 116 | 25 | 24 | 165 | 165 | 0 |
| **B** | 1 | 118 | 25 | 25 | 168 | 169 | 1 (ambigu vs E) |
| **C** | 2 | 118 | 26 | 25 | 169 | 169 | 0 |
| **D** | 3 | 118 | 25 | 26 | 169 | 170 | 1 (ambigu vs P) |
| **E** | 4 | 118 | 25 | 25 | 168 | 169 | 1 (ambigu vs B) |
| **F** | 5 | 121 | 26 | 26 | 173 | 173 | 0 |
| **G** | 6 | 121 | 26 | 26 | 173 | 173 | 0 |
| **H** | 7 | 121 | 26 | 26 | 173 | 173 | 0 |
| **I** | 8 | 121 | 26 | 26 | 173 | 173 | 0 |
| **J** | 9 | 118 | 26 | 25 | 169 | 169 | 0 |
| **K** | 10 | 121 | 26 | 26 | 173 | 173 | 0 |
| **L** | 11 | 120 | 26 | 26 | 172 | 172 | 0 |
| **M** | 12 | 121 | 26 | 26 | 173 | 173 | 0 |
| **N** | 13 | 121 | 26 | 26 | 173 | 173 | 0 |
| **O** | 14 | 121 | 26 | 26 | 173 | 173 | 0 |
| **P** | 15 | 120 | 25 | 26 | 171 | 172 | 1 (ambigu vs D) |
| **Q** | 16 | 121 | 26 | 26 | 173 | 173 | 0 |
| **R** | 17 | 120 | 25 | 26 | 171 | 171 | 0 |
| **S** | 18 | 121 | 26 | 26 | 173 | 173 | 0 |
| **T** | 19 | 121 | 26 | 26 | 173 | 173 | 0 |
| **U** | 20 | 121 | 26 | 26 | 173 | 173 | 0 |
| **V** | 21 | 120 | 26 | 26 | 172 | 172 | 0 |
| **W** | 22 | 119 | 25 | 26 | 170 | 170 | 0 |
| **X** | 23 | 122 | 26 | 26 | 174 | 174 | 0 |
| **Y** | 24 | 122 | 26 | 26 | 174 | 174 | 0 |
| **Z** | 25 | 122 | 26 | 26 | 174 | 174 | 0 |
| **TOTAL** | **26 Kelas** | **3.123** | **669** | **670** | **4.462** | **4.466** | **4 Citra Ambigu** |

Rincian per kelas tersedia pada file: [`docs/validation_p1/dataset_class_distribution.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/dataset_class_distribution.csv).

---

## 5. VERIFIKASI PEMBAGIAN DATA (*SPLIT VERIFICATION*)

- **Protokol Split**: Stratified random sampling berimbang menggunakan random seed $42$.
- **Integritas Himpunan Data**:
  - $\text{Train} \cap \text{Validation} = \emptyset$ (Nol tumpang tindih).
  - $\text{Train} \cap \text{Test} = \emptyset$ (Nol tumpang tindih).
  - $\text{Validation} \cap \text{Test} = \emptyset$ (Nol tumpang tindih).
- **Verifikasi Checksum SHA-256 & Perceptual dHash**: Tidak ditemukan duplikasi biner maupun near-duplicate (Hamming distance $\le 2$) antara Test Set dan Train Set.
- **Status Verifikasi Split**: **`VERIFIED`**.

Laporan kepatuhan integritas tersedia pada: [`docs/validation_p1/dataset_integrity_report.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/dataset_integrity_report.csv).

---

## 6. KONSISTENSI DOKUMENTASI, CONFIG & CHECKPOINT

Audit kesesuaian lintas-berkas membuktikan paritas sempurna:

| Entitas yang Diperiksa | Spesifikasi Klaim Dokumentasi | Bukti Aktual pada Berkas | Status Konsistensi |
|---|---|---|:---:|
| **Checkpoint `best.pt`** | Berasal dari Epoch 18, bobot terbaik | State dict epoch $= 18$, val acc $= 60,24\%$ | **VERIFIED** |
| **Hash SHA-256 `best.pt`** | `83c6a0933c8e1a...` | `83c6a0933c8e1a2097ce6fa1198d8578826ed37731c18137c057fea129affee9` | **VERIFIED** |
| **Jumlah Output Kelas** | 26 kelas alfabet (A–Z) | Tensor shape `[26, 1024]` pada layer klasifikasi | **VERIFIED** |
| **Sampel Evaluasi Test** | $670$ citra | Tepat $670$ baris pada `predictions.csv` | **VERIFIED** |
| **Model Produksi Web** | `web/model/fingerspell.onnx` utuh | Ukuran $1.062.205\text{ B}$, SHA-256 tidak berubah | **VERIFIED** |
| **Model Baseline P0** | `runs/image_i1_mobilenetv3_p0/best.pt` utuh | Ukuran $3.272.237\text{ B}$, SHA-256 tidak berubah | **VERIFIED** |

---

## 7. RANCANGAN PENGUMPULAN DATA VALIDASI EKSTERNAL (780 FOTO)

Untuk mengatasi keterbatasan dataset Mendeley yang tidak memiliki Subject ID, dirancang pengumpulan dataset validasi eksternal independen:

### A. Parameter Pengumpulan
- **Jumlah Relawan Baru**: **3 Orang Penutur Baru** (`EXT_S01`, `EXT_S02`, `EXT_S03`).
- **Target Huruf**: **26 Huruf** (`A` sampai `Z`).
- **Repetisi Foto**: **10 Foto** per huruf per relawan dengan variasi sudut, jarak ($0,5\text{ m}$, $1,0\text{ m}$, $1,5\text{ m}$), pencahayaan, dan latar belakang.
- **Total Sampel**: $3 \times 26 \times 10 = \mathbf{780 \text{ Foto}}$.

### B. Sumber Pengumpulan
1. Prioritas 1: Relawan mahasiswa baru di lingkungan kampus.
2. Prioritas 2: Komunitas Tuli / BISINDO lokal.
3. Prioritas 3: Pengajar bahasa isyarat untuk verifikasi akurasi pose.

Panduan operasional lengkap tersedia pada: [`docs/validation_p1/external_collection_protocol.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/external_collection_protocol.md).

---

## 8. ETIKA PENELITIAN & PRIVASI PARTISIPAN

1. **Informed Consent**: Pengambilan foto hanya dilakukan setelah partisipan menandatangani lembar persetujuan etika penelitian.
2. **Anonimitas**: Identitas asli tidak dicatat pada manifest publik, melainkan menggunakan kode `EXT_S01`, `EXT_S02`, `EXT_S03`.
3. **Privasi Wajah**: Citra difokuskan pada area tangan. Jika wajah masuk ke dalam frame, diterapkan pemburaman otomatis (*face blurring*).

---

## 9. STRUKTUR DATASET EKSTERNAL & METADATA MANIFEST

Struktur folder terstandar telah disiapkan di [`data/external/bisindo_validation/`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/):

```
data/external/bisindo_validation/
├── A/ ... Z/                       (Subfolder untuk 26 huruf)
├── external_manifest_template.csv  (Template metadata 14-kolom)
└── README.md                       (Panduan penamaan & pengisian)
```

Manifest mencakup 14 atribut kunci:
`image_path, label, signer_id, capture_id, capture_date, device, camera_angle, lighting_condition, background, image_width, image_height, consent_status, verified_label, notes`.

---

## 10. RANCANGAN EVALUASI EKSTERNAL (*EXTERNAL EVALUATION SUITE*)

Script evaluasi terisolasi [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) telah dibangun dengan karakteristik:
- **Read-Only**: Memuat `best.pt` tanpa melakukan pelatihan atau modifikasi bobot.
- **Kompatibilitas Penuh**: Menerapkan normalisasi ImageNet identik ($224 \times 224$).
- **Per-Signer Performance Tracking**: Menghitung akurasi dan Macro F1 secara keseluruhan serta rincian performa per penutur (`EXT_S01`, `EXT_S02`, `EXT_S03`) untuk mengukur ketahanan model terhadap variasi anatomi tangan.
- **Handling Partisipasi Parsial**: Mampu mengevaluasi subset huruf tanpa mengharuskan ke-26 kelas terisi sekaligus.

Checklist pelaksanaan tersedia pada: [`docs/validation_p1/external_validation_checklist.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/external_validation_checklist.md).

---

## 11. KRITERIA KESIAPAN SISTEM (READINESS STATUS)

| Kategori Kesiapan | Status Kesiapan | Dasar Bukti Audit |
|---|:---:|:---|
| **1. DATASET READY** | **`READY`** | $4.462$ citra preprocessed + $4.466$ citra mentah tersedia fisik di disk, $0$ file rusak, split 3.123/669/670 valid. |
| **2. EXTERNAL COLLECTION READY** | **`READY`** | Protokol 780 foto, etika & informed consent, struktur folder A–Z, dan template manifest 14-atribut siap. |
| **3. EXTERNAL VALIDATION READY** | **`READY (PENDING DATA)`** | Pipeline evaluasi non-destruktif dan checkpoint teruji siap jalan; saat ini berstatus **PENDING DATA COLLECTION**. |

---

## 12. REKOMENDASI TINDAKAN SELANJUTNYA

1. **Lakukan Perekaman 3 Penutur Eksternal**: Rekrut 3 sukarelawan untuk mengisi target 780 foto sesuai protokol di `docs/validation_p1/external_collection_protocol.md`.
2. **Jalankan Evaluasi Eksternal Per-Signer**: Jalankan `evaluate_external_images.py` untuk mengukur generalisasi subjek independen riil.
3. **Persiapan Ekspor ONNX Mandiri**: Siapkan ekspor ONNX terisolasi di `runs/image_i1_mobilenetv3_p1/fingerspell_p1.onnx` untuk uji runtime browser sebelum menggantikan model produksi.

