# REGISTER ANOMALI LABEL: PREFIX-FOLDER MISMATCH REGISTER
## SignBridge ASEAN — Modul Image I1 (BISINDO Alphabet)
### Status Tata Kelola: VALIDATOR_REVIEW_REQUIRED

> [!IMPORTANT]
> **ATURAN TATA KELOLA DATA**: Awalan nama berkas (*filename prefix*) **TIDAK BOLEH** dianggap sebagai ground-truth secara otomatis. Dilarang mengubah label kelas hanya berdasarkan nama berkas tanpa verifikasi visual langsung oleh validator Tuli BISINDO.

---

### 1. Ringkasan Temuan Anomali
Selama audit forensik Phase 2B, pemindaian otomatis terhadap 4.462 citra mentah menemukan **8 berkas di mana awalan nama berkas (*prefix*) tidak sesuai dengan folder kelas tempat berkas disimpan** pada dataset mentah Mendeley.
Anomali ini mengindikasikan adanya kekeliruan pengelompokan (*misplaced files*) atau kekeliruan penamaan (*mislabeling*) saat kontributor Mendeley mengumpulkan dataset.

---

### 2. Tabel Register Anomali Label (8 Kasus Teridentifikasi)

| Anomaly ID | Nama Berkas Sumber Mentah | Label Folder | Prefix Berkas | Split Saat Ini | Prediksi P1 (Confidence) | Sumber Bukti | Status Validasi |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| `ANOM-LBL-001` | `D_Bebas_Redmi_Note 12 Pro.jpg` | `C` | `D` | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/C/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-002` | `E_Baju_Apple_Iphone 11.jpg` | `L` | `E` | `test` | `Pred: V (34.2%) [Salah]` | `runs/image_i1_mobilenetv3_p1/predictions.csv:301` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-003` | `E_Bebas_Apple_Iphone 11.jpg` | `L` | `E` | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/L/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-004` | `0_BEBAS_Apple_Iphone 12.JPG` | `O` | `0` (Nol) | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/O/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-005` | `0_Polos gelap_Apple_Iphone 12.JPG` | `O` | `0` (Nol) | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/O/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-006` | `0_Polos terang_Apple_Iphone 12.JPG` | `O` | `0` (Nol) | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/O/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-007` | `Y_Polos Gelap_Iphone_14 Pro.jpg` | `V` | `Y` | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/V/` | `VALIDATOR_REVIEW_REQUIRED` |
| `ANOM-LBL-008` | `S_Baju_Iphone_14 Pro.jpg` | `Z` | `S` | `train` | *N/A (Train Split)* | `data/raw/image/bisindo_alphabet/Z/` | `VALIDATOR_REVIEW_REQUIRED` |

---

### 3. Analisis Kritis Dampak Evaluasi & Training
1. **Kasus Kritis `ANOM-LBL-002` (`E_Baju_Apple_Iphone 11.jpg` di Kelas `L`)**:
   - Berkas ini dialokasikan ke dalam **Test Set** P1 dengan ground truth label `L`.
   - Model P1 memprediksi kelas `V` dengan confidence $34,22\%$, menghasilkan evaluasi *incorrect*.
   - Jika gestur aktual yang diperagakan penandatangan adalah huruf E (sesuai nama berkas), maka metriks evaluasi recall kelas L dan precision kelas E terdistorsi secara artifisial.
2. **Kasus Angka Nol pada Kelas O (`ANOM-LBL-004` s/d `ANOM-LBL-006`)**:
   - Tiga berkas di folder O dinamai dengan awalan angka `0_` alih-alih huruf `O_`.
   - Dalam fingerspelling BISINDO, angka 0 dan huruf O memiliki bentuk lingkaran yang sangat mirip, namun orientasi pergelangan dan sudut hadap telapak tangan memiliki perbedaan konvensional.
3. **Kasus `ANOM-LBL-008` (`S_Baju_Iphone_14 Pro.jpg` di Kelas `Z`)**:
   - Mengindikasikan potensi tertukarnya foto kepalan huruf S ke dalam kelas gestur dinamis Z.

---

### 4. Tindakan Tata Kelola yang Diwajibkan
- Seluruh 8 kasus berstatus **`VALIDATOR_REVIEW_REQUIRED`**.
- Berkas tidak boleh dipindahkan, dihapus, atau diubah namanya dalam repositori saat ini.
- Untuk persiapan P2, tim peneliti akan menyertakan sampel-sampel ini dalam sesi adjudikasi khusus bersama validator Tuli.