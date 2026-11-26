# LAPORAN REKONSILIASI AKHIR SILSILAH DATA & INTEGRITAS ARTEFAK
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)

> **Dokumen**: `docs/validation_p1/FINAL_LINEAGE_AUDIT_RECONCILIATION.md`  
> **Tipe Evaluasi**: Final Lineage Reconciliation & Forensic Integrity Audit  
> **Dasar Analisis**: Penyelesaian Celah Metodologis dari `FINAL_TRAINING_DATA_LINEAGE_VERIFICATION.md` & `LINEAGE_EVIDENCE_HARDENING.md`  
> **Tanggal Audit**: 17 November 2026  
> **Auditor**: Senior Machine Learning Auditor, Computer Vision Engineer, Data Quality Analyst, & ML Reproducibility Specialist  
> **Klasifikasi Akhir**: **`HISTORICAL_LINEAGE_STRONGLY_SUPPORTED`**

---

## 1. EXECUTIVE SUMMARY

Audit rekonsiliasi akhir ini diselenggarakan untuk menyelesaikan empat celah metodologis penting yang diidentifikasi pada evaluasi silsilah data pelatihan model baseline Image Modality I1:
1. **Rekonsiliasi Status Git Manifest**: Menjelaskan secara definitif mengapa `manifest.csv` dan `preprocessing_audit_manifest.csv` tidak muncul pada status Git biasa.
2. **Verifikasi Angka 403/669 pada Checkpoint P1**: Memverifikasi secara biner apakah angka 403 dan 669 tersimpan secara literal (*explicitly stored*) atau merupakan hasil rekonstruksi analitis (*reconstructed*).
3. **Verifikasi Asal-Usul Hash Baseline**: Melacak silsilah kemunculan pertama kali nilai hash SHA-256 untuk checkpoint P1, P0 scratch, P0 legacy, dan ONNX produksi.
4. **Audit Duplikasi Intra-Split**: Memeriksa keberadaan duplikasi path, hash biner, dan duplikasi lintas-kelas di dalam masing-masing split (Train, Validation, Test).

### Ringkasan Temuan Faktual:
- **Status Git Manifest**: Kedua berkas manifest terbukti berstatus **`IGNORED`** secara sah berdasarkan aturan `.gitignore:49:data/processed/`.
- **Status Angka 403/669**: Checkpoint `best.pt` P1 **hanya menyimpan `val_acc`** sebagai float (`0.6023916292974589`). Angka 403/669 diklasifikasikan sebagai **`RECONSTRUCTED`** (bukan field yang tersimpan secara literal di checkpoint).
- **Asal Hash Baseline**: Hash P0 legacy (`6767DCAA...`) dan ONNX (`1C281E15...`) berasal dari inventaris 13 November 2026 (`docs/dataset_file_inventory.csv`). Hash P1 (`83C6A093...`) berasal dari audit 16 November 2026 (`docs/validation_p1/artifact_integrity_report.md`). Hash P0 scratch (`39B26F97...`) pertama kali diidentifikasi pada audit 17 November 2026.
- **Audit Duplikasi Intra-Split**: Ditemukan **0 duplicate path**, **0 duplicate SHA-256**, dan **0 cross-class duplicate** di dalam Train ($N=3.123$), Validation ($N=669$), maupun Test ($N=670$). Seluruh 4.462 citra processed memiliki hash biner unik 100%.
- **Klasifikasi Akhir**: Status silsilah data historis ditetapkan secara objektif dan konservatif sebagai **`HISTORICAL_LINEAGE_STRONGLY_SUPPORTED`**.

---

## 2. REKONSILIASI STATUS GIT MANIFEST (TASK 1)

Pemeriksaan Git secara mendalam dijalankan menggunakan perintah inspeksi read-only:

```powershell
git status --short --untracked-files=all
git check-ignore -v data/processed/bisindo_alphabet/manifest.csv
git check-ignore -v data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv
git ls-files --error-unmatch data/processed/bisindo_alphabet/manifest.csv
git ls-files --error-unmatch data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv
```

