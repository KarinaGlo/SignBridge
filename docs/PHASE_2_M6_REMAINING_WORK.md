# PHASE 2 — M6 REMAINING WORK BEFORE TRAINING
## SignBridge ID–PH (BISINDO ↔ FSL)

Dokumen ini merangkum seluruh pekerjaan wajib sebelum pelatihan M6 Multimodal Fusion pada data nyata dapat dilakukan dan diklaim secara ilmiah.

---

## 1. Akuisisi Data Berpasangan Nyata (Blocker Utama)
- **Masalah**: `data/raw/web_zips/` dan `data/multimodal/manifest_multimodal.csv` belum ada (`0` klip nyata).
- **Tindakan Wajib**:
  1. Kumpulkan sampel *paired* (pose + hand-crop + audio + teks) menggunakan tab **Perekam Dataset** di aplikasi web (`web/index.html`) dan simpan ZIP ke `data/raw/web_zips/`.
  2. Terapkan **mitigasi Text Shortcut Leakage** pada [`web/js/app.js#L1044-L1046`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1044-L1046): pastikan kolom teks berisi **kalimat konteks tanya-jawab**, bukan salinan kata target/gloss.
  3. Selaraskan kosakata target dengan 32 gloss resmi `BISINDO_32_GLOSSES` (jika menggunakan subset 20 kata pilot, dokumentasikan bahwa 12 kelas sisanya memiliki 0 sampel).

## 2. Pembangunan Manifest & Split Signer-Independent
- **Tindakan Wajib**:
  1. Jalankan `scripts/build_multimodal_manifest.py` setelah ZIP tersedia untuk menghasilkan `data/multimodal/manifest_multimodal.csv`.
  2. Pastikan tersedia minimal beberapa penutur (*signer*) berbeda agar protokol *signer-independent* (`--protocol si --test-signer <ID>`) dapat dijalankan tanpa kebocoran penutur antara `train` dan `test`.
  3. Verifikasi bahwa keempat modalitas (termasuk `image_path` hand-crop) terisi penuh pada sampel Recorder.

## 3. Kesiapan Eksperimen Baseline & Ablation
- **Masalah**: Belum tersedia skrip/konfigurasi terstandarisasi untuk ablasi arsitektur M6.
- **Tindakan Wajib**:
  1. Tambahkan opsi konfigurasi pada [`SignBridgeMultimodalFusion`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/models/multimodal.py) / [`train_multimodal.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/train_multimodal.py) untuk menguji ablasi:
     - **Tanpa gating** (rata-rata seragam atas modalitas aktif).
     - **Tanpa Cross-Modal Transformer** (bypass `self.fusion` / *simple concatenation baseline* `M0`).
     - **Tanpa modality dropout** (`modality_dropout: 0.0`).
  2. Jalankan benchmark unimodal (`B0` video, `B1` image, `B2` audio, `B3` text) pada manifest multimodal yang sama untuk perbandingan yang adil terhadap `M1` (Full M6).

## 4. Ekspor ONNX & Verifikasi End-to-End
- **Tindakan Wajib**:
  1. Setelah checkpoint nyata `outputs/experiments/M6_multimodal_fusion/best_model.pt` terlatih, jalankan `python -m signbridge.export_onnx_multimodal` untuk menghasilkan `web/model/multimodal_fusion.onnx`.
  2. Uji `POST /predict_multimodal` pada [`server/multimodal_service.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/multimodal_service.py) menggunakan sampel nyata dari Recorder dan pastikan tidak lagi mengembalikan HTTP 503.

## 5. Pemisahan Jalur Dataset Alfabet (Phase 1 / 1.1)
- Tetap jaga pemisahan tegas: 36 citra alfabet Mendeley (yang masih menunggu *expert adjudication* dan belum berstatus final ground truth) ditangani terpisah oleh model fingerspelling 26 kelas (`fingerspell.onnx`), tidak dicampur ke training M6 32 gloss.
