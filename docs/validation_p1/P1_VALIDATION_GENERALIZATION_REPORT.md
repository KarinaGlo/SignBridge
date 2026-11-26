# LAPORAN UTAMA AUDIT VALIDASI & GENERALISASI EKSPERIMEN I1-P1 (SIGNBRIDGE ASEAN)

> **Dokumen**: `docs/validation_p1/P1_VALIDATION_GENERALIZATION_REPORT.md`  
> **Modul**: Modality Image — BISINDO Alphabet Fingerspelling (I1)  
> **Model Target**: `runs/image_i1_mobilenetv3_p1/best.pt`  
> **Arsitektur**: `torchvision.models.mobilenet_v3_small` ($1.544.506$ parameter, $6,01\text{ MB}$)  
> **Dataset Uji**: Mendeley BISINDO Alphabet ($N = 670$ citra, $26$ kelas A–Z)  
> **Tanggal Audit**: 16 November 2026  
> **Auditor**: Senior Machine Learning Engineer & Model Auditor, SignBridge ASEAN  
> **Keputusan Akhir Audit**: **`VALIDATION PASSED WITH LIMITATIONS`**

---

## 1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)

Audit validasi dan generalisasi menyeluruh telah dilaksanakan terhadap model klasifikasi citra BISINDO **I1-P1 (MobileNetV3-Small Pretrained ImageNet)** untuk memverifikasi kebenaran klaim performa, menguji ketahanan terhadap *data leakage*, menganalisis keandalan skor keyakinan (*confidence calibration*), serta menilai kesiapan operasional integrasi webcam.

### Temuan Kunci Audit:
1. **Verifikasi Metrik Paripurna ($100\%$ Paritas)**:
   - Hasil evaluasi Test Set ($N = 670$) yang dilaporkan sebelumnya terbukti **valid, otentik, dan dapat direproduksi secara persis**:
     - **Test Accuracy**: **$61,1940\%$** (Reported: $61,19\%$)
     - **Test Macro F1**: **$61,5662\%$** (Reported: $61,57\%$)
     - **Test Macro Precision**: **$63,3004\%$** (Reported: $63,30\%$)
     - **Test Macro Recall**: **$61,2737\%$** (Reported: $61,27\%$)
   - Pengujian live forward-pass menggunakan `best.pt` menghasilkan **$0$ diskrepansi** terhadap `predictions.csv` ($670 / 670$ cocok).
2. **Integritas Artefak & Checkpoint**:
   - Checkpoint `best.pt` (SHA-256: `83c6a0933c8e1a2097ce6fa1198d8578826ed37731c18137c057fea129affee9`) utuh dan terverifikasi berasal dari **Epoch 18**.
3. **Audit Data Leakage**:
   - **Bebas Duplikasi Biner & Perseptual**: Ditemukan $0$ duplikasi hash SHA-256 dan $0$ near-duplicate dHash (Hamming distance $\le 2$) antar-split Train, Val, dan Test.
   - **Keterbatasan Subject-Level**: Metadata resmi Mendeley tidak menyertakan Subject/Volunteer ID, sehingga pemisahan dataset murni berbasis citra (*image-level*), bukan penutur (*subject-level*).
4. **Generalization Test**:
   - Infrastruktur pengujian eksternal (`data/external/bisindo_validation/` dan script [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py)) telah siap.
   - Status pengujian data luar saat ini adalah **`PENDING EXTERNAL DATA`** karena belum tersedianya citra dari sukarelawan eksternal.
5. **Kalibrasi Skor Keyakinan**:
   - Model terkalibrasi dengan sangat baik (**$ECE = 4,77\%$**, **Brier Score $= 0,1738$**). Pada rentang keyakinan tinggi ($\ge 80\%$), akurasi aktual mencapai **$94,90\%$**.
6. **Benchmark Latensi CPU**:
   - Model PyTorch forward-pass mencatat latensi rata-rata **$12,06\text{ ms}$** (median $10,32\text{ ms}$, throughput $82,9\text{ FPS}$).

