"""
signbridge/xmf/evaluate.py — TAHAP 6 (EVALUATION) SignBridge-XMF.

Mengevaluasi checkpoint pada split test protokolnya, untuk setiap SUBSET modalitas:
    VI   = kamera saja (video+citra)  <-- METRIK UTAMA untuk penerjemahan isyarat di browser
    V, I = ablation per cabang visual
    A, T = ucapan / ketikan saja (arah Dengar -> Tuli, lewat ruang konsep yang sama)
    VIA, VIT, VIAT = kombinasi fusion

Catatan kejujuran ilmiah: audio & teks dipasangkan di tingkat KONSEP, sehingga subset yang memuat A/T
hampir pasti benar dan TIDAK boleh dilaporkan sebagai akurasi pengenalan isyarat. Laporkan VI.

    python -m signbridge.xmf.evaluate --ckpt outputs/xmf/XMF_gloss_sd/best.pt
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.data import DataLoader

from signbridge.xmf.data import SUBSETS, XMFDataset
from signbridge.xmf.model import build_model
from signbridge.xmf.train import evaluate_subset

ROOT = Path(__file__).resolve().parents[2]


def _plot_confusion(y, p, classes, path: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(classes)
    cm = np.zeros((n, n), dtype=np.int64)
    for a, b in zip(y, p):
        cm[a, b] += 1
    norm = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(11, 10))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n), classes, rotation=90, fontsize=7)
    ax.set_yticks(range(n), classes, fontsize=7)
    ax.set_xlabel("Prediksi")
    ax.set_ylabel("Label sebenarnya")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def auto_device() -> str:
    from signbridge.xmf.train import auto_device as _a

    return _a()


def evaluate_checkpoint(ckpt_path: Path, out_dir: Optional[Path] = None, device: Optional[str] = None) -> dict:
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg, task, classes, protocol = ck["config"], ck["task"], ck["classes"], ck["protocol"]
    out_dir = out_dir or ckpt_path.parent
    dev = torch.device(device or auto_device())
    mcfg = dict(cfg.get("model", {}), pretrained_image=False)
    model = build_model(task, len(classes), mcfg)
    model.load_state_dict(ck["model"])
    model.to(dev).eval()

    split = "test" if protocol != "final" else "val"
    ds = XMFDataset(task, ROOT / cfg["processed_csv"], split, protocol,
                    ROOT / cfg["audio_bank"] if cfg.get("audio_bank") else None, train=False)
    dl = DataLoader(ds, batch_size=32, shuffle=False, num_workers=int(cfg.get("num_workers", 2)))

    results, ablation = {}, []
    for name in SUBSETS:
        r = evaluate_subset(model, dl, dev, name, len(classes))
        if r.get("n", 0) == 0:
            continue
        results[name] = {k: v for k, v in r.items() if not k.startswith("_")}
        ablation.append({"subset": name, "n": r["n"], "accuracy": round(r["accuracy"], 4),
                         "macro_f1": round(r["macro_f1"], 4), "top5": round(r["top5"], 4),
                         "w_video": r["mean_modality_weights"][0], "w_image": r["mean_modality_weights"][1],
                         "w_audio": r["mean_modality_weights"][2], "w_text": r["mean_modality_weights"][3]})
        if name == "VI":
            _plot_confusion(r["_y"], r["_p"], classes, out_dir / "confusion_matrix_VI.png",
                            f"SignBridge-XMF {task} — kamera saja (video+citra), protokol {protocol}")
            with (out_dir / "classification_report_VI.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["class", "precision", "recall", "f1", "support"])
                for c, cname in enumerate(classes):
                    tp = np.sum((r["_p"] == c) & (r["_y"] == c))
                    prec = tp / max(np.sum(r["_p"] == c), 1)
                    rec = tp / max(np.sum(r["_y"] == c), 1)
                    w.writerow([cname, round(prec, 4), round(rec, 4),
                                round(2 * prec * rec / max(prec + rec, 1e-9), 4), int(np.sum(r["_y"] == c))])

    with (out_dir / "ablation_modalities.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ablation[0]))
        w.writeheader()
        w.writerows(ablation)
    metrics = {"task": task, "protocol": protocol, "split": split, "checkpoint": str(ckpt_path),
               "best_epoch": ck.get("epoch"), "primary_metric": "VI (kamera saja)",
               "primary": results.get("VI"), "subsets": results,
               "note": "Subset berisi A/T dipasangkan di tingkat konsep; jangan dilaporkan sbg akurasi isyarat."}
    (out_dir / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    vi = results.get("VI", {})
    print(f"[XMF eval] {task}/{protocol}: VI acc={vi.get('accuracy', 0):.4f} F1={vi.get('macro_f1', 0):.4f} "
          f"| ablation -> {out_dir / 'ablation_modalities.csv'}")
    return metrics


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--device", default=None)
    a = ap.parse_args(argv)
    evaluate_checkpoint(a.ckpt, a.out, a.device)


if __name__ == "__main__":
    main()
