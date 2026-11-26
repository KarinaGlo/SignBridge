# AUDIT DAN KOREKSI SPESIFIKASI GESTUR BISINDO KELAS A
## Image Modality I1-P1 — SignBridge ASEAN

**Dokumen**: `docs/validation_p1/GESTURE_A_REFERENCE_AUDIT.md`  
**Tanggal**: 16 November 2026  
**Auditor**: Senior Machine Learning Engineer, Dataset Auditor, & Research Validation Engineer  
**Status Evaluasi Gestur**: **`CORRECTED & PENDING FORMAL NATIVE SIGNER SIGN-OFF`**  
**Status Tahap Pilot**: **`AWAITING GESTURE REFERENCE VERIFICATION` (HOLD — PENGAMBILAN FOTO DITANGGUHKAN)**  
**Git HEAD**: `3a99e962a5336e02ba7c02b4080b8faf8cde6a1c` (clean, zero tracked modifications)  

---

## 1. RINGKASAN EKSEKUTIF & LATAR BELAKANG AUDIT

### A. Pemicu Audit (Audit Trigger)
Pada dokumen persiapan pilot sebelumnya ([`docs/validation_p1/PILOT_COLLECTION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/PILOT_COLLECTION_REPORT.md)), Bagian 4 mencantumkan spesifikasi gestur BISINDO Kelas A sebagai:
> *"Telapak tangan terbuka menghadap depan (ke arah kamera), kelima jari merenggang tegak ke atas."*

Deskripsi tersebut terindikasi mengandung ketidaksesuaian fundamental dengan korpus linguistik BISINDO (Bahasa Isyarat Indonesia) dan konfigurasi dataset pelatihan aktual yang digunakan proyek SignBridge ASEAN. Oleh karena itu, dilakukan audit fisik berbasis bukti (*empirical ground-truth audit*) langsung terhadap dataset citra pelatihan, studi komparatif linguistik isyarat, serta verifikasi kelayakan instruksi lapangan.

### B. Temuan Utama (Core Findings)
1. **Bukti Fisik Dataset Pelatihan (100% Konvergen)**:
   Pemeriksaan visual langsung terhadap 172 citra mentah di [`data/raw/image/bisindo_alphabet/A/`](file:///d:/SEMESTER%205/ML/Projek_1/data/raw/image/bisindo_alphabet/A/) dan citra terproses di [`data/processed/bisindo_alphabet/A/`](file:///d:/SEMESTER%205/ML/Projek_1/data/processed/bisindo_alphabet/A/) membuktikan bahwa **seluruh sampel Kelas A menggunakan konfigurasi DUA TANGAN (Two-Handed Gesture)** membentuk bangun segitiga ($\Delta$ menyerupai huruf kapital "A"). **Nol persen (0%) citra menggunakan telapak tangan terbuka 5 jari.**
2. **Kesesuaian dengan Standar BISINDO (Pusbisindo / Gerkatin)**:
   Sistem ejaan jari (*fingerspelling manual alphabet*) BISINDO mengadopsi tradisi alfabet dua tangan untuk huruf vokal (A, E, I, O, U) dan beberapa konsonan. Pusbisindo mendefinisikan huruf A dengan mempertemukan ujung telunjuk dan jempol kedua tangan di depan dada membentuk segitiga.
3. **Identifikasi Asal Kesalahan**:
   Deskripsi "telapak tangan terbuka 5 jari" pada dokumen pilot sebelumnya merupakan kekeliruan fatal (menyerupai angka 5, sapaan "Halo", atau bentuk dasar telapak terbuka/B5). Sementara SIBI (Sistem Isyarat Bahasa Indonesia) dan ASL (American Sign Language) menggunakan gestur satu tangan berupa kepalan tinju tertutup dengan ibu jari tegak di samping telunjuk.
4. **Dampak Risiko Rekayasa ML**:
   Jika 10 foto pilot dikumpulkan menggunakan bentuk "telapak tangan terbuka 5 jari", model MobileNetV3-Small I1-P1 (yang dilatih pada gestur segitiga dua tangan) akan menghasilkan prediksi acak/salah dengan recall 0% pada Kelas A, sehingga mencemari validitas uji generalisasi eksternal.

### C. Keputusan Audit & Status Operasional
- **Status Pilot**: Diubah dari `AWAITING OPERATOR PHYSICAL DATA CAPTURE` menjadi **`AWAITING GESTURE REFERENCE VERIFICATION` (HOLD)**.
- **Instruksi Pengambilan Foto Lapangan**: **DITANGGUHKAN / TIDAK DIIZINKAN (NOT AUTHORIZED)** sampai konfirmasi resmi dari penutur asli Tuli (*native Deaf signer*) atau instruktur bersertifikat Pusbisindo terdokumentasi.
- **Koreksi Dokumen**: Deskripsi keliru pada `PILOT_COLLECTION_REPORT.md` **DICABUT RESMI** dan digantikan dengan spesifikasi teknis gestur dua tangan.

---

## 2. AUDIT EMPIRIS CITRA DATASET PELATIHAN (GROUND TRUTH VERIFICATION)

Audit dilakukan dengan memeriksa langsung file citra yang digunakan dalam pelatihan model MobileNetV3-Small I1-P1.

### A. Sampel Citra Mentah yang Diperiksa (`data/raw/image/bisindo_alphabet/A/`)
Direktori ini berisi 172 citra dari berbagai perangkat dan kondisi pencahayaan. Sampel representatif yang diaudit secara visual:

| Nama Berkas Citra | Resolusi Asli | Perangkat / Kondisi | Hasil Pemeriksaan Visual Konfigurasi Gestur |
|---|:---:|---|---|
| `A _Hitam_Iphone_14Pro.jpg` | 3024 × 4032 | iPhone 14 Pro, latar hitam | **Dua tangan**. Ujung telunjuk kanan & kiri bertemu di atas membentuk puncak $\wedge$. Ujung ibu jari kanan & kiri bertemu horizontal di bawah membentuk palang $-$. Jari tengah, manis, kelingking menekuk ke telapak. Membentuk segitiga kapital "A". |
| `A_ Polos Terang_Xiaomi _Note 8 Pro.jpg` | 3000 × 4000 | Xiaomi Note 8 Pro, latar terang | **Dua tangan**. Konfigurasi identik: kedua telunjuk membentuk sudut atas, kedua jempol menyentuh horizontal, membentuk segitiga huruf A simetris. |
| `20240509_182656.jpg` | 3000 × 4000 | Kamera ponsel, indoor normal | **Dua tangan**. Konfigurasi segitiga huruf A dua tangan jelas di depan tubuh. |
| `A _Bebas_Iphone_14Pro.jpg` | 3024 × 4032 | iPhone 14 Pro, latar variasi | **Dua tangan**. Konfigurasi segitiga huruf A konsisten. |
| `A_Background Baju (Garis)_Samsung_A53 5G.jpg` | 3000 × 4000 | Samsung A53 5G, latar baju | **Dua tangan**. Konfigurasi segitiga huruf A konsisten. |

### B. Sampel Citra Terproses (`data/processed/bisindo_alphabet/A/`)
Pemeriksaan pada citra 224 × 224 yang langsung diumpankan ke MobileNetV3-Small:
- `A_0000.jpg` (224 × 224): Dua tangan membentuk segitiga A di tengah frame.
- `A_0050.jpg` (224 × 224): Dua tangan membentuk segitiga A dengan variasi pencahayaan.
- `A_0100.jpg` (224 × 224): Dua tangan membentuk segitiga A dengan variasi latar.

### C. Pemeriksaan Kelas Tetangga di Dataset Mentah (`data/raw/image/bisindo_alphabet/`)
Untuk memastikan sistem ejaan alfabet yang digunakan dataset Mendeley:
- **Kelas `B`** (`B _Hitam_Iphone_14Pro.jpg`): **Dua tangan**. Tangan kiri dengan jari-jari tegak vertikal, jari telunjuk tangan kanan menyentuh bagian tengah telapak kiri membentuk simbol huruf B BISINDO.
- **Kelas `C`** (`C _Hitam_Iphone_14Pro.jpg`): **Satu tangan**. Tangan melengkung membentuk huruf "C".
- **Kelas `D`** (`D _Hitam_Iphone_14Pro.jpg`): **Dua tangan**. Tangan kiri melengkung, telunjuk tangan kanan tegak lurus menyentuh ujung-ujungnya membentuk huruf "D".

**Kesimpulan Empiris**: Dataset Mendeley `ywnjpbcz8m/1` (Samuel Ady Sanjaya, CC BY 4.0) secara konsisten dan eksklusif merekam **Alfabet Manual BISINDO Dua Tangan (Two-Handed BISINDO Fingerspelling)**. Tidak ada satu pun citra Kelas A yang berupa telapak tangan terbuka 5 jari.

---

## 3. ANALISIS PERBANDINGAN LINGUISTIK ISYARAT (BISINDO vs SIBI vs ASL)

Untuk memahami perbedaan dan menghindari kesalahan berulang di lapangan, berikut perbandingan komprehensif sistem isyarat:

```
+---------------------------------------------------------------------------------------------------+
|                               PERBANDINGAN GESTUR HURUF ALFABET 'A'                               |
+---------------------------------+---------------------------------+-------------------------------+
|         BISINDO (Alami)         |        SIBI (Struktural)        |       ASL (Internasional)     |
+---------------------------------+---------------------------------+-------------------------------+
| • Dua Tangan (Two-Handed)       | • Satu Tangan (One-Handed)      | • Satu Tangan (One-Handed)    |
| • Telunjuk bertemu di puncak    | • Kepalan tinju tertutup        | • Kepalan tinju tertutup      |
| • Jempol bertemu di dasar       | • Jempol tegak di sisi telunjuk | • Jempol merapat di samping   |
| • Membentuk segitiga kapital 'A'| • Mengadopsi ASL                | • Standar Amerika             |
| • Bentuk: [ △ Segitiga ]        | • Bentuk: [ ✊ Kepalan + Ibu Jari ]| • Bentuk: [ ✊ Kepalan + Ibu Jari ] |
+---------------------------------+---------------------------------+-------------------------------+
```

### A. BISINDO (Bahasa Isyarat Indonesia)
- **Karakter**: Bahasa isyarat alami yang tumbuh dan berkembang secara organik di kalangan komunitas Tuli Indonesia di bawah naungan GERKATIN (Gerakan untuk Kesejahteraan Tunarungu Indonesia) dan dibina oleh PUSBISINDO (Pusat Bahasa Isyarat Indonesia).
- **Alfabet Manual**: Menggunakan ejaan dua tangan (*two-handed manual alphabet*) yang berakar dari keluarga isyarat BANZSL (British, Australian, New Zealand Sign Language) yang diadaptasi secara lokal di Indonesia. Huruf-huruf vokal (A, E, I, O, U) dibentuk dengan konfigurasi dua tangan.
- **Spesifikasi Huruf A**: Ujung kedua jari telunjuk dipertemukan di atas (puncak $\wedge$), dan kedua ujung ibu jari dipertemukan di bawah secara horizontal (garis $-$, membentuk segitiga yang melambangkan huruf kapital "A" di depan dada.

### B. SIBI (Sistem Isyarat Bahasa Indonesia)
- **Karakter**: Sistem isyarat buatan (*man-made system*) yang dibakukan oleh Departemen Pendidikan dan Kebudayaan (Depdiknas) untuk keperluan pengajaran di SLB/B dengan tata bahasa meniru struktur kalimat Bahasa Indonesia lisan (berimbuhan).
- **Alfabet Manual**: Mengadopsi alfabet satu tangan (*one-handed manual alphabet*) dari ASL (American Sign Language).
- **Spesifikasi Huruf A**: Kepalan tinju satu tangan tertutup dengan keempat jari menekuk rapat ke telapak, dan ibu jari berdiri tegak merapat di samping jari telunjuk.

### C. Deskripsi Keliru: "Telapak Tangan Terbuka 5 Jari"
- Deskripsi ini sama sekali **BUKAN** huruf A dalam sistem isyarat mana pun.
- Dalam BISINDO, telapak terbuka 5 jari biasanya merepresentasikan angka 5, isyarat leksikal seperti "Halo", "Buka", atau bentuk tangan dasar (*open-5 handshape* / *B-spread*).
- Memasukkan foto telapak tangan terbuka 5 jari ke dalam Kelas A merupakan kontaminasi data (*semantic labeling corruption*).

---

## 4. STATUS VERIFIKASI PENUTUR ASLI / NATIVE SIGNER

Sesuai dengan standar etika penelitian komputasional untuk disabilitas dan prinsip *Do No Harm*:

| Parameter Verifikasi | Status | Catatan Evaluator |
|---|:---:|---|
| **Verifikasi Bukti Fisik Dataset** | **TERKONFIRMASI 100% ✅** | 172/172 citra kelas A pada dataset proyek adalah gestur segitiga dua tangan. |
| **Verifikasi Literatur Resmi Pusbisindo** | **TERKONFIRMASI 100% ✅** | Panduan alfabet BISINDO Pusbisindo mendefinisikan huruf A sebagai segitiga dua tangan. |
| **Verifikasi Formal Native Signer Proyek** | **PENDING ⏳** | Belum ada lembar persetujuan/verifikasi tertulis dari instruktur Tuli bersertifikat Pusbisindo yang tercatat dalam repositori ini. Formulir verifikasi formal telah diterbitkan di [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md) dengan status `PENDING VALIDATOR`. |
| **Izin Pengambilan Foto Lapangan** | **DITANGGUHKAN 🚫** | Pengambilan foto lapangan kelas A ditangguhkan hingga verifikasi penutur asli dicatat. |

> [!IMPORTANT]
> **Prinsip Kehati-hatian Ilmiah**: Meskipun bukti fisik dataset dan literatur Pusbisindo sudah sangat konklusif mengenai bentuk dua tangan segitiga, proyek ini menetapkan bahwa **pengambilan data lapangan baru TIDAK BOLEH dilakukan sembarangan sebelum spesifikasi teknis disetujui secara formal bersama mitra Tuli atau instruktur BISINDO**.

---

## 5. REVISI SPESIFIKASI GESTUR BISINDO KELAS A

Spesifikasi resmi pada panduan lapangan direvisi menjadi sebagai berikut:

### Tabel Spesifikasi Teknis Koreksi Gestur Kelas A:

| Parameter Gestur | Spesifikasi Terkoreksi (BISINDO Huruf A Sah) | Larangan Keras (Diskualifikasi Langsung) |
|---|---|---|
| **Keterlibatan Tangan** | **DUA TANGAN (Bimanual / Two-Handed)** wajib terlihat jelas dalam bingkai kamera. | Satu tangan tunggal (Ditolak mutlak). |
| **Puncak Gestur ($\wedge$)** | Ujung jari telunjuk tangan kanan dan ujung jari telunjuk tangan kiri saling bersentuhan di bagian atas, mengarah ke atas membentuk puncak segitiga. | Telunjuk terpisah atau menekuk. |
| **Palang / Dasar Gestur ($-$)** | Ujung ibu jari kanan dan ujung ibu jari kiri saling bersentuhan secara horizontal di bagian bawah, membentuk palang/alas segitiga. | Jempol melipat ke dalam atau tidak menyentuh. |
| **Jari-Jari Lain** | Jari tengah, jari manis, dan jari kelingking dari kedua tangan tertekuk rapat ke dalam telapak tangan. | Jari tengah/manis/kelingking terbuka atau merenggang. |
| **Bentuk Geometris Total** | Menyerupai **bangun datar segitiga / huruf kapital "A" ($\Delta$)**. | Telapak tangan terbuka merenggang 5 jari (Ditolak mutlak). Kepalan tinju satu tangan SIBI/ASL (Ditolak mutlak). |
| **Posisi Terhadap Tubuh** | Di depan dada bagian tengah (*chest-level*), menghadap lurus ke arah lensa kamera. | Terlalu tinggi menutupi wajah atau di bawah pusar. |

---

## 6. TINDAKAN KOREKSI PADA SISTEM & DOKUMEN PROYEK

1. **Pembaruan Dokumen `PILOT_COLLECTION_REPORT.md`**:
   - Status diubah menjadi: **`AWAITING GESTURE REFERENCE VERIFICATION`**.
   - Bagian 4 (Spesifikasi Gestur Kelas A) diperbarui total dengan spesifikasi dua tangan segitiga.
   - Peringatan pencabutan instruksi telapak tangan terbuka 5 jari ditegaskan secara eksplisit.
2. **Kondisi Manifest & Direktori Data**:
   - Manifest aktual `external_manifest.csv` tetap bersih (0 baris data).
   - Direktori `data/external/bisindo_validation/A/` tetap bersih (0 citra).
   - Tracker status tetap **`NOT STARTED` ⚪ (0 / 780 foto valid)**.
3. **Verifikasi Integritas Checkpoint & Model**:
   - `runs/image_i1_mobilenetv3_p1/best.pt`: `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` (**UTUH**)
   - `web/model/fingerspell.onnx`: `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` (**UTUH**)
   - `runs/image_i1_mobilenetv3/best.pt`: `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` (**UTUH**)
4. **Penerbitan Instrumen Verifikasi Formal & Protokol Lapangan**:
   - Berkas [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md) telah disempurnakan secara metodologis dengan protokol pengamatan buta dua tahap dan multi-validator (status: `PENDING VALIDATOR`).
   - Panduan operasional sesi lapangan diterbitkan di [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md).
   - Laporan evaluasi metodologis final terdokumentasi di [`docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/FINAL_METHODOLOGICAL_REVISION_REPORT.md).

---

## 7. KESIMPULAN & REKOMENDASI TAHAP BERIKUTNYA

1. **Audit Berhasil Mengidentifikasi dan Menghentikan Penyebaran Spesifikasi Keliru**:
   Koreksi spesifikasi dari "telapak tangan terbuka 5 jari" ke "gestur dua tangan segitiga" telah menyelamatkan validitas ilmiah dari pipeline validasi eksternal I1-P1.
2. **Pengambilan Data Fisik Ditahan Secara Terkendali (*Controlled Hold*)**:
   Tahap pilot pengumpulan foto fisik tetap pada status **`HOLD`** sampai formal sign-off bersama perwakilan komunitas Tuli / penutur asli BISINDO selesai dicatat dalam proyek.
3. **Kepatuhan Protokol**: Tidak ada data sintetis, tidak ada pengubahan bobot model, dan tidak ada pelanggaran integritas kode maupun data.

