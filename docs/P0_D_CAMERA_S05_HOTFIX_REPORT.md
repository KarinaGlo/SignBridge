# LAPORAN HOTFIX P0-D: CAMERA PREVIEW RENDERING & S05 EXPERT SIGNER INTEGRATION

**Proyek:** SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge  
**Fase:** P0-D Hotfix  
**Tanggal:** 20 November 2026  
**Status Akhir:** **COMPLETE WITH ISSUES (MANUAL BROWSER VERIFICATION REQUIRED FOR VISUALS)**  

---

## 1. INVESTIGASI & AKAR MASALAH TERVERIFIKASI (ROOT CAUSE ANALYSIS)

### A. Masalah Pratinjau Kamera Tidak Terlihat di Panel Perekam
Melalui investigasi kode pada alur render visual `web/js/app.js` dan `web/js/vision.js`, ditemukan akar masalah ganda yang saling memperparah:

1. **Konflik Penghapusan Kanvas (*Canvas Erasure Conflict*):**
   - Pada implementasi sebelumnya di `web/js/app.js`, frame kamera digambar ke kanvas tunggal:
     ```javascript
     rCtx.drawImage(this.vision.videoEl, 0, 0, recCanvas.width, recCanvas.height);
     ```
   - Namun tepat setelah baris tersebut, fungsi penggambaran kerangka dipanggil:
     ```javascript
     drawSkeleton86(rCtx, kp86, recCanvas.width, recCanvas.height, { mirror: true });
     ```
   - Di dalam `web/js/vision.js` (baris 124), `drawSkeleton86()` mengeksekusi:
     ```javascript
     ctx.clearRect(0, 0, width, height);
     ```
   - **Dampak Nyata:** Gambar video kamera yang baru saja digambar langsung dihapus total oleh `clearRect()` sebelum browser sempat merendernya ke layar. Kanvas hanya menyisakan garis kerangka kawat transparan di atas wadah berlatar belakang gelap (`#091422`), sehingga tampak seolah-olah kamera tidak menyala atau mati total.

2. **Penundaan Rendering / Throttling Elemen `<video>` Tersembunyi:**
   - Elemen video kamera utama (`<video id="camera-video">`) berada di dalam `#panel-translate`.
   - Ketika penutur membuka `#panel-recorder`, kontainer `#panel-translate` disembunyikan menggunakan `display: none;`. Pada peramban Chromium/Edge, elemen video di dalam kontainer yang tidak aktif dapat mengalami penundaan update frame buffer sehingga pembacaan snapshot citra berisiko menerima frame kosong jika tidak memiliki elemen penampil aktif di panel yang sedang terbuka.

3. **Ketergantungan Loop Render pada Event MediaPipe:**
   - Penggambaran frame video sebelumnya hanya diletakkan di dalam `onFrameKeypoints`. Padahal, MediaPipe Holistic berjalan asinkron pada kecepatan 10–20 FPS (tergantung beban CPU/GPU) dan memerlukan beberapa detik saat pertama kali mengompilasi shader WebAssembly/OpenGL. Selama fase inisialisasi ini, kanvas tidak pernah menerima frame gambar apa pun.

### B. Masalah Integrasi S05 (Expert BISINDO Signer)
- Dropdown penutur pada `#panel-recorder` sebelumnya dibatasi hanya pada `S01`, `S02`, `S03`, dan `S04`.
- Perlu dipastikan bahwa penambahan `S05` tidak memicu *hardcoded constraint* di pipeline manifest builder atau split stratifikasi M6.

---

## 2. BERKAS YANG DIUBAH (FILES MODIFIED)

1. `web/index.html`
   - Menambahkan elemen video cermin `<video id="rec-camera-video" playsinline muted></video>` di dalam kontainer `.rec-preview-box`.
   - Menambahkan opsi `<option value="S05">S05 (Expert BISINDO)</option>` pada elemen `<select id="rec-signer">`.

2. `web/css/style.css`
   - Menata tata letak layered preview pada `.rec-preview-box`:
     - `video`: ukuran 100%, `object-fit: cover`, `transform: scaleX(-1)` (cermin selfie), rendering kontinu melalui GPU.
     - `canvas`: `position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;` (overlay transparan khusus kerangka skeleton 86 titik).

3. `web/js/vision.js`
   - Memperbarui `drawSkeleton86()` dengan parameter opsi `{ clear = true } = {}` (backward-compatible).
   - Memperbarui deteksi `isFlipped` agar mengenali canvas `#rec-camera-preview` dan kontainer `.rec-preview-box`.

4. `web/js/app.js`
   - Menambahkan metode siklus hidup kamera recorder: `syncRecorderCameraStream()` dan `detachRecorderCameraStream()`.
   - Mengalirkan stream kamera aktif tunggal (`this.vision.stream`) ke elemen `<video id="rec-camera-video">`.
   - Pada `onFrameKeypoints`, penggambaran kanvas recorder hanya menggambar overlay kerangka skeleton tanpa menduplikasi draw frame video secara CPU copy, menghilangkan lag performa.
   - Menginisialisasi `MultimodalCapture` dengan memprioritaskan elemen video yang sedang aktif (`rec-camera-video` atau `camera-video`).
   - Menyinkronkan status stream saat tab berpindah atau tombol "Nyalakan Kamera" ditekan.

5. `web/js/recorder.js`
   - Memperkuat metode `_snapshot()` di `MultimodalCapture` agar mengambil frame dari video element yang memiliki `videoWidth > 0`.

