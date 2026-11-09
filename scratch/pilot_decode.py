import csv
import json
import subprocess
import time
from pathlib import Path

FFMPEG = Path(r"C:\Tools\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\Tools\ffmpeg\bin\ffprobe.exe")
VIDEOS_DIR = Path(r"c:\Users\PC\Downloads\Semester 5\ML\data\raw\video\wl_bisindo\videos")
AUDIT_CSV = Path(r"c:\Users\PC\Downloads\Semester 5\ML\data\raw\video\wl_bisindo\wl_bisindo_decode_audit.csv")

def main():
    with open(AUDIT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    avc_rows = [r for r in rows if r["codec"] == "avc1"]
    hevc_rows = [r for r in rows if r["codec"] == "hevc"]

    pilot_candidates = [
        # 5 AVC samples (signer 0, 1, 2, 3, 4, various resolutions and durations)
        avc_rows[0],   # signer0_label0_sample1 (1280x720, 2.7s)
        avc_rows[25],  # signer1 (1280x720)
        avc_rows[50],  # signer2 (1280x720)
        avc_rows[80],  # signer3 (1280x720)
        avc_rows[-1],  # signer4 (1280x720)
        # 5 HEVC samples (signer 0, 1, 2, 3, 4, 1920x1080, various lengths)
        hevc_rows[0],    # signer0_label1_sample1 (1920x1080)
        hevc_rows[100],  # signer1
        hevc_rows[300],  # signer2
        hevc_rows[800],  # signer3
        hevc_rows[-1],   # signer4 (durasi panjang)
    ]

    print("================================================================================")
    print("PILOT DECODE AUDIT: 10 REPRESENTATIVE VIDEOS")
    print("================================================================================")

    pilot_results = []
    all_passed = True

    for idx, c in enumerate(pilot_candidates, 1):
        filename = c["filename"]
        video_path = VIDEOS_DIR / filename
        
        # 1. FFprobe metadata check
        ffprobe_cmd = [
            str(FFPROBE),
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
            "-of", "json",
            str(video_path)
        ]
        t0 = time.time()
        p_probe = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe_time = time.time() - t0
        
        probe_data = {}
        if p_probe.returncode == 0:
            try:
                probe_data = json.loads(p_probe.stdout).get("streams", [{}])[0]
            except Exception as e:
                probe_data = {"error": str(e)}

        # 2. FFmpeg full frame decode check
        ffmpeg_cmd = [
            str(FFMPEG),
            "-v", "error",
            "-xerror",
            "-i", str(video_path),
            "-map", "0:v:0",
            "-f", "null",
            "NUL"
        ]
        t1 = time.time()
        p_decode = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        decode_time = time.time() - t1

        probe_ok = (p_probe.returncode == 0 and "codec_name" in probe_data)
        decode_ok = (p_decode.returncode == 0 and len(p_decode.stderr.strip()) == 0)
        passed = probe_ok and decode_ok
        if not passed:
            all_passed = False

        status_str = "PASS" if passed else "FAIL"

        res = {
            "index": idx,
            "filename": filename,
            "codec": probe_data.get("codec_name", c["codec"]),
            "width": probe_data.get("width", c["width"]),
            "height": probe_data.get("height", c["height"]),
            "duration": probe_data.get("duration", c["duration_sec"]),
            "ffprobe_exit": p_probe.returncode,
            "ffmpeg_exit": p_decode.returncode,
            "decode_duration_sec": round(decode_time, 3),
            "decode_error": p_decode.stderr.strip(),
            "status": status_str,
        }
        pilot_results.append(res)
        
        print(f"[{idx:2d}/10] {filename:<32} {res['codec']:<6} {res['width']}x{res['height']} dur={res['duration']}s | probe_rc={res['ffprobe_exit']} decode_rc={res['ffmpeg_exit']} ({res['decode_duration_sec']}s) -> {status_str}")
        if not passed:
            print(f"     Probe Error: {p_probe.stderr.strip()}")
            print(f"     Decode Error: {p_decode.stderr.strip()}")

    print("================================================================================")
    print(f"Pilot Result: {'ALL 10 VIDEOS PASSED' if all_passed else 'SOME VIDEOS FAILED'}")
    print("================================================================================")

    # Save summary
    with open("scratch/pilot_results.json", "w", encoding="utf-8") as out_f:
        json.dump({"all_passed": all_passed, "results": pilot_results}, out_f, indent=2)

if __name__ == "__main__":
    main()

