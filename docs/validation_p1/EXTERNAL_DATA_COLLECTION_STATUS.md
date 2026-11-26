# STATUS PELAKSANAAN PENGUMPULAN DATA VALIDASI EKSTERNAL (I1-P1)

> **Dokumen**: `docs/validation_p1/EXTERNAL_DATA_COLLECTION_STATUS.md`  
> **Modul**: Modality Image I1 — BISINDO Alphabet Fingerspelling (SignBridge ASEAN)  
> **Target Pengumpulan**: 3 Penutur Baru (`EXT_S01`, `EXT_S02`, `EXT_S03`) $\times$ 26 Huruf $\times$ 10 Foto = **780 Foto**  
> **Tanggal Pembaruan**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor  

---

## 1. PEMISAHAN EMPAT STATUS OPERASIONAL KUNCI

Untuk menjamin transparansi riset dan mencegah klaim prematur, status operasional pengumpulan data eksternal dipisahkan secara tegas ke dalam empat fase independen:

```
[FASE 1: PERSIAPAN]               -->  COMPLETED
[FASE 2: PENGUMPULAN DATA]        -->  PENDING DATA COLLECTION (0 / 780 Foto)
[FASE 3: AUDIT DATA MASUK]        -->  PENDING AUDIT (Menunggu Pengumpulan)
[FASE 4: EKSEKUSI VALIDASI MODEL] -->  PENDING EVALUATION (Menunggu Data Riil)
```

---

## 2. RINCIAN STATUS PER FASE

| No | Fase Operasional | Status Terverifikasi | Bukti Fisik & Catatan Teknis |
|:---:|---|:---:|---|
| **1** | **Persiapan Operasional (*Preparation*)** | **`COMPLETED`** | • Struktur direktori `data/external/bisindo_validation/` (A–Z) telah dibuat.<br>• Template manifest 14-kolom [`external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv) siap.<br>• Panduan Operator [`EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md) telah disahkan.<br>• Protokol sampling 780 foto dan lembar etika siap pakai.<br>• Script evaluasi non-destruktif [`evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) telah teruji. |
| **2** | **Pengumpulan Data Lapangan (*Collection*)** | **`PENDING DATA COLLECTION`** | • **Jumlah Foto Terkumpul**: **$0$ dari $780$ foto**.<br>• **Jumlah Penutur Terekam**: **$0$ dari $3$ penutur** (`EXT_S01`, `EXT_S02`, `EXT_S03`).<br>• Subfolder `A/` sampai `Z/` saat ini masih kosong dari citra nyata.<br>• Rekrutmen partisipan nyata belum dimulai di lapangan. |
| **3** | **Audit Kualitas Data Masuk (*Audit*)** | **`PENDING AUDIT`** | • Karena data belum dikumpulkan, audit integritas fisik (resolusi, dimensi, ketajaman, dan SHA-256) belum dapat dijalankan.<br>• Tidak ada data sintetis atau data fiktif yang dimasukkan. |
| **4** | **Eksekusi Validasi Model (*Execution*)** | **`PENDING EVALUATION`** | • Evaluasi inferensi model `best.pt` belum pernah dijalankan pada data eksternal.<br>• Evaluasi pada template kosong secara aman menghasilkan status `PENDING EXTERNAL DATA / NO_VALID_DATA`.<br>• **TIDAK ADA KLAIM AKURASI EKSTERNAL** yang dibuat sebelum data nyata dievaluasi. |

---

## 3. INVENTARISASI ARTEFAK PERSIAPAN EKSTERNAL

Seluruh berkas persiapan tersimpan rapi dan terisolasi:

1. **Panduan Lengkap Operator Lapangan**:  
   [`docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md)
2. **Protokol Variasi Pemotretan 780 Foto**:  
   [`docs/validation_p1/external_collection_protocol.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/external_collection_protocol.md)
3. **Checklist Kesiapan Operator**:  
   [`docs/validation_p1/external_validation_checklist.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/external_validation_checklist.md)
4. **Template Manifest Standar (14 Atribut)**:  
   [`data/external/bisindo_validation/external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv)
5. **README Direktori Eksternal**:  
   [`data/external/bisindo_validation/README.md`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/README.md)
6. **Script Evaluasi Eksternal (Per-Signer Metrics)**:  
   [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py)

---

## 4. KESIMPULAN

Tahap persiapan operasional telah tuntas $100\%$ (**`PREPARATION COMPLETED`**). Tahap selanjutnya sepenuhnya bergantung pada **tindakan manual operator di dunia nyata** untuk merekrut partisipan, mengambil foto sesuai panduan, dan mengisi manifest sebelum evaluasi model dapat dijalankan.

