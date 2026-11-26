"""
scripts/test_crop_samples.py
Performs sample hand crop testing across representative BISINDO alphabet classes (A, B, C, K, O, Y)
to verify crop consistency, bounding box safety (+25% margin), and prevent finger clipping.
"""

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from signbridge.image.crop import crop_and_resize_hand, _bilinear_resize_rgb, compute_hand_crop_box

RAW_DIR = Path("data/raw/image/bisindo_alphabet")
FIGURES_DIR = Path("docs/figures/p0_dataset")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_CLASSES = ["A", "B", "C", "K", "O", "Y"]

def run_sample_crop_test():
    fig, axes = plt.subplots(len(SAMPLE_CLASSES), 4, figsize=(12, 16), dpi=150)

    for i, letter in enumerate(SAMPLE_CLASSES):
        folder = RAW_DIR / letter
        files = sorted([f for f in folder.iterdir() if f.is_file() and not f.name.startswith("._")])
        sample_file = files[len(files) // 2]

        # 1. Load original
        im = Image.open(sample_file).convert("RGB")
        img_arr = np.asarray(im, dtype=np.uint8)
        H, W, _ = img_arr.shape

        # 2. Hand Bounding Box Detection test (Color/Intensity Otsu Thresholding to find hand contour)
        import cv2
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # Adaptive/Otsu threshold
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            pts = largest.reshape(-1, 2)
            # Use project's compute_hand_crop_box with 25% margin
            box = compute_hand_crop_box(pts, img_w=W, img_h=H, margin=0.25)
        else:
            # Fallback precentered square
            box = {"x0": 0, "y0": 0, "x1": W, "y1": H, "size": min(W, H)}

        # Overlay bounding box on original image
        overlay = img_arr.copy()
        cv2.rectangle(
            overlay,
            (box["x0"], box["y0"]),
            (box["x1"], box["y1"]),
            (0, 255, 0),
            2
        )

        # 3. Cropped patch
        cropped_patch = img_arr[box["y0"]:box["y1"], box["x0"]:box["x1"]]

        # 4. Final 224x224 resized output (using project bilinear resize)
        final_resized = _bilinear_resize_rgb(cropped_patch, out_h=224, out_w=224)

        # Column 1: Original
        axes[i, 0].imshow(img_arr)
        axes[i, 0].set_title(f"Kelas {letter}: Asli ({W}x{H})", fontsize=10, fontweight="bold")
        axes[i, 0].axis("off")

        # Column 2: Bounding Box
        axes[i, 1].imshow(overlay)
        axes[i, 1].set_title(f"Deteksi Kotak (+25% Margin)", fontsize=10, fontweight="bold")
        axes[i, 1].axis("off")

        # Column 3: Cropped patch
        axes[i, 2].imshow(cropped_patch)
        axes[i, 2].set_title(f"Patch Potongan ({box['size']}x{box['size']})", fontsize=10, fontweight="bold")
        axes[i, 2].axis("off")

        # Column 4: Final 224x224
        axes[i, 3].imshow(final_resized)
        axes[i, 3].set_title(f"Output Resize (224x224)", fontsize=10, fontweight="bold")
        axes[i, 3].axis("off")

    plt.suptitle("Uji Validasi Preprocessing Hand Crop (+25% Margin) pada Sampel Citra A-Z", fontsize=13, fontweight="bold", y=0.99)
    plt.tight_layout()
    out_fig = FIGURES_DIR / "preprocessing_crop_sample.png"
    plt.savefig(out_fig)
    plt.close()
    print("Sample crop comparison figure generated at:", out_fig)

if __name__ == "__main__":
    run_sample_crop_test()
