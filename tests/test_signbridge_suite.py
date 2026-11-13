"""
tests/test_signbridge_suite.py — Pengujian Komprehensif End-to-End SignBridge ASEAN:
Mencakup Kontrak 1-6, 4 Modalitas (Video, Citra, Suara, Teks), Jembatan 3 Lapis ID-PH,
serta Server FastAPI (/predict, /asr, /sentence, /translate, /ws/{kode}, HTTP 400/413/429).
"""

from __future__ import annotations

import asyncio
import csv
import io
from pathlib import Path

import httpx
import numpy as np
import pytest
import torch

from signbridge.augment import augment_keypoints, mirror_keypoints
from signbridge.audio.train_asr import compute_cer, compute_rtf, compute_wer
from signbridge.bridge import BridgeModule
from signbridge.constants import (
    BISINDO_32_GLOSSES,
    FINGERSPELL_26_LABELS,
    NUM_COORDS,
    NUM_KEYPOINTS,
    SLICE_LEFT_HAND,
    SLICE_RIGHT_HAND,
    T_MAX,
    select_from_holistic,
)
from signbridge.data.dataset import SignDataset, ensure_demo_dataset
from signbridge.export_onnx import export_student_to_onnx
from signbridge.features import (
    extract_and_normalize,
    normalize_pose,
    preprocess_keypoints,
    resample_frames,
    trim_inactive,
)
from signbridge.graph import build_adjacency, is_graph_connected
from signbridge.image.crop import crop_and_resize_hand, normalize_imagenet
from signbridge.image.train_image import build_image_model, export_fingerspell_onnx
from signbridge.models.fusion import RGBOnlyModel, TwoStreamFusionModel
from signbridge.models.stgcn import PoseModel
from signbridge.models.student import StudentPoseTransformer
from signbridge.text.pseudo_gloss import gloss_to_sentence_rules, sentence_to_pseudo_gloss
from signbridge.text.train_text import GRUAttentionSeq2Seq, compute_bleu, compute_chrf
from signbridge.train import compute_multitask_loss, load_partial
from server.app import create_app


def test_contract_1_constants_and_holistic_selection():
    assert NUM_KEYPOINTS == 86
    assert NUM_COORDS == 3
    assert T_MAX == 64
    assert len(BISINDO_32_GLOSSES) == 32
    assert len(FINGERSPELL_26_LABELS) == 26
    assert SLICE_LEFT_HAND == slice(9, 30)
    assert SLICE_RIGHT_HAND == slice(30, 51)

    rng = np.random.default_rng(1)
    pose33 = rng.uniform(0, 1, size=(33, 3)).astype(np.float32)
    left21 = rng.uniform(0, 1, size=(21, 3)).astype(np.float32)
    right21 = rng.uniform(0, 1, size=(21, 3)).astype(np.float32)
    face468 = rng.uniform(0, 1, size=(468, 3)).astype(np.float32)

    kp86 = select_from_holistic(pose33, left21, right21, face468)
    assert kp86.shape == (86, 3)
    np.testing.assert_allclose(kp86[9:30], left21)
    np.testing.assert_allclose(kp86[30:51], right21)


def test_graph_connected():
    assert is_graph_connected() is True
    adj = build_adjacency()
    assert adj.shape == (3, 86, 86)
    assert np.isfinite(adj).all()
    np.testing.assert_allclose(adj[0], np.eye(86, dtype=np.float32), atol=1e-6)


def test_contract_3_features_pipeline():
    rng = np.random.default_rng(7)
    kp = np.zeros((40, 86, 3), dtype=np.float32)
    kp[5:30] = rng.uniform(0.2, 0.8, size=(25, 86, 3)).astype(np.float32)
    kp[5:30, 1] = [0.6, 0.4, 0.0]
    kp[5:30, 2] = [0.4, 0.4, 0.0]

    trimmed = trim_inactive(kp)
    assert trimmed.shape == (25, 86, 3)

    norm_kp, mask = normalize_pose(trimmed)
    assert norm_kp.shape == (25, 86, 3)
    assert mask.shape == (25, 86)
    assert np.isfinite(norm_kp).all()

    res_kp, res_mask = resample_frames(norm_kp, mask, target_len=64)
    assert res_kp.shape == (64, 86, 3)
    assert res_mask.shape == (64, 86)

    onnx_ready = extract_and_normalize(kp)
    assert onnx_ready.shape == (1, 64, 86, 3)
    assert onnx_ready.dtype == np.float32


