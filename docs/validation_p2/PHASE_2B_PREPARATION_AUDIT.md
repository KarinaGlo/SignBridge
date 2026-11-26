# PHASE 2B PREPARATION AUDIT REPORT: VALIDATOR REVIEW & SESSION-AWARE SPLIT AUDIT
## Modality Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Executive Summary

### 1.1 Context & Scope
Laporan ini merupakan audit kesiapan teknis independen (**Phase 2B Preparation Audit**) untuk modul **Image Modality I1 (BISINDO Alphabet Fingerspelling A–Z, MobileNetV3-Small)** pada proyek *SignBridge ASEAN*. Audit ini bersifat **STRICTLY READ-ONLY**, tanpa melakukan perubahan pada kode, dataset, checkpoint, arsitektur, bobot model, manifest, maupun pipeline produksi.

Audit ini dirancang untuk menjawab lima pertanyaan kunci sebelum melangkah ke pengujian manusia dan pelatihan P2:
1. Apakah paket validasi buta 36 sampel siap digunakan oleh validator Tuli BISINDO yang berkualifikasi?
2. Apakah metadata dataset saat ini mendukung pembagian data berbasis sesi/perangkat (*session/device-aware grouping*)?
3. Apakah enam kandidat gestur *near-duplicate* yang diidentifikasi pada Phase 2A dapat dilacak secara definitif ke berkas sumber, sesi, dan perangkatnya?
4. Apakah skema pembagian data (*split strategy*) berbasis kelompok yang dapat direproduksi (*reproducible group-based split*) dapat dirancang tanpa merusak baseline P1?
5. Apakah proyek siap melanjutkan ke validasi manusia dan peninjauan formal kesiapan P2?

### 1.2 Ringkasan Putusan Audit (Audit Verdicts)
- **Overall Readiness Status**: **`READY_WITH_DOCUMENTED_LIMITATIONS`**
  - Paket validasi 36 sampel secara fisik utuh ($100\%$ berkas dapat dibuka dengan resolusi $224 \times 224$), unik, dan anonim. Namun memiliki batasan terdokumentasi: kolom `Tag Metodologi` pada lembar kerja validator membocorkan status sampel diagnostik test set ke penilai, sehingga harus dihilangkan pada cetakan instrumen validator akhir.
- **Session-Aware Split Feasibility Status**: **`FEASIBLE_WITH_LIMITATIONS`**
  - Pembagian berbasis perangkat (*Device-Grouped Split*) terbukti secara matematis dapat menghasilkan rasio $70,5\%$ Train / $16,0\%$ Val / $13,6\%$ Test dengan seluruh 26 kelas terwakili seimbang (dukungan minimal 21 sampel/kelas pada test set).
  - Namun, karena ketiadaan data identitas peraga pada dataset mentah Mendeley, pembagian ini **tidak dapat diklaim sebagai evaluasi independen subjek**. Status formal: **`SUBJECT_INDEPENDENT_EVALUATION_NOT_VERIFIABLE`**.

---

## 2. Status Repositori (Repository State)

### 2.1 Kondisi Git & Integritas Lingkungan
- **Git Branch**: `feature/field-test-readiness`
- **Git Commit Terakhir**: `3a99e96 docs: add GitHub push report for M0 stabilization`
- **Working Tree**: Bersih pada berkas terlacak (*0 tracked modifications*). Tidak ada `git reset`, `git clean`, maupun operasi destruktif yang dijalankan.
- **Status Checkpoint & Baseline P1**:
  - Checkpoint P1: `runs/image_i1_mobilenetv3_p1/best.pt` ($6.302.825$ bytes, SHA-256: `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9`) — **VERIFIED UNTOUCHED**.
  - Konfigurasi P1: `configs/image_i1_mobilenetv3_p1.yaml` ($977$ bytes) — **VERIFIED UNTOUCHED**.

### 2.2 Verifikasi Keberadaan Berkas Phase 2A
Seluruh lima artefak utama dari Phase 2A telah diverifikasi keberadaan fisik, integritas ukuran, dan keterbacaannya:

