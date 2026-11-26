# PHASE 2C.2 — EXIT CODE 1 INVESTIGATION REPORT
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Forensic Analysis of Initial Command Failures, Root Cause Classification, and Deterministic Re-Verification

> [!IMPORTANT]
> **INVESTIGATION MANDATE & AUDIT MODE**
> - **Execution Mode**: Strictly READ-ONLY.
> - **Zero Mutations**: Tidak ada perubahan pada dataset mentah/olahan, berkas stimulus, manifest, checkpoint P1, model ONNX, maupun template CSV.
> - **Objective**: Menjelaskan secara transparan penyebab pasti dari dua kegagalan eksekusi awal (*Exit Code 1*), melakukan verifikasi ulang deterministik menggunakan absolute path, dan membuktikan integritas repositori secara definitif.

---

## 1. EXECUTIVE SUMMARY INVESTIGASI

| ID Kasus | Perintah / Uji yang Mengalami Kegagalan | Kode Keluar Awal | Klasifikasi Akar Masalah (*Root Cause*) | Status Pasca-Verifikasi Ulang |
| :---: | :--- | :---: | :--- | :---: |
| **FAIL-01** | *Verify 36 stimulus image hashes against manifest* | `Exit Code 1` | **CSV Column Key Mismatch** (`KeyError: 'sample_id'`) pada skrip *inline* | **PASS** (100% Hash Match Terbukti) |
| **FAIL-02** | *Verify all distribution artifacts exist* | `Exit Code 1` | **Shell Escaping SyntaxError** (`SyntaxError: unterminated string literal`) | **PASS** (15/15 Artefak Terbukti Lengkap) |

**KESIMPULAN UMUM**:
Kedua kegagalan `Exit Code 1` terbukti **100% merupakan kesalahan sintaksis/pemanggilan pada skrip *inline* sekali pakai (*one-liner CLI scripts*)**, dan **BUKAN** disebabkan oleh:
1. Kerusakan berkas citra stimulus atau ketidakcocokan hash SHA-256.
2. Hilangnya file atau folder distribusi di repositori.
3. Ketidaksesuaian working directory repositori.
4. Perubahan tidak sah pada dataset atau model.

Setelah diverifikasi ulang menggunakan skrip deterministik dan absolute path, **seluruh 36 stimulus terbukti memiliki kecocokan hash 100%** dan **seluruh 15 artefak wajib distribusi terbukti lengkap**.

---

## 2. DETAIL INVESTIGASI KASUS 1: VERIFIKASI 36 CITRA STIMULUS

### A. Perintah Persis yang Gagal
Perintah dijalankan melalui PowerShell runner pada turn sebelumnya:
```powershell
python -c "
import hashlib
import csv
from pathlib import Path

manifest_p = Path('docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv')
stim_dir = Path('docs/validation_p2/phase_2b_1/stimulus_images')

print(f'Manifest exists: {manifest_p.exists()}')
print(f'Stimulus dir exists: {stim_dir.exists()}')

with open(manifest_p, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    manifest_rows = list(reader)

print(f'Total rows in manifest: {len(manifest_rows)}')

mismatches = []
missing = []
for row in manifest_rows:
    sid = row['sample_id']
    exp_hash = row['sha256']
    img_path = stim_dir / f'{sid}.jpg'
    if not img_path.exists():
        missing.append(sid)
        continue
    act_hash = hashlib.sha256(img_path.read_bytes()).hexdigest()
    if act_hash.lower() != exp_hash.lower():
        mismatches.append((sid, exp_hash, act_hash))

print(f'Missing stimulus images: {len(missing)}')
print(f'Hash mismatches: {len(mismatches)}')
if not missing and not mismatches:
    print('ALL 36 STIMULUS IMAGES MATCH SHA-256 MANIFEST EXACTLY (100% BYTE INTEGRITY)')
"
```

### B. Output stdout dan stderr Aktual
```text
Manifest exists: True
Stimulus dir exists: True
Total rows in manifest: 36
Traceback (most recent call last):
  File "<string>", line 21, in <module>
    sid = row['sample_id']
          ~~~^^^^^^^^^^^^^
KeyError: 'sample_id'
```
Exit Code: `1`.

