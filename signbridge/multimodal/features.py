"""
Preprocessing 4 modalitas untuk model fusion M6 (NumPy + Pillow, tanpa PyTorch).

Dipakai identik oleh:
  - pelatihan  : signbridge/train_multimodal.py
  - server     : server/multimodal_service.py (POST /predict_multimodal)
"""

from __future__ import annotations

import io
import json
import wave
from pathlib import Path
from typing import Optional, Sequence, Tuple, Union

import numpy as np

from signbridge.constants import IMAGENET_MEAN, IMAGENET_STD
from signbridge.features import preprocess_keypoints
from signbridge.multimodal.constants import (
    AUDIO_N_FFT,
    AUDIO_HOP,
    AUDIO_NUM_FRAMES,
    AUDIO_NUM_MELS,
    AUDIO_NUM_SAMPLES,
    AUDIO_SAMPLE_RATE,
    IMAGE_SIDE,
    POSE_SHAPE,
    TEXT_MAX_LEN,
)

PathLike = Union[str, Path]

# ---------------------------------------------------------------------------
# 1. VIDEO / POSE
# ---------------------------------------------------------------------------


def pose_from_sequence(kp_seq: Sequence) -> Tuple[np.ndarray, bool]:
    """
    Deret keypoint mentah [F, 86, 3] (koordinat MediaPipe 0..1) -> tensor [64, 86, 3]
    memakai pipeline Kontrak 3 (trim_inactive -> normalize_pose -> resample 64).
    Mengembalikan (pose, ada). `ada` False jika deret kosong/tidak valid.
    """
    arr = np.asarray(kp_seq, dtype=np.float32)
    if arr.ndim != 3 or arr.shape[0] == 0 or arr.shape[1:] != POSE_SHAPE[1:]:
        return np.zeros(POSE_SHAPE, dtype=np.float32), False
    # Titik (0,0,0) dari perekam = tidak terdeteksi -> NaN agar ditangani valid-mask
    arr = arr.copy()
    missing = np.all(np.abs(arr) < 1e-9, axis=-1)
    arr[missing] = np.nan
    if not np.any(np.isfinite(arr)):
        return np.zeros(POSE_SHAPE, dtype=np.float32), False
    pose, _mask = preprocess_keypoints(arr, target_len=POSE_SHAPE[0], trim=True)
    pose = np.nan_to_num(pose, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    return pose, True


def load_pose(kp_path: Optional[PathLike]) -> Tuple[np.ndarray, bool]:
    """Baca keypoint dari .json (perekam web: {"keypoints": [...]}) atau .npz/.npy (WL-BISINDO)."""
    if not kp_path:
        return np.zeros(POSE_SHAPE, dtype=np.float32), False
    p = Path(kp_path)
    if not p.exists():
        return np.zeros(POSE_SHAPE, dtype=np.float32), False
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        seq = data.get("keypoints", data) if isinstance(data, dict) else data
        return pose_from_sequence(seq)
    if p.suffix == ".npz":
        with np.load(p) as z:
            key = "keypoints" if "keypoints" in z.files else z.files[0]
            seq = z[key]
    else:
        seq = np.load(p)
    seq = np.asarray(seq, dtype=np.float32)
    if seq.shape == POSE_SHAPE:
        # Sudah dipreprocess (mis. .npz hasil ekstraksi WL-BISINDO)
        return np.nan_to_num(seq, nan=0.0).astype(np.float32), True
    return pose_from_sequence(seq)


# ---------------------------------------------------------------------------
# 2. CITRA (crop tangan)
# ---------------------------------------------------------------------------


def image_from_pil(img) -> np.ndarray:
    """PIL.Image -> float32 [3, 112, 112] ternormalisasi ImageNet (Kontrak 5, ukuran 112)."""
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((IMAGE_SIDE, IMAGE_SIDE))
    arr = np.asarray(img, dtype=np.float32) / 255.0  # [H, W, 3]
    mean = np.asarray(IMAGENET_MEAN, dtype=np.float32)
    std = np.asarray(IMAGENET_STD, dtype=np.float32)
    arr = (arr - mean) / std
    return np.ascontiguousarray(arr.transpose(2, 0, 1)).astype(np.float32)


def load_image(image_path: Optional[PathLike] = None, image_bytes: Optional[bytes] = None) -> Tuple[np.ndarray, bool]:
    empty = np.zeros((3, IMAGE_SIDE, IMAGE_SIDE), dtype=np.float32)
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return empty, False
    try:
        if image_bytes:
            with Image.open(io.BytesIO(image_bytes)) as im:
                return image_from_pil(im), True
        if image_path and Path(image_path).exists():
            with Image.open(image_path) as im:
                return image_from_pil(im), True
    except Exception:
        return empty, False
    return empty, False


# ---------------------------------------------------------------------------
# 3. AUDIO (WAV -> log-mel)
# ---------------------------------------------------------------------------


def read_wav(path_or_bytes: Union[PathLike, bytes]) -> Tuple[np.ndarray, int]:
    """Baca WAV PCM 16-bit (mono/stereo) memakai pustaka standar `wave`. Hasil float32 [-1, 1] mono."""
    src = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, (bytes, bytearray)) else str(path_or_bytes)
    with wave.open(src, "rb") as wf:
        n_ch = wf.getnchannels()
        width = wf.getsampwidth()
        sr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if width != 2:
        raise ValueError(f"Hanya WAV PCM 16-bit yang didukung (sampwidth={width}).")
    pcm = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if n_ch > 1:
        pcm = pcm.reshape(-1, n_ch).mean(axis=1)
    return pcm, sr