| Jalur Berkas Artefak | Ukuran (Bytes) | Status Verifikasi |
| :--- | :---: | :---: |
| `docs/validation_p2/PHASE_2A_VISUAL_FORENSIC_REPORT.md` | $22.728$ | **VERIFIED** |
| `docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md` | $6.484$ | **VERIFIED** |
| `docs/validation_p2/figures/cross_split_17_pairs_contact_sheet.png` | $3.119.576$ | **VERIFIED** |
| `docs/validation_p2/figures/high_confidence_18_errors_contact_sheet.png` | $2.424.025$ | **VERIFIED** |
| `docs/validation_p2/figures/preprocessing_simulation_comparison.png` | $2.705.037$ | **VERIFIED** |

---

## 3. Audit Paket Validasi Buta (Blind Validator Package Audit)

Audit dilakukan terhadap dokumen instrumen:
`docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md`

### 3.1 Evaluasi 12 Kriteria Kesiapan Instrumen

| No | Kriteria Audit | Hasil Pengujian | Catatan Forensik |
| :-: | :--- | :---: | :--- |
| 1 | Seluruh 36 identifier sampel hadir | **VERIFIED** | Tercatat lengkap dari `VAL-REV-001` hingga `VAL-REV-036`. |
| 2 | Identifier sampel unik | **VERIFIED** | 36 identifier unik tanpa duplikasi ID. |
| 3 | Citra dapat diakses dari jalur referensi | **VERIFIED** | $36/36$ citra dapat dibuka secara fisik oleh Pillow, resolusi $224 \times 224$ RGB. |
| 4 | Label asli, prediksi model, & confidence disembunyikan | **VERIFIED** | Lembar penilaian tidak memuat label kelas asli, tebakan model, maupun skor probabilitas. |
| 5 | Empat kategori respons terdefinisi konsisten | **VERIFIED** | `[1] Benar`, `[2] Salah`, `[3] Ambigu`, `[4] Tak Tentu` terdefinisi jelas di panduan. |
| 6 | Ruang memadai untuk catatan / alternatif | **VERIFIED** | Kolom "Huruf Usulan / Catatan Validator" tersedia di setiap baris. |
| 7 | Instruksi netral dan mudah dipahami | **VERIFIED** | Instruksi tidak mengarahkan validator ke pilihan tertentu. |
| 8 | Tidak membocorkan jawaban model yang diharapkan | **VERIFIED** | Tidak ada referensi ke kelas prediksi P1 pada lembar pengisian. |
| 9 | 19 sampel diagnostik test set teridentifikasi secara internal | **VERIFIED** | 19 sampel berasal dari test set untuk pengujian diagnostik kesalahan model. |
| 10 | Materi validator **TIDAK** membocorkan status test-set | **FAIL (LIMITATION)** | **TEMUAN KRITIS**: Kolom `Tag Metodologi` menampilkan teks `TEST_SET_DIAGNOSTIC_ONLY` dan `TRAIN_COHORT` langsung kepada validator, membocorkan asal data. Harus disembunyikan pada instrumen cetak. |
| 11 | Sampel non-test memiliki keterlacakan kohort | **VERIFIED** | 17 sampel non-test dapat dilacak ke anomali visual (blur, gelap, border clipping, near-duplicate, dan control baseline). |
| 12 | Pemetaan ID anonim ke sampel internal tersimpan aman | **VERIFIED** | Kunci pemetaan tersimpan pada `scratch/validator_sheet_rows.json` dan laporan internal tanpa diekspos ke penilai. |

### 3.2 Kesesuaian Paket untuk Penggunaan Operasional
- **Independensi Validator**: Sesuai untuk pengisian mandiri oleh validator Tuli tanpa intervensi peneliti.
- **Dukungan Multi-Validator**: Format tabel modular memungkinkan formulir diperbanyak untuk beberapa penilai (*Validator A, Validator B, Validator C*).
- **Pencatatan Perbedaan Pendapat & Variasi Regional**: Kolom catatan memungkinkan pencatatan variasi dialek BISINDO antardaerah (misalnya BISINDO Jakarta vs Yogyakarta vs Bali).
- **Analisis Kesepakatan Antar-Penilai (*Inter-Rater Agreement*)**: Struktur data 4-kategori memungkinkan perhitungan metrik statistik formal (Fleiss' Kappa / Cohen's Kappa) pasca-sesi.