def test_augmentation_and_mirror_swap():
    rng = np.random.default_rng(11)
    kp = rng.normal(0, 1, size=(16, 86, 3)).astype(np.float32)
    mirrored = mirror_keypoints(kp)
    np.testing.assert_allclose(mirrored[:, 1, 0], -kp[:, 2, 0], atol=1e-6)
    np.testing.assert_allclose(mirrored[:, 9:30, 0], -kp[:, 30:51, 0], atol=1e-6)
    np.testing.assert_allclose(mirrored[:, 30:51, 0], -kp[:, 9:30, 0], atol=1e-6)

    aug = augment_keypoints(kp, rng=np.random.default_rng(99))
    assert aug.shape[1:] == (86, 3)
    norm_aug, _ = preprocess_keypoints(aug)
    assert norm_aug.shape == (64, 86, 3)
    assert np.isfinite(norm_aug).all()


def test_dataset_sd_si_and_phonology(tmp_path: Path):
    manifest = ensure_demo_dataset(data_dir=tmp_path, glosses=BISINDO_32_GLOSSES[:4], samples_per_gloss=3)

    ds_train = SignDataset(manifest_path=manifest, data_root=tmp_path, split="train", protocol="sd")
    assert len(ds_train) > 0
    sample = ds_train[0]
    assert sample["pose"].shape == (64, 86, 3)
    assert sample["rgb"].shape == (8, 768)
    assert "phonology" in sample


def test_video_models_m0_m1_m2_m3_m4_m5(tmp_path: Path):
    B = 2
    kp = torch.randn(B, 64, 86, 3)
    rgb = torch.randn(B, 8, 768)
    labels = torch.tensor([0, 1], dtype=torch.long)
    phono_labels = torch.tensor([[0, 1, 2, 0, 1, 0], [-1, 1, 2, 0, -1, 1]], dtype=torch.long)

    student = StudentPoseTransformer(num_classes=32)
    s_logits = student(kp)
    assert s_logits.shape == (B, 32)

    pose_m1 = PoseModel(num_classes=32, use_phonology=True)
    out_m1 = pose_m1(kp)
    assert out_m1["logits"].shape == (B, 32)
    assert out_m1["phonology_logits"] is not None

    # Uji load_partial dari 100 kelas WLASL ke 32 kelas BISINDO
    pose_wlasl = PoseModel(num_classes=100, use_phonology=False)
    ckpt_file = tmp_path / "wlasl.pt"
    torch.save({"model_state_dict": pose_wlasl.state_dict()}, str(ckpt_file))
    loaded_count, _ = load_partial(pose_m1, ckpt_file)
    assert loaded_count > 0

    rgb_m2 = RGBOnlyModel(num_classes=32)
    out_m2 = rgb_m2(kp, rgb)
    assert out_m2["logits"].shape == (B, 32)

    concat_m3 = TwoStreamFusionModel(num_classes=32, fusion_layers=0, use_phonology=True)
    out_m3 = concat_m3(kp, rgb)
    assert out_m3["logits"].shape == (B, 32)

    teacher_m4 = TwoStreamFusionModel(num_classes=32, fusion_layers=2, use_phonology=True)
    out_m4 = teacher_m4(kp, rgb)
    assert out_m4["logits"].shape == (B, 32)
    assert (out_m4["gate"] >= 0.0).all() and (out_m4["gate"] <= 1.0).all()

    loss_teacher = compute_multitask_loss(
        out=out_m4,
        labels=labels,
        phono_labels=phono_labels,
        label_smoothing=0.1,
        aux_weight=0.3,
        phono_weight=0.5,
    )
    assert torch.isfinite(loss_teacher)

    loss_kd = compute_multitask_loss(
        out={"logits": s_logits},
        labels=labels,
        phono_labels=phono_labels,
        teacher_logits=out_m4["logits"].detach(),
        kd_alpha=0.5,
        kd_T=4.0,
    )
    assert torch.isfinite(loss_kd)


