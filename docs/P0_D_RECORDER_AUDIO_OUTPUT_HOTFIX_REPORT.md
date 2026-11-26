# LAPORAN TEKNIS P0-D: RECORDER AUTOMATIC SPEECH OUTPUT DISABLE & AUDIO ISOLATION

**Proyek:** SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge  
**Fase:** P0-D Hotfix — Audio Output Isolation  
**Tanggal:** 20 November 2026  
**Status Akhir:** **COMPLETE & VERIFIED (TEST SUITE 33/33 JS PASSED, 22/22 PYTHON PASSED)**  

---

## 1. INVESTIGASI & AKAR MASALAH TERVERIFIKASI (ROOT CAUSE ANALYSIS)

Melalui audit menyeluruh terhadap `web/js/app.js`, `web/js/vision.js`, `web/js/recorder.js`, `web/js/speech.js`, dan `web/js/config.js`, ditemukan **3 sumber pasti** mengapa suara otomatis (TTS dan nada chime lonceng) terdengar saat pengguna berisyarat di panel Perekam Dataset:

### Sumber 1: Klasifikasi Daring (Online Recognizers) Tetap Aktif di Latar Belakang
- Di dalam callback loop kamera `onFrameKeypoints` (`web/js/app.js`), baris kode:
  ```javascript
  this.recognizer.pushFrame(kp86, { hasVisibleHand, timestamp: now });
  this.fingerspeller.pushHandFrame(activeHand);
  ```
  sebelumnya dieksekusi secara tanpa henti tanpa mengecek tab yang sedang aktif.
- Saat penutur melakukan isyarat di `#panel-recorder`, gesture tersebut langsung diklasifikasikan oleh `SignRecognizer` (M0) dan `FingerspellRecognizer`.
- Ketika suatu gerakan atau abjad terdeteksi dengan keyakinan di atas ambang batas auto-speak ($\ge 0.50$), event handler memanggil:
  - `this.speakCurrentSentence(...)`
  - `speakText("Huruf " + letter, ...)`
- **Dampak Kritis:** Suara robot TTS ("Huruf A", "Makan", "Air", dsb.) otomatis berbunyi dari speaker komputer saat penutur sedang berisyarat.

### Sumber 2: Bunyi Lonceng (*Recognition Chime*) pada Modul `speech.js`
- Setiap kali `speakText()` dipanggil, fungsi `playRecognitionChime()` (`web/js/speech.js:73`) dieksekusi.
- Fungsi ini mengaktifkan oscillator Web Audio API:
  ```javascript
  osc.connect(gain);
  gain.connect(audioCtx.destination); // Terhubung langsung ke speaker fisik
  osc.start();
  ```
  yang membunyikan nada lonceng sinusoidal D5/A5 (587 Hz / 880 Hz) melalui pengeras suara.

### Sumber 3: Pengucapan Konfirmasi Selesai Merekam Klip
- Pada `bindRecorderControls()` di `web/js/app.js`, blok penyelesaian perekaman klip sebelumnya memanggil:
  ```javascript
  speakText(`Klip ${target} tersimpan`, "id-ID");
  ```
- Suara ini tidak hanya mengganggu, namun jika dipicu berulang juga memicu `speechSynthesis.cancel()` di latar belakang yang menghasilkan peringatan konsol `SpeechSynthesisErrorEvent { error: 'interrupted' }`.

> **Bahaya Terhadap Kualitas Dataset:**  
> Jika speaker mengeluarkan suara robot TTS dan lonceng Web Audio saat penutur merekam isyarat, gelombang suara dari speaker akan tertangkap oleh mikrofon dan **mengotori rekaman WAV 16 kHz** dataset multimodal M6. Oleh karena itu, panel perekam wajib **100% hening**.

---

## 2. BERKAS YANG DIUBAH (FILES MODIFIED)

