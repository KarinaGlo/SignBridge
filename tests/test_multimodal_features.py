"""
tests/test_multimodal_features.py — Kontrak 7: preprocessing 4 modalitas model fusion M6 (tanpa PyTorch).
"""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from signbridge.multimodal.constants import (
    AUDIO_NUM_FRAMES,
    AUDIO_NUM_MELS,
    AUDIO_SAMPLE_RATE,
    IMAGE_SIDE,
    MODALITIES,
    TEXT_MAX_LEN,
)
from signbridge.multimodal.dataset import (
    MultimodalRecord,
    MultimodalSampleLoader,
    assign_splits,
    read_manifest,
    write_manifest,
)
from signbridge.multimodal.features import (
    decode_text,
    encode_text,
    load_audio,
    load_image,
    log_mel,
    pose_from_sequence,
    read_wav,
    resample_linear,
    write_wav,
)


def _fake_kp_seq(frames: int = 40, seed: int = 0) -> list:
    rng = np.random.default_rng(seed)
    kp = rng.uniform(0.2, 0.8, size=(frames, 86, 3)).astype(np.float32)
    kp[:, 9:30] = 0.0  # tangan kiri tidak terdeteksi (format perekam: nol)
    return kp.tolist()


def _tone(seconds: float = 2.5, sr: int = 48_000, hz: float = 440.0) -> np.ndarray:
    t = np.arange(int(seconds * sr)) / sr
    return (0.3 * np.sin(2 * np.pi * hz * t)).astype(np.float32)


def test_modality_order_is_fixed():
    assert MODALITIES == ["video", "image", "audio", "text"]


def test_pose_from_sequence_shape_and_zero_handling():
    pose, ok = pose_from_sequence(_fake_kp_seq())
    assert ok and pose.shape == (64, 86, 3) and pose.dtype == np.float32
    assert np.all(np.isfinite(pose))
    assert np.allclose(pose[:, 9:30], 0.0)  # titik hilang tetap nol setelah normalisasi


def test_pose_empty_is_missing():
    pose, ok = pose_from_sequence([])
    assert not ok and pose.shape == (64, 86, 3)


def test_wav_roundtrip_and_resample(tmp_path: Path):
    x = _tone(sr=48_000)
    p = tmp_path / "a.wav"
    write_wav(p, x, sr=48_000)
    pcm, sr = read_wav(p)
    assert sr == 48_000 and pcm.shape == x.shape
    assert np.max(np.abs(pcm - x)) < 1e-3
    y = resample_linear(pcm, 48_000, AUDIO_SAMPLE_RATE)
    assert abs(y.size - 40_000) <= 1


def test_log_mel_shape_and_standardized():
    feat = log_mel(_tone(sr=16_000))
    assert feat.shape == (AUDIO_NUM_MELS, AUDIO_NUM_FRAMES) == (64, 248)
    assert abs(float(feat.mean())) < 1e-3 and abs(float(feat.std()) - 1.0) < 1e-2


def test_log_mel_peak_bin_follows_frequency():
    low = log_mel(_tone(sr=16_000, hz=300.0)).mean(axis=1).argmax()
    high = log_mel(_tone(sr=16_000, hz=3000.0)).mean(axis=1).argmax()
    assert high > low


def test_silent_audio_counts_as_missing(tmp_path: Path):
    p = tmp_path / "silent.wav"
    write_wav(p, np.zeros(16_000, dtype=np.float32), sr=16_000)
    feat, ok = load_audio(p)
    assert not ok and feat.shape == (64, 248)


def test_text_encoding_char_level():
    ids, ok = encode_text("Terima_kasih, Guru!")
    assert ok and ids.shape == (TEXT_MAX_LEN,) and ids.dtype == np.int64
    assert decode_text(ids) == "terima kasih, guru!"
    empty, ok2 = encode_text("   ")
    assert not ok2 and not empty.any()


