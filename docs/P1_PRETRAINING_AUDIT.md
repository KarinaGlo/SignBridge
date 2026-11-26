# AUDIT PRA-TRAINING EKSPERIMEN I1-P1: TRANSFER LEARNING MOBILENETV3-SMALL

> **Dokumen**: `docs/P1_PRETRAINING_AUDIT.md`  
> **Modul**: Modality Image — Klasifikasi Alfabet BISINDO A–Z (I1)  
> **Target Arsitektur**: `torchvision.models.mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)`  
> **Tanggal Audit**: 13 November 2026  
> **Auditor**: Senior Machine Learning Engineer, SignBridge ASEAN  
> **Status Audit**: **`VERIFIED & APPROVED FOR TRAINING`**

---

## 1. TUJUAN AUDIT

Audit pra-training ini dilakukan sebelum mengeksekusi **Eksperimen I1-P1** untuk memastikan integritas dataset, mencegah kebocoran data (*data leakage*), memvalidasi konsistensi pipeline preprocessing, membedah arsitektur P0 vs model resmi torchvision, serta menginvestigasi diskrepansi diagnostik prediksi P0 secara transparan dan empiris.

---

## 2. AUDIT DATASET & INTEGRITAS MANIFEST

### A. Manifest dan Distribusi Sampel
Manifest yang digunakan adalah manifest resmi P0 yang telah dibersihkan dari duplikasi lintas-kelas:
- **Lokasi Manifest**: [`data/processed/bisindo_alphabet/manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/manifest.csv)
- **Manifest Audit Preprocessing**: [`data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv)
- **Total Citra Valid**: **4.462 citra** (4 citra duplikat ambigu B vs E dan D vs P telah dieksklusi pada Tahap 4).

### B. Distribusi Split Dataset (Random Seed 42, Stratified)
| Split | Jumlah Citra | Persentase | Status Penggunaan |
|---|:---:|:---:|---|
| **Train** | $3.123$ | $70,00\%$ | Optimasi gradien bobot (Tahap 1 & Tahap 2) |
| **Validation** | $669$ | $15,00\%$ | Monitoring loss, evaluasi metrik, dan early stopping |
| **Test** | $670$ | $15,00\%$ | Evaluasi akhir independen (tidak disentuh saat training) |
| **TOTAL** | **$4.462$** | **$100,00\%$** | Konsisten $100\%$ |

### C. Representasi dan Mapping Label Kelas A–Z
- **Jumlah Kelas**: Tepat $26$ kelas alfabet (`A` sampai `Z`).
- **Mapping Label Indeks**:
  `A: 0, B: 1, C: 2, D: 3, E: 4, F: 5, G: 6, H: 7, I: 8, J: 9, K: 10, L: 11, M: 12, N: 13, O: 14, P: 15, Q: 16, R: 17, S: 18, T: 19, U: 20, V: 21, W: 22, X: 23, Y: 24, Z: 25`.
- **Konsistensi Label**: Terverifikasi identik antara `signbridge.constants.FINGERSPELL_26_LABELS`, manifest split, pipeline data loader, model output layer ($26$ logit), dan dictionary metrik evaluasi.
- **Support per Kelas**: Setiap kelas memiliki rata-rata $171\text{--}172$ sampel total, dengan $25\text{--}26$ sampel pada Test Set (Kelas A memiliki 24 sampel pada Test Set karena pengurangan duplikat).

---

## 3. AUDIT DATA LEAKAGE (KEBOCORAN DATA)

Pemeriksaan hash SHA-256 dan path fisik dilakukan terhadap seluruh pasangan split data untuk memastikan isolasi absolut:

```python
# Evaluasi irisan hash SHA-256 antar-split
Train ∩ Validation : 0 duplikasi (Himpunan kosong)
Train ∩ Test       : 0 duplikasi (Himpunan kosong)
Validation ∩ Test  : 0 duplikasi (Himpunan kosong)
```

- **Pemeriksaan File Asal (`source_path`)**: $\emptyset$ (Tidak ada gambar asal yang sama berada di lebih dari satu split).
- **Pemeriksaan Path Preprocessed (`path`)**: $\emptyset$ (Tidak ada file fisik yang tumpang tindih).
- **Pemeriksaan Checksum SHA-256**: $\emptyset$ (Tidak ada file dengan konten identik di split berbeda).
- **Kesimpulan Leakage**: **ZERO DATA LEAKAGE** terverifikasi $100\%$.

