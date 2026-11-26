# LEMBAR PENILAIAN VALIDASI BUTA BISINDO (BLIND VALIDATOR REVIEW SHEET)
## SignBridge ASEAN — Modul Image I1 (BISINDO Alphabet Fingerspelling)
### Dokumen Khusus Validator Tuli Tersertifikasi

---

### PANDUAN PENGISIAN UNTUK VALIDATOR
1. Lembar ini digunakan untuk menilai kualitas dan keabsahan visual dari **36 sampel citra bahasa isyarat BISINDO**.
2. Setiap sampel diberi kode anonim (`VAL-REV-001` s/d `VAL-REV-036`). Informasi label asli dan prediksi kecerdasan buatan telah **disembunyikan secara sengaja** untuk menjaga kenetralan evaluasi (blind review).
3. Berkas citra dapat dibuka langsung pada jalur berkas (*Image Relative Path*) yang tercantum di setiap baris.
4. Berikan tanda centang ($\checkmark$) atau tuliskan pilihan pada salah satu dari empat kolom keputusan:
   - **[1] Gestur Benar**: Bentuk tangan, orientasi jari, dan pose sepenuhnya sesuai dengan kaidah BISINDO untuk huruf yang dimaksud oleh peraga.
   - **[2] Label Salah**: Gestur tangan secara jelas memperagakan huruf BISINDO yang berbeda (tuliskan huruf aktual di kolom catatan).
   - **[3] Gestur Ambigu**: Pose tangan membingungkan, setengah tertutup, atau berada di antara dua huruf (misal antara M dan N, atau U dan V).
   - **[4] Tak Dapat Ditentukan**: Citra terlalu gelap, terlalu kabur, atau bagian tangan terpotong parah sehingga tidak dapat dinilai.
5. **Catatan Khusus**: Sampel bertanda `[TEST_SET_DIAGNOSTIC_ONLY]` dievaluasi semata-mata untuk diagnosis kesalahan model, dan hasilnya **dilarang keras digunakan untuk tuning model** guna menjaga integritas pengujian.

---

### TABEL PENILAIAN VALIDATOR (36 SAMPEL)

| No | Kode Anonim | Tag Metodologi | Image Relative Path | [1] Benar | [2] Salah | [3] Ambigu | [4] Tak Tentu | Huruf Usulan / Catatan Validator |
| :-: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `VAL-REV-001` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/K/K_0152.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 2 | `VAL-REV-002` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/C/C_0056.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 3 | `VAL-REV-003` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/Y/Y_0096.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 4 | `VAL-REV-004` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/R/R_0132.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 5 | `VAL-REV-005` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/M/M_0011.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 6 | `VAL-REV-006` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/O/O_0078.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 7 | `VAL-REV-007` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/D/D_0092.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 8 | `VAL-REV-008` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/N/N_0065.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 9 | `VAL-REV-009` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/J/J_0080.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 10 | `VAL-REV-010` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/E/E_0143.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 11 | `VAL-REV-011` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/F/F_0154.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 12 | `VAL-REV-012` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/N/N_0064.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 13 | `VAL-REV-013` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/T/T_0145.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 14 | `VAL-REV-014` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/E/E_0000.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 15 | `VAL-REV-015` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/B/B_0061.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 16 | `VAL-REV-016` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/Z/Z_0126.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 17 | `VAL-REV-017` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/O/O_0016.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 18 | `VAL-REV-018` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/C/C_0017.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 19 | `VAL-REV-019` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/Z/Z_0018.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 20 | `VAL-REV-020` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/V/V_0123.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 21 | `VAL-REV-021` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/B/B_0016.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 22 | `VAL-REV-022` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/C/C_0078.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 23 | `VAL-REV-023` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/C/C_0110.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 24 | `VAL-REV-024` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/D/D_0018.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 25 | `VAL-REV-025` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/H/H_0167.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 26 | `VAL-REV-026` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/Z/Z_0123.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 27 | `VAL-REV-027` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/Z/Z_0164.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 28 | `VAL-REV-028` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/O/O_0066.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 29 | `VAL-REV-029` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/O/O_0067.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 30 | `VAL-REV-030` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/M/M_0148.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 31 | `VAL-REV-031` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/U/U_0092.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 32 | `VAL-REV-032` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/A/A_0055.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 33 | `VAL-REV-033` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/B/B_0056.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 34 | `VAL-REV-034` | `TEST_SET_DIAGNOSTIC_ONLY` | `data/processed/bisindo_alphabet/L/L_0036.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 35 | `VAL-REV-035` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/O/O_0006.jpg` | [ ] | [ ] | [ ] | [ ] | |
| 36 | `VAL-REV-036` | `TRAIN_COHORT` | `data/processed/bisindo_alphabet/Y/Y_0036.jpg` | [ ] | [ ] | [ ] | [ ] | |

---

### LEMBAR PENGESAHAN VALIDATOR
- **Nama Validator**: ______________________________________
- **Lembaga / Komunitas**: ______________________________________
- **Tanggal Sesi Validasi**: ______________________________________
- **Tanda Tangan**: ______________________________________