### Tabel Hasil Rekonsiliasi Git:

| Berkas Manifest | Status Git | Aturan Ignore yang Berlaku | Bukti Perintah Terminal | Kesimpulan Rekonsiliasi |
|---|:---:|---|---|---|
| `data/processed/bisindo_alphabet/manifest.csv` | **`IGNORED`** | `.gitignore` baris 49 (`data/processed/`) | `git check-ignore -v` $\to$ `.gitignore:49:data/processed/` | Berkas eksis di disk, sengaja dikecualikan dari Git oleh arsitektur proyek |
| `data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv` | **`IGNORED`** | `.gitignore` baris 49 (`data/processed/`) | `git check-ignore -v` $\to$ `.gitignore:49:data/processed/` | Berkas eksis di disk, sengaja dikecualikan dari Git oleh arsitektur proyek |

*Catatan Perilaku Git*: Berkas yang cocok dengan pola `.gitignore` tidak akan ditampilkan sebagai `??` (untracked) pada `git status` standar. Perintah `git ls-files --error-unmatch` mengembalikan exit code 1 (`did not match any file(s) known to git`), yang secara definitif membuktikan bahwa kedua file tersebut berstatus **`IGNORED`**, bukan hilang (*missing*) dan bukan tracked.

---

## 3. VERIFIKASI ANGKA 403/669 PADA CHECKPOINT P1 (TASK 2)

Pemeriksaan aman terhadap struktur dictionary checkpoint PyTorch `runs/image_i1_mobilenetv3_p1/best.pt`:

```
Top-Level Checkpoint Keys:
  ['epoch', 'stage', 'model_state_dict', 'val_acc', 'val_f1', 'config']
```

### Evaluasi Keberadaan Field:

| Informasi yang Dievaluasi | Ada di Checkpoint Biner (`best.pt`) | Ada di Summary JSON (`training_summary.json`) | Ada di Training Log (`training_history.csv`) | Status Klasifikasi |
|---|:---:|:---:|:---:|:---:|
| **`val_acc = 0.6023916292974589`** | **ADA (Float)** | **ADA (Dibulatkan: 60.24%)** | **ADA (Dibulatkan: 0.6024)** | **EXPLICITLY STORED** |
| **`val_samples = 669`** | **TIDAK ADA** | **ADA (`dataset_splits.val_samples`)** | **TIDAK ADA** | **RECONSTRUCTED (Via Summary)** |
| **`num_correct = 403`** | **TIDAK ADA** | **TIDAK ADA** | **TIDAK ADA** | **RECONSTRUCTED (Matematis)** |
| **Field `val_correct` / `val_total`** | **TIDAK ADA** | **TIDAK ADA** | **TIDAK ADA** | **NOT STORED** |

### Analisis Matematis Presisi:
- Nilai yang disimpan secara literal di dalam checkpoint: `val_acc = 0.6023916292974589`.
- Perhitungan rekonsiliasi:
  $$0,6023916292974589 \times 669 = 403,0000000000000$$
  Selisih terhadap integer 403 adalah eksak $0,0 \times 10^0$.
- **Kesimpulan Metodologis**: Menyebut "angka 403/669 tersimpan di checkpoint" adalah **keliru secara teknis**. Yang benar adalah: Checkpoint menyimpan akurasi `0.6023916...`, dan angka **403 prediksi benar dari 669 sampel validasi adalah hasil rekonstruksi analitis matematis (*RECONSTRUCTED*)** yang diperoleh dengan memadukan `val_acc` checkpoint dengan ukuran split validasi dari `training_summary.json` dan `manifest.csv`.

---

## 4. VERIFIKASI ASAL-USUL HASH BASELINE CHECKPOINT DAN ONNX (TASK 3)

Penelusuran arkeologi silsilah hash SHA-256 di seluruh berkas dokumentasi historis repositori:

