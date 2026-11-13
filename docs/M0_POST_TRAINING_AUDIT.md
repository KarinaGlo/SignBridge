# LAPORAN AUDIT PASCA-PELATIHAN MODEL M0 STUDENT BASELINE (WL-BISINDO)

| Metadata Audit | Nilai |
|---|---|
| **Tanggal Audit** | 2026-11-08 |
| **Proyek** | SignBridge ASEAN (BISINDO ↔ FSL) |
| **Tahap** | POST-TRAINING AUDIT — M0 Student Baseline (WL-BISINDO) |
| **Branch Git** | `feature/dataset-acquisition` |
| **Git HEAD** | `b38b4da93b525f68edf4a9cfe6eb9331e13582e2` |
| **Auditor** | Senior Machine Learning Engineer, Computer Vision Engineer & Dataset Quality Auditor |
| **Folder Artefak** | `outputs/experiments/M0_student_baseline/` |
| **Status / Verdict Akhir** | **VERIFIED WITH LIMITATIONS** |

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Audit pasca-pelatihan (*post-training audit*) independen telah dilaksanakan terhadap seluruh artefak, log eksekusi, bobot model, integritas data, dan metrik evaluasi dari pelatihan **M0 Student Baseline (WL-BISINDO)**.

Tujuan utama audit ini adalah memvalidasi secara empiris bahwa:
1. Seluruh artefak checkpoint dan metrik benar-benar bersumber dari sesi pelatihan yang sama tanpa manipulasi data.
2. Mekanisme pelatihan (*early stopping*, konvergensi loss, bobot model) berjalan sesuai spesifikasi Kontrak 1 & 3 SignBridge.
3. Insiden *Exit Code 1* pada background task pelatihan (`task-2324`) telah diinvestigasi secara tuntas dan tidak mencemari checkpoint maupun hasil eksperimen.
4. Tidak ada kebocoran data (*data leakage*) berupa video duplikat, kesamaan hash NPZ, maupun tumpang tindih ID rekaman.
5. Metrik evaluasi test set dapat direproduksi ulang (*independently recalculated*) secara 100% presisi dari checkpoint terbaik.
6. Protokol evaluasi diidentifikasi secara jujur dan transparan sebagai **Signer-Dependent (SD)** dan bukan **Signer-Independent (LOSO)**.

Berdasarkan hasil audit komprehensif, status model M0 Student Baseline dinyatakan:
$$\mathbf{VERDICT:}\quad \textbf{VERIFIED WITH LIMITATIONS}$$

---

## 2. INTEGRITAS ARTEFAK & CHECKPOINT MODEL

### 2.1. Inventaris dan Verifikasi Hash Artefak
Seluruh 10 artefak yang dipersyaratkan pada folder `outputs/experiments/M0_student_baseline/` telah diperiksa keberadaan, ukuran fisik, dan checksum SHA-256-nya:

| No | Nama Artefak | Ukuran | Status | SHA-256 Checksum |
|---:|---|---:|:---:|---|
| 1 | `best_model.pt` | 15.35 MB | **VALID** | `17300c0082f4da0e8e7456d9255ec986c7cf6586050b4ec756247c7c09d59a7f` |
| 2 | `last_model.pt` | 15.35 MB | **VALID** | `53fc80d6ca3fa4356e301dff7bb8a816be5d4375b058fb817cb25287515cfb49` |
| 3 | `training_config.yaml` | 0.92 KB | **VALID** | `ff38ea42bf0baee693b4f6204c6ebafb1a20a4ca227fc6ecaa697e87a2ec35f5` |
| 4 | `training_history.csv` | 2.52 KB | **VALID** | `1326c2e3dd7fe8d95159ae0f40d58be31e36f9da229bfbc1a28a381121d556ad` |
| 5 | `evaluation_metrics.json` | 2.21 KB | **VALID** | `510255c2f54a86b36cb8798bf1213eb98bf68936ef11488c035caee0946b2ecf` |
| 6 | `classification_report.csv`| 1.24 KB | **VALID** | `91d9d9f58ea96c148281e58288593be46b0a996da605f6a9e324ef78923a1a35` |
| 7 | `confusion_matrix.png` | 229.28 KB | **VALID** | `68cba50bca808588599426f8d0be42199f36f1c79a4059db0ea374aa387d812b` |
| 8 | `training_loss.png` | 91.37 KB | **VALID** | `26eb0fb130bf702cb9373ebfd944e85dc6fc070055cb1e5b871239f60a927dbe` |
| 9 | `training_accuracy.png` | 91.36 KB | **VALID** | `3dc377507314cebf0766487e4125a07cb6ab063ca6ae5fae0e0a5888d30e3bb4` |
| 10 | `experiment_metadata.json` | 1.10 KB | **VALID** | `375d81b49f57ebbf7ee784869c362b66236b33c5e8c159828d05267b2d56a3e5` |

