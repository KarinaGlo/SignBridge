"""
signbridge/train_multimodal.py — Pelatihan & evaluasi M6 (fusion 4 modalitas).

    python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml
    python -m signbridge.train_multimodal --config configs/06_multimodal_fusion.yaml --smoke   # uji pipa

Keluaran di output_dir:
    best_model.pt, training_history.csv, evaluation_metrics.json,
    ablation_modalities.csv  (akurasi untuk ke-15 kombinasi modalitas pada data uji),
    modality_weights.csv     (rata-rata bobot fusion per modalitas, per kelas)

`--smoke` membangkitkan data ACAK hanya untuk memastikan seluruh pipa (data -> model -> loss ->
evaluasi -> simpan) berjalan. Angka dari mode smoke TIDAK BOLEH dilaporkan sebagai hasil.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from signbridge.constants import BISINDO_32_GLOSSES
from signbridge.models.multimodal import (
    SignBridgeMultimodalFusion,
    count_parameters,
    multimodal_loss,
)
from signbridge.multimodal.constants import MODALITIES, NUM_MODALITIES
from signbridge.multimodal.dataset import MultimodalSampleLoader, has_any_modality, read_manifest

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_CFG = {
    "experiment_id": "M6_multimodal_fusion",
    "seed": 42,
    "manifest": "data/multimodal/manifest_multimodal.csv",
    "output_dir": "outputs/experiments/M6_multimodal_fusion",
    "model": {"d_model": 128, "nhead": 4, "fusion_layers": 2, "dropout": 0.1, "modality_dropout": 0.3},
    "training": {
        "batch_size": 16, "learning_rate": 0.0005, "weight_decay": 0.01, "max_epochs": 80,
        "patience": 12, "label_smoothing": 0.1, "lambda_aux": 0.3, "augment": True,
    },
}


# ---------------------------------------------------------------------------
class TorchMultimodalDataset(Dataset):
    def __init__(self, loader: MultimodalSampleLoader, augment: bool = False, seed: int = 42):
        self.loader = loader
        self.augment = augment
        self.rng = np.random.default_rng(seed)
        self.cache: Dict[int, Dict[str, np.ndarray]] = {}

    def __len__(self) -> int:
        return len(self.loader)

    def __getitem__(self, idx: int):
        if idx not in self.cache:
            self.cache[idx] = self.loader.load(idx)
        s = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in self.cache[idx].items()}
        if self.augment:
            s = augment_sample(s, self.rng)
        return {
            "pose": torch.from_numpy(s["pose"]),
            "image": torch.from_numpy(s["image"]),
            "audio": torch.from_numpy(s["audio"]),
            "text": torch.from_numpy(s["text"]),
            "modality_mask": torch.from_numpy(s["modality_mask"]),
            "label": torch.tensor(int(s["label"]), dtype=torch.long),
        }


def augment_sample(s: Dict[str, np.ndarray], rng: np.random.Generator) -> Dict[str, np.ndarray]:
    """Augmentasi ringan per modalitas (hanya data latih)."""
    if s["modality_mask"][0] > 0:  # pose: rotasi ±12°, skala 0,9–1,1, geser ±0,03
        ang = np.deg2rad(rng.uniform(-12, 12))
        R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], dtype=np.float32)
        p = s["pose"]
        nz = np.any(p != 0, axis=-1, keepdims=True)
        xy = p[..., :2] @ R.T * rng.uniform(0.9, 1.1) + rng.uniform(-0.03, 0.03, size=2)
        p[..., :2] = np.where(nz, xy, 0.0)
        s["pose"] = p.astype(np.float32)
    if s["modality_mask"][1] > 0:  # citra: flip horizontal 0% (isyarat asimetris) -> kecerahan & noise
        s["image"] = (s["image"] * rng.uniform(0.85, 1.15) + rng.normal(0, 0.05, s["image"].shape)).astype(np.float32)
    if s["modality_mask"][2] > 0:  # audio: SpecAugment sederhana (mask waktu & frekuensi)
        a = s["audio"]
        f0 = rng.integers(0, a.shape[0] - 8)
        t0 = rng.integers(0, a.shape[1] - 25)
        a[f0:f0 + rng.integers(0, 8)] = 0.0
        a[:, t0:t0 + rng.integers(0, 25)] = 0.0
        s["audio"] = a
    return s


# ---------------------------------------------------------------------------
def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def macro_f1(preds: np.ndarray, targets: np.ndarray, num_classes: int) -> float:
    f1s = []
    for c in range(num_classes):
        tp = np.sum((preds == c) & (targets == c))
        fp = np.sum((preds == c) & (targets != c))
        fn = np.sum((preds != c) & (targets == c))
        if tp + fp + fn == 0:
            continue
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * p * r / (p + r) if p + r else 0.0)
    return float(np.mean(f1s)) if f1s else 0.0


@torch.no_grad()
def evaluate(
    model: SignBridgeMultimodalFusion, loader: DataLoader, device: torch.device,
    force_mask: Optional[List[int]] = None, num_classes: int = 32,
) -> Dict[str, object]:
    """Evaluasi; `force_mask` (mis. [1,0,1,0]) mensimulasikan hanya sebagian modalitas yang tersedia."""
    model.eval()
    preds, targets, weights, losses = [], [], [], []
    for b in loader:
        mask = b["modality_mask"].to(device)
        if force_mask is not None:
            mask = mask * torch.tensor(force_mask, dtype=mask.dtype, device=device)
        keep = mask.sum(dim=1) > 0
        if keep.sum() == 0:
            continue
        out = model(b["pose"].to(device)[keep], b["image"].to(device)[keep], b["audio"].to(device)[keep],
                    b["text"].to(device)[keep], mask[keep])
        y = b["label"].to(device)[keep]
        losses.append(float(torch.nn.functional.cross_entropy(out["logits"], y)) * int(keep.sum()))
        preds.append(out["logits"].argmax(1).cpu().numpy())
        targets.append(y.cpu().numpy())
        weights.append(out["modality_weights"].cpu().numpy())
    if not preds:
        return {"n": 0, "accuracy": float("nan"), "macro_f1": float("nan"), "loss": float("nan")}
    P, T = np.concatenate(preds), np.concatenate(targets)
    W = np.concatenate(weights)
    return {
        "n": int(T.size),
        "accuracy": float((P == T).mean()),
        "macro_f1": macro_f1(P, T, num_classes),
        "loss": float(np.sum(losses) / T.size),
        "mean_modality_weights": {m: float(W[:, i].mean()) for i, m in enumerate(MODALITIES)},
        "preds": P, "targets": T, "weights": W,
    }


def _strip(d: Dict[str, object]) -> Dict[str, object]:
    return {k: v for k, v in d.items() if k not in ("preds", "targets", "weights")}


# ---------------------------------------------------------------------------
def build_smoke_manifest(out_dir: Path, n_per_class: int = 4, num_classes: int = 32) -> Path:
    """Data ACAK untuk uji pipa. Bukan data penelitian."""
    from signbridge.multimodal.dataset import MultimodalRecord, assign_splits, write_manifest
    from signbridge.multimodal.features import write_wav

    rng = np.random.default_rng(0)
    d = out_dir / "smoke_data"
    d.mkdir(parents=True, exist_ok=True)
    recs = []
    for c in range(num_classes):
        for k in range(n_per_class):
            cid = f"smoke_c{c}_k{k}"
            kp = rng.uniform(0.3, 0.7, size=(48, 86, 3)).astype(np.float32)
            (d / f"{cid}_kp.json").write_text(json.dumps({"keypoints": kp.tolist()}))
            write_wav(d / f"{cid}.wav", 0.2 * np.sin(np.arange(40_000) * (0.02 + 0.002 * c)).astype(np.float32))
            recs.append(MultimodalRecord(cid, f"S0{k % 2}", "gloss", BISINDO_32_GLOSSES[c], c,
                                         kp_path=str(d / f"{cid}_kp.json"), audio_path=str(d / f"{cid}.wav"),
                                         text=BISINDO_32_GLOSSES[c].lower()))
    assign_splits(recs, "sd")
    for i, r in enumerate(recs):  # pastikan ada val & test
        r.split = ["train", "train", "val", "test"][i % 4]
    path = d / "manifest_smoke.csv"
    write_manifest(recs, path)
    return path


def run(cfg: Dict, smoke: bool = False, epochs_override: Optional[int] = None) -> Dict[str, object]:
    set_seed(int(cfg.get("seed", 42)))
    out_dir = Path(cfg["output_dir"] + ("_smoke" if smoke else ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    tcfg, mcfg = cfg["training"], cfg["model"]
    if epochs_override:
        tcfg = {**tcfg, "max_epochs": epochs_override}

    manifest = build_smoke_manifest(out_dir) if smoke else Path(cfg["manifest"])
    if not manifest.exists():
        raise FileNotFoundError(
            f"Manifest {manifest} tidak ditemukan. Jalankan scripts/build_multimodal_manifest.py terlebih dahulu.")
    records = read_manifest(manifest)
    dropped = [r for r in records if not has_any_modality(r)]
    if dropped:
        print(f"[M6] {len(dropped)} sampel tanpa modalitas apa pun dilewati (contoh: {dropped[0].clip_id})")
    records = [r for r in records if has_any_modality(r)]
    splits = {s: [r for r in records if r.split == s] for s in ("train", "val", "test")}
    for s, rs in splits.items():
        if not rs:
            raise ValueError(f"Split '{s}' kosong di {manifest}.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bs = int(tcfg["batch_size"])
    dl = {
        "train": DataLoader(TorchMultimodalDataset(MultimodalSampleLoader(splits["train"]), tcfg.get("augment", True)),
                            batch_size=bs, shuffle=True),
        "val": DataLoader(TorchMultimodalDataset(MultimodalSampleLoader(splits["val"])), batch_size=bs),
        "test": DataLoader(TorchMultimodalDataset(MultimodalSampleLoader(splits["test"])), batch_size=bs),
    }
    availability = {s: MultimodalSampleLoader(rs).availability() for s, rs in splits.items()}

    model = SignBridgeMultimodalFusion(num_classes=32, **mcfg).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(tcfg["learning_rate"]), weight_decay=float(tcfg["weight_decay"]))
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=4, min_lr=1e-5)

    history, best, bad = [], float("inf"), 0
    for epoch in range(1, int(tcfg["max_epochs"]) + 1):
        model.train()
        t0, tot, n, correct = time.time(), 0.0, 0, 0
        for b in dl["train"]:
            b = {k: v.to(device) for k, v in b.items()}
            out = model(b["pose"], b["image"], b["audio"], b["text"], b["modality_mask"])
            loss = multimodal_loss(out, b["label"], float(tcfg["label_smoothing"]), float(tcfg["lambda_aux"]))["loss"]
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += float(loss.detach()) * b["label"].size(0)
            n += b["label"].size(0)
            correct += int((out["logits"].argmax(1) == b["label"]).sum())
        val = evaluate(model, dl["val"], device)
        sched.step(val["loss"])
        row = {"epoch": epoch, "train_loss": round(tot / max(n, 1), 4), "train_acc": round(correct / max(n, 1), 4),
               "val_loss": round(val["loss"], 4), "val_acc": round(val["accuracy"], 4),
               "lr": opt.param_groups[0]["lr"], "duration_sec": round(time.time() - t0, 2)}
        history.append(row)
        print(f"[M6] epoch {epoch:3d} | train_loss {row['train_loss']:.4f} acc {row['train_acc']:.3f} "
              f"| val_loss {row['val_loss']:.4f} acc {row['val_acc']:.3f}")
        if val["loss"] < best - 1e-4:
            best, bad = val["loss"], 0
            torch.save({"epoch": epoch, "model": model.state_dict(), "config": cfg}, out_dir / "best_model.pt")
        else:
            bad += 1
            if bad >= int(tcfg["patience"]):
                print(f"[M6] early stopping di epoch {epoch}")
                break

    with (out_dir / "training_history.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        w.writeheader()
        w.writerows(history)

    ckpt = torch.load(out_dir / "best_model.pt", map_location=device)
    model.load_state_dict(ckpt["model"])
    test_all = evaluate(model, dl["test"], device)

    # Ablasi: 15 kombinasi modalitas
    ablation = []
    for combo in itertools.product([0, 1], repeat=NUM_MODALITIES):
        if sum(combo) == 0:
            continue
        r = evaluate(model, dl["test"], device, force_mask=list(combo))
        ablation.append({"modalities": "+".join(m for m, on in zip(MODALITIES, combo) if on),
                         "n": r["n"], "accuracy": r["accuracy"], "macro_f1": r["macro_f1"]})
    with (out_dir / "ablation_modalities.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["modalities", "n", "accuracy", "macro_f1"])
        w.writeheader()
        w.writerows(ablation)

    # Bobot fusion rata-rata per kelas
    with (out_dir / "modality_weights.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gloss", *MODALITIES])
        for c in range(32):
            sel = test_all["targets"] == c
            if sel.any():
                w.writerow([BISINDO_32_GLOSSES[c], *[round(float(x), 4) for x in test_all["weights"][sel].mean(0)]])

    metrics = {
        "experiment_id": cfg["experiment_id"] + ("_SMOKE_RANDOM_DATA" if smoke else ""),
        "best_epoch": ckpt["epoch"], "epochs_trained": len(history),
        "parameters": count_parameters(model),
        "availability_per_split": availability,
        "test": _strip(test_all),
        "note": "SMOKE TEST dengan data acak — bukan hasil penelitian." if smoke else "",
    }
    (out_dir / "evaluation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(_strip(test_all), indent=2))
    return metrics


def load_cfg(path: Optional[str]) -> Dict:
    cfg = json.loads(json.dumps(DEFAULT_CFG))
    if path:
        if yaml is None:
            raise ImportError("PyYAML diperlukan untuk membaca config.")
        user = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Pelatihan M6 SignBridge Multimodal Fusion")
    ap.add_argument("--config", type=str, default="configs/06_multimodal_fusion.yaml")
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--smoke", action="store_true", help="Uji pipa dengan data acak (bukan hasil)")
    args = ap.parse_args(argv)
    run(load_cfg(args.config), smoke=args.smoke, epochs_override=args.epochs)


if __name__ == "__main__":
    main()