---

## 4. Temuan Representasi Huruf J dan Z (J and Z Representation Audit)

### 4.1 Karakteristik Representasi pada Modalitas Image I1
Audit mendalam terhadap seluruh sampel kelas J ($N=169$) dan kelas Z ($N=174$) mengungkap temuan berikut:
1. **Modalitas Citra Diam Murni**: Seluruh sampel kelas J dan Z hanya berupa citra diam tunggal (`.jpg` / `.npy`). Tidak ada berkas video sumber (`.mp4`, `.avi`, `.mov`) maupun sekuens temporal beruntun pada dataset.
2. **Ketiadaan Definisi Key-Pose Resmi**: Tidak ditemukan dokumen acuan dalam repositori yang mendefinisikan titik awal, titik tengah, atau titik akhir dari gerakan huruf J dan Z yang harus direpresentasikan dalam citra statis.
3. **Keterbatasan pada Lembar Kerja Validator**: Panduan validator saat ini belum secara eksplisit menjelaskan kepada penilai bahwa huruf dinamis (J dan Z) dinilai berdasarkan pose representatif statis, bukan berdasarkan lintasan gerak.

### 4.2 Penemuan Forensik Label Noise pada Folder Kelas Z dan Kelas Lainnya
Pemeriksaan otomatis terhadap 4.462 nama berkas mentah menemukan anomali serius: **8 berkas memiliki awalan huruf (*prefix*) yang bertentangan dengan folder kelas tempatnya berada**:

| Folder Kelas | Prefix Berkas | Nama Berkas Sumber Mentah | Split Manifest | Status Forensik |
| :---: | :---: | :--- | :---: | :--- |
| **Z** | `S` | `S_Baju_Iphone_14 Pro.jpg` | `train` | **MISPLACED FILE / LABEL NOISE** |
| **L** | `E` | `E_Baju_Apple_Iphone 11.jpg` | `test` | **MISPLACED FILE / EVALUATED AS L (PRED: V)** |
| **L** | `E` | `E_Bebas_Apple_Iphone 11.jpg` | `train` | **MISPLACED FILE / LABEL NOISE** |
| **C** | `D` | `D_Bebas_Redmi_Note 12 Pro.jpg` | `train` | **MISPLACED FILE / LABEL NOISE** |
| **V** | `Y` | `Y_Polos Gelap_Iphone_14 Pro.jpg` | `train` | **MISPLACED FILE / LABEL NOISE** |
| **O** | `0` | `0_BEBAS_Apple_Iphone 12.JPG` | `train` | Angka 0 (nol) alih-alih huruf alfabet O |
| **O** | `0` | `0_Polos gelap_Apple_Iphone 12.JPG` | `train` | Angka 0 (nol) alih-alih huruf alfabet O |
| **O** | `0` | `0_Polos terang_Apple_Iphone 12.JPG` | `train` | Angka 0 (nol) alih-alih huruf alfabet O |

> [!CRITICAL]
> Kasus `E_Baju_Apple_Iphone 11.jpg` yang berada di folder `L` dialokasikan ke **Test Set** dengan ground truth `L`. Model P1 memprediksi kelas `V` ($34,22\%$). Ini adalah bukti konklusif adanya *label noise* yang masuk ke dalam evaluasi performa model!

### 4.3 Poin Konfirmasi Wajib dari Validator Tuli BISINDO
Validator Tuli bersertifikasi wajib memberikan keputusan formal mengenai:
1. Apakah pose diam kelingking tegak sah diakui sebagai representasi alfabet BISINDO untuk huruf J jika konteks modalitas adalah foto diam tunggal?
2. Apakah pose telunjuk mengarah miring sah diakui untuk huruf Z tanpa gerakan lintasan zigzag?
3. Verifikasi apakah berkas `S_Baju_Iphone_14 Pro.jpg` di folder Z memperagakan gestur S atau Z.

