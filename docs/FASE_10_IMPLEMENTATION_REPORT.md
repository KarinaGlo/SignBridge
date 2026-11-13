# LAPORAN FASE 10.1 — VERIFY PYTORCH IMPORT FIX & DOCKER REBUILD
**Proyek:** SignBridge ID–PH (BISINDO $\leftrightarrow$ FSL) Multimodal Classroom Bridge  
**Tanggal:** 7 November 2026  

---

## 1. File yang Diubah

| No | File | Jenis Perubahan |
|---|---|---|
| 1 | `signbridge/text/__init__.py` | Memisahkan import runtime (`sentence_to_pseudo_gloss`, `gloss_to_sentence_rules` dari `pseudo_gloss.py`) dari import modul training/evaluasi (`train_text.py`, `eval_translate.py`) menggunakan *lazy module loading* PEP 562 (`__getattr__`). |
| 2 | `signbridge/text/train_text.py` | Menambahkan *optional guard* `try: import torch ... except ImportError:` sehingga fungsi metrik teks murni (`compute_bleu`, `compute_chrf`) tetap dapat diimpor dan dijalankan saat seeding database di container Docker ringan tanpa PyTorch, sementara kelas `BahdanauAttention`, `GRUAttentionSeq2Seq`, dan `run_text_experiment` tetap berjalan penuh ketika PyTorch tersedia. |
| 3 | `signbridge/audio/__init__.py` | Memisahkan import metrik runtime (`compute_wer`, `compute_cer`, `compute_rtf`) dari import objek training (`WhisperASRWrapper`, `run_asr_experiment`) menggunakan PEP 562 (`__getattr__`). |
| 4 | `signbridge/audio/train_asr.py` | Menambahkan *optional guard* `try: import torch ... except ImportError:` sehingga fungsi metrik audio murni (`compute_wer`, `compute_cer`, `compute_rtf`) dapat diimpor saat seeding database di container Docker tanpa PyTorch, sementara `LightweightAudioEncoderDecoder`, `WhisperASRWrapper`, dan `run_asr_experiment` tetap utuh ketika PyTorch tersedia. |
| 5 | `signbridge/image/__init__.py` | Memisahkan import fungsi pemotongan tangan runtime (`compute_hand_crop_box`, `crop_and_resize_hand`, `normalize_imagenet` dari `crop.py`) dari import modul training (`build_image_model`, `run_image_training`, `export_fingerspell_onnx` dari `train_image.py`) menggunakan PEP 562 (`__getattr__`). |
| 6 | `tests/test_database_integration.py` | Menambahkan 2 pengujian regresi baru: `test_runtime_startup_without_torch` (mensimulasikan `sys.modules['torch'] = None` dan menguji startup `create_app()` + seeding database) dan `test_training_imports_remain_available` (memastikan seluruh simbol training tetap dapat diimpor saat PyTorch tersedia). |

---

## 2. Alasan Perubahan (Root Cause Analysis)

