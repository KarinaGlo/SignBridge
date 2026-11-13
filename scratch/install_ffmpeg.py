import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

TARGET_DIR = Path(r"C:\Tools\ffmpeg")
BIN_DIR = TARGET_DIR / "bin"
DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
EXPECTED_SHA256 = "60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba"
TMP_ZIP = TARGET_DIR / "ffmpeg_temp.zip"

def main():
    print(f"Creating target directory: {TARGET_DIR}")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading from {DOWNLOAD_URL} ...")
    req = urllib.request.Request(
        DOWNLOAD_URL, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req) as resp, open(TMP_ZIP, "wb") as out_f:
        shutil.copyfileobj(resp, out_f)
        
    print(f"Download complete: {TMP_ZIP.stat().st_size} bytes")
    
    # Verify SHA-256
    h = hashlib.sha256()
    with open(TMP_ZIP, "rb") as f:
        while chunk := f.read(1024*1024):
            h.update(chunk)
    actual_sha = h.hexdigest().lower()
    print(f"Computed SHA-256: {actual_sha}")
    print(f"Expected SHA-256: {EXPECTED_SHA256}")
    
    if actual_sha != EXPECTED_SHA256:
        print("ERROR: SHA-256 mismatch! Aborting installation.")
        sys.exit(1)
        
    print("SHA-256 match confirmed. Extracting binaries...")
    with zipfile.ZipFile(TMP_ZIP, "r") as zf:
        for member in zf.namelist():
            if member.endswith("bin/ffmpeg.exe") or member.endswith("bin/ffprobe.exe"):
                filename = Path(member).name
                dest = BIN_DIR / filename
                print(f"Extracting {member} -> {dest}")
                with zf.open(member) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                    
    # Clean up temp zip
    if TMP_ZIP.exists():
        TMP_ZIP.unlink()
        print("Cleaned up temporary zip archive.")
        
    ffmpeg_exe = BIN_DIR / "ffmpeg.exe"
    ffprobe_exe = BIN_DIR / "ffprobe.exe"
    
    if not (ffmpeg_exe.exists() and ffprobe_exe.exists()):
        print("ERROR: Binaries not found after extraction!")
        sys.exit(1)
        
    print(f"Installed FFmpeg: {ffmpeg_exe} ({ffmpeg_exe.stat().st_size} bytes)")
    print(f"Installed FFprobe: {ffprobe_exe} ({ffprobe_exe.stat().st_size} bytes)")
    
    # Run version check
    res1 = subprocess.run([str(ffmpeg_exe), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("\n--- FFmpeg Version ---")
    print("\n".join(res1.stdout.splitlines()[:2]))
    
    res2 = subprocess.run([str(ffprobe_exe), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("\n--- FFprobe Version ---")
    print("\n".join(res2.stdout.splitlines()[:2]))
    
    print("\nInstallation successful!")

if __name__ == "__main__":
    main()

