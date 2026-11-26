# CHECKLIST KONTROL KUALITAS DATASET MULTIMODAL (TASK P0-B)
**Proyek:** SignBridge ID–PH Multimodal Classroom Bridge  
**Dokumen Acuan:** `docs/P0_B_DATASET_PROTOCOL.md`  
**Target Penggunaan:** Validasi Sampel Perekaman Mandiri (300 Sampel Pilot & 960 Sampel Ekspansi)  

---

## 1. PANDUAN PENGGUNAAN CHECKLIST

Gunakan checklist ini untuk menginspeksi setiap klip sebelum dimasukkan ke dalam manifest pelatihan `data/multimodal/manifest_multimodal.csv`. Klip harus memenuhi status **`VALID`** agar dapat digunakan dalam pelatihan baseline dan evaluasi utama M6.

---

## 2. CHECKLIST VALIDASI TEKNIS PER MODALITAS

### A. Modalitas Video & Pose Keypoint (`*_kp.json` / `*.mp4`)
- [ ] **Durasi Klip:** Panjang video adalah $2,5 \pm 0,2$ detik (~75 frame pada 30 FPS).
- [ ] **Framing Tubuh:** Kepala, leher, kedua bahu, siku, dan kedua tangan terlihat jelas di dalam frame kamera.
- [ ] **Signing Space:** Gerakan tangan tidak keluar dari tepi kiri, kanan, atas, maupun bawah frame.
- [ ] **Deteksi Keypoint:** MediaPipe Holistic menghasilkan koordinat non-nol untuk $\ge 8$ frame aktif.
- [ ] **Ketiadaan Oklusi Ekstrem:** Tangan tidak tertutup pakaian gelap yang menyatu dengan latar belakang.
- [ ] **Pencahayaan:** Tidak ada *backlight* (wajah dan tangan tidak siluet gelap).

### B. Modalitas Citra Tangan (`*_hand.jpg`)
- [ ] **Keberadaan File:** File crop tangan tersedia dengan ekstensi `.jpg` dan dapat dibuka oleh library Pillow / OpenCV.
- [ ] **Resolusi File:** Resolusi file adalah $224 \times 224$ piksel.
- [ ] **Fokus Objek:** Objek utama di tengah gambar adalah telapak tangan dan jari-jari penutur isyarat.
- [ ] **Margin Bantalan:** Bounding box memiliki margin bantalan $+25\%$ sehingga ujung jari tidak terpotong.
- [ ] **Bukan Gambar Statis Mendeley:** Gambar diekstrak dari klip video yang sama saat peragaan berlangsung.

### C. Modalitas Audio Ucapan (`*.wav`)
- [ ] **Format Kontainer:** Format WAV PCM 16-bit Little-Endian, 1 Channel (Mono).
- [ ] **Sampling Rate:** Tepat $16.000 \text{ Hz}$ (16 kHz).
- [ ] **Jumlah Sampel:** Tepat $40.000$ sampel (durasi 2,5 detik).
- [ ] **Tingkat Volume (RMS):** Nilai $\text{RMS} \ge 1 \times 10^{-4}$ (tidak hening total atau mikrofon mati).
- [ ] **Kejelasan Ucapan:** Kalimat diucapkan secara wajar, terdengar jelas tanpa distorsi clipping/pecah.
- [ ] **Kondisi Noise:** Bebas dari dengung frekuensi rendah atau interupsi suara pihak ketiga.

### D. Modalitas Teks Konteks (`text` pada metadata)
- [ ] **Panjang Kalimat:** Terdiri dari 3 hingga 10 kata (maksimal 64 karakter).
- [ ] **Karakter Valid:** Hanya menggunakan huruf kecil `a-z`, spasi, dan tanda baca `.,?!-'`.
- [ ] **Pencegahan Shortcut (Anti-Leakage):** Kalimat **TIDAK MENGANDUNG** kata isyarat target secara eksplisit.
- [ ] **Relevansi Konteks:** Kalimat merepresentasikan percakapan kelas inklusi yang relevan secara semantik dengan isyarat.

---

## 3. CHECKLIST INTEGRITAS SAMPLE ID & METADATA

- [ ] **Format Penamaan File:** Mengikuti pola `SB_<SIGNER_ID>_<GLOSS>_T<TAKE_ID>` secara konsisten.
- [ ] **Keunikan ID:** Nilai `sample_id` bersifat unik global di seluruh repositori (tidak ada ID ganda).
- [ ] **Kesesuaian Label:** Nilai `label` integer ($0 \dots 31$) sesuai 100% dengan mapping `GLOSS_TO_ID` pada `signbridge/constants.py:198`.
- [ ] **Keberadaan Berkas Metadata:** Berkas `*_meta.json` tersimpan berdampingan dan memuat timestamp ISO 8601.
- [ ] **Izin Etik (Consent):** `consent_status` bernilai `"granted"` untuk seluruh rekaman yang melibatkan subjek manusia.

---

## 4. MATRIKS KEPUTUSAN STATUS KLIP

| Kondisi | Status yang Diberikan | Tindakan Rekomendasi |
| :--- | :---: | :--- |
| Semua checklist di atas terpenuhi 100% | **`VALID`** | Masukkan ke manifest pelatihan (`split` ditentukan sesuai protokol LOSO). |
| Video, citra, dan teks valid, namun audio hening / noise | **`WARNING`** | Tetap masukkan ke manifest dengan audio di-mask ke 0 (`modality_mask[2] = 0`). |
| Teks mengandung kata target secara leksikal | **`WARNING`** | Edit teks pada metadata menjadi kalimat konteks netral sebelum manifest di-build. |
| Keypoint $< 8$ frame atau file video rusak | **`REJECTED`** | Buang sampel dan minta signer merekam ulang take tersebut. |
| Gloss tidak terdaftar pada 32 kata resmi | **`REJECTED`** | Buang sampel karena tidak kompatibel dengan arsitektur M6. |
| Terjadi duplikasi data persis (MD5/SHA256 sama) | **`REJECTED`** | Hapus berkas duplikat dari direktori penyimpanan. |

