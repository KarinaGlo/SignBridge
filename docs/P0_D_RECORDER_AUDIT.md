# LAPORAN AUDIT IMPLEMENTASI PEREKAM DATASET SIGNBRIDGE (TASK P0-D AUDIT)
**Proyek:** SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge  
**Fokus Evaluasi:** Audit Teknis Read-Only Fitur Recorder Multimodal (Frontend, Audio, Video, Keypoints, & Pipeline Ingesti)  
**Lokasi Direktori:** `D:\SEMESTER 5\ML\Projek_1`  
**Tanggal Audit:** 20 November 2026  
**Auditor:** Senior Frontend Engineer, Backend Engineer, dan Multimodal Data Pipeline Auditor  
**Status Audit:** **READY WITH ISSUES (FONDASI TEKNIS AKTIF, BUTUH 3 PERBAIKAN KRITIS SEBELUM AKUISISI DATA)**  

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Audit teknis secara *read-only* telah dilakukan terhadap seluruh berkas implementasi fitur Recorder:
- Frontend Web: `web/index.html`, `web/js/app.js`, `web/js/recorder.js`, `web/js/config.js`, `web/css/style.css`, `web/js/features.js`, `web/js/handcrop.js`.
- Pipeline Ingesti: `scripts/web_dataset_to_multimodal.py`, `scripts/build_multimodal_manifest.py`.
- Evaluasi Kepatuhan Protokol: `docs/P0_B_DATASET_PROTOCOL.md` dan `docs/P0_C_DATABASE_STORAGE_AUDIT.md`.

### Temuan Faktual Kunci:
1. **Fitur Perekaman 4 Modalitas Berjalan Fungsional di Browser:**  
   Implementasi `web/js/recorder.js` dan `web/js/app.js` benar-benar mengekstrak 86 keypoint MediaPipe Holistic, melakukan crop bounding box tangan $+25\%$ margin pada canvas $224 \times 224$, merekam audio mono 16 kHz PCM 16-bit durasi 2,5 detik, menampung teks kalimat, dan membungkusnya menjadi berkas `.zip` metode *STORE* yang valid. 11 test unit JavaScript lulus 100%.
