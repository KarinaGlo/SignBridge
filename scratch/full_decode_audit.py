import concurrent.futures
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(r"c:\Users\PC\Downloads\Semester 5\ML")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from signbridge.data.video_metadata import WLBISINDO_LABELS

FFMPEG = Path(r"C:\Tools\ffmpeg\bin\ffmpeg.exe")
VIDEOS_DIR = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "videos"
PREV_CSV = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "wl_bisindo_decode_audit.csv"
OUT_CSV = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "wl_bisindo_decode_audit.csv"
OUT_SUMMARY_JSON = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "wl_bisindo_decode_audit_summary.json"
CHECKPOINT_FILE = WORKSPACE_ROOT / "scratch" / "full_decode_checkpoint.json"

def decode_single_video(row):
    filename = row["filename"]
    video_path = VIDEOS_DIR / filename
    
    cmd = [
        str(FFMPEG),
        "-v", "error",
        "-xerror",
        "-i", str(video_path),
        "-map", "0:v:0",
        "-f", "null",
        "-progress", "pipe:1",
        "NUL"
    ]
    
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        elapsed = time.time() - t0
        exit_code = proc.returncode
        stderr_err = proc.stderr.strip()
        
        # Parse decoded frames
        last_frame = 0
        for line in proc.stdout.splitlines():
            if line.startswith("frame="):
                val = line.split("=", 1)[1].strip()
                if val.isdigit():
                    last_frame = int(val)
                    
        if exit_code == 0 and not stderr_err and last_frame > 0:
            status = "FULL_DECODE_VALID"
            err_msg = ""
        elif exit_code == 0 and last_frame > 0:
            # Succeeded with minor non-fatal warnings
            status = "FULL_DECODE_VALID"
            err_msg = stderr_err
        elif last_frame > 0 and exit_code != 0:
            status = "PARTIAL_DECODE"
            err_msg = stderr_err
        else:
            status = "DECODE_FAILED"
            err_msg = stderr_err or f"Process failed with exit code {exit_code}"
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        exit_code = -1
        last_frame = 0
        status = "DECODE_FAILED"
        err_msg = "Decoding timed out after 60s"
    except Exception as e:
        elapsed = time.time() - t0
        exit_code = -1
        last_frame = 0
        status = "DECODE_FAILED"
        err_msg = str(e)
        
    return {
        "filename": filename,
        "decode_status": status,
        "decode_error": err_msg,
        "decode_exit_code": exit_code,
        "decode_duration_sec": round(elapsed, 3),
        "decoded_frame_count": last_frame if last_frame > 0 else "",
    }

