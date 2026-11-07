"""
models.py — Data model untuk SignBridge BISINDO.

Berisi VideoMetadata dataclass yang digunakan di seluruh data pipeline.

Requirements: 1.5, 15.2
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoMetadata:
    """
    Metadata untuk satu klip video dalam dataset.

    Field wajib
    -----------
    path : str
        Path relatif ke file video (relatif terhadap root dataset).
    gloss : str
        Label gloss (kata/konsep bahasa isyarat).
    signer_id : str
        Identifikasi unik signer (perekam video).
    split : str
        Partisi dataset — harus salah satu dari "train", "val", atau "test".

    Field opsional
    --------------
    duration_sec : float | None
        Durasi video dalam detik.
    resolution : str | None
        Resolusi dalam format "WxH" (contoh: "640x480").
    fps : float | None
        Frame rate video.
    """

    # Wajib
    path: str
    gloss: str
    signer_id: str
    split: str

    # Opsional
    duration_sec: Optional[float] = field(default=None)
    resolution: Optional[str] = field(default=None)
    fps: Optional[float] = field(default=None)

    # Nilai split yang valid
    VALID_SPLITS: frozenset[str] = field(
        default=frozenset({"train", "val", "test"}),
        init=False,
        repr=False,
        compare=False,
    )
