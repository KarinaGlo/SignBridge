"""
Kontrak 7 — Bentuk tensor model fusion multimodal M6.

PERINGATAN: kontrak antarmuka antara data (Farrel), model (Jonnathan), dan web/server (Gloria).
Jangan mengubah urutan modalitas atau dimensi tensor tanpa diskusi tim; ONNX & server bergantung padanya.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Urutan modalitas TETAP (indeks dipakai oleh modality_mask & modality_weights)
MODALITIES: List[str] = ["video", "image", "audio", "text"]
NUM_MODALITIES: int = len(MODALITIES)
MODALITY_INDEX: Dict[str, int] = {m: i for i, m in enumerate(MODALITIES)}

# Video / pose (sama dengan Kontrak 1–3)
POSE_SHAPE: Tuple[int, int, int] = (64, 86, 3)

# Citra crop tangan (lebih kecil dari 224 agar ringan di CPU/browser)
IMAGE_SIDE: int = 112
IMAGE_SHAPE: Tuple[int, int, int] = (3, IMAGE_SIDE, IMAGE_SIDE)

# Audio: 16 kHz mono, jendela tetap 2,5 detik (= durasi klip perekam), log-mel 64 bin
AUDIO_SAMPLE_RATE: int = 16_000
AUDIO_CLIP_SECONDS: float = 2.5
AUDIO_NUM_SAMPLES: int = int(AUDIO_SAMPLE_RATE * AUDIO_CLIP_SECONDS)  # 40_000
AUDIO_N_FFT: int = 400        # 25 ms
AUDIO_HOP: int = 160          # 10 ms
AUDIO_NUM_MELS: int = 64
AUDIO_NUM_FRAMES: int = 1 + (AUDIO_NUM_SAMPLES - AUDIO_N_FFT) // AUDIO_HOP  # 248
AUDIO_SHAPE: Tuple[int, int] = (AUDIO_NUM_MELS, AUDIO_NUM_FRAMES)

# Teks: tokenisasi level karakter (tanpa vocabulary kata -> tidak ada kebocoran kata uji)
TEXT_MAX_LEN: int = 64
TEXT_SHAPE: Tuple[int] = (TEXT_MAX_LEN,)

# Kolom manifest multimodal
MANIFEST_COLUMNS: List[str] = [
    "clip_id",
    "signer",
    "category",
    "gloss",
    "label",
    "kp_path",
    "image_path",
    "audio_path",
    "text",
    "split",
]
