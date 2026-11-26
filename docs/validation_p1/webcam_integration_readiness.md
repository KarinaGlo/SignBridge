# AUDIT KESIAPAN INTEGRASI WEBCAM: MODEL I1-P1 (TAHAP H)

> **Dokumen**: `docs/validation_p1/webcam_integration_readiness.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Target Integrasi**: Frontend Web Application (`web/` HTML/JS + ONNX Runtime Web)  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Kesiapan**: **`CONDITIONALLY READY (EXPORT & STABILIZATION REQUIRED)`**

---

## 1. RINGKASAN KESIAPAN INTEGRASI

Model **MobileNetV3-Small (I1-P1)** memiliki performa akurasi ($61,19\%$) dan latensi inferensi ($12\text{--}18\text{ ms}$) yang jauh melampaui baseline P0 ($7,61\%$), sehingga sangat potensial menjadi kandidat pengganti model fingerspell saat ini.

Namun, model saat ini tersimpan dalam format PyTorch Checkpoint ([`runs/image_i1_mobilenetv3_p1/best.pt`](file:///d:/SEMESTER%205/ML/Projek_1/runs/image_i1_mobilenetv3_p1/best.pt)). Model **TIDAK BOLEH** langsung ditimpa ke model produksi [`web/model/fingerspell.onnx`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/fingerspell.onnx) tanpa memenuhi prasyarat kontrak antarmuka dan stabilisasi temporal.

---

## 2. AUDIT KONSISTENSI KONTRAK INPUT & PREPROCESSING

| Parameter Pipeline | Pelatihan PyTorch P1 | Pipeline Webcam Saat Ini (`web/js`) | Status Kompatibilitas | Rekomendasi Penyesuaian |
|---|:---:|:---:|:---:|:---|
| **Format Warna** | RGB (3 kanal) | RGBA (HTML5 `<canvas>`) | **Perlu Konversi** | Ekstraksi kanal R, G, B; buang kanal Alpha di JavaScript |
| **Dimensi Input** | $224 \times 224$ piksel | $224 \times 224$ piksel | **KOMPATIBEL** | Pertahankan resolusi $224 \times 224$ |
| **Normalisasi Rentang** | $[0.0, 1.0]$ | $[0.0, 1.0]$ atau $[-1.0, 1.0]$ | **KRITIS** | Pastikan canvas piksel dibagi $255.0$ sebelum normalisasi z-score |
| **Normalisasi Mean $(\mu)$** | $[0.485, 0.456, 0.406]$ | Bervariasi di model web lama | **WAJIB SINKRON** | Terapkan persis formula ImageNet: $(R - 0.485) / 0.229$, dst. |
| **Normalisasi Std $(\sigma)$** | $[0.229, 0.224, 0.225]$ | Bervariasi di model web lama | **WAJIB SINKRON** | Pastikan nilai std ImageNet diterapkan per kanal |
| **Format Dimensi Tensor** | NCHW: `[1, 3, 224, 224]` | Float32Array NCHW | **KOMPATIBEL** | Pertahankan tensor order planar (RRR...GGG...BBB...) |
| **Output Logits** | 26 logit (`[1, 26]`) | 26 logit (`[1, 26]`) | **KOMPATIBEL** | Sesuai dengan label A–Z |

---

## 3. IDENTIFIKASI RISIKO RUNTIME WEBCAM & MITIGASINYA

### A. Risiko Distorsi Aspek Rasio Crop Tangan (*Aspect-Ratio Distortion*)
- **Masalah**: Bounding box tangan penutur jarang berbentuk bujur sangkar sempurna ($1:1$). Sebagai contoh, gestur jari telunjuk tegak (huruf D) sering menghasilkan bounding box vertikal $160 \times 240$.
- **Bahaya**: Jika bounding box non-persegi langsung di-*stretch* paksa ke kanvas $224 \times 224$, jari-jari tangan akan tampak melebar atau memendek secara artifisial, memicu salah klasifikasi antara D, P, dan T.
- **Solusi Mitigasi**: Terapkan **Square Crop with Padding / Letterboxing**. Ambil dimensi terpanjang $\max(W, H)$ sebagai sisi bujur sangkar, lalu berikan padding hitam/simetris sebelum me-resize ke $224 \times 224$.

### B. Risiko Fluktuasi Frame-ke-Frame (*Prediction Jitter*)
- **Masalah**: Inferensi citra frame tunggal pada 30 FPS rentan berfluktuasi akibat getaran mikro tangan, noise sensor webcam, atau perubahan eksposur pencahayaan sesaat.
- **Bahaya**: Output teks di layar web akan melompat-lompat dengan cepat (misalnya `D` $\to$ `P` $\to$ `D` $\to$ `T`).
- **Solusi Mitigasi**: Terapkan **Temporal Smoothing Buffer (Majority Voting)** di `web/js/app.js`:
  1. Simpan prediksi 7 frame terakhir ke dalam ring buffer.
  2. Huruf baru hanya dikonfirmasi jika muncul minimal pada $4$ dari $7$ frame ($> 50\%$).
  3. Gunakan Exponential Moving Average (EMA) pada vektor probabilitas:
     $$P_{\text{smooth}}^{(t)} = \alpha P^{(t)} + (1 - \alpha) P_{\text{smooth}}^{(t-1)}, \quad \alpha = 0,4$$

### C. Penanganan Kondisi Tangan Tidak Terdeteksi (*Idle State / Empty Canvas*)
- **Masalah**: Ketika tangan penutur keluar dari frame kamera atau tersembunyi, sistem web tidak boleh mengirim frame kosong/wajah ke model fingerspell.
- **Solusi Mitigasi**: Manfaatkan MediaPipe Hands `results.multiHandLandmarks`. Jika panjang array $= 0$, langsung set status antarmuka ke `"Menunggu Tangan..."` tanpa memicu inferensi model, menghemat penggunaan CPU/GPU browser.

### D. Penegakan Ambang Batas Keyakinan (*Confidence Thresholding*)
- **Temuan Tahap E**: Sampel dengan confidence $< 0,40$ memiliki tingkat kesalahan $71,78\%$, sedangkan sampel dengan confidence $\ge 0,80$ memiliki akurasi $94,90\%$.
- **Solusi Mitigasi**: Pasang slider atau nilai ambang default **$0,60$** di frontend. Prediksi di bawah $0,60$ dianggap sebagai isyarat transisi (*in-between gesture*) dan tidak ditampilkan sebagai karakter final.

---

## 4. PROSEDUR EKSPOR ONNX YANG AMAN (ROADMAP DEPLOYMENT)

Untuk menjaga stabilitas sistem produksi, ekspor ONNX harus mengikuti jalur terisolasi:

1. **JANGAN menimpa `web/model/fingerspell.onnx` secara langsung**.
2. Buat script ekspor terpisah:
   `python -m signbridge.image.models.export_onnx --checkpoint runs/image_i1_mobilenetv3_p1/best.pt --output runs/image_i1_mobilenetv3_p1/fingerspell_p1.onnx --opset 17`
3. Validasi numerik ONNX Runtime vs PyTorch:
   Pastikan *Mean Absolute Error* (MAE) antara output logits PyTorch dan output ONNX Runtime $< 10^{-5}$.
4. Lakukan pengujian di fixture browser terisolasi (`tests/test_web_parity.mjs` atau `scripts/replay_eval.mjs`).
5. Hanya deploy ke `web/model/fingerspell.onnx` setelah disetujui secara resmi oleh tim lead.

