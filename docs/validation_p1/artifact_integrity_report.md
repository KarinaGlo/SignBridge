# LAPORAN INTEGRITAS ARTEFAK EKSPERIMEN I1-P1 (TAHAP A)

> **Dokumen**: `docs/validation_p1/artifact_integrity_report.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Model Target**: `runs/image_i1_mobilenetv3_p1/best.pt`  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Integritas**: **`PASSED & VERIFIED`** (Seluruh 10 Berkas Utuh dan Terverifikasi)

---

## 1. TUJUAN AUDIT ARTEFAK

Memverifikasi integritas fisik, struktur parameter, dan konsistensi checksum SHA-256 dari seluruh file hasil eksperimen **I1-P1: MobileNetV3-Small Pretrained ImageNet** sebelum audit metrik dan evaluasi lanjutan dilakukan.

---

## 2. INVENTARISASI BERKAS & CHECKSUM SHA-256

Setiap file dihitung nilai cryptographic hash SHA-256 dan ukuran fisiknya untuk memastikan tidak ada file yang rusak, dimodifikasi, atau terpotong:

| No | Lokasi File | Ukuran Fisik | SHA-256 Checksum | Status Integritas |
|:---:|:---|:---:|:---|:---:|
| 1 | `runs/image_i1_mobilenetv3_p1/best.pt` | $6.302.825\text{ B}$ ($6,01\text{ MB}$) | `83c6a0933c8e1a2097ce6fa1198d8578826ed37731c18137c057fea129affee9` | **VALID** |
| 2 | `runs/image_i1_mobilenetv3_p1/last.pt` | $6.302.825\text{ B}$ ($6,01\text{ MB}$) | `4565b05ea2e774fa4750d4e6909fe46ac1bc7f29a9eb863f6eb174af90dee8f6` | **VALID** |
| 3 | `runs/image_i1_mobilenetv3_p1/training_history.csv` | $1.576\text{ B}$ | `9c4bf8855c8a7749d8c821a0c06321f0a881ccf8014dd65227ecf8cd77c34d91` | **VALID** |
| 4 | `runs/image_i1_mobilenetv3_p1/training_config.yaml` | $719\text{ B}$ | `b5236c20fdb807ee027f088cbe6797340a2d9704c8c0f5417729b7cb5f10adae` | **VALID** |
| 5 | `runs/image_i1_mobilenetv3_p1/training_summary.json` | $5.434\text{ B}$ | `d944b443f74d2d3d62daf0d0ed4426d1999a79ddbde7fddbc28b58c7da79dcb6` | **VALID** |
| 6 | `runs/image_i1_mobilenetv3_p1/classification_report.txt` | $1.654\text{ B}$ | `56996a7fb3c799e2d8bf543ffcf1b56981f9a5e091f0df78f01716e23974ba63` | **VALID** |
| 7 | `runs/image_i1_mobilenetv3_p1/confusion_matrix.csv` | $1.650\text{ B}$ | `c10b457690bdba0f84408b1fa2566561a7db2f236c6880c344da709cafb75fc5` | **VALID** |
| 8 | `runs/image_i1_mobilenetv3_p1/predictions.csv` | $63.050\text{ B}$ | `a4eda7dc143b11a70384f82935b2e271cde61800f0e32f6f4ad9f66d129677b2` | **VALID** |
| 9 | `configs/image_i1_mobilenetv3_p1.yaml` | $977\text{ B}$ | `876f00bd59793c8fb6c07e373498440a70d1061f475d76102c97064e3640cddf` | **VALID** |
| 10 | `signbridge/image/models/mobilenetv3_p1.py` | $5.173\text{ B}$ | `f4b9809dcfc33630c47c7a1218f214e2382cfde3d9766327d9bbc53c98e1881c` | **VALID** |

---

## 3. BEDAH STRUKTUR CHECKPOINT (`best.pt`)

Checkpoint `runs/image_i1_mobilenetv3_p1/best.pt` berhasil dimuat menggunakan PyTorch CPU tanpa peringatan korupsi:

1. **Top-Level Dictionary Keys**:
   - `['epoch', 'stage', 'model_state_dict', 'val_acc', 'val_f1', 'config']`
2. **Karakteristik Training Asal**:
   - `epoch`: **18**
   - `stage`: `"stage2"` (Fine-Tuning stage)
   - `val_acc`: $0,6023916292974589$ ($60,24\%$)
   - `val_f1`: $0,5958015813833096$ ($59,58\%$)
   - Konsisten $100\%$ dengan data log pada `training_history.csv` di baris Epoch 18.
3. **Struktur Parameter `model_state_dict`**:
   - Jumlah tensor parameter: **244 tensor**.
   - Bobot classifier terakhir (`backbone.classifier.3.weight`): Shape `torch.Size([26, 1024])`.
   - Bias classifier terakhir (`backbone.classifier.3.bias`): Shape `torch.Size([26])`.
   - Output logit berjumlah tepat **26 kelas**.
4. **Verifikasi Checkpoint Terakhir (`last.pt`)**:
   - `epoch`: **20**
   - `stage`: `"stage2"`
   - Total epoch pelatihan adalah 20 epoch. Checkpoint `best.pt` berasal dari epoch 18, membuktikan bahwa mekanisme best checkpoint tracking berjalan sesuai fungsinya.

---

## 4. KESIMPULAN TAHAP A

Seluruh artefak eksperimen I1-P1 berada dalam kondisi sempurna, lengkap, dan tidak mengalami korupsi data. SHA-256 yang tercatat di atas menjadi patokan absolut selama rangkaian validasi berikutnya.

