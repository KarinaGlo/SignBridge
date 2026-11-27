# Studi Perbandingan Model SignBridge-XMF

Disusun dari masukan Dosen pada presentasi progres 27 November 2026. Masukannya: *"kok modelnya cuma satu?"*, tambah gated / white / re-fusion, coba Conformer dan ResNet untuk audio, coba ShuffleNet untuk citra, dan jelaskan model teks.

SignBridge-XMF sekarang adalah **satu kerangka model yang komponennya bisa ditukar**. Ada 6 strategi fusion dan 3–4 encoder per modalitas. Semua varian:
- memakai hasil preprocessing yang sama (`data/xmf/processed/*.npz`), jadi preprocessing tidak perlu diulang,
- memakai input dan output ONNX yang sama, jadi aplikasi web tidak perlu diubah,
- dibandingkan dengan protokol yang sama (split SD dan SI, metrik yang sama).

## 1. Komponen yang dibandingkan

### Fusion (`signbridge/xmf/fusion.py`)

| Kunci | Nama | Cara kerja | Jenis |
|---|---|---|---|
| `early` | Early fusion | Ringkasan tiap modalitas digabung (concat) + indikator ketersediaan, lalu MLP | feature-level |
| `weighted` | Weighted-sum fusion | Satu bobot skalar per modalitas yang dipelajari. Bobotnya sama untuk semua input | feature-level |
| `gated` | Gated Multimodal Unit (Arevalo dkk., 2017) | Gerbang per dimensi yang bergantung pada input: z = softmax(W[u₁..u₄]), h = Σ z_m ⊙ tanh(W_m u_m) | feature-level, adaptif |
| `late` | Late fusion | Classifier terpisah per modalitas. Skornya digabung dengan bobot yang dipelajari | decision-level |
| `refusion` | Re-fusion / progressive fusion (mirip Shankar dkk., 2022) | Hasil GMU diumpankan balik ke representasi tiap modalitas, lalu di-fusion ulang (2 putaran) | iteratif |
| `attention` | **Cross-Modal Attention Fusion Transformer** (default) | [CLS] + semua token masuk Transformer bersama. Token satu modalitas meng-attend token modalitas lain, lalu gating | token-level, adaptif |

### Encoder (`signbridge/xmf/encoders.py`)

| Modalitas | Pilihan | Keterangan |
|---|---|---|
| Video (keypoint MediaPipe) | `transformer` (default), `bigru`, `tcn` | Front-end yang sama untuk semua: embedding per bagian tubuh (badan, 2 tangan, wajah) + kecepatan |
| Citra | `mobilenetv3` (default), `shufflenetv2`, `efficientnet_b0`, `resnet18` | Semua pra-latih ImageNet, 1 token per frame, lalu Transformer temporal |
| Audio | `cnn_transformer` (default), `conformer`, `resnet` | Log-mel 64 bin dihitung **di dalam graf model**. Conformer = Gulati dkk. (2020). ResNet = blok residual 2D pada spektrogram |
| Teks | `transformer` (default), `bilstm`, `textcnn` | Semuanya **tingkat karakter**. TextCNN = Kim (2014) |

Contoh ukuran dari uji asap. Ukuran ONNX dan latensi diukur dengan ONNX Runtime CPU di sandbox, jadi angkanya hanya perkiraan:

| Varian | Parameter | ONNX |
|---|---|---|
| default (attention) | 2,1 jt | 8–9 MB |
| citra shufflenetv2 | 2,5 jt | 10–12 MB |
| citra efficientnet_b0 | 5,3 jt | 21–24 MB |
| citra resnet18 | 12,4 jt | 49–52 MB (terlalu berat untuk browser HP) |
| audio conformer | 2,7 jt | 11–13 MB |
| audio resnet | 2,5 jt | 10–13 MB |

## 2. Rancangan eksperimen

Supaya perbandingannya adil, **setiap run hanya mengubah satu faktor**. Faktor lainnya tetap: data, split, augmentasi, epoch maksimum, seed, dan sampling subset modalitas.

- **Fase A – fusion:** 6 run, encoder default.
- **Fase B – encoder:** fusion terbaik dari fase A, lalu ganti satu encoder per run (10 run).
  Setiap encoder dinilai pada subset modalitasnya sendiri:

  | Encoder | Dinilai dengan |
  |---|---|
  | video | V-F1 |
  | citra | I-F1 |
  | audio | A-F1 (ucapan → konsep) |
  | teks | T-F1 (teks → konsep) |