---

## 2. TUJUAN AUDIT

Memastikan bahwa model P1 dievaluasi dengan metodologi yang valid dan jujur, tidak mengalami kebocoran data tersembunyi, dan memberikan gambaran realistis tentang performa sebenarnya sebelum melangkah ke tahap ekspor dan integrasi webcam.

---

## 3. INTEGRITAS ARTEFAK P1 (RINGKASAN TAHAP A)

Seluruh 10 file artefak utama berhasil divalidasi dengan checksum SHA-256 yang tercatat pada [`docs/validation_p1/artifact_integrity_report.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/artifact_integrity_report.md):
- Checkpoint `best.pt` dan `last.pt` berukuran tepat $6.302.825$ byte.
- Struktur bobot state_dict memiliki 244 tensor, dengan layer klasifikasi akhir `Linear(1024, 26)`.
- Tidak ada artefak yang rusak atau dimodifikasi pasca-pelatihan.

---

## 4. REVALIDASI METRIK TEST SET (RINGKASAN TAHAP B)

Laporan detail pada [`docs/validation_p1/metric_revalidation_report.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/metric_revalidation_report.md) mengonfirmasi:
- Tidak ada label kosong, NaN, atau indeks kelas di luar rentang $0\text{--}25$.
- Akurasi $61,19\%$ dan Macro F1 $61,57\%$ terbukti $100\%$ otentik.
- Seluruh 26 kelas memiliki *True Positives* positif (tidak ada lagi kelas dengan recall $0\%$, memecahkan masalah kelas C, D, N pada baseline P0).

---

## 5. AUDIT DATA LEAKAGE LANJUTAN (RINGKASAN TAHAP C)

Laporan detail pada [`docs/validation_p1/data_leakage_audit.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/data_leakage_audit.md):
- **Duplikasi Biner & Perseptual**: Tidak ada kebocoran visual langsung antar-split.
- **Subject-Level Caveat**: Karena ketiadaan identitas penutur pada metadata Mendeley, pemisahan dataset tidak dapat menjamin bahwa tangan sukarelawan di Test Set berbeda sepenuhnya dari Train Set. Oleh karena itu, akurasi $61,19\%$ mencerminkan evaluasi *subject-mixed*.
- **Background Retention**: Area kecil latar belakang pakaian di sela-sela jari tetap hadir setelah crop tangan.

---

## 6. GENERALIZATION TEST STATUS (RINGKASAN TAHAP D)

- Direktori struktur `data/external/bisindo_validation/A/` .. `Z/` telah dibuat.
- Template manifest standar [`data/external/bisindo_validation/external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv) telah disiapkan.
- Pipeline evaluasi non-destruktif [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) telah dibangun dan diuji.
- **Status Saat Ini**: **`PENDING EXTERNAL DATA`**. Model belum dapat diklaim memiliki generalisasi eksternal terbukti sebelum sukarelawan baru menyediakan sampel independen.

---

## 7. ANALISIS CONFIDENCE & KALIBRASI (RINGKASAN TAHAP E)

Laporan detail pada [`docs/validation_p1/confidence_error_analysis.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/confidence_error_analysis.md):
- **Nilai ECE Rendah ($4,77\%$)**: Model terkalibrasi dengan baik; probabilitas Softmax berkorelasi linier dengan akurasi aktual.
- **Penyaringan Kesalahan Melalui Thresholding**:
  - Pada skor keyakinan $\ge 0,80$, akurasi model mencapai **$94,90\%$**.
  - Pada skor keyakinan $< 0,40$, akurasi model anjlok ke **$28,22\%$**.
  - Ambang batas rekomendasi webcam: **$0,60$**.

---

## 8. ANALISIS ISYARAT STATIS VS DINAMIS (RINGKASAN TAHAP F)

Laporan detail pada [`docs/validation_p1/static_dynamic_class_analysis.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/static_dynamic_class_analysis.md):
- **Huruf I vs J**: Mengalami kebingungan silang simetris ($10$ kali tertukar) karena foto diam sukarelawan untuk huruf dinamis J menangkap pose awal kelingking ke atas yang identik dengan I.
- **Huruf Z**: Berhasil meraih akurasi $76,9\%$ karena pose miring telunjuk yang khas, tetapi masih tertukar dengan D dan X saat sudut tangan berubah.
- **Kesimpulan**: Isyarat dinamis membutuhkan model sekuensial (misalnya ST-GCN M1 berbasis koordinat keypoints) jika ingin mengenali trajektori gerak sejati.