| Artefak Model | Path File | Hash SHA-256 Aktual | Sumber Asal-Usul Baseline Pertama Kali | Status Verifikasi Silsilah |
|---|---|---|---|:---:|
| **P1 Best Checkpoint** | `runs/image_i1_mobilenetv3_p1/best.pt` | `83C6A0933C8E1A2097CE6FA1198D8578826ED37731C18137C057FEA129AFFEE9` | `docs/validation_p1/artifact_integrity_report.md` (16 Nov 2026 20:12 WIB) | **`VERIFIED_AGAINST_INDEPENDENT_BASELINE`** |
| **P0 Scratch Checkpoint** | `runs/image_i1_mobilenetv3_p0/best.pt` | `39B26F97A9916A9374567AA7FE25FE997CBB5BAA58C6B34D7DA5533A68E3990A` | Diukur independen pada audit silsilah data (`FINAL_TRAINING_DATA_LINEAGE_VERIFICATION.md`, 17 Nov 2026) | **`MATCHES_PREVIOUS_AUDIT_REFERENCE`** |
| **P0 Legacy Baseline** | `runs/image_i1_mobilenetv3/best.pt` | `6767DCAA4735AF671F5863542D92C9223CFD873E4C8717D487D81BC676743B03` | `docs/dataset_file_inventory.csv` baris 23 (13 Nov 2026 16:20 WIB, file modifikasi 6 Nov 2026) | **`VERIFIED_AGAINST_INDEPENDENT_BASELINE`** |
| **Production ONNX** | `web/model/fingerspell.onnx` | `1C281E158B279DE4B8A582CFC9F865C758E3050F55C4F032B54613FCD0D4C105` | `docs/dataset_file_inventory.csv` baris 22 (13 Nov 2026 16:20 WIB, file modifikasi 6 Nov 2026) | **`VERIFIED_AGAINST_INDEPENDENT_BASELINE`** |

### Perbedaan Krusial P0 Scratch vs P0 Legacy:
- **P0 Legacy (`runs/image_i1_mobilenetv3/best.pt`, `6767DCAA...`)**: Model prototipe awal yang diekspor pada 6 November 2026 dari folder `data/fingerspelling_crops` (sebelum dataset Mendeley diunduh). Checkpoint ini menjadi basis pembuatan `web/model/fingerspell.onnx`.
- **P0 Scratch (`runs/image_i1_mobilenetv3_p0/best.pt`, `39B26F97...`)**: Model baseline scratch sesungguhnya yang dilatih selama 25 epoch pada dataset Mendeley (`manifest.csv`, 4.462 sampel) pada 13 November 2026 pukul 17:11–17:57 WIB.

---

## 5. AUDIT DUPLIKASI INTRA-SPLIT (TASK 4)

Dilakukan pengujian independen terhadap 4.462 baris pada `manifest.csv` untuk mendeteksi duplikasi di dalam masing-masing split:

| Split Evaluasi | Jumlah Baris | Duplicate Path | Duplicate Processed SHA-256 | Duplicate Original Raw SHA-256 | Cross-Class Duplicate Intra-Split | Status Integritas Split |
|:---:|---:|:---:|:---:|:---:|:---:|:---:|
| **Train** | **3.123** | **0** | **0** | **0** | **0** | **CLEAN (0 Duplicates) ✅** |
| **Validation** | **669** | **0** | **0** | **0** | **0** | **CLEAN (0 Duplicates) ✅** |
| **Test** | **670** | **0** | **0** | **0** | **0** | **CLEAN (0 Duplicates) ✅** |
| **Total Dataset** | **4.462** | **0** | **0** | **0** | **0** | **PARIPURNA (4.462 Hash Unik) ✅** |

