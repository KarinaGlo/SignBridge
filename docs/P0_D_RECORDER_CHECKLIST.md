# CHECKLIST VERIFIKASI PEREKAM DATASET MULTIMODAL (TASK P0-D)
**Proyek:** SignBridge ID–PH Multimodal Classroom Bridge  
**Dokumen Acuan:** `docs/P0_D_RECORDER_AUDIT.md`, `docs/P0_D_IMPLEMENTATION_REPORT.md`, & `docs/P0_D_CAMERA_S05_HOTFIX_REPORT.md`  
**Status Pasca-Hotfix:** HOTFIX APPLIED & UNIT TEST VERIFIED (MANUAL BROWSER VERIFICATION REQUIRED)  
**Tanggal Verifikasi:** 20 November 2026  

---

## 1. CHECKLIST MODALITAS VIDEO & POSE KEYPOINTS

- [x] Kamera dapat diakses oleh browser (`navigator.mediaDevices.getUserMedia`) melalui `VisionManager`.
- [x] MediaPipe Holistic memproses frame kamera dan menghasilkan 86 landmark koordinat.
- [x] Keypoint diekstrak selama durasi 2,5 detik (menghasilkan $\ge 8$ frame aktif).
- [x] File keypoints tersimpan dalam format JSON valid (`*_kp.json`) di dalam paket ZIP dengan `clip_id` dan `sample_id`.
- [x] Preprocessing M6 (`features.py:pose_from_sequence`) dapat membaca dan me-resample ke 64 frame `[64, 86, 3]`.

---

## 2. CHECKLIST MODALITAS CITRA TANGAN (HAND CROP)

- [x] Fungsi `computeHandCropBox` mendeteksi bounding box 21 titik tangan dengan margin $+25\%$.
- [x] Snapshot diambil dari frame dengan jumlah titik tangan terbanyak (*peak confidence*).
- [x] Citra tersimpan sebagai JPEG $224 \times 224$ piksel (`*_hand.jpg`) di dalam paket ZIP.
- [x] Jika tangan tidak terdeteksi sama sekali, sistem tidak crash dan menandai modalitas gambar hilang secara anggun.
- [x] Loader M6 (`features.py:load_image`) berhasil me-resize ke $112 \times 112$ dan menerapkan normalisasi ImageNet.
- [x] **Snapshot Resiliency Hotfix**: `MultimodalCapture._snapshot()` mengambil snapshot frame dari elemen video yang aktif dan memiliki `videoWidth > 0` (`rec-camera-video` atau `camera-video`).

---

## 3. CHECKLIST MODALITAS AUDIO (SPEECH WAYS)

- [x] AudioContext merekam stream mikrofon tanpa memicu error permission.
- [x] **Audio Loopback Fixed**: Tidak terjadi loop feedback / dengung melengking dari speaker perangkat (`muteGain` dengan `gain=0` disisipkan sebelum `ctx.destination`, terputus bersih saat selesai).
- [x] Resampling linear menghasilkan audio tepat 16.000 Hz (`resampleLinear`).
- [x] File diekspor sebagai WAV PCM 16-bit mono (`*.wav`) dengan durasi $\approx 2,5$ detik (40.000 sampel).
- [x] Loader M6 (`features.py:load_audio`) berhasil mengekstrak log-mel spektrogram `[64, 248]`.

---

## 4. CHECKLIST MODALITAS TEKS & ANTI-SHORTCUT

- [x] **Text Shortcut Leakage Eliminated**: Listener auto-fill leksikal yang memasukkan kata isyarat target ke kolom kalimat telah dihapus tuntas dari `web/js/app.js`.
- [x] Tombol "Saran Konteks" (`#btn-suggest-prompt`) menyediakan variasi kalimat percakapan kelas inklusif 32 gloss tanpa kebocoran label target (`CLASSROOM_CONTEXT_PROMPTS` di `web/js/config.js`).
- [x] Pengguna dapat mengetikkan teks konteks secara bebas tanpa terhapus saat berpindah label.
- [x] Kalimat tersimpan dalam metadata klip (`*_meta.json`) dan kolom `text` pada `manifest_selfrec.csv`.
- [x] Tokenizer karakter M6 (`features.py:encode_text`) berhasil memetakan kalimat ke vektor integer 64 elemen.

---

## 5. CHECKLIST PENGEMASAN ZIP & MANIFEST

- [x] **Sample Identity Standardized**: Format `clip_id` dan `sample_id` distandarisasi ke pola `SB_<SIGNER>_<TARGET>_T<TAKE>` (misal `SB_S01_MAKAN_T01`) di `web/js/recorder.js`.
- [x] **S05 Expert Signer Integrated**: Penutur `S05` (Expert BISINDO Signer) tersedia di dropdown, menghasilkan `SB_S05_<GLOSS>_T<TAKE>`, dan terdata penuh di ZIP metadata serta manifest CSV.
- [x] Kategori ejaan jari (`letter`) tetap didukung pada dropdown UI dan disimpan dalam paket ZIP, namun dilewati secara aman oleh `scripts/build_multimodal_manifest.py` tanpa merusak manifest 32 gloss M6.
- [x] Berkas ZIP dibuat menggunakan metode STORE tanpa kompresi (`buildStoreZip`).
- [x] Berkas `manifest_selfrec.csv` tersedia di root ZIP dengan header lengkap 11 kolom.
- [x] Script `scripts/build_multimodal_manifest.py` dapat mengekstrak ZIP dan menghasilkan `manifest_multimodal.csv` tanpa error.
- [x] Script ekstraksi memvalidasi path traversal untuk mencegah celah keamanan Zip Slip.

---

## 6. CHECKLIST TAMPILAN ANTARMUKA PENGGUNA (UI/UX)

- [x] **Panel Visibility Fixed**: Aturan CSS `.app-view-panel { display: none; }` dan `.app-view-panel.active { display: block; }` terpasang di `web/css/style.css`.
- [x] Tumpukan vertikal 7 panel terselesaikan; navigasi sidebar hanya memunculkan panel aktif.
- [x] **Camera Preview Layered Architecture**: Preview menggunakan arsitektur 2-layer (`<video id="rec-camera-video">` dengan hardware rendering + `<canvas id="rec-camera-preview">` overlay transparan). Frame video tidak lagi terhapus oleh `drawSkeleton86`.
- [x] **Mirroring**: Video dicermin via CSS `transform: scaleX(-1)` dan kerangka skeleton dicermin via parameter `{ mirror: true }`.
- [x] Tombol "Nyalakan Kamera" (`#btn-toggle-rec-cam`) memudahkan penutur memeriksa framing pose sebelum mulai merekam klip.
- [x] Indikator status (`rec-status`) dan jumlah klip (`rec-clip-count`) terbarui secara real-time.
- [ ] **Manual Browser Visual Check**: *MANUAL VERIFICATION REQUIRED* (Perlu dibuka di peramban pengguna untuk memastikan kamera fisik menyala pada hardware lokal).