1. **`web/js/app.js`**
   - Menambahkan pembatasan panel aktif pada loop pengenalan isyarat di `onFrameKeypoints`:
     ```javascript
     if (this.currentAppTab !== "panel-recorder") {
       // Hanya jalankan pengenal isyarat dan ejaan jari di luar panel perekam
       this.recognizer.pushFrame(...);
       this.fingerspeller.pushHandFrame(...);
     }
     ```
   - Menambahkan guard isolasi pada `speakCurrentSentence()`, `handleSignPrediction()`, dan `handleAlphabetPrediction()`:
     ```javascript
     if (this.currentAppTab === "panel-recorder") return;
     ```
   - Menghapus panggilan TTS `speakText('Klip ... tersimpan')` pada `bindRecorderControls()` dan menggantikannya dengan konfirmasi visual senyap di `#rec-status`:
     ```javascript
     setStatus(`Klip ${target} berhasil disimpan (${res.numFrames} frame, ${res.audioSeconds} dtk audio).`);
     ```
   - Menyinkronkan pembersihan antrean ucapan saat pengguna berpindah ke tab `#panel-recorder`:
     ```javascript
     if (tabId === "panel-recorder") {
       if (typeof window !== "undefined" && window.speechSynthesis) {
         window.speechSynthesis.cancel();
       }
       if (this.recognizer?.activeBuffer) {
         this.recognizer.activeBuffer = [];
       }
       ...
     ```

2. **`web/js/speech.js`**
   - Menambahkan *defense-in-depth safety guard* di gerbang utama `speakText()`:
     ```javascript
     if (typeof window !== "undefined" && window.signBridgeApp?.currentAppTab === "panel-recorder") {
       if (window.signbridgeDebug) {
         window.signbridgeDebug.lastTTS = { text: text || "", status: "muted_in_recorder_panel", timestamp: Date.now() };
       }
       return false;
     }
     ```
     Pemeriksaan ini berada sebelum pemanggilan `playRecognitionChime()` dan `SpeechSynthesisUtterance`, memastikan 0 nada lonceng dan 0 suara TTS dapat lolos ke speaker selama panel perekam aktif.

3. **`tests/js/recorder.test.mjs`**
   - Menambahkan regression test `speakText dinonaktifkan sepenuhnya saat berada di panel-recorder dan aktif kembali di panel-translate`.

---

## 3. SOLUSI TEKNIS & PEMISAHAN PERILAKU ANTAR-PANEL

| Fitur / Perilaku | Panel Penerjemah (`panel-translate`) | Panel Perekam Dataset (`panel-recorder`) |
|---|:---:|:---:|
| **Kamera 640×480 Mirrored** | AKTIF (Hardware Rendering) | AKTIF (Hardware Rendering) |
| **MediaPipe Holistic 86-Titik** | AKTIF | AKTIF (Feed Dataset + Visualisasi Overlay) |
| **Perekaman Keypoints (Video)** | IDLE (Hanya Buffer Sliding) | **AKTIF MEREKAM (Deret Frame JSON)** |
| **Perekaman Hand Crop (Image)** | IDLE | **AKTIF MEREKAM (224×224 JPEG)** |
| **Perekaman Mikrofon (Audio)** | Sesuai Fitur STT (Jika Ditekan) | **AKTIF MEREKAM (WAV PCM16 16 kHz Mono)** |
| **Audio Monitoring / Loopback** | TIDAK ADA (Gain = 0) | **TIDAK ADA (Gain = 0 / Senyap)** |
| **Online Sign Classifier (M0)** | **AKTIF** | **DINONAKTIFKAN (Suspended)** |
| **Abjad Fingerspell Classifier** | **AKTIF** | **DINONAKTIFKAN (Suspended)** |
| **Output Suara TTS Otomatis** | **AKTIF** (Dapat Dimatikan via Toggle) | **100% SENYAP (DIBLOKIR TOTAL)** |
| **Bunyi Lonceng Web Audio** | **AKTIF** | **100% SENYAP (DIBLOKIR TOTAL)** |

