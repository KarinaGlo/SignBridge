"""
tests/test_multimodal_model.py — Kontrak 7: model fusion M6 (butuh PyTorch; dilewati bila tidak terpasang).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Model PyTorch
# ---------------------------------------------------------------------------

torch = pytest.importorskip("torch")


def _batch(B=3, seed=0):
    g = torch.Generator().manual_seed(seed)
    return (
        torch.randn(B, 64, 86, 3, generator=g),
        torch.randn(B, 3, 112, 112, generator=g),
        torch.randn(B, 64, 248, generator=g),
        torch.randint(2, 40, (B, 64), generator=g),
    )


def _model(**kw):
    from signbridge.models.multimodal import SignBridgeMultimodalFusion

    torch.manual_seed(0)
    return SignBridgeMultimodalFusion(num_classes=32, **kw)


def test_forward_shapes_and_weights_sum_to_one():
    m = _model().eval()
    pose, img, aud, txt = _batch()
    mask = torch.tensor([[1, 1, 1, 1], [1, 0, 1, 0], [0, 0, 0, 1]], dtype=torch.float32)
    out = m(pose, img, aud, txt, mask)
    assert out["logits"].shape == (3, 32)
    w = out["modality_weights"]
    assert w.shape == (3, 4)
    assert torch.allclose(w.sum(1), torch.ones(3), atol=1e-5)
    assert torch.all(w[mask == 0] == 0)  # modalitas hilang mendapat bobot nol
    assert out["aux_logits"].shape == (3, 4, 32)


def test_masked_modality_does_not_affect_prediction():
    """Isi tensor modalitas yang di-mask tidak boleh mengubah keluaran (benar-benar diabaikan)."""
    m = _model().eval()
    pose, img, aud, txt = _batch(B=2)
    mask = torch.tensor([[1, 0, 1, 1], [1, 0, 1, 1]], dtype=torch.float32)
    a = m(pose, img, aud, txt, mask)["logits"]
    b = m(pose, img * 100 + 7, aud, txt, mask)["logits"]
    assert torch.allclose(a, b, atol=1e-5)


def test_all_modalities_contribute_when_present():
    m = _model().eval()
    pose, img, aud, txt = _batch(B=1)
    full = torch.ones(1, 4)
    base = m(pose, img, aud, txt, full)["logits"]
    for k, alt in enumerate([pose * 2, img * 2, aud * 2, torch.flip(txt, [1])]):
        args = [pose, img, aud, txt]
        args[k] = alt
        assert not torch.allclose(base, m(*args, full)["logits"], atol=1e-6), f"modalitas {k} tidak berpengaruh"


def test_modality_dropout_keeps_at_least_one():
    m = _model(modality_dropout=0.95).train()
    mask = torch.ones(64, 4)
    for _ in range(5):
        dropped = m.apply_modality_dropout(mask)
        assert torch.all(dropped.sum(1) >= 1)
        assert torch.all(dropped <= mask)


def test_loss_backward_and_one_step_learns():
    from signbridge.models.multimodal import multimodal_loss

    m = _model(modality_dropout=0.0).train()
    pose, img, aud, txt = _batch(B=8)
    mask = torch.ones(8, 4)
    y = torch.arange(8) % 32
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
    first = None
    for _ in range(15):
        out = m(pose, img, aud, txt, mask)
        loss = multimodal_loss(out, y)["loss"]
        opt.zero_grad()
        loss.backward()
        opt.step()
        first = first if first is not None else float(loss)
    assert float(loss) < first


def test_text_all_padding_row_is_finite():
    m = _model().eval()
    pose, img, aud, _ = _batch(B=2)
    txt = torch.zeros(2, 64, dtype=torch.long)
    out = m(pose, img, aud, txt, torch.tensor([[1, 1, 1, 0], [1, 0, 0, 0]], dtype=torch.float32))
    assert torch.isfinite(out["logits"]).all()


def test_onnx_export_and_parity(tmp_path):
    pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    from signbridge.export_onnx_multimodal import check_parity, export

    m = _model().eval()
    path = export(m, tmp_path / "mm.onnx")
    assert check_parity(m, path) < 1e-4
