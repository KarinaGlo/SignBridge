# LAPORAN BENCHMARK INFERENSI & PROFILING SISTEM (TAHAP G)

> **Dokumen**: `docs/validation_p1/inference_benchmark_report.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Model Target**: `runs/image_i1_mobilenetv3_p1/best.pt`  
> **Metodologi**: `torch.inference_mode()`, CPU Lokal, Input Tensor `[1, 3, 224, 224]`  
> **Warm-up**: 20 Iterasi | **Benchmark Sampling**: 100 Iterasi Independen  
> **Tanggal Benchmark**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Efisiensi**: **`EXCELLENT EFFICIENCY ON CPU`** (Throughput $82,9\text{ FPS}$)

---

## 1. RINGKASAN HASIL BENCHMARK

Pengujian inferensi ulang dilakukan secara terisolasi untuk mengukur latensi eksekusi forward-pass model PyTorch murni tanpa beban visualisasi grafik:

| Parameter Kinerja | Nilai Terukur (P1 MobileNetV3) | Nilai Pembanding (P0 Baseline) | Selisih / Perubahan |
|---|:---:|:---:|:---:|
| **Model Load Time** | **$112,61\text{ ms}$** | $\approx 45\text{ ms}$ | $+67,6\text{ ms}$ (Checkpoint lebih besar) |
| **Mean Latency** | **$12,06\text{ ms}$** | $8,32\text{ ms}$ | $+3,74\text{ ms}$ |
| **Median Latency** | **$10,32\text{ ms}$** | $8,15\text{ ms}$ | $+2,17\text{ ms}$ (Sangat stabil) |
| **P95 Latency** | **$18,09\text{ ms}$** | $10,12\text{ ms}$ | $+7,97\text{ ms}$ |
| **Min Latency** | **$8,69\text{ ms}$** | $7,40\text{ ms}$ | $+1,29\text{ ms}$ |
| **Max Latency** | **$43,30\text{ ms}$** | $25,10\text{ ms}$ | Spikes akibat CPU scheduling |
| **Throughput Inferensi** | **$82,9\text{ FPS}$** | $120,2\text{ FPS}$ | $-37,3\text{ FPS}$ ($2,76\times$ standar 30 FPS) |
| **Total Parameter** | **$1.544.506$ ($1,545\text{ M}$)** | $265.826$ ($0,266\text{ M}$) | $+5,8\times$ kapasitas representasi |
| **Ukuran Checkpoint** | **$6,01\text{ MB}$** | $1,08\text{ MB}$ | $+4,93\text{ MB}$ |

---

## 2. METODOLOGI & LINGKUNGAN PENGUJIAN

- **Perangkat Keras**: CPU Host (x86_64, Windows OS).
- **Runtime Library**: PyTorch 2.14.1+cpu (Single-thread deterministic context).
- **Tipe Tensor**: Float32 (`torch.float32`), shape `[1, 3, 224, 224]`.
- **Mode Eksekusi**: `torch.inference_mode()` (mematikan pembuatan computation graph dan tracking autograd secara total).
- **Prosedur Pengukuran**:
  1. Instansiasi arsitektur model dan pemuatan bobot state_dict.
  2. Eksekusi 20 iterasi warm-up untuk memastikan cache CPU instruction dan memory allocation telah siap.
  3. Pengukuran waktu menggunakan `time.perf_counter()` berpresisi sub-mikrodetik selama 100 iterasi konsekutif.

---

## 3. ANALISIS PERBEDAAN LATENSI P0 VS P1

1. **Trade-Off Kapasitas Parameter vs Latensi**:
   - Model P0 menggunakan arsitektur miniatur 5-blok ($0,266\text{ M}$ parameter) sehingga forward-pass-nya sangat cepat ($8,32\text{ ms}$). Namun, kapasitas representasinya sangat terbatas sehingga mengalami *overfitting* parah dan akurasi rendah ($7,61\%$).
   - Model P1 mengadopsi arsitektur resmi torchvision MobileNetV3-Small berkapasitas $1,545\text{ M}$ parameter (memuat modul Squeeze-and-Excitation dan Inverted Residual berulang).
   - Penambahan latensi murni hanya sebesar **$+3,74\text{ ms}$**, namun menghasilkan lonjakan akurasi sebesar **$+53,58\%$** ($7,61\% \to 61,19\%$). Ini adalah trade-off efisiensi komputasi yang sangat menguntungkan.

---

## 4. PERINGATAN KRITIS: BATASAN VALIDITAS BENCHMARK TERHADAP APLIKASI WEBCAM

> [!WARNING]
> **JANGAN MENGKLAIM SISTEM WEBCAM MENJALANKAN INFERENSI 83 FPS!**
> 
> Pengukuran latensi di atas murni merefleksikan inferensi forward-pass tensor PyTorch pada CPU lokal. Pengukuran ini **TIDAK MENCERMINKAN** performa keseluruhan pipeline webcam pada peramban web (*browser runtime*).
> 
> Komponen overhead lain yang belum termasuk dalam angka di atas:
> 1. **Frame Capture & Canvas Rendering**: WebRTC camera stream ($16\text{--}33\text{ ms}$ per frame pada 30-60 FPS).
> 2. **MediaPipe Hand Landmark Detection**: Deteksi koordinat 21 titik tangan pada JavaScript/WASM ($20\text{--}40\text{ ms}$ pada CPU peramban).
> 3. **Hand Crop & Aspect-Ratio Padding**: Pemotongan bounding box tangan dan normalisasi di kanvas HTML5 ($3\text{--}8\text{ ms}$).
> 4. **WASM / WebGL Inference Overhead**: ONNX Runtime Web memiliki perbedaan latensi dibanding PyTorch C++ native.
> 
> Estimasi throughput realistis dari keseluruhan pipeline webcam di peramban pengguna adalah **$15\text{--}25\text{ FPS}$**, yang sudah memadai untuk interaksi manusia namun tidak mencapai 83 FPS.

