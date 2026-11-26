"""
signbridge/xmf/audio_bank.py — Bank AUDIO & TEKS per konsep (bagian dari TAHAP 2 ingestion).

Kenapa ada bank: WL-BISINDO hanya berisi video. Modalitas audio (ucapan pendengar, mis. guru) dan
teks (ketikan) dipasangkan ke klip di tingkat KONSEP: klip AIR dipasangkan dengan ucapan "air" dan
teks "air putih". Pemasangan dilakukan SEKALI di preprocess.py sehingga setiap sampel tersimpan
sebagai satu rekaman 4-modalitas.

Sumber audio (gabungkan sebanyak mungkin — makin banyak suara asli makin akurat di kelas):
  1. Rekaman asli relawan : data/raw/audio/<task>/<KONSEP>/<penutur>_*.wav   (DISARANKAN)
  2. TTS                  : edge-tts (id-ID-ArdiNeural, id-ID-GadisNeural), gTTS, espeak-ng
                            -> disimpan ke data/raw/audio_tts/<task>/<KONSEP>/*.wav (cache)

Keluaran: data/xmf/bank/<task>_audio.npz  {wave[N,40000] float16, label[N], split[N], source[N], speaker[N]}

Contoh:
    python -m signbridge.xmf.audio_bank --task gloss --tts edge,gtts,espeak
    python -m signbridge.xmf.audio_bank --task alphabet --tts espeak
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from signbridge.xmf.config import AUDIO_SR, SHAPES, classes_for, speech_scripts_for
from signbridge.xmf.ops import fit_audio, resample_linear, stable_hash

ROOT = Path(__file__).resolve().parents[2]
EDGE_VOICES = ["id-ID-ArdiNeural", "id-ID-GadisNeural"]
EDGE_RATES = ["-10%", "+0%", "+15%"]


# ---------------------------------------------------------------------------
# Baca / tulis WAV (tanpa dependensi tambahan); format lain via ffmpeg
# ---------------------------------------------------------------------------
def read_audio(path: Path) -> Tuple[np.ndarray, int]:
    if path.suffix.lower() != ".wav":
        return _ffmpeg_decode(path)
    try:
        with wave.open(str(path), "rb") as wf:
            ch, width, sr = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
            raw = wf.readframes(wf.getnframes())
        if width != 2:
            return _ffmpeg_decode(path)
        x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        return x, sr
    except wave.Error:
        return _ffmpeg_decode(path)


def _ffmpeg_decode(path: Path) -> Tuple[np.ndarray, int]:
    if not shutil.which("ffmpeg"):
        raise RuntimeError(f"ffmpeg diperlukan untuk membaca {path.suffix} ({path})")
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(AUDIO_SR), "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(out, dtype="<i2").astype(np.float32) / 32768.0, AUDIO_SR


def write_wav(path: Path, pcm: np.ndarray, sr: int = AUDIO_SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data)


# ---------------------------------------------------------------------------
# Mesin TTS
# ---------------------------------------------------------------------------
def tts_edge(text: str, out: Path) -> List[Path]:
    import edge_tts  # pip install edge-tts

    made = []
    for voice in EDGE_VOICES:
        for rate in EDGE_RATES:
            dst = out / f"edge_{voice}_{rate.replace('%', '')}_{stable_hash(text):x}.wav"
            if dst.exists():
                made.append(dst)
                continue
            with tempfile.TemporaryDirectory() as td:
                mp3 = Path(td) / "a.mp3"
                asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(str(mp3)))
                pcm, sr = _ffmpeg_decode(mp3)
            write_wav(dst, pcm, sr)
            made.append(dst)
    return made


def tts_gtts(text: str, out: Path) -> List[Path]:
    from gtts import gTTS  # pip install gTTS

    made = []
    for slow in (False, True):
        dst = out / f"gtts_{'slow' if slow else 'norm'}_{stable_hash(text):x}.wav"
        if not dst.exists():
            with tempfile.TemporaryDirectory() as td:
                mp3 = Path(td) / "a.mp3"
                gTTS(text, lang="id", slow=slow).save(str(mp3))
                pcm, sr = _ffmpeg_decode(mp3)
            write_wav(dst, pcm, sr)
        made.append(dst)
    return made


def tts_espeak(text: str, out: Path) -> List[Path]:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("espeak-ng tidak terpasang (apt install espeak-ng)")
    made = []
    for voice in ("id", "id+m3", "id+f3", "id+m7", "id+f4"):
        for speed in (140, 170):
            dst = out / f"espeak_{voice.replace('+', '-')}_{speed}_{stable_hash(text):x}.wav"
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run([exe, "-v", voice, "-s", str(speed), "-w", str(dst), text],
                               check=True, capture_output=True)
            made.append(dst)
    return made


TTS_ENGINES = {"edge": tts_edge, "gtts": tts_gtts, "espeak": tts_espeak}


# ---------------------------------------------------------------------------
# Bangun bank
# ---------------------------------------------------------------------------
def _split_for(speaker: str) -> str:
    b = stable_hash(speaker) % 100
    return "train" if b < 70 else ("val" if b < 85 else "test")


def build_bank(task: str, engines: List[str], real_dir: Path, tts_dir: Path, out_path: Path) -> dict:
    classes = classes_for(task)
    scripts = speech_scripts_for(task)
    n = SHAPES[task].audio_samples
    waves, labels, splits, sources, speakers = [], [], [], [], []

    def add(path: Path, label: int, source: str, speaker: str, split: Optional[str] = None) -> None:
        try:
            pcm, sr = read_audio(path)
        except Exception as e:  # noqa: BLE001
            print(f"[audio_bank] lewati {path.name}: {e}")
            return
        x = fit_audio(resample_linear(pcm, sr), n=n)
        if np.max(np.abs(x)) < 1e-4:
            return
        waves.append(x.astype(np.float16))
        labels.append(label)
        sources.append(source)
        speakers.append(speaker)
        splits.append(split or _split_for(speaker))

    # 1) rekaman asli: <real_dir>/<KONSEP>/<penutur>_xxx.wav
    for ci, concept in enumerate(classes):
        d = real_dir / concept
        for p in sorted(d.glob("*")) if d.exists() else []:
            if p.suffix.lower() in {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}:
                add(p, ci, "real", "real:" + p.stem.split("_")[0])

    # 2) TTS; tiap (mesin, suara) dianggap satu "penutur". Split per naskah agar tiap split punya semua konsep.
    for eng in engines:
        fn = TTS_ENGINES[eng]
        try:
            for ci, concept in enumerate(classes):
                for vi, text in enumerate(scripts[concept]):
                    for p in fn(text, tts_dir / concept):
                        add(p, ci, "tts", "tts:" + "_".join(p.stem.split("_")[:-1]), "pending")
        except Exception as e:  # noqa: BLE001
            print(f"[audio_bank] TTS '{eng}' gagal ({e}); mesin ini dilewati.")

    # Split TTS per SUARA (penutur): semua naskah ada di train, val/test = suara yang tidak pernah dilatih.
    tts_speakers = sorted({sp for sp, sl in zip(speakers, splits) if sl == "pending"})
    sp_split = {sp: ("val" if i % 7 == 5 else "test" if i % 7 == 6 else "train") for i, sp in enumerate(tts_speakers)}
    splits = [sp_split[sp] if sl == "pending" else sl for sp, sl in zip(speakers, splits)]

    if not waves:
        raise SystemExit(
            "Bank audio kosong. Rekam suara ke data/raw/audio/<task>/<KONSEP>/ atau pasang TTS "
            "(pip install edge-tts gTTS / apt install espeak-ng ffmpeg)."
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path, wave=np.stack(waves), label=np.array(labels, dtype=np.int64),
        split=np.array(splits), source=np.array(sources), speaker=np.array(speakers),
        classes=np.array(classes),
    )
    lab = np.array(labels)
    missing = [classes[i] for i in range(len(classes)) if not np.any(lab == i)]
    summary = {"n": len(waves), "real": sources.count("real"), "tts": sources.count("tts"),
               "per_split": {s: splits.count(s) for s in ("train", "val", "test")},
               "concepts_without_audio": missing}
    print(f"[audio_bank] {task}: {summary}")
    return summary


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["gloss", "alphabet"], default="gloss")
    ap.add_argument("--tts", default="edge,gtts,espeak", help="urutan mesin TTS, pisah koma; '' = tanpa TTS")
    ap.add_argument("--real-dir", type=Path, default=None)
    ap.add_argument("--tts-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    engines = [e.strip() for e in a.tts.split(",") if e.strip()]
    build_bank(
        a.task, engines,
        a.real_dir or ROOT / "data/raw/audio" / a.task,
        a.tts_dir or ROOT / "data/raw/audio_tts" / a.task,
        a.out or ROOT / "data/xmf/bank" / f"{a.task}_audio.npz",
    )


if __name__ == "__main__":
    main()
