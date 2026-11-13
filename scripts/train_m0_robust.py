"""Latih ulang M0 (Student Pose-Transformer) supaya TAHAN untuk pengenalan LIVE — dijalankan di PC Gloria.

Masalah model lama (outputs/experiments/M0_student_baseline): akurasi offline 99,1% tetapi live sering salah karena
  (1) diuji pada penutur yang SAMA dengan data latih (protokol SD) -> angka terlalu optimistis untuk orang baru;
  (2) tanpa augmentasi potongan waktu -> rapuh ketika potongan isyarat live tidak persis sama dengan klip latih;
  (3) tanpa cermin -> penutur kidal / tangan dominan berbeda tidak dikenali;
  (4) dilatih di CPU walau ada RTX 3050.

Perintah (PowerShell/terminal, dari root repo):
  # A. ukur kemampuan pada PENUTUR BARU (leave-one-signer-out), lalu laporkan rata-rata ± sd di Bab IV
  python scripts/train_m0_robust.py --loso
  # B. model final untuk web: semua penutur + augmentasi kuat (+ rekaman tim bila ada), ekspor ke web/model
  python scripts/train_m0_robust.py --protocol sd --extra-manifest data/selfrec/manifest_own.csv --export
GPU: pasang PyTorch CUDA (pip install torch --index-url https://download.pytorch.org/whl/cu121); skrip otomatis memakai cuda.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import ConcatDataset, DataLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signbridge.constants import BISINDO_32_GLOSSES  # noqa: E402
from signbridge.data.dataset import SignDataset  # noqa: E402
from signbridge.models.student import StudentPoseTransformer  # noqa: E402

MODEL_CFG = {"d_model": 160, "nhead": 4, "num_layers": 4, "dim_feedforward": 640, "dropout": 0.15}
AUG = {"enabled": True, "mirror_p": 0.5, "rot_deg": 15.0, "scale_range": (0.85, 1.15), "shift_range": 0.05,
       "noise_std": 0.004, "speed_range": (0.75, 1.3), "hand_dropout_p": 0.15, "time_crop_p": 0.7, "time_crop_min": 0.7}


def run_epoch(model, loader, device, criterion=None, optimizer=None):
    train = optimizer is not None
    model.train(train)
    tot, correct, n, ys, ps = 0.0, 0, 0, [], []
    for b in loader:
        pose = (b["pose"] * b["mask"].unsqueeze(-1).float()).to(device)
        y = b["label"].to(device)
        with torch.set_grad_enabled(train):
            logits = model(pose)
            loss = criterion(logits, y) if criterion else torch.tensor(0.0)
            if train:
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
        p = logits.argmax(-1)
        tot += float(loss) * len(y); correct += int((p == y).sum()); n += len(y)
        ys.append(y.cpu().numpy()); ps.append(p.cpu().numpy())
    return tot / max(n, 1), correct / max(n, 1), np.concatenate(ys), np.concatenate(ps)


def macro_f1(y, p, k=32):
    f = []
    for c in range(k):
        tp = ((p == c) & (y == c)).sum(); fp = ((p == c) & (y != c)).sum(); fn = ((p != c) & (y == c)).sum()
        if tp + fn:
            f.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f)) if f else 0.0


def train_one(args, protocol, test_signer, out_dir: Path, device):
    out_dir.mkdir(parents=True, exist_ok=True)
    common = dict(data_root=ROOT, protocol=protocol, test_signer=test_signer, allow_mixed_sources=False,
                  allow_partial_class_coverage=True)
    man = ROOT / args.manifest
    tr = SignDataset(man, split="train", augment_cfg=AUG, **common)
    va = SignDataset(man, split="val", **common)
    te = SignDataset(man, split="test", **common)
    train_sets = [tr]
    if args.extra_manifest and (ROOT / args.extra_manifest).exists():   # rekaman tim: hanya menambah data LATIH
        train_sets.append(SignDataset(ROOT / args.extra_manifest, split="train", augment_cfg=AUG, data_root=ROOT,
                                      protocol="sd", allow_mixed_sources=False, allow_partial_class_coverage=True))
    print(f"[data] protokol={protocol} test_signer={test_signer} latih={sum(len(d) for d in train_sets)} val={len(va)} uji={len(te)}")
    dl_tr = DataLoader(ConcatDataset(train_sets), batch_size=args.batch, shuffle=True, num_workers=args.workers, drop_last=True)
    dl_va = DataLoader(va, batch_size=64, num_workers=args.workers)
    dl_te = DataLoader(te, batch_size=64, num_workers=args.workers)

    model = StudentPoseTransformer(num_classes=32, max_len=64, num_keypoints=86, **MODEL_CFG).to(device)
    if args.init and Path(args.init).exists():
        sd = torch.load(args.init, map_location="cpu", weights_only=False)
        model.load_state_dict(sd.get("model_state_dict", sd), strict=False)
        print(f"[init] fine-tune dari {args.init}")
    crit = nn.CrossEntropyLoss(label_smoothing=0.1)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.05)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=args.epochs * len(dl_tr), pct_start=0.1)

    best, bad, hist = -1.0, 0, []
    for ep in range(1, args.epochs + 1):
        for d in train_sets:
            d.set_epoch(ep)
        t0 = time.time()
        model.train()
        tl, ta, _, _ = 0.0, 0.0, None, None
        for b in dl_tr:
            pose = (b["pose"] * b["mask"].unsqueeze(-1).float()).to(device); y = b["label"].to(device)
            loss = crit(model(pose), y)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
            tl += float(loss)
        vl, vacc, _, _ = run_epoch(model, dl_va, device, crit)
        hist.append({"epoch": ep, "train_loss": tl / len(dl_tr), "val_loss": vl, "val_acc": vacc, "sec": round(time.time() - t0, 1)})
        print(f"ep {ep:03d} train_loss {tl/len(dl_tr):.3f} val_acc {vacc:.4f} ({time.time()-t0:.0f}s)")
        if vacc > best:
            best, bad = vacc, 0
            torch.save({"model_state_dict": model.state_dict(), "config": {"model": MODEL_CFG, "augment": {k: list(v) if isinstance(v, tuple) else v for k, v in AUG.items()}},
                        "classes": list(BISINDO_32_GLOSSES), "num_classes": 32, "epoch": ep, "val_acc": vacc,
                        "protocol": protocol, "test_signer": test_signer}, out_dir / "best_model.pt")
        else:
            bad += 1
            if bad >= args.patience:
                break
    model.load_state_dict(torch.load(out_dir / "best_model.pt", map_location=device, weights_only=False)["model_state_dict"])
    _, tacc, y, p = run_epoch(model, dl_te, device)
    signers = [s.get("signer", "?") if isinstance(s, dict) else getattr(s, "signer", "?") for s in te.samples]
    per_signer = {}
    for sg in sorted(set(signers)):
        m = np.array([x == sg for x in signers])
        if m.any():
            per_signer[sg] = float((y[m] == p[m]).mean())
    res = {"protocol": protocol, "test_signer": test_signer, "test_acc": tacc, "test_macro_f1": macro_f1(y, p),
           "per_signer_acc": per_signer, "best_val_acc": best, "epochs": len(hist), "augment": {k: str(v) for k, v in AUG.items()}}
    json.dump(res, open(out_dir / "evaluation_metrics.json", "w"), indent=2)
    json.dump(hist, open(out_dir / "training_history.json", "w"), indent=2)
    print(f"[hasil] {protocol} {test_signer}: test_acc={tacc:.4f} macro_f1={res['test_macro_f1']:.4f} per_signer={per_signer}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifest_wl_bisindo.csv")
    ap.add_argument("--extra-manifest", default=None, help="manifest keypoint rekaman tim (hanya menambah data latih)")
    ap.add_argument("--protocol", default="sd", choices=["sd", "si"])
    ap.add_argument("--test-signer", default="SIGNER1")
    ap.add_argument("--loso", action="store_true", help="leave-one-signer-out untuk semua penutur")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--patience", type=int, default=25)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--init", default=None, help="checkpoint awal (mis. M0 lama) untuk fine-tune")
    ap.add_argument("--out", default="outputs/experiments/M0_robust")
    ap.add_argument("--export", action="store_true", help="ekspor model terbaik ke web/model (student.onnx + labels.json)")
    args = ap.parse_args()
    torch.manual_seed(42); np.random.seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else " — pasang PyTorch CUDA agar RTX 3050 terpakai"))
    out = ROOT / args.out

    if args.loso:
        import csv
        signers = sorted({r["signer"] for r in csv.DictReader(open(ROOT / args.manifest, encoding="utf-8"))})
        results = [train_one(args, "si", s, out / f"si_{s}", device) for s in signers]
        accs = [r["test_acc"] for r in results]
        summ = {"protocol": "LOSO", "signers": signers, "acc_per_signer": dict(zip(signers, accs)),
                "mean": float(np.mean(accs)), "std": float(np.std(accs))}
        json.dump(summ, open(out / "loso_summary.json", "w"), indent=2)
        print(f"[LOSO] akurasi penutur baru = {summ['mean']:.4f} ± {summ['std']:.4f}  {summ['acc_per_signer']}")
        return

    res = train_one(args, args.protocol, args.test_signer, out / args.protocol, device)
    if args.export:
        from signbridge.export_onnx import export_student_to_onnx
        info = export_student_to_onnx(out / args.protocol / "best_model.pt", ROOT / "web" / "model")
        print("[ekspor]", info)
    return res


if __name__ == "__main__":
    main()
