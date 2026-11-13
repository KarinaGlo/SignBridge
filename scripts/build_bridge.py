"""
scripts/build_bridge.py — Modul 05 Langkah 16 (PDF Hal. 25):
Memvalidasi tabel konsep lintas negara data/bridge/concepts.csv (32 konsep ID <-> FIL <-> EN)
dan menguji keandalan BridgeModule 3 Lapis (L1 Concept Lookup, L2 Neural Translation, L3 Animation).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.bridge import BridgeModule


def main() -> None:
    parser = argparse.ArgumentParser(description="Validasi Jembatan Komunikasi 3 Lapis ID <-> PH.")
    parser.add_argument("--concepts", type=str, default="data/bridge/concepts.csv")
    args = parser.parse_args()

    bridge = BridgeModule(concepts_csv=args.concepts)
    sample_id_to_fil = bridge.translate("Saya mau tanya guru tentang tugas buku", src="id", tgt="fil")
    sample_fil_to_id = bridge.translate("Kumusta guro salamat", src="fil", tgt="id")
    print(f"[build_bridge] Konsep dimuat: {len(bridge.concepts)} entri")
    print(f"  ID -> FIL: {sample_id_to_fil['translation']} (layer={sample_id_to_fil['layer_used']})")
    print(f"  FIL -> ID: {sample_fil_to_id['translation']} (layer={sample_fil_to_id['layer_used']})")


if __name__ == "__main__":
    main()

