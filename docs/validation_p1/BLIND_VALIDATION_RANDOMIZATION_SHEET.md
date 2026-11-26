# LEMBAR PENUGASAN URUTAN RANDOMISASI STIMULUS VALIDASI BUTA
## Blind Validation Randomization Assignment Sheet — BISINDO Kelas A
### Proyek: SignBridge ASEAN | Image Modality I1-P1 (MobileNetV3-Small)

**Dokumen**: `docs/validation_p1/BLIND_VALIDATION_RANDOMIZATION_SHEET.md`  
**Modul**: Image Modality I1 — BISINDO Alphabet Fingerspelling  
**Dokumen Instrumen Acuan**: [`docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BISINDO_A_FORMAL_VERIFICATION_FORM.md)  
**Dokumen Protokol Sesi**: [`docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p1/BLIND_VALIDATION_SESSION_PROTOCOL.md)  
**Tanggal Penerbitan**: 16 November 2026  
**Status Penggunaan**: **`PRE-GENERATED / STANDBY FOR FIELD EXECUTION`**  
*(Catatan Integritas: Urutan randomisasi ini adalah protokol yang telah di-generate secara deterministik dan BELUM digunakan dalam sesi nyata)*  

---

## 1. TUJUAN & METODE RANDOMISASI

Lembar penugasan ini dibuat untuk menghilangkan risiko kebiasaan urutan bawaan (*order habituation*) dan memutus pola selang-seling target-pembanding ($A \to B \to A \to C \to A \to D \to A$) pada kode stimulus dasar (`IMG_BLD_01` s.d. `IMG_BLD_07`).

Setiap validator diberikan **urutan penyajian unik (*unique presentation sequence*)** yang di-generate menggunakan algoritma pengacakan pseudo-random dengan nilai *random seed* tetap yang dapat direproduksi (*fully reproducible*).

### Algoritma & Formula Reproduksi:
```python
import random

stimuli = ["IMG_BLD_01", "IMG_BLD_02", "IMG_BLD_03", "IMG_BLD_04", "IMG_BLD_05", "IMG_BLD_06", "IMG_BLD_07"]

# Formula pengacakan per validator:
rng = random.Random(seed)
order = stimuli.copy()
rng.shuffle(order)
```

---

## 2. LEMBAR KERJA ENUMERATOR (ENUMERATOR-FACING ASSIGNMENT TABLE)

> [!IMPORTANT]
> **PANDUAN BAGI ENUMERATOR / NOTULIS**:
> 1. Gunakan tabel di bawah ini untuk menentukan urutan kartu/slide yang ditampilkan kepada masing-masing validator pada **Tahap 1 (Blind Observation)**.
> 2. Jangan pernah membocorkan kode stimulus berikutnya sebelum validator selesai menjawab stimulus yang sedang ditampilkan.
> 3. Catat tanggal pelaksanaan sesi, nama enumerator, dan paraf verifikasi pada kolom yang disediakan.
> 4. Tabel ini sengaja **TIDAK MEMUAT LABEL KELAS ASLI** untuk menjaga objektivitas enumerator.

### Tabel Urutan Penyajian Terandomisasi per Validator

