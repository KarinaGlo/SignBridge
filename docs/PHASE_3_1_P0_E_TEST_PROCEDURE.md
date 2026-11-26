# PHASE 3.1 — PROSEDUR UJI MANUAL P0-E (1 SAMPEL NYATA)
## SignBridge ID–PH (BISINDO ↔ FSL)

Prosedur ini memandu verifikasi **satu sampel nyata end-to-end** dari Web Recorder hingga pembentukan tensor input M6 (tanpa menjalankan training M6).

---

## Langkah 1–7: Perekaman di Browser (`http://localhost:8080`)
1. **Persetujuan Signer**: Pastikan signer (mis. `S01`) telah menandatangani persetujuan partisipasi dan masukkan kode signer pada kolom `#rec-signer`.
2. **Pilih Gloss Dictionary B**: Pada tab **Perekam Dataset**, pilih kategori `gloss` lalu pilih satu target resmi dari 32 kosakata Dictionary B (mis. `AIR` atau `BELAJAR`).
3. **Siapkan Konteks Kalimat (Anti-Leakage)**: Klik **Saran Konteks** atau ketik kalimat konteks kelas yang benar-benar akan diucapkan (tanpa menyalin kata target).
4. **Rekam Video & Audio Bersamaan**: Klik **Rekam Klip (2,5 dtk)**. Peragakan isyarat BISINDO di depan webcam sambil mengucapkan kalimat konteks ke mikrofon. Pastikan tidak ada suara TTS/speaker keluar.
5. **Periksa Status UI**: Pastikan status menunjukkan jumlah frame (`>= 8` frame) dan durasi audio (`~2.5 dtk`) tanpa peringatan `audio = missing`.
6. **Verifikasi Visual Keypoints & Hand Crop**: Pastikan overlay kerangka 86 titik tampil pada preview kamera dan ringkasan menunjukkan `video 1 · citra 1 · audio 1 · teks 1 · lengkap 4 modalitas: 1`.
7. **Buat & Simpan ZIP**: Klik **Unduh Paket ZIP** dan simpan berkas `SignBridge_<SIGNER>_<TIMESTAMP>.zip` ke folder `data/raw/web_zips/`.

---

## Langkah 8–11: Ekstraksi, Manifest & Pemeriksaan Tensor M6 (Terminal)
8. **Ekstrak & Validasi ZIP + 9. Buat Manifest**:
   ```powershell
   python scripts/build_multimodal_manifest.py --zips data/raw/web_zips --out data/multimodal
   ```
   Pastikan output menunjukkan `lengkap 4 modalitas: 1` dan berkas `data/multimodal/manifest_multimodal.csv` terbentuk.
9. **Jalankan Preprocessing & 11. Periksa Tensor Input M6**:
   ```powershell
   python -c "from signbridge.multimodal.dataset import read_manifest, MultimodalSampleLoader; recs = read_manifest('data/multimodal/manifest_multimodal.csv'); s = MultimodalSampleLoader(recs).load(0); print({k: (v.shape, str(v.dtype)) if hasattr(v, 'shape') else v for k, v in s.items()}); print('modality_mask:', s['modality_mask'])"
   ```
   Pastikan keluaran sesuai kontrak M6:
   - `pose`: `(64, 86, 3)`, `float32`
   - `image`: `(3, 112, 112)`, `float32`
   - `audio`: `(64, 248)`, `float32`
   - `text`: `(64,)`, `int64`
   - `modality_mask`: `[1. 1. 1. 1.]`

> [!NOTE]
> Jangan menjalankan training M6 pada tahap P0-E. Jika melakukan uji coba *dry-run* dengan checkpoint `--smoke`, jangan melaporkan hasil inferensinya sebagai hasil model terlatih pada data nyata.
