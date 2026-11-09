# Rencana Akuisisi & Preprocessing Dataset Multimodal SignBridge (`docs/DATASET_ACQUISITION_PLAN.md`)

**Proyek**: SignBridge ASEAN (BISINDO $\leftrightarrow$ FSL)  
**Working Directory**: `C:\Users\PC\Downloads\Semester 5\ML`  
**Branch**: `feature/dataset-acquisition`  
**Status**: Tahap 1 (Modality Text) Selesai; Menunggu Persetujuan untuk Tahap 2–5

---

## 1. Perbandingan Target Penuh Modul vs Profil A (Download Bertahap)

Sesuai koreksi wajib terhadap persyaratan modul asli **SignBridge**, berikut adalah transparansi penuh antara **Target Penuh Modul** dan **Cakupan Profil A (Download Bertahap)**:

| Modalitas & Dataset Wajib | Target Penuh Modul SignBridge | Cakupan pada Profil A (Bertahap) | Selisih / Kekurangan terhadap Target Modul | Status Pemenuhan Modul |
| :--- | :--- | :--- | :--- | :--- |
| **Video — WL-BISINDO** | $\approx 1.600$ video, $32$ gloss | Mengunduh penuh $\approx 1.600$ video ($32$ gloss) | Tidak ada selisih jika dataset Kaggle terunduh penuh | **BELUM DIUNDUH** (Menunggu Tahap 4; butuh kredensial Kaggle) |
| **Video — WLASL-300** | $\approx 4.000 - 5.000$ video ($5.118$ entri manifest), $300$ gloss | Jika diunduh terbatas untuk menghemat kuota ($\approx 1,5 - 2,0\text{ GB}$), hanya mencakup sebagian dari 300 gloss | Kurang $\approx 2.500 - 3.000$ video dibanding target penuh WLASL-300 ($\approx 4,5\text{ GB}$) | **SUBSET EKSPERIMEN** pada Profil A (Belum memenuhi target penuh WLASL-300) |
| **Video — FSL-105** | $2.130$ video, $105$ kelas FSL (eksperimen BISINDO–FSL) | Profil A hanya mengunduh/mengekstrak subset konsep yang beririsan ($32$ konsep $\approx 640$ video) atau arsip penuh jika diizinkan ($\approx 3,8\text{ GB}$) | Jika hanya subset 32 kelas yang diambil, kurang $73$ kelas ($\approx 1.490$ video) dari total 105 kelas FSL-105 | **SUBSET EKSPERIMEN** jika dipangkas; wajib unduh arsip penuh Mendeley (`doi:10.17632/48y2y99mb9.1`) untuk pemenuhan penuh |
| **Video — SignBridge-Kelas** | Minimal **$3.000$ data gabungan**, termasuk rekaman tambahan **$3\text{ signer} \times 32\text{ gloss} \times 10\text{ take} = 960\text{ contoh}$** ($\approx 2,6\text{ dtk}$) | $0$ rekaman manusia baru yang dapat diunduh dari internet | Kurang **$960$ rekaman video manusia nyata** (dan total gabungan belum mencapai $\ge 3.000$ sampel) | **`NOT AVAILABLE`** (Wajib perekaman fisik oleh 3 signer manusia; dilarang diganti data sintetis) |
| **Image — BISINDO Alphabet Image Data** | Kelas `A–Z` ($26$ kelas) dari **Mendeley Data** (`doi:10.17632/ywnjpbcz8m.1`, CC BY 4.0) | Mengunduh dataset asli penuh dari Mendeley Data ($\approx 350 - 750\text{ MB}$) | Tidak ada selisih (seluruh 26 kelas A–Z diunduh dari Mendeley) | **BELUM DIUNDUH** (Menunggu Tahap 3) |
| **Audio — Google FLEURS (`id_id`)** | Konfigurasi `id_id` (`google/fleurs`, CC BY 4.0) | Profil A mengunduh split evaluasi/dev/test + subset train `id_id` (atau penuh $\approx 1,3\text{ GB}$) | Jika hanya subset yang diunduh pada Profil A, belum mencakup seluruh split train `id_id` ($\approx 2.800$ klip) | **BELUM DIUNDUH** (Menunggu Tahap 2) |
| **Audio — Rekaman Kalimat Kelas SignBridge** | Rekaman suara nyata untuk kalimat ruang kelas (`data/audio/metadata.csv`, 60 kalimat) | Metadata teks (`metadata.csv`) sudah ada, tetapi berkas suara `.wav` asli **belum ada** | Kurang **$60$ berkas rekaman suara `.wav` nyata** (FLEURS bukan pengganti rekaman kelas, dan dilarang menggunakan gelombang sinus sintetis) | **`NOT AVAILABLE`** (Membutuhkan perekaman suara nyata; metadata CSV bukan berkas audio) |
| **Audio — FLEURS (`fil_ph`)** *(Opsional)* | Tambahan eksperimen FSL (tidak menggantikan `id_id`) | Opsional setelah `id_id` selesai | Hanya pelengkap eksperimen lintas negara | **OPSIONAL / TAMBAHAN** |
| **Text — Tatoeba Indonesian (`ind`)** | Korpus kalimat Bahasa Indonesia dari Tatoeba.org (CC BY 2.0 FR) | Diunduh penuh dari sumber resmi `downloads.tatoeba.org` | Tidak ada selisih untuk kalimat monolingual (`28.418` kalimat); namun Tatoeba **bukan** pasangan `gloss-to-sentence` | **TERPENUHI (SUDAH DIUNDUH)** di `data/text/tatoeba/ind_sentences.tsv` (**28.418 kalimat**) |
| **Text — Kalimat Kelas & TSV (`train`, `val`, `test_manual`)** | Pertahankan `kelas_sentences.txt` (200), `train.tsv` (170), `val.tsv` (30), `test_manual.tsv` (105) | Seluruh berkas asli dipertahankan 100% utuh di repository | Tidak ada perubahan | **TERPENUHI (TERSEDIA DI REPO)** |