def test_image_loading(tmp_path: Path):
    PIL = pytest.importorskip("PIL.Image")
    img = PIL.new("RGB", (320, 240), (200, 120, 40))
    p = tmp_path / "hand.jpg"
    img.save(p)
    arr, ok = load_image(p)
    assert ok and arr.shape == (3, IMAGE_SIDE, IMAGE_SIDE) and arr.dtype == np.float32
    missing, ok2 = load_image(tmp_path / "nope.jpg")
    assert not ok2 and not missing.any()


def test_manifest_roundtrip_and_loader_mask(tmp_path: Path):
    kp = tmp_path / "c1_kp.json"
    kp.write_text(json.dumps({"keypoints": _fake_kp_seq()}), encoding="utf-8")
    wav = tmp_path / "c1.wav"
    write_wav(wav, _tone(sr=16_000), sr=16_000)
    recs = [
        MultimodalRecord("c1", "S01", "gloss", "MAKAN", 7, kp_path=str(kp), audio_path=str(wav), text="saya makan"),
        MultimodalRecord("c2", "S01", "gloss", "AIR", 0, text="air"),
    ]
    mpath = tmp_path / "manifest_multimodal.csv"
    write_manifest(recs, mpath)
    back = read_manifest(mpath)
    loader = MultimodalSampleLoader(back)
    s1, s2 = loader.load(0), loader.load(1)
    assert s1["modality_mask"].tolist() == [1.0, 0.0, 1.0, 1.0]
    assert s2["modality_mask"].tolist() == [0.0, 0.0, 0.0, 1.0]
    assert int(s1["label"]) == 7
    assert s1["pose"].shape == (64, 86, 3) and s1["audio"].shape == (64, 248)


def test_assign_splits_sd_and_si():
    recs = [MultimodalRecord(f"S0{s}_t{t}", f"S0{s}", "gloss", "AIR", 0) for s in (1, 2, 3) for t in range(10)]
    assign_splits(recs, protocol="sd")
    for s in ("S01", "S02", "S03"):
        splits = [r.split for r in recs if r.signer == s]
        assert splits.count("test") >= 1 and splits.count("val") >= 1 and splits.count("train") >= 6
    assign_splits(recs, protocol="si", test_signer="S03")
    assert all(r.split == "test" for r in recs if r.signer == "S03")
    assert all(r.split in ("train", "val") for r in recs if r.signer != "S03")


def test_build_manifest_from_recorder_zip(tmp_path: Path):
    from scripts.build_multimodal_manifest import main as build_main

    zdir = tmp_path / "zips"
    zdir.mkdir()
    wav_path = tmp_path / "tmp.wav"
    write_wav(wav_path, _tone(sr=16_000), sr=16_000)
    base = "S01/gloss/MAKAN/take_01"
    rows = [
        "clip_id,signer,category,target,label,take,kp_path,handcrop_path,portrait_path,audio_path,text",
        f"S01_gloss_MAKAN_take01,S01,gloss,MAKAN,7,1,{base}_kp.json,{base}_hand.jpg,{base}_portrait.jpg,{base}.wav,saya mau makan",
        "S01_letter_A_take02,S01,letter,A,0,2,,,,,a",
    ]
    with zipfile.ZipFile(zdir / "SignBridge_S01_1.zip", "w") as z:
        z.writestr(f"{base}_kp.json", json.dumps({"keypoints": _fake_kp_seq()}))
        z.write(wav_path, f"{base}.wav")
        z.writestr("manifest_selfrec.csv", "\n".join(rows) + "\n")
    out = tmp_path / "mm"
    assert build_main(["--zips", str(zdir), "--out", str(out)]) == 0
    with (out / "manifest_multimodal.csv").open(encoding="utf-8") as f:
        got = list(csv.DictReader(f))
    assert len(got) == 1  # baris huruf dilewati
    assert got[0]["gloss"] == "MAKAN" and got[0]["label"] == "7"
    assert got[0]["kp_path"].endswith("_kp.json") and got[0]["audio_path"].endswith(".wav")
    assert got[0]["image_path"] == ""  # foto tidak ada di ZIP -> modalitas hilang
