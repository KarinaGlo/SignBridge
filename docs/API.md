# Dokumentasi Endpoint API (`docs/API.md`)

Backend FastAPI ([`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py)) menyediakan endpoint inferensi utama (Kontrak 6) dan endpoint database operasional PostgreSQL. Dokumentasi interaktif Swagger UI dapat diakses di `http://localhost:7860/docs`.

---

## 1. Endpoint Utama Aplikasi (Kontrak 6 — Dipertahankan 100%)

### `GET /health`
Memeriksa kesehatan server, status pemuatan model ONNX, jumlah kelas, konsep jembatan, dan koneksi database.
- **Response (`200 OK`)**:
  ```json
  {
    "status": "ok",
    "model_loaded": true,
    "num_classes": 32,
    "concepts_loaded": 32,
    "db_connected": true,
    "db_backend": "postgresql"
  }
  ```

### `POST /predict`
Menjalankan inferensi kosakata isyarat dari deret keypoint `[F, 86, 3]` dan mencatat log ke `inference_logs` secara *non-blocking*.
- **Request Body**:
  ```json
  {
    "keypoints": [[[0.5, 0.25, 0.0], "... 86 titik x 3 koordinat ..."]],
    "top_k": 3,
    "room_code": "2050"
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "gloss": "HALO",
    "confidence": 0.94,
    "top_k": [
      {"gloss": "HALO", "label": 0, "confidence": 0.94}
    ],
    "latency_ms": 4.12
  }
  ```

### `POST /asr`
Transkripsi berkas audio ucapan guru/teman (`multipart/form-data`, batas maksimum 10 MB; mengembalikan `HTTP 413` jika melebihi batas).

### `POST /sentence`
Menyusun kalimat Bahasa Indonesia (`id`) atau Filipino (`fil`) yang alami dari deret gloss.
- **Request Body**: `{"gloss": ["SAYA", "MAU", "TANYA", "GURU"], "lang": "id"}`
- **Response (`200 OK`)**: `{"gloss": "SAYA MAU TANYA GURU", "text": "Saya ingin bertanya kepada guru.", "lang": "id", "model": "B0+T2-Hybrid"}`

### `POST /translate`
Jembatan terjemahan 3 Lapis Indonesia $\leftrightarrow$ Filipina (`L1 Concept Lookup`, `L2 Neural MT`, `L3 Reference Animation`).
- **Request Body**: `{"text": "Saya mau tanya guru", "src": "id", "tgt": "fil"}`

### `WS /ws/{kode}`
Relay WebSocket sinkronisasi pesan ruang kelas multi-perangkat menggunakan kode ruang 4 digit.

---

## 2. Endpoint Database Operasional PostgreSQL

| Method & Endpoint | Fungsi | Parameter Query / Body |
| :--- | :--- | :--- |
| `GET /db/status` | Memeriksa koneksi database, tipe backend aktif (`postgresql` / `sqlite-fallback`), daftar tabel, dan jumlah baris. | - |
| `GET /db/concepts` | Mengambil daftar 32 konsep BISINDO $\leftrightarrow$ FSL dan 26 Abjad `A`–`Z` dari tabel `sign_concepts`. | `?category=Sapaan` (opsional) |
| `GET /db/models` | Mengambil daftar 20 versi model (`M0`–`M5`, `I1`–`I3`, `A1`–`A3`, `B0/T1`–`T3`, `X1`–`X4`) dari `model_versions`. | `?modality=video` (opsional) |
| `GET /db/evaluations` | Mengambil hasil evaluasi model dari `evaluation_runs`. | `?model_code=B0` (opsional) |
| `POST /db/evaluations` | Menyimpan hasil evaluasi baru (misal hasil LOSO / ablation Gloria) ke `evaluation_runs`. | JSON `EvaluationCreateRequest` |
| `GET /db/logs` | Mengambil histori `inference_logs` terbaru. | `?limit=50&endpoint=/predict&modality=video` |
| `GET /db/recordings` | Mengambil metadata rekaman mandiri `SignBridge-Kelas` dari `dataset_recordings`. | `?signer_id=S01` (opsional) |
| `POST /db/recordings` | Mencatat metadata rekaman mandiri baru ke `dataset_recordings`. | JSON `RecordingCreateRequest` |

