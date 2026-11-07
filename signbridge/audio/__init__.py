"""Audio ASR package (Whisper A1-A4 & WER/CER/RTF evaluation)."""

from __future__ import annotations

from typing import Any

from signbridge.audio.train_asr import (
    compute_cer,
    compute_rtf,
    compute_wer,
)

__all__ = [
    "compute_wer",
    "compute_cer",
    "compute_rtf",
    "run_asr_experiment",
    "WhisperASRWrapper",
]


def __getattr__(name: str) -> Any:
    if name in ("run_asr_experiment", "WhisperASRWrapper"):
        from signbridge.audio import train_asr

        return getattr(train_asr, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