---

## 5. Inventaris Metadata Sesi dan Perangkat (Session and Device Metadata Audit)

### 5.1 Ketersediaan Metadata Teknis
- **Metadata EXIF Hardware**: **`NOT AVAILABLE`** (Pengujian pada sampel citra menunjukkan seluruh tag EXIF telah di-strip saat preprocessing Mendeley awal).
- **Metadata Nama Berkas**:
  - Format Token Terstruktur (`<Letter>_<Condition>_<Brand>_<Model>.jpg`): **4.350 citra ($97,49\%$)**.
  - Format Stempel Waktu (`YYYYMMDD_HHMMSS.jpg`): **104 citra ($2,33\%$)**, seluruhnya tertanggal 9 Mei 2024.
  - Format Non-Standar: **8 citra ($0,18\%$)**.
- **Entitas Perangkat Teridentifikasi**: 70 jenis perangkat unik (misalnya `Samsung_A32`, `Apple_Iphone 14 Pro`, `Xiaomi_Redmi Note 9`, `Sony_A7C`).
- **Sesi Unik Teridentifikasi**: 211 sesi unik (kombinasi perangkat + latar belakang/kondisi pencahayaan).

### 5.2 Matriks Status Penetapan Entitas (Assignment Status Matrix)

| Entitas Target | Status Audit | Dasar Bukti & Metodologi |
| :--- | :---: | :--- |
| **1. Known Signer (Peraga)** | **NOT AVAILABLE** | Dataset Mendeley tidak mencatat ID peraga, nama, gender, maupun demografi. Dilarang keras menganggap satu ponsel mewakili satu penandatangan unik. |
| **2. Known Capture Session** | **INFERRED** | Dapat disimpulkan dengan keyakinan tinggi dari token kondisi dan perangkat (misal `Samsung_A55__BACKGROUND BAJU` berisi persis 26 huruf A–Z). |
| **3. Known Capture Device** | **INFERRED** | Tertera pada 97,49% nama berkas mentah. Tidak dapat diverifikasi secara perangkat keras karena ketiadaan EXIF. Berkas stempel waktu (104 citra) berstatus **NOT AVAILABLE**. |
| **4. Source Sequence / Burst Group** | **INFERRED** (untuk 104 citra stempel waktu) / **NOT AVAILABLE** (untuk 4.350 citra token) | Jarak stempel waktu berkisar menit per foto. Tidak ditemukan burst mode sub-detik. |

---

## 6. Rekonsiliasi 17 Pasangan Near-Duplicate Lintas-Split

Audit forensik Phase 2B merekonsiliasi seluruh 17 pasangan dengan dHash $\le 4$ antara Train dan Val/Test:

| Pair ID | Train Sample | Val/Test Sample | Classes | Current Splits | dHash | pHash | Device & Session Info | Visual Classification | Session Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :---: |
| **P01** | `M_0084.jpg` | `N_0083.jpg` | M vs N | Train vs Val | 1 | 9 | `Samsung_M51` (Bebas) | **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P02** | `N_0153.jpg` | `M_0153.jpg` | N vs M | Train vs Val | 2 | 9 | `Galaxy A32 5G` (Polos Terang) | **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P03** | `N_0093.jpg` | `M_0093.jpg` | N vs M | Train vs Val | 3 | 6 | `Redmi Note 9` (Wall Gray) | **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P04** | `F_0146.jpg` | `R_0166.jpg` | F vs R | Train vs Test | 3 | 21 | `Samsung_A32` vs `M51` | **COINCIDENTAL_HASH** | **NOT AVAILABLE** |
| **P05** | `X_0166.jpg` | `V_0147.jpg` | X vs V | Train vs Val | 3 | 27 | `M51` vs `Samsung_A32` | **COINCIDENTAL_HASH** | **NOT AVAILABLE** |
| **P06** | `I_0146.jpg` | `V_0147.jpg` | I vs V | Train vs Val | 3 | 31 | `Samsung_A22` vs `A32` | **COINCIDENTAL_HASH** | **NOT AVAILABLE** |
| **P07** | `V_0091.jpg` | `U_0092.jpg` | V vs U | Train vs Test | 4 | 3 | `Redmi Note 9` (Body Red) | **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P08** | `N_0152.jpg` | `M_0152.jpg` | N vs M | Train vs Test | 4 | 6 | `Samsung_A53 5G` (Polos Terang) | **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P09** | `U_0110.jpg` | `V_0111.jpg` | U vs V | Train vs Test | 4 | 12 | `Iphone 13 Pro Max` (Polos Gelap)| **NEAR_DUPLICATE_GESTURE** | **INFERRED** |
| **P10** | `I_0146.jpg` | `I_0166.jpg` | I vs I | Train vs Test | 4 | 19 | `Samsung_A22` vs `M51` | **SAME_CLASS_INTRA_GESTURE** | **NOT AVAILABLE** |
| **P11** | `U_0166.jpg` | `V_0166.jpg` | U vs V | Train vs Test | 4 | 23 | `Samsung_M51 (2)` (Putih) | **SIMILAR_BACKGROUND_ONLY** | **INFERRED** |
| **P12** | `F_0137.jpg` | `U_0137.jpg` | F vs U | Train vs Test | 4 | 24 | `Infinix Note 30` (Polos Terang) | **SIMILAR_BACKGROUND_ONLY** | **INFERRED** |
| **P13** | `B_0146.jpg` | `D_0146.jpg` | B vs D | Train vs Test | 4 | 25 | `Samsung_A22` (Polos Terang) | **SIMILAR_BACKGROUND_ONLY** | **INFERRED** |
| **P14** | `I_0146.jpg` | `V_0166.jpg` | I vs V | Train vs Test | 4 | 25 | `Samsung_A22` vs `M51` | **COINCIDENTAL_HASH** | **NOT AVAILABLE** |
| **P15** | `O_0147.jpg` | `V_0147.jpg` | O vs V | Train vs Val | 4 | 27 | `Samsung_A22` vs `A32` | **COINCIDENTAL_HASH** | **NOT AVAILABLE** |
| **P16** | `X_0166.jpg` | `I_0166.jpg` | X vs I | Train vs Test | 4 | 27 | `Samsung_M51 (2)` (Putih) | **SIMILAR_BACKGROUND_ONLY** | **INFERRED** |
| **P17** | `X_0166.jpg` | `V_0166.jpg` | X vs V | Train vs Test | 4 | 31 | `Samsung_M51 (2)` (Putih) | **SIMILAR_BACKGROUND_ONLY** | **INFERRED** |

### 6.1 Analisis Khusus Enam Pasangan Near-Duplicate Gesture (P01, P02, P03, P07, P08, P09)
- **Kasus M vs N (P01, P02, P03, P08)**: Memperlihatkan bahwa pose M dan N yang diambil pada sesi yang sama dipisahkan secara acak oleh split P1 (satu di Train, satu di Val/Test). Fitur visual tangan dan latar belakang yang identik menyebabkan model mengalami kebocoran data (*leakage*) dan distorsi akurasi timbal-balik (konfusi M $\leftrightarrow$ N).
- **Kasus U vs V (P07, P09)**: Jarak pHash sangat rendah ($3$ dan $12$). Posisi dua jari yang hampir menempel pada gestur U menyerupai bentuk V di bawah sudut kamera yang sama.
- **Tindakan**: Sampel-sampel ini **tidak dihapus atau diubah** dalam audit ini, namun wajib dimasukkan ke dalam split yang sama (*grouped into the same split*) pada P2.

---

## 7. Desain Pembagian Berbasis Kelompok (Session-Aware Split Design)

### 7.1 Komparasi Strategi Pembagian Data untuk Persiapan P2

