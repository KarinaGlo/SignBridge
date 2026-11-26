# LAPORAN AUDIT IMPLEMENTASI M6 MULTIMODAL FUSION (TASK P0-A)
**Proyek:** SignBridge ASEAN — Jembatan Komunikasi Real-Time Multimodal BISINDO ↔ FSL  
**Komponen yang Diaudit:** Arsitektur M6 Four-Modality Multimodal Fusion Network  
**Lokasi Direktori:** `D:\SEMESTER 5\ML\Projek_1`  
**Tanggal Audit:** 20 November 2026  
**Auditor:** Senior ML Engineer & Software Architect  

---

## 1. STATUS KESIAPAN SISTEM (VERDICT)

### **STATUS: READY WITH ISSUES (SIAP DENGAN CATATAN TEKNIS KRITIS)**

> **Ringkasan Penilaian:**  
> Seluruh arsitektur neural network M6, pipeline ekstraksi fitur 4 modalitas, mekanisme gated modality weighting, loss function, dan loader data telah terpasang secara utuh dan **lulus 100% unit test** (22/22 unit test multimodal lulus, 18/18 integration test lulus, 11/11 browser test lulus).  
> Namun, ada **4 isu teknis kritis** pada konfigurasi kelas, entry point perintah, mitigasi shortcut teks web recorder, dan warning deprecation ONNX yang **wajib dipahami dan ditangani** sebelum proses akuisisi 300 sampel pilot (P0-B) dimulai.

---

## 2. HASIL PENGUJIAN & STATUS DEPENDENCY LOKAL

### A. Audit Dependency
- **Python Runtime:** Python 3.13.12 (64-bit)
- **PyTorch:** Terpasang (CPU execution provider aktif)
- **ONNX Library:** `onnx == 1.23.2` terpasang
- **ONNX Runtime:** `onnxruntime == 1.20.1` terpasang
- **PyYAML:** Terpasang
- **Node.js:** v22+ terpasang untuk pengujian kontrak JavaScript

### B. Hasil Eksekusi Test Suite Faktual

| Kategori Test Suite | Command Eksekusi | Passed | Failed | Skipped | Durasi |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Multimodal Features & Data** | `pytest tests/test_multimodal_features.py` | 12 | 0 | 0 | 1.82s |
| **Multimodal Model M6 & Parity** | `pytest tests/test_multimodal_model.py` | 7 | 0 | 0 | 43.84s |
| **Multimodal Service (Server)** | `pytest tests/test_multimodal_service.py` | 3 | 0 | 0 | 2.03s |
| **Subtotal Multimodal Suite** | `pytest tests/test_multimodal_*.py` | **22** | **0** | **0** | **47.69s** |
| **Database & Suite Integrasi** | `pytest tests/test_database_integration.py tests/test_signbridge_suite.py` | **18** | **0** | **0** | **27.86s** |
| **Browser Recorder & Parity (JS)** | `node --test tests/js/recorder.test.mjs tests/js/parity.test.mjs tests/js/handcrop.test.mjs` | **11** | **0** | **0** | **291ms** |
| **TOTAL KESELURUHAN** | — | **51** | **0** | **0** | **~76s** |

*Catatan: Tidak ada test yang diubah atau dimanipulasi. Seluruh 51 test lulus pada kode asli repository commit `3772e14`.*

---

## 3. PEMERIKSAAN 10 POIN WAJIB DENGAN NOMOR BARIS (LINE-BY-LINE AUDIT)

