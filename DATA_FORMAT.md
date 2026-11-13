# DATA FORMAT — Skema Format Data SignBridge BISINDO

> Dokumentasi teknis format data keypoint dan anotasi yang digunakan dalam sistem SignBridge.
> Requirement: 15.6

---

## 1. Array Keypoint — File `.npy`

### 1.1 File Koordinat Keypoint

| Atribut | Nilai |
|---|---|
| Ekstensi file | `.npy` (NumPy binary) |
| Nama file | `<video_id>.npy` |
| Shape | `[T, 543, 3]` |
| Dtype | `float32` |
| Rentang nilai | `[-1.0, 1.0]` (koordinat ternormalisasi) |

**Penjelasan dimensi:**

```
[T, 543, 3]
 │   │    └─ koordinat: x, y, z
 │   └────── jumlah keypoint (543 total)
 └────────── jumlah frame (variabel, 1 ≤ T ≤ 10.000)
```

**Breakdown 543 keypoint:**

| Indeks | Kelompok | Jumlah Keypoint | Keterangan |
|---|---|---|---|
| `[0:21]` | Tangan kiri | 21 | MediaPipe Hand landmarks |
| `[21:42]` | Tangan kanan | 21 | MediaPipe Hand landmarks |
| `[42:75]` | Pose tubuh | 33 | MediaPipe Pose landmarks |
| `[75:543]` | Wajah | 468 | MediaPipe FaceMesh landmarks |

**Mapping pose tubuh (indeks dalam array global = indeks + 42):**

| Indeks Pose | Indeks Global | Label |
|---|---|---|
| 0 | 42 | nose |
| 1 | 43 | left_eye_inner |
| 2 | 44 | left_eye |
| 3 | 45 | left_eye_outer |
| 4 | 46 | right_eye_inner |
| 5 | 47 | right_eye |
| 6 | 48 | right_eye_outer |
| 7 | 49 | left_ear |
| 8 | 50 | right_ear |
| 9 | 51 | mouth_left |
| 10 | 52 | mouth_right |
| 11 | 53 | left_shoulder |
| 12 | 54 | right_shoulder |
| 13 | 55 | left_elbow |
| 14 | 56 | right_elbow |
| 15 | 57 | left_wrist |
| 16 | 58 | right_wrist |
| 17 | 59 | left_pinky |
| 18 | 60 | right_pinky |
| 19 | 61 | left_index |
| 20 | 62 | right_index |
| 21 | 63 | left_thumb |
| 22 | 64 | right_thumb |
| 23 | 65 | left_hip |
| 24 | 66 | right_hip |
| 25 | 67 | left_knee |
| 26 | 68 | right_knee |
| 27 | 69 | left_ankle |
| 28 | 70 | right_ankle |
| 29 | 71 | left_heel |
| 30 | 72 | right_heel |
| 31 | 73 | left_foot_index |
| 32 | 74 | right_foot_index |

**Normalisasi koordinat:**

- Koordinat `x`, `y` dinormalisasi ke `[-1.0, 1.0]` relatif terhadap bounding box tubuh per frame.
- Koordinat `z` menunjukkan kedalaman relatif (juga ternormalisasi oleh MediaPipe).
- Jika bounding box memiliki lebar atau tinggi nol, digunakan bounding box frame sebelumnya yang valid.

---

### 1.2 File Confidence Score

| Atribut | Nilai |
|---|---|
| Ekstensi file | `.npy` (NumPy binary) |
| Nama file | `<video_id>_conf.npy` |
| Shape | `[T, 543, 1]` |
| Dtype | `float32` |
| Rentang nilai | `[0.0, 1.0]` |

```
[T, 543, 1]
 │   │    └─ confidence score (satu nilai per keypoint per frame)
 │   └────── jumlah keypoint (543 total, urutan sama dengan koordinat)
 └────────── jumlah frame (sama dengan file koordinat)
```

---

### 1.3 Contoh Penggunaan Python

```python
import numpy as np

# Muat keypoint
keypoints = np.load("data/keypoints/S001_MAKAN_001.npy")
# keypoints.shape == (T, 543, 3), dtype == float32

# Muat confidence
confidence = np.load("data/keypoints/S001_MAKAN_001_conf.npy")
# confidence.shape == (T, 543, 1), dtype == float32

# Akses tangan kiri (21 keypoint)
left_hand = keypoints[:, 0:21, :]    # shape: [T, 21, 3]

# Akses pose tubuh (33 keypoint, indeks 42–74)
pose = keypoints[:, 42:75, :]        # shape: [T, 33, 3]

# Akses keypoint kiri bahu (pose indeks 11, global indeks 53)
left_shoulder = keypoints[:, 53, :]  # shape: [T, 3]
```

---

## 2. File Anotasi — Format JSON Lines (`.jsonl`)

### 2.1 Skema Field Wajib

Setiap baris dalam file `.jsonl` adalah satu objek JSON valid yang mewakili metadata satu video.

| Field | Tipe | Wajib | Nilai Valid | Keterangan |
|---|---|---|---|---|
| `path` | `string` | **Ya** | Path relatif ke file video | Contoh: `"raw/MAKAN/S001_MAKAN_001.mp4"` |
| `gloss` | `string` | **Ya** | Salah satu dari 32 gloss | Contoh: `"MAKAN"` |
| `signer_id` | `string` | **Ya** | Format `S###` | Contoh: `"S001"` |
| `split` | `string` | **Ya** | `"train"`, `"val"`, `"test"` | Split dataset |