- **Metrik utama keseluruhan:** macro-F1 subset **VI** (kamera saja). Ini kondisi nyata pengguna Tuli di browser.
- **Protokol:** SD (penanda yang sama) dan **SI** (penanda 4 tidak pernah dilihat saat training). SI lebih jujur untuk klaim generalisasi.
- **Laporan otomatis:** akurasi, macro-F1, top-5, jumlah parameter, ukuran ONNX, latensi ONNX Runtime 1 thread, dan bobot kontribusi modalitas.
- **Model deploy:** varian dengan VI macro-F1 SI terbaik yang tetap muat di browser (ONNX ≲ 25 MB, latensi ≲ 300 ms).

```bash
python -m signbridge.xmf.compare --task gloss --phase all --dry-run          # lihat rencana
python -m signbridge.xmf.compare --task gloss --phase all --protocol sd      # jalankan (bisa dilanjutkan)
python -m signbridge.xmf.compare --task gloss --phase all --protocol si
python -m signbridge.xmf.compare --task gloss --report                       # tabel -> outputs/xmf/compare/
# satu varian saja:
python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol sd \
       --set model.fusion=gated --set model.encoders.audio=conformer
```

**Perkiraan biaya:** 16 run per protokol. Sebaiknya jalankan di GPU (Colab). Untuk perbandingan awal, `--epochs 30` sudah cukup. Run yang sudah selesai otomatis dilewati, jadi kalau Colab terputus, cukup jalankan perintah yang sama lagi.

## 3. Hasil

*(Diisi dari `outputs/xmf/compare/gloss_sd/results.md` dan `gloss_si/results.md` setelah training pada data asli.)*

## 4. Catatan istilah yang perlu dikonfirmasi ke Dosen

- **"White fusion"**: tidak ada istilah baku dengan nama ini. Kemungkinan maksudnya **weighted fusion** (`weighted`) atau **late fusion** (`late`). Keduanya sudah dimasukkan.
- **"Refusion"**: diterapkan sebagai *re-fusion / progressive fusion* (`refusion`), yaitu hasil fusion diumpankan balik lalu di-fusion ulang.
- **"Fusion retrieval"** (disebut sebagai alternatif encoder citra): belum jelas. Mungkin yang dimaksud backbone ringan lain (EfficientNet, GhostNet, RegNet), atau pendekatan *retrieval*, yaitu mencocokkan embedding dengan galeri prototipe. Model ini sebenarnya sudah punya **head prototipe bersama** (cosine similarity ke prototipe tiap konsep), dan ini bisa dijelaskan sebagai komponen retrieval.

## 5. Kenapa pilihan default-nya begitu (bahan menjawab pertanyaan)

- **Citra – MobileNetV3-Small.** Alasannya bukan sekadar "ringan". Model ini dirancang dengan NAS khusus untuk CPU ponsel, akurasi ImageNet-nya (67,4%) termasuk yang terbaik di kelas sekitar 60 MFLOPs, dan dukungan operatornya di ONNX Runtime Web lengkap. ShuffleNetV2, EfficientNet-B0, dan ResNet-18 sekarang ikut dibandingkan secara terukur. Pilihan akhir mengikuti hasil (F1, ukuran, latensi), bukan asumsi.
- **Audio – log-mel + CNN-Transformer.** Di dalam model, gelombang 16 kHz diubah jadi spektrogram log-mel 64 bin (STFT sebagai Conv1d, jadi ikut ter-ekspor ke ONNX). Lalu Conv1d ×2 untuk subsampling dan pola lokal, dan Transformer untuk konteks waktu. Ini sebenarnya sudah mirip Conformer versi sederhana. Conformer penuh dan ResNet-2D sekarang dibandingkan langsung.
- **Teks – Transformer tingkat karakter.** Kosakatanya kecil (32 kata + 26 huruf) dan input guru bisa salah ketik atau tanpa spasi ("terimakasih"). Model tingkat karakter tahan terhadap hal ini, tidak butuh tokenizer atau kamus, dan kecil (±0,15 jt parameter), jadi bisa jalan di browser. BiLSTM dan TextCNN sekarang ikut dibandingkan. IndoBERT (±110 jt parameter, sekitar 440 MB) terlalu besar untuk browser dan berlebihan untuk 58 konsep. Kalau perlu, bisa diuji sebagai pembanding di server, bukan untuk deploy.
- **Kenapa fusion, bukan model per modalitas?** Satu model yang menerima 4 modalitas sekaligus belajar **ruang konsep bersama**. Isyarat, ucapan, dan teks "TERIMA KASIH" dipetakan ke titik yang sama. Inilah dasar komunikasi dua arah: Tuli→Dengar lewat video+citra, Dengar→Tuli lewat audio/teks.
- **Kejujuran metrik.** Pasangan audio dan teks dibuat di tingkat konsep (rekaman relawan + TTS), bukan direkam bersamaan dengan video isyarat. Karena itu A/T dilaporkan sebagai akurasi pengenalan konsep dari ucapan/teks, **bukan** akurasi pengenalan isyarat.