### 1. Bentuk Tensor Aktual untuk Setiap Modalitas
- **Video / Pose:**
  - File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L5-L8), [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py#L18)
  - Bentuk input tensor: `[B, 64, 86, 3]` (float32).
  - Mekanisme Encoder ([`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L59-L75)): Menghitung temporal velocity (`vel = pose[:, 1:] - pose[:, :-1]`), digabung menjadi $86 \times 3 \times 2 = 516$ fitur per frame. Diproyeksikan ke $d=128$, diproses 2-layer Transformer Encoder, dan di-downsample oleh `nn.AvgPool1d(4)` menjadi **16 token** berdimensi 128: `[B, 16, 128]`.
- **Citra (Crop Tangan):**
  - File: [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py#L21-L22), [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L77-L94)
  - Bentuk input tensor: `[B, 3, 112, 112]` (float32, normalisasi ImageNet).
  - Mekanisme Encoder: 4 blok CNN stride 2 ($112 \to 56 \to 28 \to 14 \to 7$), menghasilkan feature map spasial $7 \times 7 =$ **49 token** berdimensi 128: `[B, 49, 128]`.
- **Audio (Log-Mel Spectrogram):**
  - File: [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py#L30-L32), [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L96-L113)
  - Bentuk input tensor: `[B, 64, 248]` (float32, log-mel 64 filter banks, 248 time frames ~2.5 detik pada 16 kHz).
  - Mekanisme Encoder: 2-lapis Conv1d stride 2 ($248 \to 124 \to 62$), di-downsample `AvgPool1d(2)` menjadi **31 token** berdimensi 128: `[B, 31, 128]`.
- **Teks (Karakter Konteks):**
  - File: [`signbridge/multimodal/constants.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/constants.py#L35-L36), [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L115-L130)
  - Bentuk input tensor: `[B, 64]` (int64, vocab size = 49 karakter, padding ID = 0).
  - Mekanisme Encoder: Embedding layer + Positional Encoding + 1-layer Transformer Encoder menghasilkan **64 token** berdimensi 128: `[B, 64, 128]`.
- **Urutan Sekuens Fusion Terpadu:**
  - File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L194-L206)
  - Token digabung: `[CLS]` (1) + Video (16) + Image (49) + Audio (31) + Text (64) = **161 token** berdimensi 128 (`[B, 161, 128]`).

---

### 2. Kesesuaian Preprocessing dan Model Input
- **Kesesuaian Video:**
  - Fungsi [`pose_from_sequence`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py#L40-L57) menerima deret mentah `[F, 86, 3]`, melakukan zero-handling (titik 0 dianggap NaN agar tidak merusak normalisasi), lalu memanggil `preprocess_keypoints(arr, target_len=64)` dan mengembalikan `(64, 86, 3)`. Identik 100% dengan kebutuhan `PoseEncoder`.
- **Kesesuaian Citra:**
  - Fungsi [`load_image`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py#L89-L119) dan `image_from_pil` memotong tengah (square crop) dan me-resize menjadi `(112, 112)` serta normalisasi ImageNet `(x - mean) / std`. Meskipun web recorder menghasilkan 224x224 ([`web/js/recorder.js`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L230)), loader Python secara otomatis me-resize menjadi 112x112 saat dimuat.
- **Kesesuaian Audio:**
  - Fungsi [`load_audio`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py#L220-L238) memanggil `read_wav`, me-resample sinyal ke 16 kHz jika diperlukan via `resample_linear`, memotong/mem-pad ke 40.000 sampel (2.5 detik) via `fix_length`, dan menghitung log-mel `[64, 248]` dengan standardisasi z-score per klip (`mu=0, std=1`).
- **Kesesuaian Teks:**
  - Fungsi [`encode_text`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/multimodal/features.py#L251-L260) membersihkan teks ke huruf kecil dan memetakan karakter ke ID integer, di-pad hingga panjang tetap 64 dengan nilai 0 (`PAD_ID`).

---

### 3. Mekanisme Cross-Modal Transformer
- File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L150-L152), [`L194-L209`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L194-L209)
- **Type Embedding:** Setiap token dari modalitas $m \in \{0, 1, 2, 3\}$ ditambahkan `self.type_emb[m]` (`torch.randn(4, 128)`).
- **Transformer Config:** 2 layer Transformer Encoder, 4 attention heads, feedforward dimension = $128 \times 4 = 512$, activation = GELU, `batch_first=True`.
- **Interaksi Antar-Modalitas:** Semua 161 token saling bertukar informasi secara bebas melalui multi-head self-attention, memungkinkan representasi visual tangan dipandu oleh sinyal audio ucapan dan konteks kalimat.

---

### 4. Mekanisme Gated Modality Weighting
- File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L210-L224)
- **Ringkasan Per Modalitas ($u_m$):**
  Untuk tiap modalitas $m$, token output Transformer di-average pooling hanya atas token valid:
  $$u_m = \frac{\sum_{t \in \text{span}_m} h_t \cdot \mathbb{I}(\text{valid})}{\sum \mathbb{I}(\text{valid})} \in \mathbb{R}^d$$
- **Skor Gating:**
  $$s_m = v^T \tanh(W u_m) \in \mathbb{R}$$
- **Masking & Normalisasi Softmax:**
  Jika modalitas $m$ hilang ($\text{mask}_m < 0.5$), $s_m \leftarrow -10.000$ (`NEG_INF`).  
  $$\alpha = \text{Softmax}(s) \odot \text{mask}$$
  $$\alpha_m = \frac{\alpha_m}{\sum_j \alpha_j + 10^{-6}}$$
- **Vektor Terbobot:**
  $$z = \sum_{m=1}^4 \alpha_m u_m$$
  $$h_{\text{fused}} = \text{LayerNorm}(h_{\text{CLS}} + z)$$
  $$\text{logits} = \text{Linear}(h_{\text{fused}}) \to [B, \text{num\_classes}]$$
- Terverifikasi pada unit test [`test_forward_shapes_and_weights_sum_to_one`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_multimodal_model.py#L33-L44): $\sum \alpha_m = 1.0$ dan modalitas hilang mendapat bobot tepat $0.0$.

---

### 5. Penanganan Missing Modality dan Attention Masking
- File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L198-L208)
- **Attention Masking (`key_padding_mask`):**
  Bila modalitas $m$ hilang, seluruh rentang tokennya diatur ke `True` pada `key_pad`. Token teks yang bernilai nol (padding) juga diatur ke `True`.
  Dengan demikian, token dari modalitas yang tidak ada **sama sekali tidak dapat di-attend** oleh modalitas lain di dalam Transformer.
- **Verifikasi Nol Efek:**
  Teruji pada [`test_masked_modality_does_not_affect_prediction`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_multimodal_model.py#L46-L54): memberikan nilai acak ekstrem ($x \times 100 + 7$) pada modalitas yang hilang menghasilkan logits yang identik ($\Delta < 10^{-5}$).
- **Modality Dropout:**
  Fungsi [`apply_modality_dropout`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L161-L173) menghapus modalitas secara acak saat training ($p=0.3$), dengan jaminan minimal 1 modalitas tetap hidup (`empty.any()` ditangani dengan fallback acak berbobot).

---

### 6. Auxiliary Loss dan Total Loss
- File: [`signbridge/models/multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L158), [`L225`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L225), [`L247-L262`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L247-L262)
- Terdapat 4 linear head tambahan (`self.aux_heads = nn.ModuleList([nn.Linear(d, num_classes) for _ in range(4)])`) yang memprediksi kelas langsung dari ringkasan modalitas $u_m$.
- Formulasi Loss:
  $$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{fused}} + \lambda_{\text{aux}} \cdot \mathcal{L}_{\text{aux}}$$
  $$\mathcal{L}_{\text{aux}} = \frac{\sum_{m=1}^4 \mathcal{L}_{\text{CE}}(\text{aux\_logits}_m, y) \cdot \text{used\_mask}_m}{\sum_{m=1}^4 \text{used\_mask}_m}$$
- Default config: $\lambda_{\text{aux}} = 0.3$, label smoothing = $0.1$.
- Loss terbukti mengalirkan gradien dengan baik ([`test_loss_backward_and_one_step_learns`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_multimodal_model.py#L76-L93)).

---

### 7. Konsistensi Class Mapping dan Vocabulary (TEMUAN KRITIS #1)
- **Temuan Masalah:**
  Jumlah kelas `num_classes` saat ini **TERPATRI (HARDCODED) KE 32 KELAS** di beberapa file:
  1. [`signbridge/models/multimodal.py#L135`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L135): `def __init__(self, num_classes: int = 32, ...)`
  2. [`signbridge/train_multimodal.py#L227`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py#L227): `model = SignBridgeMultimodalFusion(num_classes=32, **mcfg).to(device)`
  3. [`signbridge/train_multimodal.py#L289`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py#L289): `for c in range(32):` (loop evaluasi per kelas)
  4. [`signbridge/export_onnx_multimodal.py#L76`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/export_onnx_multimodal.py#L76): `model = SignBridgeMultimodalFusion(num_classes=32, **mcfg)`
  5. [`server/multimodal_service.py#L18`](file:///d:/SEMESTER%205/ML/Projek_1/server/multimodal_service.py#L18), [`L87`](file:///d:/SEMESTER%205/ML/Projek_1/server/multimodal_service.py#L87), [`L90`](file:///d:/SEMESTER%205/ML/Projek_1/server/multimodal_service.py#L90): Terikat langsung pada `BISINDO_32_GLOSSES`.
  6. [`scripts/build_multimodal_manifest.py#L66-L67`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/build_multimodal_manifest.py#L66-L67): `if category != "gloss" or gloss not in GLOSS_TO_ID: continue`
- **Implikasi pada 300 Sampel Pilot:**
  Jika Anda mengumpulkan 20 kata baru di luar daftar 32 kosakata resmi (`BISINDO_32_GLOSSES`), data Anda akan **dibuang otomatis oleh script manifest**!  
  Sebaliknya, jika Anda menggunakan subset 20 kata dari 32 kosakata tersebut, training dapat berjalan lancar namun 12 kelas sisanya akan memiliki 0 sampel.
- **Rekomendasi Solusi:**  
  Untuk Pilot 300 sampel (P0-B), **wajib memilih 20 kata yang merupakan subset resmi dari `BISINDO_32_GLOSSES`**.

---

### 8. Kesesuaian Model dengan ONNX Export
- File: [`signbridge/export_onnx_multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/export_onnx_multimodal.py#L37-L65)
- Wrapper [`MultimodalOnnxWrapper`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py#L235-L245) membungkus model menjadi 5 input tensor dan 2 output tensor (`logits`, `modality_weights`).
- Paritas teruji: [`test_onnx_export_and_parity`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_multimodal_model.py#L103-L110) **LULUS (maks selisih PyTorch vs ONNX Runtime $< 1 \times 10^{-4}$)**.
- **Catatan Warning:** PyTorch 2.6 memunculkan warning tentang deprecation `dynamic_axes` ke `dynamic_shapes`, namun fungsi ekspor dan eksekusi inferensi tetap sukses 100%.

---

### 9. Kesesuaian Perintah Training dengan Entry Point Aktual (TEMUAN KRITIS #2)
- **Temuan Masalah:**
  Pada prompt perencanaan sebelumnya, terdapat perintah:
  `python -m signbridge.multimodal.train_multimodal`
  Perintah ini **AKAN GAGAL DENGAN `No module named signbridge.multimodal.train_multimodal`** karena lokasi file aktualnya adalah di root paket `signbridge/`, bukan di dalam subdirektori `multimodal/`.
- **Daftar Entry Point Faktual yang Benar:**
  - **Training M6:**
    ```bash
    python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml
    ```
  - **Smoke Test Training (Uji Pipa):**
    ```bash
    python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml --smoke
    ```
  - **ONNX Export:**
    ```bash
    python -m signbridge.export_onnx_multimodal --ckpt outputs/experiments/M6_multimodal_fusion/best_model.pt --out web/model/multimodal_fusion.onnx
    ```
  - **Build Manifest dari Rekaman Web ZIP:**
    ```bash
    python scripts/build_multimodal_manifest.py --zips data/raw/web_zips --out data/multimodal
    ```

---

### 10. Kesiapan Menerima 300 Sampel Paired Pilot (TEMUAN KRITIS #3 & #4)
- **Kesiapan Pipeline:**  
  Alur end-to-end dari perekam peramban (`web/js/recorder.js`) $\to$ Ekspor ZIP $\to$ Unpack & Build Manifest (`build_multimodal_manifest.py`) $\to$ Dataset Loader (`dataset.py`) $\to$ Training (`train_multimodal.py`) telah tersambung sempurna.
- **Isu Kritis Text Shortcut pada Recorder (TEMUAN KRITIS #3):**  
  Pada [`web/js/app.js#L1044-L1046`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1044-L1046):
  ```javascript
  targetSelect.addEventListener("change", () => {
    sentenceEl.value = glossToSentenceLocal([targetSelect.value], "id");
  });
  ```
  Ketika pengumpul data memilih kata target (misal `MAKAN`), UI web otomatis mengisi input kalimat dengan teks yang mengandung kata tersebut (misal `"Makan."`). Jika teks ini dibiarkan saat perekaman 300 sampel pilot, **terjadi kebocoran leksikal (Text Shortcut Leakage)**. Model M6 akan belajar menebak label dari teks, bukan dari video/tangan!
  *Mitigasi:* Kotak teks pada UI perekam harus diisi dengan **kalimat konteks tanya-jawab** (contoh: isyarat `MAKAN`, teks yang diketik: `"Apakah kamu sudah lapar?"`).

---

## 4. DAFTAR TINDAKAN KONKRET SEBELUM P0-B DIMULAI

Berikut adalah 4 langkah aksi wajib sebelum Anda mulai mengumpulkan data pilot di Fase P0-B:

```markdown
1. STANDARDISASI 20 KOSAKATA PILOT DARI BISINDO_32_GLOSSES
   Pilihlah tepat 20 kata dari daftar resmi agar kompatibel dengan GLOSS_TO_ID:
   Rekomendasi 20 Kata Pilot:
   [
     "AIR", "BELAJAR", "CARI", "HARI", "INGAT",
     "LAGI", "MAAF", "MAKAN", "SAYA", "TERIMA_KASIH",
     "TULI", "APA", "SIAPA", "KAPAN", "DIMANA",
     "TEMAN", "RUMAH", "PAGI", "SIANG", "MALAM"
   ]

2. TETAPKAN PANDUAN TEKS KONTEKS (ANTI-SHORTCUT) UNTUK PEREKAM
   Buat panduan kalimat pemicu untuk 20 kata tersebut. Pengumpul data TIDAK BOLEH
   membiarkan kotak teks terisi kata yang sama dengan target isyarat.
   Contoh:
   - Target "AIR"         -> Teks: "Saya merasa sangat haus di kelas"
   - Target "BELAJAR"     -> Teks: "Mari kita mulai pelajaran hari ini"
   - Target "TERIMA_KASIH"-> Teks: "Ibu guru sudah membantu saya"

3. RUN SMOKE TEST TRAINING PIPELINE LOKAL (VERIFIKASI AKHIR)
   Jalankan perintah ini di terminal untuk memastikan loop training, evaluasi,
   dan penulisan checkpoint berjalan tanpa error di komputer lokal Anda:
   python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml --smoke --epochs 2
   (Memverifikasi pembuatan outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt).

4. AKUISISI 300 SAMPEL PAIRED DI BROWSER (P0-B)
   Buka `web/index.html` -> Tab "Perekam Dataset".
   Rekam 20 kata x 15 repetisi = 300 klip.
   Klik "Unduh Paket ZIP" dan simpan ke folder `data/raw/web_zips/`.
```

---

## 5. KESIMPULAN AUDIT

Implementasi teknis M6 pada repository SignBridge berada dalam status **READY WITH ISSUES**.  
Tidak diperlukan refactoring arsitektur atau penulisan ulang modul inti karena seluruh kontrak tensor, transformer fusion, auxiliary heads, dan ONNX parity telah terverifikasi dengan hasil tes 100% lulus. Anda dapat langsung melanjutkan ke fase persiapan pengumpulan data (P0-B) dengan mematuhi daftar tindakan konkret di atas.