def main():
    print(f"Loading previous metadata from: {PREV_CSV}")
    with open(PREV_CSV, "r", encoding="utf-8") as f:
        meta_rows = list(csv.DictReader(f))
    print(f"Loaded {len(meta_rows)} video records.")
    
    # Load checkpoint if exists
    checkpoint = {}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded existing checkpoint with {len(checkpoint)} records.")
        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            checkpoint = {}
            
    to_process = [r for r in meta_rows if r["filename"] not in checkpoint or checkpoint[r["filename"]].get("decode_status") != "FULL_DECODE_VALID"]
    print(f"Videos remaining to decode: {len(to_process)}")
    
    total_start = time.time()
    completed_count = len(checkpoint)
    
    # Process using ThreadPoolExecutor with 2 workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_fn = {executor.submit(decode_single_video, row): row["filename"] for row in to_process}
        
        for future in concurrent.futures.as_completed(future_to_fn):
            fn = future_to_fn[future]
            try:
                res = future.result()
                checkpoint[fn] = res
                completed_count += 1
                
                if completed_count % 100 == 0 or completed_count == len(meta_rows):
                    print(f"Progress: {completed_count}/{len(meta_rows)} ({completed_count/len(meta_rows)*100:.1f}%) videos decoded...")
                    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                        json.dump(checkpoint, f)
            except Exception as e:
                print(f"Error processing {fn}: {e}")
                
    # Final checkpoint save
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)
        
    total_time = round(time.time() - total_start, 2)
    print(f"Decoding complete in {total_time} seconds.")
    
    # Merge results into final CSV
    final_rows = []
    status_counts = {
        "FULL_DECODE_VALID": 0,
        "PARTIAL_DECODE": 0,
        "DECODE_FAILED": 0,
        "METADATA_INVALID": 0,
        "HEADER_VALID_ONLY": 0,
        "NOT_TESTED": 0,
    }
    codec_counts = {}
    resolution_counts = {}
    durations = []
    fps_counts = {}
    frame_counts = []
    bad_videos = []
    
    for r in meta_rows:
        fn = r["filename"]
        cp = checkpoint.get(fn, {})
        
        st = cp.get("decode_status", "NOT_TESTED")
        status_counts[st] = status_counts.get(st, 0) + 1
        
        codec = r.get("codec", "")
        codec_counts[codec] = codec_counts.get(codec, 0) + 1
        
        res = f"{r.get('width', 0)}x{r.get('height', 0)}"
        resolution_counts[res] = resolution_counts.get(res, 0) + 1
        
        try:
            durations.append(float(r.get("duration_sec", 0)))
        except:
            pass
            
        try:
            fps_val = float(r.get("fps", 0))
            fps_counts[fps_val] = fps_counts.get(fps_val, 0) + 1
        except:
            pass
            
        dec_fc = cp.get("decoded_frame_count", "")
        if dec_fc != "":
            try:
                frame_counts.append(int(dec_fc))
            except:
                pass
                
        if st != "FULL_DECODE_VALID":
            bad_videos.append({
                "filename": fn,
                "status": st,
                "error": cp.get("decode_error", ""),
                "exit_code": cp.get("decode_exit_code", -1)
            })
            
        merged_row = {
            "filename": r["filename"],
            "relative_path": r["relative_path"],
            "sha256": r["sha256"],
            "label_id": r["label_id"],
            "confirmed_gloss": r["confirmed_gloss"],
            "signer_id": r["signer_id"],
            "file_size_bytes": r["file_size_bytes"],
            "width": r["width"],
            "height": r["height"],
            "fps": r["fps"],
            "duration_sec": r["duration_sec"],
            "codec": r["codec"],
            "expected_frame_count": r["expected_frame_count"],
            "decoded_frame_count": cp.get("decoded_frame_count", ""),
            "decode_status": st,
            "decode_error": cp.get("decode_error", ""),
            "decode_exit_code": cp.get("decode_exit_code", 0 if st == "FULL_DECODE_VALID" else -1),
            "decode_duration_sec": cp.get("decode_duration_sec", 0.0),
            "mapping_status": r["mapping_status"],
            "source": r["source"],
        }
        final_rows.append(merged_row)
        
    # Write final CSV
    fieldnames = [
        "filename",
        "relative_path",
        "sha256",
        "label_id",
        "confirmed_gloss",
        "signer_id",
        "file_size_bytes",
        "width",
        "height",
        "fps",
        "duration_sec",
        "codec",
        "expected_frame_count",
        "decoded_frame_count",
        "decode_status",
        "decode_error",
        "decode_exit_code",
        "decode_duration_sec",
        "mapping_status",
        "source",
    ]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(final_rows)
        
    print(f"Updated decode audit CSV written: {OUT_CSV}")
    
    # Write summary JSON
    summary = {
        "dataset": "WL-BISINDO",
        "total_videos": len(final_rows),
        "status_distribution": status_counts,
        "codecs": codec_counts,
        "resolutions": resolution_counts,
        "duration_stats": {
            "min_sec": min(durations) if durations else 0,
            "max_sec": max(durations) if durations else 0,
            "avg_sec": round(sum(durations)/len(durations), 3) if durations else 0,
        },
        "frame_stats": {
            "min_frames": min(frame_counts) if frame_counts else 0,
            "max_frames": max(frame_counts) if frame_counts else 0,
            "avg_frames": round(sum(frame_counts)/len(frame_counts), 1) if frame_counts else 0,
        },
        "fps_distribution": {
            "30.0_fps": sum(v for k, v in fps_counts.items() if abs(k - 30.0) < 0.05),
            "vfr_fps_count": sum(v for k, v in fps_counts.items() if abs(k - 30.0) >= 0.05),
            "vfr_fps_range": f"{min(fps_counts.keys())} - {max(fps_counts.keys())}" if fps_counts else "",
        },
        "total_decoding_time_sec": total_time,
        "bad_videos_count": len(bad_videos),
        "bad_videos": bad_videos,
    }
    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\nAudit Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

