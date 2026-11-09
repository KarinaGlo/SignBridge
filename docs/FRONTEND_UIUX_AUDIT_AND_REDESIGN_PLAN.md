# AUDIT FRONTEND UI/UX & RENCANA REDESIGN SIGNBRIDGE ASEAN

**Proyek**: SignBridge ASEAN — Antarmuka Web Inklusif (BISINDO & FSL)  
**Dokumen**: `docs/FRONTEND_UIUX_AUDIT_AND_REDESIGN_PLAN.md`  
**Status**: TAHAP 1 SELESAI (AUDIT & DESAIN SISTEM)  
**Tanggal**: 9 November 2026  
**Git Branch**: `feature/dataset-acquisition`  
**Git HEAD**: `b38b4da93b525f68edf4a9cfe6eb9331e13582e2`  

---

## 1. Audit Struktur Folder & File Frontend

```
web/
├── css/
│   └── style.css            (5.4 KB, Plus Jakarta Sans, basic utility styling)
├── js/
│   ├── app.js               (35.0 KB, Orkestrator utama antarmuka & event listeners)
│   ├── config.js            (15.9 KB, Konstanta 32 gloss BISINDO, 26 abjad, konsep ruang kelas)
│   ├── features.js          (9.7 KB, Normalisasi 86-keypoint & ekstraksi vektor ciri)
│   ├── fingerspell.js       (8.8 KB, Model ONNX ejaan jari 26 abjad A-Z & crop citra)
│   ├── handcrop.js          (7.0 KB, Algoritma crop bounding box tangan 224x224)
│   ├── icons.js             (1.7 KB, Inline SVG icons)
│   ├── recognizer.js        (17.4 KB, Student model ONNX Runtime Web & buffer inferensi)
│   ├── recorder.js          (5.7 KB, Perekam klip dataset multimodal WebM/WAV/ZIP)
│   ├── room.js              (3.2 KB, BroadcastChannel, WebSocket relay /ws/{kode}, P2P)
│   ├── sentence.js          (7.0 KB, Sintesis kalimat natural & pemetaan konsep)
│   ├── speech.js            (6.3 KB, Web Speech API TTS & STT listener)
│   └── vision.js            (20.4 KB, MediaPipe Holistic visualizer & rendering kanvas)
├── model/
│   ├── fingerspell.json     (Metadata kelas 26 abjad A-Z)
│   ├── fingerspell.onnx     (1.06 MB, MobileNetV3 fingerspelling)
│   ├── labels.json          (32 gloss BISINDO & FSL)
│   ├── student.onnx         (1.74 MB, StudentPoseTransformer ONNX fp32)
│   └── student_int8.onnx    (1.74 MB, Student ONNX int8)
├── index.html               (13.8 KB, Kerangka single-page application dasar)
├── manifest.webmanifest     (PWA manifest)
└── sw.js                    (Service worker cache)
```

---

## 2. Analisis Teknologi & Arsitektur Runtime

| Lapisan | Teknologi | Karakteristik & Status Operasional |
| :--- | :--- | :--- |
| **Frontend Runtime** | Vanilla ES Modules (Native Browser JS) | Bebas dependensi bundling Node.js runtime, kompatibel Chrome/Edge/Firefox modern. |
| **Styling** | Modern CSS Variables & Responsive Grid/Flexbox | Menggunakan font Google *Plus Jakarta Sans*, mendukung high-contrast & accessible styling. |
| **Komputer Visi** | MediaPipe Holistic JS (CDN) | Melacak 33 pose, 21 tangan kiri, 21 tangan kanan, dan 468 face landmark secara real-time. |
| **Inferensi On-Device** | ONNX Runtime Web (`ort.min.js` v1.18.0) | Menjalankan `student.onnx` (86 keypoints $\to$ 32 gloss) dan `fingerspell.onnx` (224x224 crop $\to$ 26 abjad) di WebAssembly/WebGL thread. |
| **Sinkronisasi Ruang** | Multi-Tier Sync (BroadcastChannel + WebSocket) | 1. BroadcastChannel (sinkronisasi instan multi-tab 1 perangkat tanpa internet).<br>2. WebSocket Relay `/ws/{kode}` ke server FastAPI.<br>3. Fallback P2P. |
| **Speech Engine** | Web Speech API (TTS & STT) | Suara otomatis teks-ke-suara bahasa Indonesia dan pengenalan suara ucapan guru/teman. |
| **Server Backend** | FastAPI (`server/app.py` port 7860) | Endpoint `/predict`, `/asr`, `/sentence`, `/translate`, `/db/*`, dan WebSocket `/ws/{kode}`. |

---

## 3. Identifikasi Fitur yang Sudah Berjalan & Fungsional

1. **Deteksi Gerakan Isyarat 86 Keypoint**:
   - MediaPipe Holistic melacak sendi tubuh dan tangan secara langsung melalui kamera.
   - Filter kecepatan (*velocity gating*) dan bounding-box tangan aktif mencegah false positive saat tangan beristirahat di bawah.
2. **Pengenalan Kata & Abjad Hibrida**:
   - Pengenalan 32 kata isyarat BISINDO $\leftrightarrow$ FSL menggunakan model student ONNX.
   - Pengenalan ejaan jari 26 abjad A–Z menggunakan crop tangan 224x224.
3. **Penyusunan Kalimat Natural**:
   - Algoritma tata bahasa *pseudo-gloss* menyusun deret kata isyarat menjadi kalimat bahasa Indonesia formal.
