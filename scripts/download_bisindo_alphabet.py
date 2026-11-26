"""
scripts/download_bisindo_alphabet.py
Official Downloader for Mendeley BISINDO Alphabet Image Data (doi:10.17632/ywnjpbcz8m.1)
Author: Samuel Ady Sanjaya (2024)
License: Creative Commons Attribution 4.0 International (CC BY 4.0)

Downloads all 26 classes (A-Z) of the compressed 224x224 RGB dataset (4,466 images, ~27.71 MB)
with full SHA-256 verification and automatic retry mechanism.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import logging
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mendeley_downloader")

MENDELEY_API_URL = "https://data.mendeley.com/public-api/datasets/ywnjpbcz8m"
DOI = "10.17632/ywnjpbcz8m.1"
DATASET_ID = "ywnjpbcz8m"
VERSION = 1
LICENSE = "CC BY 4.0"
ATTRIBUTION = "Samuel Ady Sanjaya (2024) doi:10.17632/ywnjpbcz8m.1"

# Folder ID to Letter mapping for 26 compressed RGB classes (224x224)
FOLDER_TO_LETTER: Dict[str, str] = {
    "bfd81e36-4372-425f-9ff6-4d151bee0d42": "A",
    "a4b3d61b-8828-4dbf-bdc5-dfddc4439139": "B",
    "467d13d3-b3d3-47f4-a10d-e5f0302bde2d": "C",
    "b560a0df-6ca7-4f3c-a508-feac0872ad77": "D",
    "56fcf576-0915-4d03-ae7d-701706db6365": "E",
    "4516f45f-bd05-4e4b-aa42-b10cd837766d": "F",
    "14c4eb3d-12a8-4dbe-aa2b-56f285ceac14": "G",
    "c634c181-572b-4c73-ad87-495399843a8b": "H",
    "0b0334cf-3fd7-4866-a75b-94847b28394f": "I",
    "98d5a8dd-f77c-447a-8fff-4ad748beefc8": "J",
    "55a6ad48-df08-479a-9da5-f288e75e75ee": "K",
    "c99c18c0-bfc4-4453-beca-26ed5d5382dc": "L",
    "a43d5824-3e3e-409b-a224-c91f70688cf1": "M",
    "b15fe7e8-97a2-481e-a94c-998b7b968d86": "N",
    "49674db4-5bc9-4dbb-bd76-fdb95ad956db": "O",
    "717eb6a1-e319-4b32-9547-b9b72f238efd": "P",
    "a62cd016-0d32-41f4-b572-b9c99b406f0c": "Q",
    "edb6276a-ed2c-4022-afb6-27c55b06e41f": "R",
    "800d0bc0-efd0-41f7-8dae-847b43c79621": "S",
    "4112407c-6d5b-4d7c-ae4d-c05e365e9a5a": "T",
    "1accc20a-caad-4d52-ae72-727d4c621788": "U",
    "ddcfa63a-b31d-44d9-9fc4-1077a5d400a7": "V",
    "436b35a7-231b-448e-aee4-a85c9c1b4584": "W",
    "23938078-3d9c-48ec-a0bf-bcced57a295e": "X",
    "7cab64f6-e8af-4e91-87ce-ca0f61dfefff": "Y",
    "62c8f8cc-e58f-4ae9-9e21-1333ed29b3e2": "Z",
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def download_single_file(
    task: Tuple[str, Path, int, str],
    max_retries: int = 3,
    timeout: int = 20,
) -> Tuple[bool, str, Path, int, str]:
    """
    Downloads a single file from download_url to dest_path with SHA-256 and size verification.
    task: (download_url, dest_path, expected_size, expected_sha256)
    """
    url, dest, expected_size, expected_sha = task
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded and verified
    if dest.exists() and dest.is_file() and dest.stat().st_size == expected_size:
        actual_sha = compute_sha256(dest)
        if actual_sha == expected_sha.lower():
            return True, "EXISTS_VALID", dest, expected_size, actual_sha

    tmp_path = dest.with_suffix(dest.suffix + f".tmp_{os.getpid()}")

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    time.sleep(attempt * 0.5)
                    continue
                data = resp.read()

            with tmp_path.open("wb") as f:
                f.write(data)

            if len(data) != expected_size:
                tmp_path.unlink(missing_ok=True)
                time.sleep(attempt * 0.5)
                continue

            actual_sha = compute_sha256(tmp_path)
            if actual_sha != expected_sha.lower():
                tmp_path.unlink(missing_ok=True)
                time.sleep(attempt * 0.5)
                continue

            # Atomic replace
            if dest.exists():
                dest.unlink()
            tmp_path.rename(dest)
            return True, "DOWNLOADED_OK", dest, expected_size, actual_sha

        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            if attempt < max_retries:
                time.sleep(attempt * 0.5)
            else:
                return False, f"FAILED: {e}", dest, expected_size, ""

    return False, "FAILED_MAX_RETRIES", dest, expected_size, ""


def run_download(
    out_dir: Path = Path("data/raw/image/bisindo_alphabet"),
    workers: int = 12,
    max_per_class: Optional[int] = None,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Mengambil katalog metadata resmi dari Mendeley API: %s", MENDELEY_API_URL)
    req = urllib.request.Request(MENDELEY_API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        meta_json = json.loads(resp.read().decode("utf-8"))

    # Simpan metadata resmi
    meta_path = out_dir / "mendeley_metadata.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta_json, f, indent=2)
    logger.info("Metadata JSON disimpan ke %s (%d bytes)", meta_path, meta_path.stat().st_size)

    all_files = meta_json.get("files", [])
    logger.info("Total entri file di Mendeley katalog: %d", len(all_files))

    # Filter compressed RGB files belonging to the 26 target folders
    class_tasks: Dict[str, List[Tuple[str, Path, int, str]]] = {letter: [] for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    
    for f in all_files:
        fn = f.get("filename", "")
        if fn.startswith("._"):
            continue
        fid = f.get("folder_id")
        if fid not in FOLDER_TO_LETTER:
            continue
        letter = FOLDER_TO_LETTER[fid]
        
        details = f.get("content_details", {})
        download_url = details.get("download_url")
        expected_size = details.get("size", f.get("size", 0))
        expected_sha = details.get("sha256_hash", "")
        
        dest_path = out_dir / letter / fn
        class_tasks[letter].append((download_url, dest_path, expected_size, expected_sha))

    total_tasks: List[Tuple[str, Path, int, str]] = []
    for letter in sorted(class_tasks.keys()):
        files_for_class = class_tasks[letter]
        if max_per_class is not None:
            files_for_class = files_for_class[:max_per_class]
        total_tasks.extend(files_for_class)
        logger.info("Kelas %s: %d gambar target", letter, len(files_for_class))

    logger.info("Total target unduh: %d berkas citra RGB", len(total_tasks))

    results = []
    start_time = time.time()
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download_single_file, task): task for task in total_tasks}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 500 == 0 or completed == len(total_tasks):
                elapsed = time.time() - start_time
                logger.info("Progress: %d/%d berkas diproses (%.1f detik)", completed, len(total_tasks), elapsed)

    success_count = sum(1 for r in results if r[0])
    failed_count = sum(1 for r in results if not r[0])
    total_bytes = sum(r[3] for r in results if r[0])

    logger.info(
        "Download selesai! Berhasil: %d, Gagal: %d, Total Ukuran: %d bytes (%.2f MB)",
        success_count,
        failed_count,
        total_bytes,
        total_bytes / (1024 * 1024),
    )

    # Buat file manifest hashes CSV
    hash_csv_path = out_dir / "file_hashes_sha256.csv"
    with hash_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["letter", "filename", "path", "size_bytes", "sha256", "status"])
        for success, status, dest, size, sha in sorted(results, key=lambda x: str(x[2])):
            letter = dest.parent.name
            writer.writerow([letter, dest.name, str(dest.as_posix()), size, sha, status])

    # Buat summary JSON
    summary_path = out_dir / "download_verification_summary.json"
    summary_data = {
        "dataset_name": "BISINDO Indonesian Sign Language: Alphabet Image Data",
        "doi": DOI,
        "dataset_id": DATASET_ID,
        "version": VERSION,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "download_timestamp": datetime.now().isoformat(),
        "total_files": len(total_tasks),
        "success_files": success_count,
        "failed_files": failed_count,
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "classes_count": len(class_tasks),
        "per_class_count": {letter: len(list((out_dir / letter).glob("*.jp*g")) + list((out_dir / letter).glob("*.JP*G"))) for letter in class_tasks.keys()},
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    return summary_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Mendeley BISINDO Alphabet Dataset")
    parser.add_argument("--out", type=str, default="data/raw/image/bisindo_alphabet")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--max-per-class", type=int, default=None)
    args = parser.parse_args()

    run_download(out_dir=Path(args.out), workers=args.workers, max_per_class=args.max_per_class)

