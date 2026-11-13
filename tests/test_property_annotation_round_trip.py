"""
test_property_annotation_round_trip.py — Property-based tests untuk annotation round-trip.

Property 3: Annotation Round-Trip
Untuk sembarang VideoMetadata yang valid, serialize → deserialize harus
menghasilkan objek dengan nilai identik pada semua field wajib dan opsional.

**Validates: Requirements 1.5, 15.4, 15.5**
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from src.data.annotation_parser import AnnotationParser, VALID_SPLITS
from src.data.models import VideoMetadata
from src.exceptions import SchemaValidationError

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters=("\x00",)),
    min_size=1, max_size=150,
)
_split_st = st.sampled_from(sorted(VALID_SPLITS))
_vm_strategy = st.builds(
    VideoMetadata,
    path=_safe_text, gloss=_safe_text, signer_id=_safe_text, split=_split_st,
    duration_sec=st.one_of(st.none(), st.floats(0.01, 7200.0, allow_nan=False, allow_infinity=False)),
    resolution=st.one_of(st.none(), st.from_regex(r"\d{2,4}x\d{2,4}", fullmatch=True)),
    fps=st.one_of(st.none(), st.floats(1.0, 240.0, allow_nan=False, allow_infinity=False)),
)


# ---------------------------------------------------------------------------
# Property 3.1 — Single VideoMetadata round-trip: required fields identical
# Validates: Requirements 1.5, 15.4, 15.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(record=_vm_strategy)
def test_single_record_required_fields_round_trip(record: VideoMetadata) -> None:
    """
    Property 3.1: Untuk satu VideoMetadata, serialize → deserialize menghasilkan
    nilai path, gloss, signer_id, split yang identik.

    **Validates: Requirements 1.5, 15.4, 15.5**
    """
    parser = AnnotationParser()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "single.jsonl"
        parser.save([record], p)
        loaded = parser.load(p)

    assert len(loaded) == 1
    r = loaded[0]
    assert r.path == record.path, f"path mismatch: {r.path!r} != {record.path!r}"
    assert r.gloss == record.gloss, f"gloss mismatch: {r.gloss!r} != {record.gloss!r}"
    assert r.signer_id == record.signer_id, f"signer_id mismatch: {r.signer_id!r} != {record.signer_id!r}"
    assert r.split == record.split, f"split mismatch: {r.split!r} != {record.split!r}"


# ---------------------------------------------------------------------------
# Property 3.2 — List of 1-20 records round-trip: all required fields, same count
# Validates: Requirements 1.5, 15.4, 15.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(records=st.lists(_vm_strategy, min_size=1, max_size=20))
def test_list_round_trip_count_and_required_fields(records: list[VideoMetadata]) -> None:
    """
    Property 3.2: Untuk 1–20 VideoMetadata, serialize → deserialize menghasilkan
    jumlah record identik dan semua field wajib identik untuk setiap record.

    **Validates: Requirements 1.5, 15.4, 15.5**
    """
    parser = AnnotationParser()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "list.jsonl"
        parser.save(records, p)
        loaded = parser.load(p)

    assert len(loaded) == len(records), (
        f"count mismatch: {len(loaded)} loaded, {len(records)} original"
    )
    for i, (orig, result) in enumerate(zip(records, loaded)):
        assert result.path == orig.path, f"[{i}] path mismatch"
        assert result.gloss == orig.gloss, f"[{i}] gloss mismatch"
        assert result.signer_id == orig.signer_id, f"[{i}] signer_id mismatch"
        assert result.split == orig.split, f"[{i}] split mismatch"


# ---------------------------------------------------------------------------
# Property 3.3 — Optional fields (duration_sec, fps) preserved within float precision
# Validates: Requirements 1.5, 15.4, 15.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(record=st.builds(
    VideoMetadata,
    path=_safe_text, gloss=_safe_text, signer_id=_safe_text, split=_split_st,
    duration_sec=st.floats(0.01, 7200.0, allow_nan=False, allow_infinity=False),
    resolution=st.one_of(st.none(), st.from_regex(r"\d{2,4}x\d{2,4}", fullmatch=True)),
    fps=st.floats(1.0, 240.0, allow_nan=False, allow_infinity=False),
))
def test_optional_float_fields_preserved_within_precision(record: VideoMetadata) -> None:
    """
    Property 3.3: Field opsional duration_sec dan fps yang tidak None harus
    bertahan melalui round-trip dengan presisi float64 JSON standard.

    **Validates: Requirements 1.5, 15.4, 15.5**
    """
    parser = AnnotationParser()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "float_opt.jsonl"
        parser.save([record], p)
        loaded = parser.load(p)

    r = loaded[0]
    # duration_sec harus dipertahankan
    assert r.duration_sec is not None
    assert math.isclose(r.duration_sec, record.duration_sec, rel_tol=1e-9, abs_tol=0.0), (
        f"duration_sec mismatch: {r.duration_sec!r} vs {record.duration_sec!r}"
    )
    # fps harus dipertahankan
    assert r.fps is not None
    assert math.isclose(r.fps, record.fps, rel_tol=1e-9, abs_tol=0.0), (
        f"fps mismatch: {r.fps!r} vs {record.fps!r}"
    )


# ---------------------------------------------------------------------------
# Property 3.4 — Optional fields=None yield None after round-trip (not written to JSON)
# Validates: Requirements 1.5, 15.4, 15.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    path_val=_safe_text,
    gloss_val=_safe_text,
    signer_id_val=_safe_text,
    split_val=_split_st,
)
def test_optional_fields_none_round_trip_yields_none(
    path_val: str,
    gloss_val: str,
    signer_id_val: str,
    split_val: str,
) -> None:
    """
    Property 3.4: Field opsional yang di-set None tidak ditulis ke JSON, dan
    setelah load kembali menghasilkan None (bukan nilai default lain).

    **Validates: Requirements 1.5, 15.4, 15.5**
    """
    record = VideoMetadata(
        path=path_val,
        gloss=gloss_val,
        signer_id=signer_id_val,
        split=split_val,
        duration_sec=None,
        resolution=None,
        fps=None,
    )
    import json as _json
    parser = AnnotationParser()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "none_opt.jsonl"
        parser.save([record], p)
        # Pastikan field opsional benar-benar tidak ada sebagai key di objek JSON
        raw_content = p.read_text(encoding="utf-8")
        serialized_obj = _json.loads(raw_content.strip())
        assert "duration_sec" not in serialized_obj, (
            "duration_sec key should not be written when None"
        )
        assert "fps" not in serialized_obj, "fps key should not be written when None"
        assert "resolution" not in serialized_obj, (
            "resolution key should not be written when None"
        )
        loaded = parser.load(p)

    r = loaded[0]
    assert r.duration_sec is None, f"duration_sec should be None, got {r.duration_sec!r}"
    assert r.resolution is None, f"resolution should be None, got {r.resolution!r}"
    assert r.fps is None, f"fps should be None, got {r.fps!r}"


# ---------------------------------------------------------------------------
# Property 3.5 — All valid splits ("train","val","test") round-trip correctly
# Validates: Requirements 1.5, 15.4, 15.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    path_val=_safe_text,
    gloss_val=_safe_text,
    signer_id_val=_safe_text,
    split_val=_split_st,
)
def test_all_valid_splits_round_trip(
    path_val: str,
    gloss_val: str,
    signer_id_val: str,
    split_val: str,
) -> None:
    """
    Property 3.5: Semua nilai split yang valid ("train", "val", "test") harus
    bertahan persis melalui round-trip serialize → deserialize.

    **Validates: Requirements 1.5, 15.4, 15.5**
    """
    assert split_val in VALID_SPLITS, f"Strategy produced invalid split: {split_val!r}"

    record = VideoMetadata(
        path=path_val,
        gloss=gloss_val,
        signer_id=signer_id_val,
        split=split_val,
    )
    parser = AnnotationParser()
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "split_rt.jsonl"
        parser.save([record], p)
        loaded = parser.load(p)

    assert len(loaded) == 1
    r = loaded[0]
    assert r.split == split_val, (
        f"split mismatch after round-trip: {r.split!r} != {split_val!r}"
    )
    assert r.split in VALID_SPLITS, (
        f"loaded split {r.split!r} is not in VALID_SPLITS"
    )
