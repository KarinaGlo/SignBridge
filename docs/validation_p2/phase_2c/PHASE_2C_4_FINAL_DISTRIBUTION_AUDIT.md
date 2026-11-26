# PHASE 2C.4 — FINAL PRE-DISTRIBUTION VALIDATOR PACKAGE AUDIT REPORT
## SignBridge ASEAN — Image Modality I1 (MobileNetV3-Small BISINDO A–Z)
### Comprehensive Read-Only Verification of External Validator Packages A & B

> [!IMPORTANT]
> **AUDIT MANDATE & READ-ONLY ENFORCEMENT**
> - **Execution Mode**: Strictly READ-ONLY. Tidak ada modifikasi terhadap dataset mentah/olahan, berkas citra stimulus, model, checkpoint P1, maupun template CSV.
> - **Direct Verification Principle**: Seluruh kesimpulan diverifikasi secara mandiri melalui inspeksi biner dan pembacaan berkas fisik aktual, bukan sekadar mengutip laporan fase sebelumnya.
> - **Zero Synthetic Responses**: Tidak ada data respons buatan/dummy.
> - **Firewall Protection**: Pemisahan 19 `TEST_SET_DIAGNOSTIC_ONLY` dan 17 `TRAIN_COHORT` dijaga ketat.

---

## 1. EXECUTIVE SUMMARY

| Dimensi Audit | Status Verifikasi | Bukti Aktual yang Diverifikasi |
| :--- | :---: | :--- |
| **Integritas 36 Stimulus vs Manifest** | **`VERIFIED (100% MATCH)`** | 36/36 berkas di Paket A & B cocok dengan hash kolom `sha256_hash` pada manifest master. |
| **Kesetaraan Biner Stimulus A vs B** | **`100% IDENTIK BINER`** | Seluruh 36 citra pada Paket A dan Paket B identik byte-per-byte (*0 difference*). |
| **Audit Visual & Watermark** | **`CLEAN`** | 224x224 RGB, metadata EXIF 100% bersih, bebas watermark, bebas teks label tersemat. |
| **Audit Dokumen Metodologi** | **`COMPLIANT`** | Menggunakan istilah `BLINDED_VALIDATOR_REVIEW`; 0 klaim *double-blind*; 0 klaim identitas dienkripsi; definisi 4 kategori dan batasan J/Z konsisten. |
| **Audit Template CSV Respons** | **`VALID & BLANK`** | 36 ID unik monotonik (`VAL-REV-001` s/d `036`), 100% sel keputusan kosong murni, kode `VAL-A` pada Paket A dan `VAL-B` pada Paket B. |
| **Audit Keamanan & Isolasi Paket** | **`SECURE (EXACTLY 40 FILES)`** | Tepat 40 file per paket; 0 file `INTERNAL_SAMPLE_MAPPING`, 0 file `.bak`, 0 laporan internal. |
| **Keputusan Kesiapan Teknis (*Technical Verdict*)** | **`PASS`** | Paket distribusi telah lulus seluruh uji integritas teknis dan metodologis untuk didistribusikan. |

---

## 2. HASIL VERIFIKASI 36 CITRA STIMULUS TERHADAP MASTER MANIFEST

