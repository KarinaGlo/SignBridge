"""
scripts/validation_p1/evaluate_external_images.py
Validation pipeline for evaluating P1 MobileNetV3-Small on external/unseen BISINDO images.
Strictly non-destructive; performs evaluation only without any training or weight updates.
Hardened with informed consent verification (CONSENT_SIGNED) and consistent signer_id tracking.
Multi-fallback path resolution matching tracker logic (GAP-03).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
import torch
import torchvision.transforms as T

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD
from signbridge.image.models.mobilenetv3_p1 import build_mobilenetv3_p1

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("external_evaluator")


def resolve_signer_id(row: Dict[str, str]) -> str:
    """Explicit compatibility mapping for signer identity.
    Prefers 'signer_id'. Falls back to 'subject_id' if 'signer_id' is missing or blank.
    Guarantees a single canonical ID per sample to prevent duplicate counting.
    """
    sid = (row.get("signer_id") or "").strip()
    if not sid:
        sid = (row.get("subject_id") or "").strip()
    return sid if sid else "UNKNOWN_SIGNER"


def resolve_image_path(raw_path: str, data_dir: Optional[Path] = None) -> Path:
    """Resolves an image path supporting three formats with explicit priority:
    1. Absolute path: used directly.
    2. Relative to data_dir: checked first for relative paths (if data_dir provided).
    3. Relative to ROOT: checked second if not found in data_dir.
    4. Unresolved fallback:
       - If path starts with 'data/' -> candidate is ROOT / path
       - Otherwise -> candidate is (data_dir / path) if data_dir else (ROOT / path)

    Always returns a normalized resolved Path object.
    """
    raw_str = raw_path.strip()
    p = Path(raw_str)

    if p.is_absolute():
        return p.resolve()

    if data_dir is not None:
        if not data_dir.is_absolute():
            data_dir = ROOT / data_dir
        cand_data = data_dir / p
        if cand_data.exists():
            return cand_data.resolve()
    else:
        cand_data = None

    cand_root = ROOT / p
    if cand_root.exists():
        return cand_root.resolve()

    clean_posix = p.as_posix()
    if clean_posix.startswith("data/"):
        return cand_root.resolve()
    if cand_data is not None:
        return cand_data.resolve()
    return cand_root.resolve()


def load_p1_model(checkpoint_path: Path, device: torch.device) -> torch.nn.Module:
    """Loads P1 MobileNetV3-Small without modifying checkpoint."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint P1 tidak ditemukan di: {checkpoint_path}")

    model = build_mobilenetv3_p1(num_classes=26, pretrained=False)
    ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    logger.info("Model P1 berhasil dimuat dari %s (Perangkat: %s)", checkpoint_path, device)
    return model


