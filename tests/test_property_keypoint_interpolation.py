"""
test_property_keypoint_interpolation.py — Property-based and unit tests for
KeypointExtractor._apply_interpolation().

Validates: Requirements 3.3, 3.4
"""
from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.data.keypoint_extractor import (
    KeypointExtractor,
    NUM_KEYPOINTS,
    INTERPOLATION_WINDOW,
    _GROUP_SLICES,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_sequence(T: int, missing_frames: list[int], group_idx: int = 0):
    """Build keypoints, confidence, frame_detected with some frames missing."""
    # Give each frame a unique distinguishable value: t * 0.01
    keypoints = np.zeros((T, NUM_KEYPOINTS, 3), dtype=np.float32)
    for t in range(T):
        keypoints[t] = t * 0.01

    frame_detected = np.ones((T, 4), dtype=bool)
    confidence = np.ones((T, NUM_KEYPOINTS, 1), dtype=np.float32)

    group_names = ["left_hand", "right_hand", "pose", "face"]
    slc = _GROUP_SLICES[group_names[group_idx]]

    for f in missing_frames:
        frame_detected[f, group_idx] = False
        keypoints[f, slc] = 0.0  # will be overwritten by interpolation
        confidence[f, slc] = 0.0

    return keypoints, confidence, frame_detected


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

def test_interpolation_fills_single_missing_frame():
    """T=10, group 0 missing at frame 5 → confidence[5, left_hand] == 0.5 after interpolation."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [5], group_idx=0)

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    slc = _GROUP_SLICES["left_hand"]
    assert np.all(confidence[5, slc] == 0.5), (
        f"Expected confidence 0.5 at frame 5 for left_hand, got {confidence[5, slc]}"
    )


def test_no_nan_after_interpolation():
    """T=10, various missing frames → no NaN in output."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [0, 3, 7, 9], group_idx=0)

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    assert not np.any(np.isnan(keypoints)), "keypoints contains NaN after interpolation"
    assert not np.any(np.isnan(confidence)), "confidence contains NaN after interpolation"


def test_zero_padded_when_no_neighbors_in_window():
    """T=1, frame 0 missing → confidence == 0.0 (zero-padded, no neighbors)."""
    T = 1
    keypoints, confidence, frame_detected = make_sequence(T, [0], group_idx=0)

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    slc = _GROUP_SLICES["left_hand"]
    assert np.all(confidence[0, slc] == 0.0), (
        f"Expected confidence 0.0 for zero-padded frame, got {confidence[0, slc]}"
    )


def test_interpolated_value_between_neighbors():
    """T=11, frame 5 missing, has left(4) and right(6) → value at 5 is midpoint of 4 and 6."""
    T = 11
    keypoints, confidence, frame_detected = make_sequence(T, [5], group_idx=0)

    slc = _GROUP_SLICES["left_hand"]
    left_val = keypoints[4, slc].copy()
    right_val = keypoints[6, slc].copy()
    expected_midpoint = (left_val + right_val) / 2.0

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    np.testing.assert_allclose(
        keypoints[5, slc], expected_midpoint, atol=1e-5,
        err_msg="Interpolated value at frame 5 is not the midpoint of neighbors at 4 and 6",
    )


def test_nearest_neighbor_left_only():
    """T=10, frame 9 missing (rightmost) and frame 8 valid → uses left neighbor."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [9], group_idx=0)

    slc = _GROUP_SLICES["left_hand"]
    left_val = keypoints[8, slc].copy()

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    np.testing.assert_allclose(
        keypoints[9, slc], left_val, atol=1e-5,
        err_msg="Frame 9 (rightmost missing) should copy from left neighbor frame 8",
    )
    assert np.all(confidence[9, slc] == 0.5)


def test_nearest_neighbor_right_only():
    """T=10, frame 0 missing and frame 1 valid → uses right neighbor."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [0], group_idx=0)

    slc = _GROUP_SLICES["left_hand"]
    right_val = keypoints[1, slc].copy()

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    np.testing.assert_allclose(
        keypoints[0, slc], right_val, atol=1e-5,
        err_msg="Frame 0 (leftmost missing) should copy from right neighbor frame 1",
    )
    assert np.all(confidence[0, slc] == 0.5)


def test_return_values_count_interpolated():
    """T=10, 2 missing frames both have neighbors → num_interpolated >= 1."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [3, 6], group_idx=0)

    num_interpolated, num_zero_padded = KeypointExtractor._apply_interpolation(
        keypoints, confidence, frame_detected
    )

    assert num_interpolated >= 1, (
        f"Expected num_interpolated >= 1, got {num_interpolated}"
    )


def test_return_values_count_zero_padded():
    """T=1 (frame 0 missing, group 0) → num_zero_padded >= 1."""
    T = 1
    keypoints, confidence, frame_detected = make_sequence(T, [0], group_idx=0)

    num_interpolated, num_zero_padded = KeypointExtractor._apply_interpolation(
        keypoints, confidence, frame_detected
    )

    assert num_zero_padded >= 1, (
        f"Expected num_zero_padded >= 1, got {num_zero_padded}"
    )


def test_detected_frames_unchanged():
    """Detected frames should keep their original keypoint values."""
    T = 10
    keypoints, confidence, frame_detected = make_sequence(T, [5], group_idx=0)

    slc = _GROUP_SLICES["left_hand"]
    # Save originals for all non-missing frames
    originals = {t: keypoints[t, slc].copy() for t in range(T) if t != 5}

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    for t, original_val in originals.items():
        np.testing.assert_allclose(
            keypoints[t, slc], original_val, atol=1e-6,
            err_msg=f"Detected frame {t} was modified by interpolation",
        )


# ---------------------------------------------------------------------------
# Property-Based Tests
# Validates: Requirements 3.3, 3.4
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    T=st.integers(3, 30),
    n_missing=st.integers(1, 3),
    seed=st.integers(0, 9999),
)
def test_property_5_no_nan_after_interpolation(T: int, n_missing: int, seed: int):
    """
    **Validates: Requirements 3.3, 3.4**

    Property 5: No NaN values appear in keypoints or confidence after interpolation,
    regardless of how many frames are missing.
    """
    rng = np.random.default_rng(seed)
    # Choose missing frames without replacement, capped to valid range
    n_missing = min(n_missing, T)
    missing_frames = rng.choice(T, size=n_missing, replace=False).tolist()

    keypoints, confidence, frame_detected = make_sequence(T, missing_frames, group_idx=0)

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    assert not np.any(np.isnan(keypoints)), (
        f"NaN found in keypoints after interpolation. "
        f"T={T}, missing_frames={missing_frames}"
    )
    assert not np.any(np.isnan(confidence)), (
        f"NaN found in confidence after interpolation. "
        f"T={T}, missing_frames={missing_frames}"
    )


@settings(max_examples=100)
@given(T=st.integers(7, 30))
def test_property_5_interpolated_between_neighbors(T: int):
    """
    **Validates: Requirements 3.3, 3.4**

    Property 5: Interpolated value at f lies between values of neighbors at f-1 and f+1.
    Uses middle frame as missing to guarantee both neighbors exist.
    """
    f_missing = T // 2
    keypoints, confidence, frame_detected = make_sequence(T, [f_missing])

    # Record neighbor values before interpolation
    slc = _GROUP_SLICES["left_hand"]
    left_val = keypoints[f_missing - 1, slc, 0].copy()
    right_val = keypoints[f_missing + 1, slc, 0].copy()

    KeypointExtractor._apply_interpolation(keypoints, confidence, frame_detected)

    interpolated_val = keypoints[f_missing, slc, 0]
    lo = np.minimum(left_val, right_val)
    hi = np.maximum(left_val, right_val)
    assert np.all(interpolated_val >= lo - 1e-5), (
        f"Interpolated value {interpolated_val} is below lower bound {lo}"
    )
    assert np.all(interpolated_val <= hi + 1e-5), (
        f"Interpolated value {interpolated_val} is above upper bound {hi}"
    )
