"""Uji SignBridge-XMF: ingestion (label dari nama file), ops, log-mel di dalam graf, masking, ONNX."""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from signbridge.xmf import ingest
from signbridge.xmf.config import GLOSSES, SHAPES, encode_text, parse_alphabet_name, parse_wlb_name
from signbridge.xmf.model import LogMel, XMFOnnx, build_model
from signbridge.xmf.ops import (
    crop_square, fit_audio, median_box, normalize_hands_static, person_box_from_shoulders, uniform_indices,
)


def test_parse_names():
    k = parse_wlb_name("signer4_label0_sample10_f15.jpg")
    assert (k.signer, k.label, k.sample, k.frame, k.gloss) == (4, 0, 10, 15, "AIR")
    assert parse_wlb_name("signer1_label31_sample2.mp4").gloss == "MALAM"
    assert parse_wlb_name("signer1_label40_sample2.mp4") is None
    assert parse_alphabet_name("A_Polos Terang_Samsung_A55.jpg", "A") == ("A", "samsung_a55")


def test_ingest_ignores_wrong_citra_folder_names(tmp_path: Path):
    root = tmp_path / "drive"
    (root / "video").mkdir(parents=True)
    (root / "citra" / "apa_kabar").mkdir(parents=True)        # nama folder salah (label1 = BELAJAR)
    (root / "alfabet" / "B").mkdir(parents=True)
    for s in (1, 9):
        (root / "video" / f"signer4_label1_sample{s}.mp4").write_bytes(b"x")
    for f in range(16):
        (root / "citra" / "apa_kabar" / f"signer4_label1_sample1_f{f:02d}.jpg").write_bytes(b"x")
    (root / "alfabet" / "B" / "B_Putih_Samsung_M51.jpg").write_bytes(b"x")
    g = ingest.ingest_gloss(root, test_signer=4)
    rows = {r["sample_id"]: r for r in g["rows"]}
    assert rows["signer4_label1_sample1"]["gloss"] == "BELAJAR"
    assert rows["signer4_label1_sample1"]["image_source"] == "citra"
    assert rows["signer4_label1_sample9"]["image_source"] == "video_fallback"
    assert rows["signer4_label1_sample1"]["split_si"] == "test"
    assert g["report"]["citra_folder_name_mismatch"] == ["apa_kabar -> BELAJAR"]
    a = ingest.ingest_alphabet(root)
    assert a["rows"][0]["letter"] == "B" and a["rows"][0]["label"] == 1


def test_ops():
    assert uniform_indices(100, 4).tolist() == [12, 37, 62, 87]
    box = person_box_from_shoulders((0.6, 0.4), (0.4, 0.4), 200, 100)
    assert box == pytest.approx((100.0, 40 + 0.35 * 40, 3.6 * 40))
    img = np.full((100, 200, 3), 200, np.uint8)
    out = crop_square(img, median_box([box, None], 200, 100), 112)
    assert out.shape == (112, 112, 3) and out[0, 0].sum() == 0          # luar gambar = hitam
    a = np.zeros(8000, np.float32)
    a[3000:5000] = 0.5
    y = fit_audio(a, 40000)
    assert y.shape == (40000,) and abs(np.argmax(np.abs(y) > 0.1) - 19000) < 200
    kp = np.full((86, 3), np.nan, np.float32)
    kp[30:51] = np.random.rand(21, 3)
    n = normalize_hands_static(kp)
    assert np.allclose(n[30], 0) and np.allclose(n[9:30], 0)
    assert encode_text("Terima_Kasih")[:5] == encode_text("terima kasih")[:5]


def test_logmel_matches_numpy_reference():
    from signbridge.multimodal.features import log_mel

    rng = np.random.default_rng(0)
    x = (0.2 * np.sin(np.arange(40000) / 16000 * 2 * np.pi * 440) + rng.normal(0, .01, 40000)).astype(np.float32)
    ref = log_mel(x)
    got = LogMel()(torch.from_numpy(x)[None])[0].numpy()
    assert np.max(np.abs(ref - got)) < 2e-3


def _inputs(task, mask):
    s = SHAPES[task]
    g = torch.Generator().manual_seed(0)
    return (torch.randn(1, s.pose_frames, 86, 3, generator=g), torch.rand(1, s.image_frames, 3, 112, 112, generator=g) * 255,
            torch.randn(1, s.audio_samples, generator=g) * .1, torch.tensor([encode_text("selamat pagi")]),
            torch.tensor([mask], dtype=torch.float32))


@pytest.mark.parametrize("task", ["gloss", "alphabet"])
def test_missing_modality_has_no_effect(task):
    torch.manual_seed(0)
    m = build_model(task, len(GLOSSES), {"pretrained_image": False}).eval()
    x = list(_inputs(task, [1, 1, 0, 0]))
    with torch.no_grad():
        a = m(*x)["logits"]
        x[2] = torch.randn_like(x[2])                     # ganti audio & teks yang di-mask
        x[3] = torch.tensor([encode_text("hitam")])
        b = m(*x)["logits"]
        w = m(*x)["modality_weights"]
    assert torch.allclose(a, b, atol=1e-5)
    assert float(w[0, 2]) == 0 and float(w[0, 3]) == 0 and abs(float(w.sum()) - 1) < 1e-5


def test_onnx_parity_all_masks(tmp_path):
    ort = pytest.importorskip("onnxruntime")
    torch.manual_seed(0)
    m = build_model("gloss", 32, {"pretrained_image": False}).eval()
    w = XMFOnnx(m).eval()
    f = io.BytesIO()
    torch.onnx.export(w, _inputs("gloss", [1, 1, 1, 1]), f, dynamo=False, opset_version=17,
                      input_names=["pose", "frames", "audio", "text", "modality_mask"])
    s = ort.InferenceSession(f.getvalue())
    for mask in ([1, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 1, 1]):
        x = _inputs("gloss", mask)
        with torch.no_grad():
            ref = w(*x)
        got = s.run(None, {i.name: t.numpy() for i, t in zip(s.get_inputs(), x)})
        for r, g in zip(ref, got):
            assert np.max(np.abs(r.numpy() - g)) < 1e-3, mask


def test_fixture_for_js_parity_is_current():
    """tests/js/fixtures/xmf_fixture.json harus sinkron dengan fungsi Python (dibuat oleh skrip)."""
    fx = Path(__file__).parent / "js/fixtures/xmf_fixture.json"
    data = json.loads(fx.read_text())
    for case in data["text"]:
        assert encode_text(case["text"]) == case["ids"]
    for case in data["person_box"]:
        assert person_box_from_shoulders(case["l"], case["r"], case["w"], case["h"]) == pytest.approx(case["box"])
