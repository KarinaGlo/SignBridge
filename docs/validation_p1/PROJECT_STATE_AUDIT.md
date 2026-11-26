# LAPORAN AUDIT STATUS PROYEK TERBARU (PROJECT STATE AUDIT)
## Image Modality I1-P1 (BISINDO Alphabet) — SignBridge ASEAN
### Audit Pascakualitas Gate Persiapan Sesi Validasi Buta & Transisi ke EDA Internal

**Dokumen**: `docs/validation_p1/PROJECT_STATE_AUDIT.md`  
**Proyek**: SignBridge ASEAN  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small I1-P1)  
**Dokumen Acuan Terkini**:
1. [`docs/validation_p1/FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md)
2. [`configs/image_i1_mobilenetv3_p1.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p1.yaml)
3. [`configs/image_i1_mobilenetv3_p0.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p0.yaml)
4. Berkas artefak evaluasi P1 di [`runs/image_i1_mobilenetv3_p1/`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/)  
**Tanggal Audit**: 16 November 2026  
**Auditor**: Senior Machine Learning Engineer & Dataset Quality Auditor  
**Sifat Audit**: **READ-ONLY INSPECTION (Nol Modifikasi Kode, Model, Dataset, & Manifest)**  
**Status Tahap Validasi**: **`PENDING VALIDATOR`**  
**Status Tahap Pilot**: **`PILOT_HOLD`**  
**Progres Pengumpulan Data Eksternal**: **`NOT STARTED` ⚪ (0 / 780 foto valid)**  

---

## 1. RINGKASAN STATUS PROYEK PASCA-QUALITY GATE

Berdasarkan audit komprehensif pada dokumen `FINAL_PRE_SESSION_QUALITY_GATE_REPORT.md`, seluruh rangkaian persiapan operasional untuk sesi validasi buta (*blind validation*) referensi gestur BISINDO Kelas A telah dievaluasi dengan status resmi:

- **Quality Gate Kesiapan**: **`READY_WITH_LIMITATIONS` ⚠️**  
  Seluruh materi peraga visual bebas label (`BLIND_STIMULUS_DECK.pdf`), kartu peraga JPEG, lembar randomisasi seed, dan checklist diagnostik notulis telah tersedia lengkap. Status bersyarat diberikan karena validitas linguistik hakiki hanya dapat ditentukan oleh manusia penutur asli Tuli melalui sesi tatap muka nyata.
- **Rekomendasi Sesi Lapangan**: **`CONDITIONAL_GO_FOR_HUMAN_SESSIONS`**  
  Sesi diizinkan berjalan secara kondisional dengan kepatuhan penuh terhadap SOP mitigasi kebocoran informasi dan pengacakan urutan stimulus.
- **Status Validator**: **`PENDING VALIDATOR` ⏳**  
  Seluruh instrumen isian respon, profil, dan informed consent dibiarkan 100% kosong (*unfilled*). Belum ada data validator yang direkam.
- **Status Tahap Pilot Lapangan**: **`PILOT_HOLD` 🚫**  
  Pengambilan fisik 10 foto kelas A penutur EXT_S01 ditangguhkan mutlak hingga sesi nyata selesai dan disetujui dalam *re-examination*.
- **Manifest Eksternal**: `data/external/bisindo_validation/external_manifest.csv` berukuran 163 bytes, memuat 14 kolom resmi dan **0 baris data fiktif**.
- **Progres Data Eksternal**: **`NOT STARTED` ⚪ (0 / 780 foto valid)**.

---

## 2. AUDIT KONFIGURASI MODEL & PIPELINE PELATIHAN

Pemeriksaan konfigurasi dilakukan terhadap dua tahap iterasi model image I1:

### A. Konfigurasi Eksperimen P1 ([`configs/image_i1_mobilenetv3_p1.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p1.yaml))
- **Arsitektur**: `mobilenet_v3_small_pretrained` (Transfer Learning dari bobot ImageNet `weights=DEFAULT`).
- **Dimensi Input**: $224 \times 224$ piksel, 3 kanal warna (RGB).
- **Jumlah Kelas**: 26 kelas alfabet (A–Z).
- **Dropout Classifier Head**: 0.2.
- **Strategi Pelatihan Dua Tahap (Two-Stage Training)**:
  - *Stage 1 (Feature Extraction)*: 5 epoch, batch size 32, learning rate $1 \times 10^{-3}$, weight decay $1 \times 10^{-4}$, label smoothing 0.05. Backbone dibekukan (*frozen*), hanya classifier head yang dilatih.
  - *Stage 2 (Differential Fine-Tuning)*: 15 epoch, batch size 32, backbone LR $1 \times 10^{-5}$, head LR $1 \times 10^{-4}$, min LR $1 \times 10^{-6}$, unfreeze mulai dari layer `features[9:]`, patience early stopping 5.