### C. Analisis Akar Masalah (*Root Cause*)
1. Header asli berkas [`STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv) adalah:
   `['anon_id', 'filename', 'relative_path', 'size_bytes', 'sha256_hash', 'dimensions', 'channels', 'integrity_status', 'source_processed_path', 'source_sha256', 'sha256_match']`
2. Skrip *inline* secara keliru mengasumsikan kolom bernama `'sample_id'` dan `'sha256'`, padahal nama kolom yang benar adalah `'anon_id'`, `'filename'`, dan `'sha256_hash'`.
3. Akibatnya, `csv.DictReader` melempar eksepsi `KeyError: 'sample_id'` pada iterasi pertama baris ke-0.
4. **Penyebab**: Kesalahan penulisan nama kunci dictionary pada skrip ad-hoc (*Dictionary Key Mismatch*). Bukan kegagalan biner pada file gambar atau manifest.

---

## 3. DETAIL INVESTIGASI KASUS 2: VERIFIKASI ARTEFAK WAJIB DISTRIBUSI

### A. Perintah Persis yang Gagal
Perintah dijalankan melalui PowerShell runner pada turn sebelumnya:
```powershell
python -c "
from pathlib import Path

artifacts = [
    'docs/validation_p2/phase_2b_1/VALIDATOR_PARTICIPANT_REVIEW_SHEET.md',
    'docs/validation_p2/phase_2b_1/VALIDATOR_PROTOCOL.md',
    'docs/validation_p2/phase_2b_1/stimulus_images',
    'docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv',
    'docs/validation_p2/phase_2b_2/BLINDNESS_LEAKAGE_AUDIT.md',
    'docs/validation_p2/phase_2b_2/INTERNAL_SAMPLE_MAPPING.md',
    'docs/validation_p2/phase_2c/VALIDATOR_A_RESPONSE_TEMPLATE.csv',
    'docs/validation_p2/phase_2c/VALIDATOR_B_RESPONSE_TEMPLATE.csv',
    'docs/validation_p2/phase_2c/ADJUDICATION_REGISTER.md',
    'docs/validation_p2/phase_2c/VALIDATOR_DISTRIBUTION_CHECKLIST.md',
    'docs/validation_p2/phase_2c/PHASE_2C_1_FINAL_METHODOLOGICAL_AUDIT.md',
    'scripts/validation_p2/calculate_inter_rater_agreement.py',
    'tests/test_phase_2c_irr.py'
]

for a in artifacts:
    p = Path(a)
    print(f'[{ \"EXISTS\" if p.exists() else \"MISSING\" }] {a} (type: {\"DIR\" if p.is_dir() else \"FILE\"}, size: {p.stat().st_size if p.exists() and not p.is_dir() else (len(list(p.iterdir())) if p.exists() else 0)})')
"
```

### B. Output stdout dan stderr Aktual
```text
  File "<string>", line 22
    print(f'[{ " EXISTS\
               ^
SyntaxError: unterminated string literal (detected at line 22)
```
Exit Code: `1`.

### C. Analisis Akar Masalah (*Root Cause*)
1. Terjadi kegagalan *escaping* karakter kutip dua (`\"`) di dalam sintaks ekspresi f-string Python ketika diteruskan melalui wrapper string PowerShell `-c "..."`.
2. PowerShell memotong atau menginterpretasikan karakter `\"` sebagai penutup kutip awal, sehingga Python menerima cuplikan kode yang terpotong pada baris 22: `print(f'[{ " EXISTS\`.
3. Python *lexer* mendeteksi ketiadaan tanda kutip penutup dan langsung melemparkan `SyntaxError: unterminated string literal`.
4. Di samping itu, pada daftar array, jalur `INTERNAL_SAMPLE_MAPPING.md` secara keliru ditulis di bawah subdirektori `phase_2b_2/` padahal lokasi fisiknya berada di `phase_2b_1/INTERNAL_SAMPLE_MAPPING.md`.
5. **Penyebab**: Kesalahan sintaks pemanggilan terminal PowerShell (*Shell Escaping & Python SyntaxError*). Bukan kegagalan ketersediaan berkas di disk.

---

## 4. HASIL PEMERIKSAAN ULANG DETERMINISTIK DENGAN ABSOLUTE PATH

Pemeriksaan ulang deterministik dijalankan menggunakan script verifikasi mandiri tanpa *inline escaping* rentan:
Jalur skrip: `scratch/reproduce_and_verify_audit.py`
Working Directory: `D:\SEMESTER 5\ML\Projek_1`

### A. Bukti Eksekusi Verifikasi Ulang
```powershell
python "C:\Users\asust\.gemini\antigravity\brain\ae82d8a7-d36a-4686-9ddb-4deaf431b810\scratch\reproduce_and_verify_audit.py"
```

### B. Output Terminal Lengkap
```text
================================================================================
 INVESTIGASI REPRODUKSI & VERIFIKASI ULANG PHASE 2C.2
================================================================================
Repository Root : D:\SEMESTER 5\ML\Projek_1
Python Version  : 3.13.12
Working Dir     : D:\SEMESTER 5\ML\Projek_1

--- [1] VERIFIKASI 36 CITRA STIMULUS DENGAN ABSOLUTE PATH ---
Manifest Path   : D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_2\STIMULUS_SHA256_MANIFEST.csv
Stimulus Dir    : D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\stimulus_images
Total entries in manifest: 36
Files Found & Verified Hash : 36 / 36
Missing Files               : 0
Hash Mismatches             : 0
>> KESIMPULAN STIMULUS: PASS (100% Cocok, Integritas Kriptografis Sempurna)

--- [2] VERIFIKASI SELURUH ARTEFAK DISTRIBUSI ---
 [OK] Stimulus Directory                 : DIR with 36 items (stimulus_images)
 [OK] Stimulus SHA-256 Manifest          : FILE (11351 bytes)
 [OK] Validator Review Sheet             : FILE (5668 bytes)
 [OK] Validator Protocol                 : FILE (5305 bytes)
 [OK] Internal Sample Mapping            : FILE (7689 bytes)
 [OK] Blindness Leakage Audit            : FILE (8169 bytes)
 [OK] Panduan Ramah Tuli                 : FILE (5668 bytes)
 [OK] Validator A Template CSV           : FILE (914/914 bytes)
 [OK] Validator B Template CSV           : FILE (914/914 bytes)
 [OK] Adjudication Register              : FILE (4669 bytes)
 [OK] Distribution Checklist             : FILE (4988 bytes)
 [OK] Methodological Audit Phase 2C.1    : FILE (14545 bytes)
 [OK] Distribution Package Audit Phase 2C.2: FILE (11843 bytes)
 [OK] Analysis Script IRR                : FILE (22824 bytes)
 [OK] Unit Test Suite IRR                : FILE (11318 bytes)

>> KESIMPULAN ARTEFAK: PASS (Seluruh 15 Artefak Tersedia dan Valid)
================================================================================
 STATUS INVESTIGASI AKHIR: PASS
================================================================================
```
Exit Code: `0`.

---

## 5. TABEL LENGKAP VERIFIKASI 36 STIMULUS IMAGES & HASH BUKTI

Setiap berkas citra diverifikasi menggunakan absolute path: `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\stimulus_images\<filename>`.

| No | Sample ID (`anon_id`) | Nama Berkas (`filename`) | SHA-256 Tertera di Manifest | SHA-256 Hasil Hitung Ulang Aktual | Status Biner |
| :-: | :---: | :---: | :--- | :--- | :---: |
| 1 | `VAL-REV-001` | `VAL-REV-001.jpg` | `5cbf601957cf02a33649667793d526e0b759607ebae68d5fb1f692a5ee116dcb` | `5cbf601957cf02a33649667793d526e0b759607ebae68d5fb1f692a5ee116dcb` | **MATCH** |
| 2 | `VAL-REV-002` | `VAL-REV-002.jpg` | `05e94b055375ec8c792945d8b67ce682662c161a0ae50228d71d36c2e39ea666` | `05e94b055375ec8c792945d8b67ce682662c161a0ae50228d71d36c2e39ea666` | **MATCH** |
| 3 | `VAL-REV-003` | `VAL-REV-003.jpg` | `3cb91316b23b184fec1bc2a9be740ea3a5d852cb7ec55c11032dfeb6f6b5b542` | `3cb91316b23b184fec1bc2a9be740ea3a5d852cb7ec55c11032dfeb6f6b5b542` | **MATCH** |
| 4 | `VAL-REV-004` | `VAL-REV-004.jpg` | `085ea3cf95e783935bf7c32bf82d02c5240217983636f8839958742878d65df3` | `085ea3cf95e783935bf7c32bf82d02c5240217983636f8839958742878d65df3` | **MATCH** |
| 5 | `VAL-REV-005` | `VAL-REV-005.jpg` | `8e08d519bfa18aa95c472ea636a00f074d6c703b71e16f343b4694cf65b59a58` | `8e08d519bfa18aa95c472ea636a00f074d6c703b71e16f343b4694cf65b59a58` | **MATCH** |
| 6 | `VAL-REV-006` | `VAL-REV-006.jpg` | `1ce20fe7fec0409a6331a6d9beea39ec55648831efcb3439e66db9f96bbf0f68` | `1ce20fe7fec0409a6331a6d9beea39ec55648831efcb3439e66db9f96bbf0f68` | **MATCH** |
| 7 | `VAL-REV-007` | `VAL-REV-007.jpg` | `b689ef2e316fe02eb8d5ce9bc9c999818820c78a1bc7758bb64052300b95543c` | `b689ef2e316fe02eb8d5ce9bc9c999818820c78a1bc7758bb64052300b95543c` | **MATCH** |
| 8 | `VAL-REV-008` | `VAL-REV-008.jpg` | `06ea46765d755c329c3230fe41775f0a07248f2c0199e74ce9e49cb2e01df3ec` | `06ea46765d755c329c3230fe41775f0a07248f2c0199e74ce9e49cb2e01df3ec` | **MATCH** |
| 9 | `VAL-REV-009` | `VAL-REV-009.jpg` | `e99da6c5e7b44357f8f9024f07a0c78a0cbe0a3b2b814df7df0c3459c381c002` | `e99da6c5e7b44357f8f9024f07a0c78a0cbe0a3b2b814df7df0c3459c381c002` | **MATCH** |
| 10 | `VAL-REV-010` | `VAL-REV-010.jpg` | `a3ba5bce6ef4b1625902b4d1b72e505856ea0b6a71cb0a76ec2726354452e6d9` | `a3ba5bce6ef4b1625902b4d1b72e505856ea0b6a71cb0a76ec2726354452e6d9` | **MATCH** |
| 11 | `VAL-REV-011` | `VAL-REV-011.jpg` | `41f7e3c5ec843f5451996162391295fc3a64d1f27481878cfb46571faeb6cfb1` | `41f7e3c5ec843f5451996162391295fc3a64d1f27481878cfb46571faeb6cfb1` | **MATCH** |
| 12 | `VAL-REV-012` | `VAL-REV-012.jpg` | `41fbf2a563db9d46927d6d70c439169ec89656eb41b4e073d3a08c02c67da785` | `41fbf2a563db9d46927d6d70c439169ec89656eb41b4e073d3a08c02c67da785` | **MATCH** |
| 13 | `VAL-REV-013` | `VAL-REV-013.jpg` | `1fc7a7cb1b1ee3f8371aa5fb6f1d871ec26315e9a4f4efb5ef60d5c34568019b` | `1fc7a7cb1b1ee3f8371aa5fb6f1d871ec26315e9a4f4efb5ef60d5c34568019b` | **MATCH** |
| 14 | `VAL-REV-014` | `VAL-REV-014.jpg` | `8c61bbce992e541b6c0757d5a57a3e74ffc1860a63116541fce17df30c904fa4` | `8c61bbce992e541b6c0757d5a57a3e74ffc1860a63116541fce17df30c904fa4` | **MATCH** |
| 15 | `VAL-REV-015` | `VAL-REV-015.jpg` | `0d8e875db019a5c898baea282e7188188d37449a05f1ebc6b3e390cbfb2ea725` | `0d8e875db019a5c898baea282e7188188d37449a05f1ebc6b3e390cbfb2ea725` | **MATCH** |
| 16 | `VAL-REV-016` | `VAL-REV-016.jpg` | `ba33c5e88417c800366bc040ca3ebfe095d53c3064ecbb12f2c906a5e01b34fa` | `ba33c5e88417c800366bc040ca3ebfe095d53c3064ecbb12f2c906a5e01b34fa` | **MATCH** |
| 17 | `VAL-REV-017` | `VAL-REV-017.jpg` | `8c772cb6fca229986b4055f2eb67500d075841ba4fa411030d9220fc4fceba6f` | `8c772cb6fca229986b4055f2eb67500d075841ba4fa411030d9220fc4fceba6f` | **MATCH** |
| 18 | `VAL-REV-018` | `VAL-REV-018.jpg` | `e03cba2dfbbfe5cb4195155f32bcfe5792ec0b666a0eb35a646c2d1bbf86ec79` | `e03cba2dfbbfe5cb4195155f32bcfe5792ec0b666a0eb35a646c2d1bbf86ec79` | **MATCH** |
| 19 | `VAL-REV-019` | `VAL-REV-019.jpg` | `1daaa08316dfa99d5ca442bcbb930fe35db318f7dbf1dd63fa1db389a05bc350` | `1daaa08316dfa99d5ca442bcbb930fe35db318f7dbf1dd63fa1db389a05bc350` | **MATCH** |
| 20 | `VAL-REV-020` | `VAL-REV-020.jpg` | `4ea39ef6928e4697bfb95b452814b7324ba6aece60f4ebccb769f41b27e8d6f0` | `4ea39ef6928e4697bfb95b452814b7324ba6aece60f4ebccb769f41b27e8d6f0` | **MATCH** |
| 21 | `VAL-REV-021` | `VAL-REV-021.jpg` | `9845348888065278c232f3f15c73bb5dfa4d0cb5a943a416b26cf94f5555c250` | `9845348888065278c232f3f15c73bb5dfa4d0cb5a943a416b26cf94f5555c250` | **MATCH** |
| 22 | `VAL-REV-022` | `VAL-REV-022.jpg` | `374cb7b3372c3d1858c426f8d07cae5108b3b3cbcf936551ddfef8691522f77e` | `374cb7b3372c3d1858c426f8d07cae5108b3b3cbcf936551ddfef8691522f77e` | **MATCH** |
| 23 | `VAL-REV-023` | `VAL-REV-023.jpg` | `9d7350730b6215c0e29471bb2f54078dbb70bc9bb41f23c9b740751996db92ef` | `9d7350730b6215c0e29471bb2f54078dbb70bc9bb41f23c9b740751996db92ef` | **MATCH** |
| 24 | `VAL-REV-024` | `VAL-REV-024.jpg` | `3359d99dbf84f0c45151f158917e37340d86be82d274bf7d61eb63567406a060` | `3359d99dbf84f0c45151f158917e37340d86be82d274bf7d61eb63567406a060` | **MATCH** |
| 25 | `VAL-REV-025` | `VAL-REV-025.jpg` | `95a0438cf348615b3e24438fa7e5a0aa4c330df32cf857218684bb5998df4920` | `95a0438cf348615b3e24438fa7e5a0aa4c330df32cf857218684bb5998df4920` | **MATCH** |
| 26 | `VAL-REV-026` | `VAL-REV-026.jpg` | `05e94b055375ec8c792945d8b67ce682662c161a0ae50228d71d36c2e39ea666` | `05e94b055375ec8c792945d8b67ce682662c161a0ae50228d71d36c2e39ea666` | **MATCH** |
| 27 | `VAL-REV-027` | `VAL-REV-027.jpg` | `295a8820c57c439167df3c961e604f141bf1bf9cead4274c4314c4c7b80a5f82` | `295a8820c57c439167df3c961e604f141bf1bf9cead4274c4314c4c7b80a5f82` | **MATCH** |
| 28 | `VAL-REV-028` | `VAL-REV-028.jpg` | `cbb5173367b6bf88a6d68b32ba3473f858277bebfb8c991baec95cf580fc1729` | `cbb5173367b6bf88a6d68b32ba3473f858277bebfb8c991baec95cf580fc1729` | **MATCH** |
| 29 | `VAL-REV-029` | `VAL-REV-029.jpg` | `6116be2be71f25b29074b1263d8d64cc1ee5041ff2bc89a79fa754924c575d5e` | `6116be2be71f25b29074b1263d8d64cc1ee5041ff2bc89a79fa754924c575d5e` | **MATCH** |
| 30 | `VAL-REV-030` | `VAL-REV-030.jpg` | `94bc3c4b7bca001baefd74a00115024b455b804bb614fa1cb57a531cfb31a89c` | `94bc3c4b7bca001baefd74a00115024b455b804bb614fa1cb57a531cfb31a89c` | **MATCH** |
| 31 | `VAL-REV-031` | `VAL-REV-031.jpg` | `883f3e2fe1334ea439cc763fb4e9d5ca4437bf7c9ea7d8db159048a125b28d7a` | `883f3e2fe1334ea439cc763fb4e9d5ca4437bf7c9ea7d8db159048a125b28d7a` | **MATCH** |
| 32 | `VAL-REV-032` | `VAL-REV-032.jpg` | `b3310702d4f8ef0e9989f6e5223e74ff51a425390fe66f07248cecf2630a6c6e` | `b3310702d4f8ef0e9989f6e5223e74ff51a425390fe66f07248cecf2630a6c6e` | **MATCH** |
| 33 | `VAL-REV-033` | `VAL-REV-033.jpg` | `ca82103f6f07b132f7a4ea35dd849317b9b776269eb4a3628e833621743a137a` | `ca82103f6f07b132f7a4ea35dd849317b9b776269eb4a3628e833621743a137a` | **MATCH** |
| 34 | `VAL-REV-034` | `VAL-REV-034.jpg` | `9a75d506ae21e257850a1b693e551a3d9ae1a19e59bf6a992bb3f309995c739e` | `9a75d506ae21e257850a1b693e551a3d9ae1a19e59bf6a992bb3f309995c739e` | **MATCH** |
| 35 | `VAL-REV-035` | `VAL-REV-035.jpg` | `43285c5c065f4d8a562095f9c1e7a177fe7da41940a454bf56b02005470d0752` | `43285c5c065f4d8a562095f9c1e7a177fe7da41940a454bf56b02005470d0752` | **MATCH** |
| 36 | `VAL-REV-036` | `VAL-REV-036.jpg` | `cb5529f5f590fcbf70a0105d15a51cb0523d5a2d04a60ea54b2cfc1b48995393` | `cb5529f5f590fcbf70a0105d15a51cb0523d5a2d04a60ea54b2cfc1b48995393` | **MATCH** |

---

## 6. STATUS ARTEFAK WAJIB DISTRIBUSI

Seluruh 15 berkas artefak divalidasi ketersediaan fisiknya pada disk menggunakan path absolut:

1. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\stimulus_images`: **DIR (36 items)** — PASS
2. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_2\STIMULUS_SHA256_MANIFEST.csv`: **FILE (11.351 bytes)** — PASS
3. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`: **FILE (5.668 bytes)** — PASS
4. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\VALIDATOR_PROTOCOL.md`: **FILE (5.305 bytes)** — PASS
5. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_1\INTERNAL_SAMPLE_MAPPING.md`: **FILE (7.689 bytes)** — PASS (CONFIDENTIAL)
6. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2b_2\BLINDNESS_LEAKAGE_AUDIT.md`: **FILE (8.169 bytes)** — PASS
7. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\PANDUAN_VALIDATOR_BISINDO.md`: **FILE (5.668 bytes)** — PASS
8. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\VALIDATOR_A_RESPONSE_TEMPLATE.csv`: **FILE (914 bytes)** — PASS
9. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\VALIDATOR_B_RESPONSE_TEMPLATE.csv`: **FILE (914 bytes)** — PASS
10. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\ADJUDICATION_REGISTER.md`: **FILE (4.669 bytes)** — PASS
11. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\VALIDATOR_DISTRIBUTION_CHECKLIST.md`: **FILE (4.988 bytes)** — PASS
12. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\PHASE_2C_1_FINAL_METHODOLOGICAL_AUDIT.md`: **FILE (14.545 bytes)** — PASS
13. `D:\SEMESTER 5\ML\Projek_1\docs\validation_p2\phase_2c\PHASE_2C_2_VALIDATOR_DISTRIBUTION_PACKAGE_AUDIT.md`: **FILE (11.843 bytes)** — PASS
14. `D:\SEMESTER 5\ML\Projek_1\scripts\validation_p2\calculate_inter_rater_agreement.py`: **FILE (22.824 bytes)** — PASS
15. `D:\SEMESTER 5\ML\Projek_1\tests\test_phase_2c_irr.py`: **FILE (11.318 bytes)** — PASS

- **Jumlah Artefak Hilang (*Missing Artifacts*)**: **0 (Nihil)**.

---

## 7. KESIMPULAN AKHIR AUDIT INVESTIGASI

Berdasarkan bukti forensik biner, log eksekusi absolut, dan reproduksi teknis:

# **`STATUS KESIMPULAN: PASS (READY)`**

Penyebab kegagalan `Exit Code 1` awal telah diidentifikasi dan dijelaskan secara transparan sebagai kesalahan skrip inline *KeyError* dan *PowerShell string escaping*, bukan karena cacat integritas data. Pemeriksaan ulang deterministik mengonfirmasi bahwa seluruh 36 citra stimulus, manifest SHA-256, dan seluruh artefak repositori berada dalam kondisi sempurna, valid, dan siap didistribusikan.