---

## 9. INFERENCE BENCHMARK PROFILING (RINGKASAN TAHAP G)

Laporan detail pada [`docs/validation_p1/inference_benchmark_report.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/inference_benchmark_report.md):
- Latensi model forward-pass pada CPU lokal adalah **$12,06\text{ ms}$** ($82,9\text{ FPS}$).
- Model checkpoint berukuran **$6,01\text{ MB}$** ($1,545\text{ M}$ parameter).
- **Peringatan**: Angka 83 FPS adalah inferensi murni PyTorch CPU dan tidak boleh diklaim sebagai performa total sistem webcam browser (estimasi real-time webcam aktual di browser adalah $15\text{--}25\text{ FPS}$).

---

## 10. KESIAPAN INTEGRASI WEBCAM (RINGKASAN TAHAP H)

Laporan detail pada [`docs/validation_p1/webcam_integration_readiness.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/webcam_integration_readiness.md):
1. **Normalisasi**: Pastikan kanvas HTML5 menerapkan formula ImageNet mean/std yang sama.
2. **Aspect Ratio Crop**: Hindari stretching kotak tangan non-persegi secara langsung ke $224 \times 224$; wajib gunakan square padding/letterboxing.
3. **Temporal Stabilization**: Terapkan majority voting pada 5-7 frame terakhir dan ambang batas confidence minimum $0,60$.
4. **Ekspor ONNX**: Wajib diekspor secara terisolasi ke `runs/image_i1_mobilenetv3_p1/fingerspell_p1.onnx` sebelum menggantikan model produksi.

---

## 11. KETERBATASAN UTAMA (LIMITATIONS)

1. **Belum Ada Bukti Generalisasi Subjek Eksternal**: Akurasi $61,19\%$ diukur pada sukarelawan Mendeley yang mungkin bercampur antara Train dan Test.
2. **Keterbatasan Spasial 2D pada Gestur Mirip**: Pasangan D vs P ($20$ error) dan M vs N ($17$ error) sulit dibedakan pada gambar 2D resolusi rendah.
3. **Ketiadaan Sinyal Temporal**: Huruf dinamis J dan Z rentan salah klasifikasi pada frame transisi.

---

## 12. REKOMENDASI TINDAKAN (RECOMMENDATIONS)

1. **Pengumpulan Dataset Eksternal 5–10 Penutur Baru**: Gunakan template `data/external/bisindo_validation/` untuk menguji generalisasi nyata.
2. **Implementasi Letterbox Hand Crop di Frontend**: Mengurangi distorsi jari tangan penutur saat deteksi MediaPipe.
3. **Multi-Modal / Landmark Guidance (I1-P2)**: Padukan koordinat 21 titik tangan MediaPipe dengan citra crop untuk membedakan pasangan D vs P dan M vs N secara definitif.

---

## 13. KEPUTUSAN AKHIR AUDIT (FINAL DECISION)

Berdasarkan bukti empiris dan audit mendalam:

$$\mathbf{STATUS: \text{ VALIDATION PASSED WITH LIMITATIONS}}$$

- **Evaluasi internal valid, metrik konsisten $100\%$, dan model terkalibrasi dengan baik**.
- **Namun, status generalisasi eksternal masih PENDING EXTERNAL DATA, dan terdapat keterbatasan inheren subjek Mendeley serta isyarat dinamis**. Model siap untuk tahap uji coba terbatas (*controlled trial*), namun belum disarankan untuk langsung menggantikan model produksi tanpa stabilisasi temporal.