---

## 4. AUDIT PREPROCESSING & KONSISTENSI NORMALISASI

### A. Format Input Fisik
- **Dimensi**: $224 \times 224$ piksel, saluran RGB (3 kanal).
- **Format Penyimpanan**: File `.npy` (float32 ternormalisasi) dan citra `.jpg` resolusi tinggi yang disimpan di [`data/processed/bisindo_alphabet/`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/).

### B. Skema Normalisasi ImageNet
Bobot pra-latih `torchvision.models.mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)` dilatih pada ImageNet-1K dengan parameter normalisasi standar:
- **Mean $(\mu)$**: $[0.485, 0.456, 0.406]$
- **Standard Deviation $(\sigma)$**: $[0.229, 0.224, 0.225]$

### C. Verifikasi Pencegahan Double-Normalization
- File `.npy` mentah menyimpan array citra rentang $[0.0, 1.0]$.
- Normalisasi diterapkan tepat **satu kali** saat transformasi tensor PyTorch:
  $$\text{Tensor}_{\text{norm}} = \frac{X - \mu}{\sigma}$$
- Saat inferensi atau evaluasi, citra diubah ke float $[0.0, 1.0]$ lalu dinormalisasi dengan formula yang sama tanpa penambahan transformasi ganda.

---

## 5. AUDIT KOMPARASI ARSITEKTUR: MODEL P0 VS TORCHVISION RESMI

| Aspek Arsitektur | Model P0 (`MobileNetV3SmallClassifier`) | Model P1 (`torchvision.models.mobilenet_v3_small`) |
|---|:---|:---|
| **Asal Arsitektur** | Custom CNN buatan lokal di `train_image.py` | Implementasi resmi PyTorch / Torchvision |
| **Inverted Residual Blocks** | 5 blok depthwise separable konvensional | 11 blok Inverted Residual bertingkat (*Bottleneck*) |
| **Squeeze-and-Excitation (SE)** | **TIDAK ADA** | **TERSEDIA** pada sebagian besar blok intermediate |
| **Aktivasi Non-linear** | Hardswish standar | Hardswish & ReLU teroptimasi per-stage |
| **Total Parameter** | $265.826$ parameter ($\approx 0,266\text{ M}$) | **$1.529.866$ parameter ($\approx 1,53\text{ M}$)** |
| **Bobot Awal (Initialization)** | Random weight initialization (*from scratch*) | **Pretrained ImageNet-1K (`DEFAULT`)** |
| **Ukuran Checkpoint** | $\approx 1,08\text{ MB}$ | $\approx 6,15\text{ MB}$ |
| **Kompatibilitas Bobot** | `state_dict` custom tidak kompatibel dengan torchvision | Kompatibel penuh dengan PyTorch Torch Hub / Weights API |

> **Temuan Kritis**: Model P0 bukanlah arsitektur MobileNetV3-Small resmi, melainkan miniatur CNN 5-blok yang dilatih dari nol (*from scratch*). Ketiadaan fitur visual pra-latih dan kapasitas representasi yang sangat kecil ($0,266\text{ M}$) menjadi penyebab utama terjadinya *overfitting* parah pada P0 (Train Loss $0,57$ vs Val Loss $4,32$). Model P1 mengadopsi arsitektur resmi torchvision berkapasitas $1,53\text{ M}$ parameter dengan fitur representasi kaya dari $1,2$ juta citra ImageNet.

---

## 6. AUDIT INVESTIGATIF PREDIKSI P0 (DISKREPANSI 26 VS 23 KELAS)

Laporan P0 sebelumnya mencatat dua pernyataan yang tampak kontradiktif:
1. Ringkasan eksekutif menyatakan model keluar dari *class collapse* dan memprediksi ke-26 kelas.
2. Bagian diagnostik menyatakan hanya 23 dari 26 kelas yang memiliki prediksi.

### Pembuktian Empiris Langsung pada Checkpoint P0 (`runs/image_i1_mobilenetv3_p0/best.pt`):
Evaluasi langsung terhadap $670$ citra Test Set menghasilkan data aktual berikut:

