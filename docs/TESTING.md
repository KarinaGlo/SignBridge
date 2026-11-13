# Dokumentasi Pengujian & Evaluasi (`docs/TESTING.md`)

## 1. Perbandingan Hasil Pengujian Sebelum & Sesudah Implementasi PostgreSQL

| Suite Pengujian | Perintah Eksekusi | Sebelum Integrasi PostgreSQL | Sesudah Integrasi PostgreSQL | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Core Multimodal & Contract Suite** | `pytest tests/test_signbridge_suite.py -v` | `12/12 PASSED` | **`12/12 PASSED`** | **PASSED** |
| **Database Operational & Fallback Suite** | `pytest tests/test_database_integration.py -v` | Belum tersedia | **`4/4 PASSED`** | **PASSED** |
| **JavaScript Parity & Hand-Crop Suite** | `node --test tests/js/parity.test.mjs tests/js/handcrop.test.mjs` | `7/7 PASSED` | **`7/7 PASSED`** | **PASSED** |
| **Legacy Unit & Property Suite** | `pytest tests/ -q` | `327/327 PASSED` | **`327/327 PASSED`** | **PASSED** |
| **Total Pengujian Otomatis** | Python + Node.js | `346 PASSED` | **`350 PASSED` (0 FAILED)** | **PASSED** |

---

## 2. Rincian 16 Pengujian Utama (`test_signbridge_suite.py` + `test_database_integration.py`)

1. `test_contract_1_constants_and_holistic_selection`: Verifikasi dimensi 86 titik (`9 pose + 21 tangan kiri + 21 tangan kanan + 35 wajah`), 32 gloss BISINDO, dan 26 label abjad `A`–`Z`. (**PASSED**)
2. `test_graph_connected`: Verifikasi konektivitas matriks ketetanggaan 3 partisi ST-GCN `[3, 86, 86]`. (**PASSED**)
3. `test_contract_3_features_pipeline`: Verifikasi `trim_inactive`, `normalize_pose`, `resample_frames(64)`, dan `extract_and_normalize` menghasilkan `[1, 64, 86, 3]` `float32`. (**PASSED**)
4. `test_augmentation_and_mirror_swap`: Verifikasi pembalikan simetri tangan kiri $\leftrightarrow$ kanan saat augmentasi cermin. (**PASSED**)
5. `test_dataset_sd_si_and_phonology`: Verifikasi protokol *Signer-Dependent* (`sd`) dan *Signer-Independent / LOSO* (`si`) bebas kebocoran penutur (*zero signer leakage*). (**PASSED**)
6. `test_video_models_m0_m1_m2_m3_m4_m5`: Verifikasi *forward pass*, *multitask phonology loss*, dan *Knowledge Distillation* pada ke-6 arsitektur video (`M0`–`M5`). (**PASSED**)
7. `test_contract_2_onnx_export_and_parity`: Verifikasi ekspor `web/model/student.onnx` & `student_int8.onnx` (`max_diff < 1e-4`, ukuran `1.663 MB < 10.0 MB`). (**PASSED**)
8. `test_contract_4_and_5_handcrop_and_image_models`: Verifikasi pemotongan tangan $+25\%$ margin $224 \times 224$, model `I1` (`mobilenetv3_small`), `I2` (`efficientnet_b0`), `I3` (`mobilevit_xs`), dan ekspor `fingerspell.onnx`. (**PASSED**)
9. `test_audio_modality_metrics`: Verifikasi perhitungan `WER`, `CER`, dan `RTF` pada modul Whisper ASR. (**PASSED**)
10. `test_text_modality_and_disjoint_manual_test`: Verifikasi `B0`, `T1` (`GRUAttentionSeq2Seq`), `BLEU`, `chrF`, dan pembuktian 0% tumpang-tindih antara 105 kalimat `data/text/test_manual.tsv` dan 170 kalimat `data/text/train.tsv`. (**PASSED**)
11. `test_bridge_three_layers_and_fallback`: Verifikasi Jembatan 3 Lapis Indonesia $\leftrightarrow$ Filipina (`L1 Concept`, `L2 Neural MT`, `L3 Reference Animation`, dan *fallback* saat L2 gagal). (**PASSED**)
12. `test_contract_6_fastapi_server_endpoints`: Verifikasi `/health`, `/predict`, `/asr` (termasuk `HTTP 413`), `/sentence`, `/translate`, dan *rate limiter* (`HTTP 429`). (**PASSED**)
13. `test_db_schema_seeding_and_status`: Verifikasi pembuatan 5 tabel database, *seeding* 58 konsep (`32` kata + `26` abjad), 20 versi model (`M0`–`M5`, `I1`–`I3`, `A1`–`A3`, `B0/T1`–`T3`, `X1`–`X4`), dan 3 evaluasi terverifikasi. (**PASSED**)
14. `test_db_concepts_models_and_evaluations_endpoints`: Verifikasi filter kategori pada `/db/concepts`, filter modalitas pada `/db/models`, dan CRUD `/db/evaluations` untuk pencatatan LOSO Gloria. (**PASSED**)
15. `test_inference_logging_and_recordings_crud`: Verifikasi pencatatan *non-blocking* ke `inference_logs` dari `/predict`, `/asr`, `/sentence`, `/translate` serta CRUD `/db/recordings` (`SignBridge-Kelas`). (**PASSED**)
16. `test_database_failure_graceful_degradation`: Verifikasi ketika koneksi database mati (`simulate_failure = True`), seluruh endpoint inferensi utama tetap merespons `200 OK` tanpa *crash*. (**PASSED**)

---

## 3. Hasil Pengukuran Evaluasi Aktual di Database (`evaluation_runs`)
Seluruh angka di bawah ini diukur secara nyata dari artefak yang ada di repositori (bukan angka contoh/karangan):

| Kode Model | Jenis Evaluasi | Dataset Uji | Jumlah Uji | Metrik Aktual Terukur | Latensi Rata-rata |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`B0`** | `text_gloss_to_sentence` | `data/text/test_manual.tsv` | `105` kalimat manusia | `chrF = 57.50`, `BLEU = 3.21`, `WER = 0.6226` | `0.0459 ms / kalimat` |
| **`M5`** | `onnx_validation` | Kontrak 2 (`[1, 64, 86, 3] -> [1, 32]`) | `1` sesi ONNX | `max_diff = 2.53e-07 (< 1e-4)`, `size = 1.663 MB (< 10 MB)` | `9.412 ms / sekuens` |
| **`I1`** | `onnx_validation` | Kontrak 5 (`[1, 3, 224, 224] -> [1, 26]`) | `1` sesi ONNX | `max_diff < 1e-5`, `size = 1.013 MB` | `3.109 ms / citra` |

