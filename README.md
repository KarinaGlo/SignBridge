# SignBridge ASEAN — Jembatan Komunikasi Real-Time Bahasa Isyarat Indonesia (BISINDO) & Filipina (FSL)

**SignBridge ASEAN** adalah sistem komunikasi dua arah empat modalitas (*Video*, *Citra*, *Suara*, dan *Teks*) yang dirancang untuk ruang kelas inklusif Indonesia–Filipina. Inferensi utama berjalan langsung di peramban (*browser-first*) menggunakan **MediaPipe Holistic (86 titik kanonis)** dan **ONNX Runtime Web (WebAssembly)** tanpa ketergantungan pada server GPU awan.

---

## Fitur Utama & 6 Kontrak Antarmuka Tim

1. **Kontrak 1 — Skema Data 86 Titik (`signbridge/constants.py`)**:
   - Menyeleksi 86 titik anatomis dari 543 titik MediaPipe Holistic: `[0:9]` pose tubuh atas, `[9:30]` tangan kiri, `[30:51]` tangan kanan, dan `[51:86]` 35 titik wajah ekspresif.
   - Kosakata 32 gloss ruang kelas BISINDO/FSL dan 26 huruf ejaan jari A–Z.
2. **Kontrak 2 — Model Video ONNX (`web/model/student.onnx` & `student_int8.onnx`)**:
   - Input `keypoints` `float32 [1, 64, 86, 3]` -> Output `logits` `float32 [1, 32]`.
   - Paritas numerik PyTorch vs ONNX Runtime `< 1e-4` dan ukuran model `< 2 MB` (batas `< 10 MB`).
3. **Kontrak 3 — Paritas Preprocessing Python <-> JS (`signbridge/features.py` ≡ `web/js/features.js`)**:
   - Pipeline `trim_inactive -> normalize_pose -> resample_frames(64)` diverifikasi identik (`max diff < 1e-5`) oleh `node --test tests/js/parity.test.mjs`.
4. **Kontrak 4 & 5 — Paritas Hand Crop & Model Citra ONNX (`signbridge/image/crop.py` ≡ `web/js/handcrop.js`)**:
   - Pemotongan kotak tangan persegi `+25%` ke `224x224` diverifikasi oleh `node --test tests/js/handcrop.test.mjs`.
   - Model `web/model/fingerspell.onnx` menerima input `image` `float32 [1, 3, 224, 224]` -> output `logits` `[1, 26]`.
5. **Kontrak 6 — Server Hibrida FastAPI (`server/app.py`)**:
   - Menyediakan endpoint `/health`, `POST /predict`, `POST /asr` (batas 10 MB -> HTTP 413), `POST /sentence`, `POST /translate` (Jembatan 3 Lapis L1/L2/L3), dan relay ruang kelas `WebSocket /ws/{kode}` dengan pembatas laju 60 request/menit/IP (HTTP 429 + `Retry-After`).

---

## Panduan Cepat Menjalankan Sistem

### 1. Menjalankan Pengujian Otomatis (Python & Node.js)

```bash
# Uji paritas JavaScript <-> Python (Kontrak 3 & 4)
node --test tests/js/parity.test.mjs tests/js/handcrop.test.mjs

# Uji seluruh suite Python (Kontrak 1-6, Model 4 Modalitas, ONNX, & Server FastAPI)
pytest -q
```

### 2. Menjalankan Pelatihan & Ekspor ONNX

```bash
# Modalitas 1 (Video): Latih Student / Teacher & ekspor ke web/model/student.onnx
python -m signbridge.train --config configs/00_student_baseline.yaml --epochs 2
python -m signbridge.export_onnx --out web/model

# Modalitas 2 (Citra): Latih MobileNetV3-Small & ekspor ke web/model/fingerspell.onnx
python -m signbridge.image.train_image --config configs/image_i1_mobilenetv3.yaml --export --epochs 2

# Modalitas 3 (Suara) & Modalitas 4 (Teks)
python -m signbridge.audio.train_asr --config configs/asr_a1_tiny_zeroshot.yaml
python -m signbridge.text.train_text --config configs/text_t0_rules.yaml
python -m signbridge.text.eval_translate --pair id-fil --system rules
```

### 3. Menjalankan Server FastAPI & Aplikasi Web PWA

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

Buka `http://localhost:7860` di peramban untuk menggunakan **Ruang Kelas 2-Arah**, **Jembatan ASEAN (ID <-> PH)**, **Mode Latihan Mandiri**, dan **Perekam Dataset Multimodal**.