2. **Tiga Hambatan Kritis (Critical Blockers) yang Ditemukan:**
   - **C1 — Kebocoran Data Teks (Text Shortcut Leakage):** Pada [`web/js/app.js:1044-1046`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1044-L1046), pemilihan target gloss secara otomatis memanggil `glossToSentenceLocal([targetSelect.value], "id")` yang mengisi kolom teks dengan kata target (misal isyarat `MAKAN` $\to$ teks `"Makan."`). Jika dibiarkan saat perekaman, model M6 akan mengalami jalan pintas leksikal (*shortcut learning*).
   - **C2 — Ketiadaan Aturan CSS `.app-view-panel`:** Berkas [`web/css/style.css`](file:///d:/SEMESTER%205/ML/Projek_1/web/css/style.css) **tidak memiliki aturan CSS sama sekali untuk kelas `.app-view-panel`**. Akibatnya, seluruh 7 panel halaman aplikasi (Terjemahan, Kelas, Riwayat, Panduan, Latihan, Perekam, Pengaturan) dirender bertumpuk secara vertikal dalam satu halaman panjang tanpa bisa disembunyikan.
   - **C3 — Berkas Video Mentah (.mp4/.webm) Tidak Disimpan:** `recorder.js` hanya menyimpan keypoint JSON dan gambar crop tangan JPG. Video mentah kamera tidak pernah direkam ke berkas kontainer video, bertentangan dengan protokol arsip primer P0-B.
3. **Potensi Feedback Akustik (Audio Screeching):** Pada [`web/js/recorder.js:263`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L263), `node.connect(ctx.destination)` menyalurkan audio mikrofon langsung ke speaker output saat merekam, yang dapat memicu dengung melengking jika pengguna tidak menggunakan headphone.

---

## 2. AUDIT RINCI KOMPONEN 4 MODALITAS

### A. Modalitas Video & Pose Keypoint
- **Mekanisme Perekaman:** [`web/js/app.js:261-266`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L261-L266) mengalirkan callback MediaPipe `onFrameKeypoints` ke `this.capture.pushFrame(kp86, rightHand21, leftHand21)` selama klip aktif (durasi 2,5 detik / 2500 ms).
- **Format Keypoint:** Deret array float32 `[F, 86, 3]` yang mencakup 9 titik tubuh atas, 21 titik tangan kiri, 21 titik tangan kanan, dan 35 titik wajah.
- **Ekspor Video:** Berkas video kamera mentah (`.mp4` / `.webm`) **TIDAK DIEKSPOR**. Yang diekspor ke ZIP hanyalah berkas koordinat `take_XX_kp.json`.
- **Kompatibilitas M6:** Loader M6 (`features.py:61-70`) dapat membaca `take_XX_kp.json` secara sempurna karena format JSON `{"keypoints": [...]}` didukung langsung dan di-resample linear ke 64 frame (`[64, 86, 3]`).

### B. Modalitas Citra (Crop Tangan)
- **Logika Ekstraksi Hand Crop:** [`web/js/recorder.js:207-238`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L207-L238) membandingkan jumlah titik tangan per frame. Frame dengan jumlah titik tangan terbanyak (*peak confidence*) diambil snapshot-nya.
- **Bounding Box:** Fungsi `computeHandCropBox` ([`web/js/handcrop.js:20`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/handcrop.js#L20)) menghitung kotak persegi di sekitar 21 titik tangan dengan margin bantalan **+25%**.
- **Resolusi & Format:** Canvas memotong dan me-resize gambar tangan ke $224 \times 224$ piksel JPEG (kualitas 0.90) sebagai `take_XX_hand.jpg`.
- **Pemeriksaan Gambar Kosong:** Jika tangan sama sekali tidak terdeteksi selama 2,5 detik, `handSnapshot` bernilai `null` dan berkas tidak disimpan. Hal ini secara tepat diterjemahkan oleh M6 sebagai modalitas hilang (`has_img = False`).

### C. Modalitas Audio (Ucapan Lisan)
- **Mekanisme Penangkapan:** [`web/js/recorder.js:254-263`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L254-L263) meminta stream mikrofon via `navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } })`.
- **Resampling & Format:** Chunks audio di-resample dari sample rate sistem (misal 44.1 kHz / 48 kHz) ke **16.000 Hz** via `resampleLinear`, lalu dienkode ke **WAV PCM 16-bit mono** via `encodeWavPCM16`.
- **Durasi & Sampel:** Klip 2,5 detik menghasilkan $\approx 40.000$ sampel (2,5 dtk $\times$ 16.000 Hz). Di Python, `features.py:fix_length` memastikan panjangnya tepat 40.000 sampel.
- **Sinkronisasi:** Audio dan video mulai ditangkap secara paralel saat `this.active = true` (garis waktu 2500 ms yang sama).
- **Temuan Resiko:** `node.connect(ctx.destination)` di baris 263 menyebabkan feedback audio jika tidak memakai headphone.

### D. Modalitas Teks (Konteks Percakapan)
- **Input Pengguna:** Input field `<input id="rec-sentence">` ([`web/index.html:1135`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html#L1135)) memungkinkan penutur memasukkan teks hingga 64 karakter.
- **Isu Auto-Fill Kritis:** [`web/js/app.js:1044-1046`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1044-L1046) memasang event listener yang menimpa isi teks setiap kali dropdown target diganti:
  ```javascript
  targetSelect.addEventListener("change", () => {
    sentenceEl.value = glossToSentenceLocal([targetSelect.value], "id");
  });
  ```
  Ini menghasilkan kebocoran leksikal langsung (misal: target `MAKAN` $\to$ kalimat `"Makan."`).
- **Penanganan Teks Kosong:** Jika dikosongkan, metadata mencatat string kosong `""`, dan M6 menandai `has_text = False` (modalitas teks hilang).

---

## 3. IDENTITAS SAMPEL & STRUKTUR EKSPOR ZIP

### A. Pola Identitas Aktual vs Protokol P0-B

| Atribut Identitas | Implementasi Aktual (`web/js/recorder.js:322`) | Standar Protokol P0-B (`docs/P0_B_DATASET_PROTOCOL.md`) | Evaluasi Konsistensi |
| :--- | :--- | :--- | :---: |
| **Pola Sample ID** | `${signer}_${category}_${target}_take${take}` | `SB_<SIGNER>_<GLOSS>_T<TAKE>` | **Berbeda Format** |
| **Contoh Nilai** | `S01_gloss_MAKAN_take01` | `SB_S01_MAKAN_T01` | Perlu standardisasi |
| **Path Berkas di ZIP**| `S01/gloss/MAKAN/take_01_hand.jpg` | `S01/MAKAN/SB_S01_MAKAN_T01_hand.jpg` | Berbeda subfolder |
| **Di Manifest M6** | `SignBridge_S01_1732100000:S01_gloss_MAKAN_take01` | `selfrec:SB_S01_MAKAN_T01` | Menggunakan prefix nama ZIP |

### B. Kelengkapan Berkas dalam ZIP
Fungsi `buildFiles()` ([`web/js/recorder.js:357-401`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L357-L401)) menghasilkan struktur berkas yang rapi dan konsisten:
- `manifest_selfrec.csv` (memuat daftar seluruh klip dalam paket).
- Deret berkas per klip:
  - `take_XX_kp.json` (Keypoint 86 titik).
  - `take_XX_hand.jpg` (Citra crop tangan 224x224).
  - `take_XX_portrait.jpg` (Citra wajah & tubuh atas 320px).
  - `take_XX.wav` (Audio ucapan 16 kHz mono).
  - `take_XX_meta.json` (Metadata klip & timestamp ISO).

---

## 4. AUDIT FRONTEND UI & CSS (`web/css/style.css`)

### Temuan Kegagalan Tampilan Panel (Critical Layout Bug)
- Di [`web/index.html:1102`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html#L1102), panel didefinisikan sebagai `<section id="panel-recorder" class="app-view-panel">`.
- Di [`web/js/app.js:203`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L203), navigasi tab mengubah class:
  ```javascript
  const panels = document.querySelectorAll(".app-view-panel");
  panels.forEach((p) => { p.classList.toggle("active", p.id === tabId); });
  ```
- **Pemeriksaan CSS:** Di [`web/css/style.css`](file:///d:/SEMESTER%205/ML/Projek_1/web/css/style.css), **TIDAK ADA SATU PUN RULE CSS UNTUK `.app-view-panel`**.
- **Dampak Nyata:** Semua panel memiliki nilai default browser `display: block`. Akibatnya, saat pengguna membuka tampilan aplikasi (`#view-app`), ketujuh panel muncul bertumpuk secara vertikal di satu halaman panjang! Pengguna harus menggulir jauh ke bawah melewati Terjemahan Langsung, Ruang Kelas, Riwayat Sesi, Panduan Bahasa, dan Latihan Mandiri hanya untuk menemukan panel Perekam Dataset.

---

## 5. KLASIFIKASI TEMUAN MASALAH (ISSUE PRIORITIZATION)

### A. TEMUAN CRITICAL (Wajib Diperbaiki Sebelum Pengumpulan Data)
1. **Auto-Fill Teks Membocorkan Label (Text Shortcut Learning):**
   - *Lokasi:* [`web/js/app.js:1044-1046`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/app.js#L1044-L1046).
   - *Kondisi:* Setiap penggantian dropdown target otomatis mengisi kolom teks dengan kata target (misal `"Makan."`).
   - *Dampak:* Model M6 belajar dari jalan pintas leksikal dan mengabaikan modalitas visual/audio.
   - *Rekomendasi:* Hapus event listener auto-fill tersebut dan ganti dengan bank template kalimat dialog kelas kontekstual tanpa kata target.
2. **Ketiadaan Rule CSS untuk `.app-view-panel`:**
   - *Lokasi:* [`web/css/style.css`](file:///d:/SEMESTER%205/ML/Projek_1/web/css/style.css).
   - *Kondisi:* Tidak ada definisi `.app-view-panel { display: none; }` dan `.app-view-panel.active { display: block; }`.
   - *Dampak:* Seluruh halaman aplikasi bertumpuk berantakan dan tab navigasi tidak menyembunyikan panel non-aktif.
   - *Rekomendasi:* Tambahkan deklarasi CSS tab switching yang tepat pada `web/css/style.css`.
3. **Ketiadaan Rekaman Berkas Video Mentah (.mp4/.webm):**
   - *Lokasi:* [`web/js/recorder.js:357-400`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L357-L400).
   - *Kondisi:* Perekam hanya mengekstrak koordinat JSON keypoint, tidak merekam stream video kamera ke berkas MP4/WebM.
   - *Dampak:* Tidak ada rekaman video mentah fisik untuk keperluan audit kualitas manusia dan arsip primer P0-B.
   - *Rekomendasi:* Tambahkan `MediaRecorder` sederhana untuk mengekspor klip `.webm` berdampingan dengan `_kp.json`.

### B. TEMUAN HIGH (Tinggi)
4. **Potensi Feedback Loop Audio (Howling / Screeching):**
   - *Lokasi:* [`web/js/recorder.js:263`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L263).
   - *Kondisi:* `node.connect(ctx.destination)` menyalurkan input mikrofon langsung ke speaker output.
   - *Dampak:* Bunyi dengung kencang jika perekaman dilakukan tanpa menggunakan earphone/headphone.
   - *Rekomendasi:* Lepaskan sambungan ke `ctx.destination` atau lewatkan ke GainNode dengan `gain.value = 0`.
5. **Ketiadaan Preview Kamera Mandiri pada Panel Perekam:**
   - *Lokasi:* [`web/index.html:1102-1143`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html#L1102-L1143).
   - *Kondisi:* Elemen video kamera `<video id="camera-video">` hanya berada di Panel 1 (`#panel-translate`). Jika Panel 1 disembunyikan dengan benar oleh CSS, penutur tidak dapat melihat dirinya sendiri saat berisyarat di Panel 6.
   - *Rekomendasi:* Pindahkan kamera ke kontainer bersama atau tampilkan preview kamera di panel perekam.

### C. TEMUAN MEDIUM (Sedang)
6. **Inkonsistensi Format Naming Sample ID:**
   - *Lokasi:* [`web/js/recorder.js:322`](file:///d:/SEMESTER%205/ML/Projek_1/web/js/recorder.js#L322).
   - *Kondisi:* Menggunakan format `${signer}_${category}_${target}_take${take}`, bukan `SB_<SIGNER>_<GLOSS>_T<TAKE>`.
   - *Rekomendasi:* Ubah generator `clipId` agar menghasilkan format P0-B `SB_S01_MAKAN_T01`.
7. **Kategori 'letter' Otomatis Dibuang oleh Manifest Builder:**
   - *Lokasi:* [`web/index.html:1128`](file:///d:/SEMESTER%205/ML/Projek_1/web/index.html#L1128), [`scripts/build_multimodal_manifest.py:66`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/build_multimodal_manifest.py#L66).
   - *Kondisi:* UI mengizinkan kategori `letter` (ejaan jari A–Z), tetapi manifest builder membuangnya karena M6 hanya menerima gloss.
   - *Rekomendasi:* Beri label pada UI bahwa perekam M6 dikhususkan untuk 20 kata pilot (gloss).

---

## 6. PENILAIAN AKHIR KESIAPAN (FINAL READINESS ASSESSMENT)

### **KEPUTUSAN: READY WITH ISSUES**

> **Dasar Keputusan:**  
> Seluruh algoritma inti (ekstraksi MediaPipe 86-titik, crop tangan bounding box $+25\%$, resampling audio WAV mono 16 kHz 16-bit, dan pengemasan ZIP tanpa kompresi) telah **terbukti bekerja secara benar dan lulus unit test**.  
> Namun, perekaman pilot 300 sampel **TIDAK BOLEH DIMULAI SEBELUM 3 ISU KRITIS DIPERBAIKI**:
> 1. Mematikan auto-fill teks leksikal shortcut.
> 2. Menambahkan CSS `.app-view-panel` agar UI tidak bertumpuk.
> 3. Menghilangkan sambungan audio ke `ctx.destination` untuk mencegah feedback screeching.

---

## 7. REKOMENDASI TAHAP IMPLEMENTASI P0-D

Setelah audit ini diserahkan, tahap implementasi perbaikan P0-D direkomendasikan dikerjakan dengan urutan:
1. **Langkah 1 (Frontend Fix):** Tambahkan CSS tab switching `.app-view-panel` di `web/css/style.css` dan perbaiki preview kamera.
2. **Langkah 2 (Anti-Shortcut Fix):** Ganti auto-fill `sentenceEl.value` di `web/js/app.js` dengan template konteks kalimat dialog kelas.
3. **Langkah 3 (Audio Safety):** Hapus `node.connect(ctx.destination)` di `web/js/recorder.js` agar tidak terjadi loop feedback suara.
4. **Langkah 4 (Standardisasi ID):** Sesuaikan generator ID klip di `web/js/recorder.js` agar menghasilkan format `SB_<SIGNER>_<GLOSS>_T<TAKE>`.
5. **Langkah 5 (Verifikasi Uji Rekam):** Jalankan perekaman 1 sampel uji coba di peramban, verifikasi ZIP di `data/raw/web_zips/`, ekstrak via `build_multimodal_manifest.py`, dan pastikan dibaca dengan benar oleh M6 loader.

