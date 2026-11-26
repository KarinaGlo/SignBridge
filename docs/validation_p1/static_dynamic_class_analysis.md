# AUDIT KHUSUS KELAS STATIS DAN DINAMIS: ANALISIS HURUF I, J, DAN Z (TAHAP F)

> **Dokumen**: `docs/validation_p1/static_dynamic_class_analysis.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Fokus Huruf**: `I`, `J`, dan `Z`  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Status Kesimpulan**: **`INHERENT TEMPORAL LIMITATION`** (Perlu Model Sekuensial untuk Isyarat Dinamis)

---

## 1. LATAR BELAKANG FONOLOGIS BISINDO

Dalam linguistik Bahasa Isyarat Indonesia (BISINDO), alfabet manual (*fingerspelling*) terbagi menjadi dua kategori utama:
1. **Isyarat Statis (*Static Handshapes*)**: Abjad yang direpresentasikan melalui konfigurasi bentuk tangan diam tanpa lintasan pergerakan (misalnya A, B, C, D, E, dll.).
2. **Isyarat Dinamis (*Dynamic Gestures / Stroke Gestures*)**: Abjad yang memerlukan trajektori pergerakan tangan dalam ruang spasial untuk melengkapi makna fonologisnya:
   - **Huruf J**: Dimulai dari pose kelingking tegak ke atas, kemudian ditarik ke bawah melengkung menyerupai mata kail (*hook stroke*).
   - **Huruf Z**: Menggunakan jari telunjuk tegak yang digerakkan di udara membentuk pola zig-zag tiga garis (*zig-zag stroke*).

Model **MobileNetV3-Small (I1)** saat ini adalah **pengklasifikasi citra tunggal 2D statis** ($1 \text{ frame} \to 26 \text{ kelas}$). Audit ini mengevaluasi dampak ketiadaan dimensi temporal pada performa pengenalan huruf-huruf tersebut.

---

## 2. BUKTI EMPIRIS KUANTITATIF DARI TEST SET (N = 670)

Berikut performa aktual model P1 pada huruf `I`, `J`, dan `Z`:

| Karakter | Tipe Isyarat Riil | Support Uji | Benar (TP) | Recall | Precision | F1-Score | Pola Kesalahan Terbanyak |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **I** | **Statis** | 26 | 11 | **$42,31\%$** | $50,00\%$ | $45,83\%$ | Tertukar ke **J ($5$ kali)**, **C ($5$ kali)**, Y ($2$ kali) |
| **J** | **Dinamis** | 25 | 15 | **$60,00\%$** | $45,45\%$ | $51,72\%$ | Tertukar ke **I ($5$ kali)**, **C ($2$ kali)**, Y ($1$ kali) |
| **Z** | **Dinamis** | 26 | 20 | **$76,92\%$** | $80,00\%$ | $78,43\%$ | Tertukar ke **D ($2$ kali)**, **X ($2$ kali)**, G ($1$ kali) |

---

## 3. ANALISIS KEBINGUNGAN SILANG ANTARA HURUF I DAN J

### Fenomena Kebingungan Simetris (Symmetric Confusion):
- **Huruf I diprediksi sebagai J**: $5$ sampel ($19,2\%$ dari support huruf I).
- **Huruf J diprediksi sebagai I**: $5$ sampel ($20,0\%$ dari support huruf J).
- **Total Kebingungan Silang I $\leftrightarrow$ J**: **$10$ sampel citra**.

### Mengapa Hal Ini Terjadi pada Citra Statis?
1. **Pose Diam Sukarelawan**:
   Karena dataset Mendeley berbasis foto diam (bukan rekaman video), sukarelawan yang memperagakan huruf `J` terpaksa "membekukan" gerakan tangan mereka pada salah satu titik waktu:
   - Jika difoto pada awal gerakan: Tangan memperlihatkan pose kelingking lurus ke atas &mdash; secara visual **identik $100\%$ dengan huruf I**.
   - Jika difoto pada akhir gerakan: Kelingking melengkung ke dalam &mdash; secara visual menyerupai varian lengkungan huruf C atau pose transisi.
2. **Ketiadaan Vektor Kecepatan (*Velocity Vector*)**:
   Model konvolusi 2D hanya menerima tensor spasial $[3, 224, 224]$. Tidak ada parameter $\frac{dy}{dt}$ atau $\frac{dx}{dt}$ yang menginformasikan bahwa tangan sedang meluncur turun. Akibatnya, pembeda antara I dan J terdegradasi menjadi tebakan berbasis detail mikro kulit atau noise latar belakang.

---

## 4. ANALISIS HURUF Z: MENGAPA RECALL DAPAT MENCAPAI 76,9%?

Meskipun huruf `Z` adalah isyarat dinamis, model meraih akurasi $76,92\%$ pada Test Set. Mengapa demikian?
- **Pose Khas (*Signature Keyframe*)**:
  Pada dataset Mendeley, para sukarelawan secara konsisten berpose menirukan awal goresan huruf Z: jari telunjuk mengacung ke depan dengan sudut miring horizontal tertentu ($\approx 45^\circ$) dan pergelangan tangan sedikit tertekuk.
- **Kesalahan yang Tersisa**:
  Ketika orientasi telunjuk sedikit lebih tegak atau menekuk, model langsung salah mengklasifikasikannya sebagai:
  - **D ($2$ kali)**: Telunjuk tegak lurus ke atas.
  - **X ($2$ kali)**: Telunjuk melengkung membentuk kait.
  - **G ($1$ kali)**: Telunjuk mengarah horizontal ke samping.

---

## 5. KESIMPULAN ARSITEKTURAL & KEBUTUHAN SEQUENCE MODEL

1. **Batas Teoretis Model Citra Tunggal**:
   Arsitektur citra 2D (seperti MobileNetV3 I1) secara fundamental **tidak mampu membedakan isyarat dinamis sejati secara konsisten** karena hilangnya dimensi temporal ($T$).
2. **Risiko pada Penggunaan Webcam Nyata**:
   Saat pengguna melakukan gerakan huruf `J` di depan webcam, frame-frame awal akan terdeteksi sebagai `I`, dan frame tengah mungkin terdeteksi sebagai `C` atau `J`.
3. **Solusi Rekayasa Sistem SignBridge**:
   - **Jangka Pendek (Heuristik Web)**: Terapkan *stabilization window* 5 frame di frontend JavaScript. Jika terdeteksi huruf `I` yang diikuti penurunan koordinat Y ujung kelingking (Landmark 20 MediaPipe), klasifikasikan sebagai `J`.
   - **Jangka Panjang (Sequence Model)**: Alihkan pengenalan gestur dinamis ke modul video atau modul landmark sekuensial (seperti ST-GCN M1 atau Temporal GRU) yang menerima deret koordinat $T \times 21 \times 3$.

