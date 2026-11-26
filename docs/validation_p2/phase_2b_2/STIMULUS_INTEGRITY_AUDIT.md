# AUDIT INTEGRITAS CITRA STIMULUS (STIMULUS INTEGRITY AUDIT)
## Modul Image I1 — BISINDO Alphabet Fingerspelling (MobileNetV3-Small)
### SignBridge ASEAN — Multimodal Classroom Bridge (BISINDO ↔ FSL)

---

## 1. Ringkasan Eksekutif (Executive Summary)
Laporan ini memvalidasi integritas fisik, resolusi, format, dan konsistensi kriptografis dari **36 berkas citra stimulus anonim** (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`) yang tersimpan di direktori:
`docs/validation_p2/phase_2b_1/stimulus_images/`

Tujuan pengujian adalah memastikan bahwa seluruh citra stimulus:
1. Secara fisik utuh, tidak kosong (*zero-byte*), dan bebas dari kerusakan (*corruption*).
2. Memiliki resolusi terstandarisasi $224 \times 224$ piksel dengan ruang warna 3-kanal RGB.
3. Memiliki identitas biner (*cryptographic SHA-256 hash*) yang cocok 100% dengan berkas sumber aslinya di `data/processed/bisindo_alphabet/`.
4. Bebas dari penukaran berkas (*file swap*), duplikasi pemetaan, atau salah pasang sampel (*mismatched pairing*).

---

## 2. Metodologi Pengujian Integritas Berkas (Task 1)
Pengujian teknis dilakukan menggunakan script Python terisolasi:
- **Verifikasi Keterbacaan**: Membuka setiap berkas menggunakan mesin *Pillow (PIL)* untuk memeriksa integritas header JPEG dan *raster stream*.
- **Verifikasi Dimensi**: Memeriksa nilai piksel lebar ($W$) dan tinggi ($H$) serta mode warna (`RGB`).
- **Verifikasi Kriptografis**: Menghitung hash SHA-256 berukuran 256-bit (64 karakter heksadesimal) dengan *buffer read* 64 KB.

### 2.1 Hasil Pengujian Integritas Fisik 36 Berkas
- **Total Berkas Terdeteksi**: Tepat **36 berkas**.
- **Pola Penamaan**: Terverifikasi terurut secara konsisten dari `VAL-REV-001.jpg` hingga `VAL-REV-036.jpg`.
- **ID Duplikat**: **Nol (0)** ID duplikat.
- **Keterbacaan Berkas**: **100,0% (36/36 berkas)** dapat dibuka tanpa kesalahan I/O.
- **Dimensi & Mode Warna**: **100,0% (36/36 berkas)** berdimensi tepat $224 \times 224$ piksel, mode 3-kanal RGB.
- **Berkas Kosong / Corrupt**: **Nol (0)** berkas kosong ($0$ bytes) atau rusak. Rentang ukuran berkas berada pada $3.670$ bytes hingga $12.448$ bytes.

---

## 3. Konsistensi Pemetaan Internal (Internal Mapping Consistency — Task 2)

Pencocokan silang (*cross-referencing*) dilakukan secara otomatis antara berkas stimulus dengan:
1. Dokumen kunci peneliti: `docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md`.
2. Manifest dataset produksi: `data/processed/bisindo_alphabet/manifest.csv`.

### 3.1 Hasil Pengujian Kesetaraan Biner dan Piksel
- **Kecocokan Hash SHA-256**: **36 dari 36 sampel (100,0%)** memiliki nilai hash SHA-256 yang identik persis dengan berkas sumbernya di direktori `data/processed/bisindo_alphabet/`.
- **Kesetaraan Piksel Array**: Dilakukan perbandingan langsung matriks piksel `numpy.array_equal(arr_stimulus, arr_source)` terhadap seluruh $224 \times 224 \times 3 = 150.528$ nilai piksel per citra. Seluruh **36 citra (100,0%) identik piksel-demi-piksel (*lossless parity*)**.
- **Verifikasi Penukaran Berkas (*Swapped Files*)**: **Nol (0)** kasus penukaran berkas. Setiap ID anonim terpetakan secara bijektif (satu-ke-satu) ke sumber aslinya.
- **Verifikasi Pemetaan Ganda / Hilang**: Tidak ada ID anonim yang hilang atau memiliki rujukan ganda.

---

## 4. Tabel Verifikasi Integritas & Kriptografis (36 Sampel Stimulus)

Tabel berikut mendokumentasikan nilai hash SHA-256 dan status integritas masing-masing citra stimulus:

| Sample ID | Nama Berkas Stimulus | Ukuran (Bytes) | Dimensi | Mode | Nilai Hash SHA-256 | Status Integritas | Status Kesetaraan Sumber |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| `VAL-REV-001` | `VAL-REV-001.jpg` | $9.378$ | $224 \times 224$ | RGB | `49e4162ae18586482d36ec49188bf50cb8018c0c51ff6b31885aad762812f5a2` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-002` | `VAL-REV-002.jpg` | $10.024$ | $224 \times 224$ | RGB | `a8441607c5b59c399cae202c2654803689c2c346a3d8fc2fa7237f75df222d14` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-003` | `VAL-REV-003.jpg` | $5.362$ | $224 \times 224$ | RGB | `4b14d7ecf7ac2ee833bc0ff22a508a6b1b70e1b1efa2cddbeb2bdb1bab40dcc3` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-004` | `VAL-REV-004.jpg` | $8.070$ | $224 \times 224$ | RGB | `4f5c4ac3864ed6440962d55c9a882642fced4b34b7903b94618aa9ce59b368f9` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-005` | `VAL-REV-005.jpg` | $7.795$ | $224 \times 224$ | RGB | `faca457ad376326496f1660096f90b40f9efad094c9093c2a9b57735ce1ceb89` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-006` | `VAL-REV-006.jpg` | $6.974$ | $224 \times 224$ | RGB | `8be3d34af83bf44c716a9427e03b80bb55bb02dec857ea5f90e1212af5474926` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-007` | `VAL-REV-007.jpg` | $5.494$ | $224 \times 224$ | RGB | `255784f82cc4444338a0f96170a90e2c3389ebcca7d420d4fed4af2bbe105d85` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-008` | `VAL-REV-008.jpg` | $9.923$ | $224 \times 224$ | RGB | `7f81fa721d9de1eda50b689077eea7822ef8048b3661a4a73954d8efcbeb9d77` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-009` | `VAL-REV-009.jpg` | $6.331$ | $224 \times 224$ | RGB | `573209b8e451cd7449642f868350e7300958af03bd8f2b44fd29697abc7274ed` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-010` | `VAL-REV-010.jpg` | $8.074$ | $224 \times 224$ | RGB | `17ed50fa9cd7d5ad2f6d7448079696d12517d3e549589d032b85129010648846` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-011` | `VAL-REV-011.jpg` | $8.956$ | $224 \times 224$ | RGB | `e89e65b91f1a741b0cf6bbfc678a2e6b57297ea6c69a61f52966aa08f96605fb` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-012` | `VAL-REV-012.jpg` | $8.591$ | $224 \times 224$ | RGB | `49287a56b7e794f837be211ee8f29ca6154ebe62628d6cd376e7dba569720e42` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-013` | `VAL-REV-013.jpg` | $8.169$ | $224 \times 224$ | RGB | `8f6e55c4bbcd3477693567d974ef5c0f1411ecef53a7768221a7ebe610f8ca6c` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-014` | `VAL-REV-014.jpg` | $8.952$ | $224 \times 224$ | RGB | `b2dd2e1c642aa194d152880c3a4ce4732e6a97392a4e9292f9db778fda4ed824` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-015` | `VAL-REV-015.jpg` | $7.671$ | $224 \times 224$ | RGB | `17a8089ae1262d4c0628e967819dd3756ffae9db95c80efc93ec19b02319ef47` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-016` | `VAL-REV-016.jpg` | $7.675$ | $224 \times 224$ | RGB | `d4c5cba1b933d02a5a54dbbb75ebc08799307d9f95764bf1d0d97746ea50259f` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-017` | `VAL-REV-017.jpg` | $3.670$ | $224 \times 224$ | RGB | `bfcebb360d5b4129e924d54625f3c5b8e998e3b3e23ae62432d6aa96e1935767` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-018` | `VAL-REV-018.jpg` | $3.931$ | $224 \times 224$ | RGB | `0ae8a6ec12a95c96b010cbfbdfb13684eb2023d8c11e5ae5d7331dd58bebb938` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-019` | `VAL-REV-019.jpg` | $3.937$ | $224 \times 224$ | RGB | `ee62828e833fb35e729a6501fe9dbe39f8d956dfcb17cbbba4ca26a27e7790b9` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-020` | `VAL-REV-020.jpg` | $8.077$ | $224 \times 224$ | RGB | `d331a98075f10645607da74ecce3e582e0e0fba75440d995ff71c6ae78a10052` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-021` | `VAL-REV-021.jpg` | $4.296$ | $224 \times 224$ | RGB | `64582f3ef840742f15598642ca024b17bfb941584c3ea2d3d9223bb0d08a56b4` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-022` | `VAL-REV-022.jpg` | $4.954$ | $224 \times 224$ | RGB | `e61ff13028d7b322a3fc514f76aa9b1ff580c85c270d4c9dcf8cf407886a111a` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-023` | `VAL-REV-023.jpg` | $7.288$ | $224 \times 224$ | RGB | `e4af29f1da50b68e3b45483a77fc0a0bdb2e6c8fb692ce5a679910c2030e7758` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-024` | `VAL-REV-024.jpg` | $4.498$ | $224 \times 224$ | RGB | `2d78e63363ddee4549544458f3a464bcc40615d1e449a95f36863db244ff1480` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-025` | `VAL-REV-025.jpg` | $11.085$ | $224 \times 224$ | RGB | `18be40d78b223c384be0854af9f51afacbc16a811fa9ee193a6a048f7433b96b` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-026` | `VAL-REV-026.jpg` | $11.666$ | $224 \times 224$ | RGB | `b02b5223760cc1e1b4686dea797718b479aabb4fd07d1ba81bff900a5e30a073` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-027` | `VAL-REV-027.jpg` | $10.088$ | $224 \times 224$ | RGB | `b8557e91a253961159637a0706ef24a5006e39debf79b2c11bce67e450d2bf42` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-028` | `VAL-REV-028.jpg` | $10.741$ | $224 \times 224$ | RGB | `9bd801424436c81d1f0195868085e459d62e64ff0e374200e9b7843b75062391` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-029` | `VAL-REV-029.jpg` | $12.448$ | $224 \times 224$ | RGB | `81cdc63978b5ebc4ae819124b820e0189135754d65ced8fac08b63defe3c20c6` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-030` | `VAL-REV-030.jpg` | $8.077$ | $224 \times 224$ | RGB | `f7eed5a83eb22642aa0eaf110a375d999831bd03773f1d21b5cd6e75aad56c01` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-031` | `VAL-REV-031.jpg` | $8.599$ | $224 \times 224$ | RGB | `41b6966d3e598bbb9c1609affb6af55cc5bd5eeb394fe0c9e8927e413cb86c03` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-032` | `VAL-REV-032.jpg` | $9.644$ | $224 \times 224$ | RGB | `e26751109cd53d4a48dfc3c99f58c038c430553ff815a74bcbd148ac2d7833fa` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-033` | `VAL-REV-033.jpg` | $7.868$ | $224 \times 224$ | RGB | `e0ff7934b75d7bda3d73e53ad3d5f73d59a6f2308d1df7c1ca938415df72a869` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-034` | `VAL-REV-034.jpg` | $8.784$ | $224 \times 224$ | RGB | `9efe38b8e0b0b67d91e44955ab07054aa8a02b59e7e9980f9e894733b0e19b45` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-035` | `VAL-REV-035.jpg` | $8.694$ | $224 \times 224$ | RGB | `b39c1e685cc2f6bbc3cbcc5d258a4b30b8a92a67ff5f6a34421c80a2fc900806` | **VALID** | `MATCH_100%_EXACT` |
| `VAL-REV-036` | `VAL-REV-036.jpg` | $8.136$ | $224 \times 224$ | RGB | `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` | **VALID** | `MATCH_100%_EXACT` |

Dokumen manifest mesin lengkap tersimpan pada berkas:
[`docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv).