### 2.2 Field Opsional

| Field | Tipe | Keterangan |
|---|---|---|
| `duration_sec` | `float` | Durasi video dalam detik |
| `resolution` | `string` | Format `"WxH"`, contoh: `"640x480"` |
| `fps` | `float` | Frame rate video |

### 2.3 Contoh Entri `.jsonl`

```json
{"path": "raw/MAKAN/S001_MAKAN_001.mp4", "gloss": "MAKAN", "signer_id": "S001", "split": "train", "duration_sec": 3.2, "resolution": "640x480", "fps": 30.0}
{"path": "raw/MINUM/S002_MINUM_001.mp4", "gloss": "MINUM", "signer_id": "S002", "split": "val", "duration_sec": 2.8, "resolution": "1280x720", "fps": 30.0}
{"path": "raw/MAKAN/S003_MAKAN_001.mp4", "gloss": "MAKAN", "signer_id": "S003", "split": "test", "duration_sec": 3.0, "resolution": "640x480", "fps": 30.0}
```

### 2.4 Aturan Validasi

1. Setiap baris **harus** dapat di-parse sebagai JSON yang valid.
2. Semua empat field wajib (`path`, `gloss`, `signer_id`, `split`) **harus** ada dan bertipe string.
3. Nilai `split` **harus** merupakan salah satu dari: `"train"`, `"val"`, `"test"`.
4. Nilai `gloss` **harus** merupakan salah satu dari 32 gloss yang terdefinisi.
5. Nilai `signer_id` **harus** mengikuti format `S` diikuti minimal satu digit.
6. Jika field opsional ada, tipe datanya **harus** sesuai (`float` untuk `duration_sec` dan `fps`, `string` untuk `resolution`).

### 2.5 Penanganan Error

Jika validasi gagal, `AnnotationParser` akan menghasilkan `SchemaValidationError` dengan:
- Nama file `.jsonl`
- Nomor baris yang bermasalah (1-indexed)
- Nama field yang bermasalah
- Nilai yang ditemukan

---

## 3. Konfigurasi Graf Keypoint — `configs/graph_config.yaml`

File YAML ini mendefinisikan topologi `Keypoint_Graph` untuk Stream_A.

**Field wajib:**

| Field | Tipe | Keterangan |
|---|---|---|
| `num_nodes` | `int` | Jumlah node (harus 33 untuk pose tubuh) |
| `node_labels` | `list[str]` | Label string untuk setiap node, panjang = `num_nodes` |
| `edges.spatial` | `list[[int, int]]` | Pasangan indeks edge anatomis |
| `edges.temporal` | `list` atau `[]` | Dibuat programatik; bisa kosong di YAML |
| `edges.symmetry` | `list[[int, int]]` | Pasangan simetri kiri–kanan |

**Aturan validasi:**
- Semua indeks node dalam `edges.spatial` dan `edges.symmetry` harus berada dalam `[0, num_nodes - 1]`.
- Tidak boleh ada isolated node setelah semua edge dikonstruksi.

---

## 4. Anotasi Fonologis — `configs/phonological_annotations.yaml`

File YAML ini mendefinisikan label fonologis untuk setiap gloss.

**Skema per gloss:**

```yaml
NAMA_GLOSS:
  handshape:  "<string>"   # salah satu dari 20 kelas handshape
  lokasi:     "<string>"   # salah satu dari 10 kelas lokasi
  arah_gerak: "<string>"   # salah satu dari 8 kelas arah_gerak
```

**Kelas yang valid:**

- `handshape` (20 kelas): `B-flat`, `B-open`, `C-shape`, `O-shape`, `F-shape`, `V-shape`,
  `G-shape`, `H-shape`, `L-shape`, `A-shape`, `S-fist`, `D-shape`, `W-shape`, `Y-shape`,
  `5-open`, `X-hook`, `R-cross`, `ILY`, `N-shape`, `K-shape`
- `lokasi` (10 kelas): `neutral-space`, `mouth`, `chin`, `forehead`, `chest`, `shoulder`,
  `temple`, `neck`, `cheek`, `abdomen`
- `arah_gerak` (8 kelas): `towards-body`, `away-from-body`, `upward`, `downward`,
  `lateral-left`, `lateral-right`, `circular`, `stationary`

---

## 5. Ringkasan Validasi Format

| File | Constraint Kritis | Exception jika Gagal |
|---|---|---|
| `<id>.npy` | shape `[T, 543, 3]`, dtype `float32`, nilai ∈ `[-1, 1]` | `SchemaValidationError` |
| `<id>_conf.npy` | shape `[T, 543, 1]`, dtype `float32`, nilai ∈ `[0, 1]` | `SchemaValidationError` |
| `*.jsonl` | field wajib ada, split valid, JSON parseable per baris | `SchemaValidationError` |
| `graph_config.yaml` | indeks node valid, tidak ada isolated node | `GraphConfigError` |
| `phonological_annotations.yaml` | 32 gloss, nilai label dalam set valid | Pesan error + hentikan proses |
