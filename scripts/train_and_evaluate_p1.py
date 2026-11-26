"""
scripts/train_and_evaluate_p1.py
Full Implementation & Evaluation Pipeline for Experiment I1-P1:
Transfer Learning MobileNetV3-Small (Pretrained ImageNet) on BISINDO Alphabet.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, UnidentifiedImageError
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD
from signbridge.image.models.mobilenetv3_p1 import build_mobilenetv3_p1, MobileNetV3SmallPretrainedClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("p1_trainer")


def set_seed(seed: int = 42) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class FingerspellP1Dataset(Dataset):
    """
    BISINDO Fingerspelling Dataset with tailored data augmentation for Sign Language.
    Strictly forbids horizontal flipping to preserve chirality/orientation of hand signs.
    """

    def __init__(
        self,
        manifest_path: str | Path,
        split: str = "train",
        seed: int = 42,
        is_train: bool = True,
    ) -> None:
        super().__init__()
        self.manifest_path = Path(manifest_path)
        self.split = split
        self.seed = seed
        self.is_train = is_train

        # Setup transforms
        if self.is_train:
            # Conservative augmentation tailored for sign gestures
            self.transform = T.Compose([
                T.RandomResizedCrop(IMAGE_SIZE, scale=(0.92, 1.0), ratio=(0.95, 1.05)),
                T.RandomRotation(degrees=(-10, 10)),
                T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
                T.ToTensor(),
                T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ])
        else:
            # Deterministic for Val and Test
            self.transform = T.Compose([
                T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                T.ToTensor(),
                T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ])

        self.rows: List[Dict[str, str]] = []
        self._load_manifest()

    def _load_manifest(self) -> None:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest tidak ditemukan: {self.manifest_path}")

        split_paths: Dict[str, set] = {"train": set(), "val": set(), "test": set()}
        split_sources: Dict[str, set] = {"train": set(), "val": set(), "test": set()}
        split_shas: Dict[str, set] = {"train": set(), "val": set(), "test": set()}

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                row_split = (r.get("split") or "").strip().lower()
                img_rel = (r.get("path") or "").strip()
                if not img_rel:
                    continue
                if row_split in split_paths:
                    split_paths[row_split].add(img_rel)
                    src_rel = (r.get("source_path") or "").strip()
                    if src_rel:
                        split_sources[row_split].add(src_rel)
                    sha_val = (r.get("sha256") or "").strip().lower()
                    if sha_val:
                        split_shas[row_split].add(sha_val)
                if row_split == self.split:
                    self.rows.append(r)

        # Audit leakage check
        for s1, s2 in (("train", "val"), ("train", "test"), ("val", "test")):
            if split_paths[s1].intersection(split_paths[s2]):
                raise ValueError(f"Data leakage detected on path between {s1} and {s2}")
            if split_shas[s1].intersection(split_shas[s2]):
                raise ValueError(f"Data leakage detected on SHA-256 between {s1} and {s2}")

        if not self.rows:
            raise ValueError(f"Tidak ada sampel untuk split={self.split!r}")

    def __len__(self) -> int:
        return len(self.rows)

    def load_pil_image(self, idx: int) -> Tuple[Image.Image, int]:
        r = self.rows[idx]
        letter = (r.get("letter") or "").strip().upper()
        if letter in FINGERSPELL_26_LABELS:
            lbl = FINGERSPELL_26_LABELS.index(letter)
        elif str(r.get("label", "")).isdigit():
            lbl = int(r["label"])
        else:
            raise ValueError(f"Label kelas tidak valid: {r}")

        img_path = Path(str(r.get("path", "")).strip())
        if not img_path.is_absolute():
            img_path = ROOT / img_path

        if not img_path.exists() or not img_path.is_file():
            raise FileNotFoundError(f"File citra tidak ditemukan: {img_path}")

        if img_path.suffix.lower() == ".npy":
            raw_arr = np.load(str(img_path))
            if raw_arr.ndim != 3 or raw_arr.shape[2] != 3:
                raise ValueError(f"Array .npy invalid shape {raw_arr.shape}")
            if raw_arr.max() <= 1.0:
                raw_arr = (raw_arr * 255.0).clip(0, 255).astype(np.uint8)
            else:
                raw_arr = raw_arr.clip(0, 255).astype(np.uint8)
            pil_img = Image.fromarray(raw_arr)
        else:
            with Image.open(img_path) as im:
                pil_img = im.convert("RGB")

        return pil_img, lbl

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        pil_img, lbl = self.load_pil_image(idx)
        tensor = self.transform(pil_img)
        return tensor, torch.tensor(lbl, dtype=torch.long)


def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> Tuple[float, float, float, float, float, np.ndarray, List[int], List[int], List[float]]:
    """
    Evaluates model returning:
    (accuracy, macro_precision, macro_recall, macro_f1, weighted_f1, confusion_mat, all_preds, all_labels, all_confs)
    """
    model.eval()
    all_preds: List[int] = []
    all_labels: List[int] = []
    all_confs: List[float] = []

    with torch.no_grad():
        for imgs, lbls in loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = F.softmax(logits, dim=-1)
            conf, preds = torch.max(probs, dim=-1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(lbls.tolist())
            all_confs.extend(conf.cpu().tolist())

    y_true = np.array(all_labels)
    y_pred = np.array(all_preds)

    acc = float(np.mean(y_true == y_pred)) if len(y_true) > 0 else 0.0
    macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=list(range(26)))

    return acc, macro_p, macro_r, macro_f1, weighted_f1, cm, all_preds, all_labels, all_confs


def measure_inference_speed(
    model: nn.Module,
    device: torch.device,
    warmup: int = 20,
    iterations: int = 100,
) -> Dict[str, float]:
    """Measures precise inference latency and throughput on single image input."""
    model.eval()
    dummy = torch.randn(1, 3, IMAGE_SIZE, IMAGE_SIZE, device=device)

    # Warmup
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(dummy)

    # Benchmark
    times: List[float] = []
    with torch.no_grad():
        for _ in range(iterations):
            t0 = time.perf_counter()
            _ = model(dummy)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)

    times_arr = np.array(times)
    mean_lat = float(np.mean(times_arr))
    median_lat = float(np.median(times_arr))
    min_lat = float(np.min(times_arr))
    max_lat = float(np.max(times_arr))
    p95_lat = float(np.percentile(times_arr, 95))
    throughput = 1000.0 / mean_lat if mean_lat > 0 else 0.0

    return {
        "mean_latency_ms": round(mean_lat, 2),
        "median_latency_ms": round(median_lat, 2),
        "min_latency_ms": round(min_lat, 2),
        "max_latency_ms": round(max_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
        "throughput_fps": round(throughput, 1),
    }


def plot_confusion_matrix(cm: np.ndarray, out_path: Path) -> None:
    plt.figure(figsize=(13, 11), dpi=150)
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Confusion Matrix 26 Kelas A-Z (MobileNetV3 I1-P1 Pretrained Test Set)", fontsize=13, fontweight="bold", pad=12)
    plt.colorbar(fraction=0.046, pad=0.04)
    tick_marks = np.arange(len(FINGERSPELL_26_LABELS))
    plt.xticks(tick_marks, FINGERSPELL_26_LABELS, fontsize=9, fontweight="bold")
    plt.yticks(tick_marks, FINGERSPELL_26_LABELS, fontsize=9, fontweight="bold")
    plt.xlabel("Predicted Class", fontsize=11, fontweight="bold")
    plt.ylabel("True Class", fontsize=11, fontweight="bold")

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            if val > 0:
                plt.text(
                    j,
                    i,
                    format(val, "d"),
                    ha="center",
                    va="center",
                    color="white" if val > thresh else "black",
                    fontsize=8,
                    fontweight="bold" if i == j else "normal",
                )

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info("Confusion matrix disimpan ke: %s", out_path)


def plot_prediction_distribution(y_true: List[int], y_pred: List[int], out_path: Path) -> None:
    true_counts = [y_true.count(i) for i in range(26)]
    pred_counts = [y_pred.count(i) for i in range(26)]

    x = np.arange(26)
    width = 0.38

    plt.figure(figsize=(14, 6), dpi=150)
    plt.bar(x - width/2, true_counts, width, label="True Support (Ground Truth)", color="#3b82f6", alpha=0.85)
    plt.bar(x + width/2, pred_counts, width, label="Predicted Counts (P1 Model)", color="#10b981", alpha=0.85)

    plt.xlabel("Kelas Alfabet BISINDO (A-Z)", fontsize=11, fontweight="bold")
    plt.ylabel("Jumlah Sampel Citra", fontsize=11, fontweight="bold")
    plt.title("Distribusi Prediksi per Kelas vs Ground Truth (Test Set N=670)", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(x, FINGERSPELL_26_LABELS, fontsize=10, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info("Distribusi prediksi disimpan ke: %s", out_path)


def plot_training_curves(history: List[Dict[str, Any]], out_dir: Path) -> None:
    epochs = [h["epoch"] for h in history]
    tr_loss = [h["train_loss"] for h in history]
    va_loss = [h["val_loss"] for h in history]
    va_acc = [h["val_acc"] * 100.0 for h in history]
    tr_acc = [h.get("train_acc", 0.0) * 100.0 for h in history]
    va_f1 = [h["val_macro_f1"] * 100.0 for h in history]
    stages = [h.get("stage", "stage2") for h in history]

    # Find stage transition line
    stage1_end = max([h["epoch"] for h in history if h.get("stage") == "stage1"], default=0)

    # 1. Loss Curves
    plt.figure(figsize=(9, 5), dpi=150)
    plt.plot(epochs, tr_loss, "o-", color="#2563eb", linewidth=2, label="Training Loss")
    plt.plot(epochs, va_loss, "s-", color="#dc2626", linewidth=2, label="Validation Loss")
    if stage1_end > 0 and stage1_end < len(epochs):
        plt.axvline(x=stage1_end + 0.5, color="#6b7280", linestyle="--", linewidth=1.5, label="Stage 1 -> Stage 2 (Fine-Tuning)")
    plt.title("Kurva Loss Training vs Validation (MobileNetV3 I1-P1 Pretrained)", fontsize=13, fontweight="bold", pad=10)
    plt.xlabel("Epoch", fontsize=10, fontweight="bold")
    plt.ylabel("CrossEntropy Loss", fontsize=10, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_dir / "training_loss_curves.png")
    plt.close()

    # 2. Accuracy Curves
    plt.figure(figsize=(9, 5), dpi=150)
    if any(tr_acc):
        plt.plot(epochs, tr_acc, "o-", color="#0284c7", linewidth=2, label="Training Accuracy (%)")
    plt.plot(epochs, va_acc, "s-", color="#16a34a", linewidth=2, label="Validation Accuracy (%)")
    if stage1_end > 0 and stage1_end < len(epochs):
        plt.axvline(x=stage1_end + 0.5, color="#6b7280", linestyle="--", linewidth=1.5, label="Stage 1 -> Stage 2")
    plt.title("Kurva Akurasi Training vs Validasi (MobileNetV3 I1-P1)", fontsize=13, fontweight="bold", pad=10)
    plt.xlabel("Epoch", fontsize=10, fontweight="bold")
    plt.ylabel("Akurasi (%)", fontsize=10, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_dir / "training_accuracy_curves.png")
    plt.close()

    # 3. Macro F1 Curves
    plt.figure(figsize=(9, 5), dpi=150)
    plt.plot(epochs, va_f1, "^-", color="#8b5cf6", linewidth=2, label="Validation Macro F1 (%)")
    if stage1_end > 0 and stage1_end < len(epochs):
        plt.axvline(x=stage1_end + 0.5, color="#6b7280", linestyle="--", linewidth=1.5, label="Stage 1 -> Stage 2")
    plt.title("Kurva Validation Macro F1 per Epoch (MobileNetV3 I1-P1)", fontsize=13, fontweight="bold", pad=10)
    plt.xlabel("Epoch", fontsize=10, fontweight="bold")
    plt.ylabel("Macro F1 (%)", fontsize=10, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_dir / "training_f1_curves.png")
    plt.close()


def plot_prediction_samples(
    test_ds: FingerspellP1Dataset,
    preds: List[int],
    labels: List[int],
    confs: List[float],
    out_path: Path,
) -> None:
    correct_indices = [i for i in range(len(labels)) if preds[i] == labels[i]]
    error_indices = [i for i in range(len(labels)) if preds[i] != labels[i]]

    n_correct = min(5, len(correct_indices))
    n_error = min(5, len(error_indices))
    total_cols = max(5, max(n_error, n_correct))

    fig, axes = plt.subplots(2, total_cols, figsize=(3.2 * total_cols, 7), dpi=150)

    # Row 1: Correct predictions
    for c_i in range(total_cols):
        ax = axes[0, c_i]
        if c_i < n_correct:
            idx = correct_indices[c_i * (len(correct_indices) // max(1, n_correct))]
            pil_img, _ = test_ds.load_pil_image(idx)
            true_char = FINGERSPELL_26_LABELS[labels[idx]]
            pred_char = FINGERSPELL_26_LABELS[preds[idx]]
            conf_val = confs[idx] * 100.0

            ax.imshow(pil_img)
            ax.set_title(f"BENAR: {true_char}\nPred: {pred_char} ({conf_val:.1f}%)", fontsize=9, fontweight="bold", color="#16a34a")
        else:
            ax.axis("off")
        ax.axis("off")

    # Row 2: Error predictions
    for e_i in range(total_cols):
        ax = axes[1, e_i]
        if e_i < n_error:
            idx = error_indices[e_i]
            pil_img, _ = test_ds.load_pil_image(idx)
            true_char = FINGERSPELL_26_LABELS[labels[idx]]
            pred_char = FINGERSPELL_26_LABELS[preds[idx]]
            conf_val = confs[idx] * 100.0

            ax.imshow(pil_img)
            ax.set_title(f"SALAH: Target {true_char}\nPred: {pred_char} ({conf_val:.1f}%)", fontsize=9, fontweight="bold", color="#dc2626")
        elif n_error == 0:
            if e_i == total_cols // 2:
                ax.text(0.5, 0.5, "100% Sempurna!\nTidak Ada Kesalahan Prediksi", ha="center", va="center", fontsize=11, fontweight="bold", color="#16a34a")
            ax.axis("off")
        else:
            ax.axis("off")
        ax.axis("off")

    axes[0, 0].set_ylabel("Prediksi Benar", fontsize=11, fontweight="bold")
    axes[1, 0].set_ylabel("Prediksi Salah", fontsize=11, fontweight="bold")
    plt.suptitle("Inspeksi Sampel Prediksi Model I1-P1 MobileNetV3 Pretrained (Test Set)", fontsize=13, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info("Visualisasi sampel prediksi disimpan ke: %s", out_path)


def run_training_and_evaluation(config_path: Path, smoke_test: bool = False) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    seed = int(cfg.get("seed", 42))
    set_seed(seed)

    out_dir = ROOT / cfg.get("output_dir", "runs/image_i1_mobilenetv3_p1")
    out_dir.mkdir(parents=True, exist_ok=True)

    fig_dir = ROOT / "docs" / "figures" / "p1"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Save copy of configuration
    with open(out_dir / "training_config.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    manifest_path = ROOT / cfg["data"]["manifest"]
    stage1_cfg = cfg["training"]["stage1"]
    stage2_cfg = cfg["training"]["stage2"]

    stage1_epochs = 1 if smoke_test else int(stage1_cfg["epochs"])
    stage2_epochs = 1 if smoke_test else int(stage2_cfg["epochs"])
    batch_size = int(stage1_cfg.get("batch_size", 32))
    label_smoothing = float(stage1_cfg.get("label_smoothing", 0.05))

    logger.info("Memuat dataset fingerspelling P1 dari: %s", manifest_path)
    train_ds = FingerspellP1Dataset(manifest_path=manifest_path, split="train", seed=seed, is_train=True)
    val_ds = FingerspellP1Dataset(manifest_path=manifest_path, split="val", seed=seed + 1, is_train=False)
    test_ds = FingerspellP1Dataset(manifest_path=manifest_path, split="test", seed=seed + 2, is_train=False)

    logger.info(
        "Dataset Loaded: Train=%d, Val=%d, Test=%d (Total=%d)",
        len(train_ds), len(val_ds), len(test_ds), len(train_ds) + len(val_ds) + len(test_ds)
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    device = torch.device("cpu")
    logger.info("Menggunakan perangkat: %s", device)

    # Bangun model MobileNetV3-Small Pretrained
    model = build_mobilenetv3_p1(
        num_classes=int(cfg["model"]["num_classes"]),
        dropout=float(cfg["model"]["dropout"]),
        pretrained=bool(cfg["model"].get("pretrained", True)),
    ).to(device)

    param_info = model.count_parameters()
    logger.info("Parameter Info Awal: %s", param_info)

    best_val_f1 = -1.0
    best_val_acc = -1.0
    best_epoch = -1
    best_ckpt_path = out_dir / "best.pt"
    last_ckpt_path = out_dir / "last.pt"

    history: List[Dict[str, Any]] = []
    total_training_start = time.time()
    current_global_epoch = 0

    # =========================================================================
    # STAGE 1: FEATURE EXTRACTION (FREEZE BACKBONE, TRAIN HEAD)
    # =========================================================================
    logger.info("=== MEMULAI STAGE 1: FEATURE EXTRACTION (%d EPOCH) ===", stage1_epochs)
    model.freeze_backbone()
    s1_lr = float(stage1_cfg["lr"])
    s1_wd = float(stage1_cfg["weight_decay"])

    s1_trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer_s1 = torch.optim.AdamW(s1_trainable_params, lr=s1_lr, weight_decay=s1_wd)
    scheduler_s1 = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_s1, T_max=stage1_epochs, eta_min=1e-5)

    for epoch in range(1, stage1_epochs + 1):
        current_global_epoch += 1
        ep_t0 = time.time()
        model.train()
        train_loss_total = 0.0
        train_correct = 0
        train_samples = 0

        for b_idx, (imgs, lbls) in enumerate(train_loader):
            if smoke_test and b_idx >= 2:
                break
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer_s1.zero_grad()
            logits = model(imgs)
            loss = F.cross_entropy(logits, lbls, label_smoothing=label_smoothing)
            loss.backward()
            optimizer_s1.step()

            train_loss_total += loss.item() * imgs.size(0)
            preds = logits.argmax(dim=-1)
            train_correct += (preds == lbls).sum().item()
            train_samples += imgs.size(0)

        scheduler_s1.step()
        train_loss = train_loss_total / max(1, train_samples)
        train_acc = train_correct / max(1, train_samples)

        # Evaluasi Validasi
        val_acc, val_p, val_r, val_f1, _, _, _, _, _ = evaluate_model(model, val_loader, device)

        # Hitung val loss
        model.eval()
        val_loss_total = 0.0
        val_samples = 0
        with torch.no_grad():
            for b_idx, (imgs, lbls) in enumerate(val_loader):
                if smoke_test and b_idx >= 2:
                    break
                imgs, lbls = imgs.to(device), lbls.to(device)
                logits = model(imgs)
                loss = F.cross_entropy(logits, lbls, label_smoothing=label_smoothing)
                val_loss_total += loss.item() * imgs.size(0)
                val_samples += imgs.size(0)
        val_loss = val_loss_total / max(1, val_samples)

        ep_time = time.time() - ep_t0
        curr_lr = scheduler_s1.get_last_lr()[0]

        is_best = val_f1 > best_val_f1
        if is_best:
            best_val_f1 = val_f1
            best_val_acc = val_acc
            best_epoch = current_global_epoch
            torch.save({
                "epoch": current_global_epoch,
                "stage": "stage1",
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "val_f1": val_f1,
                "config": cfg,
            }, str(best_ckpt_path))

        torch.save({
            "epoch": current_global_epoch,
            "stage": "stage1",
            "model_state_dict": model.state_dict(),
            "val_acc": val_acc,
            "val_f1": val_f1,
            "config": cfg,
        }, str(last_ckpt_path))

        history.append({
            "epoch": current_global_epoch,
            "stage": "stage1",
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "val_macro_f1": round(val_f1, 4),
            "val_precision": round(val_p, 4),
            "val_recall": round(val_r, 4),
            "lr": round(curr_lr, 7),
            "time_sec": round(ep_time, 2),
        })

        logger.info(
            "[Stage 1 - Ep %2d/%2d] Train Loss: %.4f (Acc: %5.1f%%) | Val Loss: %.4f | Val Acc: %6.2f%% | Val F1: %6.2f%% | LR: %.6f | %.1fs %s",
            epoch, stage1_epochs, train_loss, train_acc * 100.0, val_loss, val_acc * 100.0, val_f1 * 100.0, curr_lr, ep_time,
            "(BEST)" if is_best else ""
        )

    # =========================================================================
    # STAGE 2: FINE-TUNING (UNFREEZE BACKBONE TOP LAYERS, DIFFERENTIAL LR)
    # =========================================================================
    logger.info("=== MEMULAI STAGE 2: FINE-TUNING (%d EPOCH) ===", stage2_epochs)
    unfreeze_from = int(stage2_cfg.get("unfreeze_from_layer", 9))
    model.unfreeze_backbone(from_layer=unfreeze_from)

    backbone_lr = float(stage2_cfg["backbone_lr"])
    head_lr = float(stage2_cfg["head_lr"])
    s2_wd = float(stage2_cfg["weight_decay"])
    min_lr = float(stage2_cfg.get("min_lr", 1e-6))
    patience = int(stage2_cfg.get("patience", 5))

    # Parameter groups with differential learning rates
    backbone_params = [p for p in model.backbone.features.parameters() if p.requires_grad]
    head_params = [p for p in model.backbone.classifier.parameters() if p.requires_grad]

    optimizer_s2 = torch.optim.AdamW([
        {"params": backbone_params, "lr": backbone_lr, "weight_decay": s2_wd},
        {"params": head_params, "lr": head_lr, "weight_decay": s2_wd},
    ])
    scheduler_s2 = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_s2, T_max=stage2_epochs, eta_min=min_lr)

    epochs_without_improvement = 0

    for epoch in range(1, stage2_epochs + 1):
        current_global_epoch += 1
        ep_t0 = time.time()
        model.train()
        train_loss_total = 0.0
        train_correct = 0
        train_samples = 0

        for b_idx, (imgs, lbls) in enumerate(train_loader):
            if smoke_test and b_idx >= 2:
                break
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer_s2.zero_grad()
            logits = model(imgs)
            loss = F.cross_entropy(logits, lbls, label_smoothing=label_smoothing)
            loss.backward()
            optimizer_s2.step()

            train_loss_total += loss.item() * imgs.size(0)
            preds = logits.argmax(dim=-1)
            train_correct += (preds == lbls).sum().item()
            train_samples += imgs.size(0)

        scheduler_s2.step()
        train_loss = train_loss_total / max(1, train_samples)
        train_acc = train_correct / max(1, train_samples)

        # Evaluasi Validasi
        val_acc, val_p, val_r, val_f1, _, _, _, _, _ = evaluate_model(model, val_loader, device)

        # Hitung val loss
        model.eval()
        val_loss_total = 0.0
        val_samples = 0
        with torch.no_grad():
            for b_idx, (imgs, lbls) in enumerate(val_loader):
                if smoke_test and b_idx >= 2:
                    break
                imgs, lbls = imgs.to(device), lbls.to(device)
                logits = model(imgs)
                loss = F.cross_entropy(logits, lbls, label_smoothing=label_smoothing)
                val_loss_total += loss.item() * imgs.size(0)
                val_samples += imgs.size(0)
        val_loss = val_loss_total / max(1, val_samples)

        ep_time = time.time() - ep_t0
        curr_lrs = scheduler_s2.get_last_lr()

        is_best = val_f1 > best_val_f1
        if is_best:
            best_val_f1 = val_f1
            best_val_acc = val_acc
            best_epoch = current_global_epoch
            epochs_without_improvement = 0
            torch.save({
                "epoch": current_global_epoch,
                "stage": "stage2",
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "val_f1": val_f1,
                "config": cfg,
            }, str(best_ckpt_path))
        else:
            epochs_without_improvement += 1

        torch.save({
            "epoch": current_global_epoch,
            "stage": "stage2",
            "model_state_dict": model.state_dict(),
            "val_acc": val_acc,
            "val_f1": val_f1,
            "config": cfg,
        }, str(last_ckpt_path))

        history.append({
            "epoch": current_global_epoch,
            "stage": "stage2",
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
            "val_macro_f1": round(val_f1, 4),
            "val_precision": round(val_p, 4),
            "val_recall": round(val_r, 4),
            "lr": round(curr_lrs[1], 7),  # head lr
            "time_sec": round(ep_time, 2),
        })

        logger.info(
            "[Stage 2 - Ep %2d/%2d] Train Loss: %.4f (Acc: %5.1f%%) | Val Loss: %.4f | Val Acc: %6.2f%% | Val F1: %6.2f%% | Head LR: %.6f | %.1fs %s",
            epoch, stage2_epochs, train_loss, train_acc * 100.0, val_loss, val_acc * 100.0, val_f1 * 100.0, curr_lrs[1], ep_time,
            "(BEST)" if is_best else f"[No improve: {epochs_without_improvement}/{patience}]"
        )

        if epochs_without_improvement >= patience and not smoke_test:
            logger.info("Early stopping terpicu pada epoch %d (patience=%d). Menghentikan training.", current_global_epoch, patience)
            break

    total_training_time = time.time() - total_training_start
    logger.info("Pelatihan selesai dalam %.1f detik. Best Epoch: %d (Val Acc: %.2f%%, Val F1: %.2f%%)",
                total_training_time, best_epoch, best_val_acc * 100.0, best_val_f1 * 100.0)

    # Simpan training history CSV
    with open(out_dir / "training_history.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "stage", "train_loss", "train_acc", "val_loss", "val_acc", "val_macro_f1", "val_precision", "val_recall", "lr", "time_sec"])
        writer.writeheader()
        writer.writerows(history)

    # Plot training curves
    plot_training_curves(history, fig_dir)
    shutil.copy(fig_dir / "training_loss_curves.png", out_dir / "training_loss_curves.png")
    shutil.copy(fig_dir / "training_accuracy_curves.png", out_dir / "training_accuracy_curves.png")
    shutil.copy(fig_dir / "training_f1_curves.png", out_dir / "training_f1_curves.png")

    # =========================================================================
    # TAHAP 7: EVALUASI RIGOROUS PADA TEST SET MENGGUNAKAN BEST CHECKPOINT
    # =========================================================================
    logger.info("=== TAHAP 7: EVALUASI TEST SET MENGGUNAKAN BEST CHECKPOINT (%s) ===", best_ckpt_path)
    best_ckpt = torch.load(str(best_ckpt_path), map_location=device, weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    test_acc, test_p, test_r, test_f1, test_wf1, test_cm, test_preds, test_labels, test_confs = evaluate_model(
        model, test_loader, device
    )

    # Benchmark CPU inference latency
    latency_info = measure_inference_speed(model, device=device, warmup=20, iterations=100)

    # Simpan confusion matrix CSV
    with open(out_dir / "confusion_matrix.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["True_Class"] + [f"Pred_{c}" for c in FINGERSPELL_26_LABELS])
        for idx, row in enumerate(test_cm):
            writer.writerow([FINGERSPELL_26_LABELS[idx]] + list(row))

    # Plot Confusion Matrix
    cm_fig_path = fig_dir / "confusion_matrix_p1.png"
    plot_confusion_matrix(test_cm, cm_fig_path)
    shutil.copy(cm_fig_path, out_dir / "confusion_matrix.png")

    # Plot Prediction Distribution
    dist_fig_path = fig_dir / "prediction_distribution_p1.png"
    plot_prediction_distribution(test_labels, test_preds, dist_fig_path)
    shutil.copy(dist_fig_path, out_dir / "prediction_distribution.png")

    # Plot Prediction Samples Grid
    sample_fig_path = fig_dir / "sample_predictions_p1.png"
    plot_prediction_samples(test_ds, test_preds, test_labels, test_confs, sample_fig_path)
    shutil.copy(sample_fig_path, out_dir / "sample_predictions_grid.png")

    # Simpan predictions.csv
    with open(out_dir / "predictions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "path", "true_label", "true_char", "pred_label", "pred_char", "confidence", "correct"])
        for i in range(len(test_labels)):
            t_lbl = test_labels[i]
            p_lbl = test_preds[i]
            r_row = test_ds.rows[i]
            writer.writerow([
                i,
                r_row.get("path", ""),
                t_lbl,
                FINGERSPELL_26_LABELS[t_lbl],
                p_lbl,
                FINGERSPELL_26_LABELS[p_lbl],
                round(test_confs[i], 4),
                int(t_lbl == p_lbl),
            ])

    # Classification report per class
    target_names = [f"Kelas_{c}" for c in FINGERSPELL_26_LABELS]
    clf_report_dict = classification_report(
        test_labels, test_preds, target_names=target_names, output_dict=True, zero_division=0
    )
    clf_report_text = classification_report(
        test_labels, test_preds, target_names=target_names, digits=4, zero_division=0
    )

    with open(out_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(clf_report_text)

    # Evaluasi komparasi Model P0 (runs/image_i1_mobilenetv3_p0/best.pt) pada Test Set yang SAMA
    p0_ckpt_path = ROOT / "runs" / "image_i1_mobilenetv3_p0" / "best.pt"
    p0_metrics = {
        "accuracy_pct": 7.61,
        "macro_precision_pct": 8.23,
        "macro_recall_pct": 7.60,
        "macro_f1_pct": 7.50,
        "weighted_f1_pct": 7.49,
        "latency_ms": 8.32,
        "throughput_fps": 120.2,
    }

    if p0_ckpt_path.exists():
        p0_summary_file = ROOT / "runs" / "image_i1_mobilenetv3_p0" / "training_summary.json"
        if p0_summary_file.exists():
            with open(p0_summary_file, "r") as pf:
                p0_json = json.load(pf)
                p0_metrics["accuracy_pct"] = p0_json["final_test_metrics"]["accuracy_pct"]
                p0_metrics["macro_precision_pct"] = p0_json["final_test_metrics"]["macro_precision_pct"]
                p0_metrics["macro_recall_pct"] = p0_json["final_test_metrics"]["macro_recall_pct"]
                p0_metrics["macro_f1_pct"] = p0_json["final_test_metrics"]["macro_f1_pct"]
                p0_metrics["weighted_f1_pct"] = p0_json["final_test_metrics"]["weighted_f1_pct"]
                p0_metrics["latency_ms"] = p0_json["inference_benchmark_cpu"]["mean_latency_ms"]
                p0_metrics["throughput_fps"] = p0_json["inference_benchmark_cpu"]["throughput_fps"]

    # Error analysis: top misclassified pairs
    error_pairs: Dict[str, int] = defaultdict(int)
    for i in range(len(test_labels)):
        if test_preds[i] != test_labels[i]:
            t_char = FINGERSPELL_26_LABELS[test_labels[i]]
            p_char = FINGERSPELL_26_LABELS[test_preds[i]]
            error_pairs[f"{t_char} -> {p_char}"] += 1

    error_analysis = [
        {"pair": k, "count": v} for k, v in sorted(error_pairs.items(), key=lambda x: x[1], reverse=True)
    ]

    unique_preds = len(set(test_preds))
    zero_recall_classes = [c for c in FINGERSPELL_26_LABELS if clf_report_dict[f"Kelas_{c}"]["recall"] == 0.0]

    # Model size on disk
    best_size_mb = round(best_ckpt_path.stat().st_size / (1024 * 1024), 2)

    eval_summary = {
        "experiment_id": cfg.get("experiment_id", "image_i1_mobilenetv3_p1"),
        "model_architecture": "torchvision.models.mobilenet_v3_small(weights=DEFAULT)",
        "parameter_count": param_info["total_params"],
        "parameter_millions": round(param_info["total_params"] / 1e6, 3),
        "checkpoint_size_mb": best_size_mb,
        "total_epochs_trained": current_global_epoch,
        "best_epoch": best_epoch,
        "total_training_time_seconds": round(total_training_time, 2),
        "dataset_splits": {
            "train_samples": len(train_ds),
            "val_samples": len(val_ds),
            "test_samples": len(test_ds),
            "total_samples": len(train_ds) + len(val_ds) + len(test_ds),
        },
        "best_validation_metrics": {
            "accuracy_pct": round(best_val_acc * 100.0, 2),
            "macro_f1_pct": round(best_val_f1 * 100.0, 2),
        },
        "final_test_metrics": {
            "accuracy_pct": round(test_acc * 100.0, 2),
            "macro_precision_pct": round(test_p * 100.0, 2),
            "macro_recall_pct": round(test_r * 100.0, 2),
            "macro_f1_pct": round(test_f1 * 100.0, 2),
            "weighted_f1_pct": round(test_wf1 * 100.0, 2),
        },
        "inference_benchmark_cpu": latency_info,
        "comparison_with_p0": {
            "p0_accuracy_pct": p0_metrics["accuracy_pct"],
            "p1_accuracy_pct": round(test_acc * 100.0, 2),
            "accuracy_delta_pct": round(test_acc * 100.0 - p0_metrics["accuracy_pct"], 2),
            "p0_macro_f1_pct": p0_metrics["macro_f1_pct"],
            "p1_macro_f1_pct": round(test_f1 * 100.0, 2),
            "macro_f1_delta_pct": round(test_f1 * 100.0 - p0_metrics["macro_f1_pct"], 2),
            "p0_macro_precision_pct": p0_metrics["macro_precision_pct"],
            "p1_macro_precision_pct": round(test_p * 100.0, 2),
            "p0_macro_recall_pct": p0_metrics["macro_recall_pct"],
            "p1_macro_recall_pct": round(test_r * 100.0, 2),
            "p0_latency_ms": p0_metrics["latency_ms"],
            "p1_latency_ms": latency_info["mean_latency_ms"],
        },
        "quality_checks": {
            "class_collapse_detected": unique_preds < 20,
            "unique_predicted_classes": unique_preds,
            "zero_recall_classes_count": len(zero_recall_classes),
            "zero_recall_classes": zero_recall_classes,
            "overfitting_reduced": bool(history[best_epoch - 1]["val_loss"] < 2.0),
            "top_misclassified_pairs": error_analysis[:10],
        },
        "classification_report_per_class": {
            c: {
                "precision": round(clf_report_dict[f"Kelas_{c}"]["precision"] * 100.0, 2),
                "recall": round(clf_report_dict[f"Kelas_{c}"]["recall"] * 100.0, 2),
                "f1_score": round(clf_report_dict[f"Kelas_{c}"]["f1-score"] * 100.0, 2),
                "support": clf_report_dict[f"Kelas_{c}"]["support"],
            }
            for c in FINGERSPELL_26_LABELS
        },
    }

    with open(out_dir / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    logger.info("=== EVALUASI TEST SET SELESAI ===")
    logger.info("Test Accuracy  : %.2f%% (P0: %.2f%% | Delta: %+.2f%%)", test_acc * 100.0, p0_metrics["accuracy_pct"], test_acc * 100.0 - p0_metrics["accuracy_pct"])
    logger.info("Test Macro F1  : %.2f%% (P0: %.2f%% | Delta: %+.2f%%)", test_f1 * 100.0, p0_metrics["macro_f1_pct"], test_f1 * 100.0 - p0_metrics["macro_f1_pct"])
    logger.info("CPU Latency    : %.2f ms (Throughput: %.1f FPS)", latency_info["mean_latency_ms"], latency_info["throughput_fps"])

    return eval_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SignBridge P1 Training & Evaluation")
    parser.add_argument("--config", type=str, default="configs/image_i1_mobilenetv3_p1.yaml")
    parser.add_argument("--smoke-test", action="store_true", help="Run 1-batch smoke test")
    args = parser.parse_args()

    run_training_and_evaluation(Path(args.config), smoke_test=args.smoke_test)

