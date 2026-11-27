# Tasks — Rombak SignBridge-XMF

## Selesai (branch rombak/xmf-crossmodal-fusion)
- [x] 1. Kode pipeline `signbridge/xmf/` (ingest, audio_bank, preprocess, model, train, evaluate, export)
- [x] 2. Runtime web `web/js/xmf.js` + perbaikan syntax error `web/js/app.js`
- [x] 3. Tes Python & JS (paritas), uji asap data sintetis, dokumen + diagram + video ilustrasi

## Fase cicil — sambil menunggu upload citra
- [x] 4. Setup Mac: `bash ~/Downloads/setup_mac.sh` (atau `bash scripts/setup_mac.sh`) (repo, branch, .venv, folder data, symlink Drive)
- [x] 5. Ingest awal: `python -m signbridge.xmf.ingest` → cek `data/xmf/ingest/ingest_report.json`
- [ ] 6. Rekam suara relawan ke `data/raw/audio/gloss/<KONSEP>/<nama>_<n>.wav` (4 orang × 32 kata × 5)
- [ ] 7. Bank audio: `python -m signbridge.xmf.audio_bank --task gloss --tts edge,gtts`
- [ ] 8. Preprocess video (klip tanpa citra → video_fallback): `python -m signbridge.xmf.preprocess --task gloss --workers 4`
- [ ] 9. Uji coba training singkat: `python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol sd --epochs 3`

## Masukan Dosen (presentasi 27 Nov) — studi perbandingan model
- [x] 13. Fusion bisa dipilih: early, weighted, gated (GMU), late, refusion, attention (`signbridge/xmf/fusion.py`)
- [x] 14. Encoder bisa dipilih: video transformer/bigru/tcn · citra mobilenetv3/shufflenetv2/efficientnet_b0/resnet18 ·
       audio cnn_transformer/conformer/resnet · teks transformer/bilstm/textcnn (`signbridge/xmf/encoders.py`)
- [x] 15. Runner perbandingan `python -m signbridge.xmf.compare` (fase A fusion, fase B encoder) + tabel hasil
- [ ] 16. Jalankan `compare --phase all --protocol sd` lalu `--protocol si` di GPU (Colab) → isi docs/XMF_COMPARISON.md
- [ ] 17. Model deploy = varian terbaik (VI macro-F1 SI) → `train --protocol final --set ...` → export
- [ ] 18. Konfirmasi ke Pak Nadhif istilah "white fusion" dan "fusion retrieval" (lihat catatan di docs/XMF_COMPARISON.md)

## Setelah citra lengkap
- [ ] 10. Ulang sync → ingest → `preprocess --refresh-citra`
- [ ] 11. Training penuh SD, SI, final (+ alfabet)
- [ ] 12. Export ONNX → uji langsung di browser → laporkan metrik V+I (SD & SI) ke Dosen
