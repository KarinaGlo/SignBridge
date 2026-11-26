# REGISTER PEMERIKSAAN REPRESENTASI HURUF J DAN Z
## SignBridge ASEAN — Modul Image I1 (BISINDO Alphabet)
### Status: VALIDATOR_REVIEW_REQUIRED

> [!IMPORTANT]
> **BATASAN LINGUISTIK**: Tim peneliti teknik mesin / rekayasa AI **DILARANG** menentukan sendiri konvensi gestur BISINDO yang benar.
> Pertanyaan representasi huruf dinamis (J dan Z) dalam bentuk citra diam tunggal wajib diserahkan secara utuh kepada keputusan validator Tuli BISINDO berkualifikasi.

---

### 1. Masalah Representasi Modalitas Citra Diam untuk Huruf Dinamis
Dalam kamus standar BISINDO:
- **Huruf J** adalah gestur dinamis: jari kelingking ditegakkan lalu digerakkan melengkung ke bawah membentuk huruf 'J' di udara.
- **Huruf Z** adalah gestur dinamis: jari telunjuk ditegakkan lalu digerakkan secara zigzag di udara membentuk huruf 'Z'.
Pada dataset Mendeley Image I1, seluruh data berupa **foto diam tunggal (*static single-frame image*)** tanpa informasi lintasan waktu (*motion trajectory*). Hal ini menyebabkan huruf J terekam hanya sebagai pose kelingking diam (identik dengan huruf I), dan huruf Z terekam sebagai pose telunjuk diam.

---

### 2. Tabel Register Kasus Representasi J dan Z

| Case ID | Sample Ref / ID | Representasi Saat Ini | Bukti Empiris Repositori | Pertanyaan Kritis untuk Validator Tuli | Status Validasi |
| :---: | :---: | :--- | :--- | :--- | :---: |
| `REG-JZ-01` | `VAL-REV-009` (`J_0080.jpg`) | Pose statis kelingking tegak menghadap depan | Model P1 memprediksi sebagai `I` (Conf: $78,3\%$) | Apakah pose diam kelingking tegak sah diakui sebagai huruf J dalam fingerspelling foto statis, ataukah harus ada penanda arah gerak khusus? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-02` | Kohort Kelas J ($N=169$) | $100\%$ citra diam tanpa sekuens video | $10$ kesalahan test set berupa konfusi timbal balik J $\leftrightarrow$ I | Pose kunci manakah (*canonical keyframe*) yang paling tepat mewakili huruf J: saat awal (kelingking tegak), saat lengkungan bawah, atau saat akhir gerakan? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-03` | `VAL-REV-016` (`Z_0126.jpg`) | Telunjuk miring dengan blur gerakan tangan | Laplacian variance rendah ($5,55$), terindikasi tangan bergerak saat difoto | Apakah blur gerakan (*motion blur*) pada telunjuk ini masih dapat dikenali sebagai gestur Z yang valid? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-04` | `VAL-REV-019` (`Z_0018.jpg`) | Telunjuk menghadap samping dengan pencahayaan gelap | Laplacian variance $6,72$, luminansi rendah | Apakah orientasi telunjuk ke samping sah mewakili huruf Z pada kondisi pencahayaan rendah? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-05` | `VAL-REV-026` (`Z_0123.jpg`) | Telunjuk menyentuh batas tepi frame | Ujung telunjuk terpotong oleh cropping batas tepi | Apakah pemotongan ujung telunjuk ini menggugurkan keabsahan gestur huruf Z? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-06` | `ANOM-LBL-008` (`S_Baju...jpg`) | Berkas di folder Z dengan awalan nama `S_` | Folder `Z/`, nama file `S_Baju_Iphone_14 Pro.jpg` | Apakah pose tangan pada berkas ini sebenarnya adalah kepalan huruf S atau gestur huruf Z? | `PENDING_VALIDATOR_REVIEW` |
| `REG-JZ-07` | Kebijakan Modalitas P2 | Klasifikasi citra diam (MobileNetV3) | Batas teoritis Bayes error rate pada citra diam J vs I | Apakah pengenalan huruf J dan Z sebaiknya dipindahkan ke modalitas Video (V1) yang menangkap lintasan gerak sekuensial? | `PENDING_VALIDATOR_REVIEW` |

---

### 3. Protokol Penyerahan ke Validator
Pertanyaan-pertanyaan di atas akan diajukan secara terstruktur dalam sesi wawancara kualitatif pasca-evaluasi buta bersama validator Tuli BISINDO.