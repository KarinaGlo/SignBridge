"""
test_keypoint_extractor.py — Unit tests untuk KeypointExtractor.

Karena MediaPipe membutuhkan GPU/kamera dan video nyata, semua tes ini
menggunakan mock untuk MediaPipe dan OpenCV supaya bisa berjalan di CI
tanpa hardware khusus.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
"""
from __future__ import annotations

import logging
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers — build fake MediaPipe landmark objects
# ---------------------------------------------------------------------------

def _make_landmark(x: float, y: float, z: float = 0.0):
    """Return a simple object with .x .y .z attributes."""
    lm = MagicMock()
    lm.x = x
    lm.y = y
    lm.z = z
    return lm


def _make_landmark_list(coords: list[tuple]) -> MagicMock:
    """
    Build a fake NormalizedLandmarkList from a list of (x, y, z) tuples.
    coords must have exactly the right count for the group.
    """
    lm_list = MagicMock()
    lm_list.landmark = [_make_landmark(*c) for c in coords]
    return lm_list


def _make_holistic_results(
    left_hand=True,
    right_hand=True,
    pose=True,
    face=True,
    value: float = 0.5,   # landmark coordinate value (in [0,1])
):
    """
    Return a fake MediaPipe Holistic results object.
    If a group flag is False, that landmark list is None (not detected).
    """
    results = MagicMock()

    def _lm_list(n):
        return _make_landmark_list([(value, value, value)] * n)

    results.left_hand_landmarks  = _lm_list(21) if left_hand  else None
    results.right_hand_landmarks = _lm_list(21) if right_hand else None
    results.pose_landmarks       = _lm_list(33) if pose       else None
    results.face_landmarks       = _lm_list(468) if face      else None
    return results


# ---------------------------------------------------------------------------
# Fixture: build a fake video that yields N synthetic frames
# ---------------------------------------------------------------------------

def _make_fake_cap(num_frames: int, frame_shape=(480, 640, 3)):
    """
    Build a mock cv2.VideoCapture that yields num_frames BGR frames then stops.
    """
    cap = MagicMock()
    # Create simple BGR frames
    frame = np.zeros(frame_shape, dtype=np.uint8)
    call_count = [0]

    def read_side_effect():
        if call_count[0] < num_frames:
            call_count[0] += 1
            return True, frame.copy()
        return False, None

    cap.isOpened.return_value = True
    cap.read.side_effect = read_side_effect
    cap.release = MagicMock()
    return cap


# ---------------------------------------------------------------------------
# Context managers helpers
# ---------------------------------------------------------------------------

def _patch_mediapipe_and_cv2(num_frames: int, results_per_frame=None):
    """
    Returns two context-manager patches:
      1. mediapipe mock
      2. cv2 mock
    Caller is responsible for combining them with nested `with` statements.
    """
    if results_per_frame is None:
        results_per_frame = [_make_holistic_results()] * num_frames

    # ---------- MediaPipe mock ----------
    mp_mock = MagicMock()

    holistic_instance = MagicMock()
    holistic_instance.__enter__ = MagicMock(return_value=holistic_instance)
    holistic_instance.__exit__ = MagicMock(return_value=False)

    results_iter = iter(results_per_frame)

    def process_side_effect(rgb_frame):
        return next(results_iter)

    holistic_instance.process.side_effect = process_side_effect
    mp_mock.solutions.holistic.Holistic.return_value = holistic_instance

    # ---------- cv2 mock ----------
    cv2_mock = MagicMock()
    fake_cap = _make_fake_cap(num_frames)
    cv2_mock.VideoCapture.return_value = fake_cap
    cv2_mock.cvtColor.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2_mock.COLOR_BGR2RGB = 4  # any constant

    return mp_mock, cv2_mock


# ---------------------------------------------------------------------------
# Import extractor (after helpers are defined)
# ---------------------------------------------------------------------------

from src.data.keypoint_extractor import (
    KeypointExtractor,
    KeypointResult,
    BatchExtractionReport,
    NUM_KEYPOINTS,
    NUM_LEFT_HAND,
    NUM_RIGHT_HAND,
    NUM_POSE,
    NUM_FACE,
    INTERPOLATION_WINDOW,
    _apply_interpolation_standalone,  # tested directly where possible
)


