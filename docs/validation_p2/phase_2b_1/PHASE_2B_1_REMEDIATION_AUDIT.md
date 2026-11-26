# LAPORAN AUDIT REMEDIASI PAKET VALIDATOR & REGISTER ANOMALI DATA (PHASE 2B.1)
## Modality Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Ringkasan Eksekutif (Executive Summary)

### 1.1 Mandat & Tujuan Phase 2B.1
Laporan ini merupakan penyelesaian resmi dari tahap **Phase 2B.1 — Validator Package Remediation & Label Anomaly Register** pada modul **Image Modality I1 (BISINDO Alphabet Fingerspelling A–Z)**, proyek *SignBridge ASEAN*. 

Tahap ini dirancang khusus untuk memulihkan (*remediation*) integritas metodologis paket validasi buta sebelum didistribusikan kepada validator Tuli BISINDO, menuntaskan catatan hambatan kritis dari laporan `docs/validation_p2/PHASE_2B_PREPARATION_AUDIT.md`, serta menyusun register tata kelola anomali dataset secara formal.

### 1.2 Ringkasan Hasil Remediasi
1. **Sanitasi Total Lembar Kerja Peserta**: Telah diterbitkan lembar kerja baru khusus peserta (`VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`) yang **100% bersih dari kebocoran informasi**. Seluruh tag metodologi (`TEST_SET_DIAGNOSTIC_ONLY`, `TRAIN_COHORT`), label kelas asli, tebakan model AI, skor probabilitas confidence, nama arsitektur, nama split, dan jalur internal telah dieliminasi total.
2. **Isolasi Folder Citra Stimulus**: Seluruh 36 citra uji disalin ke subfolder anonim `stimulus_images/` dengan penamaan murni berbasis kode anonim (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`). Langkah ini mengeliminasi kebocoran nama folder (seperti `/K/K_0152.jpg` yang membocorkan huruf K).
3. **Pemisahan Kunci Dekripsi Peneliti**: Kunci pemetaan internal (`INTERNAL_SAMPLE_MAPPING.md`) diisolasi secara ketat dan terpisah dari materi peserta.
4. **Register Anomali Terstruktur**:
   - Register Anomali Label (`LABEL_ANOMALY_REGISTER.md`): Mendokumentasikan 8 kasus ketidaksesuaian awalan berkas (*prefix-folder mismatch*) pada dataset mentah Mendeley.
   - Register Kemiripan Lintas-Split (`NEAR_DUPLICATE_REGISTER.md`): Mendokumentasikan 6 pasangan kritis berstatus `CROSS_SPLIT_SIMILARITY_CANDIDATE`.
   - Register Representasi Huruf Dinamis (`JZ_REPRESENTATION_REGISTER.md`): Menyusun 7 kasus dan pertanyaan linguistik untuk huruf J dan Z.
5. **Protokol Standar Validasi**: Menetapkan panduan operasional multi-validator dengan mekanisme adjudikasi pihak ketiga (*third-party adjudication*) dan batas toleransi kesepakatan inter-rater Fleiss/Cohen's Kappa.
6. **Hasil Pengujian Otomatis**: **9 dari 9 pemeriksaan sistematis berstatus `PASS` (100% Lolos)**.

---

## 2. Struktur Berkas yang Diterbitkan pada Phase 2B.1

Seluruh artefak hasil remediasi ditempatkan secara terpusat pada direktori baru:
[`docs/validation_p2/phase_2b_1/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/)