### Temuan:
1. **Zero Same-Path Duplicate**: Tidak ada baris ganda yang menunjuk path file yang sama.
2. **Zero Exact Binary Duplicate**: Seluruh 3.123 sampel train memiliki hash biner yang berbeda; seluruh 669 sampel val unik; seluruh 670 sampel test unik.
3. **Zero Cross-Class Duplicate**: Tidak ada dua sampel dengan hash sama yang diberi label kelas berbeda di dalam split yang sama maupun di seluruh dataset processed.

---

## 6. AUDIT ULANG CROSS-SPLIT & EMPAT DUPLIKAT HISTORIS (TASK 5)

### 6.1. Cross-Split Leakage Check
- Irisan `Train` $\cap$ `Validation`: **0 path, 0 hash SHA-256**.
- Irisan `Train` $\cap$ `Test`: **0 path, 0 hash SHA-256**.
- Irisan `Validation` $\cap$ `Test`: **0 path, 0 hash SHA-256**.

### 6.2. Status Empat Duplikat Biner Historis:
- `D_Polos Gelap_iPhone_XR.jpeg` & `P_Polos Gelap_iPhone_XR.jpeg` (SHA-256: `a992...`)
- `B_polos gelap_Iphone_13promax.jpg` & `E_polos gelap_Iphone_13promax.jpg` (SHA-256: `99c4...`)

Hasil pemindaian:
1. Keempat file **masih tersimpan utuh** di folder data mentah (`data/raw/image/bisindo_alphabet/`).
2. Keempat file **tercatat resmi sebagai `EXCLUDED`** pada `data/processed/bisindo_alphabet/preprocessing_audit_manifest.csv`.
3. Keempat file **TIDAK PERNAH MUNCUL** pada `manifest.csv` processed.
4. Keempat file **TIDAK PERNAH MASUK** ke dalam Train, Validation, maupun Test Set model P0 atau P1.
5. Tidak ada file `.jpg` atau `.npy` hasil olahan yang diturunkan dari keempat file ini di storage processed.

---

## 7. VERIFIKASI KONSISTENSI DATASET & ARTEFAK TRAINING (TASK 6)

Rekonsiliasi paritas komparatif seluruh artefak:

| Komponen Parameter | Sumber Manifest Processed | Sumber Summary Training P0 | Sumber Summary Training P1 | Kesesuaian Paritas |
|---|:---:|:---:|:---:|:---:|
| **Total Sampel** | 4.462 citra | 4.462 sampel | 4.462 sampel | **EXACT MATCH (100%) ✅** |
| **Sampel Train** | 3.123 citra | 3.123 sampel | 3.123 sampel | **EXACT MATCH (100%) ✅** |
| **Sampel Validation** | 669 citra | 669 sampel | 669 sampel | **EXACT MATCH (100%) ✅** |
| **Sampel Test** | 670 citra | 670 sampel | 670 sampel | **EXACT MATCH (100%) ✅** |
| **Jumlah Kelas** | 26 kelas (A–Z) | 26 kelas | 26 kelas | **EXACT MATCH (100%) ✅** |
| **File JPG Fisik di Disk**| 4.462 file | N/A | N/A | **EXACT MATCH (100%) ✅** |
| **File NPY Fisik di Disk**| 4.462 file | N/A | N/A | **EXACT MATCH (100%) ✅** |

---

## 8. KETERBATASAN AUDIT YANG WAJIB DICATAT (TASK 7)

Audit ini **TIDAK MENGKLAIM** bahwa dataset bebas dari seluruh bentuk bias dan cacat:
1. **Subject-Level Leakage**: Ketiadaan metadata `signer_id` pada dataset publik Mendeley mengakibatkan isolasi penutur antar-split **tidak dapat diverifikasi (`NOT_VERIFIABLE_WITH_AVAILABLE_METADATA`)**.
2. **Near-Duplicate & Burst Shots**: Audit biner hanya membuktikan ketiadaan klon bit-by-bit; foto beruntun dengan variasi pose mikro yang diambil dalam hitungan milidetik tetap berpotensi ada di dalam dataset mentah Mendeley.
3. **Validitas Linguistik**: Klasifikasi gestur tetap berstatus **`LINGUISTIC_LABEL_VALIDITY_PENDING_HUMAN_VALIDATION`** hingga sesi verifikasi bersama penutur Tuli dilaksanakan.
4. **Ketiadaan Hash Konten Manifest Historis**: Skrip pelatihan P0/P1 tidak mencatat hash konten `manifest.csv` saat runtime pada 13 November 2026.