### 2.2. Verifikasi Parameter & Bobot Checkpoint
Model `StudentPoseTransformer` dimuat secara mandiri menggunakan PyTorch 2.2.2:
- **Konfigurasi Arsitektur**: `num_classes=32`, `d_model=160`, `nhead=4`, `num_layers=4`, `dim_feedforward=640`, `dropout=0.10`.
- **Jumlah Parameter Terhitung**: Tepat **1.335.872 parameter** (100% konsisten dengan rancangan Bab 2.3).
- **Epoch Checkpoint**:
  - `best_model.pt`: Epoch **48** (`val_loss = 0.7375`, `val_acc = 97.78%`).
  - `last_model.pt`: Epoch **58** (`val_loss = 0.7445`, `val_acc = 98.33%`).
- **Divergensi Bobot (Weight Divergence Norm)**:
  $$\|\mathbf{W}_{\text{best}} - \mathbf{W}_{\text{last}}\|_2 = 3.2226 > 0$$
  Hal ini membuktikan secara definitif bahwa `best_model.pt` dan `last_model.pt` adalah dua checkpoint yang berbeda dari urutan epoch yang valid pada run pelatihan yang sama.

---

## 3. AUDIT RIWAYAT TRAINING & INVESTIGASI LOG TASK-2324

### 3.1. Validasi Early Stopping
Berdasarkan pembacaan baris-per-baris file `training_history.csv`:
- Total epoch yang dijalankan: Tepat **58 epoch**.
- Loss validasi terendah tercapai pada **Epoch 48** dengan nilai $0.7375$.
- Sepuluh epoch berikutnya (Epoch 49 hingga 58) mencatatkan nilai loss validasi sebagai berikut:
  `[0.7499, 0.7419, 0.7396, 0.7387, 0.7453, 0.7443, 0.7429, 0.7413, 0.7386, 0.7445]`
- Seluruh 10 epoch berturut-turut tersebut memiliki nilai `val_loss` lebih tinggi dari epoch 48 ($> 0.7375$).
- **Kesimpulan**: Logika *Early Stopping* dengan parameter `patience = 10` terbukti dieksekusi secara presisi dan objektif.

### 3.2. Investigasi Mendalam Exit Code 1 pada Task-2324
Pada akhir eksekusi background task `task-2324`, sistem melaporkan exit code 1. Pemeriksaan mendalam terhadap file log asli (`task-2324.log`) mengungkapkan:
1. Pelatihan berjalan sukses penuh dari Epoch 1 hingga Epoch 58 tanpa hambatan.
2. Checkpoint `best_model.pt` dan `last_model.pt` telah selesai disimpan ke disk.
3. Evaluasi akhir model terbaik terhadap validation set dan test set telah dieksekusi tuntas dan metrik telah tercatat di memori.
4. Grafik konvergensi `training_loss.png` dan `training_accuracy.png` telah di-render dan disimpan.
5. Pada baris 444 dari file `scripts/train_m0_baseline.py`, tepat ketika hendak menulis file `experiment_metadata.json`, terjadi eksepsi:
   ```text
   Traceback (most recent call last):
     File "scripts/train_m0_baseline.py", line 444, in <module>
       "sklearn_version": sklearn.__version__,
                          ^^^^^^^
   NameError: name 'sklearn' is not defined
   ```
   Penyebab: Modul `sklearn` diimpor di baris atas script menggunakan sintaks `from sklearn.metrics import (...)` tanpa pernyataan `import sklearn` global.
6. **Dampak terhadap Integritas**: **NOL / TIDAK ADA DAMPAK**. Checkpoint model, riwayat loss, metrik evaluasi, dan matriks konfusi telah selesai dihitung dan disimpan sebelum error penulisan metadata ini terjadi. File `experiment_metadata.json` kemudian difinalisasi secara rapi melalui `scratch/finalize_m0_eval.py`.

---

## 4. AUDIT DATA LEAKAGE & DISTRIBUSI SIGNER

Pemeriksaan kebocoran data dilakukan dengan membandingkan irisan himpunan (*set intersection*) antara subset Train (960 sampel), Validation (180 sampel), dan Test (460 sampel) menggunakan manifest `manifest_wl_bisindo.csv` dan sidecar `manifest_wl_bisindo_source_metadata.csv`:

### 4.1. Verifikasi Kebocoran Berkas Fisik
| Uji Kebocoran | Train vs Val | Train vs Test | Val vs Test | Status |
|---|:---:|:---:|:---:|:---:|
| **Sample / Video ID Overlap** | 0 | 0 | 0 | **ZERO LEAKAGE (PASS)** |
| **Video File SHA-256 Overlap** | 0 | 0 | 0 | **ZERO LEAKAGE (PASS)** |
| **Keypoint NPZ SHA-256 Overlap**| 0 | 0 | 0 | **ZERO LEAKAGE (PASS)** |

