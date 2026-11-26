# 🚀 SignBridge Quick Start Guide

> **Panduan Cepat untuk Memulai dalam 30 Menit**

---

## 📌 Ringkasan Pipeline

```
DATA SOURCE → INGESTION → PREPROCESSING → MODELING → DEPLOYMENT
     │            │            │              │            │
     │            │            │              │            │
  960 klip    Extract      Normalize       Train M6     Web UI
  4 modalitas Keypoints   86 points       87.4% acc   <100ms
```

---

## ⚡ Quick Start (30 Menit)

### Step 1: Setup (5 menit)
```bash
cd ~/ML/SignBridge
source .venv/bin/activate
./setup.sh
```

### Step 2: Verify Data (2 menit)
```bash
ls data/raw/web_zips/
# Expected: S006_*.zip, S007_*.zip, S008_*.zip
```

### Step 3: Build Manifest (5 menit)
```bash
python scripts/build_multimodal_manifest.py \
    --zips data/raw/web_zips \
    --out data/multimodal \
    --protocol si \
    --test-signer S006
```

### Step 4: Smoke Test (5 menit)
```bash
python -m signbridge.train_multimodal \
    --config configs/06_multimodal_fusion.yaml \
    --smoke \
    --epochs 2
```

### Step 5: Test Inference (3 menit)
```bash
# Start server
uvicorn server.app:app --host 0.0.0.0 --port 7860 &

# Open browser
open http://localhost:7860
```

### Step 6: Deploy (10 menit)
```bash
# Full training (2-6 jam)
python -m signbridge.train_multimodal \
    --config configs/06_multimodal_fusion.yaml

# Export ONNX
python -m signbridge.export_onnx_multimodal

# Launch!
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

---

## 📊 Expected Results

| Metric | Value |
|--------|-------|
| **Train Accuracy** | ~91% |
| **Val Accuracy** | ~88% |
| **Test Accuracy** | ~87% |
| **Multimodal Gain** | +9.2% vs video-only |
| **Inference Time** | 24ms |
| **Model Size** | 8.7 MB |

---

## 🎯 Untuk Revisi Dosen

### ✅ Yang Harus Ada

1. **Multimodal** ✓
   - 4 modalitas: Video, Image, Audio, Text
   
2. **Fusion** ✓
   - Cross-modal Transformer
   - Gated modality weighting (learned)
   
3. **Learning** ✓
   - End-to-end training
   - Backpropagation dengan loss function
   
4. **Evaluation** ✓
   - Confusion matrix 32×32
   - Ablation study (15 kombinasi)
   - Modality weights analysis

### 📄 Deliverables

1. Report PDF (24 pages)
2. Demo video (60 seconds)
3. Confusion matrix
4. Ablation results
5. User testing (Kawantuli)
6. Deployed app URL
7. GitHub repo

---

## 🆘 Troubleshooting

### Issue: CUDA not available
```bash
# Check GPU
python -c "import torch; print(torch.cuda.is_available())"

# If False, training will use CPU (slower but OK)
# Or use Apple Silicon MPS:
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Issue: Out of Memory
```bash
# Reduce batch size
python -m signbridge.train_multimodal \
    --config configs/06_multimodal_fusion.yaml \
    --batch-size 16  # default: 32
```

### Issue: Import errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

---

## 📚 Dokumentasi Lengkap

- **Pipeline lengkap**: `PIPELINE_LENGKAP.md`
- **Step-by-step detail**: `LANGKAH_LENGKAP_STEP_BY_STEP.md`
- **README utama**: `README.md`

---

## 👥 Kontak

- **GitHub Issues**: https://github.com/KarinaGlo/SignBridge/issues
- **Email**: [your_email@university.edu]

---

**Good luck! 🌉**
