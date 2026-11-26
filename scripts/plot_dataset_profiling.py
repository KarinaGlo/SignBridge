import matplotlib.pyplot as plt
import json
from pathlib import Path
from PIL import Image

FIGURES_DIR = Path("docs/figures/p0_dataset")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

with open("docs/validation_bisindo_alphabet_summary.json") as f:
    data = json.load(f)

stats = data["per_class_stats"]
classes = sorted(stats.keys())
counts = [stats[c]["count"] for c in classes]

# 1. Class Distribution Bar Chart
plt.figure(figsize=(12, 5), dpi=150)
bars = plt.bar(classes, counts, color="#2563eb", edgecolor="#1d4ed8", width=0.7)
plt.axhline(40, color="#dc2626", linestyle="--", linewidth=1.5, label="Target Minimum Proyek (40/kelas)")
avg_count = sum(counts) / len(counts)
plt.axhline(avg_count, color="#16a34a", linestyle=":", linewidth=1.5, label=f"Rata-rata Aktual ({avg_count:.1f}/kelas)")

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2.0, yval + 1, int(yval), ha="center", va="bottom", fontsize=8, fontweight="bold")

plt.title("Distribusi Jumlah Citra per Kelas A-Z (Mendeley BISINDO Alphabet v1)", fontsize=13, fontweight="bold", pad=12)
plt.xlabel("Kelas Huruf (A-Z)", fontsize=11, fontweight="bold")
plt.ylabel("Jumlah Citra 224x224 RGB", fontsize=11, fontweight="bold")
plt.ylim(0, 195)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(loc="lower right", frameon=True)
plt.tight_layout()
dist_path = FIGURES_DIR / "class_distribution.png"
plt.savefig(dist_path)
plt.close()
print("Generated:", dist_path)

# 2. Sample 26 Classes Grid
RAW_DIR = Path("data/raw/image/bisindo_alphabet")
fig, axes = plt.subplots(4, 7, figsize=(14, 8), dpi=150)
axes = axes.flatten()

for idx, c in enumerate(classes):
    c_folder = RAW_DIR / c
    files = sorted([f for f in c_folder.iterdir() if f.is_file() and not f.name.startswith("._")])
    img_sample = files[len(files) // 2]  # pick middle sample
    im = Image.open(img_sample)
    axes[idx].imshow(im)
    cls_cnt = stats[c]["count"]
    axes[idx].set_title(f"Kelas {c} ({cls_cnt})", fontsize=9, fontweight="bold")
    axes[idx].axis("off")

# Hide remaining 2 subplots (4*7 = 28, we have 26 classes)
for idx in range(len(classes), len(axes)):
    axes[idx].axis("off")

plt.suptitle("Sampel Citra Tangan Asli 26 Kelas A-Z (Resolusi Asli 224x224 RGB)", fontsize=14, fontweight="bold", y=0.98)
plt.tight_layout()
grid_path = FIGURES_DIR / "sample_classes_grid.png"
plt.savefig(grid_path)
plt.close()
print("Generated:", grid_path)