# ---------------------------------------------------------------------------
# Test 1: output shape correct
# ---------------------------------------------------------------------------

class TestOutputShape:

    def test_output_shape_correct(self, tmp_path):
        """
        Mock holistic returning 10 frames — output must be [10, 543, 3] / [10, 543, 1].
        """
        num_frames = 10
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        assert isinstance(result, KeypointResult)
        assert result.keypoints.shape == (num_frames, 543, 3)
        assert result.confidence.shape == (num_frames, 543, 1)
        assert result.keypoints.dtype == np.float32
        assert result.confidence.dtype == np.float32
        assert result.num_frames == num_frames


# ---------------------------------------------------------------------------
# Test 2: coordinates remapped to [-1, 1]
# ---------------------------------------------------------------------------

class TestCoordinateRemapping:

    def test_keypoints_remapped_to_minus1_1(self, tmp_path):
        """
        MediaPipe yields landmarks at value=0.75 → after *2-1 = 0.5.
        """
        num_frames = 3
        raw_val = 0.75
        expected_val = raw_val * 2.0 - 1.0  # 0.5

        results = [_make_holistic_results(value=raw_val)] * num_frames
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        # All coords should be expected_val (within float tolerance)
        assert result.keypoints.shape == (num_frames, 543, 3)
        np.testing.assert_allclose(result.keypoints, expected_val, atol=1e-5)

    def test_zero_coordinate_remaps_to_minus1(self, tmp_path):
        """MediaPipe value 0.0 → -1.0"""
        num_frames = 1
        results = [_make_holistic_results(value=0.0)]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        np.testing.assert_allclose(result.keypoints, -1.0, atol=1e-5)

    def test_one_coordinate_remaps_to_plus1(self, tmp_path):
        """MediaPipe value 1.0 → +1.0"""
        num_frames = 1
        results = [_make_holistic_results(value=1.0)]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        np.testing.assert_allclose(result.keypoints, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 3: interpolation fills missing frame
# ---------------------------------------------------------------------------

class TestInterpolation:

    def _make_results_with_missing_hand(self, num_frames: int, missing_frame: int):
        """
        Build per-frame results where left_hand is missing on `missing_frame`
        but present (at value=0.0) on frame 0 and (value=1.0) on frame num_frames-1.
        """
        results = []
        for f in range(num_frames):
            if f == missing_frame:
                r = _make_holistic_results(left_hand=False, value=0.0)
            elif f < missing_frame:
                r = _make_holistic_results(left_hand=True, value=0.0)
            else:
                r = _make_holistic_results(left_hand=True, value=1.0)
            results.append(r)
        return results

    def test_interpolation_fills_missing_frame(self, tmp_path):
        """
        Frame 5 missing, valid at frame 4 (val=0.0) and frame 6 (val=1.0).
        After remapping: 0.0→-1.0, 1.0→+1.0.
        Interpolated frame 5 = midpoint = 0.0.
        """
        num_frames = 11
        missing = 5
        results = self._make_results_with_missing_hand(num_frames, missing)
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        # Left hand slice [0:21]
        left_hand_frame5 = result.keypoints[missing, 0:21, :]
        # Expected: midpoint of -1.0 and +1.0 = 0.0
        np.testing.assert_allclose(left_hand_frame5, 0.0, atol=1e-5)

        # Confidence for that frame/group should be 0.5
        left_hand_conf5 = result.confidence[missing, 0:21, 0]
        np.testing.assert_allclose(left_hand_conf5, 0.5, atol=1e-5)

    def test_interpolation_uses_nearest_when_only_one_side(self, tmp_path):
        """
        Frame 0 missing (no left neighbor), right neighbor at frame 2.
        Should use nearest-neighbor (right side).
        """
        num_frames = 5
        # Frame 0: left_hand missing; frames 1..4: left_hand present at value=0.6
        results = []
        for f in range(num_frames):
            if f == 0:
                results.append(_make_holistic_results(left_hand=False, value=0.6))
            else:
                results.append(_make_holistic_results(left_hand=True, value=0.6))

        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        expected = 0.6 * 2.0 - 1.0  # = 0.2
        np.testing.assert_allclose(result.keypoints[0, 0:21, :], expected, atol=1e-5)
        np.testing.assert_allclose(result.confidence[0, 0:21, 0], 0.5, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 4: zero-padding when no valid neighbors
# ---------------------------------------------------------------------------

class TestZeroPadding:

    def test_zero_padding_when_no_valid_neighbors(self, tmp_path, caplog):
        """
        If only frame 0 exists and left_hand is missing → no neighbors in ±5 → zero-pad.
        """
        num_frames = 1
        results = [_make_holistic_results(left_hand=False)]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with caplog.at_level(logging.WARNING, logger="src.data.keypoint_extractor"):
            with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
                with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                    extractor = KeypointExtractor()
                    result = extractor.extract_video(video_path)

        # Left hand should be zero-padded
        np.testing.assert_allclose(result.keypoints[0, 0:21, :], 0.0, atol=1e-5)
        # Confidence = 0.0
        np.testing.assert_allclose(result.confidence[0, 0:21, 0], 0.0, atol=1e-5)
        # A warning should have been logged
        assert result.num_zero_padded >= 1
        assert any("zero-padded" in rec.message.lower() for rec in caplog.records)

    def test_zero_padding_when_all_frames_missing_for_group(self, tmp_path, caplog):
        """
        7 frames, left_hand never detected (window 5 < 7 for middle frames too).
        Frames 0..4: no right neighbor within ±5, frames 6: no left neighbor within ±5 …
        Actually with 7 frames frames 0 and 6 have no neighbor on one side,
        but all 7 frames are missing → no valid neighbor anywhere → all zero-padded.
        """
        num_frames = 7
        results = [_make_holistic_results(left_hand=False)] * num_frames
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with caplog.at_level(logging.WARNING, logger="src.data.keypoint_extractor"):
            with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
                with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                    extractor = KeypointExtractor()
                    result = extractor.extract_video(video_path)

        np.testing.assert_allclose(result.keypoints[:, 0:21, :], 0.0, atol=1e-5)
        np.testing.assert_allclose(result.confidence[:, 0:21, 0], 0.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 5: confidence values (detected=1.0, interpolated=0.5, zero-padded=0.0)
# ---------------------------------------------------------------------------

class TestConfidenceValues:

    def test_confidence_values(self, tmp_path):
        """
        3-frame video:
          Frame 0: left_hand detected (val=0.2)
          Frame 1: left_hand missing  (neighbors: frame 0 at left, frame 2 at right)
          Frame 2: left_hand detected (val=0.8)
        Expected confidence: [1.0, 0.5, 1.0] for left_hand group.
        """
        results = [
            _make_holistic_results(left_hand=True,  value=0.2),
            _make_holistic_results(left_hand=False, value=0.2),
            _make_holistic_results(left_hand=True,  value=0.8),
        ]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(3, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        lh_conf = result.confidence[:, 0:21, 0]
        np.testing.assert_allclose(lh_conf[0], 1.0, atol=1e-5)
        np.testing.assert_allclose(lh_conf[1], 0.5, atol=1e-5)
        np.testing.assert_allclose(lh_conf[2], 1.0, atol=1e-5)

    def test_confidence_zero_padded_is_0(self, tmp_path):
        """Single frame with missing left_hand → confidence 0.0."""
        results = [_make_holistic_results(left_hand=False)]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(1, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        np.testing.assert_allclose(result.confidence[0, 0:21, 0], 0.0, atol=1e-5)

    def test_confidence_all_groups_detected_is_1(self, tmp_path):
        """All groups detected → confidence 1.0 everywhere."""
        num_frames = 5
        results = [_make_holistic_results()] * num_frames
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        np.testing.assert_allclose(result.confidence, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 6: FileNotFoundError raised for missing video
# ---------------------------------------------------------------------------

class TestFileNotFound:

    def test_filenotfound_raised(self, tmp_path):
        """extract_video must raise FileNotFoundError if path does not exist."""
        extractor = KeypointExtractor()
        with pytest.raises(FileNotFoundError):
            extractor.extract_video(tmp_path / "nonexistent_video.mp4")

    def test_runtimeerror_raised_when_video_not_openable(self, tmp_path):
        """extract_video must raise RuntimeError if cv2 can't open the file."""
        video_path = tmp_path / "corrupt.mp4"
        video_path.touch()

        mp_mock = MagicMock()
        cv2_mock = MagicMock()
        cap_mock = MagicMock()
        cap_mock.isOpened.return_value = False
        cv2_mock.VideoCapture.return_value = cap_mock

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                with pytest.raises(RuntimeError):
                    extractor.extract_video(video_path)


# ---------------------------------------------------------------------------
# Test 7: batch_extract saves .npy files
# ---------------------------------------------------------------------------

class TestBatchExtract:

    def _mock_extract_video(self, num_frames=5):
        """Return a KeypointResult with correct shapes for mocking."""
        kp = np.zeros((num_frames, 543, 3), dtype=np.float32)
        conf = np.ones((num_frames, 543, 1), dtype=np.float32)
        return KeypointResult(
            keypoints=kp,
            confidence=conf,
            num_frames=num_frames,
            num_interpolated=0,
            num_zero_padded=0,
        )

    def test_batch_extract_saves_npy_files(self, tmp_path):
        """batch_extract must save <stem>.npy for each video."""
        video_paths = [tmp_path / f"video_{i}.mp4" for i in range(3)]
        for vp in video_paths:
            vp.touch()

        output_dir = tmp_path / "keypoints"
        extractor = KeypointExtractor()

        mock_result = self._mock_extract_video()
        with patch.object(extractor, "extract_video", return_value=mock_result):
            report = extractor.batch_extract(video_paths, output_dir)

        assert report.total == 3
        assert report.succeeded == 3
        assert report.failed == 0

        for vp in video_paths:
            expected_npy = output_dir / f"{vp.stem}.npy"
            assert expected_npy.exists(), f"Expected {expected_npy} to exist"

    def test_batch_extract_confidence_files_saved(self, tmp_path):
        """batch_extract must save <stem>_conf.npy for each video."""
        video_paths = [tmp_path / f"clip_{i}.mp4" for i in range(2)]
        for vp in video_paths:
            vp.touch()

        output_dir = tmp_path / "keypoints"
        extractor = KeypointExtractor()

        mock_result = self._mock_extract_video()
        with patch.object(extractor, "extract_video", return_value=mock_result):
            report = extractor.batch_extract(video_paths, output_dir)

        for vp in video_paths:
            expected_conf = output_dir / f"{vp.stem}_conf.npy"
            assert expected_conf.exists(), f"Expected {expected_conf} to exist"

    def test_batch_extract_npy_content_correct_shape(self, tmp_path):
        """Saved .npy files must have correct array shapes."""
        video_paths = [tmp_path / "myvideo.mp4"]
        video_paths[0].touch()

        output_dir = tmp_path / "out"
        extractor = KeypointExtractor()

        mock_result = self._mock_extract_video(num_frames=7)
        with patch.object(extractor, "extract_video", return_value=mock_result):
            extractor.batch_extract(video_paths, output_dir)

        kp_loaded = np.load(output_dir / "myvideo.npy")
        conf_loaded = np.load(output_dir / "myvideo_conf.npy")

        assert kp_loaded.shape == (7, 543, 3)
        assert conf_loaded.shape == (7, 543, 1)

    def test_batch_extract_handles_failure_gracefully(self, tmp_path):
        """If extract_video raises, batch_extract records it as failed."""
        video_paths = [tmp_path / "ok.mp4", tmp_path / "bad.mp4"]
        for vp in video_paths:
            vp.touch()

        output_dir = tmp_path / "out"
        extractor = KeypointExtractor()

        good_result = self._mock_extract_video()

        def side_effect(vp):
            if "bad" in vp.name:
                raise RuntimeError("simulated failure")
            return good_result

        with patch.object(extractor, "extract_video", side_effect=side_effect):
            report = extractor.batch_extract(video_paths, output_dir)

        assert report.total == 2
        assert report.succeeded == 1
        assert report.failed == 1

    def test_batch_extract_creates_output_dir(self, tmp_path):
        """batch_extract must create output_dir if it doesn't exist."""
        video_paths = [tmp_path / "vid.mp4"]
        video_paths[0].touch()

        output_dir = tmp_path / "new_dir" / "nested"
        extractor = KeypointExtractor()

        mock_result = self._mock_extract_video()
        with patch.object(extractor, "extract_video", return_value=mock_result):
            extractor.batch_extract(video_paths, output_dir)

        assert output_dir.exists()

    def test_batch_extract_report_structure(self, tmp_path):
        """BatchExtractionReport must have correct fields."""
        video_paths = [tmp_path / f"v{i}.mp4" for i in range(4)]
        for vp in video_paths:
            vp.touch()

        output_dir = tmp_path / "out"
        extractor = KeypointExtractor()

        mock_result = self._mock_extract_video()
        with patch.object(extractor, "extract_video", return_value=mock_result):
            report = extractor.batch_extract(video_paths, output_dir)

        assert isinstance(report, BatchExtractionReport)
        assert report.total == 4
        assert len(report.results) == 4
        # Each entry is (path, KeypointResult or Exception)
        for path, res in report.results:
            assert isinstance(path, Path)
            assert isinstance(res, KeypointResult)


# ---------------------------------------------------------------------------
# Test: KeypointResult counting (num_interpolated, num_zero_padded)
# ---------------------------------------------------------------------------

class TestResultCounting:

    def test_num_interpolated_counted_correctly(self, tmp_path):
        """
        With 3 frames, left_hand missing on frame 1 but valid on 0 and 2:
        num_interpolated should be >= 1 (frame 1 has at least one group interpolated).
        """
        results = [
            _make_holistic_results(left_hand=True,  value=0.2),
            _make_holistic_results(left_hand=False, value=0.2),
            _make_holistic_results(left_hand=True,  value=0.8),
        ]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(3, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        assert result.num_interpolated >= 1

    def test_num_zero_padded_counted_correctly(self, tmp_path):
        """
        Single frame, left_hand missing → no neighbor → zero-padded.
        num_zero_padded should be 1.
        """
        results = [_make_holistic_results(left_hand=False)]
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(1, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        assert result.num_zero_padded >= 1

    def test_all_detected_no_interpolation_no_zero_padding(self, tmp_path):
        """All groups always detected → num_interpolated=0, num_zero_padded=0."""
        num_frames = 8
        results = [_make_holistic_results()] * num_frames
        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        assert result.num_interpolated == 0
        assert result.num_zero_padded == 0


# ---------------------------------------------------------------------------
# Test: interpolation window boundary (exactly ±5 is valid, ±6 is not)
# ---------------------------------------------------------------------------

class TestInterpolationWindow:

    def test_interpolation_exactly_at_window_boundary(self, tmp_path):
        """
        Valid frames at distance exactly 5: should interpolate.
        missing_frame=5, valid at 0 and 10 (distance 5 each).
        """
        num_frames = 11  # frames 0..10
        results = []
        for f in range(num_frames):
            if f == 5:
                results.append(_make_holistic_results(left_hand=False, value=0.5))
            elif f < 5:
                results.append(_make_holistic_results(left_hand=True, value=0.0))
            else:
                results.append(_make_holistic_results(left_hand=True, value=1.0))

        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        # Frame 5 should be interpolated (confidence 0.5)
        np.testing.assert_allclose(result.confidence[5, 0:21, 0], 0.5, atol=1e-5)

    def test_no_interpolation_beyond_window(self, tmp_path):
        """
        Valid frames at distance > 5: should zero-pad the missing frame.
        13 frames, frame 6 missing, valid at frames 0 and 12 (both > 5 away).
        """
        num_frames = 13  # frames 0..12
        results = []
        for f in range(num_frames):
            if f == 6:
                results.append(_make_holistic_results(left_hand=False, value=0.5))
            elif f == 0:
                results.append(_make_holistic_results(left_hand=True, value=0.2))
            elif f == 12:
                results.append(_make_holistic_results(left_hand=True, value=0.8))
            else:
                results.append(_make_holistic_results(left_hand=False, value=0.5))

        mp_mock, cv2_mock = _patch_mediapipe_and_cv2(num_frames, results)

        video_path = tmp_path / "dummy.mp4"
        video_path.touch()

        with patch("src.data.keypoint_extractor._get_mediapipe", return_value=mp_mock):
            with patch("src.data.keypoint_extractor._get_cv2", return_value=cv2_mock):
                extractor = KeypointExtractor()
                result = extractor.extract_video(video_path)

        # Frame 6 should be zero-padded
        np.testing.assert_allclose(result.keypoints[6, 0:21, :], 0.0, atol=1e-5)
        np.testing.assert_allclose(result.confidence[6, 0:21, 0], 0.0, atol=1e-5)
