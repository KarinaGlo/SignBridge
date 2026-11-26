# PHASE 1.1 — SOURCE PROVENANCE REPORT
## SignBridge ID–PH (BISINDO ↔ FSL) — BISINDO Alphabet Dataset Validation

> [!WARNING]
> **PROVENANCE LIMITATION NOTICE**
> File sumber asli `VALIDATOR_A_RESPONSE_ACTUAL (2).csv` dan `VALIDATOR_B_RESPONSE_ACTUAL (1).csv` **tidak ditemukan pada disk** di dalam repositori `D:\SEMESTER 5\ML\Projek_1`. Hasil analisis Phase 1 berasal dari payload CSV yang diberikan secara verbatim pada prompt pengguna, **bukan** dari berkas fisik di repositori, dan **tidak** diklaim atau disalin ke `docs/validation_p2/phase_2c/raw_responses/` sebagai berkas asli.

---

## 1. Hasil Pencarian Sumber Asli (Tugas A)

Pemeriksaan menyeluruh dilakukan pada repositori `D:\SEMESTER 5\ML\Projek_1` (`Get-ChildItem -Recurse -File -Filter "*VALIDATOR*RESPONSE*"` dan inspeksi langsung direktori `raw_responses/`):

| Target Berkas | Lokasi yang Diperiksa | Status | Temuan Aktual |
| :--- | :--- | :---: | :--- |
| `VALIDATOR_A_RESPONSE_ACTUAL (2).csv` | Seluruh `D:\SEMESTER 5\ML\Projek_1` | **NOT FOUND** | Tidak ada berkas `*ACTUAL*` di repositori. |
| `VALIDATOR_B_RESPONSE_ACTUAL (1).csv` | Seluruh `D:\SEMESTER 5\ML\Projek_1` | **NOT FOUND** | Tidak ada berkas `*ACTUAL*` di repositori. |
| `docs/validation_p2/phase_2c/raw_responses/` | Direktori intake respons mentah | **EMPTY** | Hanya berisi `.gitkeep` (198 bytes) dan `quarantine/.gitkeep` (179 bytes). |
| `docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv` | Template kosong pra-distribusi | **FOUND** | Template kosong (954 bytes, SHA-256: `6aadd634...`). |
| `docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv` | Template kosong pra-distribusi | **FOUND** | Template kosong (954 bytes, SHA-256: `e8e45aa8...`). |

### Kebijakan Non-Rekonstruksi
- Sesuai protokol Phase 1.1, salinan hasil ingest dari prompt **tidak** disalin ke [`docs/validation_p2/phase_2c/raw_responses/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/raw_responses/) agar tidak mengaburkan batas antara berkas asli lapangan dan salinan yang diterima melalui chat/prompt.
- Seluruh hasil analisis Phase 1 dipertahankan tanpa modifikasi data validator.

---

## 2. Inventaris SHA-256 Berkas yang Tersedia

### 2.1. Salinan Prompt-Ingested (Bukan Berkas Disk Asli Repositori)
| Berkas (Lokasi Scratch Sesi) | Ukuran | SHA-256 |
| :--- | :---: | :--- |
| `VALIDATOR_A_RESPONSE_ACTUAL (2).csv` (prompt-ingested verbatim) | 1,865 bytes | `8adf32cc99254479317c20a43f0d32929baf6648a231f34e31b8b24dfb456b2e` |
| `VALIDATOR_B_RESPONSE_ACTUAL (1).csv` (prompt-ingested verbatim) | 2,163 bytes | `c989b0eadf4ab10ccb9e81f91370e8533e83400a5f71275004f7e47fb92ab749` |

### 2.2. Berkas Asli Repositori & Output Turunan Phase 1 / 1.1
| Berkas | Ukuran | SHA-256 |
| :--- | :---: | :--- |
| [`VALIDATOR_A_RESPONSE_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv) | 954 bytes | `6aadd6341dc0968a4014f52ea5ed13b1228974538bfed2c2dc5e8692e0c4277a` |
| [`VALIDATOR_B_RESPONSE_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv) | 954 bytes | `e8e45aa829d974d6286d904363d005b9fcc5804c4c074f79a8f4393696686014` |
| [`VALIDATOR_COMPARISON.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_COMPARISON.csv) | 5,916 bytes | `3a47941a6f1df7334dfa3bf1c9048a65f7b5819dec884b2b452b230d1f5dc49e` |
| [`VALIDATOR_DISAGREEMENTS.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_DISAGREEMENTS.csv) | 3,814 bytes | `bfae0c72f1c93b8920649606fd3df4838afa02488703e99aeaace3dc6701b6c8` |
| [`VALIDATOR_AGREEMENT_SUMMARY.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_AGREEMENT_SUMMARY.csv) | 1,832 bytes | `9784176f299bd983e2968d9f7a16ced13f8b274b6ad5d44e01e0f6b0215f7491` |
| [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) | 6,418 bytes | `aac3b39b8cb5c0bd40bb4a2aae81c6ce5c004addbf2964adad12e547413b6e45` |
| [`ALPHABET_DATASET_QC_FINAL.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/ALPHABET_DATASET_QC_FINAL.csv) | 10,788 bytes | `27ededc2f53e4053d49f56c152cfbcc0418cfad6b98b6d521727043150f3a2c0` |

---

## 3. Verifikasi Kesesuaian Isi dengan Analisis Phase 1

Perbandingan sel-demi-sel antara payload Validator A & B dengan [`VALIDATOR_COMPARISON.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_COMPARISON.csv) mengonfirmasi:
- **36/36 baris cocok 100%** pada seluruh kolom asli (`identified_letter`, `decision`, `regional_variation`, `notes`, `review_date`).
- **Angka Phase 1 terverifikasi identik**: Decision agreement `17/36 (47.22%)`, Cohen's kappa `0.109375`, `FULL_AGREEMENT` `11/36`, dan `25/36` sampel memerlukan adjudikasi/tinjauan gambar ahli.

---

## 4. Tindakan Pemulihan Provenance yang Disarankan
Untuk menutup celah provenance (*chain of custody*) secara tuntas:
1. Tempatkan berkas asli ekspor Validator A (`VALIDATOR_A_RESPONSE_ACTUAL (2).csv`) dan Validator B (`VALIDATOR_B_RESPONSE_ACTUAL (1).csv`) dari perangkat fasilitator/USB ke [`docs/validation_p2/phase_2c/raw_responses/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/raw_responses/) sebagai arsip read-only.
2. Hitung SHA-256 berkas asli tersebut dan cocokkan dengan hash salinan prompt-ingested di atas (`8adf32cc...` dan `c989b0ea...`).