1. **Jumlah Kelas Unik pada Output Prediksi (`y_pred`)**: **26 kelas**.
   Semua indeks $0$ sampai $25$ (`A` sampai `Z`) benar-benar muncul sebagai output prediksi model.
   - Distribusi frekuensi prediksi:
     - `K`: $53$ kali, `Y`: $43$ kali, `G`: $40$ kali, `O`, `Q`, `R`: $35$ kali, `T`: $34$ kali, `L`: $32$ kali, `Z`: $31$ kali, `J`: $29$ kali, `W`: $27$ kali, `F`, `I`, `X`: $26$ kali, `U`: $25$ kali, `V`: $23$ kali, `A`: $21$ kali, `P`: $20$ kali, `D`: $18$ kali, `E`: $17$ kali, `H`: $16$ kali, `N`, `S`: $13$ kali, `C`: $12$ kali, `M`: $11$ kali, `B`: $9$ kali.
   - Kelas yang tidak pernah diprediksi sama sekali: **TIDAK ADA ($\emptyset$)**.

2. **Analisis True Positives (TP) dan Recall**:
   Walaupun semua 26 kelas pernah diprediksi, terdapat **3 kelas** yang prediksinya **tidak pernah benar sekalipun** (*True Positives* $= 0$):
   - **Kelas C**: Diprediksi $12$ kali, namun semuanya salah (TP = $0$, Support = $25$, Recall = $0,00\%$, Precision = $0,00\%$).
   - **Kelas D**: Diprediksi $18$ kali, namun semuanya salah (TP = $0$, Support = $26$, Recall = $0,00\%$, Precision = $0,00\%$).
   - **Kelas N**: Diprediksi $13$ kali, namun semuanya salah (TP = $0$, Support = $26$, Recall = $0,00\%$, Precision = $0,00\%$).

3. **Kesimpulan Resolusi Diskrepansi**:
   - Pernyataan "26 kelas diprediksi" merujuk pada **frekuensi kemunculan kelas di `y_pred`** (model tidak mengalami *single-class collapse* seperti model M0 lama yang hanya memprediksi 1 kelas).
   - Pernyataan "23 kelas diprediksi" merujuk pada **jumlah kelas yang memiliki Recall $> 0$** ($23$ kelas berhasil ditebak benar minimal 1 kali, sedangkan $3$ kelas yaitu C, D, N memiliki Recall $0\%$).
   - Hal ini membuktikan bahwa P0 tidak mengalami keruntuhan kelas total, tetapi mengalami kebingungan klasifikasi parah pada fitur-fitur gestur tertentu.

---

## 7. RENCANA EKSEKUSI P1

1. **Arsitektur Model**: `signbridge/image/models/mobilenetv3_p1.py` menggunakan `torchvision.models.mobilenet_v3_small` dengan bobot ImageNet ter-cache lokal, mengganti head klasifikasi `classifier[3]` menjadi `nn.Linear(1024, 26)`.
2. **Strategi Training 2-Tahap**:
   - **Stage 1 (Feature Extraction)**: Freeze backbone `features`, latih classifier baru ($lr = 10^{-3}$, AdamW, weight decay $10^{-4}$).
   - **Stage 2 (Fine-Tuning)**: Unfreeze layer atas backbone (`features[9:]` dan pooling), latih dengan learning rate rendah ($lr_{\text{backbone}} = 10^{-5}, lr_{\text{head}} = 10^{-4}$, Cosine Annealing).
3. **Augmentasi Khusus Bahasa Isyarat**: Rotasi kecil ($\pm 10^\circ$), sedikit affine scale ($0,95\text{--}1,05$), ColorJitter ringan. **TANPA HORIZONTAL FLIP** untuk mempertahankan polaritas tangan kiri/kanan.
4. **Early Stopping**: Berdasarkan `Validation Macro F1` (patience = 5 epoch).
5. **Output Terisolasi**: Seluruh artefak disimpan di `runs/image_i1_mobilenetv3_p1/` dan `docs/figures/p1/` tanpa menyentuh artefak P0 maupun model produksi.

Audit selesai dengan sukses. Seluruh parameter terverifikasi aman untuk dilanjutkan ke tahap implementasi dan training.

