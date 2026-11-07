# Laporan Persiapan GitHub & Branch `feature/dataset-acquisition` (`docs/GITHUB_PUSH_REPORT.md`)
**Tanggal**: 7 November 2026  
**Branch Aktif**: `feature/dataset-acquisition`  
**Konfigurasi Git Lokal**: `user.name=KarinaGlo`, `user.email=gloriadanapricilia@gmail.com`, `init.defaultbranch=master`

---

## 1. Hasil Pemeriksaan Awal Repository

1. **Status Awal**:
   - Direktori kerja `d:\SEMESTER 5\ML\Projek_1` sebelumnya belum memiliki inisialisasi `.git` lokal dan belum memiliki berkas `.gitignore`.
   - Konfigurasi global Git menggunakan branch default `master` (`init.defaultbranch=master`).
2. **Tindakan Inisialisasi Aman**:
   - Repository Git diinisialisasi (`git init`) dan langsung dialihkan ke branch pengembangan `feature/dataset-acquisition` (`git checkout -b feature/dataset-acquisition`) **sebelum** membuat commit apa pun, sehingga branch `master`/`main` tetap bersih dan tidak menerima commit langsung sesuai aturan wajib.

---

## 2. Konfigurasi `.gitignore` & Keamanan Data

Berkas [`.gitignore`](file:///d:/SEMESTER%205/ML/Projek_1/.gitignore) telah dikonfigurasi untuk mengecualikan:
- **Kredensial & Rahasia**: `.env`, `.env.*` (kecuali `.env.example`), `*.pem`, `*.key`, `credentials.json`.
- **Database Operasional Lokal**: `*.db`, `*.sqlite`, `data/signbridge_operational.db`, `pgdata/`.
- **Dataset Mentah & Arsip Besar**: `data/raw/`, `data/keypoints/`, `*.mp4`, `*.webm`, `*.wav`, `*.npz`, `*.zip`.
- **Checkpoint Pelatihan PyTorch**: `*.pt`, `*.pth`, `runs/**/*.pt` (termasuk `runs/image_i1_mobilenetv3/best.pt`), dengan tetap melacak `runs/**/result.json` dan model runtime ringan `web/model/*.onnx` (`\le 1,66\text{ MB}`).
- **Cache Runtime & Pengujian**: `__pycache__/`, `.pytest_cache/`, `.hypothesis/`, `node_modules/`.

---

## 3. Struktur Commit pada Branch `feature/dataset-acquisition`

Seluruh perubahan dikelompokkan ke dalam 4 commit terstruktur pada branch `feature/dataset-acquisition`:

1. `chore: configure gitignore`
   - Menambahkan [`.gitignore`](file:///d:/SEMESTER%205/ML/Projek_1/.gitignore) dan [`.env.example`](file:///d:/SEMESTER%205/ML/Projek_1/.env.example).
2. `chore: prepare SignBridge repository`
   - Menambahkan seluruh kode inti aplikasi (`signbridge/`, `server/`, `web/`, `configs/`, `migrations/`, `scripts/`, `deploy/`, `tests/`, `docker-compose.yml`, `SignBridge_Notebook.ipynb`, `report/`).
3. `data: add dataset acquisition documentation`
   - Menambahkan manifest/metadata dataset ringan (`data/phonology.csv`, `data/PHONOLOGY_GUIDE.md`, `data/bridge/concepts.csv`, `data/text/`, `data/audio/`), dokumentasi [`docs/DATASET.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/DATASET.md), dan [`docs/DATASET_ACQUISITION.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/DATASET_ACQUISITION.md).
4. `docs: add GitHub push report`
   - Menambahkan laporan audit dan validasi teknis (`docs/API.md`, `docs/DATABASE.md`, `docs/DEPLOYMENT.md`, `docs/EXPERIMENTS.md`, `docs/TESTING.md`, `docs/IMPLEMENTATION_REPORT.md`, `docs/FINAL_AUDIT.md`, `docs/FASE_9_DEPLOYMENT_AUDIT.md`, `docs/FASE_10_IMPLEMENTATION_REPORT.md`, `docs/FASE_11_FUNCTIONAL_VALIDATION.md`, serta `docs/GITHUB_PUSH_REPORT.md`).

---

## 4. Spesifikasi Pull Request (Menunggu Persetujuan)

- **Source Branch**: `feature/dataset-acquisition`
- **Target Branch**: `master` (atau `main` sesuai branch default pada remote GitHub)
- **Judul PR**: `feat: SignBridge ID-PH Multimodal AI, PostgreSQL 16 Integration, & Dataset Acquisition Pipeline`
- **Ringkasan Perubahan untuk PR**:
  - Implementasi penuh pipeline 4 modalitas (Video 86-node ST-GCN/Transformer, Citra Fingerspelling A–Z, Audio ASR/TTS, Teks Gloss-to-Sentence & 3-Layer Bridge ID–PH).
  - Integrasi database operasional PostgreSQL 16 (5 tabel, migrasi SQL otomatis, *idempotent seeding*, dan fallback SQLite).
  - Perbaikan pemisahan *lazy import* PyTorch pada modul runtime Docker (`signbridge-asean` & `signbridge-postgres` berstatus *Healthy*).
  - Validasi fungsional end-to-end (345 pengujian Python & 7 pengujian paritas JavaScript lulus) serta dokumentasi akuisisi dataset.
- **Status Merge**: **DITAHAN (Tidak di-merge otomatis)** — menunggu peninjauan dan persetujuan eksplisit pengguna.
