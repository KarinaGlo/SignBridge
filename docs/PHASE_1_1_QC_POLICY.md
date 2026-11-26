# PHASE 1.1 — ALPHABET DATASET QUALITY CONTROL (QC) POLICY
## SignBridge ID–PH (BISINDO ↔ FSL) — BISINDO Alphabet Image Dataset

Kebijakan ini mengatur kelayakan label, status QC, dan tata kelola sampel hasil validasi 36 citra alfabet BISINDO (Mendeley) sebelum dapat digunakan pada evaluasi atau pelatihan model.

---

## 1. Aturan Inti QC (Wajib Dipatuhi)

1. **`FULL_AGREEMENT` Bukan Otomatis Final Ground Truth**
   - Kesepakatan dua validator (`IDENTIFIED` + huruf identik, saat ini 11/36 sampel) hanya berstatus **kesepakatan validator sementara (*provisional validator agreement*)** dengan `final_qc_status = QC_PENDING` dan `final_ground_truth_eligible = FALSE`.
   - Status ini **tidak** setara dengan *final ground truth* sampai prosedur persetujuan ahli (*expert sign-off*) diselesaikan.

2. **Syarat Status `IDENTIFIED` sebagai Label Final**
   - Keputusan `IDENTIFIED` hanya dapat dipromosikan menjadi label final (`QC_ACCEPTED`, `final_ground_truth_eligible = TRUE`) setelah melalui prosedur persetujuan ahli BISINDO yang terdokumentasi (`adjudicator_id` dan `adjudication_date` terisi pada [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv)).

3. **Larangan Pemaksaan Label pada `AMBIGUOUS`**
   - Sampel dengan keputusan akhir `AMBIGUOUS` **tidak boleh dipaksakan** menjadi satu huruf A–Z melalui *majority voting*, tebakan, atau penyalinan label folder Mendeley.
   - Sampel `AMBIGUOUS` wajib ditahan dari kumpulan *ground truth* (`final_ground_truth_eligible = FALSE`).

4. **Isolasi Sampel `UNDETERMINABLE` dari Data Training**
   - Sampel dengan keputusan akhir `UNDETERMINABLE` **harus dipisahkan secara tegas** dari seluruh sampel yang layak untuk training maupun evaluasi akurasi (`final_ground_truth_eligible = FALSE`, `final_qc_status = QC_REJECTED` setelah dikonfirmasi ahli).

5. **Kewajiban Audit Trail untuk Setiap Perubahan Label**
   - Setiap penetapan atau perubahan label terhadap label asli Mendeley maupun respons Validator A/B wajib meninggalkan jejak audit lengkap: `validator_A_*`, `validator_B_*`, `expert_final_*`, `adjudication_reason`, `adjudicator_id`, dan `adjudication_date`.
   - Berkas respons validator asli dan citra sumber Mendeley bersifat **immutable (read-only)**.

6. **Larangan Penghapusan Sampel yang Tidak Lolos QC**
   - Sampel yang berstatus `AMBIGUOUS`, `UNDETERMINABLE`, atau `QC_REJECTED` **dilarang dihapus** dari arsip/manifest audit. Sampel tersebut dipertahankan dengan penandaan status QC yang jelas sebagai bukti kualitas dataset dan analisis kegagalan (*error/outlier analysis*).

---

## 2. Matriks Pemetaan Status QC

| Kondisi Sampel | `final_qc_status` | `provisional_use_eligible` | `final_ground_truth_eligible` | Kelayakan Training / Evaluasi |
| :--- | :--- | :---: | :---: | :--- |
| `FULL_AGREEMENT` (sebelum *expert sign-off*) | `QC_PENDING` | `TRUE` | `FALSE` | Hanya penggunaan diagnostik sementara; belum final. |
| Disetujui Ahli sebagai `IDENTIFIED` | `QC_ACCEPTED` | `TRUE` | `TRUE` | Layak sebagai *ground truth* (tetap patuhi *firewall* `TEST_SET_DIAGNOSTIC_ONLY`). |
| Menunggu Adjudikasi Ahli (selisih huruf/keputusan) | `QC_REQUIRES_ADJUDICATION` | `FALSE` | `FALSE` | Ditahan; menunggu keputusan ahli. |
| Menunggu Tinjauan Gambar & Ahli (`BOTH_AMBIGUOUS` / `AMB vs UND`) | `QC_REQUIRES_IMAGE_REVIEW` | `FALSE` | `FALSE` | Ditahan; menunggu inspeksi ahli. |
| Dikonfirmasi Ahli sebagai `AMBIGUOUS` / `UNDETERMINABLE` | `QC_REJECTED` | `FALSE` | `FALSE` | Dipisahkan dari training; tetap disimpan di arsip audit. |

---

## 3. Batasan Cakupan & Firewall Data
- Kebijakan ini berlaku untuk **36 sampel audit alfabet BISINDO** (`VAL-REV-001`–`VAL-REV-036`) dan **tidak** mengklaim validasi terhadap seluruh 8,620 citra Mendeley.
- Sebanyak **19 sampel** bertanda `TEST_SET_DIAGNOSTIC_ONLY` tetap terisolasi dari training/tuning P2 untuk mencegah *test leakage*.
