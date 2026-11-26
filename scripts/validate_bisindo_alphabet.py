"""
scripts/validate_bisindo_alphabet.py
Performs comprehensive automated validation and statistical profiling on the downloaded
Mendeley BISINDO Alphabet dataset in data/raw/image/bisindo_alphabet/<A..Z>/.
"""

import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from PIL import Image

RAW_DIR = Path("data/raw/image/bisindo_alphabet")
FIGURES_DIR = Path("docs/figures/p0_dataset")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def run_validation():
    print(f"=== Memulai Validasi Dataset: {RAW_DIR} ===")
    if not RAW_DIR.exists():
        print(f"ERROR: Direktori {RAW_DIR} tidak ditemukan!")
        sys.exit(1)

    classes = [d.name for d in RAW_DIR.iterdir() if d.is_dir() and len(d.name) == 1 and d.name.isalpha()]
    classes.sort()
    print(f"Ditemukan {len(classes)} folder kelas: {classes}")

    total_images = 0
    corrupt_images = 0
    non_224_count = 0
    non_rgb_count = 0
    per_class_stats = {}
    sha_map = defaultdict(list)
    dimensions_set = set()
    formats_set = set()

    all_file_records = []

    for c in classes:
        folder = RAW_DIR / c
        files = sorted([f for f in folder.iterdir() if f.is_file() and not f.name.startswith("._")])
        count = len(files)
        total_images += count
        class_corrupt = 0
        class_sizes = []

        for f in files:
            size_b = f.stat().st_size
            class_sizes.append(size_b)
            sha = compute_sha256(f)
            sha_map[sha].append((c, f.name, size_b))

            # Validate Image with PIL
            try:
                with Image.open(f) as img:
                    img.verify()
                with Image.open(f) as img:
                    w, h = img.size
                    dimensions_set.add((w, h))
                    formats_set.add(img.format)
                    mode = img.mode
                    if mode != "RGB":
                        non_rgb_count += 1
                    if w != 224 or h != 224:
                        non_224_count += 1
            except Exception as e:
                class_corrupt += 1
                corrupt_images += 1
                print(f"CORRUPT FILE: {f} ({e})")

            all_file_records.append({
                "class": c,
                "filename": f.name,
                "path": str(f.as_posix()),
                "size_bytes": size_b,
                "sha256": sha
            })

        avg_size = sum(class_sizes) / len(class_sizes) if class_sizes else 0
        per_class_stats[c] = {
            "count": count,
            "corrupt": class_corrupt,
            "min_size": min(class_sizes) if class_sizes else 0,
            "max_size": max(class_sizes) if class_sizes else 0,
            "avg_size_kb": round(avg_size / 1024, 2),
            "total_bytes": sum(class_sizes)
        }

    # Duplicate analysis
    duplicate_groups = {sha: items for sha, items in sha_map.items() if len(items) > 1}
    cross_class_duplicates = {sha: items for sha, items in duplicate_groups.items() if len(set(x[0] for x in items)) > 1}
    intra_class_duplicates = {sha: items for sha, items in duplicate_groups.items() if len(set(x[0] for x in items)) == 1}

    print("\n--- RINGKASAN VALIDASI TEKNIS ---")
    print(f"Total Folder Kelas     : {len(classes)} (Target: 26)")
    print(f"Total Gambar Valid     : {total_images} (Target: 4.466)")
    print(f"Total Gambar Rusak     : {corrupt_images} (Target: 0)")
    print(f"Total Bukan 224x224    : {non_224_count} (Target: 0)")
    print(f"Total Bukan RGB        : {non_rgb_count} (Target: 0)")
    print(f"Resolusi Ditemukan     : {dimensions_set}")
    print(f"Format Gambar          : {formats_set}")
    print(f"Grup SHA-256 Identik   : {len(duplicate_groups)} grup")
    print(f" - Duplikat Lintas-Kelas: {len(cross_class_duplicates)} grup")
    print(f" - Duplikat Dalam-Kelas : {len(intra_class_duplicates)} grup")

    if cross_class_duplicates:
        print("\nDetail Duplikat Lintas-Kelas (Penting untuk disaring agar tidak ambigu):")
        for sha, items in cross_class_duplicates.items():
            print(f"  SHA: {sha[:16]}... -> {items}")

    # Output validation JSON
    report_json = {
        "total_classes": len(classes),
        "total_images": total_images,
        "corrupt_images": corrupt_images,
        "non_224_count": non_224_count,
        "non_rgb_count": non_rgb_count,
        "dimensions": [f"{w}x{h}" for w, h in dimensions_set],
        "formats": list(formats_set),
        "total_duplicate_groups": len(duplicate_groups),
        "cross_class_duplicate_groups": len(cross_class_duplicates),
        "intra_class_duplicate_groups": len(intra_class_duplicates),
        "cross_class_details": [
            {"sha256": sha, "files": [{"class": c, "filename": fn, "size": sz} for c, fn, sz in items]}
            for sha, items in cross_class_duplicates.items()
        ],
        "per_class_stats": per_class_stats
    }

    report_path = Path("docs/validation_bisindo_alphabet_summary.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
    print(f"\nRingkasan validasi disimpan ke: {report_path}")

    return report_json

if __name__ == "__main__":
    run_validation()