Tidak ada satupun file rekaman fisik atau file ekstraksi keypoint yang digunakan secara ganda lintas split.

### 4.2. Distribusi Signer & Klasifikasi Protokol
Pemeriksaan tabulasi silang (*cross-tabulation*) antara identitas penanda isyarat (`signer`) dan split dataset menghasilkan sebaran berikut:

| Identitas Signer | Sampel Train | Sampel Validation | Sampel Test | Total Video |
|---|---:|---:|---:|---:|
| **SIGNER0** | 72 | 12 | 36 | 120 |
| **SIGNER1** | 252 | 52 | 116 | 420 |
| **SIGNER2** | 252 | 52 | 116 | 420 |
| **SIGNER3** | 192 | 32 | 96 | 320 |
| **SIGNER4** | 192 | 32 | 96 | 320 |
| **TOTAL** | **960** | **180** | **460** | **1.600** |

### Penetapan Protokol Ilmiah:
- Kelima signer (SIGNER0 s.d. SIGNER4) terdistribusi di ketiga split (Train, Val, Test).
- Meskipun tidak ada video rekaman fisik yang berulang, subjek penanda isyarat yang sama muncul pada subset latih dan uji.
- **Kesimpulan Resmi Auditor**: Eksperimen ini adalah protokol **Signer-Dependent (SD)**. Hasil akurasi **TIDAK DAPAT** diklaim sebagai performa generalisasi terhadap pengguna baru yang belum pernah dilihat (*Signer-Independent / LOSO*). Klaim performa harus secara eksplisit mencantumkan batasan ini.

---

## 5. REPRODUKSI DAN REKALKULASI INDEPENDEN TEST SET

Auditor memuat ulang `best_model.pt` dan dataset uji melalui `SignDataset` (split="test", protocol="sd", $N = 460$) menggunakan script audit mandiri `scratch/audit_m0_post_training.py` tanpa mengandalkan cache hasil sebelumnya:

| Metrik Evaluasi | Nilai Dilaporkan (Reported) | Nilai Rekalkulasi Independen | Selisih (Delta) | Kesimpulan |
|---|---:|---:|---:|:---:|
| **Test Loss (Cross-Entropy)** | 0.6820 | 0.6820 | 0.0000 | **100% PERSIS** |
| **Test Top-1 Accuracy** | 99.13% | 99.13% | 0.00% | **100% PERSIS** |
| **Test Top-5 Accuracy** | 100.00% | 100.00% | 0.00% | **100% PERSIS** |
| **Macro Precision** | 99.18% | 99.18% | 0.00% | **100% PERSIS** |
| **Macro Recall** | 99.12% | 99.12% | 0.00% | **100% PERSIS** |
| **Macro F1-Score** | 99.12% | 99.12% | 0.00% | **100% PERSIS** |
| **Weighted F1-Score** | 99.13% | 99.13% | 0.00% | **100% PERSIS** |

- Total prediksi benar pada Test Set: **456 dari 460 sampel** (hanya 4 sampel keliru terklasifikasi).
- 26 dari 32 kelas mencapai F1-Score sempurna $100.00\%$.
- Tiga kelas dengan F1-Score terendah yang memerlukan perhatian pada model lanjutan:
  1. `KAPAN` (F1: 89.66%) — tertukar dengan `DIMANA` karena kesamaan orientasi telapak tangan dan pergerakan pergelangan tangan.
  2. `DIMANA` (F1: 92.31%) — tertukar dengan `KAPAN`.
  3. `CARI` (F1: 96.55%) — tertukar dengan `LIHAT` akibat kedekatan area artikulasi wajah/mata.

---

## 6. AUDIT LINGKUNGAN (ENVIRONMENT) & RISIKO REPRODUCIBILITY

### 6.1. Konfigurasi Runtime yang Digunakan
- **Python Binary**: `C:\Users\PC\Downloads\Semester 5\ML\.venv_m0\Scripts\python.exe`
- **Python Version**: `Python 3.11.0b4` (pre-release beta build, 11 Juli 2022).
- **NumPy Version**: `1.26.4` (C-API release, pin strict).
- **PyTorch Version**: `2.2.2+cpu`.
- **Komputasi Hardware**: 100% CPU execution (tanpa akselerasi CUDA).

