"""
signbridge/xmf/train.py — TAHAP 4-5 (MODELING + TRAINING) SignBridge-XMF.

    python -m signbridge.xmf.train --config configs/xmf_gloss.yaml                    # protokol di config
    python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol si      # uji penanda baru
    python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol final   # model deploy
    python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --set model.fusion=gated \
                                   --set model.encoders.audio=conformer               # varian lain

Pemilihan checkpoint terbaik memakai macro-F1 validasi pada subset KAMERA SAJA (video+citra),
karena itulah kondisi nyata pengguna Tuli di browser. Hasil: outputs/xmf/<exp>/{best.pt, history.csv, ...}
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader, WeightedRandomSampler

from signbridge.xmf.config import classes_for
from signbridge.xmf.data import XMFDataset, sample_subset_masks, subset_mask
from signbridge.xmf.model import build_model, count_params, xmf_loss

ROOT = Path(__file__).resolve().parents[2]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_config(path: Path, overrides: Optional[Dict] = None, sets: Optional[list] = None) -> Dict:
    """`sets` = daftar "a.b.c=nilai", mis. ["model.fusion=gated", "model.encoders.audio=conformer"]."""
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for k, v in (overrides or {}).items():
        if v is not None:
            cfg[k] = v
    for item in sets or []:
        key, _, val = item.partition("=")
        node = cfg
        parts = key.strip().split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = yaml.safe_load(val)
    return cfg


def variant_tag(model_cfg: Dict) -> str:
    """Nama pendek varian, mis. 'gated' atau 'attention-audio_conformer'."""
    from signbridge.xmf.model import DEFAULT_ENCODERS

    enc = model_cfg.get("encoders") or {}
    diff = [f"{k}_{v}" for k, v in sorted(enc.items()) if DEFAULT_ENCODERS.get(k) != v]
    return "-".join([model_cfg.get("fusion", "attention")] + diff)


def _to(batch: Dict[str, torch.Tensor], dev: torch.device) -> Dict[str, torch.Tensor]:
    return {k: v.to(dev, non_blocking=True) for k, v in batch.items()}


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n: int) -> float:
    f1s = []
    for c in range(n):
        tp = np.sum((y_pred == c) & (y_true == c))
        fp = np.sum((y_pred == c) & (y_true != c))
        fn = np.sum((y_pred != c) & (y_true == c))
        if tp + fp + fn == 0:
            continue
        f1s.append(2 * tp / max(2 * tp + fp + fn, 1))
    return float(np.mean(f1s)) if f1s else 0.0


@torch.no_grad()
def evaluate_subset(model, loader, dev, subset: str, num_classes: int) -> Dict:
    model.eval()
    ys, ps, probs, weights, losses = [], [], [], [], []
    for b in loader:
        b = _to(b, dev)
        m = subset_mask(b["mask"], subset)
        keep = m.sum(1) > 0
        if keep.sum() == 0:
            continue
        o = model(b["pose"][keep], b["frames"][keep], b["audio"][keep], b["text"][keep], m[keep])
        losses.append(float(torch.nn.functional.cross_entropy(o["logits"], b["label"][keep])) * int(keep.sum()))
        pr = torch.softmax(o["logits"], 1)
        ys.append(b["label"][keep].cpu().numpy())
        ps.append(pr.argmax(1).cpu().numpy())
        probs.append(pr.cpu().numpy())
        weights.append(o["modality_weights"].cpu().numpy())
    if not ys:
        return {"n": 0}
    y, p, pr = np.concatenate(ys), np.concatenate(ps), np.concatenate(probs)
    top5 = np.mean([y[i] in np.argsort(-pr[i])[:5] for i in range(len(y))])
    return {"n": int(len(y)), "loss": float(sum(losses) / len(y)), "accuracy": float(np.mean(y == p)),
            "macro_f1": macro_f1(y, p, num_classes), "top5": float(top5),
            "mean_modality_weights": np.concatenate(weights).mean(0).round(4).tolist(),
            "_y": y, "_p": p, "_prob": pr}


def make_loaders(cfg: Dict, task: str, protocol: str):
    proc = ROOT / cfg["processed_csv"]
    bank = ROOT / cfg["audio_bank"] if cfg.get("audio_bank") else None
    tr = XMFDataset(task, proc, "train", protocol, bank, train=True, cache=cfg.get("cache", False))
    va = XMFDataset(task, proc, "val", protocol, bank, train=False, cache=cfg.get("cache", False))
    te = XMFDataset(task, proc, "test", protocol, bank, train=False) if protocol != "final" else None
    if len(tr) == 0 or len(va) == 0:
        raise SystemExit(f"Split kosong (train={len(tr)}, val={len(va)}). Jalankan ingest & preprocess dulu.")
    # sampler seimbang per kelas (data citra masih dicicil -> jumlah per kelas bisa timpang)
    labels = np.array(tr.labels())
    counts = np.bincount(labels, minlength=len(classes_for(task))).astype(np.float64)
    w = 1.0 / np.maximum(counts[labels], 1)
    sampler = WeightedRandomSampler(torch.tensor(w), num_samples=len(tr), replacement=True)
    nw = int(cfg.get("num_workers", 2))
    kw = dict(num_workers=nw, persistent_workers=nw > 0, pin_memory=torch.cuda.is_available())
    bs = int(cfg["training"]["batch_size"])
    return (DataLoader(tr, batch_size=bs, sampler=sampler, drop_last=len(tr) > bs, **kw),
            DataLoader(va, batch_size=bs * 2, shuffle=False, **kw),
            DataLoader(te, batch_size=bs * 2, shuffle=False, **kw) if te is not None and len(te) else None,
            (len(tr), len(va), len(te) if te else 0))


def train(cfg: Dict, protocol: str, out_dir: Path, device: Optional[str] = None, max_epochs: Optional[int] = None):
    task = cfg["task"]
    classes = classes_for(task)
    set_seed(int(cfg.get("seed", 42)))
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    out_dir.mkdir(parents=True, exist_ok=True)
    tl, vl, test_l, sizes = make_loaders(cfg, task, protocol)
    model = build_model(task, len(classes), cfg.get("model", {})).to(dev)
    tc = cfg["training"]
    epochs = int(max_epochs or tc["max_epochs"])

    backbone = [p for n, p in model.named_parameters() if n.startswith("image_enc.backbone") and p.requires_grad]
    others = [p for n, p in model.named_parameters() if not n.startswith("image_enc.backbone") and p.requires_grad]
    opt = torch.optim.AdamW([{"params": others, "lr": tc["learning_rate"]},
                             {"params": backbone, "lr": tc["learning_rate"] * tc.get("backbone_lr_mult", 0.2)}],
                            weight_decay=tc["weight_decay"])
    steps = max(1, epochs * len(tl))
    warm = min(int(0.05 * steps), 500)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / max(warm, 1) if s < warm else 0.5 * (1 + np.cos(np.pi * (s - warm) / max(steps - warm, 1))))
    use_amp = dev.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    rng = random.Random(int(cfg.get("seed", 42)))
    probs = cfg["modality_subsets"]

    print(f"[XMF] varian: {model.describe()}")
    print(f"[XMF] task={task} protokol={protocol} device={dev} | train/val/test={sizes} | "
          f"param={count_params(model):,} (latih {count_params(model, True):,})")
    hist, best, best_ep, bad = [], -1.0, -1, 0
    for ep in range(1, epochs + 1):
        model.train()
        t0, tot, n = time.time(), 0.0, 0
        for b in tl:
            b = _to(b, dev)
            m = sample_subset_masks(b["mask"].cpu(), probs, rng).to(dev)
            with torch.autocast(dev.type, enabled=use_amp):
                o = model(b["pose"], b["frames"], b["audio"], b["text"], m)
                L = xmf_loss(o, b["label"], tc["label_smoothing"], tc["lambda_proto"])
            opt.zero_grad(set_to_none=True)
            scaler.scale(L["loss"]).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot += float(L["loss"].detach()) * b["label"].size(0)
            n += b["label"].size(0)
        vi = evaluate_subset(model, vl, dev, "VI", len(classes))
        va = evaluate_subset(model, vl, dev, "VIAT", len(classes))
        row = {"epoch": ep, "train_loss": round(tot / max(n, 1), 4), "val_VI_acc": round(vi["accuracy"], 4),
               "val_VI_f1": round(vi["macro_f1"], 4), "val_VIAT_acc": round(va["accuracy"], 4),
               "val_VI_loss": round(vi["loss"], 4), "sec": round(time.time() - t0, 1)}
        hist.append(row)
        print("  " + " | ".join(f"{k}={v}" for k, v in row.items()))
        score = vi["macro_f1"] - 1e-3 * vi["loss"]
        if score > best:
            best, best_ep, bad = score, ep, 0
            torch.save({"model": model.state_dict(), "config": cfg, "task": task, "classes": classes,
                        "protocol": protocol, "epoch": ep, "val_VI": {k: v for k, v in vi.items() if not k.startswith("_")}},
                       out_dir / "best.pt")
        else:
            bad += 1
            if bad >= int(tc["patience"]):
                print(f"[XMF] early stopping di epoch {ep} (terbaik: {best_ep})")
                break

    with (out_dir / "history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hist[0]))
        w.writeheader()
        w.writerows(hist)
    (out_dir / "train_summary.json").write_text(json.dumps(
        {"task": task, "protocol": protocol, "best_epoch": best_ep, "epochs_trained": len(hist),
         "sizes": dict(zip(["train", "val", "test"], sizes)), "params": count_params(model),
         "variant": variant_tag(cfg.get("model", {})), "description": model.describe(),
         "seconds": round(sum(r["sec"] for r in hist), 1)}, indent=2))
    print(f"[XMF] selesai. checkpoint terbaik epoch {best_ep} -> {out_dir / 'best.pt'}")
    return out_dir / "best.pt", test_l


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--protocol", choices=["sd", "si", "final"], default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--no-eval", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="KUNCI=NILAI",
                    help="ubah config, mis. --set model.fusion=gated --set model.encoders.audio=conformer")
    a = ap.parse_args(argv)
    cfg = load_config(a.config, sets=a.set)
    protocol = a.protocol or cfg.get("protocol", "sd")
    tag = variant_tag(cfg.get("model", {}))
    name = cfg["experiment_id"] if tag == "attention" else f"{cfg['experiment_id']}_{tag}"
    out = a.out or ROOT / "outputs/xmf" / f"{name}_{protocol}"
    ckpt, _ = train(cfg, protocol, out, a.device, a.epochs)
    if not a.no_eval and protocol != "final":
        from signbridge.xmf.evaluate import evaluate_checkpoint

        evaluate_checkpoint(ckpt, out, a.device)


if __name__ == "__main__":
    main()