6. `tests/js/recorder.test.mjs`
   - Menambahkan unit test untuk opsi `clear: true` vs `clear: false` pada `drawSkeleton86()`.
   - Menambahkan unit test validasi identitas dan struktur berkas untuk penutur `S05` (`SB_S05_BELAJAR_T01`).

---

## 3. RINGKASAN SOLUSI TEKNIS (SOLUTION ARCHITECTURE)

```
                       [ Satu MediaStream Kamera ]
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
       [#camera-video] (Tab Utama)      [#rec-camera-video] (Tab Recorder)
             │                                       │
      MediaPipe Holistic                      Hardware Rendering
     (86 Landmark Stream)                 (60 FPS Mirrored Selfie View)
              │                                      │
              └───────────────┐ ┌────────────────────┘
                              ▼ ▼
                  [#rec-camera-preview (Canvas Overlay)]
                   - drawSkeleton86({ clear: true })
                   - Hanya menghapus layer skeleton transparan
                   - Video di belakangnya TIDAK PERNAH terhapus!
```

- **Keunggulan Solusi Layered:**
  1. Video kamera langsung menyala dan berjalan mulus (30–60 FPS) segera setelah kamera aktif, tanpa menunggu MediaPipe selesai mengompilasi model WASM.
  2. Kerangka 86 titik digambar tepat di atas video dengan orientasi cermin yang sinkron.
  3. Menggunakan 1 stream kamera tunggal dari `VisionManager` tanpa instansiasi perangkat kedua.
  4. Pengambilan crop tangan pada klip rekaman dijamin memiliki frame aktif karena mengambil dari video yang sedang terpasang di DOM aktif.

---

## 4. HASIL PENGUJIAN OTOMATIS (TEST RESULTS)

### A. JavaScript Test Suite (Node.js Test Runner)
Perintah:
```bash
node --test tests/js/*.test.mjs
```
**Hasil:** **32 passed, 0 failed** (Durasi: ~460 ms)
- `tests/js/recorder.test.mjs`:
  - `drawSkeleton86 menghormati parameter clear: true vs clear: false`: **PASSED**
  - `MultimodalRecorder mendukung penutur S05 (Expert BISINDO) dengan sample_id baku`: **PASSED**
  - Seluruh pengujian resampling, WAV header, escaping CSV, dan manifest 4 modalitas: **PASSED**
- Seluruh 30 pengujian JavaScript lainnya (vision parity, handcrop, recognizer, sentence): **PASSED**

### B. Python Multimodal Suite (Pytest)
Perintah:
```bash
python -m pytest tests/test_multimodal_features.py tests/test_multimodal_model.py tests/test_multimodal_service.py
```
**Hasil:** **22 passed, 0 failed, 3 warnings** (Durasi: 47 s)
- Fitur multimodal 4 cabang: **PASSED**
- Model M6 fusion, gated weighting, auxiliary loss: **PASSED**
- Ekspor ONNX runtime dan paritas numerik PyTorch ↔ ONNX: **PASSED**

---

## 5. RISIKO & KETERBATASAN TERSISA

1. **Akses Browser Wajib Localhost / HTTPS:**  
   API kamera `getUserMedia` diblokir oleh sistem keamanan peramban jika berkas dibuka via protokol `file:///`. Pengguna wajib menjalankannya melalui `http://localhost:8080`.
2. **Keterbatasan Perangkat Kamera Tunggal:**  
   Jika webcam fisik sedang dipakai oleh aplikasi video conference lain (Zoom, Meet, Teams), browser akan mengembalikan `NotReadableError`.
3. **Verifikasi Visual Belum Dilakukan Manual oleh Peneliti:**  
   Meskipun pengujian unit canvas dan stream binding telah lulus, pengujian visual pada layar monitor pengguna membutuhkan konfirmasi manual.

---

## 6. LANGKAH VERIFIKASI MANUAL DI BROWSER (MANUAL BROWSER TESTING)

Untuk memverifikasi tampilan kamera secara langsung di komputer Anda:

1. Buka terminal PowerShell di folder proyek dan jalankan server lokal:
   ```powershell
   cd "D:\SEMESTER 5\ML\Projek_1"
   python -m http.server 8080
   ```
2. Buka browser (Google Chrome atau Microsoft Edge) dan akses URL:
   ```text
   http://localhost:8080
   ```
3. Klik tombol navigasi sidebar **"Perekam Dataset"**.
4. Periksa dropdown **"Penutur"**: Pastikan opsi **"S05 (Expert BISINDO)"** muncul dan dapat dipilih.
5. Klik tombol **"Nyalakan Kamera"**:
   - Berikan izin (*Allow*) jika browser meminta izin kamera.
   - **Verifikasi Visual:** Layar pratinjau sekarang menampilkan video wajah/tubuh Anda secara cermin (*selfie view*) dengan latar belakang video langsung menyala.
   - Ketika Anda mengangkat tangan, kerangka MediaPipe (warna biru/ungu/kuning) akan muncul mengikuti pergerakan tangan dan wajah Anda.
6. Coba klik **"Rekam Klip (2.5 dtk)"**:
   - Status hitung mundur (3, 2, 1) akan berjalan di bawah video.
   - Kamera tetap menyala stabil selama klip direkam.
   - Klip tersimpan dengan ID format `SB_S05_<GLOSS>_T01`.

---

## 7. STATUS AKHIR

**Status:** **COMPLETE WITH ISSUES (MANUAL BROWSER VERIFICATION REQUIRED FOR VISUALS)**  
Implementasi kode, perbaikan alur render layered, dan integrasi penutur S05 telah selesai secara teknis dan diverifikasi oleh seluruh unit test otomatis. Status menunggu verifikasi visual langsung pada peramban pengguna.

