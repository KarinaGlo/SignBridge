"""
test_keypoint_parser.py — Unit tests dan property tests untuk KeypointParser.

Validates: Requirements 15.1, 15.2, 15.3, 3.2, 3.6
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from src.data.annotation_parser import AnnotationParser, VALID_SPLITS
from src.data.keypoint_parser import (
    NUM_COORDS,
    NUM_KEYPOINTS,
    T_MAX,
    T_MIN,
    KeypointParser,
)
from src.exceptions import SchemaValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_array(T: int = 10) -> np.ndarray:
    """Buat array keypoint valid [T, 543, 3] float32 dengan nilai ∈ [-1, 1]."""
    rng = np.random.default_rng(42)
    return rng.uniform(-1.0, 1.0, size=(T, 543, 3)).astype(np.float32)


# ---------------------------------------------------------------------------
# Unit Tests — Round-trip & basic load/save
# ---------------------------------------------------------------------------

def test_load_valid_array_round_trip(tmp_path):
    """Save lalu load menghasilkan array yang identik."""
    arr = _valid_array(T=5)
    parser = KeypointParser()
    p = tmp_path / "kp.npy"
    parser.save(arr, p)
    loaded = parser.load(p)
    assert loaded.shape == arr.shape
    assert loaded.dtype == np.float32
    np.testing.assert_array_equal(loaded, arr)


def test_load_raises_filenotfound(tmp_path):
    """Load dari path yang tidak ada harus raise FileNotFoundError."""
    parser = KeypointParser()
    with pytest.raises(FileNotFoundError):
        parser.load(tmp_path / "nonexistent.npy")


# ---------------------------------------------------------------------------
# Unit Tests — Shape validation
# ---------------------------------------------------------------------------

def test_load_raises_wrong_shape_keypoints(tmp_path):
    """Shape [T, 100, 3] (keypoints salah) harus raise SchemaValidationError."""
    arr = np.zeros((5, 100, 3), dtype=np.float32)
    p = tmp_path / "bad_kp.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "shape"


def test_load_raises_wrong_shape_coords(tmp_path):
    """Shape [T, 543, 4] (koordinat salah) harus raise SchemaValidationError."""
    arr = np.zeros((5, 543, 4), dtype=np.float32)
    p = tmp_path / "bad_coords.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "shape"


def test_load_raises_t_too_small(tmp_path):
    """Shape [0, 543, 3] (T=0 < T_MIN=1) harus raise SchemaValidationError."""
    arr = np.zeros((0, 543, 3), dtype=np.float32)
    p = tmp_path / "t_zero.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "shape"


def test_load_raises_t_too_large(tmp_path):
    """Shape [10001, 543, 3] (T > T_MAX=10000) harus raise SchemaValidationError."""
    # Simpan langsung tanpa validasi parser untuk menghindari membuat array besar
    arr = np.zeros((10001, 543, 3), dtype=np.float32)
    p = tmp_path / "t_large.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "shape"


# ---------------------------------------------------------------------------
# Unit Tests — Dtype validation
# ---------------------------------------------------------------------------

def test_load_raises_wrong_dtype(tmp_path):
    """Array dtype float64 harus raise SchemaValidationError dengan field_name='dtype'."""
    arr = np.zeros((5, 543, 3), dtype=np.float64)
    p = tmp_path / "bad_dtype.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "dtype"


# ---------------------------------------------------------------------------
# Unit Tests — Value range validation
# ---------------------------------------------------------------------------

def test_load_raises_values_above_1(tmp_path):
    """Nilai 1.01 harus raise SchemaValidationError dengan field_name='values'."""
    arr = _valid_array(T=3)
    arr[0, 0, 0] = 1.01
    p = tmp_path / "above.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "values"


def test_load_raises_values_below_minus_1(tmp_path):
    """Nilai -1.01 harus raise SchemaValidationError dengan field_name='values'."""
    arr = _valid_array(T=3)
    arr[0, 0, 0] = -1.01
    p = tmp_path / "below.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "values"


# ---------------------------------------------------------------------------
# Unit Tests — SchemaValidationError attributes
# ---------------------------------------------------------------------------

def test_schema_error_contains_filename(tmp_path):
    """Pesan SchemaValidationError harus memuat nama file."""
    arr = np.zeros((5, 100, 3), dtype=np.float32)
    fname = "my_keypoints.npy"
    p = tmp_path / fname
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert fname in str(exc_info.value)


def test_schema_error_field_name_shape(tmp_path):
    """error.field_name == 'shape' untuk array dengan shape salah."""
    arr = np.zeros((5, 200, 3), dtype=np.float32)
    p = tmp_path / "s.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "shape"


def test_schema_error_field_name_dtype(tmp_path):
    """error.field_name == 'dtype' untuk array dengan dtype salah."""
    arr = np.zeros((5, 543, 3), dtype=np.int32)
    p = tmp_path / "d.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "dtype"


def test_schema_error_field_name_values(tmp_path):
    """error.field_name == 'values' untuk array dengan nilai di luar rentang."""
    arr = _valid_array(T=2)
    arr[1, 10, 2] = 2.5
    p = tmp_path / "v.npy"
    np.save(str(p), arr)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)
    assert exc_info.value.field_name == "values"


# ---------------------------------------------------------------------------
# Unit Tests — Save behaviour
# ---------------------------------------------------------------------------

def test_save_creates_parent_dirs(tmp_path):
    """save() harus membuat direktori induk yang belum ada."""
    arr = _valid_array(T=2)
    p = tmp_path / "nested" / "deep" / "kp.npy"
    parser = KeypointParser()
    parser.save(arr, p)
    assert p.exists()


# ---------------------------------------------------------------------------
# Unit Tests — Boundary values
# ---------------------------------------------------------------------------

def test_boundary_values_accepted(tmp_path):
    """Nilai tepat -1.0 dan 1.0 harus dianggap valid."""
    arr = np.zeros((3, 543, 3), dtype=np.float32)
    arr[0, 0, 0] = -1.0
    arr[0, 0, 1] = 1.0
    p = tmp_path / "boundary.npy"
    parser = KeypointParser()
    parser.save(arr, p)
    loaded = parser.load(p)
    np.testing.assert_array_equal(loaded, arr)


def test_t_min_boundary(tmp_path):
    """T=1 (batas minimum) harus valid."""
    arr = np.zeros((1, 543, 3), dtype=np.float32)
    p = tmp_path / "t1.npy"
    parser = KeypointParser()
    parser.save(arr, p)
    loaded = parser.load(p)
    assert loaded.shape == (1, 543, 3)


def test_t_max_boundary(tmp_path):
    """T=10000 (batas maksimum) harus valid — gunakan array kecil yang di-reshape."""
    # Buat array (10000, 543, 3) float32 dengan nilai 0 (hemat memori: ~6.6 MB)
    arr = np.zeros((10000, 543, 3), dtype=np.float32)
    p = tmp_path / "t10000.npy"
    parser = KeypointParser()
    parser.save(arr, p)
    loaded = parser.load(p)
    assert loaded.shape == (10000, 543, 3)


# ---------------------------------------------------------------------------
# Property Test — Property 4: Keypoint Array Round-Trip
# ---------------------------------------------------------------------------

# Feature: signbridge-bisindo, Property 4: Keypoint Array Round-Trip
@settings(max_examples=100)
@given(
    arr=arrays(
        dtype=np.float32,
        shape=st.tuples(
            st.integers(min_value=T_MIN, max_value=100),
            st.just(NUM_KEYPOINTS),
            st.just(NUM_COORDS),
        ),
        elements=st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False),
    )
)
def test_property_4_keypoint_array_round_trip(tmp_path_factory, arr):
    """
    Property 4: Keypoint Array Round-Trip
    Save → load produces array with identical shape, dtype, and values
    for any valid array with shape [T, 543, 3], dtype float32, values ∈ [-1.0, 1.0].

    **Validates: Requirements 3.2, 3.6**
    """
    parser = KeypointParser()
    tmp = tmp_path_factory.mktemp("kp")
    p = tmp / "test.npy"
    parser.save(arr, p)
    loaded = parser.load(p)
    assert loaded.shape == arr.shape
    assert loaded.dtype == np.float32
    np.testing.assert_array_equal(loaded, arr)


# ---------------------------------------------------------------------------
# Property Tests — Property 18: Schema Validation Rejection
# ---------------------------------------------------------------------------
#
# Feature: signbridge-bisindo, Property 18: Schema Validation Rejection
#
# KeypointParser side — property-based and parametric unit tests.
# AnnotationParser side — see test_annotation_parser.py which already contains
#   test_property_invalid_split_raises_schema_error and
#   test_property_missing_required_field_raises_schema_error (Property 18 partial).
#
# **Validates: Requirements 15.1, 15.2, 15.3**
# ---------------------------------------------------------------------------


# -- KeypointParser: wrong shape (property-based) ----------------------------

@settings(max_examples=100)
@given(
    bad_shape=st.one_of(
        # Wrong keypoints dimension (not 543)
        st.tuples(st.integers(1, 50), st.integers(1, 542), st.just(3)),
        st.tuples(st.integers(1, 50), st.integers(544, 600), st.just(3)),
        # Wrong coords dimension (not 3)
        st.tuples(st.integers(1, 50), st.just(NUM_KEYPOINTS), st.integers(1, 2)),
        st.tuples(st.integers(1, 50), st.just(NUM_KEYPOINTS), st.integers(4, 6)),
    )
)
def test_property_18_wrong_shape_raises_schema_error(bad_shape):
    """
    Property 18: KeypointParser.validate() must raise SchemaValidationError
    with field_name == "shape" for any array whose shape is not [T, 543, 3].

    **Validates: Requirements 15.1, 15.3**
    """
    arr = np.zeros(bad_shape, dtype=np.float32)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.validate(arr)
    assert exc_info.value.field_name == "shape"


# -- KeypointParser: T out-of-range ------------------------------------------

@pytest.mark.parametrize("bad_T", [0, T_MAX + 1])
def test_property_18_t_out_of_range_raises_schema_error(bad_T):
    """
    Property 18: T=0 (below T_MIN) and T=10001 (above T_MAX) must be rejected.

    **Validates: Requirements 15.1, 15.3**
    """
    arr = np.zeros((bad_T, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.validate(arr)
    assert exc_info.value.field_name == "shape"


# -- KeypointParser: wrong dtype ---------------------------------------------

def test_property_18_float64_dtype_raises_schema_error():
    """
    Property 18: Array with dtype float64 (instead of float32) must raise
    SchemaValidationError with field_name == "dtype".

    **Validates: Requirements 15.1, 15.3**
    """
    arr = np.zeros((5, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float64)
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.validate(arr)
    assert exc_info.value.field_name == "dtype"


# -- KeypointParser: value out-of-range --------------------------------------

@pytest.mark.parametrize("bad_value", [1.0001, -1.0001, 2.0, -2.0, 100.0, -100.0])
def test_property_18_value_out_of_range_raises_schema_error(bad_value):
    """
    Property 18: Values outside [-1.0, 1.0] must raise SchemaValidationError
    with field_name == "values".

    **Validates: Requirements 15.1, 15.3**
    """
    arr = np.zeros((5, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)
    arr[0, 0, 0] = bad_value
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.validate(arr)
    assert exc_info.value.field_name == "values"


# -- KeypointParser: NaN values ----------------------------------------------

def test_property_18_nan_values_raises_schema_error():
    """
    Property 18: Array containing NaN values must raise SchemaValidationError
    with field_name == "values".

    **Validates: Requirements 15.1, 15.3**
    """
    arr = np.zeros((5, NUM_KEYPOINTS, NUM_COORDS), dtype=np.float32)
    arr[2, 100, 1] = float("nan")
    parser = KeypointParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.validate(arr)
    assert exc_info.value.field_name == "values"


# -- AnnotationParser: missing required fields (Property 18 — unit) ----------

@pytest.mark.parametrize("missing_field", ["path", "gloss", "signer_id", "split"])
def test_property_18_annotation_missing_field_raises_schema_error(tmp_path, missing_field):
    """
    Property 18: AnnotationParser.load() must raise SchemaValidationError
    identifying the missing required field name for any record that omits it.

    **Validates: Requirements 15.2, 15.3**
    """
    row = {
        "path": "videos/MAKAN/signer01_001.mp4",
        "gloss": "MAKAN",
        "signer_id": "signer01",
        "split": "train",
    }
    del row[missing_field]

    p = tmp_path / "missing.jsonl"
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")

    parser = AnnotationParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)

    err = exc_info.value
    assert err.field_name == missing_field
    assert err.line_number == 1


# -- AnnotationParser: invalid split value (Property 18 — unit) --------------

@pytest.mark.parametrize("bad_split", ["Train", "VAL", "TEST", "unknown", "", " train"])
def test_property_18_annotation_invalid_split_raises_schema_error(tmp_path, bad_split):
    """
    Property 18: AnnotationParser.load() must raise SchemaValidationError
    with field_name == "split" for any record with a split value not in
    {"train", "val", "test"}.

    **Validates: Requirements 15.2, 15.3**
    """
    row = {
        "path": "videos/MAKAN/signer01_001.mp4",
        "gloss": "MAKAN",
        "signer_id": "signer01",
        "split": bad_split,
    }

    p = tmp_path / "bad_split.jsonl"
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")

    parser = AnnotationParser()
    with pytest.raises(SchemaValidationError) as exc_info:
        parser.load(p)

    err = exc_info.value
    assert err.field_name == "split"
    assert err.found_value == bad_split
    assert err.line_number == 1
