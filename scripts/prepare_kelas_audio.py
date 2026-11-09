"""
scripts/prepare_kelas_audio.py — Modul 03 Langkah 13 (PDF Hal. 20):
Memvalidasi korpus suara ruang kelas (WAV 16 kHz mono) terhadap data/audio/metadata.csv.

Keamanan Pipeline (Tahap A):
- Fungsi pembuatan gelombang sinus sintetis (`write_sine_wav`) telah dihapus sepenuhnya.
- Tidak pernah membuat berkas `.wav` palsu atau menimpa `data/audio/metadata.csv` yang sudah ada.
- Jika berkas `.wav` fisik belum tersedia di disk, melaporkan status `NOT AVAILABLE` secara eksplisit
  dan menghentikan proses dengan `FileNotFoundError`.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from signbridge.audio.train_asr import load_wav_waveform


def inspect_kelas_audio_status(audio_dir: Path) -> Dict[str, Any]:
    """
    Periksa keberadaan fisik berkas `.wav` yang direferensikan di dalam `audio_dir / metadata.csv`
    tanpa membuat audio sintetis dan tanpa mengubah `metadata.csv`.
    """
    audio_dir = Path(audio_dir)
    if not audio_dir.exists():
        raise FileNotFoundError(f"Direktori audio tidak ditemukan: {audio_dir}")

    meta_csv = audio_dir / "metadata.csv"
    if not meta_csv.exists() or not meta_csv.is_file():
        raise FileNotFoundError(f"Berkas metadata audio tidak ditemukan: {meta_csv}")

    with meta_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "file" not in reader.fieldnames or "text" not in reader.fieldnames:
            raise ValueError(
                f"Header metadata audio tidak valid pada {meta_csv}: diharapkan kolom 'file' dan 'text', "
                f"diperoleh {reader.fieldnames}"
            )
        rows = list(reader)

    if not rows:
        raise ValueError(f"Berkas metadata audio kosong (0 baris data): {meta_csv}")

    available_files: List[str] = []
    missing_files: List[str] = []
    corrupt_files: List[str] = []

    for row in rows:
        rel_file = (row.get("file") or "").strip()
        if not rel_file:
            raise ValueError(f"Baris pada {meta_csv} memiliki kolom 'file' kosong: {row}")
        wav_path = audio_dir / rel_file
        if not wav_path.exists() or not wav_path.is_file():
            missing_files.append(str(wav_path.as_posix()))
            continue
        try:
            waveform, sr = load_wav_waveform(wav_path)
            if waveform.size == 0 or sr <= 0:
                corrupt_files.append(str(wav_path.as_posix()))
            else:
                available_files.append(str(wav_path.as_posix()))
        except Exception:
            corrupt_files.append(str(wav_path.as_posix()))

    status = "AVAILABLE" if (len(available_files) == len(rows) and not corrupt_files) else "NOT AVAILABLE"
    return {
        "metadata_csv": str(meta_csv.as_posix()),
        "total_expected": len(rows),
        "available_count": len(available_files),
        "missing_count": len(missing_files),
        "corrupt_count": len(corrupt_files),
        "available_files": available_files,
        "missing_files": missing_files,
        "corrupt_files": corrupt_files,
        "status": status,
    }


def prepare_audio_files(audio_dir: Path, strict: bool = True) -> int:
    """
    Validasi ketersediaan berkas `.wav` ruang kelas di `audio_dir`.
    Tidak pernah membuat gelombang sinus sintetis. Jika ada berkas `.wav` yang belum tersedia
    atau rusak dan `strict=True`, lempar FileNotFoundError / ValueError dengan status `NOT AVAILABLE`.
    """
    report = inspect_kelas_audio_status(audio_dir)
    if report["corrupt_count"] > 0:
        raise ValueError(
            f"Ditemukan {report['corrupt_count']} berkas WAV rusak di {audio_dir}: "
            f"{report['corrupt_files'][:3]}"
        )
    if report["missing_count"] > 0:
        msg = (
            f"[prepare_kelas_audio] STATUS: NOT AVAILABLE — "
            f"{report['missing_count']} dari {report['total_expected']} berkas WAV fisik belum tersedia "
            f"di {audio_dir} (contoh: {report['missing_files'][0]}). "
            "Pembuatan gelombang sinus sintetis telah dinonaktifkan."
        )
        print(msg)
        if strict:
            raise FileNotFoundError(msg)
        return report["available_count"]

    return report["available_count"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validasi WAV 16 kHz mono & metadata.csv untuk Whisper ASR.")
    parser.add_argument("--in", dest="in_dir", type=str, default="data/raw/audio")
    parser.add_argument("--out", type=str, default="data/audio")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Hanya tampilkan laporan NOT AVAILABLE tanpa keluar dengan exception",
    )
    args = parser.parse_args()

    n = prepare_audio_files(Path(args.out), strict=not args.allow_missing)
    print(f"[prepare_kelas_audio] {n} berkas audio WAV 16 kHz tervalidasi di {args.out}")


if __name__ == "__main__":
    main()


