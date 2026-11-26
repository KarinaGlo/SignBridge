"""
scripts/validation_p1/generate_audit_figures.py
Generates comprehensive diagnostic visual figures for P1 audit:
- Confidence score distribution (correct vs incorrect)
- Calibration curve (Reliability diagram with ECE)
- Per-class accuracy comparison
- Top confused pairs bar chart
"""

from __future__ import annotations

import csv
from collections import defaultdict
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix

from signbridge.constants import FINGERSPELL_26_LABELS

FIGURES_DIR = ROOT / "docs" / "validation_p1" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PRED_FILE = ROOT / "runs" / "image_i1_mobilenetv3_p1" / "predictions.csv"


def generate_figures():
    with open(PRED_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    true_labels = np.array([int(r["true_label"]) for r in rows])
    pred_labels = np.array([int(r["pred_label"]) for r in rows])
    confs = np.array([float(r["confidence"]) for r in rows])
    corrects = np.array([int(r["correct"]) for r in rows])

    correct_mask = (corrects == 1)
    incorrect_mask = (corrects == 0)

    # =========================================================================
    # 1. CONFIDENCE DISTRIBUTION (CORRECT VS INCORRECT)
    # =========================================================================
    plt.figure(figsize=(10, 5), dpi=150)
    bins = np.linspace(0.0, 1.0, 21)
    plt.hist(confs[correct_mask], bins=bins, alpha=0.7, color="#10b981", label=f"Prediksi Benar (N={correct_mask.sum()})", edgecolor="black")
    plt.hist(confs[incorrect_mask], bins=bins, alpha=0.7, color="#ef4444", label=f"Prediksi Salah (N={incorrect_mask.sum()})", edgecolor="black")
    plt.xlabel("Confidence Score (Probabilitas Logit Max)", fontsize=11, fontweight="bold")
    plt.ylabel("Frekuensi Jumlah Sampel", fontsize=11, fontweight="bold")
    plt.title("Distribusi Skor Keyakinan (Confidence) Prediksi Benar vs Salah (Test Set N=670)", fontsize=12, fontweight="bold", pad=12)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "confidence_distribution.png")
    plt.close()
    print("Saved confidence_distribution.png")

    # =========================================================================
    # 2. CALIBRATION CURVE (RELIABILITY DIAGRAM & ECE)
    # =========================================================================
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_centers = 0.5 * (bin_boundaries[1:] + bin_boundaries[:-1])
    bin_accs = []
    bin_confs = []
    bin_counts = []
    ece = 0.0

    for i in range(n_bins):
        b_lo = bin_boundaries[i]
        b_hi = bin_boundaries[i + 1]
        mask = (confs > b_lo) & (confs <= b_hi)
        count = mask.sum()
        bin_counts.append(count)
        if count > 0:
            b_acc = float(np.mean(corrects[mask]))
            b_conf = float(np.mean(confs[mask]))
            ece += np.abs(b_conf - b_acc) * (count / len(confs))
            bin_accs.append(b_acc)
            bin_confs.append(b_conf)
        else:
            bin_accs.append(0.0)
            bin_confs.append(bin_centers[i])

    plt.figure(figsize=(7, 6), dpi=150)
    plt.plot([0, 1], [0, 1], "--", color="#6b7280", label="Perfect Calibration (Ideal)")
    plt.plot(bin_confs, bin_accs, "s-", color="#2563eb", linewidth=2.5, markersize=7, label=f"Model P1 (ECE = {ece*100:.2f}%)")
    plt.bar(bin_centers, bin_accs, width=0.08, alpha=0.25, color="#3b82f6", edgecolor="#1d4ed8")
    plt.xlabel("Confidence (Rata-rata)", fontsize=11, fontweight="bold")
    plt.ylabel("Accuracy Aktual", fontsize=11, fontweight="bold")
    plt.title(f"Reliability Diagram (Kalibrasi Model P1)\nECE = {ece*100:.2f}%, Brier Score = {np.mean((confs - corrects)**2):.4f}", fontsize=12, fontweight="bold", pad=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=10, loc="upper left")
    plt.xlim(0, 1.02)
    plt.ylim(0, 1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "calibration_curve.png")
    plt.close()
    print("Saved calibration_curve.png")

    # =========================================================================
    # 3. PER-CLASS ACCURACY
    # =========================================================================
    cm = confusion_matrix(true_labels, pred_labels, labels=list(range(26)))
    per_class_acc = [cm[i, i] / max(1, cm[i, :].sum()) * 100.0 for i in range(26)]

    plt.figure(figsize=(14, 5.5), dpi=150)
    x = np.arange(26)
    colors = ["#10b981" if acc >= 60 else "#f59e0b" if acc >= 40 else "#ef4444" for acc in per_class_acc]
    bars = plt.bar(x, per_class_acc, color=colors, edgecolor="black", alpha=0.85)
    plt.axhline(y=61.19, color="#2563eb", linestyle="--", linewidth=1.5, label="Rata-rata Akurasi Keseluruhan (61.19%)")
    plt.xticks(x, FINGERSPELL_26_LABELS, fontsize=10, fontweight="bold")
    plt.xlabel("Kelas Alfabet BISINDO (A-Z)", fontsize=11, fontweight="bold")
    plt.ylabel("Akurasi (Recall) per Kelas (%)", fontsize=11, fontweight="bold")
    plt.title("Akurasi (Recall) per Kelas pada Test Set N=670", fontsize=12, fontweight="bold", pad=12)
    plt.ylim(0, 105)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.legend(fontsize=10)

    for bar, acc_val in zip(bars, per_class_acc):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{acc_val:.0f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "per_class_accuracy.png")
    plt.close()
    print("Saved per_class_accuracy.png")

    # =========================================================================
    # 4. TOP CONFUSION PAIRS
    # =========================================================================
    error_pairs = defaultdict(int)
    for t, p in zip(true_labels, pred_labels):
        if t != p:
            error_pairs[f"{FINGERSPELL_26_LABELS[t]} -> {FINGERSPELL_26_LABELS[p]}"] += 1

    top10 = sorted(error_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
    pairs = [k for k, v in top10]
    counts = [v for k, v in top10]

    plt.figure(figsize=(10, 5), dpi=150)
    plt.barh(pairs[::-1], counts[::-1], color="#f97316", edgecolor="black", alpha=0.85)
    plt.xlabel("Jumlah Kesalahan Prediksi (Sampel)", fontsize=11, fontweight="bold")
    plt.ylabel("Pasangan Huruf (Ground Truth -> Prediksi Salah)", fontsize=11, fontweight="bold")
    plt.title("10 Pasangan Huruf yang Paling Sering Tertukar (Confusion Pairs)", fontsize=12, fontweight="bold", pad=12)
    plt.grid(axis="x", linestyle="--", alpha=0.5)
    for idx, count in enumerate(counts[::-1]):
        plt.text(count + 0.2, idx, str(count), va="center", fontsize=9, fontweight="bold")
    plt.xlim(0, max(counts) + 2)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_confusion_pairs.png")
    plt.close()
    print("Saved top_confusion_pairs.png")


if __name__ == "__main__":
    generate_figures()
