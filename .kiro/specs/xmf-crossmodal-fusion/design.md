# Design — SignBridge-XMF

Dokumen lengkap: [`docs/XMF_PIPELINE.md`](../../../docs/XMF_PIPELINE.md) · Diagram: `docs/architecture/xmf_pipeline.png`,
`docs/architecture/xmf_model.png`.

| Tahap | Modul | Keluaran |
|---|---|---|
| 1 Source | `scripts/xmf_sync_drive.sh` / symlink Google Drive | `data/raw/wlbisindo_drive/` |
| 2 Ingestion | `signbridge/xmf/ingest.py`, `audio_bank.py` | `data/xmf/ingest/*.csv`, `data/xmf/bank/*.npz` |
| 3 Preprocessing | `signbridge/xmf/preprocess.py`, `ops.py` | `data/xmf/processed/<task>/*.npz` |
| 4 Modeling | `signbridge/xmf/model.py` | `SignBridgeXMF` |
| 5 Training | `signbridge/xmf/train.py`, `data.py`, `configs/xmf_*.yaml` | `outputs/xmf/<exp>/best.pt` |
| 6 Evaluation | `signbridge/xmf/evaluate.py` | metrics, ablation, confusion |
| 7 Export | `signbridge/xmf/export.py` | `web/model/xmf_<task>.onnx/.json` |
| 8 Deployment | `web/js/xmf.js`, `server/app.py`, Docker | aplikasi web |
