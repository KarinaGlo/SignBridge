"""
evaluate.py — Comprehensive Run Evaluation, Per-Signer Analysis, Gate Analysis,
Confusion Matrix, & Error Report Generator (Bab 6.4 - 6.6 Modul Gloria).

Usage:
  python -m signbridge.evaluate --run runs/03_fusion_bisindo

Generates inside the run folder:
  - metrics.json         : accuracy, top-5, macro-F1, per-signer accuracy,
                           mean_confidence_correct, mean_confidence_wrong,
                           top_confusions (top 10 confused gloss pairs),
                           gate_per_gloss (if fusion model)
  - confusion_matrix.png : Visual confusion matrix heatmap
  - report.txt           : Human-readable evaluation summary for Bab IV
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from signbridge.constants import BISINDO_32_GLOSSES


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp_v = np.exp(shifted)
    return exp_v / np.sum(exp_v, axis=-1, keepdims=True)


def evaluate_run_dir(run_dir: str | Path) -> Dict[str, Any]:
    run_dir = Path(run_dir)
    npz_path = run_dir / "test_predictions.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Prediction file not found: {npz_path}")

    with np.load(str(npz_path), allow_pickle=True) as data:
        logits = data["logits"].astype(np.float32)
        preds = data["preds"].astype(np.int64)
        labels = data["labels"].astype(np.int64)
        signers = [str(s) for s in data["signers"]]
        gates = data["gates"].astype(np.float32) if "gates" in data else np.zeros((0,), dtype=np.float32)
        classes = [str(c) for c in data["classes"]] if "classes" in data else list(BISINDO_32_GLOSSES)

    num_classes = len(classes) if len(classes) > 0 else int(logits.shape[1])
    probs = _softmax(logits)
    confidences = np.max(probs, axis=-1)

    correct_mask = preds == labels
    accuracy = float(np.mean(correct_mask)) if len(labels) > 0 else 0.0

    k = min(5, logits.shape[1])
    top_k = np.argsort(logits, axis=1)[:, -k:]
    top5 = float(np.mean([labels[i] in top_k[i] for i in range(len(labels))])) if len(labels) > 0 else 0.0

    # Per-gloss F1 & Macro-F1
    per_gloss_f1: Dict[str, float] = {}
    f1_list: List[float] = []
    for c in range(num_classes):
        g_name = classes[c] if c < len(classes) else f"class_{c}"
        tp = float(np.sum((preds == c) & (labels == c)))
        fp = float(np.sum((preds == c) & (labels != c)))
        fn = float(np.sum((preds != c) & (labels == c)))
        denom = 2 * tp + fp + fn
        f1 = (2 * tp / denom) if denom > 0 else 0.0
        per_gloss_f1[g_name] = round(f1, 4)
        if tp + fn > 0:
            f1_list.append(f1)
    macro_f1 = float(np.mean(f1_list)) if f1_list else 0.0

    # Per-signer accuracy
    per_signer: Dict[str, float] = {}
    unique_signers = sorted(set(signers))
    signers_arr = np.array(signers)
    for s in unique_signers:
        s_mask = signers_arr == s
        if np.any(s_mask):
            per_signer[s] = round(float(np.mean(correct_mask[s_mask])), 4)

    # Confidence statistics
    mean_conf_correct = (
        float(np.mean(confidences[correct_mask])) if np.any(correct_mask) else 0.0
    )
    mean_conf_wrong = (
        float(np.mean(confidences[~correct_mask])) if np.any(~correct_mask) else 0.0
    )

    # Confusion matrix & top 10 confused pairs
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for y_true, y_pred in zip(labels, preds):
        if 0 <= y_true < num_classes and 0 <= y_pred < num_classes:
            cm[y_true, y_pred] += 1

    confusion_pairs: List[Tuple[int, str, str]] = []
    for i in range(num_classes):
        for j in range(num_classes):
            if i != j and cm[i, j] > 0:
                true_g = classes[i] if i < len(classes) else f"class_{i}"
                pred_g = classes[j] if j < len(classes) else f"class_{j}"
                confusion_pairs.append((int(cm[i, j]), true_g, pred_g))
    confusion_pairs.sort(key=lambda x: x[0], reverse=True)
    top_confusions = [
        {"true_gloss": tg, "pred_gloss": pg, "count": cnt}
        for cnt, tg, pg in confusion_pairs[:10]
    ]

    # Gate analysis per gloss (pose share g vs RGB share 1-g)
    gate_per_gloss: Dict[str, float] = {}
    if gates.ndim == 2 and len(gates) == len(labels):
        sample_gate_mean = np.mean(gates, axis=-1)
        for c in range(num_classes):
            c_mask = labels == c
            if np.any(c_mask):
                g_name = classes[c] if c < len(classes) else f"class_{c}"
                gate_per_gloss[g_name] = round(float(np.mean(sample_gate_mean[c_mask])), 4)

    metrics = {
        "run": run_dir.name,
        "num_samples": int(len(labels)),
        "num_classes": num_classes,
        "accuracy": round(accuracy, 4),
        "top5": round(top5, 4),
        "macro_f1": round(macro_f1, 4),
        "per_signer": per_signer,
        "mean_confidence_correct": round(mean_conf_correct, 4),
        "mean_confidence_wrong": round(mean_conf_wrong, 4),
        "top_confusions": top_confusions,
        "per_gloss_f1": per_gloss_f1,
        "gate_per_gloss": gate_per_gloss,
    }

    with (run_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # Save confusion_matrix.png
    _save_confusion_matrix_plot(cm, classes, run_dir / "confusion_matrix.png")

    # Save human-readable report.txt
    report_lines = [
        f"SignBridge Evaluation Report — {run_dir.name}",
        "=" * 60,
        f"Samples evaluated        : {len(labels)}",
        f"Top-1 Accuracy           : {accuracy * 100:.2f}%",
        f"Top-5 Accuracy           : {top5 * 100:.2f}%",
        f"Macro-F1                 : {macro_f1 * 100:.2f}%",
        f"Mean Confidence (Correct): {mean_conf_correct:.4f}",
        f"Mean Confidence (Wrong)  : {mean_conf_wrong:.4f}",
        "",
        "Per-Signer Accuracy:",
    ]
    for s, s_acc in per_signer.items():
        report_lines.append(f"  - {s}: {s_acc * 100:.2f}%")

    report_lines.append("")
    report_lines.append("Top Confused Gloss Pairs (True -> Predicted):")
    if top_confusions:
        for item in top_confusions:
            report_lines.append(
                f"  - {item['true_gloss']} -> {item['pred_gloss']} : {item['count']}x"
            )
    else:
        report_lines.append("  (No misclassifications)")

    (run_dir / "report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"[evaluate] Saved metrics.json, confusion_matrix.png, report.txt to {run_dir}")
    return metrics


def _save_confusion_matrix_plot(cm: np.ndarray, classes: List[str], out_path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 8), dpi=120)
        im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
        fig.colorbar(im, ax=ax)
        ax.set_title("SignBridge Confusion Matrix")
        ax.set_xlabel("Predicted Gloss")
        ax.set_ylabel("True Gloss")
        if len(classes) <= 35:
            ticks = np.arange(len(classes))
            ax.set_xticks(ticks)
            ax.set_yticks(ticks)
            ax.set_xticklabels(classes, rotation=90, fontsize=7)
            ax.set_yticklabels(classes, fontsize=7)
        fig.tight_layout()
        fig.savefig(str(out_path))
        plt.close(fig)
    except Exception:
        # Fallback minimal 1x1 PNG if matplotlib is unavailable
        minimal_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        out_path.write_bytes(minimal_png)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="SignBridge Evaluation CLI")
    parser.add_argument("--run", type=str, required=True, help="Path to run directory (e.g. runs/03_fusion_bisindo)")
    args = parser.parse_args(argv)
    evaluate_run_dir(args.run)


if __name__ == "__main__":
    main()