- **Manifest Pelatihan**: `data/processed/bisindo_alphabet/manifest.csv` (4.462 sampel).

### B. Konfigurasi Eksperimen P0 ([`configs/image_i1_mobilenetv3_p0.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/image_i1_mobilenetv3_p0.yaml))
- **Arsitektur**: `mobilenet_v3_small` (Pelatihan dari nol / *train from scratch* tanpa bobot pretrained).
- **Hasil Historis**: Mengalami *training collapse* dengan akurasi uji hanya 7,61% dan Macro F1 7,50%. Hal ini membuktikan kebutuhan absolut transfer learning pada korpus ukuran sedang (~4.400 sampel).

---

## 3. INVENTARISASI ARTEFAK EVALUASI P1 DI REPOSITORI

Pemeriksaan fisik pada direktori [`runs/image_i1_mobilenetv3_p1/`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/) membuktikan keberadaan lengkap seluruh artefak evaluasi:

| Nama Berkas Artefak | Ukuran | Format | Deskripsi & Isi Berkas |
|---|:---:|:---:|---|
| `best.pt` | 6.302.825 B | PyTorch Checkpoint | Bobot model terbaik pada epoch 18 (Val F1: 59,58%). |
| `last.pt` | 6.302.825 B | PyTorch Checkpoint | Bobot model epoch terakhir (epoch 20). |
| `classification_report.txt` | 1.654 B | Teks Laporan | Precision, recall, F1-score, dan support per kelas (Test N=670). |
| `confusion_matrix.csv` | 1.650 B | Matriks CSV | Tabel confusion matrix $26 \times 26$ angka bulat. |
| `confusion_matrix.png` | 107.847 B | Gambar Plot | Visualisasi heatmap matriks konfusi uji. |
| `predictions.csv` | 63.050 B | Data CSV | 670 baris prediksi individual memuat `confidence` dan `correct`. |
| `prediction_distribution.png`| 61.389 B | Gambar Plot | Plot distribusi prediksi per kelas. |
| `sample_predictions_grid.png`| 1.840.670 B| Gambar Plot | Grid $5 \times 5$ sampel visual prediksi benar vs salah. |
| `training_accuracy_curves.png`| 77.884 B | Gambar Plot | Kurva train vs validation accuracy selama 20 epoch. |
| `training_f1_curves.png` | 61.514 B | Gambar Plot | Kurva train vs validation macro F1. |
| `training_loss_curves.png` | 81.359 B | Gambar Plot | Kurva train vs validation cross-entropy loss. |
| `training_history.csv` | 1.576 B | Data CSV | Log metrik numerik per epoch (loss, acc, f1, lr). |
| `training_summary.json` | 5.434 B | Data JSON | Ringkasan terstruktur lengkap metrik P1, komparasi P0, dan benchmark latensi. |

---

## 4. VERIFIKASI KRIPTOGRAFIS TIGA ARTEFAK MODEL

Audit hash SHA-256 memverifikasi bahwa model checkpoint dan file ONNX produksi tidak mengalami alterasi:

```powershell
Get-FileHash -Algorithm SHA256 "runs/image_i1_mobilenetv3_p1/best.pt", "runs/image_i1_mobilenetv3/best.pt", "web/model/fingerspell.onnx"
```

| Artefak Model | Hash Baseline Resmi | Hash Aktual Terverifikasi | Status Kecocokan |
|---|---|---|:---:|
| **P1 Checkpoint** (`runs/.../best.pt`) | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | **100% MATCH (UTUH) ✅** |
| **P0 Checkpoint** (`runs/.../best.pt`) | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | **100% MATCH (UTUH) ✅** |
| **Production ONNX** (`web/.../fingerspell.onnx`) | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | **100% MATCH (UTUH) ✅** |

---

## 5. KESIMPULAN AUDIT STATUS PROYEK

1. Seluruh artefak persiapan sesi validasi buta referensi gestur BISINDO Kelas A telah siap secara operasional dan berada dalam kondisi aman (*safe state*).
2. Repositori memiliki artefak evaluasi P1 yang lengkap, kredibel, dan siap dianalisis secara mendalam tanpa perlu training ulang.
3. Analisis teknis internal (EDA dataset dan error analysis P1) dapat dilanjutkan secara independen untuk mempersiapkan fondasi eksperimen P2 di masa mendatang.