4. **Jembatan Komunikasi 3 Lapis (L1 / L2 / L3)**:
   - **L1 Concept**: Pemetaan konsep semantik BISINDO dan FSL.
   - **L2 Neural/Fallback MT**: Penerjemahan teks lintas bahasa (Indonesia $\leftrightarrow$ Filipino).
   - **L3 Reference Skeletal Player**: Animasi kanvas kerangka isyarat untuk memandu siswa Tuli.
5. **Speech-to-Text & Text-to-Speech**:
   - Guru/teman dengar berbicara $\to$ teks berukuran besar muncul di layar $\to$ animasi kerangka isyarat L3 ditampilkan.
   - Kalimat dari isyarat dibacakan otomatis via audio synthesizer browser.
6. **Sinkronisasi Multi-Perangkat (Ruang Kelas)**:
   - Satu ruangan kelas dengan kode bersama (misal: `BRIDGE-204`) dapat menyinkronkan teks, transkrip, dan giliran bicara antar-peserta.

---

## 4. Analisis Kesenjangan UI/UX (Eksisting vs Referensi SaaS)

Berdasarkan 5 screenshot referensi yang dilampirkan:

| Elemen UI/UX | Kondisi Eksisting | Standar Referensi SaaS Baru (Target Redesign) |
| :--- | :--- | :--- |
| **Navigasi Utama** | Tab horizontal monoton di atas halaman (`nav-tabs`). | **Sidebar navigasi SaaS profesional di sebelah kiri** (ikon modern, state aktif jelas, branding SignBridge, workspace dropdown, promo card aksesibilitas di bawah). |
| **Landing Page** | Tidak tersedia (langsung masuk ke form teknis). | **Landing page SaaS kelas dunia**: Dark navy hero (`#0B1F35`), live interactive app preview, feature strip, dual value-prop cards, 3-step workflow, bilingual comparison, classroom showcase, accessibility pillars, metrics, FAQ accordion, dan footer 4 kolom. |
| **Live Translation** | Card terpisah dengan kontrol sederhana. | **Kamera besar terfokus di tengah dengan live subtitle ribbon navy di bawah video**, status pulse `Mengenali Isyarat`, bilah peserta dengar (`Raka Pratama · Mendengarkan`), kontrol bar lengkap (Kamera, Mic, Teks, Fullscreen), serta **panel percakapan di sebelah kanan dengan chat bubble interaktif & ukuran teks dinamis**. |
| **Ruang Kelas** | Layout 2 kolom teknis tanpa konteks presentasi materi. | **Ruang Kelas Inklusif**: Kode kelas `BRIDGE-204` dengan tombol salin cepat, badge `4 perangkat terhubung`, materi pelajaran bersama (slide edukasi, 3 langkah interaktif), notifikasi interaktif `Ayu ingin berkontribusi` dengan tombol `Berikan Kesempatan`, bilah peserta & perangkat, serta obrolan kelas real-time. |
| **Bahasa & Istilah** | Campuran Inggris & Indonesia (mis. "Sign state Idle", "Auto-speak TTS", "Hybrid", "Viewport"). | **100% Bahasa Indonesia**: "Mulai Percakapan", "Ruang Kelas", "Terjemahan Langsung", "Riwayat Sesi", "Panduan Bahasa", "Pengaturan & Aksesibilitas", "Kamera Aktif", "Mikrofon Aktif", "Teks Aktif", "Menunggu giliran berikutnya...". |
| **Animasi & Feedback** | Tidak ada animasi (perpindahan tab instan/kaku). | **Transisi fade & slide lembut (200–350 ms)**, hover micro-interactions pada tombol, indikator suara gelombang berdenyut saat audio aktif, pulse dot hijau saat AI mengenali isyarat, dan toast notification modern. |
| **Aksesibilitas** | Ukuran font tetap, tanpa mode kontras tinggi. | **Kontrol ukuran teks caption (Aa: Normal / Besar / Ekstra Besar)**, font *Plus Jakarta Sans*, kontras warna WCAG AAA, focus indicators, dan kepatuhan `prefers-reduced-motion`. |

---

## 5. Rencana Eksekusi Bertahap

- [x] **Tahap 1 — Audit Frontend & Pemetaan Arsitektur** (Dokumen ini selesai).
- [ ] **Tahap 2 — Design System & Global Styles** (`web/css/style.css` diperbarui dengan palette warna SaaS navy `#10243E`/`#0B1F35`, teal `#10B8A6`, spacing sistematis, typography, button variants, card styling, dan animasi keyframes).
- [ ] **Tahap 3 — Redesign Komponen & Struktur Halaman** (`web/index.html` direstrukturisasi menjadi arsitektur multi-view terpadu: Landing Page, Dashboard Sidebar Shell, Live Translation, Ruang Kelas, Riwayat Sesi, Panduan Bahasa, dan Pengaturan).
- [ ] **Tahap 4 — Integrasi Controller JS & Animasi Interaktif** (`web/js/app.js` dan modul pendukung diperbarui untuk mengontrol navigasi sidebar, interaktivitas landing page, toggle caption size, raise-hand classroom interaction, audio waveform, dan sinkronisasi real-time tanpa merusak model ONNX/MediaPipe).
- [ ] **Tahap 5 — Optimasi Responsivitas & Aksesibilitas** (Desktop, tablet, smartphone drawer, keyboard navigation, contrast ratio).
- [ ] **Tahap 6 — Verifikasi Komprehensif** (Pengujian seluruh tombol, kamera, mic, Web Speech API, ONNX loading, WebSocket/BroadcastChannel room, dan regresi).