| Strategi | Metadata yang Dibutuhkan | Risiko Kebocoran Latar Belakang | Kelayakan Teknis | Representasi 26 Kelas | Status Subjek |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **A. Device-Grouped Split** | Token nama perangkat ($97,5\%$) | **Nol antarsesi perangkat** | **FEASIBLE** | **Lengkap (26/26 di tiap split)** | `SUBJECT_INDEPENDENT_EVALUATION_NOT_VERIFIABLE` |
| **B. Session-Grouped Split** | Token perangkat + latar belakang | Rendah (hanya sensor kamera) | **FEASIBLE** | **Lengkap (26/26 di tiap split)** | `SUBJECT_INDEPENDENT_EVALUATION_NOT_VERIFIABLE` |
| **C. Signer-Grouped Split** | ID penandatangan (*signer_id*) | **Nol total** | **NOT FEASIBLE** | Tidak dapat dijalankan | `NOT AVAILABLE IN DATASET` |
| **D. Combined Signer/Session** | ID penandatangan + sesi | **Nol total** | **NOT FEASIBLE** | Tidak dapat dijalankan | `NOT AVAILABLE IN DATASET` |

### 7.2 Simulasi Empiris Device-Grouped Split (Tanpa Mengubah Data Asli)
Simulasi komputasi pembagian 70 perangkat unik menghasilkan sebaran yang sangat seimbang:
- **Train Split**: $3.144$ citra ($70,5\%$) dari 57 kelompok perangkat.
- **Validation Split**: $712$ citra ($16,0\%$) dari 7 kelompok perangkat.
- **Test Split**: $606$ citra ($13,6\%$) dari 6 kelompok perangkat.
- **Keseimbangan Kelas**: Seluruh 26 kelas hadir lengkap di ketiga split. Pada Test set, setiap kelas memiliki dukungan antara **21 hingga 24 citra**.

---

## 8. Tata Kelola Data Uji (Test-Set Governance Policy)

Untuk menjaga integritas ilmiah dan mencegah kontaminasi evaluasi (*evaluation leakage*):
1. **Preservasi Absolut Test Set P1**: Test set P1 ($N=670$) tidak diubah, tidak disetel ulang, dan tidak dikurangi.
2. **Status Diagnostik Validasi Buta**: Sampel uji yang dievaluasi validator (`VAL-REV-001` s/d `VAL-REV-015`) berstatus **`TEST_SET_DIAGNOSTIC_ONLY`**. Hasil penilaian validator semata-mata digunakan untuk menganalisis akurasi baseline historis.
3. **Larangan Penyetelan Model Berbasis Uji**: Dilarang keras menggunakan umpan balik validator pada sampel test set untuk:
   - Melakukan tuning bobot model atau retraining terarah.
   - Memilih teknik prapemrosesan (*preprocessing selection*).
   - Menyetel hyperparameter model.
4. **Kebijakan Sampel Mislabel pada Test Set**: Jika validator mengonfirmasi bahwa sampel uji salah label (misalnya `E_Baju_Apple_Iphone 11.jpg` di kelas L), sampel tersebut diberi catatan diagnostik pada laporan akhir, namun **label pada test set historis P1 tidak diubah** agar keterbandingan baseline tetap terjaga.

---

## 9. Hambatan Kritis Sebelum P2 (Critical Blockers)

1. **`BLOCKER-1` (Ketiadaan Validasi Manusia)**: Sesi validasi buta oleh validator Tuli BISINDO belum terlaksana. Tanpa penandatanganan resmi validator, koreksi label atau pembersihan sampel tidak memiliki legitimasi linguistik.
2. **`BLOCKER-2` (Kebocoran Antarsesi pada Split P1)**: Evaluasi P1 saat ini terbukti memuat 6 pasangan gestur identik antarsplit (kebocoran Train $\leftrightarrow$ Val/Test). P2 tidak boleh menggunakan split P1.
3. **`BLOCKER-3` (Kebocoran Label pada Lembar Validator)**: Lembar `BLIND_VALIDATOR_REVIEW_SHEET.md` saat ini memuat kolom `Tag Metodologi` yang menampilkan status test set kepada validator. Hal ini harus dihilangkan pada lembar cetak validator.

