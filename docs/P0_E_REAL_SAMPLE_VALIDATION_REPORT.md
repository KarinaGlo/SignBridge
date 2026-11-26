# P0-E — REAL SAMPLE VALIDATION REPORT
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

> [!CAUTION]
> **STATUS SAMPEL NYATA: `PENDING MANUAL USER RECORDING` (BELUM ADA SAMPEL NYATA)**
> Pada saat audit P0-E dijalankan (`2026-11-26`), **belum ada satu pun berkas ZIP rekaman nyata** di `data/raw/web_zips/` maupun di seluruh repositori `D:\SEMESTER 5\ML\Projek_1`. Sesuai aturan audit, tidak ada data palsu atau sintetis yang dibuat untuk menggantikan sampel nyata.

---

## 1. Catatan Perekaman Sampel Nyata (Tahap 2)

Seluruh metrik di bawah ini **belum terisi** karena menunggu eksekusi perekaman fisik oleh pengguna di browser:

| Parameter Observasi | Nilai Aktual | Status |
| :--- | :--- | :---: |
| Status webcam | *Belum diverifikasi di browser* | `MANUAL VERIFICATION REQUIRED` |
| Status mikrofon | *Belum diverifikasi di browser* | `MANUAL VERIFICATION REQUIRED` |
| `sample_id` | *Menunggu ZIP nyata* (`SB_<SIGNER_ID>_<GLOSS>_T<TAKE_ID>`) | `PENDING` |
| Target gloss (Dictionary B) | *Menunggu ZIP nyata* | `PENDING` |
| Jumlah frame (`num_frames`) | *Menunggu ZIP nyata* | `PENDING` |
| Jumlah keypoint valid | *Menunggu ZIP nyata* | `PENDING` |
| Timestamp setiap frame (`frame_records`) | *Menunggu ZIP nyata* | `PENDING` |
| Keberadaan hand crop (`*_hand.jpg`) | *Menunggu ZIP nyata* | `PENDING` |
| Status audio (`audio_status`, `*.wav`) | *Menunggu ZIP nyata* | `PENDING` |

---

## 2. Instruksi Langkah-demi-Langkah untuk Pengguna

Jalankan prosedur berikut untuk menghasilkan 1 sampel nyata P0-E:

1. Jalankan server lokal dari root proyek:
   ```powershell
   python -m http.server 8080 -d web
   ```
   Lalu buka `http://localhost:8080` di browser (Chrome/Edge).
2. Buka tab **Perekam Dataset**, klik **Nyalakan Kamera**, dan berikan izin **Kamera** serta **Mikrofon** saat diminta browser.
3. Masukkan **Signer ID** (mis. `S01`) yang telah menandatangani persetujuan.
4. Pada dropdown target (`#rec-target`), pilih satu **gloss** yang valid dari Dictionary B (mis. `AIR` atau `BELAJAR`).
5. Klik **Saran Konteks** (atau ketik kalimat konteks kelas yang benar-benar akan diucapkan tanpa menulis kata target).
6. Klik **Rekam Klip (2,5 dtk)**: peragakan isyarat BISINDO sambil mengucapkan kalimat konteks. Pastikan status UI menampilkan jumlah frame `>= 8` dan durasi audio `~2.5 dtk` tanpa peringatan `audio = missing`.
7. Klik **Unduh Paket ZIP** dan simpan file `SignBridge_<SIGNER>_<TIMESTAMP>.zip` ke folder:
   `D:\SEMESTER 5\ML\Projek_1\data\raw\web_zips\`
8. Setelah ZIP tersimpan di `data/raw/web_zips/`, lanjutkan validasi ZIP, `build_multimodal_manifest.py`, dan `MultimodalSampleLoader`.
