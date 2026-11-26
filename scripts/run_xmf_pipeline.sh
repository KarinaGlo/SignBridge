#!/usr/bin/env bash
# scripts/run_xmf_pipeline.sh — Pipeline SignBridge-XMF end-to-end di perangkat sendiri.
#   source -> ingestion -> preprocessing -> modeling/training -> evaluation -> export -> deployment
#
#   bash scripts/run_xmf_pipeline.sh            # semua tahap, tugas gloss + alfabet
#   STAGES="ingest preprocess" bash scripts/run_xmf_pipeline.sh
#   TASKS=gloss PROTOCOLS="sd si" bash scripts/run_xmf_pipeline.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-python}"
STAGES="${STAGES:-sync ingest bank preprocess train export serve}"
TASKS="${TASKS:-gloss alphabet}"
PROTOCOLS="${PROTOCOLS:-sd si}"          # protokol riset yang dilaporkan; model deploy selalu 'final'
WORKERS="${WORKERS:-4}"
TTS="${TTS:-edge,gtts,espeak}"
has() { [[ " $STAGES " == *" $1 "* ]]; }

has sync       && { bash scripts/xmf_sync_drive.sh || echo "[lewati] sinkronisasi Drive (pakai data yang sudah ada)"; }
has ingest     && $PY -m signbridge.xmf.ingest --drive-root data/raw/wlbisindo_drive
for T in $TASKS; do
  has bank       && $PY -m signbridge.xmf.audio_bank --task "$T" --tts "$TTS"
  has preprocess && $PY -m signbridge.xmf.preprocess --task "$T" --workers "$WORKERS" --refresh-citra
  if has train; then
    for P in $PROTOCOLS; do
      [[ "$T" == alphabet && "$P" == si ]] && continue        # alfabet tidak punya ID penanda
      $PY -m signbridge.xmf.train --config "configs/xmf_${T}.yaml" --protocol "$P"
    done
    $PY -m signbridge.xmf.train --config "configs/xmf_${T}.yaml" --protocol final
  fi
  has export && $PY -m signbridge.xmf.export --ckpt "outputs/xmf/XMF_${T}_final/best.pt" --out web/model
done
has serve && { echo "Buka http://localhost:7860 (Ctrl+C untuk berhenti)"; $PY -m uvicorn server.app:app --host 0.0.0.0 --port 7860; }