---

## 4. HASIL REGRESSION TESTS

### A. JavaScript Test Suite
```powershell
node --test tests/js/*.test.mjs
```
**Hasil:** **33 tests passed, 0 failed** (Durasi: ~297 ms)
- `speakText dinonaktifkan sepenuhnya saat berada di panel-recorder dan aktif kembali di panel-translate`: **PASSED**
  - Menguji `speakText("Halo dunia")` mengembalikan `false` dan tidak memanggil `speechSynthesis.speak()` saat di `panel-recorder`.
  - Menguji `speakText("Halo dunia")` otomatis aktif kembali saat berpindah ke `panel-translate`.
- `MultimodalRecorder menulis 4 modalitas + manifest lengkap`: **PASSED**
- `MultimodalRecorder mendukung penutur S05 (Expert BISINDO) dengan sample_id baku`: **PASSED**
- `drawSkeleton86 menghormati parameter clear: true vs clear: false`: **PASSED**
- Seluruh 29 tes lainnya (parity, handcrop, recognizer, sentence): **PASSED**

### B. Python Multimodal Suite (Pytest)
```powershell
python -m pytest tests/test_multimodal_features.py tests/test_multimodal_model.py tests/test_multimodal_service.py
```
**Hasil:** **22 tests passed, 0 failed, 3 warnings** (Durasi: ~65 s)
- Branch ekstraksi audio log-mel spektrogram `[64, 248]` tetap 100% kompatibel.
- Arsitektur model M6, Gated Fusion, Modality Dropout, dan ekspor ONNX tidak mengalami regresi apa pun.

---

## 5. KONFIRMASI PEREKAMAN AUDIO MIKROFON (WAV 16 KHZ)

Hotfix ini **SAMA SEKALI TIDAK MENGGANGGU** akuisisi audio mikrofon:
1. `navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } })` tetap dijalankan oleh `MultimodalCapture.capture()`.
2. `ScriptProcessorNode` menampung buffer PCM float32 secara utuh selama durasi 2,5 detik.
3. Resampling linear `resampleLinear` mengubah audio peramban (44.1 kHz / 48 kHz) ke tepat 16.000 Hz.
4. `encodeWavPCM16` menghasilkan berkas WAV PCM 16-bit mono 40.000 sampel yang disimpan ke dalam arsip ZIP (`*_meta.json`, `*.wav`).
5. Karena speaker fisik komputer 100% senyap, data audio yang direkam adalah murni suara penutur tanpa polusi artefak suara TTS komputer.

---

## 6. VERIFIKASI MANUAL DI BROWSER

Untuk membuktikan secara langsung di komputer Anda:
1. Jalankan `python -m http.server 8080` dan buka `http://localhost:8080`.
2. Masuk ke tab **"Perekam Dataset"**.
3. Nyalakan kamera dan gerakkan tangan / lakukan berbagai isyarat di depan webcam:
   - **Verifikasi 1:** Tidak ada suara robot TTS ("Huruf ...", dsb.) yang keluar dari speaker komputer Anda.
   - **Verifikasi 2:** Tidak ada bunyi lonceng Web Audio yang berbunyi.
   - **Verifikasi 3:** Konsol browser (`F12`) bersih dari galat `SpeechSynthesisErrorEvent { error: 'interrupted' }`.
4. Rekam 1 klip isyarat (misal `S05`, `MAKAN`):
   - Setelah selesai merekam 2,5 detik, sistem memberikan konfirmasi visual senyap di teks status tanpa membunyikan suara apa pun.
   - Unduh berkas ZIP: audio `.wav` di dalam ZIP berisi rekaman suara Anda secara bersih.
5. Pindah kembali ke tab **"Terjemahkan"**:
   - Fitur terjemahan dan TTS kembali berfungsi normal seperti sedia kala.

