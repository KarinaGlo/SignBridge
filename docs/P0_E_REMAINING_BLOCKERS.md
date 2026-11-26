# P0-E — REMAINING BLOCKERS
## SignBridge ID–PH (BISINDO ↔ FSL)

Validasi P0-E (1 sampel nyata dari Live Recorder sampai M6 inference) saat ini berstatus **`BLOCKED`** oleh dua hambatan faktual berikut:

---

## Blocker #1 — Belum Ada Sampel Nyata dari Live Recorder (Aksi Pengguna)
- **Fakta**: Folder `data/raw/web_zips/` belum ada (`0` berkas `SignBridge_*.zip`) dan `data/multimodal/manifest_multimodal.csv` belum ada.
- **Dampak**: Tahap 2 (verifikasi webcam & mikrofon fisik), Tahap 3 (validasi ZIP nyata), dan Tahap 4 (manifest & preprocessing sampel nyata) tidak dapat dijalankan.
- **Solusi**: Pengguna menjalankan perekaman 1 take nyata di browser mengikuti [`P0_E_REAL_SAMPLE_VALIDATION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/P0_E_REAL_SAMPLE_VALIDATION_REPORT.md) dan menyimpan file ZIP ke `data/raw/web_zips/`.

---

## Blocker #2 — Belum Tersedia Model ONNX M6 (`web/model/multimodal_fusion.onnx`)
- **Fakta**: `web/model/multimodal_fusion.onnx` tidak ada di disk, dan `outputs/experiments/M6_multimodal_fusion/best_model.pt` juga tidak ada. Satu-satunya checkpoint yang tersedia adalah [`outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt`](file:///d:/SEMESTER%205/ML/Projek_1/outputs/experiments/M6_multimodal_fusion_smoke/best_model.pt) yang dilatih menggunakan **data acak/sintetis** (`--smoke`, `image=0` di seluruh split).
- **Dampak**: `MultimodalService` (`server/multimodal_service.py`) mengembalikan `available=False` (HTTP 503). Inferensi pada sampel nyata belum dapat menghasilkan prediksi model M6 yang terlatih pada data nyata.
- **Solusi**:
  1. Setelah pengumpulan dataset *paired* nyata selesai, latih M6 pada data nyata untuk menghasilkan `outputs/experiments/M6_multimodal_fusion/best_model.pt`, lalu ekspor ke `web/model/multimodal_fusion.onnx` via `python -m signbridge.export_onnx_multimodal`.
  2. (Catatan: jika hanya ingin memverifikasi eksekusi teknis *pipeline* ONNX sebelum training penuh setelah 1 ZIP nyata tersedia, ekspor *smoke* checkpoint **hanya** boleh dilabeli sebagai uji mekanik pipeline, **bukan** akurasi model nyata.)
