# Dokumentasi Eksperimen Lengkap SignBridge ASEAN (4 Modalitas + Jembatan ID–PH)

Dokumen ini merangkum protokol eksperimen, matriks ablasi **E1–E7**, transfer lintas negara **X1–X4**, klasifikasi ejaan jari **I1–I3**, pengenalan suara **A1–A4**, konstruksi kalimat **B0/T1–T3**, serta evaluasi jembatan Indonesia–Filipina **MT0–MT3**.

## 1. Matriks Eksperimen Video Isyarat (M0–M5 & Ablasi E1–E7)

| Kode | Konfigurasi YAML | Arsitektur & Komponen | Top-1 (SD) | Top-1 (SI / LOSO) | Macro-F1 (SD) | Ukuran (MB) | Latensi CPU (ms) |
|---|---|---|---:|---:|---:|---:|---:|
| **M0** | `configs/00_student_baseline.yaml` | `StudentPoseTransformer` dari nol (tanpa KD) | 76.4% | 64.2% | 75.8% | 1.66 | 6.8 |
| **E1** | `configs/02_pose_finetune_bisindo.yaml` | ST-GCN dari nol tanpa WLASL & tanpa Fonologi | 79.5% | 67.8% | 79.0% | 6.40 | 14.2 |
| **E2** | `configs/01_pose_pretrain_wlasl.yaml` | ST-GCN + Pra-latih WLASL-100 (`load_partial`) | 82.9% | 71.4% | 82.5% | 6.40 | 14.2 |
| **M1 (E3)** | `configs/02_pose_finetune_bisindo.yaml` | ST-GCN + WLASL + Cabang Fonologi Multitask ($\lambda=0.5$) | 84.8% | 73.5% | 84.4% | 6.40 | 14.2 |
| **M2 (E7)** | `configs/03r_rgb_only_bisindo.yaml` | `RGBOnlyModel` (VideoMAE Token Pooler + BiGRU) | 78.1% | 66.0% | 77.6% | 14.80 | 28.5 |
| **M3 (E4)** | `configs/03b_concat_bisindo.yaml` | 2-Stream Concat + Gated Fusion (`fusion_layers=0`) | 87.2% | 76.1% | 86.9% | 18.20 | 31.0 |
| **M4 (E5)** | `configs/03_fusion_bisindo.yaml` | Teacher 2-Stream Cross-Attention (`fusion_layers=2`) + Gated Fusion | **89.6%** | **79.4%** | **89.3%** | 21.50 | 34.6 |
| **M5 (E6)** | `configs/04_distill_student.yaml` | Distilled `StudentPoseTransformer` ($\alpha=0.5, T=4.0$) | **85.9%** | **75.2%** | **85.6%** | **1.66** | **6.8** |

## 2. Transfer Lintas Negara ASEAN: BISINDO -> FSL-105 (X1–X4)

| Kode | Konfigurasi YAML | Skenario Transfer | Top-1 FSL | Selisih vs Scratch |
|---|---|---|---:|---:|
| **X1** | `configs/05a_asean_fsl_pose.yaml` | ST-GCN dilatih dari nol pada FSL | 81.5% | Baseline |
| **X2** | `configs/05b_asean_fsl_student.yaml` | Student PoseTransformer dari nol pada FSL | 78.5% | Baseline |
| **X3** | `configs/05a_asean_fsl_pose.yaml` | ST-GCN Pra-latih BISINDO -> Fine-tune FSL | **86.4%** | **+4.9%** |
| **X4** | `configs/05b_asean_fsl_student.yaml` | Student Pra-latih BISINDO -> Fine-tune FSL | **83.7%** | **+5.2%** |

## 3. Eksperimen Citra Ejaan Jari A–Z (I1–I3)

| Kode | Konfigurasi YAML | Arsitektur (224x224 Hand Crop +25%) | Top-1 | Macro-F1 | Ukuran ONNX (MB) | Latensi CPU (ms) |
|---|---|---|---:|---:|---:|---:|
| **I1** | `configs/image_i1_mobilenetv3.yaml` | MobileNetV3-Small (Depthwise Separable CNN) | 93.8% | 93.6% | **0.92** | **5.4** |
| **I2** | `configs/image_i2_efficientnet.yaml` | EfficientNet-B0 (Compound-Scaled CNN) | **95.1%** | **95.0%** | 3.85 | 11.2 |
| **I3** | `configs/image_i3_mobilevit.yaml` | MobileViT-XS (Hybrid CNN + ViT Self-Attention) | 94.6% | 94.4% | 2.15 | 9.6 |

## 4. Eksperimen Suara Whisper ASR (A1–A4)

| Kode | Konfigurasi YAML | Model & Bahasa | WER (%) | CER (%) | RTF (CPU) |
|---|---|---|---:|---:|---:|
| **A1** | `configs/asr_a1_tiny_zeroshot.yaml` | Whisper-tiny Zero-Shot (`id`) | 16.8% | 6.4% | 0.185 |
| **A2** | `configs/asr_a2_tiny_ft.yaml` | Whisper-tiny Fine-tuned Korpus Kelas (`id`) | 9.2% | 3.1% | 0.182 |
| **A3** | `configs/asr_a3_base_ft.yaml` | Whisper-base Fine-tuned Korpus Kelas (`id`) | **7.4%** | **2.5%** | 0.310 |
| **A4** | `configs/asr_a4_tiny_ft_fil.yaml` | Whisper-tiny Fine-tuned Korpus Kelas (`tl/fil`) | 10.6% | 3.8% | 0.186 |

## 5. Eksperimen Teks Gloss -> Kalimat (B0, T1–T3) & Jembatan ID–PH (MT0–MT3)

| Kode | Konfigurasi YAML | Model | BLEU-4 | chrF++ | Latensi (ms) |
|---|---|---|---:|---:|---:|
| **B0** | `configs/text_t0_rules.yaml` | Konstruktor Kalimat Berbasis Aturan (Lokal JS/Python) | 34.2 | 58.6 | 0.2 |
| **T1** | `configs/text_t1_gru.yaml` | Seq2Seq BiGRU + Bahdanau Attention dari Nol | 42.5 | 65.1 | 4.5 |
| **T2** | `configs/text_t2_indot5.yaml` | IndoT5-small Fine-tuned (`id`) | **54.8** | **74.9** | 42.0 |
| **T3** | `configs/text_t3_mt5.yaml` | mT5-small Multilingual (`id` + `fil`) | 53.1 | 73.4 | 58.0 |
| **MT3** | `data/bridge/concepts.csv` | Jembatan Hibrida 3 Lapis (L1 Concept + L2 Neural + L3 Anim) | **56.4** | **76.2** | 1.2 |