---

## 9. MATRIKS BUKTI: TERKONFIRMASI VS INFERENSIAL VS TIDAK TERSEDIA

| Kategori Bukti | Status Pembuktian | Rincian Bukti Faktual |
|---|:---:|---|
| **Bukti Terkonfirmasi (Empiris)** | **TERBUKTI 100%** | - Status `.gitignore:49` untuk kedua manifest.<br>- Ketiadaan 4 duplikat raw di dalam manifest processed.<br>- 0 duplikasi intra-split (Train, Val, Test) pada 4.462 baris.<br>- 0 duplikasi cross-split.<br>- Paritas absolut jumlah sampel ($N=4.462$, Train: 3.123, Val: 669, Test: 670).<br>- Nilai `val_acc` float di checkpoint P1.<br>- Hash SHA-256 keempat checkpoint model cocok 100%. |
| **Bukti Inferensial (Sangat Didukung)** | **STRONGLY SUPPORTED** | - Rekonstruksi pecahan 403/669 dari `val_acc` dan `N_val`.<br>- Kesamaan konten manifest saat ini dengan manifest saat training (didukung timestamp NTFS 13/11/2026 17:01 WIB yang mendahului training). |
| **Bukti Tidak Tersedia** | **ABSENT** | - Hash SHA-256 konten `manifest.csv` yang dicatat saat training.<br>- Git commit hash historis yang melacak `manifest.csv`.<br>- Metadata identitas penutur (*Signer ID*). |

---

## 10. RANCANGAN PROVENANCE HARDENING UNTUK EKSPERIMEN P2 (TASK 13)

Rancangan arsitektur pencatatan silsilah data yang direkomendasikan untuk eksperimen P2 (**tanpa diimplementasikan saat ini**):

```python
# Blueprint Hardening Silsilah Data Pelatihan P2 (Non-Destruktif)
class ExperimentProvenanceTracker:
    @staticmethod
    def capture_provenance(manifest_path, config_path, audit_manifest_path):
        import hashlib, subprocess, datetime, torch, sys
        
        def file_sha256(p):
            with open(p, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        
        try:
            git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            git_dirty = bool(subprocess.check_output(["git", "status", "--porcelain"]))
        except Exception:
            git_commit, git_dirty = "UNKNOWN", True
            
        provenance = {
            "timestamp_utc": datetime.datetime.utcnow().isoformat(),
            "manifest_path": str(manifest_path),
            "manifest_sha256": file_sha256(manifest_path),
            "audit_manifest_sha256": file_sha256(audit_manifest_path),
            "config_sha256": file_sha256(config_path),
            "git_commit_sha": git_commit,
            "git_is_dirty": git_dirty,
            "python_version": sys.version,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available()
        }
        return provenance
```
*Penyimpanan*: Dictionary provenance di atas disimpan ke dalam checkpoint `best.pt` di bawah key `provenance` dan diekspor ke `runs/.../provenance.json` tanpa membebani runtime inference model.

---

## 11. KLASIFIKASI AKHIR

Berdasarkan rekonsiliasi menyeluruh terhadap fakta bahwa seluruh konfigurasi, timestamp, paritas sampel matematis ($N=4.462$), kebersihan intra-split (0 duplikat), dan isolasi 4 file raw terbukti konsisten, namun **hash konten manifest historis tidak pernah direkam saat training**, maka status silsilah data historis secara resmi ditetapkan sebagai:

$$\mathbf{HISTORICAL\_LINEAGE\_STRONGLY\_SUPPORTED}$$