def write_wav(path: PathLike, pcm: np.ndarray, sr: int = AUDIO_SAMPLE_RATE) -> None:
    """Tulis float32 [-1,1] mono menjadi WAV PCM 16-bit (dipakai uji & alat bantu)."""
    x = np.clip(np.asarray(pcm, dtype=np.float32), -1.0, 1.0)
    data = (x * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data)


def resample_linear(pcm: np.ndarray, sr_in: int, sr_out: int = AUDIO_SAMPLE_RATE) -> np.ndarray:
    """Resampling interpolasi linear (cukup untuk ucapan; identik dengan resampleLinear di recorder.js)."""
    pcm = np.asarray(pcm, dtype=np.float32)
    if sr_in == sr_out or pcm.size == 0:
        return pcm.copy()
    n_out = int(round(pcm.size * sr_out / sr_in))
    if n_out <= 1:
        return np.zeros(max(n_out, 0), dtype=np.float32)
    pos = np.arange(n_out, dtype=np.float64) * (pcm.size - 1) / (n_out - 1)
    return np.interp(pos, np.arange(pcm.size), pcm).astype(np.float32)


def fix_length(pcm: np.ndarray, n: int = AUDIO_NUM_SAMPLES) -> np.ndarray:
    """Potong / pad nol di akhir hingga tepat n sampel."""
    out = np.zeros(n, dtype=np.float32)
    m = min(n, pcm.size)
    out[:m] = pcm[:m]
    return out


def _hz_to_mel(f: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + f / 700.0)


