# CHECKLIST KESIAPAN & EKSEKUSI VALIDASI EKSTERNAL (I1-P1)

> **Dokumen**: `docs/validation_p1/external_validation_checklist.md`  
> **Modul**: Modality Image I1 — BISINDO Alphabet Fingerspelling  
> **Tujuan**: Panduan Langkah Demi Langkah dari Pengumpulan Sampel hingga Evaluasi  
> **Status**: **`CHECKLIST READY`**

---

## 1. TAHAP PRA-PENGUMPULAN (*PRE-COLLECTION*)

- [x] Struktur direktori `data/external/bisindo_validation/` subfolder `A/` s.d. `Z/` telah siap.
- [x] Template metadata 14-kolom [`external_manifest_template.csv`](file:///d:/SEMESTER%205/ML/Projek_1/data/external/bisindo_validation/external_manifest_template.csv) telah siap.
- [x] Script evaluasi mandiri [`scripts/validation_p1/evaluate_external_images.py`](file:///d:/SEMESTER%205/ML/Projek_1/scripts/validation_p1/evaluate_external_images.py) telah teruji.
- [ ] Lembar persetujuan etika (*Informed Consent Form*) dicetak / disiapkan untuk 3 relawan baru.
- [ ] Poster / kartu acuan abjad BISINDO terverifikasi disiapkan di lokasi perekaman.
- [ ] Perangkat smartphone/kamera telah dibersihkan lensanya dan baterai terisi penuh.

---

## 2. TAHAP PENGAMBILAN DATA (*COLLECTION IN PROGRESS*)

- [ ] Relawan 1 (`EXT_S01`): 26 abjad $\times$ 10 foto = 260 foto selesai diambil.
- [ ] Relawan 2 (`EXT_S02`): 26 abjad $\times$ 10 foto = 260 foto selesai diambil.
- [ ] Relawan 3 (`EXT_S03`): 26 abjad $\times$ 10 foto = 260 foto selesai diambil.
- [ ] Verifikasi ketajaman: Tidak ada foto buram atau tangan terpotong frame kamera.
- [ ] Penamaan file: Seluruh foto mengikuti pola `[SIGNER_ID]_[LABEL]_[REPETITION].jpg`.
- [ ] Pencatatan manifest: Metadata 14 atribut per foto terisi lengkap tanpa baris kosong.

---

## 3. TAHAP PASCA-PENGUMPULAN & EVALUASI (*POST-COLLECTION & EVALUATION*)

- [ ] File citra dipindahkan ke subfolder masing-masing (`data/external/bisindo_validation/<A..Z>/`).
- [ ] File manifest final disimpan sebagai `data/external/bisindo_validation/manifest.csv`.
- [ ] Jalankan audit integritas berkas (pastikan tidak ada file berukuran 0 byte).
- [ ] Jalankan script evaluasi inferensi murni:
  ```bash
  python scripts/validation_p1/evaluate_external_images.py \
    --manifest data/external/bisindo_validation/manifest.csv \
    --checkpoint runs/image_i1_mobilenetv3_p1/best.pt \
    --out-dir runs/image_i1_mobilenetv3_p1/external_validation/
  ```
- [ ] Periksa laporan ringkasan `runs/image_i1_mobilenetv3_p1/external_validation/external_validation_summary.json`.
- [ ] Evaluasi akurasi total dan akurasi per penutur (`EXT_S01`, `EXT_S02`, `EXT_S03`).
- [ ] Bandingkan performa eksternal vs performa internal Test Set Mendeley ($61,19\%$).
- [ ] Dokumentasikan temuan pada laporan penutup `docs/validation_p1/EXTERNAL_TEST_RESULTS.md`.