---

## 2. Urutan Eksekusi Bertahap & Gate Persetujuan

### Tahap 1 — Modality TEXT (**SELESAI**)
1. **Verifikasi Sumber Resmi**:
   - URL Resmi: `https://downloads.tatoeba.org/exports/per_language/ind/ind_sentences.tsv.bz2`
   - Lisensi: Creative Commons Attribution 2.0 France (CC BY 2.0 FR)
2. **Hasil Eksekusi**:
   - Berkas terkompresi disimpan di `data/text/tatoeba/ind_sentences.tsv.bz2` (`330.738 byte`).
   - Berkas hasil ekstraksi disimpan di `data/text/tatoeba/ind_sentences.tsv` (`1.389.405 byte`, berisi **28.418 kalimat Bahasa Indonesia** asli).
   - Berkas `data/text/kelas_sentences.txt` (`200` kalimat), `data/text/train.tsv` (`170` pasangan), `data/text/val.tsv` (`30` pasangan), dan `data/text/test_manual.tsv` (`105` pasangan) **tetap utuh 100% tanpa modifikasi**.
   - Catatan Keaslian: `ind_sentences.tsv` adalah korpus kalimat Bahasa Indonesia murni (`id_kalimat`, `ind`, `kalimat`) dan **tidak** diklaim sebagai pasangan `gloss-to-sentence`.

---

### Tahap 2 — Modality AUDIO (**MENUNGGU PERSETUJUAN**)
- **Target**:
  1. Mengunduh **Google FLEURS (`id_id`)** resmi dari Hugging Face (`google/fleurs`, lisensi CC BY 4.0).
  2. Mencatat status **Rekaman Suara Kelas SignBridge** (`data/audio/wavs/id_001.wav`..`id_060.wav`) sebagai **`NOT AVAILABLE`** sampai ada rekaman suara nyata (tidak menggunakan FLEURS sebagai pengganti rekaman kelas dan tidak membuat gelombang sinus sintetis).
  3. (`fil_ph` hanya diunduh jika disetujui sebagai tambahan eksperimen FSL setelah `id_id`).

---

### Tahap 3 — Modality IMAGE (**MENUNGGU PERSETUJUAN**)
- **Target**:
  1. Mengunduh **BISINDO Indonesian Sign Language: Alphabet Image Data** dari sumber resmi **Mendeley Data** (`doi:10.17632/ywnjpbcz8m.1`, lisensi CC BY 4.0) yang mencakup 26 kelas abjad `A–Z`.
  2. Menjalankan pemotongan kotak tangan persegi `+25%` ($224 \times 224$) hanya pada citra nyata yang berhasil diunduh (tanpa citra dummy acak).

---

### Tahap 4 & 5 — Modality VIDEO (**MENUNGGU PERSETUJUAN**)
- **Target**:
  1. **WL-BISINDO** ($\approx 1.600$ video, $32$ gloss) dari Kaggle (`glennleonali/wl-bisindo`) — memerlukan konfigurasi kredensial Kaggle API (`~/.kaggle/kaggle.json`), jika kredensial belum tersedia maka berstatus **`BLOCKED`**.
  2. **FSL-105** ($2.130$ video, $105$ kelas) dari Mendeley Data (`doi:10.17632/48y2y99mb9.1`, CC BY 4.0).
  3. **WLASL-300** ($\approx 4.000 - 5.000$ video, $300$ gloss) dari manifest resmi `dxli94/WLASL` / mirror Kaggle. Apabila hanya subset yang diunduh pada Profil A, wajib diberi label **Subset Eksperimen**.
  4. **SignBridge-Kelas (Rekaman Tambahan 960 Klip: 3 signer $\times$ 32 gloss $\times$ 10 take, $\approx 2,6\text{ dtk}$ menuju total $\ge 3.000$ data)**: Berstatus **`NOT AVAILABLE`** hingga perekaman fisik dilakukan oleh tim.
