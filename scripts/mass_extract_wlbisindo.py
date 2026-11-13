"""
scripts/mass_extract_wlbisindo.py — Ekstraksi Massal 1.600 Video WL-BISINDO (Tahap A.3.3)

Kontrak Ekstraksi:
- 1.600 video MP4 asli dari data/raw/video/wl_bisindo/videos/
- 32 kelas resmi WL-BISINDO (WLBISINDO_LABELS)
- 5 signer asli (signer0..signer4)
- 86 keypoints per frame: Pose (9), Left Hand (21), Right Hand (21), Face (35)
- Output tensor: [64, 86, 3] float32
- Valid mask: [64, 86] bool
- Resampling: midpoint-floor deterministik ke 64 frame
- Normalisasi bahu: center di midpoint bahu, scale di lebar bahu
- Ekstraksi bertahap: 16 batch @ 100 video dengan checkpoint persisten
- Tidak pernah menghasilkan data sintetis/acak.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.constants import (
    MANIFEST_COLUMNS,
    NUM_COORDS,
    NUM_KEYPOINTS,
    select_from_holistic,
)
from signbridge.data.video_metadata import (
    EXP_INCLUDED,
    WLBISINDO_LABELS,
    assign_wlbisindo_sd_splits,
    compute_file_sha256,
    parse_wlbisindo_filename,
)
from signbridge.features import preprocess_keypoints


def extract_single_video_worker(args: Tuple[str, str, str, int, str]) -> Dict[str, Any]:
    """
    Fungsi worker proses tunggal untuk mengekstrak 1 video WL-BISINDO.
    args: (video_path_str, out_npz_path_str, gloss, label_id, signer_id)
    """
    vpath_str, out_npz_str, gloss, label_id, signer_id = args
    vpath = Path(vpath_str)
    out_npz = Path(out_npz_str)

    # 1. Cek apakah output sudah ada dan valid (resume mode)
    if out_npz.exists() and out_npz.is_file() and out_npz.stat().st_size > 0:
        try:
            with np.load(str(out_npz)) as data:
                kp = data["keypoints"]
                mask = data["valid_mask"]
                if (
                    kp.shape == (64, 86, 3)
                    and kp.dtype == np.float32
                    and mask.shape == (64, 86)
                    and mask.dtype == bool
                    and not np.isnan(kp).any()
                    and not np.isinf(kp).any()
                    and str(data["gloss"]) == gloss
                    and int(data["label"]) == label_id
                    and str(data["signer"]) == signer_id
                ):
                    return {
                        "filename": vpath.name,
                        "success": True,
                        "resumed": True,
                        "npz_path": str(out_npz),
                        "frames": 64,
                        "filesize": out_npz.stat().st_size,
                        "error": "",
                    }
        except Exception:
            pass  # Output rusak, ekstrak ulang

    # 2. Buka video fisik dengan OpenCV
    cap = cv2.VideoCapture(str(vpath))
    if not cap.isOpened():
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": 0,
            "filesize": 0,
            "error": f"VideoCapture failed to open: {vpath.name}",
        }

    frames_kp: List[np.ndarray] = []
    try:
        with mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as holistic:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = holistic.process(rgb)

                def _lm_to_arr(lms: Any, count: int) -> Optional[np.ndarray]:
                    if lms is None:
                        return None
                    return np.array(
                        [[lm.x, lm.y, lm.z] for lm in lms.landmark[:count]],
                        dtype=np.float32,
                    )

                kp86 = select_from_holistic(
                    _lm_to_arr(res.pose_landmarks, 33),
                    _lm_to_arr(res.left_hand_landmarks, 21),
                    _lm_to_arr(res.right_hand_landmarks, 21),
                    _lm_to_arr(res.face_landmarks, 468),
                )
                frames_kp.append(kp86)
    except Exception as e:
        cap.release()
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": 0,
            "filesize": 0,
            "error": f"Holistic extraction exception: {str(e)}",
        }
    finally:
        cap.release()

    if not frames_kp:
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": 0,
            "filesize": 0,
            "error": f"No frames decoded from: {vpath.name}",
        }

    raw_kp = np.stack(frames_kp, axis=0).astype(np.float32)

    # 3. Preprocessing Contract 3 (trim_inactive -> normalize_pose -> resample_frames)
    norm_kp, valid_mask = preprocess_keypoints(raw_kp, target_len=64, trim=True)

    # 4. Validasi ketat sebelum disimpan
    if norm_kp.shape != (64, 86, 3) or norm_kp.dtype != np.float32:
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": raw_kp.shape[0],
            "filesize": 0,
            "error": f"Invalid normalized shape/dtype: {norm_kp.shape}, {norm_kp.dtype}",
        }
    if valid_mask.shape != (64, 86) or valid_mask.dtype != bool:
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": raw_kp.shape[0],
            "filesize": 0,
            "error": f"Invalid mask shape/dtype: {valid_mask.shape}, {valid_mask.dtype}",
        }
    if np.isnan(norm_kp).any() or np.isinf(norm_kp).any():
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": raw_kp.shape[0],
            "filesize": 0,
            "error": "Found NaN or Inf in normalized keypoints",
        }

    # 5. Simpan atomic ke .npz
    tmp_npz = out_npz.with_suffix(".tmp.npz")
    try:
        np.savez_compressed(
            tmp_npz,
            keypoints=norm_kp,
            valid_mask=valid_mask,
            raw_keypoints=raw_kp,
            gloss=gloss,
            label=label_id,
            signer=signer_id,
            source="wl_bisindo",
        )
        if out_npz.exists():
            out_npz.unlink()
        tmp_npz.rename(out_npz)
    except Exception as e:
        if tmp_npz.exists():
            tmp_npz.unlink()
        return {
            "filename": vpath.name,
            "success": False,
            "resumed": False,
            "npz_path": "",
            "frames": raw_kp.shape[0],
            "filesize": 0,
            "error": f"Failed to save .npz: {str(e)}",
        }

    return {
        "filename": vpath.name,
        "success": True,
        "resumed": False,
        "npz_path": str(out_npz),
        "frames": raw_kp.shape[0],
        "filesize": out_npz.stat().st_size,
        "error": "",
    }


def run_mass_extraction(
    raw_dir: Path,
    out_dir: Path,
    manifest_file: Path,
    checkpoint_file: Path,
    batch_size: int = 100,
    max_workers: int = 4,
) -> None:
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    manifest_file = Path(manifest_file)
    checkpoint_file = Path(checkpoint_file)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Pindai dan urutkan seluruh berkas video
    video_files = sorted(raw_dir.glob("*.mp4"))
    total_videos = len(video_files)
    if total_videos != 1600:
        raise ValueError(f"Diharapkan tepat 1.600 video WL-BISINDO, ditemukan: {total_videos}")

    # 2. Parse record & tentukan SD split deterministik
    records = [parse_wlbisindo_filename(v) for v in video_files]
    sd_splits = assign_wlbisindo_sd_splits(records)

    # 3. Baca checkpoint jika ada
    checkpoint_data: Dict[str, Any] = {
        "total_videos": total_videos,
        "processed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "last_batch_completed": 0,
        "completed_files": {},
        "failed_files": {},
        "started_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat(),
        "dependencies": {
            "python": sys.version.split()[0],
            "mediapipe": mp.__version__,
            "opencv": cv2.__version__,
            "numpy": np.__version__,
        },
    }

    if checkpoint_file.exists():
        try:
            with checkpoint_file.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
                if loaded.get("total_videos") == total_videos:
                    checkpoint_data = loaded
                    print(
                        f"[CHECKPOINT] Resume dari batch {checkpoint_data.get('last_batch_completed', 0)}: "
                        f"{checkpoint_data.get('success_count', 0)} sukses, {checkpoint_data.get('failed_count', 0)} gagal."
                    )
        except Exception as e:
            print(f"[CHECKPOINT] Gagal membaca checkpoint lama ({e}), memulai checkpoint baru.")

    completed_map = checkpoint_data["completed_files"]
    failed_map = checkpoint_data["failed_files"]

    # 4. Bagi menjadi 16 batch @ 100 video
    num_batches = (total_videos + batch_size - 1) // batch_size
    print(f"=== MEMULAI EKSTRAKSI MASSAL {total_videos} VIDEO ({num_batches} BATCH @ {batch_size}) ===")
    print(f"Workers: {max_workers} proses paralel | Output: {out_dir}")

    total_start_time = time.time()

    for batch_idx in range(1, num_batches + 1):
        batch_start_time = time.time()
        start_idx = (batch_idx - 1) * batch_size
        end_idx = min(start_idx + batch_size, total_videos)
        batch_videos = video_files[start_idx:end_idx]

        # Siapkan tugas worker
        tasks = []
        for vf in batch_videos:
            rec = parse_wlbisindo_filename(vf)
            vid_id = f"wl_bisindo_{vf.stem}"
            npz_path = out_dir / f"{vid_id}.npz"
            tasks.append((str(vf), str(npz_path), rec.source_gloss, rec.source_label_id, rec.signer_id))

        batch_success = 0
        batch_failed = 0
        batch_resumed = 0

        # Eksekusi paralel batch
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(extract_single_video_worker, t): t[0] for t in tasks}
            for fut in as_completed(futures):
                res = fut.result()
                fname = res["filename"]
                if res["success"]:
                    batch_success += 1
                    if res.get("resumed"):
                        batch_resumed += 1
                    completed_map[fname] = {
                        "npz_path": res["npz_path"],
                        "filesize": res["filesize"],
                        "frames": res["frames"],
                    }
                    if fname in failed_map:
                        del failed_map[fname]
                else:
                    batch_failed += 1
                    failed_map[fname] = res["error"]
                    print(f"  [ERROR] {fname}: {res['error']}")

        batch_duration = time.time() - batch_start_time

        # Update checkpoint kumulatif
        checkpoint_data["processed_count"] = len(completed_map) + len(failed_map)
        checkpoint_data["success_count"] = len(completed_map)
        checkpoint_data["failed_count"] = len(failed_map)
        checkpoint_data["last_batch_completed"] = batch_idx
        checkpoint_data["updated_at"] = datetime.datetime.now().isoformat()

        # Simpan atomic checkpoint
        tmp_ckpt = checkpoint_file.with_suffix(".tmp.json")
        with tmp_ckpt.open("w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)
        if checkpoint_file.exists():
            checkpoint_file.unlink()
        tmp_ckpt.rename(checkpoint_file)

        remaining = total_videos - checkpoint_data["processed_count"]
        # Format progres yang diwajibkan:
        # Batch X/16 | Processed | Success | Failed | Remaining | Duration
        print(
            f"Batch {batch_idx:02d}/{num_batches:02d} | "
            f"Processed: {checkpoint_data['processed_count']:4d}/{total_videos} | "
            f"Success: {checkpoint_data['success_count']:4d} | "
            f"Failed: {checkpoint_data['failed_count']:2d} | "
            f"Remaining: {remaining:4d} | "
            f"Duration: {batch_duration:5.1f}s (Resumed: {batch_resumed})"
        )

    total_duration = time.time() - total_start_time
    print(f"\n=== SELURUH {num_batches} BATCH SELESAI DALAM {total_duration/60:.2f} MENIT ===")

    # 5. Buat manifest resmi hasil ekstraksi (Contract 1: MANIFEST_COLUMNS)
    manifest_rows = []
    meta_rows = []

    print("Membuat manifest resmi hasil ekstraksi...")
    for idx, vf in enumerate(video_files):
        rec = parse_wlbisindo_filename(vf)
        vid_id = f"wl_bisindo_{vf.stem}"
        npz_path = out_dir / f"{vid_id}.npz"
        split_sd = sd_splits[vf.name]

        try:
            kp_rel = str(npz_path.resolve().relative_to(ROOT.resolve()).as_posix())
        except ValueError:
            kp_rel = str(npz_path.as_posix())

        try:
            src_rel = str(vf.resolve().relative_to(ROOT.resolve()).as_posix())
        except ValueError:
            src_rel = str(vf.as_posix())

        manifest_rows.append(
            {
                "video_id": vid_id,
                "source": "wl_bisindo",
                "gloss": rec.source_gloss,
                "label": rec.source_label_id,
                "signer": rec.signer_id,
                "kp_path": kp_rel,
                "rgb_path": "",
                "split_sd": split_sd,
            }
        )

        meta_rows.append(
            {
                "video_id": vid_id,
                "source": "wl_bisindo",
                "source_path": src_rel,
                "source_label_id": rec.source_label_id,
                "source_gloss": rec.source_gloss,
                "signer_id": rec.signer_id,
                "official_split": "",
                "split_sd": split_sd,
                "sha256": compute_file_sha256(vf),
                "dup_status": "UNIQUE",
                "experiment_status": EXP_INCLUDED,
            }
        )

    with manifest_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(MANIFEST_COLUMNS))
        writer.writeheader()
        writer.writerows(manifest_rows)

    meta_file = manifest_file.with_name(f"{manifest_file.stem}_source_metadata.csv")
    from scripts.extract_keypoints import SOURCE_METADATA_COLUMNS

    with meta_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(SOURCE_METADATA_COLUMNS))
        writer.writeheader()
        writer.writerows(meta_rows)

    print(f"Manifest tersimpan: {manifest_file} ({len(manifest_rows)} entri)")
    print(f"Metadata tersimpan: {meta_file} ({len(meta_rows)} entri)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mass Extraction WL-BISINDO 1.600 Video (Batching & Checkpoint)")
    parser.add_argument("--raw-dir", type=str, default="data/raw/video/wl_bisindo/videos")
    parser.add_argument("--out-dir", type=str, default="data/keypoints/wl_bisindo")
    parser.add_argument("--manifest-file", type=str, default="data/manifest_wl_bisindo.csv")
    parser.add_argument("--checkpoint-file", type=str, default="data/keypoints/wl_bisindo/checkpoint.json")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()

    run_mass_extraction(
        raw_dir=Path(args.raw_dir),
        out_dir=Path(args.out_dir),
        manifest_file=Path(args.manifest_file),
        checkpoint_file=Path(args.checkpoint_file),
        batch_size=args.batch_size,
        max_workers=args.max_workers,
    )


if __name__ == "__main__":
    main()