1. **Penyebab Container `signbridge-asean` Restarting (`ModuleNotFoundError: No module named 'torch'`):**
   - Image Docker [`server/Dockerfile`](file:///d:/SEMESTER%205/ML/Projek_1/server/Dockerfile) dirancang ringan untuk inferensi (`onnxruntime` + `fastapi` + `sqlalchemy` + `psycopg2-binary` sesuai [`server/requirements.txt`](file:///d:/SEMESTER%205/ML/Projek_1/server/requirements.txt)) tanpa menginstal PyTorch (`torch`).
   - Saat [`server/app.py`](file:///d:/SEMESTER%205/ML/Projek_1/server/app.py#L52) mengeksekusi `from signbridge.text.pseudo_gloss import gloss_to_sentence_rules`, Python terlebih dahulu mengeksekusi [`signbridge/text/__init__.py`](file:///d:/SEMESTER%205/ML/Projek_1/signbridge/text/__init__.py).
   - Sebelumnya, `signbridge/text/__init__.py` secara *eager* menjalankan `from signbridge.text.train_text import (...)` pada baris 7, yang langsung memanggil `import torch` pada baris 27 di `signbridge/text/train_text.py`.
   - Selain itu, saat `server/database.py` melakukan *initial seeding* tabel `evaluation_runs` (`_run_and_record_verified_evaluations`) pada container PostgreSQL baru, fungsi tersebut mengimpor `compute_wer`, `compute_bleu`, dan `compute_chrf` dari `train_asr.py` dan `train_text.py`.
2. **Solusi Tanpa Menambah Dependency Besar (`torch`) ke Docker:**
   - Dengan menerapkan *lazy attribute loading* (`__getattr__` PEP 562) pada `signbridge/text/__init__.py`, `signbridge/audio/__init__.py`, dan `signbridge/image/__init__.py` serta melindungi `import torch` di `train_text.py` dan `train_asr.py`, modul runtime dan seeding database berjalan 100% tanpa PyTorch, sedangkan modul training tetap utuh ketika dijalankan di lingkungan training.

---

## 3. Hasil Semua Pengujian

### 3.1 Primary & Database Integration Suite
**Command:**
```powershell
pytest tests/test_signbridge_suite.py tests/test_database_integration.py -v
```
**Hasil Aktual (`task-652`):**
- **PASSED:** `18` (`12` di `test_signbridge_suite.py` + `6` di `test_database_integration.py`, termasuk `test_runtime_startup_without_torch` dan `test_training_imports_remain_available`)
- **FAILED:** `0`
- **SKIPPED:** `0`
- **Durasi:** `31.06s`

### 3.2 JavaScript Parity & Handcrop Suite
**Command:**
```powershell
node --test tests/js/parity.test.mjs tests/js/handcrop.test.mjs
```
**Hasil Aktual:**
- **PASSED:** `7`
- **FAILED:** `0`
- **SKIPPED:** `0`
- **Durasi:** `588.84ms`

### 3.3 Full Baseline Python Test Suite (`pytest -q`)
**Command:**
```powershell
pytest -q
```
**Hasil Aktual (`task-690`):**
- **PASSED:** **`345`**
- **FAILED:** **`0`**
- **SKIPPED:** **`0`**
- **Durasi:** **`124.59s (0:02:04)`**

---

## 4. Investigasi Penyebab `pytest -q` Exit Code 1 Sebelumnya

Pada eksekusi `task-657` sebelumnya (yang berjalan bersamaan ketika Docker sedang mengekstrak 488 MB paket Debian di disk), 2 *property-based test* Hypothesis pada [`tests/test_frame_extractor.py`](file:///d:/SEMESTER%205/ML/Projek_1/tests/test_frame_extractor.py) mengalami `hypothesis.errors.DeadlineExceeded` (batas default Hypothesis 200ms per test case):
1. `test_property_frame_files_sequential_no_gaps(num_frames=26)`:
   - Log aktual: `On an initial run, this test took 250.45ms, which exceeded the deadline of 200.00ms, but on a subsequent run it took 77.49 ms, which did not.`
2. `test_property_valid_compression_levels_produce_readable_pngs(compression=0, num_frames=10)`:
   - Log aktual: `On an initial run, this test took 260.67ms, which exceeded the deadline of 200.00ms, but on a subsequent run it took 120.80 ms, which did not.`

**Kesimpulan Investigasi:**
- Bukan merupakan kegagalan logika kode (*assertion failure*), melainkan fluktuasi latensi penulisan file PNG sementara (`tmp_path_factory`) di Windows ketika disk sedang sibuk (> 200ms).
- Saat dijalankan kembali secara terpisah (`pytest tests/test_frame_extractor.py -q`, `task-661`), seluruh **66 passed in 15.47s**.
- Saat seluruh suite dijalankan kembali (`pytest -q`, `task-690`), seluruh **345 passed, 0 failed in 124.59s** tanpa mengubah ekspektasi tes apa pun.

---

## 5. Status Docker Compose

### 5.1 Rebuild & Startup Container
**Command yang dijalankan:**
```powershell
docker compose down
docker compose build --no-cache signbridge
docker compose up -d
docker compose ps
```
**Output Aktual `docker compose ps`:**
```text
NAME                  IMAGE                 COMMAND                  SERVICE      CREATED          STATUS                    PORTS
signbridge-asean      projek_1-signbridge   "uvicorn server.app:…"   signbridge   53 seconds ago   Up 40 seconds (healthy)   0.0.0.0:7860->7860/tcp, [::]:7860->7860/tcp, 0.0.0.0:8080->7860/tcp, [::]:8080->7860/tcp
signbridge-postgres   postgres:16-alpine    "docker-entrypoint.s…"   postgres     53 seconds ago   Up 52 seconds (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
```
Kedua container (`signbridge-asean` dan `signbridge-postgres`) berstatus **`Up ... (healthy)`** dan tidak lagi mengalami *Restarting*.

### 5.2 Log Container `signbridge-asean`
**Command:**
```powershell
docker logs signbridge-asean --tail 100
```
**Output Aktual:**
```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
INFO:     127.0.0.1:38872 - "GET /health HTTP/1.1" 200 OK
```

---

## 6. Status PostgreSQL 16 Asli (`db_backend: "postgresql"`)

### 6.1 Verifikasi `GET http://localhost:7860/health`
**Command:**
```powershell
Invoke-RestMethod http://localhost:7860/health | ConvertTo-Json -Depth 5
```
**Output Aktual:**
```json
{
    "status":  "ok",
    "model_loaded":  true,
    "num_classes":  32,
    "concepts_loaded":  32,
    "db_connected":  true,
    "db_backend":  "postgresql"
}
```

### 6.2 Verifikasi `GET http://localhost:7860/db/status`
**Command:**
```powershell
Invoke-RestMethod http://localhost:7860/db/status | ConvertTo-Json -Depth 5
```
**Output Aktual:**
```json
{
    "db_connected":  true,
    "active_backend":  "postgresql",
    "database_url":  "postgresql+psycopg2://signbridge:***@postgres:5432/signbridge_db",
    "tables":  [
                   "sign_concepts",
                   "model_versions",
                   "evaluation_runs",
                   "inference_logs",
                   "dataset_recordings"
               ],
    "counts":  {
                   "sign_concepts":  58,
                   "model_versions":  20,
                   "evaluation_runs":  3,
                   "inference_logs":  0,
                   "dataset_recordings":  0
               },
    "last_error":  null
}
```

### 6.3 Verifikasi Langsung 5 Tabel di Dalam Container `signbridge-postgres`
**Command:**
```powershell
docker exec signbridge-postgres psql -U signbridge -d signbridge_db -c "\dt"
```
**Output Aktual:**
```text
                List of relations
 Schema |        Name        | Type  |   Owner    
--------+--------------------+-------+------------
 public | dataset_recordings | table | signbridge
 public | evaluation_runs    | table | signbridge
 public | inference_logs     | table | signbridge
 public | model_versions     | table | signbridge
 public | sign_concepts      | table | signbridge
(5 rows)
```

### 6.4 Verifikasi `/docs` & Endpoint Text Builder (`POST /sentence`)
**Command:**
```powershell
Invoke-WebRequest -Uri http://localhost:7860/docs -UseBasicParsing | Select-Object StatusCode, StatusDescription
Invoke-RestMethod -Uri http://localhost:7860/sentence -Method Post -ContentType "application/json" -Body '{"gloss":["SAYA","MAU","BELAJAR","BUKU"],"lang":"id"}' | ConvertTo-Json -Depth 5
```
**Output Aktual:**
```text
StatusCode StatusDescription
---------- -----------------
       200 OK               
{
    "gloss":  "SAYA MAU BELAJAR BUKU",
    "text":  "Saya mau belajar buku.",
    "lang":  "id",
    "model":  "B0+T2-Hybrid"
}
```

---

## 7. Status Empat Modalitas

| Modalitas | Status Runtime di Docker & Lokal | Detail Implementasi & Data |
|---|---|---|
| **1. Video (BISINDO & FSL)** | **AKTIF (`PASSED`)** | Model ONNX `web/model/student.onnx` (`model_loaded: true`, `32` kelas) berjalan di container `signbridge-asean` (`POST /predict`) dan di browser (`MediaPipe Holistic` 86-node graph + `PHONOLOGY_DB`). |
| **2. Gambar (Fingerspelling A–Z)** | **AKTIF (`PASSED`)** | Model ONNX `web/model/fingerspell.onnx` (`26` kelas A–Z) dan klasifikasi geometri 21 titik tangan (`FINGERSPELL_DB` di `web/js/fingerspell.js`) berjalan penuh. |
| **3. Audio (Speech-to-Text & TTS)** | **AKTIF (Web Speech API Browser + Fallback Server `POST /asr`)** | Di browser menggunakan Web Speech Recognition & Web Speech Synthesis (`id-ID` & `fil-PH`); di server `POST /asr` memvalidasi ukuran file (batas 10 MB) dan mencatat telemetri ke PostgreSQL `inference_logs`. |
| **4. Teks & Jembatan ID $\leftrightarrow$ FIL** | **AKTIF (`PASSED`)** | `POST /sentence` (`gloss_to_sentence_rules` tanpa ketergantungan PyTorch) dan `POST /translate` (`BridgeModule` L1/L2/L3 untuk 32 konsep BISINDO $\leftrightarrow$ FSL) berjalan penuh dan teruji pada 105 kalimat manusia nyata (`data/text/test_manual.tsv`). |

---

## 8. Masalah yang Belum Terselesaikan / Catatan Operasional

1. **Dataset Eksternal Besar Belum Diunduh/Dilatih Secara Penuh:**
   - Sesuai instruksi untuk tidak mengunduh dataset besar tanpa persetujuan, dataset eksternal (`WL-BISINDO`, `WLASL-300`, `FSL-105`, `Mendeley BISINDO Alphabet`, `FLEURS id_id`) serta 960 video fisik `SignBridge-Kelas` belum diunduh ke dalam repositori. Bobot `student.onnx` dan `fingerspell.onnx` saat ini adalah artefak tervalidasi kontrak bentuk tensor & paritas (`< 1e-4`), namun belum dilatih pada korpus video/gambar eksternal penuh.
2. **Endpoint Server `POST /asr` Menggunakan Respons Ringan (Tanpa Bobot Whisper di Container):**
   - Container Docker ringan tidak menyertakan bobot `faster-whisper`/`torch` agar ukuran image tetap ramping dan cepat dibangun; pengenalan suara real-time utama berjalan di browser melalui Web Speech API (`web/js/speech.js`).
3. **Atribut `version: "3.9"` pada `docker-compose.yml`:**
   - Docker Compose terbaru menampilkan peringatan minor `the attribute version is obsolete, it will be ignored` (tidak memengaruhi jalannya container).

