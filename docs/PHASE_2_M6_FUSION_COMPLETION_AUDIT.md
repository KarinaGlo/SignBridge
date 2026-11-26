# PHASE 2 — M6 MULTIMODAL FUSION COMPLETION AUDIT
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

> [!IMPORTANT]
> **RINGKASAN VERDICT UTAMA**
> - **Status Implementasi Kode M6**: **`IMPLEMENTED, NOT TRAINED`** (seluruh arsitektur 4-modalitas, Transformer fusion, gated weighting, manifest builder, dataset loader, ONNX exporter, dan `MultimodalService` sudah tertulis dan lulus unit test).
> - **Status Model M6**: **`TRAINED ON SYNTHETIC/DUMMY DATA`** (hanya terdapat 1 checkpoint `--smoke` pada data acak/sintetis di [`outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt`](file:///d:/SEMESTER%205/ML/Projek_1/outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt); **0** training pada data nyata, **0** model ONNX terpasang di `web/model/multimodal_fusion.onnx`, dan **0** sampel nyata Recorder yang pernah melewati pipeline hingga inferensi M6).

---

## A. Audit Empat Modalitas

Seluruh spesifikasi diverifikasi langsung terhadap [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py), [`signbridge/multimodal/features.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py), [`signbridge/features.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/features.py), dan [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py):

| Modalitas | Spesifikasi Diharapkan | Implementasi Aktual di Kode | Status |
| :--- | :--- | :--- | :--- |
| **1. Video/Pose** | `[B,64,86,3]`, 86 MediaPipe Holistic keypoints, shoulder normalization, 64 frames | `POSE_SHAPE = (64, 86, 3)`; `trim_inactive` + `normalize_pose` (pusat bahu & lebar bahu) + resampling 64 frame; `PoseEncoder` menghitung posisi+kecepatan (`516` fitur) → 2-layer Transformer → `AvgPool1d(4)` → **16 token** (`d=128`). | `IMPLEMENTED, NOT TRAINED` |
| **2. Image** | `[B,3,112,112]`, hand crop, encoder image, 49 tokens | `IMAGE_SHAPE = (3, 112, 112)`; `image_from_pil` melakukan *center square crop* + resize ke `112×112` + normalisasi ImageNet (catatan: web recorder mengekspor crop `224×224`, lalu loader Python me-resize ke `112×112`); `ImageEncoder` 4 blok Conv2d stride 2 (`112→56→28→14→7`) → **49 token**. | `IMPLEMENTED, NOT TRAINED` |
| **3. Audio** | `[B,64,248]`, mono WAV 16 kHz, log-mel 64 bins, FFT 400, hop 160, 31 tokens | `AUDIO_SAMPLE_RATE=16000`, durasi `2.5s` (`40,000` sampel), `AUDIO_N_FFT=400`, `AUDIO_HOP=160`, `AUDIO_NUM_MELS=64`, `AUDIO_NUM_FRAMES=248`, z-score per klip; `AudioEncoder` 2×Conv1d stride 2 + `AvgPool1d(2)` + 1-layer Transformer → **31 token**. | `IMPLEMENTED, NOT TRAINED` |
| **4. Text** | `[B,64]`, char tokenizer, padding 0, 64 tokens | `TEXT_MAX_LEN=64`, `PAD_ID=0`, `UNK_ID=1`, `TEXT_VOCAB_SIZE=49` (47 karakter + PAD + UNK); `TextEncoder` Embedding + positional embedding + 1-layer Transformer dengan `src_key_padding_mask` → **64 token**. | `IMPLEMENTED, NOT TRAINED` |

---

## B. Audit Arsitektur Fusion

Terverifikasi pada [`SignBridgeMultimodalFusion`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L132-L232) dan [`configs/06_multimodal_fusion.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/06_multimodal_fusion.yaml):
- **Urutan Token**: `CLS (1) + Video (16) + Image (49) + Audio (31) + Text (64) = 161 tokens` berdimensi `d_model = 128`.
- **Seluruh Modalitas Masuk ke Fusion**: Loop `for m, tok in enumerate(tokens)` menambahkan `type_emb[m]`, menggabungkan seluruh 4 aliran token + `CLS`, serta menerapkan `src_key_padding_mask` untuk modalitas yang hilang (`mask[:, m] < 0.5`). Tidak ada modalitas yang sekadar dideklarasikan.
- **Cross-Modal Transformer**: 2 layer (`fusion_layers: 2`), 4 heads (`nhead: 4`), feedforward `512`, GELU.
- **Gated Modality Weighting**: `s_m = gate_vec(tanh(gate_proj(U)))`, masked softmax atas modalitas aktif (`NEG_INF = -1e4`).
- **Modality Dropout**: `modality_dropout = 0.3` aktif saat `model.training`, dengan fallback menjaga minimal 1 modalitas aktif.
- **Classifier & Auxiliary Loss**: `head = Linear(128, 32)` untuk 32 gloss + 4 `aux_heads` (`lambda_aux = 0.3`, `label_smoothing = 0.1`).

---

## C. Integritas Label (Dictionary B)

Verifikasi deterministik terhadap seluruh titik definisi label menghasilkan kecocokan **32/32 (100%)**:
- [`signbridge/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/constants.py#L162-L195) (`BISINDO_32_GLOSSES`) == [`web/model/labels.json`](file:///d:/SEMESTER%205/ML/Projek_1/web/model/labels.json) == [`web/js/config.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/config.js#L46-L79) (`BISINDO_GLOSSES`).
- [`scripts/build_multimodal_manifest.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/build_multimodal_manifest.py#L66-L67) secara eksplisit menyaring `if category != "gloss" or gloss not in GLOSS_TO_ID: continue`, sehingga **tidak** mencampurkan dataset alfabet A–Z dengan 32 gloss Dictionary B.

---

## D. Audit Bukti Training

Detail lengkap dicatat pada [`PHASE_2_M6_TRAINING_EVIDENCE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_2_M6_TRAINING_EVIDENCE.csv):
- **Skrip & Konfigurasi**: [`signbridge/train_multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py) dan [`configs/06_multimodal_fusion.yaml`](file:///d:/SEMESTER%205/ML/Projek_1/configs/06_multimodal_fusion.yaml) tersedia (`AdamW`, `lr=0.0005`, `weight_decay=0.01`, `max_epochs=80`, `patience=12`).
- **Training Data Nyata**: **TIDAK ADA** (`outputs/experiments/M6_multimodal_fusion/` tidak ada).
- **Satu-satunya Checkpoint M6**: [`outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt`](file:///d:/SEMESTER%205/ML/Projek_1/outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt) — berasal dari mode `--smoke` (`M6_multimodal_fusion_SMOKE_RANDOM_DATA`) dengan **data acak/sintetis** (pose random uniform, audio gelombang sinus, **0 sampel gambar** di seluruh split train/val/test), dilatih **2 epoch** (`train_acc=0.0156`, `val_acc=0.0938`, `test_acc=0.125`, `macro_f1=0.0558`).

---

## E. Kesiapan Baseline dan Ablation

- **Evaluasi Kombinasi Modalitas (15 subset)**: Sudah terprogram di [`signbridge/train_multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py#L272-L283) (`ablation_modalities.csv`), mencakup unimodal (`video`, `image`, `audio`, `text`) hingga 4-modalitas melalui `force_mask` saat evaluasi. Namun baru dijalankan pada `--smoke` (dengan `image` = `NaN` karena 0 gambar).
- **Baseline Unimodal Nyata**: `M0_student_baseline` dan `M1_stgcn_baseline` ada pada data pose `WL-BISINDO`, bukan pada manifest multimodal terpadu (`B0`–`B3` & `M0`–`M1` pada dataset multimodal belum dijalankan).
- **Ablation Arsitektural**: **Belum ada** flag/config terpisah di `train_multimodal.py` maupun `configs/` untuk menguji variasi arsitektur **tanpa gating**, **tanpa Cross-Modal Transformer** (`fusion_layers=0` belum didukung eksplisit sebagai baseline non-transformer), atau **tanpa `aux_heads`** (hanya `modality_dropout: 0.0` yang bisa diatur lewat config). Status: **`PARTIALLY IMPLEMENTED`**.

---

## F. Audit Data dan Alur End-to-End

- `data/raw/web_zips/`: **Tidak ada** (0 berkas ZIP dari Recorder).
- `data/multimodal/manifest_multimodal.csv`: **Tidak ada**.
- `web/model/multimodal_fusion.onnx`: **Tidak ada** (`MultimodalService.available` bernilai `False`, endpoint `/predict_multimodal` mengembalikan HTTP 503).
- `assign_splits` di [`signbridge/multimodal/dataset.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/dataset.py#L103-L126) sudah mendukung protokol *signer-independent* (`protocol="si"`, `test_signer`), tetapi belum pernah dijalankan pada data nyata.
- **Kesimpulan End-to-End**: **Belum ada bukti** satu pun sampel nyata dari Recorder yang berhasil melewati seluruh pipeline hingga inferensi M6.

---

## I. Kesimpulan (6 Pertanyaan Wajib)

1. **Apa yang benar-benar sudah selesai?**
   Kode arsitektur M6 (`SignBridgeMultimodalFusion`), preprocessing 4 modalitas (`features.py`), manifest builder (`build_multimodal_manifest.py`), dataset loader (`dataset.py`), skrip training & ONNX exporter (`train_multimodal.py`, `export_onnx_multimodal.py`), layanan API (`multimodal_service.py`), sinkronisasi label 32 gloss Dictionary B, dan unit test kontrak.
2. **Apa yang hanya berupa rancangan / belum terimplementasi penuh?**
   Eksperimen baseline terstandarisasi `B0–B3` dan `M0–M1` pada manifest multimodal, serta variasi ablation arsitektural (tanpa gating, tanpa Cross-Modal Transformer).
3. **Apa yang sudah diimplementasikan tetapi belum dilatih?**
   Seluruh model M6 pada data nyata (termasuk `ImageEncoder` yang bahkan pada `--smoke` memiliki 0 sampel gambar), serta deployment `web/model/multimodal_fusion.onnx`.
4. **Apa yang sudah dilatih dan menggunakan data apa?**
   Hanya `M6_multimodal_fusion_smoke` (2 epoch) menggunakan **data acak/sintetis** dari `build_smoke_manifest()` (tidak valid untuk klaim riset).
5. **Apa yang belum memiliki bukti?**
   Bukti training pada data nyata berpasangan, bukti validasi eksperimental (`B0–B3`, `M0` vs `M1`, ablasi arsitektural), evaluasi *signer-independent* nyata, dan bukti 1 sampel nyata Recorder lolos end-to-end ke inferensi ONNX.
6. **Apa pekerjaan yang wajib dilakukan sebelum training M6?**
   Dirinci lengkap pada [`PHASE_2_M6_REMAINING_WORK.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/PHASE_2_M6_REMAINING_WORK.md): pengumpulan data *paired* nyata lewat Recorder (dengan panduan teks anti-*shortcut*), pembangunan `manifest_multimodal.csv` dengan split *signer-independent*, penambahan config/flag ablasi arsitektural, dan penyelesaian *expert adjudication* alfabet (terpisah dari M6).
