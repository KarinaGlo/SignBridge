# PHASE 2C.6 — HUMAN VALIDATION HANDOFF & RESPONSE INGESTION READINESS AUDIT
## SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)
### Module: Image Modality I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)

> [!IMPORTANT]
> **GOVERNANCE & READ-ONLY AUDIT MANDATE**
> - **Execution Mode**: Strictly READ-ONLY terhadap dataset asli, checkpoint model, dan kode produksi.
> - **Firewall Protection**: 19 sampel `TEST_SET_DIAGNOSTIC_ONLY` terisolasi penuh dari 17 sampel `TRAIN_COHORT`.
> - **Zero Synthetic Data Mandate**: Tidak ada pembuatan data tanggapan palsu/rekaan.
> - **Current Status**: **`WAITING_FOR_HUMAN_VALIDATION`**
> - **P2 Training Status**: **`STRICT HOLD`**

---

## 1. EXECUTIVE SUMMARY & VERDICT

Berdasarkan serangkaian audit biner, verifikasi struktural otomatis, analisis algoritma statistik, dan inspeksi tata kelola data:

# **`OVERALL VERDICT: READY_FOR_MANUAL_HANDOFF`**

Paket distribusi eksternal untuk **Validator A** dan **Validator B** telah diverifikasi secara teknis dan metodologis, bebas dari kebocoran label/model, dan siap diserahkan secara manual oleh fasilitator lapangan.

### Matriks Klasifikasi Status Temuan Audit:

| Kategori Status Temuan | Jumlah Aspek | Ringkasan Status |
| :--- | :---: | :--- |
| **1. Verified by Automated Checks** | 8 Aspek | **`PASS (100%)`** — Integritas biner, struktur paket, skema CSV, 0 kebocoran, unit tests 15/15 lulus. |
| **2. Requires Human Confirmation** | 5 Aspek | **`PENDING FIELD ACTION`** — Penyerahan fisik, penandatanganan Informed Consent, pencegahan bias. |
| **3. Not Yet Performed** | 4 Aspek | **`SCHEDULED`** — Pengisian mandiri oleh validator, pengumpulan CSV, ingest data mentah. |
| **4. Blocked Pending Validator Responses** | 3 Aspek | **`BLOCKED (STRICT HOLD)`** — Kalkulasi IRR nyata, adjudikasi Validator C, pelatihan model P2. |

---

## 2. VERIFIED BY AUTOMATED CHECKS (VERIFIKASI OTOMATIS)

Pemeriksaan otomatis dilakukan secara langsung pada repositori lokal `D:\SEMESTER 5\ML\Projek_1`:

### 2.1. Inventaris & Kelengkapan Paket Distribusi
- **Paket Validator A** ([`docs/validation_p2/phase_2c/distribution/validator_A/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_A/)):
  - **Total File**: Tepat **40 file**.
  - **Citra Stimulus**: 36 file JPG (`stimulus_images/VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
  - **Dokumen Panduan**: 3 file Markdown (`PANDUAN_VALIDATOR_BISINDO.md`, `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`, `VALIDATOR_PROTOCOL.md`).
  - **Template CSV**: 1 file `VALIDATOR_A_RESPONSE_TEMPLATE.csv` (SHA-256: `80d68a3c47f7ea9bf96964b3fc82c2c1e82994ab5a72793d89c99ea29c92db13`).
- **Paket Validator B** ([`docs/validation_p2/phase_2c/distribution/validator_B/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_B/)):
  - **Total File**: Tepat **40 file**.
  - **Citra Stimulus**: 36 file JPG (`stimulus_images/VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
  - **Dokumen Panduan**: 3 file Markdown (`PANDUAN_VALIDATOR_BISINDO.md`, `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`, `VALIDATOR_PROTOCOL.md`).
  - **Template CSV**: 1 file `VALIDATOR_B_RESPONSE_TEMPLATE.csv` (SHA-256: `55b35d922a087c2650c4b4fc2bbbfdca77edbde102db7f095754f1c2ce965e3c`).
- **Status Audit**: **`PASS (100% STRUCTURE MATCH)`**.

### 2.2. Verifikasi Kriptografis 36 Stimulus vs Master Manifest
- **Manifest Sumber**: [`docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv).
- **Hasil Pemeriksaan**:
  - Kecocokan Paket A vs Master Manifest: **36/36 (100% MATCH)**.
  - Kecocokan Paket B vs Master Manifest: **36/36 (100% MATCH)**.
  - Kesetaraan Biner Paket A vs Paket B: **36/36 (0 difference, 100% IDENTIK)**.
  - Verifikasi khusus `VAL-REV-036`: SHA-256 `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` (**MATCH** pada manifest, Paket A, dan Paket B).
- **Status Audit**: **`PASS (100% CRYPTOGRAPHIC INTEGRITY)`**.

### 2.3. Verifikasi Template CSV Respons
- **Header Baku**: `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` (Persis sama di kedua file).
- **Jumlah Baris**: Tepat 37 baris (1 baris header + 36 rekaman data).
- **Kesesuaian ID**: Tepat 36 ID unik dari `VAL-REV-001` hingga `VAL-REV-036` tanpa lompatan atau duplikasi.
- **Isolasi Kode**: Paket A seluruhnya `VAL-A`, Paket B seluruhnya `VAL-B`.
- **Status Respons**: Kolom keputusan kosong murni (36/36 belum diisi, 0 rekaman sintetik).
- **Status Audit**: **`PASS (100% BLANK & VALID)`**.

### 2.4. Audit Kebocoran Informasi (*Zero Leakage Check*)
Pencarian teks menyeluruh (*deep scan*) dijalankan terhadap seluruh berkas dokumen dan CSV di Paket A dan B:
- Kata kunci yang dipindai: `TRAIN_COHORT`, `TEST_SET_DIAGNOSTIC_ONLY`, `ground_truth`, `INTERNAL_SAMPLE_MAPPING`, `confidence_score`, `MobileNetV3`, `prediction`.
- **Temuan**: **0 temuan kebocoran**.
- Metadata citra EXIF: **100% stripped/bersih**.
- **Status Audit**: **`PASS (ZERO LEAKAGE)`**.

### 2.5. Integritas Baseline Checkpoint P1 & Model ONNX
Pemeriksaan SHA-256 terhadap model baseline membuktikan tidak ada perubahan bobot:
- **PyTorch P1 Checkpoint** ([`runs/image_i1_mobilenetv3_p1/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/best.pt)):
  $$\text{SHA-256} = \texttt{83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9} \quad (\textbf{INTACT})$$
- **ONNX Web Model** ([`web/model/fingerspell.onnx`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/fingerspell.onnx)):
  $$\text{SHA-256} = \texttt{1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105} \quad (\textbf{INTACT})$$
- **Status Audit**: **`PASS (BASELINE UNTOUCHED)`**.

### 2.6. Eksekusi Unit Test Suite Otomatis
Eksekusi uji regresi automated pipeline melalui perintah:
```powershell
pytest tests/test_phase_2c_irr.py -v
```
- **Hasil**: **15 passed in 10.22s (Exit Code: 0)**.
- Seluruh 15 skenario (keputusan identik, divergen, huruf alternatif sama/beda, flag ambiguitas, trap varians nol, deteksi berkas kosong/parsial, deteksi ID duplikat/salah/terpotong, kode validator salah, dan ketiadaan huruf koreksi pada `INCORRECT`) terverifikasi bekerja sesuai spesifikasi.
- **Status Audit**: **`PASS (100% TESTS PASSED)`**.

---

## 3. REQUIRES HUMAN CONFIRMATION (MEMERLUKAN TINDAKAN MANUSIA)

Aspek-aspek berikut secara mendasar berada di luar domain verifikasi berkas kode dan wajib dikonfirmasi langsung oleh tim fasilitator manusia:

| Parameter Kepatuhan | Tindakan Lapangan yang Wajib Dilakukan | Status Saat Ini |
| :--- | :--- | :---: |
| **Waktu & Tanggal Distribusi** | Fasilitator mencatat waktu (jam/menit) dan tanggal fisik saat paket diserahkan ke validator. | `PENDING FIELD ACTION` |
| **Informed Consent Fisik** | Fasilitator wajib memberikan penjelasan hak subjek dan memperoleh tanda tangan lembar *Informed Consent* sebelum validator membuka paket stimulus. | `PENDING SIGNATURE` |
| **Media Transfer Terisolasi** | Memastikan transfer file dilakukan secara offline (USB flash drive aman/kabel terisolasi) tanpa mengunggah paket ke forum/repositori publik. | `PENDING FIELD ACTION` |
| **Pencegahan Bias Fasilitator** | Fasilitator mematuhi protokol: tidak boleh menyebutkan label huruf, tidak boleh memberi petunjuk non-verbal, dan tidak boleh mengomentari pilihan validator. | `PENDING PROTOCOL ADHERENCE` |
| **Penjagaan Independensi Sesi** | Memastikan Validator A dan Validator B mengisi lembar evaluasi secara mandiri tanpa saling berkomunikasi atau membandingkan jawaban. | `PENDING PROTOCOL ADHERENCE` |

---

## 4. NOT YET PERFORMED (BELUM DILAKSANAKAN)

Tahapan operasional yang dijadwalkan berikutnya setelah penyerahan fisik:
1. **Sesi Evaluasi Mandiri oleh Validator**: Validator A dan Validator B meninjau 36 gambar stimulus dan mengisi lembar kerja CSV.
2. **Pengembalian Berkas Respons CSV**: Validator menyerahkan kembali berkas CSV respons (ditargetkan dalam rentang waktu $H+3$).
3. **Penghitungan SHA-256 Pra-Buka**: Fasilitator langsung menghitung hash SHA-256 seketika saat berkas diterima dari validator sebelum berkas dibuka oleh aplikasi apa pun.
4. **Pengarsipan Mentah (*Raw Ingestion*)**: Berkas asli disalin ke direktori aman [`docs/validation_p2/phase_2c/raw_responses/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/raw_responses/) dan diberi atribut *read-only*.

---

## 5. BLOCKED PENDING VALIDATOR RESPONSES (TERBLOKIR MENUNGGU RESPONS)

Tahapan berikut **DIBLOKIR SECARA KETAT** dan tidak boleh dieksekusi sebelum respons nyata diterima:
1. **Perhitungan Metrik Inter-Rater Reliability Nyata**:
   - Dilarang membuat kesimpulan reliabilitas inter-rater ($\kappa$, $P_o$, Correct Letter Agreement) berdasarkan data dummy atau asumsi.
2. **Sidang Adjudikasi Bersama Validator C (`VAL-C`)**:
   - Adjudikasi hanya dapat dijalankan setelah daftar divergensi riil diekstrak oleh script dari respons Validator A dan B yang valid.
3. **Pelatihan Model Phase 2 (P2 Retraining)**:
   - Pelatihan ulang model MobileNetV3-Small berstatus **`STRICT HOLD`**.
   - Model tidak boleh dilatih ulang sebelum hasil validasi manusia dipisahkan secara disiplin antara kohort latih dan kohort uji.

---

## 6. AUDIT STATISTIK & KETERBATASAN METODOLOGIS ENGINE ANALISIS

Tinjauan mendalam dilakukan terhadap implementasi engine kalkulasi [`scripts/validation_p2/calculate_inter_rater_agreement.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p2/calculate_inter_rater_agreement.py):

### 6.1. Formulasi Matematika yang Diimplementasikan
1. **Kesepakatan Teramati (*Observed Agreement*)**:
   $$P_o = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(y_{a,i} = y_{b,i}), \quad N = 36$$
2. **Kesepakatan Peluang (*Chance Agreement*)**:
   $$P_e = \sum_{k \in \mathcal{C}} \left( \frac{n_{a,k}}{N} \right) \cdot \left( \frac{n_{b,k}}{N} \right), \quad \mathcal{C} = \{\text{AMBIGUOUS}, \text{CORRECT}, \text{INCORRECT}, \text{UNDETERMINABLE}\}$$
3. **Nominal Cohen's Kappa Unweighted**:
   $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   Diimplementasikan menggunakan pustaka scikit-learn dengan parameter `labels=labels` eksplisit, menjamin ukuran matriks kontingensi $4 \times 4$ konsisten sekalipun ada kategori yang bernilai nol (tidak dipilih oleh kedua validator).
4. **Penanganan Kasus Varians Nol (*Zero-Variance Trap*)**:
   Jika kedua validator sepakat 100% pada satu kategori seragam ($P_o = 1.0, P_e = 1.0$), penyebut $1 - P_e = 0$ menghasilkan bentuk tak tentu $\frac{0}{0}$. Script secara eksplisit menangani kondisi ini dengan menetapkan $\kappa = \text{None}$ dan status `UNDEFINED_ZERO_VARIANCE`, sehingga mencegah kegagalan runtime (*division by zero*).
5. **Kesepakatan Huruf Kondisional (*Conditional Correct Letter Agreement*)**:
   Dievaluasi secara eksklusif pada subset sampel di mana kedua validator memilih `INCORRECT`:
   $$\text{Letter Agreement Rate} = \frac{\sum_{i \in \text{Both Incorrect}} \mathbb{I}(\text{let}_{a,i} = \text{let}_{b,i})}{|\text{Both Incorrect}|}$$
   Jika $|\text{Both Incorrect}| = 0$, rate ditetapkan sebagai `None` dengan pelaporan denominator eksplisit.

### 6.2. Keterbatasan Rumus Confidence Interval yang Wajib Didokumentasikan
Script menggunakan rumus pendekatan asimptotik (Fleiss et al.) untuk Standard Error dan 95% Confidence Interval:
$$\text{SE}(\kappa) \approx \sqrt{\frac{P_o (1 - P_o)}{N (1 - P_e)^2}}, \quad \text{CI}_{95\%} = \kappa \pm 1.96 \cdot \text{SE}(\kappa)$$

> [!WARNING]
> **KETERBATASAN METODOLOGIS ASUMSI ASIMPTOTIK PADA SAMPEL KECIL ($N=36$)**
> - **Varians Umum vs Pendekatan Sederhana**: Rumus di atas merupakan aproksimasi varians di sekitar hipotesis nol ($H_0: \kappa = 0$). Rumus varians sampel besar penuh (Fleiss, Cohen, & Everitt, 1969) melibatkan suku-suku probabilitas marjinal orde lebih tinggi dan sel non-diagonal.
> - **Distribusi Miring pada $N=36$**: Dengan ukuran sampel $N=36$, pendekatan kurva normal untuk Confidence Interval rentan terhadap bias jika proporsi salah satu kategori sangat dominan (misal mayoritas sampel bernilai `CORRECT`).
> - **Kondisi Batas Ekstrem**: Jika $P_o \to 1.0$, $\text{SE}(\kappa) \to 0$ sehingga confidence interval dapat menyusut secara semu (*collapsed interval*).
> - **Rekomendasi Publikasi**: Kelulusan 15 unit tests membuktikan kode bebas dari kesalahan sintaksis dan runtime, **namun tidak menjamin normalitas statistik pada sampel kecil**. Untuk keperluan publikasi ilmiah atau laporan akhir, estimasi interval berbasis *bootstrap resampling* (misal $B=2.000$ iterasi) disarankan untuk mendampingi nilai CI analitik ini.

---

## 7. DATA FIREWALL & ATURAN KOHORT

Pemisahan 36 sampel purposif dijaga secara ketat dalam metadata internal:
* **`TRAIN_COHORT` (17 Sampel)**:
  - `VAL-REV-016`, `018`, `019`, `020`, `021`, `022`, `023`, `024`, `026`, `027`, `028`, `029`, `030`, `033`, `034`, `035`, `036`.
  - Hasil adjudikasi validator pada kelompok ini diizinkan untuk digunakan sebagai bahan perbaikan label data latih P2.
* **`TEST_SET_DIAGNOSTIC_ONLY` (19 Sampel)**:
  - `VAL-REV-001` s/d `015`, `017`, `025`, `031`, `032`.
  - **FIREWALL TOTAL**: Hasil evaluasi kelompok ini **DILARANG DIGUNAKAN** untuk melatih ulang model, tuning hyperparameter, memilih arsitektur, maupun mengubah ambang batas deteksi. Kelompok ini hanya boleh dilaporkan sebagai tolok ukur reliabilitas generalisasi eksternal.

---

## 8. KESIMPULAN & TAHAPAN AKSI SELANJUTNYA

Semua kriteria teknis persiapan distribusi telah terpenuhi secara sempurna:
1. Paket distribusi eksternal A dan B telah siap di folder masing-masing.
2. Log distribusi [`VALIDATOR_DISTRIBUTION_EXECUTION_LOG.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/VALIDATOR_DISTRIBUTION_EXECUTION_LOG.md) telah disiapkan dengan tempat pencatatan lengkap.
3. SOP penerimaan [`RESPONSE_INGESTION_INTEGRITY_PROCEDURE.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/RESPONSE_INGESTION_INTEGRITY_PROCEDURE.md) telah disiapkan beserta folder karantina.
4. Engine analisis statistik telah tervalidasi dan siap mengeksekusi data riil saat tersedia.

**Langkah Selanjutnya**:
- Fasilitator riset lapangan melakukan serah terima paket secara manual dan privat kepada Validator A dan Validator B, mengawal pengisian lembar *Informed Consent*, dan memastikan tidak ada pembocoran label maupun sugesti jawaban.
- Status proyek tetap: **`WAITING_FOR_HUMAN_VALIDATION`**.
- Status pelatihan P2 tetap: **`STRICT HOLD`**.