| Validator ID | Random Seed | Posisi 1 | Posisi 2 | Posisi 3 | Posisi 4 | Posisi 5 | Posisi 6 | Posisi 7 | Tanggal Sesi Nyata | Nama Enumerator | Status Sesi |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `VAL_BISINDO_01` | `20261101` | `IMG_BLD_02` | `IMG_BLD_03` | `IMG_BLD_05` | `IMG_BLD_04` | `IMG_BLD_07` | `IMG_BLD_01` | `IMG_BLD_06` | `[ BELUM ]` | `[ ............... ]` | `BELUM DIGUNAKAN` |
| `VAL_BISINDO_02` | `20261102` | `IMG_BLD_03` | `IMG_BLD_07` | `IMG_BLD_06` | `IMG_BLD_02` | `IMG_BLD_04` | `IMG_BLD_01` | `IMG_BLD_05` | `[ BELUM ]` | `[ ............... ]` | `BELUM DIGUNAKAN` |
| `VAL_BISINDO_03` *(Cadangan/Lintas-Wilayah)* | `20261103` | `IMG_BLD_04` | `IMG_BLD_03` | `IMG_BLD_07` | `IMG_BLD_05` | `IMG_BLD_06` | `IMG_BLD_02` | `IMG_BLD_01` | `[ BELUM ]` | `[ ............... ]` | `BELUM DIGUNAKAN` |
| `VAL_BISINDO_04` *(Cadangan/Lintas-Wilayah)* | `20261104` | `IMG_BLD_01` | `IMG_BLD_04` | `IMG_BLD_05` | `IMG_BLD_03` | `IMG_BLD_02` | `IMG_BLD_07` | `IMG_BLD_06` | `[ BELUM ]` | `[ ............... ]` | `BELUM DIGUNAKAN` |

---

## 3. VERIFIKASI POLA RANDOMISASI

Pemeriksaan urutan membuktikan bahwa pengacakan berhasil memecah pola ritmis:
- **`VAL_BISINDO_01`**: Dimulai dari citra pembanding (`IMG_BLD_02`), diikuti dua citra target (`03`, `05`), pembanding (`04`), dua target (`07`, `01`), dan diakhiri pembanding (`06`).
- **`VAL_BISINDO_02`**: Dimulai dari dua citra target (`IMG_BLD_03`, `07`), diikuti pembanding (`06`, `02`, `04`), dan diakhiri dua target (`01`, `05`).
- Seluruh urutan memuat tepat 7 stimulus tanpa repetisi dan tanpa ada stimulus yang terlewat ($7/7$ permutasi lengkap).

---

## 4. BAGIAN MAPPING KELAS AKTUAL (RESEARCHER-ONLY MAPPING SECTION)

> [!CAUTION]
> **HANYA DAPAT DIAKSES OLEH LEAD RESEARCH METHODOLOGIST & AUDITOR DATASET**.
> Bagian ini **DILARANG KERAS DICETAK ATAU DIBERIKAN** kepada enumerator lapangan, Juru Bahasa Isyarat, maupun validator sebelum Tahap 1 (Blind Observation) selesai dan dikunci.

| Kode Stimulus Anonim | Kelas Aktual | Tipe Sampel | Path Berkas Sumber di Repository |
|:---:|:---:|:---:|---|
| `IMG_BLD_01` | **Kelas A** | Target Utama | `data/raw/image/bisindo_alphabet/A/A _Hitam_Iphone_14Pro.jpg` |
| `IMG_BLD_02` | **Kelas B** | Distractor Pembanding | `data/raw/image/bisindo_alphabet/B/20240509_182924.jpg` |
| `IMG_BLD_03` | **Kelas A** | Target Utama | `data/raw/image/bisindo_alphabet/A/A_ Polos Terang_Xiaomi _Note 8 Pro.jpg` |
| `IMG_BLD_04` | **Kelas C** | Distractor Pembanding | `data/raw/image/bisindo_alphabet/C/20240509_183146.jpg` |
| `IMG_BLD_05` | **Kelas A** | Target Utama | `data/raw/image/bisindo_alphabet/A/20240509_182656.jpg` |
| `IMG_BLD_06` | **Kelas D** | Distractor Pembanding | `data/raw/image/bisindo_alphabet/D/20240509_183310.jpg` |
| `IMG_BLD_07` | **Kelas A** | Target Utama | `data/raw/image/bisindo_alphabet/A/A_Background Baju (Garis)_Samsung_A53 5G.jpg` |

---

## 5. CATATAN KEPATUHAN OPERASIONAL

1. Lembar penugasan ini bersifat persiapan teknis operasional (*pre-session artifact*).
2. Tidak ada tanggal sesi nyata yang dikarang.
3. Tidak ada klaim bahwa urutan di atas telah digunakan dalam sesi tatap muka.
4. Status proyek tetap **`PENDING VALIDATOR`** dan **`PILOT_HOLD`**.

