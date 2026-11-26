# ADJUDICATION REGISTER & TIE-BREAKER PROTOCOL
## SignBridge ASEAN — Modul Image I1 (BISINDO Alphabet Fingerspelling)
### Dokumen Tata Kelola Adjudikasi & Resolusi Ketidaksepakatan Validator Independen (Phase 2C.8 Standard)

> [!IMPORTANT]
> Register ini digunakan khusus untuk mendokumentasikan, meneliti, dan merekonsiliasi seluruh stimulus yang memicu ketidaksepakatan (*disagreement*) atau ambiguitas antara **Validator A (`VAL-A`)** dan **Validator B (`VAL-B`)** dalam protokol **BLIND LETTER IDENTIFICATION**.
> Proses resolusi dipimpin oleh **Validator C (`VAL-C`)** bertindak sebagai *Senior Linguistic Adjudicator* independen.

---

### 1. KRITERIA DAN ENAM PEMICU ESKALASI ADJUDIKASI (TRIGGERS)

Sebuah sampel stimulus anonim wajib didaftarkan ke dalam register adjudikasi ini apabila memenuhi minimal salah satu dari enam kondisi berikut:

1. **Letter Identification Divergence (Perbedaan Identifikasi Huruf)**:
   - Huruf yang diidentifikasi oleh `VAL-A` berbeda langsung dengan `VAL-B` (misal: `VAL-A` mengidentifikasi `M`, `VAL-B` mengidentifikasi `N`).
2. **Gesture Clarity Divergence (Perbedaan Keputusan Kejelasan Gestur)**:
   - Keputusan kejelasan `VAL-A` berbeda secara langsung dengan `VAL-B` (misal: satu memilih `IDENTIFIED`, yang lain memilih `AMBIGUOUS` atau `UNDETERMINABLE`).
3. **Ambiguity Flag (Status Gestur Samar)**:
   - Salah satu atau kedua validator memilih opsi `AMBIGUOUS` karena konfigurasi jari berada di antara dua huruf atau sudut pandang meragukan.
4. **Indeterminacy Flag (Status Gestur Tidak Dapat Ditentukan)**:
   - Salah satu atau kedua validator memilih opsi `UNDETERMINABLE` akibat cacat visual berat, kegelapan total, kekaburan parah, atau jari kunci terpotong (*border clipping*).
5. **Regional Variation Discrepancy (Konflik Variasi Daerah)**:
   - Terdapat perbedaan signifikan dalam interpretasi variasi dialek regional (`VAL-A` memilih `YES` dan `VAL-B` memilih `NO`, atau sebaliknya).
6. **Consensus vs Ground-Truth Divergence (Divergensi Konsensus terhadap Label Internal)**:
   - Pemicu audit internal: Kedua validator sepakat mengidentifikasi huruf tertentu (`let_a == let_b`), namun huruf tersebut berbeda dari label referensi internal dataset mentah (`let_a != ground_truth`). Pemicu ini dideteksi secara otomatis oleh script analisis internal tanpa mengekspos label asli kepada validator eksternal.

---

### 2. PROTOKOL KERJA RESOLUSI VALIDATOR C (VAL-C)

1. **Prinsip Evaluasi Buta Berkelanjutan (*Blinded Adjudication*)**:
   - Validator C mengevaluasi gambar stimulus secara independen menggunakan kode anonim `VAL-REV-001` s/d `VAL-REV-036`.
   - Validator C **dilarang keras** diberitahu label bawaan dataset mentah (*ground truth* asli), nama file mentah, split asal (`train`/`test`), maupun prediksi model P1.
2. **Kontrol Pengungkapan Konteks (*Context Disclosure Control*)**:
   - Validator C diperlihatkan catatan deskriptif kualitatif linguistik dari `VAL-A` dan `VAL-B` tanpa mengungkapkan identitas validator pengusul.
3. **Keputusan Konsensus Mengikat (*Binding Adjudication Consensus*)**:
   - Keputusan akhir Validator C bersifat mengikat (*final binding determination*) untuk penetapan konsistensi linguistik dan taksonomi anomali dataset.
4. **Proteksi Firewall Data Uji (*Test Set Leakage Firewall*)**:
   - Apabila sampel teradjudikasi merupakan kohort `TEST_SET_DIAGNOSTIC_ONLY` (19 sampel), hasil adjudikasi **hanya dicatat untuk diagnostik akurasi dan analisis kegagalan baseline P1**.
   - **DILARANG KERAS**: Mengubah test set split, melakukan re-labeling test set untuk retraining, atau menyetel threshold model P2 berdasarkan adjudikasi test set.

---

### 3. REGISTER ADJUDIKASI SAMPEL (TEMPLATE PELAPORAN RESMI)

*Catatan: Baris di bawah ini akan diisi secara otomatis oleh pipa analisis (`scripts/validation_p2/calculate_inter_rater_agreement.py`) segera setelah respons aktual dari Validator A dan Validator B diunggah.*

| Adjudication ID | Sample ID | Split Cohort | Val A Decision | Val A Letter | Val B Decision | Val B Letter | Discrepancy Type / Trigger | Val C Decision | Val C Letter | Final Adjudicated Label | Status | Adjudication Date |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| *Contoh: ADJ-001* | *VAL-REV-xxx* | *TRAIN_COHORT* | *IDENTIFIED* | *M* | *IDENTIFIED* | *N* | *Letter Divergence (M vs N)* | *PENDING* | *-* | *-* | *AWAITING_INPUT* | *-* |
| *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *(TBD)* | *WAITING_RESPONSES* | *-* |

---

### 4. METRIK DAN STATUS REKONSILIASI AKHIR

- **Total Stimulus Ditinjau**: 36
- **Total Kesepakatan Penuh (Unanimous Agreement)**: *Menunggu respons aktual*
- **Total Kasus Memerlukan Adjudikasi**: *Menunggu respons aktual*
- **Status Operasional Saat Ini**: `WAITING_FOR_HUMAN_VALIDATION` (0 respons masuk)
