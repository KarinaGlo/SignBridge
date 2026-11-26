# VALIDATOR DISTRIBUTION CHECKLIST & OPERATIONAL DISPATCH PROTOCOL
## SignBridge ASEAN — Modul Image I1 (MobileNetV3-Small BISINDO A–Z)
### Panduan Pemeriksaan Kesiapan Paket Distribusi Validator Independen (Phase 2C.8 Standard)

> [!IMPORTANT]
> **KLARIFIKASI METODOLOGIS: BLINDED VALIDATOR REVIEW**
> Protokol evaluasi ini secara metodologis diklasifikasikan sebagai **`BLINDED_VALIDATOR_REVIEW`** (Evaluasi Buta Validator dengan Kunci Tertutup), **bukan** *Double-Blind Review* murni.
> **Alasan**: Tim peneliti memegang kunci pemetaan internal ([`INTERNAL_SAMPLE_MAPPING.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md)). Validator mengevaluasi stimulus dalam kondisi buta (*blinded*) tanpa mengetahui label, akurasi, prediksi model P1, maupun split data.

---

## 1. INVENTARIS PAKET DISTRIBUSI PESERTA (YANG BOLEH DIBAGIKAN)

Paket yang didistribusikan kepada **Validator A (`VAL-A`)** dan **Validator B (`VAL-B`)** masing-masing memuat tepat **41 berkas**:

| No | Komponen Berkas | Jalur Berkas dalam Paket Distribusi | Status Verifikasi | Catatan Operasional |
| :-: | :--- | :--- | :---: | :--- |
| 1 | **Buku Kerja Excel Interaktif** | `VALIDATOR_A_WORKBOOK.xlsx` (untuk Val A)<br>`VALIDATOR_B_WORKBOOK.xlsx` (untuk Val B) | **VERIFIED CLEAN** | 3 Sheets: Panduan, Lembar Penilaian (embedded images 96x96, dropdown data validation, frozen header), Ringkasan Progres. |
| 2 | **Template Respon CSV Individu (V2)** | `VALIDATOR_A_RESPONSE_TEMPLATE.csv` (Val A)<br>`VALIDATOR_B_RESPONSE_TEMPLATE.csv` (Val B) | **VERIFIED CLEAN** | 36 baris kosong, header baku Schema V2, bebas label dan prediksi. |
| 3 | **Panduan Validator Ramah Tuli** | `PANDUAN_VALIDATOR_BISINDO.md` | **VERIFIED CLEAN** | Menjelaskan metodologi buta, blind letter identification, dan kejelasan 3 kategori. |
| 4 | **Lembar Penilaian Partisipan** | `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md` | **VERIFIED CLEAN** | Lembar instrumen format tabel cetak / markdown alternatif. |
| 5 | **Protokol Operasional Validator** | `VALIDATOR_PROTOCOL.md` | **VERIFIED CLEAN** | Menjelaskan kualifikasi, etika, dan tata kelola evaluasi buta. |
| 6 | **36 Citra Stimulus Anonim** | `stimulus_images/` (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`) | **VERIFIED CLEAN** | Resolusi 224x224, EXIF metadata stripped, tanpa watermark. 100% cocok master manifest. |

---

## 2. DAFTAR BERKAS TERLARANG (STRICTLY CONFIDENTIAL — DILARANG DIBAGIKAN)

Berikut adalah daftar berkas rahasia internal tim peneliti yang **DILARANG KERAS** disertakan dalam paket validator:

- [x] **DILARANG**: [`INTERNAL_SAMPLE_MAPPING.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md) (Memuat kunci dekripsi, label asli, dan prediksi P1).
- [x] **DILARANG**: Skor probabilitas / confidence model P1 (misal: "K -> T 95.1%").
- [x] **DILARANG**: Informasi split dataset asal (`train`, `val`, `test`, `TRAIN_COHORT`, `TEST_SET_DIAGNOSTIC_ONLY`).
- [x] **DILARANG**: Nama berkas mentah asli (misal: `K_Polos Terang_Samsung_A55.jpg`).
- [x] **DILARANG**: Dokumen evaluasi model internal (`docs/validation_p1/`, `I1_DATA_QUALITY_LABEL_AUDIT.md`, dll.).

---

## 3. CHECKLIST PRA-DISTRIBUSI OLEH FASILITATOR (PRE-DISPATCH CHECKLIST)

Sebelum menyerahkan instrumen kepada validator, fasilitator wajib memverifikasi item-item berikut:

- [ ] **1. Integritas Buku Kerja Excel**: `VALIDATOR_A_WORKBOOK.xlsx` / `VALIDATOR_B_WORKBOOK.xlsx` dapat dibuka dengan baik di Microsoft Excel atau WPS Office, pratinjau citra tampil sempurna, dan dropdown berfungsi lancar.
- [ ] **2. Integritas Citra Stimulus**: Seluruh 36 berkas JPG di folder `stimulus_images/` dapat dibuka dan tampil jelas pada perangkat validator.
- [ ] **3. Keselarasan ID**: File gambar `VAL-REV-001.jpg` s/d `VAL-REV-036.jpg` sesuai urutan baris pada lembar kerja dan CSV.
- [ ] **4. Ketiadaan Petunjuk Lisan**: Fasilitator dilarang memberikan petunjuk lisan, isyarat tangan, atau ekspresi wajah yang mengarahkan jawaban validator.
- [ ] **5. Independensi Penilaian**: Validator A dan Validator B mengisi instrumen secara terpisah tanpa komunikasi timbal balik.
- [ ] **6. Pemisahan Berkas Output**: File respon Validator A (`VAL-A`) dan Validator B (`VAL-B`) disimpan pada berkas yang terpisah dan tidak saling dibagikan.

---

## 4. ALUR KERJA PASCA-PENGUMPULAN DATA (POST-COLLECTION WORKFLOW)

```text
[Validator A & B Selesai Mengisi (.xlsx atau .csv)]
                     │
                     ▼
[Hitung SHA-256 Seketika & Arsipkan ke raw_responses/]
                     │
                     ▼
[Verifikasi Pra-Ingesti (load_and_validate_response)]
                     │
     ┌───────────────┴───────────────┐
     ▼                               ▼
[Lolos Validasi Lengkap]    [Skema Salah / Korup]
     │                               │
     ▼                               ▼
[Buat Working Copy]         [Karantina Tanpa Hapus Sumber]
     │                               │
     ▼                               ▼
[calculate_inter_rater_agreement.py] [Klarifikasi ke Validator]
     │
     ├───────────────────────────────┐
     ▼                               ▼
[Unanimous Agreement]      [Discrepancies Detected]
     │                               │
     │                               ▼
     │                     [Isi ADJUDICATION_REGISTER.md]
     │                               │
     │                               ▼
     │                     [Validator C Review]
     │                               │
     └──────────────┬────────────────┘
                    ▼
[Final Report & Rekomendasi Kesiapan Fase P2]
(P2 Training Berstatus STRICT HOLD Selama Proses)
```