### 6.2. Analisis Risiko Interpreter Python Beta
Pemeriksaan menunjukkan bahwa sistem host menjalankan `Python 3.11.0b4` (versi beta sebelum rilis stabil Python 3.11.0 GA pada Oktober 2022).
- **Risiko**: Interpreter pra-rilis memiliki potensi inkonsistensi ABI internal pada ekstensi C (seperti yang sempat memicu error pada kombinasi PyTorch 2.2.2 dan NumPy 2.4.6).
- **Mitigasi yang Telah Dilakukan**: Isolasi penuh dalam virtual environment `.venv_m0` dengan mengunci NumPy tepat pada versi `1.26.4` terbukti berhasil meredam konflik ABI sehingga training dan inferensi berjalan tanpa crash numerik.
- **Rekomendasi untuk Produksi / M1**: Untuk pipeline deployment produksi, staging Docker, atau eksperimen lanjutan skala besar, interpreter Python pada mesin host sangat disarankan diperbarui ke rilis stabil resmi (**Python 3.11.9+** atau **Python 3.10.x LTS**).

---

## 7. REKONSILIASI KETIDAKSESUAIAN (DISCREPANCY ANALYSIS)

Pemeriksaan silang antara laporan pelatihan sebelumnya (`M0_STUDENT_BASELINE_TRAINING_REPORT.md`) dengan audit pasca-pelatihan ini:
1. **Nilai Metrik**: Ditemukan **0 selisih metrik**. Seluruh akurasi, F1-score, loss, dan parameter count cocok hingga digit desimal keempat.
2. **Penamaan Label Kelas**: Pada run awal sebelum error baris 444, classification report sempat menggunakan indeks numerik 0-31. Auditor telah merekonsiliasi dan memastikan bahwa pemetaan string kelas pada `classification_report.csv` dan `confusion_matrix.png` 100% konsisten dengan daftar resmi `BISINDO_32_GLOSSES` / `WLBISINDO_LABELS`.
3. **Klaim Protokol**: Audit memperjelas dan mengoreksi bahwa tingginya akurasi ($99.13\%$) terjadi di bawah protokol **Signer-Dependent**. Laporan resmi SignBridge tidak boleh mengklaim performa ini setara dengan inferensi *unseen signers*.

---

## 8. MATRIKS RISIKO & MITIGASI UNTUK MODEL SELANJUTNYA (M1 / M2)

| Aspek | Temuan Audit M0 | Risiko pada Tahap M1/M2 | Rencana Mitigasi |
|---|---|---|---|
| **Signer Independence** | Protokol Signer-Dependent ($99.13\%$) | Performa diprediksi turun signifikan jika diuji pada signer baru (unseen subject) | Rancang evaluasi Leave-One-Signer-Out (LOSO) pada pengujian komparatif M1/M2 |
| **Keseimbangan Kelas Dominan Tangan** | 28 kelas satu tangan, 4 kelas dua tangan | Model rentan mengabaikan representasi tangan kiri | Pertahankan spatial masking valid mask $\mathbf{P} \odot \mathbf{M}$ dan evaluasi performa per kelas 2-tangan secara terpisah |
| **Kelas Mirip (Confusing Pairs)** | `KAPAN` vs `DIMANA` ($89.66\%$ vs $92.31\%$) | Ambiguitas klasifikasi pada isyarat tanya berkecepatan mirip | Eksplorasi fitur diferensial kecepatan tingkat tinggi atau multi-scale temporal pooling |
| **Runtime Interpreter** | Python 3.11.0b4 beta | Potensi kendala kompatibilitas saat memasang pustaka akselerasi tambahan | Pertahankan `.venv_m0` yang terisolasi dan agendakan upgrade host Python ke rilis stabil |

---

## 9. KESIMPULAN & VONIS AKHIR (FINAL VERDICT)

Audit pasca-pelatihan menyatakan bahwa seluruh proses training M0 Student Baseline telah memenuhi kaidah rekayasa perangkat lunak dan metodologi riset pembelajaran mesin yang ketat, reproducible, bebas dari pemalsuan data, serta zero data leakage.

```
================================================================================
                    SIGNBRIDGE POST-TRAINING AUDIT VERDICT                      
================================================================================
  Status:           VERIFIED WITH LIMITATIONS                                   
  Artefak:          10 / 10 Lengkap, Checkpoint Valid (Best Epoch 48, Last 58)  
  Parameter Count:  1,335,872 Parameter (Sesuai Desain Bab 2.3)                
  Data Leakage:     0 Overlap (Video SHA, NPZ SHA, Sample ID)                   
  Evaluasi:         Test Acc = 99.13% | Macro F1 = 99.12% | Top-5 = 100.00%    
  Rekalkulasi:      100.00% Reproducible (Delta = 0.0000%)                      
  Batasan:          1. Protokol Signer-Dependent (SD), bukan LOSO/Unseen Signer 
                    2. Domain Terbatas Isolated Word (ISLR 32 Kelas)            
                    3. Runtime Python 3.11.0b4 Beta Memerlukan Pinning Khusus   
================================================================================
```

*Auditor merekomendasikan model M0 Student Baseline diterima sebagai baseline resmi (anchor benchmark) proyek SignBridge ASEAN untuk subset kata terisolasi WL-BISINDO.*

