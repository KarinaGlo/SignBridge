"""
signbridge/xmf/compare.py — studi perbandingan model SignBridge-XMF (fusion x encoder per modalitas).

Rancangan eksperimen (satu faktor diubah setiap kali, sisanya tetap -> perbandingan adil):
    Fase A  fusion  : early, weighted, gated, late, refusion, attention   (encoder default)
    Fase B  encoder : fusion terbaik fase A, lalu ganti SATU encoder per run
                      video {transformer, bigru, tcn} · citra {mobilenetv3, shufflenetv2, efficientnet_b0, resnet18}
                      audio {cnn_transformer, conformer, resnet} · teks {transformer, bilstm, textcnn}

    python -m signbridge.xmf.compare --task gloss --phase A                 # 6 run
    python -m signbridge.xmf.compare --task gloss --phase B                 # 10 run (fusion terbaik fase A)
    python -m signbridge.xmf.compare --task gloss --phase all --epochs 30   # semua
    python -m signbridge.xmf.compare --task gloss --phase all --dry-run     # lihat rencana saja
    python -m signbridge.xmf.compare --task gloss --report                  # susun ulang tabel dari hasil

Run yang sudah punya evaluation_metrics.json dilewati (bisa dilanjutkan setelah terputus).
Hasil: outputs/xmf/compare/<task>_<protocol>/{results.csv, results.md}

Metrik per varian: akurasi & macro-F1 uji untuk subset VI (kamera saja — metrik utama isyarat), V, I,
A (ucapan -> konsep), T (teks -> konsep), VIAT; jumlah parameter; ukuran ONNX; latensi ONNX Runtime CPU 1 thread.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from signbridge.xmf.fusion import FUSION_NAMES, FUSIONS
from signbridge.xmf.model import DEFAULT_ENCODERS

ROOT = Path(__file__).resolve().parents[2]
ENCODER_OPTIONS = {
    "pose": ["transformer", "bigru", "tcn"],
    "image": ["mobilenetv3", "shufflenetv2", "efficientnet_b0", "resnet18"],
    "audio": ["cnn_transformer", "conformer", "resnet"],
    "text": ["transformer", "bilstm", "textcnn"],
}
SUBSET_COLS = ["VI", "V", "I", "A", "T", "VIAT"]


def phase_a() -> List[Dict]:
    return [{"fusion": f, "encoders": dict(DEFAULT_ENCODERS)} for f in FUSIONS]


def phase_b(fusion: str) -> List[Dict]:
    runs = [{"fusion": fusion, "encoders": dict(DEFAULT_ENCODERS)}]
    for mod, opts in ENCODER_OPTIONS.items():
        for o in opts:
            if o != DEFAULT_ENCODERS[mod]:
                runs.append({"fusion": fusion, "encoders": dict(DEFAULT_ENCODERS, **{mod: o})})
    return runs


def run_dir(cfg: Dict, variant: Dict, protocol: str) -> Path:
    from signbridge.xmf.train import variant_tag

    tag = variant_tag(variant)
    name = cfg["experiment_id"] if tag == "attention" else f"{cfg['experiment_id']}_{tag}"
    return ROOT / "outputs/xmf" / f"{name}_{protocol}"


def onnx_stats(ckpt: Path, runs: int = 10) -> Dict:
    """Ekspor sementara ke memori lalu ukur ukuran & latensi ONNX Runtime CPU (1 thread, mirip WASM)."""
    import onnxruntime as ort
    import torch

    from signbridge.xmf.export import dummy_inputs
    from signbridge.xmf.model import XMFOnnx, build_model

    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    m = build_model(ck["task"], len(ck["classes"]), dict(ck["config"].get("model", {}), pretrained_image=False))
    m.load_state_dict(ck["model"])
    w = XMFOnnx(m.eval()).eval()
    x = dummy_inputs(m.shapes)
    f = io.BytesIO()
    torch.onnx.export(w, x, f, dynamo=False, opset_version=17,
                      input_names=["pose", "frames", "audio", "text", "modality_mask"])
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    s = ort.InferenceSession(f.getvalue(), so)
    feed = {i.name: t.numpy() for i, t in zip(s.get_inputs(), x)}
    s.run(None, feed)
    t0 = time.perf_counter()
    for _ in range(runs):
        s.run(None, feed)
    return {"onnx_mb": round(len(f.getvalue()) / 1e6, 1), "latency_ms": round((time.perf_counter() - t0) / runs * 1000, 1)}


def collect(cfg: Dict, variants: List[Dict], protocol: str, with_onnx: bool = True) -> List[Dict]:
    from signbridge.xmf.train import variant_tag

    rows = []
    for v in variants:
        d = run_dir(cfg, v, protocol)
        mfile, sfile = d / "evaluation_metrics.json", d / "train_summary.json"
        if not mfile.exists():
            continue
        met = json.loads(mfile.read_text())
        summ = json.loads(sfile.read_text()) if sfile.exists() else {}
        row = {"variant": variant_tag(v), "fusion": FUSION_NAMES[v["fusion"]],
               **{f"enc_{k}": v["encoders"][k] for k in ("pose", "image", "audio", "text")},
               "params_M": round(summ.get("params", 0) / 1e6, 2), "epochs": summ.get("epochs_trained"),
               "train_min": round(summ.get("seconds", 0) / 60, 1)}
        for s in SUBSET_COLS:
            r = met["subsets"].get(s) or {}
            row[f"{s}_acc"] = round(r.get("accuracy", float("nan")), 4)
            row[f"{s}_f1"] = round(r.get("macro_f1", float("nan")), 4)
        if with_onnx and (d / "best.pt").exists():
            try:
                row.update(onnx_stats(d / "best.pt"))
            except Exception as e:  # noqa: BLE001
                print(f"[compare] ONNX {row['variant']} gagal diukur: {e}")
        rows.append(row)
    return rows


def write_report(rows: List[Dict], out: Path, title: str) -> None:
    if not rows:
        print("[compare] belum ada hasil.")
        return
    out.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    best = max(rows, key=lambda r: np.nan_to_num(r["VI_f1"], nan=-1))
    cols = ["variant", "params_M", "onnx_mb", "latency_ms", "VI_acc", "VI_f1", "V_f1", "I_f1", "A_f1", "T_f1", "VIAT_f1"]
    lines = [f"# {title}", "",
             "Metrik utama = **VI macro-F1** (kamera saja: video+citra, kondisi nyata pengguna Tuli).",
             "A/T = pengenalan konsep dari ucapan/teks (arah Dengar→Tuli), bukan akurasi pengenalan isyarat.", "",
             "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in sorted(rows, key=lambda r: -np.nan_to_num(r["VI_f1"], nan=-1)):
        cells = [("**" + str(r.get(c, "")) + "**") if r is best and c == "variant" else str(r.get(c, "")) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    # encoder dinilai di subset modalitasnya sendiri (fusion & encoder lain tetap sama)
    judge = {"pose": ("V_f1", "video saja"), "image": ("I_f1", "citra saja"),
             "audio": ("A_f1", "ucapan -> konsep"), "text": ("T_f1", "teks -> konsep")}
    ref_fusion = rows[-1]["fusion"]
    lines += ["", "## Encoder terbaik per modalitas (dinilai pada subset modalitasnya sendiri)", "",
              "| modalitas | metrik | kandidat (F1) | terbaik |", "|---|---|---|---|"]
    for mod, (col, label) in judge.items():
        cand = {}
        for r in rows:
            if r["fusion"] != ref_fusion:
                continue
            others = all(r[f"enc_{k}"] == DEFAULT_ENCODERS[k] for k in judge if k != mod)
            if others:
                cand[r[f"enc_{mod}"]] = r.get(col)
        if len(cand) > 1:
            win = max(cand, key=lambda k: np.nan_to_num(cand[k], nan=-1))
            lines.append(f"| {mod} | {col} ({label}) | " + ", ".join(f"{k} {v}" for k, v in cand.items())
                         + f" | **{win}** |")
    lines += ["", f"Terbaik (VI macro-F1): **{best['variant']}** — {best['fusion']}, "
                  f"video={best['enc_pose']}, citra={best['enc_image']}, audio={best['enc_audio']}, teks={best['enc_text']}"]
    (out / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[compare] -> {out / 'results.csv'}")


def best_fusion(cfg: Dict, protocol: str) -> Optional[str]:
    rows = collect(cfg, phase_a(), protocol, with_onnx=False)
    if not rows:
        return None
    b = max(rows, key=lambda r: np.nan_to_num(r["VI_f1"], nan=-1))
    return b["variant"].split("-")[0]


def main(argv=None) -> None:
    from signbridge.xmf.evaluate import evaluate_checkpoint
    from signbridge.xmf.train import load_config, train

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["gloss", "alphabet"], default="gloss")
    ap.add_argument("--config", type=Path, default=None, help="default: configs/xmf_<task>.yaml")
    ap.add_argument("--protocol", choices=["sd", "si"], default="sd")
    ap.add_argument("--phase", choices=["A", "B", "all"], default="A")
    ap.add_argument("--fusion", default=None, help="fusion untuk fase B (default: terbaik dari fase A)")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true", help="hanya susun tabel dari run yang sudah ada")
    a = ap.parse_args(argv)
    if a.task == "alphabet" and a.protocol == "si":
        raise SystemExit("alfabet tidak punya ID penanda; pakai --protocol sd")

    cfg = load_config(a.config or ROOT / f"configs/xmf_{a.task}.yaml")
    out = ROOT / "outputs/xmf/compare" / f"{a.task}_{a.protocol}"
    title = f"Perbandingan model SignBridge-XMF — {a.task}, protokol {a.protocol.upper()}"

    variants: List[Dict] = []
    if a.phase in ("A", "all"):
        variants += phase_a()
    if a.report:
        variants = phase_a() + phase_b(a.fusion or best_fusion(cfg, a.protocol) or "attention")
        write_report(collect(cfg, _unique(variants), a.protocol), out, title)
        return
    if a.phase == "B":
        variants += phase_b(a.fusion or best_fusion(cfg, a.protocol) or "attention")

    def todo(vs):
        return [v for v in _unique(vs) if not (run_dir(cfg, v, a.protocol) / "evaluation_metrics.json").exists()]

    if a.dry_run:
        from signbridge.xmf.train import variant_tag

        pending = todo(variants + (phase_b(a.fusion or "<terbaik fase A>") if a.phase == "all" else []))
        print(f"[compare] {len(pending)} run akan dijalankan:")
        for v in pending:
            print("   -", variant_tag(v))
        return

    def run_all(vs):
        for i, v in enumerate(todo(vs), 1):
            c = json.loads(json.dumps(cfg))
            c["model"].update({"fusion": v["fusion"], "encoders": v["encoders"]})
            d = run_dir(cfg, v, a.protocol)
            print(f"\n===== [{i}] {d.name} =====")
            ckpt, _ = train(c, a.protocol, d, a.device, a.epochs)
            evaluate_checkpoint(ckpt, d, a.device)

    run_all(variants)
    if a.phase == "all":
        bf = a.fusion or best_fusion(cfg, a.protocol) or "attention"
        print(f"\n[compare] fusion terbaik fase A = {bf} -> fase B")
        variants += phase_b(bf)
        run_all(variants)
    write_report(collect(cfg, _unique(variants), a.protocol), out, title)


def _unique(vs: List[Dict]) -> List[Dict]:
    seen, out = set(), []
    for v in vs:
        k = json.dumps(v, sort_keys=True)
        if k not in seen:
            seen.add(k)
            out.append(v)
    return out


if __name__ == "__main__":
    main()
