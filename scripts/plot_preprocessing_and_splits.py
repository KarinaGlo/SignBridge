"""
scripts/plot_preprocessing_and_splits.py
Generates visual quality control figures for preprocessed dataset:
1. docs/figures/p0_dataset/full_26_classes_preprocessing_grid.png (All 26 classes A-Z comparison)
2. docs/figures/p0_dataset/split_distribution_by_class.png (Stacked bar chart of train/val/test)
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed" / "bisindo_alphabet"
RAW_DIR = ROOT / "data" / "raw" / "image" / "bisindo_alphabet"
FIGURES_DIR = ROOT / "docs" / "figures" / "p0_dataset"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

with open(PROCESSED_DIR / "preprocessing_summary.json", encoding="utf-8") as f:
    summary = json.load(f)

class_split_stats = summary["class_split_stats"]
classes = sorted(class_split_stats.keys())

# 1. Stacked Bar Chart of Train / Val / Test Splits
train_counts = [class_split_stats[c]["train"] for c in classes]
val_counts = [class_split_stats[c]["val"] for c in classes]
test_counts = [class_split_stats[c]["test"] for c in classes]

plt.figure(figsize=(14, 6), dpi=150)
bar_width = 0.65
indices = np.arange(len(classes))

p1 = plt.bar(indices, train_counts, bar_width, label="Train (70%)", color="#2563eb", edgecolor="#1d4ed8")
p2 = plt.bar(indices, val_counts, bar_width, bottom=train_counts, label="Validation (15%)", color="#f59e0b", edgecolor="#d97706")
bottom_test = np.array(train_counts) + np.array(val_counts)
p3 = plt.bar(indices, test_counts, bar_width, bottom=bottom_test, label="Test (15%)", color="#10b981", edgecolor="#059669")

plt.title("Stratified Data Split 70/15/15 per Kelas A-Z (4.462 Citra Valid)", fontsize=13, fontweight="bold", pad=12)
plt.xlabel("Kelas Huruf Alfabet (A-Z)", fontsize=11, fontweight="bold")
plt.ylabel("Jumlah Citra 224x224 RGB", fontsize=11, fontweight="bold")
plt.xticks(indices, classes, fontweight="bold")
plt.ylim(0, 195)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(loc="lower right", frameon=True, fontsize=10)

for i in range(len(classes)):
    tot = train_counts[i] + val_counts[i] + test_counts[i]
    plt.text(i, tot + 2, str(tot), ha="center", va="bottom", fontsize=8, fontweight="bold")

plt.tight_layout()
split_fig = FIGURES_DIR / "split_distribution_by_class.png"
plt.savefig(split_fig)
plt.close()
print("Generated:", split_fig)

# 2. Full 26 Classes Visual Quality Inspection Grid (Original vs Processed)
fig, axes = plt.subplots(7, 8, figsize=(16, 15), dpi=150)
axes = axes.flatten()

# We display 26 pairs (original & processed), total 52 subplots in an 8-column layout
for idx, c in enumerate(classes):
    raw_folder = RAW_DIR / c
    proc_folder = PROCESSED_DIR / c

    raw_files = sorted([f for f in raw_folder.iterdir() if f.is_file() and not f.name.startswith("._")])
    proc_files = sorted([f for f in proc_folder.iterdir() if f.is_file() and f.suffix == ".jpg"])

    mid_i = len(raw_files) // 2
    raw_sample = raw_files[mid_i]
    proc_sample = proc_files[min(mid_i, len(proc_files) - 1)]

    ax_raw = axes[idx * 2]
    ax_proc = axes[idx * 2 + 1]

    im_raw = Image.open(raw_sample)
    im_proc = Image.open(proc_sample)

    ax_raw.imshow(im_raw)
    ax_raw.set_title(f"[{c}] Asli", fontsize=8, fontweight="bold")
    ax_raw.axis("off")

    ax_proc.imshow(im_proc)
    ax_proc.set_title(f"[{c}] Processed", fontsize=8, fontweight="bold", color="#1d4ed8")
    ax_proc.axis("off")

# Hide remaining unused subplots (56 - 52 = 4)
for i in range(len(classes) * 2, len(axes)):
    axes[i].axis("off")

plt.suptitle("Quality Control: Perbandingan Citra Asli vs Hasil Preprocessing 26 Kelas A-Z", fontsize=14, fontweight="bold", y=0.99)
plt.tight_layout()
grid_fig = FIGURES_DIR / "full_26_classes_preprocessing_grid.png"
plt.savefig(grid_fig)
plt.close()
print("Generated:", grid_fig)

