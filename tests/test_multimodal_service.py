"""
tests/test_multimodal_service.py — Kontrak 7: layanan POST /predict_multimodal (NumPy, sesi ONNX tiruan).
"""

from __future__ import annotations

import base64

import numpy as np
import pytest

from signbridge.multimodal.features import write_wav


# ---------------------------------------------------------------------------
# Layanan server (tanpa PyTorch / onnxruntime)
# ---------------------------------------------------------------------------


class _FakeSession:
    def __init__(self):
        self.last = None

    def run(self, names, feeds):
        self.last = feeds
        logits = np.zeros((1, 32), np.float32)
        logits[0, 7] = 5.0
        w = feeds["modality_mask"] / feeds["modality_mask"].sum()
        return [logits, w.astype(np.float32)]


def _service():
    from server.multimodal_service import MultimodalService

    svc = MultimodalService.__new__(MultimodalService)
    svc.session = _FakeSession()
    return svc


def test_service_builds_inputs_with_correct_shapes_and_mask(tmp_path):
    from server.multimodal_service import MultimodalPredictRequest

    p = tmp_path / "a.wav"
    write_wav(p, 0.2 * np.sin(np.arange(40_000) * 0.05).astype(np.float32))
    audio_b64 = base64.b64encode(p.read_bytes()).decode()
    kp = np.random.default_rng(0).uniform(0.3, 0.7, (30, 86, 3)).tolist()
    req = MultimodalPredictRequest(keypoints=kp, audio_base64=audio_b64, text="saya makan")
    feeds = _service().build_inputs(req)
    assert feeds["pose"].shape == (1, 64, 86, 3)
    assert feeds["image"].shape == (1, 3, 112, 112)
    assert feeds["audio"].shape == (1, 64, 248)
    assert feeds["text"].shape == (1, 64) and feeds["text"].dtype == np.int64
    assert feeds["modality_mask"].tolist() == [[1.0, 0.0, 1.0, 1.0]]


def test_service_predict_reports_weights_and_used_modalities():
    from server.multimodal_service import MultimodalPredictRequest

    out = _service().predict(MultimodalPredictRequest(text="saya makan"))
    assert out["gloss"] == "MAKAN"
    assert out["modalities_used"] == ["text"]
    assert out["modality_weights"]["text"] == 1.0 and out["modality_weights"]["video"] == 0.0


def test_service_rejects_empty_request():
    from server.multimodal_service import MultimodalPredictRequest

    with pytest.raises(ValueError):
        _service().predict(MultimodalPredictRequest())
