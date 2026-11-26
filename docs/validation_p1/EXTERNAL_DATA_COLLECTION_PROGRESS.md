# LAPORAN PROGRES PENGUMPULAN DATA EKSTERNAL BISINDO (I1-P1)

**Status Progres**: `NOT STARTED` ⚪  
**Keterangan**: Belum ada foto eksternal fisik yang dikumpulkan maupun didaftarkan di manifest.  
**Waktu Pembaruan (UTC)**: `2026-11-16T15:43:29.842126+00:00`  
**Direktori Data**: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation`  

### Identifikasi File Manifest
- **Manifest aktual**: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv` — **`TERSEDIA & AKTIF 🟢`**
- **Template referensi**: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv` — **`STANDBY`**
- **File yang dibaca saat ini**: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv` (Mode: `ACTUAL_MANIFEST`)

---

## 1. RINGKASAN EKSEKUTIF PROGRES

| Parameter Evaluasi | Target | Capaian Aktual | Kekurangan (Defisit) | Persentase | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Total Sampel Foto** | **780** | **0** | **780** | **0.0%** | `NOT STARTED` |
| Foto Penutur `EXT_S01` | 260 | 0 | 260 | 0.0% | ⏳ BELUM LENGKAP |
| Foto Penutur `EXT_S02` | 260 | 0 | 260 | 0.0% | ⏳ BELUM LENGKAP |
| Foto Penutur `EXT_S03` | 260 | 0 | 260 | 0.0% | ⏳ BELUM LENGKAP |
| Kombinasi Penutur-Huruf Lengkap | 78 sel | 0 sel | 78 sel | 0.0% | ⏳ BELUM LENGKAP |

---

## 2. AUDIT INTEGRITAS & STATUS ANOMALI DATA

Setiap foto wajib memenuhi informed consent bertanda `CONSENT_SIGNED`, terverifikasi fisiknya di disk, tidak terduplikasi, dan terdaftar dalam manifest.

| Kategori Audit Integritas | Jumlah Kasus | Status | Keterangan Aturan |
|---|:---:|:---:|---|
| **Consent Terverifikasi (`CONSENT_SIGNED`)** | **0** | ⚪ BELUM ADA DATA | Hanya data dengan persetujuan sah yang dihitung |
| **Data Ditolak (Consent Tidak Sah/Kosong)** | **0** | 🟢 AMAN (0) | Ditolak otomatis; dilarang masuk evaluasi |
| **File Tercatat tapi Tidak Ditemukan di Disk** | **0** | 🟢 AMAN (0) | Baris manifest merujuk path yang belum ada di disk |
| **File di Disk Belum Tercatat di Manifest** | **0** | 🟢 AMAN (0) | File citra fisik ada tetapi belum didaftarkan di manifest |
| **Foto Duplikat Ditolak (Path / SHA-256)** | **0** | 🟢 AMAN (0) | Sampel identik tidak boleh dihitung ganda |
| **Penutur Tidak Dikenal / Tidak Valid** | **0** | 🟢 AMAN (0) | Wajib salah satu dari: EXT_S01, EXT_S02, EXT_S03 |
| **Label Huruf Tidak Valid** | **0** | 🟢 AMAN (0) | Wajib huruf alfabet kapital A–Z |

---

## 3. PROGRES PER KELAS ALFABET (A–Z)

Setiap huruf memerlukan 30 foto (10 foto × 3 penutur).

| Huruf | Target Total | Terkumpul | Kekurangan | Capaian (%) | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **B** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **C** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **D** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **E** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **F** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **G** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **H** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **I** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **J** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **K** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **L** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **M** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **N** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **O** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **P** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **Q** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **R** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **S** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **T** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **U** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **V** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **W** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **X** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **Y** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |
| **Z** | 30 | 0 | 30 | 0.0% | ⚪ KOSONG |

---

## 4. MATRIKS KOMBINASI PENUTUR × HURUF (78 KOMBINASI)

Target masing-masing sel adalah **10 foto**.

| Huruf | `EXT_S01` (Target 10) | `EXT_S02` (Target 10) | `EXT_S03` (Target 10) | Total Terkumpul (Target 30) | Status Baris |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **B** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **C** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **D** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **E** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **F** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **G** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **H** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **I** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **J** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **K** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **L** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **M** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **N** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **O** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **P** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **Q** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **R** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **S** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **T** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **U** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **V** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **W** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **X** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **Y** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |
| **Z** | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | ⚠️ 0/10 (-10) | **0/30** | ⚪ BELUM ADA |

---

## 5. REKOMENDASI OPERATOR LAPANGAN

> [!IMPORTANT]
> **STATUS SAAT INI: BELUM ADA DATA FISIK EKSTERNAL (0 / 780)**  
> Seluruh folder A–Z dan template manifest telah disiapkan di `data/external/bisindo_validation/`. Jangan menjalankan evaluasi model sebelum foto fisik terkumpul dan terverifikasi.

Langkah tindak lanjut pengumpulan data:
1. **Rekrutmen 3 Signer**: Hubungi partisipan baru (`EXT_S01`, `EXT_S02`, `EXT_S03`) dan pastikan formulir informed consent ditandatangani (`CONSENT_SIGNED`).
2. **Sesi Pemotretan**: Ambil foto sesuai [Panduan Operator](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/EXTERNAL_DATA_COLLECTION_OPERATOR_GUIDE.md) dengan target 10 foto per huruf per penutur.
3. **Penyimpanan Foto**: Simpan file di folder kelas masing-masing, misalnya `data/external/bisindo_validation/A/EXT_S01_A_01.jpg`.
4. **Pengisian Manifest**: Daftarkan file ke `data/external/bisindo_validation/external_manifest.csv`.
5. **Pemantauan Berkala**: Jalankan script tracker ini (`python scripts/validation_p1/track_external_collection.py`) untuk memantau pemenuhan kuota kuadran dan mendeteksi anomali secara real-time.