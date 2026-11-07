"""
tests/test_database_integration.py — Pengujian Integrasi Database Operasional & Telemetri
(PostgreSQL / SQLAlchemy 2.0 + FastAPI Endpoints + Fallback Ketahanan).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Coroutine

import numpy as np
from fastapi import UploadFile

from server.app import (
    EvaluationCreateRequest,
    PredictRequest,
    RecordingCreateRequest,
    SentenceRequest,
    TranslateRequest,
    create_app,
)


def _run_sync(coro: Coroutine[Any, Any, Any]) -> Any:
    """Jalankan coroutine endpoint FastAPI secara sinkron tanpa socket loop Windows."""
    try:
        coro.send(None)
    except StopIteration as stop:
        return stop.value
    raise RuntimeError("Coroutine awaited an unexpected async I/O primitive")


def test_db_schema_seeding_and_status(tmp_path: Path):
    test_db_url = f"sqlite:///{(tmp_path / 'test_signbridge.db').as_posix()}"
    app = create_app(database_url=test_db_url, fallback_db_url=test_db_url)
    h = app.state.handlers

    health = _run_sync(h["health"]())
    assert health["status"] == "ok"
    assert health["model_loaded"] is True
    assert health["num_classes"] == 32
    assert health["concepts_loaded"] == 32
    assert health["db_connected"] is True

    st = _run_sync(h["db_status"]())
    assert st["db_connected"] is True
    # 32 BISINDO/FSL concepts + 26 A-Z letters = 58 concepts
    assert st["counts"]["sign_concepts"] == 58
    # M0-M5 (6) + I1-I3 (3) + A1-A3 (3) + B0,T1-T3 (4) + X1-X4 (4) = 20 models
    assert st["counts"]["model_versions"] == 20
    # Minimal 3 evaluasi terverifikasi (B0 test_manual.tsv, M5 ONNX, I1 ONNX)
    assert st["counts"]["evaluation_runs"] >= 3


def test_db_concepts_models_and_evaluations_endpoints(tmp_path: Path):
    test_db_url = f"sqlite:///{(tmp_path / 'test_endpoints.db').as_posix()}"
    app = create_app(database_url=test_db_url, fallback_db_url=test_db_url)
    h = app.state.handlers

    concepts = _run_sync(h["db_concepts"](category=None))
    assert concepts["db_connected"] is True
    assert concepts["count"] == 58

    sapaan = _run_sync(h["db_concepts"](category="Sapaan"))
    assert sapaan["count"] == 4

    abjad = _run_sync(h["db_concepts"](category="Abjad Ejaan Jari"))
    assert abjad["count"] == 26

    models = _run_sync(h["db_models"](modality=None))
    assert models["count"] == 20

    video_models = _run_sync(h["db_models"](modality="video"))
    assert video_models["count"] == 6

    evals = _run_sync(h["db_evaluations"](model_code="B0"))
    assert evals["count"] >= 1
    b0_eval = evals["items"][0]
    assert b0_eval["test_count"] == 105
    assert b0_eval["bleu"] is not None and b0_eval["chrf"] is not None

    # Tambah evaluasi baru (simulasi pencatatan evaluasi LOSO Gloria)
    created_ev = _run_sync(
        h["db_create_evaluation"](
            EvaluationCreateRequest(
                model_code="M5",
                dataset_name="SignBridge-Kelas LOSO Fold S03",
                evaluation_type="loso_signer_independent",
                protocol="loso_si",
                accuracy=0.875,
                macro_f1=0.862,
                latency_ms=8.4,
                test_count=320,
            )
        )
    )
    assert created_ev["status"] == "created"


def test_inference_logging_and_recordings_crud(tmp_path: Path):
    test_db_url = f"sqlite:///{(tmp_path / 'test_logging.db').as_posix()}"
    app = create_app(database_url=test_db_url, fallback_db_url=test_db_url)
    h = app.state.handlers

    # 1. Panggil /predict, /asr, /sentence, /translate
    kp = np.random.uniform(0.2, 0.8, size=(16, 86, 3)).astype(np.float32).tolist()
    _run_sync(h["predict"](PredictRequest(keypoints=kp, top_k=3, room_code="4821")))
    _run_sync(h["asr"](file=UploadFile(filename="sample.wav", file=io.BytesIO(b"RIFF0000WAVEfmt ")), lang="id"))
    _run_sync(h["sentence"](SentenceRequest(gloss=["SAYA", "MAU", "TANYA", "GURU"], lang="id", room_code="4821")))
    _run_sync(h["translate"](TranslateRequest(text="Saya mau tanya guru", src="id", tgt="fil", room_code="4821")))

    logs = _run_sync(h["db_logs"](limit=50, endpoint=None, modality=None))
    assert logs["db_connected"] is True
    assert logs["count"] == 4
    endpoints_logged = {item["endpoint"] for item in logs["items"]}
    assert endpoints_logged == {"/predict", "/asr", "/sentence", "/translate"}

    # 2. Tambah metadata rekaman SignBridge-Kelas
    rec_res = _run_sync(
        h["db_create_recording"](
            RecordingCreateRequest(
                recording_code="SBK_S01_HALO_001",
                signer_id="S01",
                gloss="HALO",
                repetition=1,
                duration=2.6,
                file_path="data/raw/selfrec/SBK_S01_HALO_001.webm",
                keypoint_path="data/keypoints/selfrec/SBK_S01_HALO_001.npz",
            )
        )
    )
    assert rec_res["status"] == "created"

    recs = _run_sync(h["db_recordings"](signer_id="S01"))
    assert recs["count"] == 1
    assert recs["items"][0]["gloss"] == "HALO"


def test_database_failure_graceful_degradation(tmp_path: Path):
    """
    Pastikan ketika database mati/gagal total, seluruh endpoint inferensi utama
    (/predict, /asr, /sentence, /translate, /health) TETAP berjalan normal tanpa crash.
    """
    test_db_url = f"sqlite:///{(tmp_path / 'test_fallback.db').as_posix()}"
    app = create_app(database_url=test_db_url, fallback_db_url=test_db_url)
    h = app.state.handlers

    # Simulasikan kegagalan koneksi database saat runtime
    app.state.db.simulate_failure = True

    health = _run_sync(h["health"]())
    assert health["status"] == "ok"
    assert health["model_loaded"] is True
    assert health["db_connected"] is False

    kp = np.random.uniform(0.2, 0.8, size=(12, 86, 3)).astype(np.float32).tolist()
    pred = _run_sync(h["predict"](PredictRequest(keypoints=kp, top_k=3)))
    assert "gloss" in pred and len(pred["top_k"]) == 3

    sent = _run_sync(h["sentence"](SentenceRequest(gloss="SAYA BELAJAR BUKU", lang="id")))
    assert len(sent["text"]) > 5

    tr = _run_sync(h["translate"](TranslateRequest(text="Halo guru", src="id", tgt="fil")))
    assert "translation" in tr


def test_runtime_startup_without_torch(tmp_path: Path):
    """
    Pastikan server/app.py, signbridge.text, dan seeding database berhasil diimpor
    dan dijalankan di dalam container Docker ringan yang TIDAK memiliki PyTorch (torch=None).
    """
    import subprocess
    import sys

    db_path = (tmp_path / "no_torch_docker.db").as_posix()
    code = f"""