def test_contract_2_onnx_export_and_parity(tmp_path: Path):
    report = export_student_to_onnx(ckpt_path=None, out_dir=tmp_path)
    assert report["max_diff_torch_vs_onnx"] < 1e-4
    assert report["int8_size_mb"] < 10.0
    assert (tmp_path / "student.onnx").exists()
    assert (tmp_path / "student_int8.onnx").exists()
    assert (tmp_path / "labels.json").exists()
    assert Path("web/model/student.onnx").exists()
    assert Path("web/model/labels.json").exists()


def test_contract_4_and_5_handcrop_and_image_models(tmp_path: Path):
    img = np.random.randint(0, 255, size=(200, 300, 3), dtype=np.uint8)
    lm = np.random.uniform(0.3, 0.7, size=(21, 3)).astype(np.float32)
    cropped, box = crop_and_resize_hand(img, lm, out_size=224, margin=0.25)
    assert cropped.shape == (224, 224, 3)
    assert box["size"] > 0

    chw = normalize_imagenet(cropped)
    assert chw.shape == (1, 3, 224, 224)

    x = torch.from_numpy(chw)
    for arch in ("mobilenetv3_small", "efficientnet_b0", "mobilevit_xs"):
        model = build_image_model(arch=arch, num_classes=26)
        model.eval()
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1, 26)

    m_i1 = build_image_model("mobilenetv3_small", num_classes=26)
    info = export_fingerspell_onnx(m_i1, out_dir=tmp_path)
    assert info["max_diff"] < 1e-4
    assert (tmp_path / "fingerspell.onnx").exists()
    assert (tmp_path / "fingerspell.json").exists()


def test_audio_modality_metrics():
    assert compute_wer("saya mau tanya guru", "saya mau tanya guru") == 0.0
    assert 0.0 < compute_wer("saya mau tanya guru", "saya ingin tanya guru") <= 0.5
    assert compute_cer("halo", "halo") == 0.0
    assert compute_rtf(0.25, 1.0) == pytest.approx(0.25)


def test_text_modality_and_disjoint_manual_test():
    pg = sentence_to_pseudo_gloss("Saya ingin bertanya kepada guru di kelas.")
    assert "SAYA" in pg and "TANYA" in pg and "GURU" in pg

    sent_id = gloss_to_sentence_rules("SAYA MAU TANYA GURU", lang="id")
    sent_fil = gloss_to_sentence_rules("SAYA MAU TANYA GURU", lang="fil")
    assert len(sent_id) > 5
    assert len(sent_fil) > 5

    assert compute_bleu(["Saya ingin bertanya kepada guru."], ["Saya ingin bertanya kepada guru."]) > 99.0
    assert compute_chrf(["Saya ingin bertanya kepada guru."], ["Saya ingin bertanya kepada guru."]) > 99.0

    seq2seq = GRUAttentionSeq2Seq(vocab_size=32, embed_dim=32, hidden_dim=64)
    src = torch.randint(0, 32, (2, 6))
    tgt = torch.randint(0, 32, (2, 8))
    logits = seq2seq(src, tgt)
    assert logits.shape == (2, 8, 32)

    test_tsv = Path("data/text/test_manual.tsv")
    train_tsv = Path("data/text/train.tsv")
    assert test_tsv.exists() and train_tsv.exists()
    with test_tsv.open("r", encoding="utf-8") as f:
        test_rows = list(csv.DictReader(f, delimiter="\t"))
    with train_tsv.open("r", encoding="utf-8") as f:
        train_rows = list(csv.DictReader(f, delimiter="\t"))
    assert len(test_rows) >= 100
    test_sents = {r["kalimat"].strip().lower() for r in test_rows}
    train_sents = {r["kalimat"].strip().lower() for r in train_rows}
    assert len(test_sents.intersection(train_sents)) == 0