---

## 10. Rekomendasi Langkah Selanjutnya (Recommended Next Steps)

1. **Revisi Instrumen Cetak Validator**:
   - Terbitkan versi khusus peserta (*participant-facing sheet*) yang menghapus kolom `Tag Metodologi` agar pengujian berstatus *true double-blind*.
2. **Laksanakan Sesi Validasi Buta Pilot**:
   - Eksekusi penelaahan 36 sampel bersama validator Tuli BISINDO dengan lembar kerja terstandarisasi.
3. **Formalisasi Definisi Representasi Huruf J & Z**:
   - Susun panduan singkat bagi validator mengenai penilaian pose kunci statis (*canonical static keyframe*) untuk huruf bergerak.
4. **Rancang Pipeline P2 Berbasis Device-Grouped Split**:
   - Siapkan skrip pembagian data `train_test_split_grouped.py` yang memisahkan seluruh perangkat secara tegas antara Train, Val, dan Test untuk pelatihan P2 mendatang.

---

## 11. Perintah yang Dijalankan (Exact Commands Executed)
Semua skrip verifikasi dijalankan secara terisolasi di direktori scratch:
- `python scratch/audit_validator_package.py`: Verifikasi 36 ID anonim, resolusi berkas fisik, dan keterbacaan Pillow.
- `python scratch/check_tag_mismatch.py`: Audit konsistensi tag metodologi vs split aktual manifest.
- `python scratch/inspect_j_z.py`: Pengecekan sampel kelas J dan Z serta penemuan berkas prefix S.
- `python scratch/check_s_z_hash.py`: Komputasi hash biner perbandingan `S_Baju_Iphone_14 Pro.jpg` di folder S vs folder Z.
- `python scratch/check_prefix_folder_mismatch.py`: Pemindaian 4.462 berkas mentah untuk menemukan 8 anomali prefix nama vs folder kelas.
- `python scratch/check_e_in_l_prediction.py`: Pengecekan riwayat prediksi model P1 terhadap berkas prefix E di folder L.
- `python scratch/audit_metadata.py`: Audit tag EXIF, sebaran token nama perangkat, dan stempel waktu.
- `python scratch/simulate_group_splits.py`: Simulasi algoritma pembagian data berbasis kelompok perangkat (*Device-Grouped Split*).

---

## 12. Jalur Bukti Teknis (Evidence Paths)
- `docs/validation_p2/participant_material/BLIND_VALIDATOR_REVIEW_SHEET.md`
- `docs/validation_p2/PHASE_2A_VISUAL_FORENSIC_REPORT.md`
- `docs/validation_p2/figures/cross_split_17_pairs_contact_sheet.png`
- `docs/validation_p2/figures/high_confidence_18_errors_contact_sheet.png`
- `docs/validation_p2/figures/preprocessing_simulation_comparison.png`
- `scratch/validator_sheet_rows.json`
- `scratch/cross_split_17_pairs.json`
- `scratch/high_conf_18_errors.json`

---

## 13. Keterbatasan & Klaim yang Belum Terverifikasi (Limitations)
- Tidak ada klaim bahwa validator Tuli telah menyetujui pose apa pun pada tahap ini (**PENDING VALIDATOR**).
- Tidak ada klaim bahwa kebocoran peraga telah teratasi (**SUBJECT_INDEPENDENT_EVALUATION_NOT_VERIFIABLE**).
- Tidak ada pelatihan ulang P2 yang dijalankan (**HOLD P2**).

---

## 14. Status Akhir Audit (Final Status)

### Overall Readiness Status:
$$\mathbf{READY\_WITH\_DOCUMENTED\_LIMITATIONS}$$

### Session-Aware Split Feasibility Status:
$$\mathbf{FEASIBLE\_WITH\_LIMITATIONS}$$