def preprocess_image(img_path: Path) -> torch.Tensor:
    """Standardized deterministic preprocessing identical to P1 inference."""
    transform = T.Compose([
        T.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    if img_path.suffix.lower() == ".npy":
        arr = np.load(str(img_path))
        if arr.max() <= 1.0:
            arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
        else:
            arr = arr.clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(arr).convert("RGB")
    else:
        with Image.open(img_path) as im:
            pil_img = im.convert("RGB")

    return transform(pil_img).unsqueeze(0)  # [1, 3, 224, 224]


def evaluate_external_dataset(
    manifest_path: Path,
    checkpoint_path: Path,
    out_dir: Path,
    device: Optional[torch.device] = None,
    model: Optional[torch.nn.Module] = None,
    data_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Evaluates an external manifest of unseen images.

    Hardened rules:
    1. Consent check is performed first: rows without exact consent_status == 'CONSENT_SIGNED'
       are immediately rejected and never reach image loading, preprocessing, or model inference.
    2. 'signer_id' is used consistently for grouping and predictions output.
    3. Multi-fallback path resolution (GAP-03) matching tracker logic.
    """
    if device is None:
        device = torch.device("cpu")

    out_dir.mkdir(parents=True, exist_ok=True)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest eksternal tidak ditemukan: {manifest_path}")

    if data_dir is None:
        data_dir = manifest_path.parent

    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        logger.warning("Manifest eksternal kosong. Status: PENDING EXTERNAL DATA.")
        summary = {
            "status": "PENDING EXTERNAL DATA",
            "message": "Tidak ada baris data di dalam manifest eksternal.",
            "manifest": str(manifest_path),
            "total_manifest_rows": 0,
            "total_evaluated_samples": 0,
            "total_rejected_samples": 0,
            "rejected_counts": {
                "consent_invalid": 0,
                "file_not_found": 0,
                "invalid_label": 0,
            },
        }
        with open(out_dir / "external_validation_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    if model is None:
        model = load_p1_model(checkpoint_path, device)
    else:
        model.to(device)
        model.eval()

    results: List[Dict[str, Any]] = []
    y_true: List[int] = []
    y_pred: List[int] = []
    confs: List[float] = []

    rejected_counts = {
        "consent_invalid": 0,
        "file_not_found": 0,
        "invalid_label": 0,
    }

    logger.info("Mengevaluasi %d baris manifest eksternal...", len(reader))
    start_t = time.time()

    valid_manifest_rows = 0
    for idx, row in enumerate(reader):
        raw_p = (row.get("image_path") or row.get("path") or "").strip()
        if not raw_p or raw_p.startswith("#"):
            continue

        valid_manifest_rows += 1

        # 1. HARD REJECT: Informed Consent check BEFORE any image I/O or model inference
        consent_status = (row.get("consent_status") or "").strip()
        if consent_status != "CONSENT_SIGNED":
            logger.warning(
                "Baris %d ditolak: consent_status ('%s') tidak valid (wajib persis 'CONSENT_SIGNED'). Data tidak akan diproses ke inferensi.",
                idx,
                consent_status,
            )
            rejected_counts["consent_invalid"] += 1
            continue

        # 2. File existence check via standardized multi-fallback resolver (GAP-03)
        p = resolve_image_path(raw_p, data_dir=data_dir)

        if not p.exists():
            logger.warning("Citra tidak ditemukan di disk pada baris %d: %s", idx, p)
            rejected_counts["file_not_found"] += 1
            continue

        # 3. Label validation
        lbl_str = (row.get("label") or "").strip().upper()
        if lbl_str in FINGERSPELL_26_LABELS:
            t_idx = FINGERSPELL_26_LABELS.index(lbl_str)
        elif lbl_str.isdigit() and 0 <= int(lbl_str) < len(FINGERSPELL_26_LABELS):
            t_idx = int(lbl_str)
        else:
            logger.warning("Label tidak valid untuk baris %d: '%s'", idx, lbl_str)
            rejected_counts["invalid_label"] += 1
            continue

        # 4. Canonical Signer ID resolution
        signer_id = resolve_signer_id(row)

        # 5. Preprocessing and inference (only uncompromised, consented data reaches here)
        inp_tensor = preprocess_image(p).to(device)
        with torch.inference_mode():
            logits = model(inp_tensor)
            probs = torch.softmax(logits, dim=-1)
            conf_val, p_idx = torch.max(probs, dim=-1)

        p_idx_int = int(p_idx.item())
        conf_float = float(conf_val.item())

        y_true.append(t_idx)
        y_pred.append(p_idx_int)
        confs.append(conf_float)

        results.append({
            "index": idx,
            "image_path": str(p),
            "true_label": t_idx,
            "true_char": FINGERSPELL_26_LABELS[t_idx],
            "pred_label": p_idx_int,
            "pred_char": FINGERSPELL_26_LABELS[p_idx_int],
            "confidence": round(conf_float, 4),
            "correct": int(t_idx == p_idx_int),
            "signer_id": signer_id,
            "device": (row.get("device") or "").strip(),
            "lighting": (row.get("lighting_condition") or row.get("lighting") or "").strip(),
        })

    eval_time = time.time() - start_t
    total_rejected = sum(rejected_counts.values())

    if not y_true:
        logger.warning("Tidak ada citra eksternal valid yang berhasil dievaluasi.")
        status_msg = "PENDING EXTERNAL DATA" if valid_manifest_rows == 0 else "NO_VALID_DATA"
        detail_msg = (
            "Manifest hanya berisi komentar atau contoh data template. Tidak ada baris data yang dievaluasi."
            if valid_manifest_rows == 0
            else "Tidak ada baris data valid yang lolos validasi (consent/file/label)."
        )
        summary = {
            "status": status_msg,
            "message": detail_msg,
            "total_manifest_rows": len(reader),
            "total_evaluated_samples": 0,
            "total_rejected_samples": total_rejected,
            "rejected_counts": rejected_counts,
        }
        with open(out_dir / "external_validation_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    # Save predictions.csv with canonical signer_id
    pred_csv_path = out_dir / "external_predictions.csv"
    with open(pred_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "index",
            "image_path",
            "true_label",
            "true_char",
            "pred_label",
            "pred_char",
            "confidence",
            "correct",
            "signer_id",
            "device",
            "lighting",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Compute metrics on classes actually present in the external data
    present_classes = sorted(list(set(y_true)))
    acc = float(accuracy_score(y_true, y_pred))
    macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    target_names = [f"Kelas_{FINGERSPELL_26_LABELS[c]}" for c in present_classes]
    clf_report_text = classification_report(
        y_true, y_pred, labels=present_classes, target_names=target_names, digits=4, zero_division=0
    )

    with open(out_dir / "external_classification_report.txt", "w", encoding="utf-8") as f:
        f.write(clf_report_text)

    # Per-signer performance breakdown strictly grouped by signer_id
    signer_data = defaultdict(lambda: {"true": [], "pred": []})
    for r in results:
        sid = r["signer_id"]
        signer_data[sid]["true"].append(r["true_label"])
        signer_data[sid]["pred"].append(r["pred_label"])

    signer_metrics = {}
    for sid, svals in signer_data.items():
        s_acc = float(accuracy_score(svals["true"], svals["pred"]))
        s_f1 = float(f1_score(svals["true"], svals["pred"], average="macro", zero_division=0))
        signer_metrics[sid] = {
            "samples": len(svals["true"]),
            "accuracy_pct": round(s_acc * 100.0, 2),
            "macro_f1_pct": round(s_f1 * 100.0, 2),
        }

    summary = {
        "status": "EVALUATED",
        "checkpoint": str(checkpoint_path),
        "total_manifest_rows": len(reader),
        "total_evaluated_samples": len(y_true),
        "total_rejected_samples": total_rejected,
        "rejected_counts": rejected_counts,
        "unique_classes_present": len(present_classes),
        "present_classes_list": [FINGERSPELL_26_LABELS[c] for c in present_classes],
        "accuracy_pct": round(acc * 100.0, 2),
        "macro_precision_pct": round(macro_p * 100.0, 2),
        "macro_recall_pct": round(macro_r * 100.0, 2),
        "macro_f1_pct": round(macro_f1 * 100.0, 2),
        "per_signer_performance": signer_metrics,
        "evaluation_time_seconds": round(eval_time, 2),
    }

    with open(out_dir / "external_validation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(
        "Evaluasi eksternal selesai: Evaluated=%d, Rejected=%d (Consent=%d), Acc=%.2f%%, Macro F1=%.2f%%",
        len(y_true),
        total_rejected,
        rejected_counts["consent_invalid"],
        acc * 100.0,
        macro_f1 * 100.0,
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate P1 on External Unseen Images")
    parser.add_argument("--manifest", type=str, default="data/external/bisindo_validation/external_manifest_template.csv")
    parser.add_argument("--checkpoint", type=str, default="runs/image_i1_mobilenetv3_p1/best.pt")
    parser.add_argument("--out-dir", type=str, default="runs/image_i1_mobilenetv3_p1/external_validation")
    parser.add_argument("--data-dir", type=str, default=None)
    args = parser.parse_args()

    data_dir_arg = Path(args.data_dir) if args.data_dir else None
    evaluate_external_dataset(Path(args.manifest), Path(args.checkpoint), Path(args.out_dir), data_dir=data_dir_arg)