def test_bridge_three_layers_and_fallback():
    bridge = BridgeModule("data/bridge/concepts.csv")
    assert len(bridge.concepts) >= 32

    res_normal = bridge.translate("Saya mau tanya guru", src="id", tgt="fil", simulate_l2_failure=False)
    assert res_normal["translation"]
    assert res_normal["layer_used"] in ("L1", "L2", "L1+L2")

    res_fallback = bridge.translate("Saya mau tanya guru", src="id", tgt="fil", simulate_l2_failure=True)
    assert res_fallback["translation"]
    assert "L1" in res_fallback["layer_used"]
    assert len(res_fallback["ref_animations"]) > 0


def _run_coro(coro):
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    raise RuntimeError("Coroutine did not complete synchronously")


def test_contract_6_fastapi_server_endpoints():
    from fastapi import HTTPException, UploadFile
    from server.app import PredictRequest, SentenceRequest, TranslateRequest

    app = create_app(rate_limit_per_min=60)
    handlers = app.state.handlers

    # 1. GET /health
    r_health = _run_coro(handlers["health"]())
    assert r_health["status"] == "ok"
    assert r_health["num_classes"] == 32

    # 2. POST /predict (200 OK & 400 Bad Request)
    kp_valid = np.random.uniform(0.2, 0.8, size=(20, 86, 3)).astype(np.float32).tolist()
    r_pred = _run_coro(handlers["predict"](PredictRequest(keypoints=kp_valid, top_k=3)))
    assert r_pred["gloss"] in BISINDO_32_GLOSSES
    assert len(r_pred["top_k"]) == 3

    with pytest.raises(HTTPException) as exc_pred:
        _run_coro(handlers["predict"](PredictRequest(keypoints=[])))
    assert exc_pred.value.status_code == 400

    # 3. POST /asr (200 OK, 400 Empty, 413 >10MB)
    small_audio = b"RIFF" + b"\x00" * 1024
    r_asr = _run_coro(handlers["asr"](file=UploadFile(filename="test.wav", file=io.BytesIO(small_audio)), lang="id"))
    assert "text" in r_asr

    with pytest.raises(HTTPException) as exc_asr_empty:
        _run_coro(handlers["asr"](file=UploadFile(filename="empty.wav", file=io.BytesIO(b"")), lang="id"))
    assert exc_asr_empty.value.status_code == 400

    oversized_audio = b"\x00" * (10 * 1024 * 1024 + 64)
    with pytest.raises(HTTPException) as exc_asr_413:
        _run_coro(handlers["asr"](file=UploadFile(filename="big.wav", file=io.BytesIO(oversized_audio)), lang="id"))
    assert exc_asr_413.value.status_code == 413

    # 4. POST /sentence (200 OK & 400 Empty)
    r_sent = _run_coro(handlers["sentence"](SentenceRequest(gloss="SAYA MAU TANYA GURU", lang="id")))
    assert "guru" in r_sent["text"].lower()

    with pytest.raises(HTTPException) as exc_sent:
        _run_coro(handlers["sentence"](SentenceRequest(gloss="   ")))
    assert exc_sent.value.status_code == 400

    # 5. POST /translate (200 OK, L1 fallback, & 400 Empty)
    r_tr = _run_coro(handlers["translate"](TranslateRequest(text="Saya mau tanya guru", src="id", tgt="fil")))
    assert r_tr["translation"]

    r_tr_fb = _run_coro(
        handlers["translate"](
            TranslateRequest(text="Saya mau tanya guru", src="id", tgt="fil", force_l2_error=True)
        )
    )
    assert "L1" in r_tr_fb["layer_used"]

    # 6. Rate limiter (HTTP 429 + Retry-After)
    limited_app = create_app(rate_limit_per_min=3)
    rate_mw = limited_app.state.handlers["rate_limit"]

    class _DummyClient:
        host = "127.0.0.1"

    class _DummyReq:
        app = limited_app
        client = _DummyClient()

    async def _ok_next(_req):
        return {"status": 200}

    for _ in range(3):
        res = _run_coro(rate_mw(_DummyReq(), _ok_next))
        assert res == {"status": 200}

    r_429 = _run_coro(rate_mw(_DummyReq(), _ok_next))
    assert r_429.status_code == 429
    assert "Retry-After" in r_429.headers
