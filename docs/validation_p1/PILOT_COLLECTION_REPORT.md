# LAPORAN TAHAP PILOT PENGUMPULAN DATA EKSTERNAL
## BISINDO I1-P1 (PENUTUR EXT_S01, KELAS A)

**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 (BISINDO Alphabet Fingerspelling)  
**Dokumen**: `docs/validation_p1/PILOT_COLLECTION_REPORT.md`  
**Tanggal**: 16 November 2026  
**Status Tahap Pilot**: **`AWAITING GESTURE REFERENCE VERIFICATION`** (HOLD — Pengambilan Foto Nyata Ditangguhkan Menunggu Verifikasi Native Signer)  
**Dokumen Audit Gestur**: [`docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md) (`TERSEDIA ✅`)  
**Formulir Verifikasi Formal**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md) (`PENDING VALIDATOR ⏳`)  
**Panduan Sesi Validasi Buta**: [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md) (`TERSEDIA ✅`)  
**Laporan Revisi Metodologis Final**: [`docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md) (`TERSEDIA ✅`)  
**Manifest Aktual**: [`data/external/bisindo_validation/external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv) (`TERSEDIA & AKTIF 🟢`)  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)  

---

## 1. RINGKASAN EKSEKUTIF PILOT

Tahap pilot pengumpulan data eksternal BISINDO bertujuan menguji kelayakan operasional pengambilan data riil di lapangan pada skala terkecil sebelum ekspansi penuh ke 780 foto.

### Target Spesifik Pilot:
- **Penutur**: `EXT_S01` (1 partisipan baru).
- **Kelas Huruf**: `A` (BISINDO Alfabet).
- **Jumlah Target**: **10 foto** dengan variasi pencahayaan, sudut, latar, dan jarak.

### Status Pencapaian Saat Ini:
1. **Manifest Aktual Resmi Dibuat**: Berkas [`external_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv) telah berhasil dibuat dengan struktur 14 kolom resmi sesuai kontrak template.
2. **Template Referensi Terjaga**: Berkas [`external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv) dipertahankan 100% utuh tanpa modifikasi (`STANDBY`).
3. **Kepatuhan Etika & Integritas Ilmiah**: Sesuai mandat, **tidak ada foto sintetis, placeholder, atau data fiktif yang dibuat**. Manifest belum diisi karena metadata hanya boleh dicatat setelah foto nyata diambil dan formulir persetujuan fisik ditandatangani.
4. **Verifikasi Tracker Lapangan**: Tracker dijalankan dan secara otomatis mendeteksi `external_manifest.csv` dalam mode `ACTUAL_MANIFEST`. Status sistem adalah **`NOT STARTED` ⚪ (0 / 780 foto valid, defisit pilot: 10 foto, defisit total: 780 foto)**.
5. **Kesiapan Folder Kelas A**: Direktori target `data/external/bisindo_validation/A/` telah bersih dan siap menerima 10 file citra nyata.

---

## 2. AUDIT STRUKTUR DIREKTORI & INTEGRITAS SISTEM

### A. Keberadaan File Manifest Aktual vs Template
Pemeriksaan status berkas di `data/external/bisindo_validation/`:
- `external_manifest.csv`: **Tersedia (Ukuran: 172 bytes)** — Memuat header resmi 14 kolom.
- `external_manifest_template.csv`: **Utuh (Ukuran: 390 bytes)** — Menyimpan baris contoh diawali `#`.
- Folder Kelas `A`–`Z`: Seluruh 26 subdirektori tersedia lengkap.

### B. Header Resmi Manifest Aktual (14 Kolom)
```csv
image_path,label,signer_id,capture_id,capture_date,device,camera_angle,lighting_condition,background,image_width,image_height,consent_status,verified_label,notes
```

### C. Hasil Audit Fisik Direktori Citra
- Jumlah file citra di `data/external/bisindo_validation/A/`: **0 foto**
- Jumlah file citra di seluruh folder `data/external/bisindo_validation/`: **0 foto**
- **Status Data Aktual**: **0 / 10 foto pilot (0 / 780 foto total)**.

---

## 3. HASIL EKSEKUSI TRACKER TERHADAP MANIFEST AKTUAL

Perintah eksekusi:
```powershell
python scripts/validation_p1/track_external_collection.py --data-dir data/external/bisindo_validation --output-report docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md --output-json docs/validation_p1/external_collection_progress.json
```

### Ringkasan Output Tracker:
- **Status Keseluruhan**: `NOT STARTED` ⚪
- **Keterangan**: Belum ada foto eksternal fisik yang dikumpulkan maupun didaftarkan di manifest.
- **Identifikasi Manifest**:
  - Manifest aktual: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest.csv` — **`TERSEDIA & AKTIF 🟢`**
  - Template referensi: `D:/SEMESTER 5/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv` — **`STANDBY`**
  - Mode Pembacaan: **`ACTUAL_MANIFEST`**
- **Metrik Pilot (EXT_S01, Huruf A)**:
  - Foto Terkumpul: **0 / 10**
  - Defisit Pilot: **10 foto**
  - Defisit Total: **780 foto**
- **Audit Anomali Data**:
  - `unconsented_count`: 0
  - `missing_disk_count`: 0
  - `unregistered_disk_count`: 0
  - `duplicate_count`: 0
  - `invalid_signer_count`: 0
  - `invalid_label_count`: 0

---

## 4. SPESIFIKASI GESTUR BISINDO KELAS A (KOREKSI DUA TANGAN — ANTI-ASL / ANTI-SIBI)

> [!CAUTION]
> **PENCABUTAN INSTRUKSI KELIRU**: Instruksi sebelumnya yang menyebutkan BISINDO A berupa *"telapak tangan terbuka 5 jari"* dinyatakan **KELIRU & DICABUT RESMI**. Berdasarkan audit empiris dataset training ([`docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md)), 100% citra Kelas A pada dataset proyek menggunakan **gestur dua tangan membentuk bangun segitiga ($\Delta$)**.