import sys
sys.modules['torch'] = None
sys.modules['torch.nn'] = None
sys.modules['torch.nn.functional'] = None

from signbridge.text.pseudo_gloss import gloss_to_sentence_rules, sentence_to_pseudo_gloss
assert gloss_to_sentence_rules("HALO GURU", lang="id") == "Halo guru."
assert "PAGI" in sentence_to_pseudo_gloss("Saya belajar pagi ini.")

from server.app import create_app, SentenceRequest
app = create_app(database_url="sqlite:///{db_path}", fallback_db_url="sqlite:///{db_path}")
assert app.state.db.is_connected() is True
st = app.state.db.get_status_summary()
assert st["counts"]["sign_concepts"] == 58
assert st["counts"]["model_versions"] == 20
assert st["counts"]["evaluation_runs"] >= 3
print("NO_TORCH_DOCKER_OK")
"""
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"Gagal tanpa torch:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    assert "NO_TORCH_DOCKER_OK" in proc.stdout


def test_training_imports_remain_available():
    """
    Pastikan seluruh modul training tetap dapat diimpor dari signbridge.text,
    signbridge.audio, dan signbridge.image ketika PyTorch tersedia.
    """
    from signbridge.audio import WhisperASRWrapper, compute_cer, compute_rtf, compute_wer, run_asr_experiment
    from signbridge.image import build_image_model, compute_hand_crop_box, export_fingerspell_onnx, run_image_training
    from signbridge.text import (
        GRUAttentionSeq2Seq,
        compute_bleu,
        compute_chrf,
        gloss_to_sentence_rules,
        run_text_experiment,
        run_translation_eval,
        sentence_to_pseudo_gloss,
    )

    assert callable(gloss_to_sentence_rules)
    assert callable(sentence_to_pseudo_gloss)
    assert callable(compute_bleu)
    assert callable(compute_chrf)
    assert callable(run_text_experiment)
    assert callable(run_translation_eval)
    assert GRUAttentionSeq2Seq is not None
    assert callable(compute_wer)
    assert callable(compute_cer)
    assert callable(compute_rtf)
    assert callable(run_asr_experiment)
    assert WhisperASRWrapper is not None
    assert callable(compute_hand_crop_box)
    assert callable(build_image_model)
    assert callable(run_image_training)
    assert callable(export_fingerspell_onnx)