Pemeriksaan kriptografis biner dijalankan secara independen terhadap setiap citra pada kedua paket distribusi dengan mencocokkannya ke master manifest:
- **Jalur Manifest**: [`docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv)
- **Kolom Kunci Manifest yang Digunakan**: `anon_id`, `filename`, `relative_path`, `sha256_hash`.

### Rincian Verifikasi 36 Sampel (Full 64-Hex SHA-256):

| No | Sample ID (`anon_id`) | Nama Berkas (`filename`) | SHA-256 Master Manifest | SHA-256 Aktual Paket A | SHA-256 Aktual Paket B | Status Biner |
| :-: | :---: | :---: | :--- | :--- | :--- | :---: |
| 1 | `VAL-REV-001` | `VAL-REV-001.jpg` | `49e4162ae18586482d36ec49188bf50cb8018c0c51ff6b31885aad762812f5a2` | `49e4162ae18586482d36ec49188bf50cb8018c0c51ff6b31885aad762812f5a2` | `49e4162ae18586482d36ec49188bf50cb8018c0c51ff6b31885aad762812f5a2` | **MATCH** |
| 2 | `VAL-REV-002` | `VAL-REV-002.jpg` | `a8441607c5b59c399cae202c2654803689c2c346a3d8fc2fa7237f75df222d14` | `a8441607c5b59c399cae202c2654803689c2c346a3d8fc2fa7237f75df222d14` | `a8441607c5b59c399cae202c2654803689c2c346a3d8fc2fa7237f75df222d14` | **MATCH** |
| 3 | `VAL-REV-003` | `VAL-REV-003.jpg` | `4b14d7ecf7ac2ee833bc0ff22a508a6b1b70e1b1efa2cddbeb2bdb1bab40dcc3` | `4b14d7ecf7ac2ee833bc0ff22a508a6b1b70e1b1efa2cddbeb2bdb1bab40dcc3` | `4b14d7ecf7ac2ee833bc0ff22a508a6b1b70e1b1efa2cddbeb2bdb1bab40dcc3` | **MATCH** |
| 4 | `VAL-REV-004` | `VAL-REV-004.jpg` | `4f5c4ac3864ed6440962d55c9a882642fced4b34b7903b94618aa9ce59b368f9` | `4f5c4ac3864ed6440962d55c9a882642fced4b34b7903b94618aa9ce59b368f9` | `4f5c4ac3864ed6440962d55c9a882642fced4b34b7903b94618aa9ce59b368f9` | **MATCH** |
| 5 | `VAL-REV-005` | `VAL-REV-005.jpg` | `faca457ad376326496f1660096f90b40f9efad094c9093c2a9b57735ce1ceb89` | `faca457ad376326496f1660096f90b40f9efad094c9093c2a9b57735ce1ceb89` | `faca457ad376326496f1660096f90b40f9efad094c9093c2a9b57735ce1ceb89` | **MATCH** |
| 6 | `VAL-REV-006` | `VAL-REV-006.jpg` | `8be3d34af83bf44c716a9427e03b80bb55bb02dec857ea5f90e1212af5474926` | `8be3d34af83bf44c716a9427e03b80bb55bb02dec857ea5f90e1212af5474926` | `8be3d34af83bf44c716a9427e03b80bb55bb02dec857ea5f90e1212af5474926` | **MATCH** |
| 7 | `VAL-REV-007` | `VAL-REV-007.jpg` | `255784f82cc4444338a0f96170a90e2c3389ebcca7d420d4fed4af2bbe105d85` | `255784f82cc4444338a0f96170a90e2c3389ebcca7d420d4fed4af2bbe105d85` | `255784f82cc4444338a0f96170a90e2c3389ebcca7d420d4fed4af2bbe105d85` | **MATCH** |
| 8 | `VAL-REV-008` | `VAL-REV-008.jpg` | `7f81fa721d9de1eda50b689077eea7822ef8048b3661a4a73954d8efcbeb9d77` | `7f81fa721d9de1eda50b689077eea7822ef8048b3661a4a73954d8efcbeb9d77` | `7f81fa721d9de1eda50b689077eea7822ef8048b3661a4a73954d8efcbeb9d77` | **MATCH** |
| 9 | `VAL-REV-009` | `VAL-REV-009.jpg` | `573209b8e451cd7449642f868350e7300958af03bd8f2b44fd29697abc7274ed` | `573209b8e451cd7449642f868350e7300958af03bd8f2b44fd29697abc7274ed` | `573209b8e451cd7449642f868350e7300958af03bd8f2b44fd29697abc7274ed` | **MATCH** |
| 10 | `VAL-REV-010` | `VAL-REV-010.jpg` | `17ed50fa9cd7d5ad2f6d7448079696d12517d3e549589d032b85129010648846` | `17ed50fa9cd7d5ad2f6d7448079696d12517d3e549589d032b85129010648846` | `17ed50fa9cd7d5ad2f6d7448079696d12517d3e549589d032b85129010648846` | **MATCH** |
| 11 | `VAL-REV-011` | `VAL-REV-011.jpg` | `e89e65b91f1a741b0cf6bbfc678a2e6b57297ea6c69a61f52966aa08f96605fb` | `e89e65b91f1a741b0cf6bbfc678a2e6b57297ea6c69a61f52966aa08f96605fb` | `e89e65b91f1a741b0cf6bbfc678a2e6b57297ea6c69a61f52966aa08f96605fb` | **MATCH** |
| 12 | `VAL-REV-012` | `VAL-REV-012.jpg` | `49287a56b7e794f837be211ee8f29ca6154ebe62628d6cd376e7dba569720e42` | `49287a56b7e794f837be211ee8f29ca6154ebe62628d6cd376e7dba569720e42` | `49287a56b7e794f837be211ee8f29ca6154ebe62628d6cd376e7dba569720e42` | **MATCH** |
| 13 | `VAL-REV-013` | `VAL-REV-013.jpg` | `8f6e55c4bbcd3477693567d974ef5c0f1411ecef53a7768221a7ebe610f8ca6c` | `8f6e55c4bbcd3477693567d974ef5c0f1411ecef53a7768221a7ebe610f8ca6c` | `8f6e55c4bbcd3477693567d974ef5c0f1411ecef53a7768221a7ebe610f8ca6c` | **MATCH** |
| 14 | `VAL-REV-014` | `VAL-REV-014.jpg` | `b2dd2e1c642aa194d152880c3a4ce4732e6a97392a4e9292f9db778fda4ed824` | `b2dd2e1c642aa194d152880c3a4ce4732e6a97392a4e9292f9db778fda4ed824` | `b2dd2e1c642aa194d152880c3a4ce4732e6a97392a4e9292f9db778fda4ed824` | **MATCH** |
| 15 | `VAL-REV-015` | `VAL-REV-015.jpg` | `5fd1d0c1ed0c65f2650f158f1cd883d0b6fc953d13c7c780622fe4899055fe50` | `5fd1d0c1ed0c65f2650f158f1cd883d0b6fc953d13c7c780622fe4899055fe50` | `5fd1d0c1ed0c65f2650f158f1cd883d0b6fc953d13c7c780622fe4899055fe50` | **MATCH** |
| 16 | `VAL-REV-016` | `VAL-REV-016.jpg` | `01ea0e9a3dd14b60f9dbc14dc0a58130f83a1b0333e2092f897dbdca284eb10a` | `01ea0e9a3dd14b60f9dbc14dc0a58130f83a1b0333e2092f897dbdca284eb10a` | `01ea0e9a3dd14b60f9dbc14dc0a58130f83a1b0333e2092f897dbdca284eb10a` | **MATCH** |
| 17 | `VAL-REV-017` | `VAL-REV-017.jpg` | `da582b83f4140825274a22a3adcbd0f622849e21a318b6bc7a73f5d6c928a7f6` | `da582b83f4140825274a22a3adcbd0f622849e21a318b6bc7a73f5d6c928a7f6` | `da582b83f4140825274a22a3adcbd0f622849e21a318b6bc7a73f5d6c928a7f6` | **MATCH** |
| 18 | `VAL-REV-018` | `VAL-REV-018.jpg` | `3b3943536a10169b9e34d127c6fba8b5e6d02bbaf3342a4442dc369a200bce6c` | `3b3943536a10169b9e34d127c6fba8b5e6d02bbaf3342a4442dc369a200bce6c` | `3b3943536a10169b9e34d127c6fba8b5e6d02bbaf3342a4442dc369a200bce6c` | **MATCH** |
| 19 | `VAL-REV-019` | `VAL-REV-019.jpg` | `d1f7944071eae3d6429ee9fa760aca7716aa126a3c4f6dec3fd92eeeab1d4e8b` | `d1f7944071eae3d6429ee9fa760aca7716aa126a3c4f6dec3fd92eeeab1d4e8b` | `d1f7944071eae3d6429ee9fa760aca7716aa126a3c4f6dec3fd92eeeab1d4e8b` | **MATCH** |
| 20 | `VAL-REV-020` | `VAL-REV-020.jpg` | `882a4d38b521b7c34c52677293811b217edf559e7aeaa38c9dd5bca924622d7f` | `882a4d38b521b7c34c52677293811b217edf559e7aeaa38c9dd5bca924622d7f` | `882a4d38b521b7c34c52677293811b217edf559e7aeaa38c9dd5bca924622d7f` | **MATCH** |
| 21 | `VAL-REV-021` | `VAL-REV-021.jpg` | `654b0e2d78b9e91a23c44286ba736a4012ea989a7196bd3f482f87c1f6cf9013` | `654b0e2d78b9e91a23c44286ba736a4012ea989a7196bd3f482f87c1f6cf9013` | `654b0e2d78b9e91a23c44286ba736a4012ea989a7196bd3f482f87c1f6cf9013` | **MATCH** |
| 22 | `VAL-REV-022` | `VAL-REV-022.jpg` | `621d683f8f3037cfc54d81c9535073ceecac7bf95d310697849dba5b953e544c` | `621d683f8f3037cfc54d81c9535073ceecac7bf95d310697849dba5b953e544c` | `621d683f8f3037cfc54d81c9535073ceecac7bf95d310697849dba5b953e544c` | **MATCH** |
| 23 | `VAL-REV-023` | `VAL-REV-023.jpg` | `e4af29f1da50b68e3b45483a77fc0a0bdb2e6c8fb692ce5a679910c2030e7758` | `e4af29f1da50b68e3b45483a77fc0a0bdb2e6c8fb692ce5a679910c2030e7758` | `e4af29f1da50b68e3b45483a77fc0a0bdb2e6c8fb692ce5a679910c2030e7758` | **MATCH** |
| 24 | `VAL-REV-024` | `VAL-REV-024.jpg` | `2d78e63363ddee4549544458f3a464bcc40615d1e449a95f36863db244ff1480` | `2d78e63363ddee4549544458f3a464bcc40615d1e449a95f36863db244ff1480` | `2d78e63363ddee4549544458f3a464bcc40615d1e449a95f36863db244ff1480` | **MATCH** |
| 25 | `VAL-REV-025` | `VAL-REV-025.jpg` | `18be40d78b223c384be0854af9f51afacbc16a811fa9ee193a6a048f7433b96b` | `18be40d78b223c384be0854af9f51afacbc16a811fa9ee193a6a048f7433b96b` | `18be40d78b223c384be0854af9f51afacbc16a811fa9ee193a6a048f7433b96b` | **MATCH** |
| 26 | `VAL-REV-026` | `VAL-REV-026.jpg` | `b02b5223760cc1e1b4686dea797718b479aabb4fd07d1ba81bff900a5e30a073` | `b02b5223760cc1e1b4686dea797718b479aabb4fd07d1ba81bff900a5e30a073` | `b02b5223760cc1e1b4686dea797718b479aabb4fd07d1ba81bff900a5e30a073` | **MATCH** |
| 27 | `VAL-REV-027` | `VAL-REV-027.jpg` | `b8557e91a253961159637a0706ef24a5006e39debf79b2c11bce67e450d2bf42` | `b8557e91a253961159637a0706ef24a5006e39debf79b2c11bce67e450d2bf42` | `b8557e91a253961159637a0706ef24a5006e39debf79b2c11bce67e450d2bf42` | **MATCH** |
| 28 | `VAL-REV-028` | `VAL-REV-028.jpg` | `9bd801424436c81d1f0195868085e459d62e64ff0e374200e9b7843b75062391` | `9bd801424436c81d1f0195868085e459d62e64ff0e374200e9b7843b75062391` | `9bd801424436c81d1f0195868085e459d62e64ff0e374200e9b7843b75062391` | **MATCH** |
| 29 | `VAL-REV-029` | `VAL-REV-029.jpg` | `81cdc63978b5ebc4ae819124b820e0189135754d65ced8fac08b63defe3c20c6` | `81cdc63978b5ebc4ae819124b820e0189135754d65ced8fac08b63defe3c20c6` | `81cdc63978b5ebc4ae819124b820e0189135754d65ced8fac08b63defe3c20c6` | **MATCH** |
| 30 | `VAL-REV-030` | `VAL-REV-030.jpg` | `f7eed5a83eb22642aa0eaf110a375d999831bd03773f1d21b5cd6e75aad56c01` | `f7eed5a83eb22642aa0eaf110a375d999831bd03773f1d21b5cd6e75aad56c01` | `f7eed5a83eb22642aa0eaf110a375d999831bd03773f1d21b5cd6e75aad56c01` | **MATCH** |
| 31 | `VAL-REV-031` | `VAL-REV-031.jpg` | `41b6966d3e598bbb9c1609affb6af55cc5bd5eeb394fe0c9e8927e413cb86c03` | `41b6966d3e598bbb9c1609affb6af55cc5bd5eeb394fe0c9e8927e413cb86c03` | `41b6966d3e598bbb9c1609affb6af55cc5bd5eeb394fe0c9e8927e413cb86c03` | **MATCH** |
| 32 | `VAL-REV-032` | `VAL-REV-032.jpg` | `e26751109cd53d4a48dfc3c99f58c038c430553ff815a74bcbd148ac2d7833fa` | `e26751109cd53d4a48dfc3c99f58c038c430553ff815a74bcbd148ac2d7833fa` | `e26751109cd53d4a48dfc3c99f58c038c430553ff815a74bcbd148ac2d7833fa` | **MATCH** |
| 33 | `VAL-REV-033` | `VAL-REV-033.jpg` | `e0ff7934b75d7bda3d73e53ad3d5f73d59a6f2308d1df7c1ca938415df72a869` | `e0ff7934b75d7bda3d73e53ad3d5f73d59a6f2308d1df7c1ca938415df72a869` | `e0ff7934b75d7bda3d73e53ad3d5f73d59a6f2308d1df7c1ca938415df72a869` | **MATCH** |
| 34 | `VAL-REV-034` | `VAL-REV-034.jpg` | `9efe38b8e0b0b67d91e44955ab07054aa8a02b59e7e9980f9e894733b0e19b45` | `9efe38b8e0b0b67d91e44955ab07054aa8a02b59e7e9980f9e894733b0e19b45` | `9efe38b8e0b0b67d91e44955ab07054aa8a02b59e7e9980f9e894733b0e19b45` | **MATCH** |
| 35 | `VAL-REV-035` | `VAL-REV-035.jpg` | `b39c1e685cc2f6bbc3cbcc5d258a4b30b8a92a67ff5f6a34421c80a2fc900806` | `b39c1e685cc2f6bbc3cbcc5d258a4b30b8a92a67ff5f6a34421c80a2fc900806` | `b39c1e685cc2f6bbc3cbcc5d258a4b30b8a92a67ff5f6a34421c80a2fc900806` | **MATCH** |
| 36 | `VAL-REV-036` | `VAL-REV-036.jpg` | `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` | `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` | `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` | **MATCH** |

- **Total Citra Terdaftar di Manifest**: 36.
- **Citra Hilang (*Missing*)**: **0**.
- **Citra Berlebih (*Extra*)**: **0**.
- **Ketidakcocokan Hash (*Mismatches*)**: **0**.
- **Perbedaan Biner Antara Paket A dan Paket B**: **0 (Identik 100%)**.
- **Konfirmasi Khusus `VAL-REV-036`**: Nilai hash biner aktual pada Master Manifest, Paket A, dan Paket B adalah persis sama: `87e1b8c7098952c46fcc2b83120d55465afd7249ef6a5be7ada8d9325d8f1687` (**MATCH**).

---

## 3. AUDIT VISUAL DAN PEMERIKSAAN KEBOCORAN PADA CITRA

Pemeriksaan atribut visual dijalankan menggunakan pustaka Pillow (`PIL.Image`) dan *pixel-level forensic check*:
- **Resolusi**: Seluruh 36 berkas memiliki dimensi tepat 224 x 224 piksel.
- **Mode Warna**: Seluruh 36 berkas berformat 3-channel RGB standar.
- **Metadata EXIF**: **100% bersih / stripped** (tidak ada metadata kamera, waktu perekaman, lokasi GPS, maupun nama file mentah tersimpan di EXIF).
- **Tanda Visual / Watermark**: **0 temuan**. Tidak ada teks huruf, bounding box, atau anotasi AI yang tertera pada piksel gambar.

### Sampel-Sampel yang Memerlukan Perhatian Khusus Validator:
Berdasarkan investigasi forensik dataset, sampel-sampel berikut memiliki anomali visual yang perlu dicermati oleh validator manusia tanpa diberi tahu label asli:
1. **Representasi Statis Huruf Dinamis (J & Z)**:
   - `VAL-REV-009` (Asli: J) — Peraga memperagakan pose statis jari kelingking; rentan membingungkan dengan huruf statis I.
   - `VAL-REV-016`, `VAL-REV-019`, `VAL-REV-026`, `VAL-REV-027` (Asli: Z) — Peraga memperagakan pose statis telunjuk; rentan membingungkan dengan huruf statis D atau 1 jika tanpa lintasan gerak di udara.
2. **Pemotongan Batas Parah (*Border Clipping Outliers*)**:
   - `VAL-REV-025`, `VAL-REV-026`, `VAL-REV-027`, `VAL-REV-028`, `VAL-REV-029` — Sebagian konfigurasi jari atau pergelangan tangan terpotong oleh tepi bingkai gambar; validator diminta menentukan apakah informasi yang tersisa cukup untuk pembacaan (`AMBIGUOUS`/`UNDETERMINABLE`).
3. **Pencahayaan Gelap Ekstrem (*Lighting Outliers*)**:
   - `VAL-REV-021`, `VAL-REV-022`, `VAL-REV-023`, `VAL-REV-024` — Citra dengan kontras rendah dan bayangan gelap; menguji batas toleransi pembacaan gestur.

---

## 4. AUDIT DOKUMEN PESERTA DAN KONSISTENSI METODOLOGI

Tiga dokumen Markdown pada masing-masing paket diperiksa baris demi baris:
1. `PANDUAN_VALIDATOR_BISINDO.md`
2. `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`
3. `VALIDATOR_PROTOCOL.md`

### Temuan Audit Dokumen:
1. **Kesesuaian Istilah Blind Review**:
   - Istilah **`BLINDED_VALIDATOR_REVIEW`** digunakan secara tepat dan konsisten pada seluruh dokumen.
   - **Klaim `double-blind`**: **0 temuan (Telah dieliminasi sepenuhnya)**.
2. **Ketiadaan Klaim Enkripsi Palsu**:
   - Dokumen menyatakan: *"Identitas sampel disamarkan menggunakan kode anonim (`VAL-REV-001` sampai `VAL-REV-036`)."*
   - **Klaim bahwa identitas sampel dienkripsi**: **0 temuan (Tidak ada klaim enkripsi pada kode pseudonim)**.
   - Kata *kriptografis* hanya digunakan secara tepat pada penjelasan penghitungan *checksum hash SHA-256* file CSV saat pengembalian.
3. **Konsistensi Definisi 4 Kategori**:
   - Seluruh dokumen memuat definisi yang seragam untuk `CORRECT`, `INCORRECT`, `AMBIGUOUS`, dan `UNDETERMINABLE`.
   - Kewajiban mengisi `correct_letter` untuk pilihan `INCORRECT` ditegaskan di semua dokumen.
4. **Keterbatasan Foto Statis J/Z**:
   - Seluruh dokumen menegaskan bahwa pengujian menggunakan foto diam, pilihan `CORRECT` hanya menunjukkan bahwa pose dapat dikenali, foto diam tidak membuktikan lintasan gerak dinamis, dan validator dianjurkan memilih `AMBIGUOUS` atau `UNDETERMINABLE` jika bukti visual tidak memadai tanpa gerakan.
5. **Kerahasiaan Label & Model**:
   - Tidak ada label ground truth, prediksi model P1, probabilitas confidence, maupun informasi kohort train/test yang bocor ke dokumen peserta.
6. **Konsistensi Antara Paket A dan B**:
   - Seluruh file Markdown di Paket A dan Paket B **100% identik biner** (*SHA-256 match*).

---

## 5. AUDIT TEMPLATE CSV RESPONS

Pemeriksaan terhadap berkas CSV respons di kedua paket:
- `docs/validation_p2/phase_2c/distribution/validator_A/VALIDATOR_A_RESPONSE_TEMPLATE.csv`
- `docs/validation_p2/phase_2c/distribution/validator_B/VALIDATOR_B_RESPONSE_TEMPLATE.csv`

### Hasil Pemeriksaan:
1. **Header Baku**: `validator_code,sample_id,decision,correct_letter,regional_variation,notes,review_date` (Persis sama di kedua file).
2. **Jumlah Baris**: Tepat 37 baris (1 baris header + 36 baris rekaman data).
3. **Kesesuaian Kode Validator**:
   - Paket A: 100% sel `validator_code` bernilai `VAL-A`.
   - Paket B: 100% sel `validator_code` bernilai `VAL-B`.
4. **Kelengkapan & Keunikan ID**:
   - Tepat 36 sample ID unik dari `VAL-REV-001` sampai `VAL-REV-036` berurutan secara teratur.
   - Tidak ada ID duplikat, tidak ada ID yang hilang.
5. **Status Pengisian**:
   - Kolom `decision`, `correct_letter`, `regional_variation`, `notes`, dan `review_date` **100% kosong murni (0 data terisi)**.
   - Tidak ada rekayasa jawaban buatan/dummy.
6. **Format Garis Akhir**:
   - Diakhiri dengan standard POSIX single newline (`\n`), ukuran file tepat 914 bytes.

---

## 6. AUDIT KEAMANAN DAN ISOLASI PAKET

Pemeriksaan inventaris fisik pada kedua folder paket:
- `docs/validation_p2/phase_2c/distribution/validator_A/`: **Tepat 40 file**.
- `docs/validation_p2/phase_2c/distribution/validator_B/`: **Tepat 40 file**.

### Rincian 40 File per Paket:
- 36 file citra JPG di subfolder `stimulus_images/` (`VAL-REV-001.jpg` s/d `VAL-REV-036.jpg`).
- 1 file panduan: `PANDUAN_VALIDATOR_BISINDO.md`.
- 1 file lembar kerja: `VALIDATOR_PARTICIPANT_REVIEW_SHEET.md`.
- 1 file protokol: `VALIDATOR_PROTOCOL.md`.
- 1 file template CSV spesifik (`VALIDATOR_A_RESPONSE_TEMPLATE.csv` untuk Paket A, `VALIDATOR_B_RESPONSE_TEMPLATE.csv` untuk Paket B).

### Hasil Pemeriksaan Keamanan:
- **`INTERNAL_SAMPLE_MAPPING.md`**: **TIDAK ADA (0 temuan)**.
- **Berkas Backup (`*.bak`)**: **TIDAK ADA (0 temuan)**.
- **Laporan Model Internal / Manifest**: **TIDAK ADA (0 temuan)**.
- **Berkas Tambahan / Tak Dikenal**: **TIDAK ADA (0 temuan)**.

---

## 7. BATASAN AUDIT TEKNIS & PERBEDAAN DENGAN KEPATUHAN ETIKA RISET

> [!CAUTION]
> **KLARIFIKASI BATASAN AUDIT TEKNIS VS KELAYAKAN ETIKA PARTISIPAN MANUSIA**
> Audit teknis pada dokumen ini **hanya membuktikan integritas berkas, ketiadaan kebocoran data, dan kesiapan metodologis artefak**. Verifikasi teknis berkas komputer **TIDAK DAN BUKAN MERUPAKAN BUKTI KELAYAKAN ETIKA RISET INSTITUSIONAL SECARA MENYELURUH**.
> 
> Peneliti dan tim riset wajib membedakan secara tegas tiga domain validasi berikut:
> 1. **Verifikasi Teknis Paket (*Technical Package Verification*)**:
>    - Membuktikan integritas biner berkas (SHA-256), kesetaraan stimulus 100%, ketiadaan kebocoran ground-truth label, prediksi model, confidence score, dan metadata EXIF.
>    - *Status*: **`PASS (VERIFIED 100%)`**.
> 2. **Kesiapan Metodologis (*Methodological Readiness*)**:
>    - Membuktikan protokol blinded review telah disusun secara independen, rubrik 4 kategori telah didefinisikan secara baku, dan alur adjudikasi telah tersedia.
>    - *Status*: **`READY (VERIFIED)`**.
> 3. **Persetujuan Etika Subjek Manusia di Lapangan (*Informed Consent & Human Ethics Clearance*)**:
>    - Meliputi persetujuan sukarela tertulis partisipan (*Informed Consent Form*), penjelasan hak partisipan untuk berhenti kapan saja, transparansi penggunaan data, perlindungan kerahasiaan identitas validator manusia, dan pemenuhan regulasi komite etik institusional terkait penelitian yang melibatkan partisipan manusia.
>    - *Status*: **Merupakan tanggung jawab operasional fasilitator/peneliti di lapangan saat pelaksanaan interaksi manusia secara langsung, dan tidak dapat digantikan oleh verifikasi berkas kode/data.**

---

## 8. DAFTAR RISIKO METODOLOGIS YANG BELUM TERSELESAIKAN (RESIDUAL RISKS)

Berikut adalah risiko-risiko inheren yang tidak dapat diselesaikan hanya melalui verifikasi paket statis, melainkan harus dikawal selama pelaksanaan evaluasi manusia:

1. **Variasi Dialek Regional yang Tidak Terduga**:
   - Perbedaan latar belakang kedaerahan antara Validator A dan Validator B dapat memicu persepsi berbeda terhadap gestur tertentu.
   - *Rencana Mitigasi*: Register Adjudikasi bersama Validator C (`VAL-C`) telah disiapkan untuk merekonsiliasi divergensi dialek.
2. **Keterbatasan Domain Foto Diam pada Gestur Temporal (J & Z)**:
   - Pengujian citra statis pada huruf dinamis secara inheren tidak mampu membuktikan kebenaran lintasan gerak temporal.
   - *Rencana Mitigasi*: Pilihan `AMBIGUOUS` dan `UNDETERMINABLE` telah distandarisasi, dan modul video/keypoint (M1/V1) direkomendasikan pada roadmap masa depan SignBridge.
3. **Generalisasi Statistik Terbatas pada 36 Sampel**:
   - 36 sampel purposif ditujukan secara khusus untuk diagnosis kegagalan model P1 dan batas ketahanan noise visual, sehingga metrik kesepakatan tidak boleh diartikan sebagai reliabilitas absolut untuk seluruh 4.462 citra dataset mentah.
4. **Integritas Firewall Data Uji Pasca-Evaluasi**:
   - Tim peneliti wajib memastikan bahwa umpan balik koreksi dari 19 sampel `TEST_SET_DIAGNOSTIC_ONLY` tidak disalahgunakan untuk pelatihan ulang model P2.

---

## 9. KESIMPULAN AKHIR (*FINAL VERDICT*)

Berdasarkan seluruh hasil inspeksi forensik biner, kesetaraan stimulus 100%, ketiadaan kebocoran label/model, dan pemenuhan tata kelola data:

# **`FINAL VERDICT: PASS (TECHNICAL & METHODOLOGICAL READINESS)`**

Kedua paket distribusi (`validator_A` dan `validator_B`) **telah terbukti 100% memenuhi kriteria integritas teknis dan kesiapan metodologis**. Paket ini siap dan aman untuk diserahkan secara manual oleh peneliti kepada Validator A dan Validator B, dengan tetap mewajibkan pelaksanaan *Informed Consent* dan etika riset lapangan sebelum sesi evaluasi dimulai.

---

## 10. REKOMENDASI TINDAKAN BERIKUTNYA

1. **Pemberian Persetujuan Etis (*Informed Consent*)**:
   - Sebelum paket dibuka, peneliti wajib memberikan penjelasan hak validator dan mendapatkan persetujuan tertulis (*Informed Consent*).
2. **Penyerahan Manual oleh Peneliti**:
   - Salin isi folder [`docs/validation_p2/phase_2c/distribution/validator_A/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_A/) dan serahkan secara privat kepada Validator A.
   - Salin isi folder [`docs/validation_p2/phase_2c/distribution/validator_B/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/distribution/validator_B/) dan serahkan secara privat kepada Validator B.
3. **Pendampingan Sesi Evaluasi Tanpa Intervensi**:
   - Fasilitator mendampingi sesi dengan mematuhi protokol: dilarang memberikan petunjuk lisan atau isyarat mengenai jawaban yang diharapkan.
4. **Penyimpanan Respons Asli Segera (*Raw Immutable Storage*)**:
   - Saat file CSV respons diterima kembali, langsung hitung hash SHA-256 dan arsipkan ke `docs/validation_p2/phase_2c/raw_responses/`.
5. **Eksekusi Analisis Otomatis**:
   - Jalankan `python scripts/validation_p2/calculate_inter_rater_agreement.py` untuk memperoleh metrik kesepakatan reliabilitas inter-rater (Kappa, observed agreement, dan conditional correct letter agreement) serta mengekstrak kasus divergensi ke register adjudikasi.