Operator lapangan wajib memastikan partisipan `EXT_S01` memperagakan bentuk gestur BISINDO asli sesuai korpus pelatihan:

| Aspek Gestur | BISINDO Kelas A (Wajib — Sah) | Larangan: SIBI / ASL / Salah Kaprah |
|---|---|---|
| **Keterlibatan Tangan** | **DUA TANGAN (Two-Handed / Bimanual)**. Kedua tangan aktif di depan dada. | Satu tangan tunggal (Ditolak). |
| **Bentuk Tangan ($\wedge$)** | Ujung kedua jari telunjuk (kanan dan kiri) bersentuhan di atas membentuk puncak segitiga. | Telunjuk terpisah atau tertekuk. |
| **Palang Bawah ($-$)** | Ujung kedua ibu jari (kanan dan kiri) bersentuhan horizontal di bawah membentuk alas/palang segitiga. | Ibu jari melipat ke dalam atau tidak menyentuh. |
| **Jari Lainnya** | Jari tengah, jari manis, dan kelingking kedua tangan tertekuk rapat ke dalam telapak tangan. | Jari tengah/manis/kelingking terbuka. |
| **Bentuk Total** | Menyerupai **bangun segitiga / huruf kapital "A" ($\Delta$)**. | **Ditolak mutlak**: Telapak tangan terbuka 5 jari (angka 5/sapaan) atau kepalan tinju SIBI/ASL. |
| **Orientasi & Posisi** | Setinggi dada (*chest-level*), menghadap langsung ke lensa kamera. | Menutupi wajah atau di luar bingkai kamera. |

> [!IMPORTANT]
> **STATUS TUNGGU VERIFIKASI PENUTUR ASLI**: Meskipun bukti dataset dan literatur Pusbisindo telah konklusif mengenai bentuk dua tangan segitiga, pengambilan foto fisik **DITANGGUHKAN SEMENTARA (HOLD)** hingga proses verifikasi formal bersama penutur asli Tuli (*native Deaf signer*) atau instruktur BISINDO dicatat dalam repositori.

---

## 5. PANDUAN KERJA OPERATOR LAPANGAN (CHECKLIST EKSEKUSI PILOT)

Untuk menyelesaikan pilot 10 foto ini, operator lapangan perlu melaksanakan langkah berikut:

### Langkah 1: Rekrutmen & Informed Consent
1. Partisipan baru `EXT_S01` membaca lembar informasi penelitian.
2. Partisipan menandatangani formulir persetujuan informed consent fisik.
3. Status consent pada catatan: `CONSENT_SIGNED`.

### Langkah 2: Sesi Pengambilan 10 Foto (EXT_S01, Kelas A)
Ambil 10 foto dengan variasi terkontrol dan simpan di folder `data/external/bisindo_validation/A/`:

| No | Nama File Target | Variasi Jarak | Sudut Kamera | Kondisi Pencahayaan | Latar Belakang |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | `EXT_S01_A_01.jpg` | Standar (0.8 m) | Frontal sejajar mata | Lampu ruangan terang (300 lux) | Tembok polos putih |
| 2 | `EXT_S01_A_02.jpg` | Standar (0.8 m) | Sedikit dari atas (+15°) | Lampu ruangan terang (300 lux) | Tembok polos putih |
| 3 | `EXT_S01_A_03.jpg` | Standar (0.8 m) | Sedikit dari kiri (-15°) | Lampu ruangan terang (300 lux) | Tembok polos putih |
| 4 | `EXT_S01_A_04.jpg` | Dekat (0.5 m) | Frontal sejajar mata | Lampu ruangan terang (300 lux) | Tembok polos krem/abu |
| 5 | `EXT_S01_A_05.jpg` | Jauh (1.2 m) | Frontal sejajar mata | Lampu ruangan terang (300 lux) | Tembok polos putih |
| 6 | `EXT_S01_A_06.jpg` | Standar (0.8 m) | Frontal sejajar mata | Cahaya redup (100–150 lux) | Tembok polos putih |
| 7 | `EXT_S01_A_07.jpg` | Standar (0.8 m) | Frontal sejajar mata | Cahaya samping (side shadow) | Tembok polos putih |
| 8 | `EXT_S01_A_08.jpg` | Standar (0.8 m) | Sedikit dari kanan (+15°) | Cahaya alami jendela (siang) | Latar rumah wajar (pintu kayu) |
| 9 | `EXT_S01_A_09.jpg` | Standar (0.8 m) | Frontal sejajar mata | Lampu hangat (warm light) | Tembok polos putih |
| 10 | `EXT_S01_A_10.jpg` | Standar (0.8 m) | Frontal sejajar mata | Lampu ruangan terang (300 lux) | Latar kontras gelap (kain hitam/biru) |

### Langkah 3: Pengisian Metadata ke `external_manifest.csv`
Buka berkas `data/external/bisindo_validation/external_manifest.csv` dan tambahkan 10 baris data sesuai format:
```csv
image_path,label,signer_id,capture_id,capture_date,device,camera_angle,lighting_condition,background,image_width,image_height,consent_status,verified_label,notes
A/EXT_S01_A_01.jpg,A,EXT_S01,CAP_001,2026-11-20,Samsung_Galaxy_A54,eye_level_frontal,indoor_lamp_300lux,plain_white_wall,1080,1920,CONSENT_SIGNED,A,dua_tangan_segitiga_a_jelas
A/EXT_S01_A_02.jpg,A,EXT_S01,CAP_002,2026-11-20,Samsung_Galaxy_A54,high_angle_15deg,indoor_lamp_300lux,plain_white_wall,1080,1920,CONSENT_SIGNED,A,dua_tangan_segitiga_a_jelas
...
```

### Langkah 4: Validasi Ulang Tracker
Setelah 10 foto disimpan di disk dan manifest diisi, jalankan:
```powershell
python scripts/validation_p1/track_external_collection.py --data-dir data/external/bisindo_validation --output-report docs/validation_p1/EXTERNAL_DATA_COLLECTION_PROGRESS.md --output-json docs/validation_p1/external_collection_progress.json
```
Target status setelah foto dimasukkan: **`IN PROGRESS`** dengan capaian **`10 / 780 foto (1.28%)`**, defisit kelas A untuk EXT_S01 menjadi **0 (Lengkap ✅)**, dan 0 anomali.

---

## 6. VERIFIKASI INTEGRITAS SISTEM & CHECKPOINT

- **SHA-256 Checkpoint Model & ONNX**:
  - `runs/image_i1_mobilenetv3_p1/best.pt`: `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` (**100% UTUH**)
  - `web/model/fingerspell.onnx`: `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` (**100% UTUH**)
  - `runs/image_i1_mobilenetv3/best.pt`: `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` (**100% UTUH**)
- **Git Commit HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (Tidak berubah)
- **Status Working Tree**: `0 tracked files modified`. Seluruh perubahan lokal terjaga aman.

---

## 7. KESIMPULAN & STATUS TAHAP BERIKUTNYA

Tahap persiapan pilot telah diverifikasi secara teknis dan spesifikasi gestur telah dikoreksi:
1. Manifest aktual `external_manifest.csv` telah siap dan aktif (14 kolom resmi).
2. Tracker telah berhasil membaca manifest aktual tanpa error (`NOT STARTED`, 0/780 foto).
3. Seluruh folder penampung telah disiapkan.
4. Spesifikasi gestur kelas A telah dikoreksi menjadi **konfigurasi dua tangan segitiga ($\Delta$)** dan instruksi lama yang keliru telah dicabut.
5. Sistem kini **berhenti pada titik tunggu operasional (*hold state: AWAITING GESTURE REFERENCE VERIFICATION*)**: pengambilan fisik 10 foto oleh operator lapangan ditangguhkan sampai formal sign-off bersama perwakilan komunitas Tuli / penutur asli BISINDO tercatat secara resmi.

