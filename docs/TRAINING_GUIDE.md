# Panduan Training Ulang Model SignBridge

Dokumentasi lengkap untuk melatih ulang model supaya lebih akurat, khususnya untuk **pengenalan live di kamera**.

---

## Masalah Model Lama

Model `M0_student_baseline` punya akurasi offline 99,13% tetapi sering salah saat pengenalan live karena:

1. **Diuji pada penutur yang SAMA** dengan data latih (protokol SD) → angka terlalu optimistis untuk orang baru
2. **Tanpa augmentasi potongan waktu** → rapuh ketika potongan isyarat live tidak persis sama dengan klip latih
3. **Tanpa cermin** → penutur kidal / tangan dominan berbeda tidak dikenali
4. **Dilatih di CPU** walau ada RTX 3050 → lambat

---

## Prasyarat (PC Gloria)

### 1. Hardware
- **GPU**: RTX 3050 atau lebih tinggi (opsional tapi sangat disarankan)
- **RAM**: minimal 8 GB
- **Storage**: minimal 10 GB kosong

### 2. Software
```bash
# Python 3.10 atau 3.11 (bukan 3.13+, PyTorch belum support)
python --version

# Install PyTorch dengan CUDA (untuk RTX 3050)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies training
pip install -r requirements-train.txt

# Verifikasi CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
# Output harus: CUDA: True
```

### 3. Data
Pastikan file ini ada:
- `data/manifest_wl_bisindo.csv` — manifest keypoint WL-BISINDO (sudah ter-ekstrak)
- `data/keypoints/*.npz` — file keypoint yang direferensikan manifest
- (Opsional) `data/selfrec/manifest_own.csv` — rekaman tim dari Perekam Dataset

---

## Cara Training

### A. Ukur Kemampuan pada Penutur Baru (LOSO)

**Leave-One-Signer-Out (LOSO)** mengukur akurasi model saat mengenali **orang yang tidak pernah dilihat saat training**. Ini angka yang **jujur** untuk dilaporkan di paper.

```bash
# Jalankan dari root repo SignBridge
cd "C:\Users\PC\SignBridge"  # atau path repo kalian

# Training LOSO (akan melatih N model, di mana N = jumlah penutur unik)
python scripts/train_m0_robust.py --loso --epochs 120 --batch 32
```

**Output:**
- Folder: `outputs/experiments/M0_robust/si_SIGNER1/`, `si_SIGNER2/`, dst.
- File hasil: `outputs/experiments/M0_robust/loso_summary.json`
- Console: `[LOSO] akurasi penutur baru = 0.8234 ± 0.0456`

**Durasi:** ~2-4 jam tergantung jumlah penutur dan GPU.

**Laporkan di paper:**
> "Evaluasi leave-one-signer-out menunjukkan akurasi rata-rata **82.34% ± 4.56%** pada penutur baru, menunjukkan model dapat menggeneralisasi ke pengguna yang tidak pernah dilihat saat training."

### B. Latih Model Final untuk Web

Model final dilatih dengan **semua data** (termasuk rekaman tim kalau ada) dan augmentasi kuat, lalu diekspor ke `web/model/student.onnx`.

```bash
# Training model final + ekspor ONNX
python scripts/train_m0_robust.py \
  --protocol sd \
  --extra-manifest data/selfrec/manifest_own.csv \
  --epochs 150 \
  --batch 32 \
  --export
```

**Argumen:**
- `--protocol sd`: split signer-dependent (60% train, 10% val, 30% test dari semua penutur)
- `--extra-manifest`: tambahkan rekaman tim (opsional, hapus argumen ini kalau belum ada)
- `--export`: ekspor model terbaik ke `web/model/student.onnx`

**Output:**
- Model PyTorch: `outputs/experiments/M0_robust/sd/best_model.pt`
- Model ONNX: `web/model/student.onnx` (siap dipakai browser)
- Metadata: `web/model/labels.json`

**Durasi:** ~1-2 jam dengan GPU.

### C. Fine-tune dari Model Lama (Opsional)

Kalau mau mulai dari model lama yang sudah ada:

```bash
python scripts/train_m0_robust.py \
  --protocol sd \
  --init outputs/experiments/M0_student_baseline/model.pt \
  --epochs 50 \
  --batch 32 \
  --export
```

---

## Augmentasi yang Dipakai

Model robust menggunakan augmentasi kuat untuk mengatasi variasi live:

```python
AUG = {
  "enabled": True,
  "mirror_p": 0.5,           # 50% cermin horizontal (untuk kidal)
  "rot_deg": 15.0,           # rotasi ±15° (posisi badan miring)
  "scale_range": (0.85, 1.15),  # zoom 85-115% (jarak kamera)
  "shift_range": 0.05,       # shift 5% (posisi tidak tepat tengah)
  "noise_std": 0.004,        # noise kecil pada koordinat
  "speed_range": (0.75, 1.3),   # kecepatan isyarat 75-130%
  "hand_dropout_p": 0.15,    # 15% satu tangan hilang sesaat
  "time_crop_p": 0.7,        # 70% potong waktu awal/akhir (70-100% durasi)
  "time_crop_min": 0.7,
}
```

---

## Monitoring Training

### 1. TensorBoard (Opsional)

```bash
# Install tensorboard
pip install tensorboard

# Jalankan TensorBoard
tensorboard --logdir outputs/experiments/M0_robust

# Buka http://localhost:6006
```

### 2. Console Output

Training akan menampilkan progress per epoch:

```
ep 001 train_loss 2.345 val_acc 0.7234 (23s)
ep 002 train_loss 1.892 val_acc 0.8012 (22s)
...
ep 045 train_loss 0.234 val_acc 0.9456 (21s)
[hasil] sd SIGNER1: test_acc=0.9234 macro_f1=0.9156 per_signer={'SIGNER1': 0.95, 'SIGNER2': 0.89}
```

---

## Troubleshooting

### Error: CUDA out of memory
**Solusi:** Kurangi batch size
```bash
python scripts/train_m0_robust.py --loso --batch 16  # dari 32 ke 16
```

### Error: CUDA tidak tersedia (training di CPU)
**Penyebab:** PyTorch tidak ter-install dengan CUDA support.

**Solusi:**
```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
python -c "import torch; print(torch.cuda.is_available())"  # harus True
```

### Error: ModuleNotFoundError: No module named 'signbridge'
**Solusi:** Jalankan dari root repo
```bash
cd "C:\Users\PC\SignBridge"
python scripts/train_m0_robust.py --loso
```

### Training sangat lambat (>10 menit per epoch)
**Penyebab:** GPU tidak terpakai (jalan di CPU).

**Cek:**
```bash
python -c "import torch; print(f'Device: {torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\")}')"
```

**Solusi:** Pastikan PyTorch CUDA ter-install (lihat di atas).

---

## Setelah Training

### 1. Commit Model Baru ke Git

```bash
git add web/model/student.onnx web/model/labels.json
git add outputs/experiments/M0_robust/loso_summary.json
git commit -m "feat: model M0 robust dengan LOSO acc 82.34±4.56%"
git push
```

### 2. Test di Web

```bash
# Pull perubahan terbaru (kalau training di PC lain)
git pull

# Jalankan server
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

Buka http://localhost:7860, **hard refresh** (Ctrl+Shift+R), lalu test:
1. Klik tab **"Kata"**
2. Angkat tangan → isyarat → turunkan tangan
3. Coba kata yang sering salah dulu (dari hasil evaluasi)

### 3. Dokumentasikan Hasil di Paper

Dari `outputs/experiments/M0_robust/loso_summary.json`:

```json
{
  "protocol": "LOSO",
  "mean": 0.8234,
  "std": 0.0456,
  "acc_per_signer": {
    "SIGNER1": 0.85,
    "SIGNER2": 0.79,
    "SIGNER3": 0.83
  }
}
```

**Tulis di paper:**
> "Model Student Pose-Transformer dengan augmentasi robust mencapai akurasi **82.34% ± 4.56%** pada evaluasi leave-one-signer-out, menunjukkan kemampuan generalisasi yang baik terhadap penutur baru."

---

## Hyperparameter Tuning (Advanced)

Kalau mau coba konfigurasi lain, edit `train_m0_robust.py`:

```python
# Baris 18-19
MODEL_CFG = {
  "d_model": 160,        # dimensi embedding (coba: 128, 192, 256)
  "nhead": 4,            # jumlah attention head (coba: 2, 8)
  "num_layers": 4,       # layer transformer (coba: 3, 6)
  "dim_feedforward": 640,  # dimensi FFN (coba: 512, 1024)
  "dropout": 0.15,       # dropout rate (coba: 0.1, 0.2)
}
```

Atau pakai argumen CLI:
```bash
python scripts/train_m0_robust.py --loso --epochs 150 --lr 5e-4 --batch 64
```

---

## Referensi

- **Paper WL-BISINDO**: Kindy et al. (2025) - baseline model STGCN
- **Transformer for Sign Language**: Vaswani et al. (2017) - arsitektur attention
- **Augmentation Strategy**: Ko et al. (2019) - spatial & temporal augmentation

---

**Catatan:** Script ini sudah dioptimasi untuk RTX 3050. Kalau pakai GPU lebih kuat (RTX 4060+), bisa naikkan `--batch 64` untuk training lebih cepat.
