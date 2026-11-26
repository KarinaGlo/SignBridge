# Tasks — Rombak SignBridge-XMF

## Selesai (branch rombak/xmf-crossmodal-fusion)
- [x] 1. Kode pipeline `signbridge/xmf/` (ingest, audio_bank, preprocess, model, train, evaluate, export)
- [x] 2. Runtime web `web/js/xmf.js` + perbaikan syntax error `web/js/app.js`
- [x] 3. Tes Python & JS (paritas), uji asap data sintetis, dokumen + diagram + video ilustrasi

## Fase cicil — sambil menunggu upload citra
- [ ] 4. Setup Mac: `bash ~/Downloads/setup_mac.sh` (atau `bash scripts/setup_mac.sh`) (repo, branch, .venv, folder data, symlink Drive)
- [ ] 5. Ingest awal: `python -m signbridge.xmf.ingest` → cek `data/xmf/ingest/ingest_report.json`
- [ ] 6. Rekam suara relawan ke `data/raw/audio/gloss/<KONSEP>/<nama>_<n>.wav` (4 orang × 32 kata × 5)
- [ ] 7. Bank audio: `python -m signbridge.xmf.audio_bank --task gloss --tts edge,gtts`
- [ ] 8. Preprocess video (klip tanpa citra → video_fallback): `python -m signbridge.xmf.preprocess --task gloss --workers 4`
- [ ] 9. Uji coba training singkat: `python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol sd --epochs 3`

## Setelah citra lengkap
- [ ] 10. Ulang sync → ingest → `preprocess --refresh-citra`
- [ ] 11. Training penuh SD, SI, final (+ alfabet)
- [ ] 12. Export ONNX → uji langsung di browser → laporkan metrik V+I (SD & SI) ke Dosen
