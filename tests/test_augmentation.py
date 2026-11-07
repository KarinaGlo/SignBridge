"""
test_augmentation.py — Unit tests dan property-based tests untuk pipeline augmentasi.

Mencakup:
- TemporalAugmenter (Tasks 5.1, 5.2)
- SpatialKeypointAugmenter (Tasks 5.3, 5.4)
- SpatialRGBAugmenter (Task 5.5)
- AugmentationPipeline (Tasks 5.6, 5.7)
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.augmentation.temporal_augmenter import TemporalAugmenter
from src.augmentation.spatial_keypoint_augmenter import SpatialKeypointAugmenter
from src.augmentation.spatial_rgb_augmenter import SpatialRGBAugmenter
from src.augmentation.pipeline import (
    AugmentationConfig,
    AugmentationPipeline,
    AugmentationSample,
)


# =============================================================================
# TemporalAugmenter — Unit Tests (Task 5.1)
# =============================================================================


class TestTemporalAugmenterSpeedPerturbation:
    """Unit tests untuk speed_perturbation."""

    def test_speed_perturbation_length_s1(self):
        """s=1.0 → panjang output sama dengan T."""
        T = 20
        seq = np.arange(T * 3, dtype=np.float32).reshape(T, 3)
        aug = TemporalAugmenter(seed=0)
        out = aug.speed_perturbation(seq, speed_factor=1.0)
        assert len(out) == T

    def test_speed_perturbation_length_s2(self):
        """s=2.0 → panjang output ~T/2."""
        T = 20
        seq = np.arange(T * 3, dtype=np.float32).reshape(T, 3)
        aug = TemporalAugmenter(seed=0)
        out = aug.speed_perturbation(seq, speed_factor=2.0)
        expected = int(math.floor(T / 2.0))  # 10
        assert abs(len(out) - expected) <= 1

    def test_speed_perturbation_length_s05(self):
        """s=0.5 → panjang output ~T*2."""
        T = 20
        seq = np.arange(T * 3, dtype=np.float32).reshape(T, 3)
        aug = TemporalAugmenter(seed=0)
        out = aug.speed_perturbation(seq, speed_factor=0.5)
        expected = int(math.floor(T / 0.5))  # 40
        assert abs(len(out) - expected) <= 1


class TestTemporalAugmenterFrameDrop:
    """Unit tests untuk random_frame_drop."""

    def test_frame_drop_min_retained(self):
        """drop_ratio=0.2, T=20 → minimal ceil(20*0.8)=16 frame dipertahankan."""
        T = 20
        seq = np.arange(T * 3, dtype=np.float32).reshape(T, 3)
        aug = TemporalAugmenter(seed=0)
        out = aug.random_frame_drop(seq, drop_ratio=0.2)
        min_retained = math.ceil(T * 0.8)  # 16
        assert len(out) >= min_retained

    def test_frame_drop_preserves_order(self):
        """Frame yang dipertahankan harus dalam urutan asli."""
        T = 30
        seq = np.arange(T, dtype=np.float32).reshape(T, 1)
        aug = TemporalAugmenter(seed=42)
        out = aug.random_frame_drop(seq, drop_ratio=0.3)
        # Nilai harus monoton meningkat (urutan asli dijaga)
        assert all(out[i, 0] < out[i + 1, 0] for i in range(len(out) - 1))


class TestTemporalAugmenterJitter:
    """Unit tests untuk temporal_jitter."""

    def test_temporal_jitter_shape_preserved(self):
        """Shape[1:] harus tidak berubah setelah temporal jitter."""
        T = 15
        seq = np.zeros((T, 543, 3), dtype=np.float32)
        aug = TemporalAugmenter(seed=0)
        out = aug.temporal_jitter(seq, offset=2)
        assert out.shape == seq.shape

    def test_temporal_jitter_zero_offset(self):
        """offset=0 harus menghasilkan array identik."""
        T = 10
        seq = np.random.default_rng(0).random((T, 5)).astype(np.float32)
        aug = TemporalAugmenter(seed=0)
        out = aug.temporal_jitter(seq, offset=0)
        np.testing.assert_array_equal(out, seq)

    def test_temporal_jitter_positive_offset(self):
        """Offset positif: frame pertama hasil harus nol (padding)."""
        T = 10
        seq = np.ones((T, 3), dtype=np.float32)
        aug = TemporalAugmenter(seed=0)
        out = aug.temporal_jitter(seq, offset=3)
        np.testing.assert_array_equal(out[:3], np.zeros((3, 3), dtype=np.float32))


# =============================================================================
# Property 10: Temporal Augmentation Bounds (Task 5.2)
# =============================================================================


@settings(max_examples=100)
@given(
    T=st.integers(5, 50),
    s=st.floats(0.7, 1.3),
    r=st.floats(0.0, 0.20),
)
def test_property_10_temporal_augmentation_bounds(T, s, r):
    """
    Property 10: speed_perturbation output length = floor(T/s) ±1
    frame_drop retains >= ceil(T * (1-r)) frames

    Validates: Requirements 5.1
    """
    seq = np.arange(T * 3, dtype=np.float32).reshape(T, 3)
    aug = TemporalAugmenter(seed=42)

    # Speed perturbation
    out = aug.speed_perturbation(seq, speed_factor=s)
    expected = int(math.floor(T / s))
    assert abs(len(out) - expected) <= 1, (
        f"Speed perturbation: T={T}, s={s}, "
        f"expected ~{expected} but got {len(out)}"
    )

    # Frame drop
    out_drop = aug.random_frame_drop(seq, drop_ratio=r)
    min_retained = math.ceil(T * (1 - r))
    assert len(out_drop) >= min_retained, (
        f"Frame drop: T={T}, r={r}, "
        f"expected >= {min_retained} but got {len(out_drop)}"
    )


# =============================================================================
# SpatialKeypointAugmenter — Unit Tests (Task 5.3)
# =============================================================================


class TestSpatialKeypointAugmenter:
    """Unit tests untuk SpatialKeypointAugmenter."""

    def _make_seq(self, T: int = 5) -> np.ndarray:
        """Buat sekuens keypoint acak dengan shape [T, 543, 3]."""
        rng = np.random.default_rng(42)
        return rng.uniform(-1.0, 1.0, (T, 543, 3)).astype(np.float32)

    def test_flip_negates_x(self):
        """Koordinat x harus dinegasi setelah flip.

        Setelah flip: tangan kiri/kanan ditukar, sehingga:
          - flipped[:, 0:21, 0] == -seq[:, 21:42, 0]  (left ← negated right)
          - flipped[:, 21:42, 0] == -seq[:, 0:21, 0]  (right ← negated left)
          - flipped[:, 42:, 0] == -seq[:, 42:, 0]     (pose/wajah hanya dinegasi)
        """
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        flipped, _ = aug.flip(seq)

        # Tangan kiri setelah flip = negasi tangan kanan asli
        np.testing.assert_allclose(
            flipped[:, 0:21, 0], -seq[:, 21:42, 0], atol=1e-6,
            err_msg="Left hand x setelah flip harus = -right_hand_x asli"
        )
        # Tangan kanan setelah flip = negasi tangan kiri asli
        np.testing.assert_allclose(
            flipped[:, 21:42, 0], -seq[:, 0:21, 0], atol=1e-6,
            err_msg="Right hand x setelah flip harus = -left_hand_x asli"
        )
        # Keypoint lainnya (pose/wajah): hanya x dinegasi, tidak ditukar
        np.testing.assert_allclose(
            flipped[:, 42:, 0], -seq[:, 42:, 0], atol=1e-6,
            err_msg="Keypoint pose/wajah x harus dinegasi setelah flip"
        )

    def test_flip_preserves_yz(self):
        """Koordinat y dan z harus tidak berubah setelah flip (untuk non-hand keypoints)."""
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        flipped, _ = aug.flip(seq)
        # y dan z untuk area wajah [75:543] tidak berubah
        np.testing.assert_allclose(
            flipped[:, 75:, 1:], seq[:, 75:, 1:], atol=1e-6,
            err_msg="Koordinat y, z harus tidak berubah di area non-tangan"
        )

    def test_flip_swaps_hands(self):
        """Tangan kiri [0:21] dan tangan kanan [21:42] harus ditukar setelah flip."""
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        flipped, _ = aug.flip(seq)

        # Setelah flip: left hand baru = negasi right hand asli (hanya x yang dinegasi)
        # Koordinat yz dari left hand baru = right hand asli
        np.testing.assert_allclose(
            flipped[:, 0:21, 1:],   # left hand y,z setelah flip
            seq[:, 21:42, 1:],       # right hand y,z asli
            atol=1e-6,
            err_msg="Tangan kiri y,z setelah flip harus = tangan kanan asli y,z"
        )
        np.testing.assert_allclose(
            flipped[:, 21:42, 1:],  # right hand y,z setelah flip
            seq[:, 0:21, 1:],        # left hand y,z asli
            atol=1e-6,
            err_msg="Tangan kanan y,z setelah flip harus = tangan kiri asli y,z"
        )

    def test_rotate_2d_shape(self):
        """rotate_2d harus mempertahankan shape."""
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        out = aug.rotate_2d(seq, angle_deg=10.0)
        assert out.shape == seq.shape

    def test_rotate_2d_clips(self):
        """rotate_2d harus clip ke [-1, 1]."""
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        out = aug.rotate_2d(seq, angle_deg=45.0)
        assert out.min() >= -1.0 - 1e-7
        assert out.max() <= 1.0 + 1e-7

    def test_gaussian_noise_clips(self):
        """add_gaussian_noise harus clip ke [-1, 1]."""
        seq = self._make_seq()
        aug = SpatialKeypointAugmenter()
        out = aug.add_gaussian_noise(seq, std=0.02)
        assert out.min() >= -1.0 - 1e-7
        assert out.max() <= 1.0 + 1e-7


# =============================================================================
# Property 9: Horizontal Flip Involution (Task 5.4)
# =============================================================================


@settings(max_examples=100)
@given(
    T=st.integers(1, 20),
)
def test_property_9_flip_involution(T):
    """
    Property 9: flip(flip(seq)) == seq (involusi)
    Flip satu kali: keypoint tangan kiri/kanan ditukar DAN x dinegasi

    Validates: Requirements 5.2, 5.4
    """
    rng = np.random.default_rng(42)
    seq = rng.uniform(-1.0, 1.0, (T, 543, 3)).astype(np.float32)
    aug = SpatialKeypointAugmenter()

    flipped_once, _ = aug.flip(seq)
    flipped_twice, _ = aug.flip(flipped_once)

    np.testing.assert_allclose(
        flipped_twice, seq, atol=1e-6,
        err_msg="Double flip harus menghasilkan identitas"
    )

    # Setelah satu flip: x dinegasi DAN tangan ditukar
    # left_hand hasil = -original_right_hand (hanya x yang dinegasi)
    np.testing.assert_allclose(
        flipped_once[:, 0:21, 0],   # left hand x setelah flip
        -seq[:, 21:42, 0],           # harus = negasi right hand x asli
        atol=1e-6,
        err_msg="Left hand x setelah flip harus = -right_hand_x asli"
    )


# =============================================================================
# SpatialRGBAugmenter — Unit Tests (Task 5.5)
# =============================================================================


class TestSpatialRGBAugmenter:
    """Unit tests untuk SpatialRGBAugmenter."""

    def _make_frames(self, T: int = 4, H: int = 32, W: int = 32) -> np.ndarray:
        """Buat sekuens frame acak [T, H, W, 3] dalam [0, 1]."""
        rng = np.random.default_rng(42)
        return rng.random((T, H, W, 3)).astype(np.float32)

    def test_flip_shape_preserved(self):
        """flip harus mempertahankan shape."""
        frames = self._make_frames()
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.flip(frames)
        assert out.shape == frames.shape

    def test_flip_reverses_width(self):
        """flip harus membalik sumbu lebar."""
        frames = self._make_frames()
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.flip(frames)
        np.testing.assert_allclose(
            out[:, :, :, :], frames[:, :, ::-1, :],
            atol=1e-6
        )

    def test_random_crop_resize_shape(self):
        """random_crop_resize harus mempertahankan shape [T, H, W, 3]."""
        frames = self._make_frames(T=3, H=64, W=64)
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.random_crop_resize(frames, scale=0.8)
        assert out.shape == frames.shape

    def test_color_jitter_clips(self):
        """color_jitter harus clip ke [0, 1]."""
        frames = self._make_frames()
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.color_jitter(frames)
        assert out.min() >= -1e-7
        assert out.max() <= 1.0 + 1e-7

    def test_augment_with_flip_shape(self):
        """augment dengan was_keypoint_flipped=True harus mempertahankan shape."""
        frames = self._make_frames()
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.augment(frames, was_keypoint_flipped=True)
        assert out.shape == frames.shape

    def test_augment_without_flip_shape(self):
        """augment dengan was_keypoint_flipped=False harus mempertahankan shape."""
        frames = self._make_frames()
        aug = SpatialRGBAugmenter(seed=0)
        out = aug.augment(frames, was_keypoint_flipped=False)
        assert out.shape == frames.shape


# =============================================================================
# AugmentationPipeline — Unit Tests (Task 5.6)
# =============================================================================


class TestAugmentationPipeline:
    """Unit tests untuk AugmentationPipeline."""

    def _make_kp(self, T: int = 10) -> np.ndarray:
        return np.random.default_rng(42).uniform(-1.0, 1.0, (T, 543, 3)).astype(np.float32)

    def test_val_pipeline_is_identity(self):
        """Pipeline val harus mengembalikan salinan identik dari keypoints."""
        kp = self._make_kp()
        config = AugmentationConfig(enabled=True, split="val", seed=0)
        pipeline = AugmentationPipeline(config)
        result = pipeline(AugmentationSample(keypoints=kp.copy()))
        np.testing.assert_array_equal(result.keypoints, kp)

    def test_test_pipeline_is_identity(self):
        """Pipeline test harus mengembalikan salinan identik dari keypoints."""
        kp = self._make_kp()
        config = AugmentationConfig(enabled=True, split="test", seed=0)
        pipeline = AugmentationPipeline(config)
        result = pipeline(AugmentationSample(keypoints=kp.copy()))
        np.testing.assert_array_equal(result.keypoints, kp)

    def test_disabled_pipeline_is_identity(self):
        """Pipeline yang dinonaktifkan harus mengembalikan salinan identik."""
        kp = self._make_kp()
        config = AugmentationConfig(enabled=False, split="train", seed=0)
        pipeline = AugmentationPipeline(config)
        result = pipeline(AugmentationSample(keypoints=kp.copy()))
        np.testing.assert_array_equal(result.keypoints, kp)

    def test_train_pipeline_returns_same_shape(self):
        """Pipeline train harus mengembalikan keypoints dengan jumlah fitur yang sama (K, C)."""
        kp = self._make_kp(T=20)
        config = AugmentationConfig(enabled=True, split="train", seed=42)
        pipeline = AugmentationPipeline(config)
        result = pipeline(AugmentationSample(keypoints=kp.copy()))
        # Shape[1:] harus tetap [543, 3]
        assert result.keypoints.shape[1:] == kp.shape[1:]

    def test_val_pipeline_deterministic(self):
        """Pipeline val harus deterministik — dua panggilan harus menghasilkan output identik."""
        kp = self._make_kp()
        config = AugmentationConfig(enabled=True, split="val", seed=0)
        pipeline = AugmentationPipeline(config)
        r1 = pipeline(AugmentationSample(keypoints=kp.copy()))
        r2 = pipeline(AugmentationSample(keypoints=kp.copy()))
        np.testing.assert_array_equal(r1.keypoints, r2.keypoints)


# =============================================================================
# Property 8: Augmentation Non-Contamination (Task 5.7)
# =============================================================================


@settings(max_examples=100)
@given(
    split=st.sampled_from(["val", "test"]),
    enabled=st.booleans(),
    seed=st.integers(0, 9999),
)
def test_property_8_val_test_deterministic(split, enabled, seed):
    """
    Property 8: pipeline val/test harus deterministik (tidak ada transformasi acak).
    Memanggil dua kali dengan input yang sama harus menghasilkan output identik.

    Validates: Requirements 5.5, 5.6
    """
    kp = np.random.default_rng(seed).uniform(-1.0, 1.0, (10, 543, 3)).astype(np.float32)

    config = AugmentationConfig(enabled=enabled, split=split, seed=seed)
    pipeline = AugmentationPipeline(config)

    r1 = pipeline(AugmentationSample(keypoints=kp.copy()))
    r2 = pipeline(AugmentationSample(keypoints=kp.copy()))

    np.testing.assert_array_equal(
        r1.keypoints, r2.keypoints,
        err_msg=f"Pipeline {split} (enabled={enabled}) harus deterministik"
    )
