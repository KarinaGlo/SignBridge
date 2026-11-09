import csv
import hashlib
import json
import os
import re
import struct
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(r"c:\Users\PC\Downloads\Semester 5\ML")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from signbridge.data.video_metadata import WLBISINDO_LABELS

VIDEOS_DIR = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "videos"
OUT_CSV = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "wl_bisindo_decode_audit.csv"
OUT_SUMMARY_JSON = WORKSPACE_ROOT / "data" / "raw" / "video" / "wl_bisindo" / "wl_bisindo_decode_audit_summary.json"

FILENAME_PATTERN = re.compile(r"^signer(?P<signer>\d+)_label(?P<label>\d+)_sample(?P<sample>\d+)\.mp4$", re.IGNORECASE)

def parse_iso_bmff(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    
    file_size = len(data)
    if file_size < 16:
        return None, "File too small for MP4 header"
    
    # Locate ftyp and moov
    offset = 0
    header_valid = False
    moov_data = None
    
    while offset + 8 <= file_size:
        box_size = struct.unpack(">I", data[offset:offset+4])[0]
        box_type = data[offset+4:offset+8]
        
        if box_size == 1:
            if offset + 16 > file_size:
                break
            box_size = struct.unpack(">Q", data[offset+8:offset+16])[0]
            payload_start = offset + 16
        elif box_size == 0:
            box_size = file_size - offset
            payload_start = offset + 8
        else:
            payload_start = offset + 8
            
        if box_type == b"ftyp":
            header_valid = True
            
        if box_type == b"moov":
            moov_data = data[payload_start:offset+box_size]
            
        offset += box_size
        
    if not header_valid or moov_data is None:
        return None, "Missing ftyp or moov box"
        
    # Parse mvhd for movie duration
    mvhd_idx = moov_data.find(b"mvhd")
    duration_sec = 0.0
    if mvhd_idx != -1:
        body = moov_data[mvhd_idx+4:]
        version = body[0]
        if version == 0 and len(body) >= 20:
            timescale, duration = struct.unpack(">II", body[12:20])
            if timescale > 0:
                duration_sec = duration / timescale
        elif version == 1 and len(body) >= 32:
            timescale = struct.unpack(">I", body[20:24])[0]
            duration = struct.unpack(">Q", body[24:32])[0]
            if timescale > 0:
                duration_sec = duration / timescale

    # Iterate traks inside moov to find the video track
    pos = 0
    width = 0
    height = 0
    sample_count = 0
    codec = "unknown"
    
    while pos + 8 <= len(moov_data):
        sz = struct.unpack(">I", moov_data[pos:pos+4])[0]
        bt = moov_data[pos+4:pos+8]
        if sz == 1 and pos + 16 <= len(moov_data):
            sz = struct.unpack(">Q", moov_data[pos+8:pos+16])[0]
        if sz == 0 or pos + sz > len(moov_data):
            break
            
        if bt == b"trak":
            trak = moov_data[pos:pos+sz]
            # search for tkhd in this trak
            tkhd_i = trak.find(b"tkhd")
            if tkhd_i != -1 and tkhd_i >= 4:
                tkhd_sz = struct.unpack(">I", trak[tkhd_i-4:tkhd_i])[0]
                if tkhd_i - 4 + tkhd_sz <= len(trak):
                    tkhd = trak[tkhd_i-4:tkhd_i-4+tkhd_sz]
                    w_cand = struct.unpack(">I", tkhd[-8:-4])[0] / 65536.0
                    h_cand = struct.unpack(">I", tkhd[-4:])[0] / 65536.0
                    if w_cand > 0 and h_cand > 0:
                        width = int(round(w_cand))
                        height = int(round(h_cand))
                        # parse stsz in this video trak
                        stsz_i = trak.find(b"stsz")
                        if stsz_i != -1 and stsz_i + 16 <= len(trak):
                            sample_count = struct.unpack(">I", trak[stsz_i+12:stsz_i+16])[0]
                        if b"avc1" in trak:
                            codec = "avc1"
                        elif b"mp4v" in trak:
                            codec = "mp4v"
                        elif b"hvc1" in trak or b"hev1" in trak:
                            codec = "hevc"
                        break
        pos += sz
        
    fps = 0.0
    if duration_sec > 0 and sample_count > 0:
        fps = round(sample_count / duration_sec, 2)
        
    return {
        "header_valid": header_valid,
        "width": width,
        "height": height,
        "duration_sec": round(duration_sec, 3),
        "codec": codec,
        "expected_frame_count": sample_count,
        "fps": fps,
    }, None

def main():
    print("Starting WL-BISINDO Full Decode Audit analysis...")
    start_time = time.time()
    
    video_files = sorted(list(VIDEOS_DIR.glob("*.mp4")))
    print(f"Total video files found: {len(video_files)}")
    
    rows = []
    decoder_missing_err = "Decoder unavailable: ffmpeg/ffprobe/cv2/av not installed in environment"
    
    resolutions = {}
    durations = []
    frame_counts = []
    fps_counts = {}
    codec_counts = {}
    status_counts = {
        "FULL_DECODE_VALID": 0,
        "HEADER_VALID_ONLY": 0,
        "PARTIAL_DECODE": 0,
        "DECODE_FAILED": 0,
        "METADATA_INVALID": 0,
        "NOT_TESTED": 0,
    }
    
    for idx, vf in enumerate(video_files, 1):
        filename = vf.name
        rel_path = f"data/raw/video/wl_bisindo/videos/{filename}"
        file_size = vf.stat().st_size
        
        # SHA-256
        h = hashlib.sha256()
        with open(vf, "rb") as f:
            while chunk := f.read(1024*1024):
                h.update(chunk)
        sha256_hex = h.hexdigest()
        
        # Parse filename
        m = FILENAME_PATTERN.match(filename)
        if not m:
            signer_id = "UNKNOWN"
            label_id = -1
        else:
            signer_id = f"SIGNER{m.group('signer')}"
            label_id = int(m.group("label"))
            
        confirmed_gloss = WLBISINDO_LABELS.get(label_id, "UNKNOWN")
        mapping_status = "CONFIRMED" if label_id in WLBISINDO_LABELS else "UNVERIFIED"
        
        info, err = parse_iso_bmff(vf)
        if err or not info:
            decode_status = "METADATA_INVALID"
            decode_error = f"{decoder_missing_err}; Container error: {err}"
            width, height, fps, dur, codec, expected_frames = 0, 0, 0.0, 0.0, "", ""
        else:
            decode_status = "HEADER_VALID_ONLY"
            decode_error = decoder_missing_err
            width = info["width"]
            height = info["height"]
            fps = info["fps"]
            dur = info["duration_sec"]
            codec = info["codec"]
            expected_frames = info["expected_frame_count"]
            
            res_key = f"{width}x{height}"
            resolutions[res_key] = resolutions.get(res_key, 0) + 1
            durations.append(dur)
            frame_counts.append(expected_frames)
            fps_counts[fps] = fps_counts.get(fps, 0) + 1
            codec_counts[codec] = codec_counts.get(codec, 0) + 1
            
        status_counts[decode_status] += 1
        
        row = {
            "filename": filename,
            "relative_path": rel_path,
            "sha256": sha256_hex,
            "label_id": label_id,
            "confirmed_gloss": confirmed_gloss,
            "signer_id": signer_id,
            "file_size_bytes": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "duration_sec": dur,
            "codec": codec,
            "expected_frame_count": expected_frames,
            "decoded_frame_count": "",
            "decode_status": decode_status,
            "decode_error": decode_error,
            "mapping_status": mapping_status,
            "source": "wl_bisindo",
        }
        rows.append(row)
        
        if idx % 400 == 0:
            print(f"Processed {idx}/{len(video_files)} videos...")
            
    # Write CSV
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
        "mapping_status",
        "source",
    ]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Audit manifest written to: {OUT_CSV}")
    
    elapsed = time.time() - start_time
    summary = {
        "total_audited": len(rows),
        "status_distribution": status_counts,
        "resolutions": resolutions,
        "codecs": codec_counts,
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
            "other_vfr_fps_range": f"{min(fps_counts.keys())} - {max(fps_counts.keys())}",
            "vfr_video_count": sum(v for k, v in fps_counts.items() if abs(k - 30.0) >= 0.05),
        },
        "audit_elapsed_sec": round(elapsed, 2),
    }
    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
