# Panduan Deployment Lokal, Docker Compose, & Azure (`docs/DEPLOYMENT.md`)

## 1. Menjalankan Secara Lokal (Tanpa Docker)
1. Pastikan dependensi server telah terpasang:
   ```powershell
   pip install -r server/requirements.txt
   ```
2. Jalankan migrasi & *seeding* database operasional (otomatis memakai `DATABASE_URL` PostgreSQL jika aktif, atau *fallback* ke `data/signbridge_operational.db` jika PostgreSQL belum dinyalakan):
   ```powershell
   python scripts/migrate_db.py
   ```
3. Jalankan server FastAPI + Web PWA:
   ```powershell
   python -m uvicorn server.app:app --host 127.0.0.1 --port 7860
   ```
4. Akses di peramban:
   - **Aplikasi Web PWA**: `http://localhost:7860`
   - **Swagger UI API Docs**: `http://localhost:7860/docs`
   - **Status Kesehatan & DB**: `http://localhost:7860/health` dan `http://localhost:7860/db/status`

---

## 2. Menjalankan dengan Docker Compose (PostgreSQL 16 + FastAPI/Web)
Berkas [`docker-compose.yml`](file:///d:/SEMESTER%205/ML/Projek_1/docker-compose.yml) menjalankan 2 kontainer (`postgres:16-alpine` dengan *persistent volume* `pgdata` dan `signbridge-asean`):

```powershell
docker compose up --build -d
```

Setelah kontainer berjalan:
- **Frontend Web PWA (Port 8080)**: `http://localhost:8080`
- **API & Swagger Docs (Port 7860)**: `http://localhost:7860/docs`
- **PostgreSQL 16 (Port 5432)**: `localhost:5432` (database: `signbridge_db`, user: `signbridge`)

---

## 3. Deployment Cloud Bonus (Azure Container Apps)
Skrip [`deploy/azure/deploy.sh`](file:///d:/SEMESTER%205/ML/Projek_1/deploy/azure/deploy.sh) tetap dipertahankan untuk *deployment* satu perintah ke Azure Container Apps:
```bash
bash deploy/azure/deploy.sh
```

---

## 4. Troubleshooting
- **Database PostgreSQL belum menyala saat pengembangan lokal**: Tidak masalah; [`DatabaseManager`](file:///d:/SEMESTER%205/ML/Projek_1/server/database.py) otomatis beralih ke *fallback* lokal (`sqlite-fallback`) sehingga aplikasi web dan API tetap berjalan 100%.
- **Perubahan tampilan web tidak langsung terlihat**: Tekan **`Ctrl + Shift + R`** pada peramban untuk memuat ulang *Service Worker* PWA.

