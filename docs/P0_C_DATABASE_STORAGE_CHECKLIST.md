# CHECKLIST AUDIT BASIS DATA & SISTEM PENYIMPANAN DATA (TASK P0-C)
**Proyek:** SignBridge ID–PH Multimodal Classroom Bridge  
**Dokumen Acuan:** `docs/P0_C_DATABASE_STORAGE_AUDIT.md`  
**Sasaran Evaluasi:** Kesiapan Infrastruktur PostgreSQL 16 & Media Storage Menjelang P0-D  

---

## 1. CHECKLIST ARSITEKTUR & SKEMA POSTGRESQL

- [ ] **Konektivitas Database:** Aplikasi dapat terhubung ke PostgreSQL 16 via `DATABASE_URL` atau fallback aman ke SQLite lokal tanpa crash.
- [ ] **Dukungan Multimodal di `dataset_recordings`:**
  - [ ] Memiliki kolom `image_path` (VARCHAR).
  - [ ] Memiliki kolom `audio_path` (VARCHAR).
  - [ ] Memiliki kolom `text` (VARCHAR / TEXT).
  - [ ] Memiliki kolom `category` (VARCHAR, misal `gloss` atau `letter`).
  - [ ] Memiliki kolom `split` (VARCHAR, misal `train`, `val`, `test`).
- [ ] **Kesesuaian Foreign Key:** Kolom referensi konsep mendukung atau tidak memblokir kata-kata dari Kamus B (WL-BISINDO 32 Gloss).
- [ ] **Integritas Indexing:** Kolom `signer_id`, `gloss`, dan `recording_code` memiliki index untuk kueri cepat.

---

## 2. CHECKLIST PENYIMPANAN BERKAS FISIK (MEDIA STORAGE)

- [ ] **Direktori Penyimpanan Host:** Folder `data/raw/web_zips/` dan `data/multimodal/raw/` tersedia dan memiliki izin tulis.
- [ ] **Kelengkapan 4 Modalitas Per Sampel:**
  - [ ] Berkas keypoint pose tersedia (`*_kp.json` atau `*_kp.npz`).
  - [ ] Berkas crop tangan tersedia (`*_hand.jpg`).
  - [ ] Berkas audio ucapan tersedia (`*.wav`).
  - [ ] Metadata kalimat konteks tersedia di berkas JSON terkait (`*_meta.json`).
- [ ] **Format Berkas Sesuai Kontrak 7:**
  - [ ] Audio adalah WAV 16 kHz mono 16-bit PCM.
  - [ ] Citra crop tangan beresolusi $224 \times 224$ (atau $\ge 112 \times 112$).
  - [ ] Keypoint memiliki deret 86 titik koordinat MediaPipe.

---

## 3. CHECKLIST INTEGRITAS IDENTITAS SAMPEL & MANIFEST

- [ ] **Pola ID Unik:** Mengikuti pola `SB_<SIGNER>_<GLOSS>_T<TAKE>` secara seragam di seluruh subsistem.
- [ ] **Kesesuaian Manifest M6:** Berkas `manifest_multimodal.csv` memuat 10 kolom wajib:
  `clip_id, signer, category, gloss, label, kp_path, image_path, audio_path, text, split`.
- [ ] **Path Resolution:** Seluruh path relatif di dalam manifest dapat diselesaikan dengan benar oleh `signbridge/multimodal/dataset.py`.
- [ ] **Ketiadaan Berkas Orphan:** Tidak ada berkas media yang tersimpan di disk tanpa terdaftar di manifest atau database.

---

## 4. CHECKLIST PERSISTENSI DOCKER & KEAMANAN

- [ ] **Docker PostgreSQL Volume:** Volume `pgdata` dipetakan ke `/var/lib/postgresql/data` (bukan penyimpanan ephemeral container).
- [ ] **Docker Media Bind Mount:** Folder `./data` dipetakan ke `/app/data` di dalam container.
- [ ] **Proteksi Zip Slip:** Seluruh script ekstraksi ZIP memvalidasi bahwa `target_path.startswith(destination_folder)`.
- [ ] **Batas Ukuran Upload:** Server menolak payload media yang melebihi batas 10 MB per berkas.
- [ ] **Pencegahan Duplikasi:** Script manifest mendeteksi dan menolak klip dengan hash konten yang identik.

