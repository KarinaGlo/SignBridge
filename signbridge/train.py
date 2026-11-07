"""
train.py — Unified Training, Transfer Learning, & Knowledge Distillation CLI for SignBridge.

Usage (from Bab 5 Modul Jonnathan):
  python -m signbridge.train --config configs/00_student_baseline.yaml
  python -m signbridge.train --config configs/01_pose_pretrain_wlasl.yaml
  python -m signbridge.train --config configs/02_pose_finetune_bisindo.yaml
  python -m signbridge.train --config configs/03_fusion_bisindo.yaml
  python -m signbridge.train --config configs/03b_concat_bisindo.yaml
  python -m signbridge.train --config configs/03r_rgb_only_bisindo.yaml
  python -m signbridge.train --config configs/04_distill_student.yaml
  python -m signbridge.train --config configs/05a_asean_fsl_pose.yaml
  python -m signbridge.train --config configs/05b_asean_fsl_student.yaml

Outputs in runs/<name>/:
  - best.pt              : Checkpoint dict (model_state_dict, config, classes, best_val_acc, param_count)
  - log.csv              : Per-epoch training/validation metrics (epoch, train_loss, train_acc, val_loss, val_acc, lr)
  - result.json          : Summary metrics (val_acc, test_acc, top5_acc, macro_f1, param_millions, protocol)
  - test_predictions.npz : Arrays (logits, preds, labels, signers, gates) for Gloria's evaluate.py
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import yaml

from signbridge.constants import BISINDO_32_GLOSSES
from signbridge.data.dataset import SignDataset, ensure_demo_dataset
from signbridge.models.fusion import build_video_model
from signbridge.models.student import StudentPoseTransformer


def select_device(preferred: Optional[str] = None) -> torch.device:
    """Select CUDA, MPS (Apple Silicon Mac M1-M3), or CPU."""
    if preferred:
        return torch.device(preferred)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_partial(model: nn.Module, ckpt_path: str | Path) -> Tuple[int, int]:
    """
    Transfer matching weights from a pretrained checkpoint (`init_from`), skipping layers
    whose shapes differ (e.g. classification head 300 WLASL -> 32 BISINDO -> 105 FSL)
    and remapping `encoder.*` <-> `stream_a.*` prefixes if needed.

    Returns (num_loaded_tensors, num_skipped_tensors).
    """
    ckpt_path = Path(ckpt_path)
    if not ckpt_path.exists():
        return 0, 0

    ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    src_state: Dict[str, torch.Tensor] = ckpt.get("model_state_dict", ckpt)
    dst_state = model.state_dict()

    loaded = 0
    skipped = 0
    new_state: Dict[str, torch.Tensor] = {}

    for dst_k, dst_v in dst_state.items():
        candidates = [dst_k]
        if dst_k.startswith("stream_a."):
            candidates.append(dst_k.replace("stream_a.", "encoder.", 1))
        elif dst_k.startswith("encoder."):
            candidates.append(dst_k.replace("encoder.", "stream_a.", 1))

        matched = False
        for cand in candidates:
            if cand in src_state and src_state[cand].shape == dst_v.shape:
                new_state[dst_k] = src_state[cand]
                loaded += 1
                matched = True
                break
        if not matched:
            new_state[dst_k] = dst_v
            skipped += 1

    model.load_state_dict(new_state, strict=False)
    return loaded, skipped


def compute_multitask_loss(
    out: Dict[str, Any],
    labels: torch.Tensor,
    phono_labels: torch.Tensor,
    label_smoothing: float = 0.1,
    aux_weight: float = 0.3,
    phono_weight: float = 0.5,
    teacher_logits: Optional[torch.Tensor] = None,
    kd_alpha: float = 0.5,
    kd_T: float = 4.0,
) -> torch.Tensor:
    """
    Compute training loss for Student, Pose-only, RGB-only, or Two-Stream Teacher:
      - Standard / Teacher:
          L = CE_ls(y) + 0.3 * (CE_pose + CE_rgb) + 0.5 * (1/|F|) * sum_f CE(phono_f)
      - Distillation (when teacher_logits is provided):
          L = alpha * CE(y, s) + (1 - alpha) * T^2 * KL(sigma(t/T) || sigma(s/T))
    """
    logits = out["logits"]

    if teacher_logits is not None:
        hard_loss = F.cross_entropy(logits, labels, label_smoothing=label_smoothing)
        soft_loss = F.kl_div(
            F.log_softmax(logits / kd_T, dim=-1),
            F.softmax(teacher_logits.detach() / kd_T, dim=-1),
            reduction="batchmean",
        ) * (kd_T ** 2)
        return kd_alpha * hard_loss + (1.0 - kd_alpha) * soft_loss

    loss = F.cross_entropy(logits, labels, label_smoothing=label_smoothing)

    # Auxiliary pose & RGB losses (for TwoStreamFusionModel)
    pose_logits = out.get("pose_logits")
    rgb_logits = out.get("rgb_logits")
    if pose_logits is not None and rgb_logits is not None and aux_weight > 0:
        ce_pose = F.cross_entropy(pose_logits, labels)
        ce_rgb = F.cross_entropy(rgb_logits, labels)
        loss = loss + aux_weight * (ce_pose + ce_rgb)

    # Phonological multitask head loss (ignoring -1 labels)
    phono_logits_list = out.get("phonology_logits")
    if phono_logits_list and phono_weight > 0 and phono_labels is not None:
        phono_losses: List[torch.Tensor] = []
        for f_idx, f_logits in enumerate(phono_logits_list):
            if f_idx < phono_labels.shape[1]:
                target_f = phono_labels[:, f_idx]
                valid = target_f >= 0
                if torch.any(valid):
                    phono_losses.append(F.cross_entropy(f_logits[valid], target_f[valid]))
        if phono_losses:
            loss = loss + phono_weight * (sum(phono_losses) / len(phono_losses))

    return loss


def _forward_model(
    model: nn.Module,
    pose: torch.Tensor,
    rgb: torch.Tensor,
) -> Dict[str, Any]:
    if isinstance(model, StudentPoseTransformer):
        return model.forward_dict(pose, rgb)
    return model(pose, rgb)


def _compute_macro_f1(preds: np.ndarray, targets: np.ndarray, num_classes: int) -> float:
    f1s: List[float] = []
    for c in range(num_classes):
        tp = float(np.sum((preds == c) & (targets == c)))
        fp = float(np.sum((preds == c) & (targets != c)))
        fn = float(np.sum((preds != c) & (targets == c)))
        denom = 2 * tp + fp + fn
        if tp + fn > 0:
            f1s.append((2 * tp / denom) if denom > 0 else 0.0)
    return float(np.mean(f1s)) if f1s else 0.0


@torch.no_grad()
def evaluate_split(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int,
) -> Dict[str, Any]:
    model.eval()
    total_loss = 0.0
    total_count = 0
    all_logits: List[np.ndarray] = []
    all_labels: List[np.ndarray] = []
    all_signers: List[str] = []
    all_gates: List[np.ndarray] = []

    for batch in loader:
        pose = batch["pose"].to(device)
        rgb = batch["rgb"].to(device)
        labels = batch["label"].to(device)

        out = _forward_model(model, pose, rgb)
        logits = out["logits"]
        loss = F.cross_entropy(logits, labels)

        B = labels.size(0)
        total_loss += float(loss.item()) * B
        total_count += B

        all_logits.append(logits.cpu().numpy())
        all_labels.append(labels.cpu().numpy())
        all_signers.extend(batch["signer"])
        if out.get("gate") is not None:
            all_gates.append(out["gate"].cpu().numpy())

    if total_count == 0:
        return {
            "loss": 0.0,
            "acc": 0.0,
            "top5_acc": 0.0,
            "macro_f1": 0.0,
            "logits": np.zeros((0, num_classes), dtype=np.float32),
            "preds": np.zeros((0,), dtype=np.int64),
            "labels": np.zeros((0,), dtype=np.int64),
            "signers": np.array([], dtype=str),
            "gates": np.zeros((0,), dtype=np.float32),
        }

    logits_np = np.concatenate(all_logits, axis=0)
    labels_np = np.concatenate(all_labels, axis=0)
    preds_np = np.argmax(logits_np, axis=1)

    acc = float(np.mean(preds_np == labels_np))
    k = min(5, logits_np.shape[1])
    top_k = np.argsort(logits_np, axis=1)[:, -k:]
    top5_acc = float(np.mean([labels_np[i] in top_k[i] for i in range(len(labels_np))]))
    macro_f1 = _compute_macro_f1(preds_np, labels_np, num_classes)
    gates_np = np.concatenate(all_gates, axis=0) if all_gates else np.zeros((0,), dtype=np.float32)

    return {
        "loss": total_loss / max(1, total_count),
        "acc": acc,
        "top5_acc": top5_acc,
        "macro_f1": macro_f1,
        "logits": logits_np,
        "preds": preds_np,
        "labels": labels_np,
        "signers": np.array(all_signers),
        "gates": gates_np,
    }


def run_training(
    config_path: str | Path,
    protocol_override: Optional[str] = None,
    test_signer_override: Optional[str] = None,
    out_dir_override: Optional[str | Path] = None,
    epochs_override: Optional[int] = None,
) -> Dict[str, Any]:
    config_path = Path(config_path)
    with config_path.open("r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)

    seed = int(cfg.get("seed", 42))
    torch.manual_seed(seed)
    np.random.seed(seed)

    run_name = cfg.get("name", config_path.stem)
    if protocol_override and protocol_override.lower() == "si":
        signer_tag = test_signer_override or cfg.get("data", {}).get("test_signer", "s3")
        run_name = f"{run_name}_si_{signer_tag}"

    out_dir = Path(out_dir_override) if out_dir_override else Path("runs") / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    data_cfg = cfg.get("data", {})
    data_root = Path(data_cfg.get("root", "data"))
    manifest_path = Path(data_cfg.get("manifest", data_root / "manifest.csv"))
    source_filter = data_cfg.get("sources", data_cfg.get("source", ["bisindo"]))
    if isinstance(source_filter, str):
        source_filter = [source_filter]

    # Ensure demo dataset exists if manifest is missing
    if not manifest_path.exists():
        src_name = source_filter[0] if source_filter else "bisindo"
        ensure_demo_dataset(data_root, source=src_name)

    protocol = (protocol_override or data_cfg.get("protocol", "sd")).lower()
    test_signer = str(test_signer_override or data_cfg.get("test_signer", "s3"))
    phonology_csv = data_cfg.get("phonology_csv", data_root / "phonology.csv")
    augment_cfg = cfg.get("augment", cfg.get("augmentation", {"enabled": True}))

    train_ds = SignDataset(
        manifest_path=manifest_path,
        data_root=data_root,
        split="train",
        protocol=protocol,
        test_signer=test_signer,
        source_filter=source_filter,
        phonology_csv=phonology_csv,
        augment_cfg=augment_cfg,
        base_seed=seed,
    )
    val_ds = SignDataset(
        manifest_path=manifest_path,
        data_root=data_root,
        split="val",
        protocol=protocol,
        test_signer=test_signer,
        source_filter=source_filter,
        phonology_csv=phonology_csv,
        augment_cfg={"enabled": False},
        base_seed=seed,
    )
    test_ds = SignDataset(
        manifest_path=manifest_path,
        data_root=data_root,
        split="test",
        protocol=protocol,
        test_signer=test_signer,
        source_filter=source_filter,
        phonology_csv=phonology_csv,
        augment_cfg={"enabled": False},
        base_seed=seed,
    )

    classes = train_ds.classes if train_ds.classes else list(BISINDO_32_GLOSSES)
    num_classes = int(cfg.get("model", {}).get("num_classes", len(classes) or 32))

    train_cfg = cfg.get("train", cfg.get("training", {}))
    batch_size = int(train_cfg.get("batch_size", 16))
    epochs = int(epochs_override if epochs_override is not None else train_cfg.get("epochs", 10))
    lr = float(train_cfg.get("lr", train_cfg.get("base_lr", 1e-3)))
    weight_decay = float(train_cfg.get("weight_decay", 1e-2))
    grad_clip = float(train_cfg.get("grad_clip", 1.0))
    label_smoothing = float(train_cfg.get("label_smoothing", 0.1))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    device = select_device()
    model = build_video_model(cfg, num_classes=num_classes, phono_num_classes=train_ds.phono_num_classes).to(device)

    # Transfer learning initialization (`init_from`)
    init_from = cfg.get("init_from") or train_cfg.get("init_from")
    if init_from:
        loaded_cnt, skipped_cnt = load_partial(model, init_from)
        print(f"[init_from] {init_from}: loaded={loaded_cnt}, skipped={skipped_cnt}")

    # Teacher model for knowledge distillation (`teacher_ckpt`)
    teacher_model: Optional[nn.Module] = None
    distill_cfg = cfg.get("distill", cfg.get("distillation", {}))
    teacher_ckpt_path = cfg.get("teacher_ckpt") or distill_cfg.get("teacher_ckpt")
    kd_alpha = float(cfg.get("kd_alpha", distill_cfg.get("alpha", 0.5)))
    kd_T = float(cfg.get("kd_T", distill_cfg.get("temperature", 4.0)))

    if teacher_ckpt_path and Path(teacher_ckpt_path).exists():
        t_ckpt = torch.load(str(teacher_ckpt_path), map_location=device, weights_only=False)
        t_cfg = t_ckpt.get("config", {"model": {"type": "fusion"}})
        teacher_model = build_video_model(
            t_cfg, num_classes=num_classes, phono_num_classes=train_ds.phono_num_classes
        ).to(device)
        teacher_model.load_state_dict(t_ckpt["model_state_dict"], strict=False)
        teacher_model.eval()
        for p in teacher_model.parameters():
            p.requires_grad = False

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))

    param_count = sum(p.numel() for p in model.parameters())
    param_millions = round(param_count / 1e6, 3)

    best_val_acc = -1.0
    best_ckpt_path = out_dir / "best.pt"
    log_rows: List[Dict[str, Any]] = []

    for epoch in range(1, epochs + 1):
        train_ds.set_epoch(epoch)
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch in train_loader:
            pose = batch["pose"].to(device)
            rgb = batch["rgb"].to(device)
            labels = batch["label"].to(device)
            phono = batch["phonology"].to(device)

            optimizer.zero_grad()
            out = _forward_model(model, pose, rgb)

            t_logits = None
            if teacher_model is not None:
                with torch.no_grad():
                    t_out = _forward_model(teacher_model, pose, rgb)
                    t_logits = t_out["logits"]

            loss = compute_multitask_loss(
                out=out,
                labels=labels,
                phono_labels=phono,
                label_smoothing=label_smoothing,
                teacher_logits=t_logits,
                kd_alpha=kd_alpha,
                kd_T=kd_T,
            )
            loss.backward()
            if grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()

            B = labels.size(0)
            running_loss += float(loss.item()) * B
            preds = out["logits"].argmax(dim=-1)
            correct += int((preds == labels).sum().item())
            total += B

        scheduler.step()
        train_loss = running_loss / max(1, total)
        train_acc = correct / max(1, total)

        val_metrics = evaluate_split(model, val_loader, device, num_classes)
        current_lr = optimizer.param_groups[0]["lr"]

        row = {
            "epoch": epoch,
            "train_loss": round(train_loss, 5),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_metrics["loss"], 5),
            "val_acc": round(val_metrics["acc"], 4),
            "val_macro_f1": round(val_metrics["macro_f1"], 4),
            "lr": round(current_lr, 7),
        }
        log_rows.append(row)

        if val_metrics["acc"] >= best_val_acc:
            best_val_acc = val_metrics["acc"]
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "config": cfg,
                    "classes": classes,
                    "num_classes": num_classes,
                    "best_val_acc": best_val_acc,
                    "param_count": param_count,
                },
                str(best_ckpt_path),
            )

    # Save log.csv
    log_csv_path = out_dir / "log.csv"
    with log_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["epoch", "train_loss", "train_acc", "val_loss", "val_acc", "val_macro_f1", "lr"],
        )
        writer.writeheader()
        writer.writerows(log_rows)

    # Evaluate best model on test set
    best_ckpt = torch.load(str(best_ckpt_path), map_location=device, weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    test_metrics = evaluate_split(model, test_loader, device, num_classes)

    # Save test_predictions.npz
    np.savez_compressed(
        out_dir / "test_predictions.npz",
        logits=test_metrics["logits"],
        preds=test_metrics["preds"],
        labels=test_metrics["labels"],
        signers=test_metrics["signers"],
        gates=test_metrics["gates"],
        classes=np.array(classes),
    )

    result_summary = {
        "name": run_name,
        "config": str(config_path),
        "protocol": protocol,
        "test_signer": test_signer if protocol == "si" else "all",
        "num_classes": num_classes,
        "param_count": param_count,
        "param_millions": param_millions,
        "best_val_acc": round(float(best_val_acc), 4),
        "test_acc": round(float(test_metrics["acc"]), 4),
        "top5_acc": round(float(test_metrics["top5_acc"]), 4),
        "macro_f1": round(float(test_metrics["macro_f1"]), 4),
        "epochs": epochs,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with (out_dir / "result.json").open("w", encoding="utf-8") as f:
        json.dump(result_summary, f, indent=2)

    print(
        f"[train] {run_name} complete | val_acc={best_val_acc:.4f} | "
        f"test_acc={test_metrics['acc']:.4f} | macro_f1={test_metrics['macro_f1']:.4f} | "
        f"params={param_millions}M"
    )
    return result_summary


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="SignBridge Video/Pose Training CLI")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config file")
    parser.add_argument("--protocol", type=str, default=None, choices=["sd", "si"], help="Split protocol (sd or si)")
    parser.add_argument("--test-signer", type=str, default=None, help="Held-out signer for SI protocol (e.g. s3)")
    parser.add_argument("--out", type=str, default=None, help="Output run directory override")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of training epochs")
    args = parser.parse_args(argv)

    run_training(
        config_path=args.config,
        protocol_override=args.protocol,
        test_signer_override=args.test_signer,
        out_dir_override=args.out,
        epochs_override=args.epochs,
    )


if __name__ == "__main__":
    main()