| No | Berkas yang Diterbitkan | Tipe Berkas | Target Pembaca | Deskripsi & Fungsi |
| :-: | :--- | :---: | :---: | :--- |
| 1 | [`VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md) | Markdown | **Peserta / Validator** | Lembar penilaian buta steril tanpa kebocoran informasi apa pun. |
| 2 | [`INTERNAL_SAMPLE_MAPPING.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md) | Markdown | **Peneliti Internal** | Kunci pemetaan dekripsi antara ID anonim dengan label ground truth dan model. |
| 3 | [`LABEL_ANOMALY_REGISTER.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/LABEL_ANOMALY_REGISTER.md) | Markdown | **Dataset Governance** | Register resmi 8 anomali awalan nama berkas vs folder kelas. |
| 4 | [`NEAR_DUPLICATE_REGISTER.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/NEAR_DUPLICATE_REGISTER.md) | Markdown | **Model Audit** | Register 6 pasangan kemiripan lintas-split (M/N dan U/V). |
| 5 | [`JZ_REPRESENTATION_REGISTER.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/JZ_REPRESENTATION_REGISTER.md) | Markdown | **Linguistic Review** | Register evaluasi konvensi citra diam huruf dinamis J dan Z. |
| 6 | [`VALIDATOR_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md) | Markdown | **SOP Operasional** | Standar prosedur operasional pelaksanaan validasi buta multi-penilai. |
| 7 | [`PHASE_2B_1_REMEDIATION_AUDIT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/PHASE_2B_1_REMEDIATION_AUDIT.md) | Markdown | **Audit Report** | Laporan audit menyeluruh pemenuhan remediasi metodologis. |
| 8 | `stimulus_images/` (36 berkas `.jpg`) | Direktori Gambar | **Peserta / Validator** | Berkas citra $224 \times 224$ RGB bernilai hash identik, dinamai `VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`. |

---

## 3. Hasil Verifikasi Otomatis Kesiapan Paket (Automated Verification)

Pemeriksaan otomatis dijalankan melalui script `scratch/run_automated_phase2b1_audit.py` untuk menguji integritas teknis seluruh artefak:

| Check ID | Parameter Pemeriksaan Teknis | Syarat Ambang Batas | Nilai Teramati | Status |
| :---: | :--- | :--- | :---: | :---: |
| **CHK-01** | Keberadaan dan keterbacaan 6 dokumen utama | Seluruh berkas ada & ukuran $>0$ | $6/6$ berkas terbaca utuh | **PASS** |
| **CHK-02** | Keunikan & kelengkapan 36 baris tabel peserta | Tepat 36 baris, 36 ID unik | 36 baris, 36 ID unik | **PASS** |
| **CHK-03** | Sanitasi tag metodologi pada lembar peserta | $0$ tag (`TEST_SET_DIAGNOSTIC_ONLY`, dll) | $0$ tag ditemukan | **PASS** |
| **CHK-04** | Sanitasi kebocoran label, prediksi, & jalur internal | $0$ referensi model, confidence, jalur data | $0$ kebocoran terdeteksi | **PASS** |
| **CHK-05** | Integritas folder citra stimulus anonim | 36 berkas `.jpg`, dimensi $224 \times 224$, RGB | 36 berkas verified $224 \times 224$ RGB | **PASS** |
| **CHK-06** | Kelengkapan kunci pemetaan internal peneliti | 36 baris lengkap terpetakan ke label/split | 36 baris terpetakan lengkap | **PASS** |
| **CHK-07** | Kelengkapan Register Anomali Label | Tepat 8 kasus anomali awalan nama berkas | 8 kasus unik tercatat | **PASS** |
| **CHK-08** | Kelengkapan Register Near-Duplicate Lintas Split | Tepat 6 pasangan kemiripan berstatus resmi | 6 pasangan unik tercatat | **PASS** |
| **CHK-09** | Kelengkapan Register Representasi Huruf J dan Z | Kasus representasi terstruktur lengkap | 7 kasus unik tercatat | **PASS** |

---

## 4. Analisis Tata Kelola Register Khusus (Special Governance Registers)

### 4.1 Register Anomali Label (Prefix-Folder Mismatches)
Dari 8 kasus yang terdaftar pada `LABEL_ANOMALY_REGISTER.md`, kasus paling kritis secara metodologis adalah **`ANOM-LBL-002` (`E_Baju_Apple_Iphone 11.jpg` di folder `L`)**:
- Berkas ini berada dalam folder `L` pada dataset mentah Mendeley dan teralokasi ke **Test Set** P1 dengan ground truth label `L`.
- Model P1 memprediksi kelas `V` ($34,22\%$).
- Kasus ini membuktikan bahwa kesalahan prediksi model P1 pada test set sebagian dipicu oleh cacat anotasi (*label noise*) pada data sumber.
- **Aturan Tata Kelola**: Awalan nama berkas `E_` **TIDAK BOLEH** langsung dianggap sebagai ground truth baru. Status ditetapkan sebagai **`VALIDATOR_REVIEW_REQUIRED`** hingga dinilai langsung oleh penutur asli BISINDO.

### 4.2 Register Kandidat Kemiripan Lintas-Split (Cross-Split Candidates)
Enam pasangan yang terdaftar pada `NEAR_DUPLICATE_REGISTER.md` (`CAND-DUP-01` s/d `CAND-DUP-06`, meliputi P01, P02, P03, P07, P08, P09):
- Membuktikan secara komputasional bahwa stratified random splitting per-citra pada P1 memisahkan gestur yang diambil berturutan dari satu perangkat ke dalam Train dan Val/Test.
- **Ketentuan Terminologi**: Digunakan istilah resmi **`CROSS_SPLIT_SIMILARITY_CANDIDATE`**. Pasangan ini tidak boleh serta-merta dinyatakan sebagai "confirmed duplicate" atau "signer leakage" tanpa bukti visual validator dan metadata identitas peraga.
- **Solusi P2**: Wajib dikelompokkan bersama dalam satu split pada pembagian data berbasis kelompok perangkat (*Device-Grouped Split*).

### 4.3 Register Representasi Huruf J dan Z
- Mengonfirmasi bahwa modalitas Image I1 adalah **citra diam tunggal (*static frame*)**.
- Tim pengembang model secara etis dan metodologis **dilarang memutuskan sendiri** konvensi representasi statis huruf dinamis.
- Seluruh 7 kasus pertanyaan linguistik pada `JZ_REPRESENTATION_REGISTER.md` diserahkan kepada validator Tuli BISINDO pada sesi evaluasi kualitatif.

---

## 5. Kebijakan Tata Kelola Data Uji (Test-Set Governance & Anti-Contamination Policy)

Untuk menjamin standar integritas saintifik tertinggi:
1. **Pemisahan Tujuan Diagnostik**: Sebanyak 19 sampel uji yang diperiksa validator semata-mata berfungsi untuk mendiagnosis apakah kegagalan model P1 bersumber dari arsitektur atau label noise data sumber.
2. **Larangan Kontaminasi Model P2**:
   - Dilarang keras memasukkan 19 sampel uji ini ke dalam data pelatihan P2.
   - Dilarang keras menggunakan hasil penilaian sampel uji untuk memilih hyperparameter atau menentukan threshold confidence P2.
   - Dilarang keras melakukan tuning model secara terarah (*targeted fine-tuning*) pada sampel yang teridentifikasi salah label dalam uji coba.
3. **Preservasi Baseline Historis**: Hasil akurasi test set P1 ($61,19\%$) tetap dipertahankan sebagai baseline historis resmi proyek SignBridge ASEAN.

---

## 6. Keterbatasan Audit & Pernyataan Kepatuhan (Limitations & Compliance)

1. **Kepatuhan Read-Only Mutlak**: Seluruh dataset mentah, citra olahan, manifest pelatihan, checkpoint model (`best.pt`, `last.pt`, `model.onnx`), konfigurasi YAML, pipeline preprocessing, dan skrip produksi berstatus **100% UNTOUCHED**.
2. **Ketiadaan Klaim Persetujuan Validator**: Audit ini **TIDAK MENGKLAIM** bahwa validator telah menyetujui pose apa pun pada saat ini. Status keterlibatan manusia tetap berstatus **`PENDING VALIDATOR`**.
3. **Ketiadaan Klaim Independensi Peraga**: Karena ketiadaan metadata penandatangan pada dataset Mendeley, proyek secara jujur menyatakan status **`SUBJECT_INDEPENDENT_EVALUATION_NOT_VERIFIABLE`**.
4. **P2 Training Tetap Tertahan**: Pelatihan ulang P2 **TIDAK DIJALANKAN** sebelum sesi validasi buta selesai dan disahkan oleh komunitas Tuli BISINDO.

---

## 7. Keputusan Akhir Audit (Final Readiness Status)

Berdasarkan keberhasilan pemenuhan seluruh 9 kriteria verifikasi otomatis, eliminasi total kebocoran data pada lembar peserta, ketersediaan citra stimulus anonim mandiri, serta formalisasi seluruh register anomali data:

$$\mathbf{READY\_FOR\_VALIDATOR\_DISTRIBUTION}$$

> [!TIP]
> **Rekomendasi Operasional**:
> Berkas [`VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md) beserta folder pendamping [`stimulus_images/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/stimulus_images/) telah memenuhi standar kerahasiaan buta ganda (*double-blind standard*) dan dapat segera didistribusikan kepada validator Tuli BISINDO independen untuk pelaksanaan sesi evaluasi resmi.

