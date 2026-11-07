"""
eval_translate.py — Evaluate Indonesia <-> Philippines Translation Models (MT0-MT3).

Usage (Bab 6.16 Langkah 16 & Bab 11.5):
  python -m signbridge.text.eval_translate --direction id-fil --limit 300
  python -m signbridge.text.eval_translate --direction fil-id --limit 300

Models compared:
  - MT0: Concept dictionary lookup (`data/bridge/concepts.csv`, offline L1)
  - MT1: facebook/m2m100_418M
  - MT2: facebook/nllb-200-distilled-600M (default server model)
  - MT3: facebook/nllb-200-1.3B
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from signbridge.bridge import BridgeModule
from signbridge.text.train_text import compute_bleu, compute_chrf


PARALLEL_CLASSROOM_ID_FIL: List[Tuple[str, str]] = [
    ("Selamat pagi teman.", "Magandang umaga kaibigan."),
    ("Terima kasih guru.", "Salamat guro."),
    ("Apakah kamu sudah makan?", "Kumain ka na ba?"),
    ("Saya belajar di rumah.", "Nag-aaral ako sa bahay."),
    ("Di mana keluarga kamu?", "Nasaan ang pamilya mo?"),
    ("Maaf saya datang sore.", "Paumanhin dumating ako nang hapon."),
    ("Ibu saya minum air.", "Umiinom ng tubig ang nanay ko."),
    ("Siapa nama teman baik kamu?", "Sino ang pangalan ng mabuting kaibigan mo?"),
    ("Kapan kita mulai belajar?", "Kailan tayo magsisimulang mag-aral?"),
    ("Bagaimana kabar keluarga hari ini?", "Kumusta ang pamilya ngayon?"),
]


def run_translation_eval(
    direction: str = "id-fil",
    limit: int = 300,
    out_dir: str | Path = "runs",
) -> Dict[str, Any]:
    direction = direction.lower().strip()
    if direction not in ("id-fil", "fil-id"):
        raise ValueError(f"direction must be 'id-fil' or 'fil-id', got {direction!r}")

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    bridge = BridgeModule()

    pairs = PARALLEL_CLASSROOM_ID_FIL[: max(1, min(limit, len(PARALLEL_CLASSROOM_ID_FIL)))]
    src_sents = [p[0] if direction == "id-fil" else p[1] for p in pairs]
    ref_sents = [p[1] if direction == "id-fil" else p[0] for p in pairs]
    src_lang = "id" if direction == "id-fil" else "fil"
    tgt_lang = "fil" if direction == "id-fil" else "id"

    models_spec = [
        ("MT0", "kamus_konsep", 0.0),
        ("MT1", "facebook/m2m100_418M", 418.0),
        ("MT2", "facebook/nllb-200-distilled-600M", 600.0),
        ("MT3", "facebook/nllb-200-1.3B", 1300.0),
    ]

    summary: Dict[str, Any] = {"direction": direction, "limit": limit, "models": {}}

    for mt_id, model_name, params_m in models_spec:
        t0 = time.perf_counter()
        hyps: List[str] = []
        for s in src_sents:
            if mt_id == "MT0":
                res = bridge.translate_l1_only(s, src_lang=src_lang, tgt_lang=tgt_lang)
                hyps.append(res["translation"])
            else:
                res = bridge.translate_text(s, src_lang=src_lang, tgt_lang=tgt_lang, model_tag=mt_id)
                hyps.append(res["translation"])
        latency_ms = ((time.perf_counter() - t0) / max(1, len(src_sents))) * 1000.0

        bleu = compute_bleu(ref_sents, hyps)
        chrf = compute_chrf(ref_sents, hyps)

        run_folder = out_root / f"translate_{mt_id.lower()}_{direction.replace('-', '_')}"
        run_folder.mkdir(parents=True, exist_ok=True)
        entry = {
            "id": mt_id,
            "name": run_folder.name,
            "modality": "translate",
            "model": model_name,
            "direction": direction,
            "bleu": round(bleu, 2),
            "chrf": round(chrf, 2),
            "latency_ms": round(latency_ms, 2),
            "param_millions": params_m,
        }
        with (run_folder / "result.json").open("w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        summary["models"][mt_id] = entry
        print(
            f"[eval_translate] {mt_id} ({direction}) | BLEU={bleu:.2f} | "
            f"chrF={chrf:.2f} | latency={latency_ms:.2f} ms"
        )

    return summary


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate ID <-> FIL Bridge Translation Models (MT0-MT3)")
    parser.add_argument("--direction", type=str, default="id-fil", choices=["id-fil", "fil-id"])
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--out", type=str, default="runs")
    args = parser.parse_args(argv)
    run_translation_eval(direction=args.direction, limit=args.limit, out_dir=args.out)


if __name__ == "__main__":
    main()

