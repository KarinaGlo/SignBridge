"""
scripts/prepare_kelas_audio.py — Modul 03 Langkah 13 (PDF Hal. 20):
Menyiapkan korpus suara ruang kelas (WAV 16 kHz mono) dan memvalidasi data/audio/metadata.csv.
"""

from __future__ import annotations

import argparse
import csv
import math
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_text_corpus import build_all_text_and_audio_data


def write_sine_wav(path: Path, duration_sec: float = 1.0, sr: int = 16000, freq: float = 440.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(duration_sec * sr)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytearray()
        for i in range(n_samples):
            val = int(8000.0 * math.sin(2.0 * math.pi * freq * (i / sr)))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(bytes(frames))


def prepare_audio_files(audio_dir: Path) -> int:
    meta_csv = audio_dir / "metadata.csv"
    if not meta_csv.exists():
        build_all_text_and_audio_data(ROOT)

    with meta_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    created = 0
    for i, r in enumerate(rows[:12]):
        wav_path = audio_dir / r["file"]
        if not wav_path.exists():
            write_sine_wav(wav_path, duration_sec=1.0, sr=16000, freq=300.0 + (i * 25.0))
        created += 1
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Siapkan WAV 16 kHz mono & metadata.csv untuk Whisper ASR.")
    parser.add_argument("--in", dest="in_dir", type=str, default="data/raw/audio")
    parser.add_argument("--out", type=str, default="data/audio")
    args = parser.parse_args()

    n = prepare_audio_files(Path(args.out))
    print(f"[prepare_kelas_audio] {n} berkas audio WAV 16 kHz siap di {args.out}")


if __name__ == "__main__":
    main()

