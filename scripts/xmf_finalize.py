"""
scripts/xmf_finalize.py — langkah terakhir tanpa Colab: run kombinasi SI -> pilih model -> training final -> ekspor ONNX.

Jalan di GPU NVIDIA, GPU Apple (MPS, MacBook M-series) atau CPU (otomatis). Run yang sudah selesai dilewati.

    python scripts/xmf_finalize.py                 # semua langkah
    python scripts/xmf_finalize.py --skip-combo    # langsung training final dari hasil yang ada
    python scripts/xmf_finalize.py --dry-run       # tampilkan rencana saja

Folder outputs/ sebaiknya menunjuk ke folder Drive yang sama dengan Colab (lihat docs/XMF_COMPARISON.md),
supaya hasil 16 varian SI terbaca dan tidak diulang.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

COMBO = {"fusion": "late", "encoders": {"pose": "tcn", "image": "efficientnet_b0", "audio": "conformer",
                                        "text": "transformer"}}
CANDIDATES_SI = [  # kandidat model gloss (dibandingkan pada VI macro-F1 protokol SI)
    COMBO,
    {"fusion": "late", "encoders": {"pose": "transformer", "image": "efficientnet_b0", "audio": "cnn_transformer",
                                    "text": "transformer"}},
    {"fusion": "late", "encoders": {"pose": "transformer", "image": "mobilenetv3", "audio": "conformer",
                                    "text": "transformer"}},
    {"fusion": "late", "encoders": {"pose": "tcn", "image": "mobilenetv3", "audio": "cnn_transformer",
                                    "text": "transformer"}},
]
ALPHABET_FINAL = {"fusion": "refusion"}   # terbaik di perbandingan fusion alfabet (82,1%)
MAX_ONNX_MB = 25


def sets_of(v):
    s = [f"model.fusion={v['fusion']}"]
    s += [f"model.encoders.{k}={x}" for k, x in v.get("encoders", {}).items()]
    return s


def main():
    from signbridge.xmf.compare import run_dir
    from signbridge.xmf.evaluate import evaluate_checkpoint
    from signbridge.xmf.export import export
    from signbridge.xmf.train import auto_device, load_config, train, variant_tag

    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-combo", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--device", default=None)
    a = ap.parse_args()
    dev = a.device or auto_device()
    print(f"[finalize] device = {dev}")

    cfg = load_config(ROOT / "configs/xmf_gloss.yaml")
    combo_dir = run_dir(cfg, COMBO, "si")
    if not a.skip_combo and not (combo_dir / "evaluation_metrics.json").exists():
        print(f"[finalize] 1/4 run kombinasi SI -> {combo_dir.name}")
        if not a.dry_run:
            c = load_config(ROOT / "configs/xmf_gloss.yaml", sets=sets_of(COMBO))
            ckpt, _ = train(c, "si", combo_dir, dev, 30)
            evaluate_checkpoint(ckpt, combo_dir, dev)
    else:
        print("[finalize] 1/4 run kombinasi SI: sudah ada / dilewati")

    print("[finalize] 2/4 pilih model gloss (VI macro-F1, protokol SI):")
    best, best_f1 = None, -1.0
    for v in CANDIDATES_SI:
        f = run_dir(cfg, v, "si") / "evaluation_metrics.json"
        if not f.exists():
            print(f"   - {variant_tag(v):55s} belum ada hasil")
            continue
        f1 = json.loads(f.read_text())["primary"]["macro_f1"]
        print(f"   - {variant_tag(v):55s} F1 = {f1:.4f}")
        if f1 > best_f1:
            best, best_f1 = v, f1
    if best is None:
        raise SystemExit("Belum ada hasil SI kandidat. Pastikan outputs/ menunjuk ke folder Drive hasil Colab.")
    print(f"[finalize] model gloss terpilih: {variant_tag(best)} (F1 SI {best_f1:.4f})")

    jobs = [("gloss", best, ROOT / "outputs/xmf/FINAL_gloss"), ("alphabet", ALPHABET_FINAL, ROOT / "outputs/xmf/FINAL_alphabet")]
    for i, (task, v, out) in enumerate(jobs, 3):
        print(f"[finalize] {i}/4 training final {task}: {variant_tag(v)} -> {out}")
        if a.dry_run:
            continue
        if not (out / "best.pt").exists():
            c = load_config(ROOT / f"configs/xmf_{task}.yaml", sets=sets_of(v))
            train(c, "final", out, dev, None)
        onnx = export(out / "best.pt", ROOT / "web/model")
        mb = onnx.stat().st_size / 1e6
        print(f"[finalize]    ONNX {onnx.name}: {mb:.1f} MB" + ("  (PERINGATAN: > 25 MB, berat untuk HP)" if mb > MAX_ONNX_MB else ""))
    print("[finalize] selesai. Model web ada di web/model/.")


if __name__ == "__main__":
    main()
