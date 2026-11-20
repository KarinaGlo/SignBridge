"""
server/multimodal_service.py — Inferensi M6 (fusion 4 modalitas) via onnxruntime untuk POST /predict_multimodal.

Preprocessing memakai signbridge.multimodal.features (sama persis dengan pelatihan).
Jika web/model/multimodal_fusion.onnx belum ada, layanan melaporkan `available=False`
dan endpoint mengembalikan HTTP 503 — tidak ada prediksi palsu.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel

from signbridge.constants import BISINDO_32_GLOSSES
from signbridge.multimodal.constants import MODALITIES
from signbridge.multimodal.features import encode_text, load_audio, load_image, pose_from_sequence

MAX_MEDIA_BYTES = 10 * 1024 * 1024  # 10 MB per berkas


class MultimodalPredictRequest(BaseModel):
    keypoints: Optional[List[Any]] = None   # [F, 86, 3] koordinat MediaPipe
    image_base64: Optional[str] = None      # JPG/PNG crop tangan
    audio_base64: Optional[str] = None      # WAV PCM 16-bit
    text: Optional[str] = None              # kalimat konteks / transkrip
    top_k: int = 3
    room_code: Optional[str] = None


def _b64(data: Optional[str], name: str) -> Optional[bytes]:
    if not data:
        return None
    if "," in data and data.strip().startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=False)
    except Exception as e:
        raise ValueError(f"{name}: base64 tidak valid ({e})") from e
    if len(raw) > MAX_MEDIA_BYTES:
        raise ValueError(f"{name}: ukuran {len(raw)} byte melebihi batas 10 MB")
    return raw


class MultimodalService:
    def __init__(self, onnx_path: Path):
        self.onnx_path = Path(onnx_path)
        self.session = None
        if self.onnx_path.exists():
            try:
                import onnxruntime as ort

                self.session = ort.InferenceSession(str(self.onnx_path), providers=["CPUExecutionProvider"])
            except Exception:
                self.session = None

    @property
    def available(self) -> bool:
        return self.session is not None

    def build_inputs(self, req: MultimodalPredictRequest) -> Dict[str, np.ndarray]:
        pose, has_pose = pose_from_sequence(req.keypoints) if req.keypoints else (np.zeros((64, 86, 3), np.float32), False)
        image, has_img = load_image(image_bytes=_b64(req.image_base64, "image_base64"))
        audio, has_audio = load_audio(audio_bytes=_b64(req.audio_base64, "audio_base64"))
        text, has_text = encode_text(req.text)
        mask = np.array([[has_pose, has_img, has_audio, has_text]], dtype=np.float32)
        return {
            "pose": pose[None].astype(np.float32),
            "image": image[None].astype(np.float32),
            "audio": audio[None].astype(np.float32),
            "text": text[None].astype(np.int64),
            "modality_mask": mask,
        }

    def predict(self, req: MultimodalPredictRequest) -> Dict[str, Any]:
        inputs = self.build_inputs(req)
        mask = inputs["modality_mask"][0]
        if mask.sum() == 0:
            raise ValueError("Tidak ada modalitas valid pada permintaan (keypoints/image/audio/text).")
        logits, weights = self.session.run(["logits", "modality_weights"], inputs)
        logits, weights = logits[0], weights[0]
        probs = np.exp(logits - logits.max())
        probs = probs / probs.sum()
        k = max(1, min(int(req.top_k), len(BISINDO_32_GLOSSES)))
        top = np.argsort(probs)[::-1][:k]
        return {
            "gloss": BISINDO_32_GLOSSES[int(top[0])],
            "confidence": round(float(probs[top[0]]), 4),
            "top_k": [{"gloss": BISINDO_32_GLOSSES[int(i)], "label": int(i), "confidence": round(float(probs[i]), 4)}
                      for i in top],
            "modalities_used": [m for m, on in zip(MODALITIES, mask) if on > 0],
            "modality_weights": {m: round(float(w), 4) for m, w in zip(MODALITIES, weights)},
            "model": "M6-MultimodalFusion",
        }