def _mel_to_hz(m: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def mel_filterbank(
    sr: int = AUDIO_SAMPLE_RATE, n_fft: int = AUDIO_N_FFT, n_mels: int = AUDIO_NUM_MELS,
    fmin: float = 20.0, fmax: Optional[float] = None,
) -> np.ndarray:
    """Filterbank mel segitiga (HTK) berbentuk [n_mels, n_fft//2 + 1]."""
    fmax = fmax or sr / 2.0
    n_bins = n_fft // 2 + 1
    mels = np.linspace(_hz_to_mel(np.array(fmin)), _hz_to_mel(np.array(fmax)), n_mels + 2)
    hz = _mel_to_hz(mels)
    bins = np.fft.rfftfreq(n_fft, d=1.0 / sr)
    fb = np.zeros((n_mels, n_bins), dtype=np.float32)
    for i in range(n_mels):
        lo, ce, hi = hz[i], hz[i + 1], hz[i + 2]
        up = (bins - lo) / max(ce - lo, 1e-9)
        down = (hi - bins) / max(hi - ce, 1e-9)
        fb[i] = np.maximum(0.0, np.minimum(up, down))
    return fb


_MEL_FB = mel_filterbank()
_WINDOW = np.hanning(AUDIO_N_FFT).astype(np.float32)


def log_mel(pcm16k: np.ndarray) -> np.ndarray:
    """
    Sinyal 16 kHz (panjang bebas) -> log-mel float32 [64, 248] berdurasi tetap 2,5 detik,
    distandarkan per-klip (mean 0, std 1) agar tidak bergantung volume mikrofon.
    """
    x = fix_length(np.asarray(pcm16k, dtype=np.float32))
    idx = np.arange(AUDIO_N_FFT)[None, :] + AUDIO_HOP * np.arange(AUDIO_NUM_FRAMES)[:, None]
    frames = x[idx] * _WINDOW[None, :]                       # [248, 400]
    power = np.abs(np.fft.rfft(frames, n=AUDIO_N_FFT, axis=1)) ** 2  # [248, 201]
    mel = power @ _MEL_FB.T                                  # [248, 64]
    feat = np.log(mel + 1e-6).T.astype(np.float32)           # [64, 248]
    mu, sd = float(feat.mean()), float(feat.std())
    return ((feat - mu) / (sd + 1e-5)).astype(np.float32)


def load_audio(
    audio_path: Optional[PathLike] = None, audio_bytes: Optional[bytes] = None,
    min_rms: float = 1e-4,
) -> Tuple[np.ndarray, bool]:
    """WAV -> log-mel [64, 248]. Dianggap tidak ada bila file hilang/rusak atau hening total."""
    empty = np.zeros((AUDIO_NUM_MELS, AUDIO_NUM_FRAMES), dtype=np.float32)
    try:
        if audio_bytes:
            pcm, sr = read_wav(audio_bytes)
        elif audio_path and Path(audio_path).exists():
            pcm, sr = read_wav(audio_path)
        else:
            return empty, False
    except Exception:
        return empty, False
    pcm = resample_linear(pcm, sr, AUDIO_SAMPLE_RATE)
    if pcm.size == 0 or float(np.sqrt(np.mean(pcm ** 2))) < min_rms:
        return empty, False
    return log_mel(pcm), True


# ---------------------------------------------------------------------------
# 4. TEKS (tokenisasi karakter)
# ---------------------------------------------------------------------------

PAD_ID, UNK_ID = 0, 1
TEXT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,?!-'"
CHAR_TO_ID = {c: i + 2 for i, c in enumerate(TEXT_ALPHABET)}
TEXT_VOCAB_SIZE: int = len(TEXT_ALPHABET) + 2


def encode_text(text: Optional[str], max_len: int = TEXT_MAX_LEN) -> Tuple[np.ndarray, bool]:
    """Kalimat -> id karakter int64 [64] (0 = padding). Kosong -> (nol, False)."""
    ids = np.zeros(max_len, dtype=np.int64)
    if not text or not str(text).strip():
        return ids, False
    norm = " ".join(str(text).lower().replace("_", " ").split())
    for i, ch in enumerate(norm[:max_len]):
        ids[i] = CHAR_TO_ID.get(ch, UNK_ID)
    return ids, True


def decode_text(ids: Sequence[int]) -> str:
    inv = {v: k for k, v in CHAR_TO_ID.items()}
    return "".join(inv.get(int(i), "?") for i in ids if int(i) != PAD_ID)
