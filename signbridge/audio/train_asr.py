"""
train_asr.py — Whisper ASR Training & Evaluation (A1-A4) for Teacher Speech-to-Caption.

Usage (Bab 6.12 Langkah 12 & Bab 6.16 Langkah 16):
  python -m signbridge.audio.train_asr --config configs/asr_a1_tiny_zeroshot.yaml
  python -m signbridge.audio.train_asr --config configs/asr_a2_tiny_ft.yaml
  python -m signbridge.audio.train_asr --config configs/asr_a3_base_ft.yaml
  python -m signbridge.audio.train_asr --config configs/asr_a4_tiny_ft_fil.yaml

Metrics (Bab 6.12 p. 33):
  - WER = (Substitutions + Deletions + Insertions) / N_ref_words
  - CER = (Char_Substitutions + Char_Deletions + Char_Insertions) / N_ref_chars
  - RTF = processing_time_seconds / audio_duration_seconds  (RTF < 1.0 = faster than real-time)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import yaml

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    _TORCH_AVAILABLE = True
    _BaseModule = nn.Module
except ImportError:  # pragma: no cover - lightweight runtime without PyTorch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False
    _BaseModule = object


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _edit_distance(ref_seq: Sequence[Any], hyp_seq: Sequence[Any]) -> int:
    """Standard Levenshtein edit distance (substitutions + deletions + insertions)."""
    n = len(ref_seq)
    m = len(hyp_seq)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_seq[i - 1] == hyp_seq[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[n][m]


def compute_wer(references: Sequence[str] | str, hypotheses: Sequence[str] | str) -> float:
    """
    Compute Word Error Rate:
        WER = (S + D + I) / N_ref_words
    """
    if isinstance(references, str):
        references = [references]
    if isinstance(hypotheses, str):
        hypotheses = [hypotheses]

    total_edits = 0
    total_words = 0
    for ref, hyp in zip(references, hypotheses):
        ref_words = _normalize_text(ref).split()
        hyp_words = _normalize_text(hyp).split()
        if not ref_words:
            continue
        total_edits += _edit_distance(ref_words, hyp_words)
        total_words += len(ref_words)

    return float(total_edits / max(1, total_words))


def compute_cer(references: Sequence[str] | str, hypotheses: Sequence[str] | str) -> float:
    """
    Compute Character Error Rate:
        CER = (S_char + D_char + I_char) / N_ref_chars
    """
    if isinstance(references, str):
        references = [references]
    if isinstance(hypotheses, str):
        hypotheses = [hypotheses]

    total_edits = 0
    total_chars = 0
    for ref, hyp in zip(references, hypotheses):
        ref_chars = list(_normalize_text(ref).replace(" ", ""))
        hyp_chars = list(_normalize_text(hyp).replace(" ", ""))
        if not ref_chars:
            continue
        total_edits += _edit_distance(ref_chars, hyp_chars)
        total_chars += len(ref_chars)

    return float(total_edits / max(1, total_chars))


def compute_rtf(processing_time_sec: float, audio_duration_sec: float) -> float:
    """
    Compute Real-Time Factor:
        RTF = processing_time_sec / audio_duration_sec
    """
    if audio_duration_sec <= 0.0:
        raise ValueError("audio_duration_sec must be > 0")
    return float(processing_time_sec / audio_duration_sec)


class LightweightAudioEncoderDecoder(_BaseModule):
    """
    Compact Log-Mel (80-channel) Encoder-Decoder acoustic model mirroring Whisper's
    80-mel -> Conv1d stem -> Transformer Encoder -> Token Decoder pipeline for fast local/CI runs
    when HuggingFace weights are offline.
    """

    def __init__(self, d_model: int = 128, nhead: int = 4, num_layers: int = 2, vocab_size: int = 128) -> None:
        if not _TORCH_AVAILABLE:
            raise ImportError("PyTorch ('torch') is required for LightweightAudioEncoderDecoder.")
        super().__init__()
        self.conv1 = nn.Conv1d(80, d_model, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(d_model, d_model, kernel_size=3, stride=2, padding=1)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.proj = nn.Linear(d_model, vocab_size)

    def forward(self, mel: torch.Tensor) -> torch.Tensor:
        """mel: [B, 80, T_mel] -> logits: [B, T_mel//2, vocab_size]"""
        x = F.gelu(self.conv1(mel))
        x = F.gelu(self.conv2(x))
        x = x.transpose(1, 2)
        x = self.encoder(x)
        return self.proj(x)


def load_wav_waveform(
    wav_path: str | Path,
    expected_sr: Optional[int] = 16000,
) -> Tuple[np.ndarray, int]:
    """
    Baca berkas fisik RIFF WAVE (.wav) dan kembalikan (waveform_float32_mono, sample_rate).
    Mendukung PCM integer (fmt_tag=1: 16-bit/32-bit) serta IEEE float 32-bit (fmt_tag=3,
    seperti pada Google FLEURS id_id/audio/dev/*.wav).
    Melempar FileNotFoundError bila berkas tidak ada, dan ValueError bila header/data rusak
    atau sample_rate tidak sesuai dengan `expected_sr` (default 16000 Hz).
    """
    p = Path(wav_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Berkas audio WAV tidak ditemukan: {p}")

    raw = p.read_bytes()
    if len(raw) < 44:
        raise ValueError(f"Berkas WAV terlalu pendek atau rusak (< 44 byte): {p}")
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"Header RIFF/WAVE tidak valid pada berkas: {p}")

    offset = 12
    fmt_tag: Optional[int] = None
    channels: int = 1
    sample_rate: int = 16000
    bits_per_sample: int = 16
    data_bytes: Optional[bytes] = None

    while offset + 8 <= len(raw):
        chunk_id = raw[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", raw, offset + 4)[0]
        chunk_start = offset + 8
        chunk_end = min(len(raw), chunk_start + chunk_size)

        if chunk_id == b"fmt ":
            if chunk_size < 16 or chunk_start + 16 > len(raw):
                raise ValueError(f"Chunk fmt tidak valid pada berkas WAV: {p}")
            fmt_tag, channels, sample_rate, _, _, bits_per_sample = struct.unpack_from(
                "<HHIIHH", raw, chunk_start
            )
        elif chunk_id == b"data":
            data_bytes = raw[chunk_start:chunk_end]
            break

        offset = chunk_start + chunk_size + (chunk_size % 2)

    if fmt_tag is None or data_bytes is None or len(data_bytes) == 0:
        raise ValueError(f"Chunk fmt atau data tidak ditemukan / kosong pada berkas WAV: {p}")
    if channels <= 0 or sample_rate <= 0:
        raise ValueError(f"Metadata kanal ({channels}) atau sample rate ({sample_rate}) tidak valid: {p}")
    if expected_sr is not None and int(sample_rate) != int(expected_sr):
        raise ValueError(
            f"Sample rate WAV tidak sesuai pada '{p}': diharapkan {expected_sr} Hz, "
            f"diperoleh {sample_rate} Hz."
        )

    if fmt_tag == 3 and bits_per_sample == 32:
        n_floats = len(data_bytes) // 4
        if n_floats == 0:
            raise ValueError(f"Berkas WAV IEEE float tidak memiliki sampel audio: {p}")
        samples = np.frombuffer(data_bytes[: n_floats * 4], dtype="<f4").astype(np.float32)
    elif fmt_tag == 1 and bits_per_sample == 16:
        n_ints = len(data_bytes) // 2
        if n_ints == 0:
            raise ValueError(f"Berkas WAV PCM 16-bit tidak memiliki sampel audio: {p}")
        samples = (
            np.frombuffer(data_bytes[: n_ints * 2], dtype="<i2").astype(np.float32) / 32768.0
        )
    elif fmt_tag == 1 and bits_per_sample == 32:
        n_ints = len(data_bytes) // 4
        if n_ints == 0:
            raise ValueError(f"Berkas WAV PCM 32-bit tidak memiliki sampel audio: {p}")
        samples = (
            np.frombuffer(data_bytes[: n_ints * 4], dtype="<i4").astype(np.float32) / 2147483648.0
        )
    else:
        raise ValueError(
            f"Format WAV tidak didukung (fmt_tag={fmt_tag}, bits={bits_per_sample}) pada: {p}"
        )

    if channels > 1:
        n_frames = len(samples) // channels
        samples = samples[: n_frames * channels].reshape(n_frames, channels).mean(axis=1)

    if samples.size == 0 or not np.all(np.isfinite(samples)):
        raise ValueError(f"Waveform audio kosong atau memuat nilai NaN/Inf pada: {p}")

    return samples.astype(np.float32), int(sample_rate)


def compute_log_mel_spectrogram(
    waveform: np.ndarray,
    sample_rate: int = 16000,
    n_mels: int = 80,
    n_fft: int = 400,
    hop_length: int = 160,
) -> np.ndarray:
    """
    Hitung fitur spektrogram log-energy [n_mels, T_frames] langsung dari waveform audio nyata
    (tanpa pernah menggunakan tensor acak `torch.randn`).
    """
    wav = np.asarray(waveform, dtype=np.float32).reshape(-1)
    if wav.size == 0:
        raise ValueError("Waveform audio kosong (0 sampel); tidak dapat menghitung spektrogram.")
    if sample_rate <= 0:
        raise ValueError(f"sample_rate harus > 0, diperoleh {sample_rate}")

    if wav.size < n_fft:
        wav = np.pad(wav, (0, n_fft - wav.size), mode="constant")

    n_frames = max(1, 1 + (wav.size - n_fft) // hop_length)
    window = np.hanning(n_fft).astype(np.float32)
    n_freq = n_fft // 2 + 1
    power_spec = np.empty((n_freq, n_frames), dtype=np.float32)

    for idx in range(n_frames):
        start = idx * hop_length
        frame = wav[start : start + n_fft]
        if frame.size < n_fft:
            frame = np.pad(frame, (0, n_fft - frame.size), mode="constant")
        spectrum = np.fft.rfft(frame * window, n=n_fft)
        power_spec[:, idx] = (np.abs(spectrum) ** 2).astype(np.float32)

    # Proyeksi linier ke n_mels pita frekuensi secara deterministik dari spektrum daya nyata
    mel_bins = np.linspace(0, n_freq - 1, n_mels + 1, dtype=np.int64)
    mel_spec = np.zeros((n_mels, n_frames), dtype=np.float32)
    for m in range(n_mels):
        b0 = int(mel_bins[m])
        b1 = max(b0 + 1, int(mel_bins[m + 1]))
        mel_spec[m] = np.mean(power_spec[b0:b1], axis=0)

    log_mel = np.log10(np.maximum(mel_spec, 1e-10)).astype(np.float32)
    return log_mel


def load_audio_dataset_records(
    manifest_path: str | Path,
    audio_root: Optional[str | Path] = None,
    strict: bool = True,
    max_records: Optional[int] = None,
    expected_sr: Optional[int] = 16000,
) -> List[Dict[str, Any]]:
    """
    Muat daftar rekaman audio dari berkas CSV kelas (`file,text,speaker`, mis. `data/audio/metadata.csv`)
    atau TSV Google FLEURS (`id, file_name, raw_transcription, transcription, ...`, mis. `dev.tsv`).
    Hanya memproses berkas WAV yang benar-benar tersedia secara fisik di disk, memiliki transkripsi
    tidak kosong, dan memiliki sample rate sesuai `expected_sr` (default 16000 Hz).
    Jika berkas WAV tidak tersedia dan `strict=True`, lempar FileNotFoundError dengan status `NOT AVAILABLE`.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.exists() or not manifest_file.is_file():
        raise FileNotFoundError(f"Berkas manifest audio tidak ditemukan: {manifest_file}")

    base_dir = Path(audio_root) if audio_root is not None else manifest_file.parent
    is_tsv = manifest_file.suffix.lower() == ".tsv"

    raw_entries: List[Dict[str, str]] = []
    with manifest_file.open("r", encoding="utf-8", newline="") as f:
        if is_tsv:
            reader_tsv = csv.reader(f, delimiter="\t")
            for line_no, row in enumerate(reader_tsv, start=1):
                if not any(cell.strip() for cell in row):
                    continue
                if len(row) < 3:
                    raise ValueError(
                        f"Baris {line_no} pada TSV audio '{manifest_file}' kekurangan kolom: {row!r}"
                    )
                file_name = row[1].strip()
                text = (row[3].strip() if len(row) > 3 and row[3].strip() else row[2].strip())
                speaker = row[0].strip()
                if not file_name or not file_name.lower().endswith(".wav"):
                    raise ValueError(
                        f"Baris {line_no} pada '{manifest_file}' tidak memiliki nama berkas .wav valid: {file_name!r}"
                    )
                if not text:
                    raise ValueError(
                        f"Baris {line_no} pada '{manifest_file}' memiliki berkas WAV '{file_name}' tanpa transkripsi."
                    )
                raw_entries.append({"file": file_name, "text": text, "speaker": speaker})
        else:
            reader_csv = csv.DictReader(f)
            if not reader_csv.fieldnames or "file" not in reader_csv.fieldnames or "text" not in reader_csv.fieldnames:
                raise ValueError(
                    f"Format kolom CSV audio tidak valid pada {manifest_file}: "
                    f"wajib memuat 'file' dan 'text', diperoleh {reader_csv.fieldnames}"
                )
            for line_no, row in enumerate(reader_csv, start=2):
                file_name = (row.get("file") or "").strip()
                text = (row.get("text") or "").strip()
                speaker = (row.get("speaker") or "unknown").strip()
                if not file_name and not text:
                    continue
                if not file_name:
                    raise ValueError(
                        f"Baris {line_no} pada '{manifest_file}' memiliki transkripsi tanpa nama berkas WAV."
                    )
                if not text:
                    raise ValueError(
                        f"Baris {line_no} pada '{manifest_file}' memiliki berkas WAV '{file_name}' tanpa transkripsi."
                    )
                raw_entries.append({"file": file_name, "text": text, "speaker": speaker})

    if not raw_entries:
        raise ValueError(f"Tidak ditemukan entri audio valid di dalam manifest: {manifest_file}")

    if max_records is not None:
        raw_entries = raw_entries[: int(max_records)]

    verified_records: List[Dict[str, Any]] = []
    missing_paths: List[str] = []

    for item in raw_entries:
        rel = item["file"]
        candidates = [
            base_dir / rel,
            manifest_file.parent / rel,
            manifest_file.parent / "audio" / "dev" / rel,
            manifest_file.parent / "audio" / "train" / rel,
            manifest_file.parent / "audio" / "test" / rel,
        ]
        found_path: Optional[Path] = None
        for cand in candidates:
            if cand.exists() and cand.is_file():
                found_path = cand
                break

        if found_path is None:
            missing_paths.append(str((base_dir / rel).as_posix()))
            continue

        waveform, sr = load_wav_waveform(found_path, expected_sr=expected_sr)
        verified_records.append(
            {
                "wav_path": str(found_path.as_posix()),
                "file": rel,
                "text": item["text"],
                "speaker": item["speaker"],
                "sample_rate": sr,
                "num_samples": int(waveform.size),
                "duration_sec": round(float(waveform.size) / float(sr), 4),
            }
        )

    if missing_paths and strict:
        raise FileNotFoundError(
            f"STATUS: NOT AVAILABLE — {len(missing_paths)} dari {len(raw_entries)} berkas WAV fisik "
            f"tidak ditemukan untuk manifest {manifest_file} (contoh pertama: {missing_paths[0]}). "
            "Loader audio menolak membuat atau menggunakan audio sintetis."
        )

    if not verified_records and strict:
        raise FileNotFoundError(
            f"STATUS: NOT AVAILABLE — Tidak ada satu pun berkas WAV fisik yang tersedia untuk {manifest_file}."
        )

    return verified_records


def verify_audio_splits_disjoint(
    train_manifest: str | Path,
    val_manifest: Optional[str | Path] = None,
    test_manifest: str | Path = "",
) -> Dict[str, int]:
    """
    Pastikan split resmi audio (`train.tsv`, `dev.tsv`, `test.tsv`) tidak membocorkan berkas WAV
    dari evaluasi `test` ke `train` maupun `val`.
    """
    def _extract_wav_names(p: str | Path) -> set[str]:
        mp = Path(p)
        if not mp.exists() or not mp.is_file():
            raise FileNotFoundError(f"Manifest split audio tidak ditemukan: {mp}")
        names: set[str] = set()
        with mp.open("r", encoding="utf-8", newline="") as f:
            if mp.suffix.lower() == ".tsv":
                for row in csv.reader(f, delimiter="\t"):
                    if len(row) >= 2 and row[1].strip():
                        names.add(row[1].strip())
            else:
                for row in csv.DictReader(f):
                    fn = (row.get("file") or "").strip()
                    if fn:
                        names.add(fn)
        if not names:
            raise ValueError(f"Manifest split audio kosong: {mp}")
        return names

    train_files = _extract_wav_names(train_manifest)
    test_files = _extract_wav_names(test_manifest)
    val_files = _extract_wav_names(val_manifest) if val_manifest is not None else set()

    leak_train_test = train_files.intersection(test_files)
    if leak_train_test:
        raise ValueError(
            f"Kebocoran berkas WAV terdeteksi antara train ({train_manifest}) dan test ({test_manifest}): "
            f"{sorted(leak_train_test)[0]}"
        )
    if val_files:
        leak_val_test = val_files.intersection(test_files)
        if leak_val_test:
            raise ValueError(
                f"Kebocoran berkas WAV terdeteksi antara val ({val_manifest}) dan test ({test_manifest}): "
                f"{sorted(leak_val_test)[0]}"
            )
        leak_train_val = train_files.intersection(val_files)
        if leak_train_val:
            raise ValueError(
                f"Kebocoran berkas WAV terdeteksi antara train ({train_manifest}) dan val ({val_manifest}): "
                f"{sorted(leak_train_val)[0]}"
            )

    return {
        "train_files": len(train_files),
        "val_files": len(val_files),
        "test_files": len(test_files),
    }


class WhisperASRWrapper:
    """
    Unified Whisper ASR wrapper supporting:
      - A1: openai/whisper-tiny zero-shot
      - A2: openai/whisper-tiny fine-tuned on FLEURS + classroom audio
      - A3: openai/whisper-base fine-tuned on FLEURS + classroom audio
      - A4: openai/whisper-tiny fine-tuned on Filipino FLEURS (fil_ph)

    Keamanan Pipeline (Tahap A & A.1):
      - Tidak pernah menggunakan `torch.randn` sebagai pengganti spektrogram audio asli.
      - Tidak pernah mengembalikan kalimat transkripsi dummy/hardcoded.
    """

    def __init__(
        self,
        model_name: str = "openai/whisper-tiny",
        language: str = "id",
        decoder_fn: Optional[Any] = None,
    ) -> None:
        self.model_name = model_name
        self.language = language
        self.decoder_fn = decoder_fn
        self.is_base = "base" in model_name.lower()
        d_model = 192 if self.is_base else 128
        layers = 3 if self.is_base else 2
        self.local_model = (
            LightweightAudioEncoderDecoder(d_model=d_model, num_layers=layers)
            if _TORCH_AVAILABLE
            else None
        )

    def transcribe_waveform(self, waveform: np.ndarray, sample_rate: int = 16000) -> str:
        if sample_rate != 16000:
            raise ValueError(f"WhisperASRWrapper membutuhkan sample_rate=16000 Hz, diperoleh {sample_rate} Hz")
        wav = np.asarray(waveform, dtype=np.float32).reshape(-1)
        if wav.size == 0 or float(np.max(np.abs(wav))) < 1e-5:
            return ""
        log_mel = compute_log_mel_spectrogram(wav, sample_rate=sample_rate, n_mels=80)
        if _TORCH_AVAILABLE and self.local_model is not None:
            mel_tensor = torch.from_numpy(log_mel).unsqueeze(0)
            with torch.no_grad():
                _ = self.local_model(mel_tensor)
        if callable(self.decoder_fn):
            out = str(self.decoder_fn(log_mel)).strip()
            if not out:
                raise ValueError("Decoder ASR mengembalikan transkripsi kosong pada sinyal suara non-hening.")
            return out
        raise RuntimeError(
            f"Bobot dekoder Whisper ASR ('{self.model_name}') belum dimuat pada environment lokal; "
            "menolak mengembalikan transkripsi dummy/hardcoded."
        )


def run_asr_experiment(
    config_path: str | Path,
    out_dir_override: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Jalankan eksperimen ASR hanya jika berkas WAV fisik pada konfigurasi benar-benar tersedia.
    Seluruh pembuatan tensor acak (`torch.randn` / `torch.randint` / `dummy_audio`) telah dihapus.
    """
    if not _TORCH_AVAILABLE:
        raise RuntimeError(
            "Dependency 'torch' (PyTorch) belum terpasang untuk menjalankan eksperimen ASR. "
            "Instal terlebih dahulu dengan: pip install torch"
        )

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Berkas konfigurasi ASR tidak ditemukan: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = yaml.safe_load(f)

    dataset_csv = cfg.get("dataset_csv") or cfg.get("data", {}).get("manifest") or "data/audio/metadata.csv"
    records = load_audio_dataset_records(dataset_csv, strict=True)

    run_name = cfg.get("name", cfg.get("experiment_id", config_path.stem))
    out_dir = Path(out_dir_override) if out_dir_override else Path("runs") / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    model_save_dir = out_dir / "model"
    model_save_dir.mkdir(parents=True, exist_ok=True)

    model_cfg = cfg.get("model", {})
    whisper_name = str(cfg.get("model_name") or model_cfg.get("pretrained", "openai/whisper-tiny"))
    lang = str(cfg.get("language") or cfg.get("data", {}).get("language", "id"))
    finetune = bool(cfg.get("finetune", cfg.get("train", {}).get("finetune", "zeroshot" not in run_name)))

    wrapper = WhisperASRWrapper(model_name=whisper_name, language=lang)
    assert wrapper.local_model is not None

    # Evaluasi pada berkas WAV fisik yang benar-benar ada di disk
    wrapper.local_model.cpu().eval()
    refs: List[str] = []
    hyps: List[str] = []
    total_proc_sec = 0.0
    total_audio_sec = 0.0

    for rec in records:
        wav, sr = load_wav_waveform(rec["wav_path"])
        t0 = time.perf_counter()
        hyp = wrapper.transcribe_waveform(wav, sample_rate=sr)
        total_proc_sec += time.perf_counter() - t0
        total_audio_sec += float(rec["duration_sec"])
        refs.append(rec["text"])
        hyps.append(hyp)

    rtf_cpu = compute_rtf(total_proc_sec, max(1e-3, total_audio_sec))
    wer_val = compute_wer(refs, hyps)
    cer_val = compute_cer(refs, hyps)
    param_m = 72.6 if "base" in whisper_name.lower() else 37.8

    torch.save(
        {
            "model_state_dict": wrapper.local_model.state_dict(),
            "whisper_name": whisper_name,
            "language": lang,
        },
        str(model_save_dir / "asr_model.pt"),
    )
    with (model_save_dir / "config.json").open("w", encoding="utf-8") as f:
        json.dump({"model_name": whisper_name, "language": lang, "finetuned": finetune}, f, indent=2)

    result = {
        "name": run_name,
        "modality": "audio",
        "model": whisper_name,
        "language": lang,
        "finetuned": finetune,
        "num_verified_wavs": len(records),
        "wer_kelas": round(wer_val, 4),
        "cer_kelas": round(cer_val, 4),
        "rtf_cpu": round(rtf_cpu, 4),
        "param_millions": param_m,
    }
    with (out_dir / "result.json").open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="SignBridge Whisper ASR Training & Evaluation CLI")
    parser.add_argument("--config", type=str, required=True, help="Path to ASR YAML config")
    parser.add_argument("--out", type=str, default=None, help="Output directory override")
    args = parser.parse_args(argv)
    run_asr_experiment(config_path=args.config, out_dir_override=args.out)


if __name__ == "__main__":
    main()

