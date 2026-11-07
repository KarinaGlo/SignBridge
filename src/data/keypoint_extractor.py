"""
keypoint_extractor.py — Ekstraksi keypoint skeleton dari video menggunakan MediaPipe Holistic.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keypoint layout: [left_hand(21), right_hand(21), pose(33), face(468)] = 543
# ---------------------------------------------------------------------------
NUM_LEFT_HAND = 21
NUM_RIGHT_HAND = 21
NUM_POSE = 33
NUM_FACE = 468
NUM_KEYPOINTS = 543  # 21 + 21 + 33 + 468
INTERPOLATION_WINDOW = 5  # ±5 frames

# Slice indices for each group within the 543-keypoint array
_SLICE_LEFT_HAND = slice(0, 21)
_SLICE_RIGHT_HAND = slice(21, 42)
_SLICE_POSE = slice(42, 75)
_SLICE_FACE = slice(75, 543)

_GROUP_SLICES = {
    "left_hand": _SLICE_LEFT_HAND,
    "right_hand": _SLICE_RIGHT_HAND,
    "pose": _SLICE_POSE,
    "face": _SLICE_FACE,
}

_GROUP_SIZES = {
    "left_hand": NUM_LEFT_HAND,
    "right_hand": NUM_RIGHT_HAND,
    "pose": NUM_POSE,
    "face": NUM_FACE,
}


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class KeypointResult:
    keypoints: np.ndarray    # [T, 543, 3] float32
    confidence: np.ndarray   # [T, 543, 1] float32
    num_frames: int
    num_interpolated: int    # frames that had at least one group interpolated
    num_zero_padded: int     # frames that had at least one group zero-padded


@dataclass
class BatchExtractionReport:
    total: int
    succeeded: int
    failed: int
    results: list  # list of (video_path, KeypointResult or Exception)


# ---------------------------------------------------------------------------
# Helper: lazy import of mediapipe
# ---------------------------------------------------------------------------

def _get_mediapipe():
    """Lazy import of mediapipe to keep class definition importable without it."""
    try:
        import mediapipe as mp
        return mp
    except ImportError:
        raise ImportError(
            "mediapipe is required for KeypointExtractor. "
            "Install with: pip install mediapipe==0.10.11"
        )


def _get_cv2():
    """Lazy import of cv2 (opencv-python)."""
    try:
        import cv2
        return cv2
    except ImportError:
        raise ImportError(
            "opencv-python is required for KeypointExtractor. "
            "Install with: pip install opencv-python==4.9.0.80"
        )


# ---------------------------------------------------------------------------
# KeypointExtractor
# ---------------------------------------------------------------------------

class KeypointExtractor:
    """
    Ekstrak 543 keypoint MediaPipe Holistic per frame dari video.

    Keypoint layout in output array [T, 543, 3]:
      [0:21]    — left hand (21 keypoints)
      [21:42]   — right hand (21 keypoints)
      [42:75]   — pose (33 keypoints)
      [75:543]  — face (468 keypoints)

    Confidence array [T, 543, 1]:
      1.0 = detected, 0.5 = interpolated, 0.0 = missing/zero-padded

    Missing detection handling (Req 3.3, 3.4):
    - If a keypoint GROUP is missing on frame f:
      → Try linear interpolation from nearest valid frames within ±5 frames
      → If no valid frames in window: zero-pad and log warning
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

    # ------------------------------------------------------------------
    # Internal: landmark list → numpy row of shape [N, 3]
    # ------------------------------------------------------------------

    @staticmethod
    def _landmarks_to_array(landmark_list, n: int) -> Optional[np.ndarray]:
        """
        Convert a MediaPipe landmark list (NormalizedLandmarkList) to
        a float32 array of shape [n, 3] with coordinates remapped from
        [0, 1] → [-1, 1].  Returns None if landmark_list is None.
        """
        if landmark_list is None:
            return None
        coords = np.array(
            [[lm.x, lm.y, lm.z] for lm in landmark_list.landmark],
            dtype=np.float32,
        )
        # MediaPipe returns normalized [0, 1]; remap to [-1, 1]
        coords = coords * 2.0 - 1.0
        return coords  # [n, 3]

    # ------------------------------------------------------------------
    # Internal: process a single frame → (keypoints_row, detected_mask)
    # ------------------------------------------------------------------

    @staticmethod
    def _process_frame(
        holistic_results,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract one frame's keypoints from MediaPipe Holistic results.

        Returns
        -------
        kp_row : np.ndarray [543, 3] float32
            Keypoint coordinates. Zero where group was not detected.
        detected : np.ndarray [4] bool
            True for each group that was actually detected
            (order: left_hand, right_hand, pose, face).
        """
        kp_row = np.zeros((NUM_KEYPOINTS, 3), dtype=np.float32)
        detected = np.zeros(4, dtype=bool)

        groups = [
            ("left_hand",  holistic_results.left_hand_landmarks,  NUM_LEFT_HAND,  _SLICE_LEFT_HAND),
            ("right_hand", holistic_results.right_hand_landmarks, NUM_RIGHT_HAND, _SLICE_RIGHT_HAND),
            ("pose",       holistic_results.pose_landmarks,       NUM_POSE,       _SLICE_POSE),
            ("face",       holistic_results.face_landmarks,       NUM_FACE,       _SLICE_FACE),
        ]

        for idx, (name, lm_list, n, slc) in enumerate(groups):
            arr = KeypointExtractor._landmarks_to_array(lm_list, n)
            if arr is not None:
                kp_row[slc] = arr
                detected[idx] = True

        return kp_row, detected

    # ------------------------------------------------------------------
    # Internal: interpolation pass
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_interpolation(
        keypoints: np.ndarray,   # [T, 543, 3]
        confidence: np.ndarray,  # [T, 543, 1]
        frame_detected: np.ndarray,  # [T, 4] bool per group
    ) -> Tuple[int, int]:
        """
        Apply per-group interpolation in-place.

        Returns
        -------
        num_interpolated : int  frames where at least one group was interpolated
        num_zero_padded  : int  frames where at least one group was zero-padded
        """
        T = keypoints.shape[0]
        group_order = ["left_hand", "right_hand", "pose", "face"]
        frame_interpolated = np.zeros(T, dtype=bool)
        frame_zero_padded = np.zeros(T, dtype=bool)

        for g_idx, group_name in enumerate(group_order):
            slc = _GROUP_SLICES[group_name]
            n_kp = _GROUP_SIZES[group_name]

            for f in range(T):
                if frame_detected[f, g_idx]:
                    # Already have valid data; confidence already 1.0
                    continue

                # Search for nearest valid frames within ±INTERPOLATION_WINDOW
                left_t: Optional[int] = None
                right_t: Optional[int] = None

                for delta in range(1, INTERPOLATION_WINDOW + 1):
                    if left_t is None and (f - delta) >= 0 and frame_detected[f - delta, g_idx]:
                        left_t = f - delta
                    if right_t is None and (f + delta) < T and frame_detected[f + delta, g_idx]:
                        right_t = f + delta
                    if left_t is not None and right_t is not None:
                        break

                if left_t is not None and right_t is not None:
                    # Linear interpolation
                    t_ratio = (f - left_t) / (right_t - left_t)
                    keypoints[f, slc] = (
                        keypoints[left_t, slc]
                        + (keypoints[right_t, slc] - keypoints[left_t, slc]) * t_ratio
                    )
                    confidence[f, slc] = 0.5
                    frame_interpolated[f] = True

                elif left_t is not None:
                    # Nearest-neighbor from left
                    keypoints[f, slc] = keypoints[left_t, slc]
                    confidence[f, slc] = 0.5
                    frame_interpolated[f] = True

                elif right_t is not None:
                    # Nearest-neighbor from right
                    keypoints[f, slc] = keypoints[right_t, slc]
                    confidence[f, slc] = 0.5
                    frame_interpolated[f] = True

                else:
                    # No valid frames in ±5 window → zero-pad
                    keypoints[f, slc] = 0.0
                    confidence[f, slc] = 0.0
                    frame_zero_padded[f] = True
                    logger.warning(
                        "Frame %d: group '%s' zero-padded (%d keypoints)",
                        f, group_name, n_kp,
                    )

        num_interpolated = int(frame_interpolated.sum())
        num_zero_padded = int(frame_zero_padded.sum())
        return num_interpolated, num_zero_padded

    # ------------------------------------------------------------------
    # Public: extract_video
    # ------------------------------------------------------------------

    def extract_video(self, video_path: Path) -> KeypointResult:
        """
        Ekstrak keypoint dari semua frame video.

        Returns KeypointResult with:
        - keypoints: [T, 543, 3] float32, coordinates ∈ [-1, 1] (normalized)
        - confidence: [T, 543, 1] float32
        - Interpolation applied for missing frames in ±5 window
        - Zero-padding with log warning if no valid frames in window

        Raises
        ------
        FileNotFoundError
            If video_path does not exist.
        RuntimeError
            If the video cannot be opened by OpenCV.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video tidak ditemukan: {video_path}")

        mp = _get_mediapipe()
        cv2 = _get_cv2()

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Tidak dapat membuka video: {video_path}")

        raw_kp: list[np.ndarray] = []
        frame_detected_list: list[np.ndarray] = []

        try:
            with mp.solutions.holistic.Holistic(
                static_image_mode=self.static_image_mode,
                model_complexity=self.model_complexity,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            ) as holistic:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(rgb_frame)
                    kp_row, detected = self._process_frame(results)
                    raw_kp.append(kp_row)
                    frame_detected_list.append(detected)
        finally:
            cap.release()

        if not raw_kp:
            # Edge case: empty video
            keypoints = np.zeros((0, NUM_KEYPOINTS, 3), dtype=np.float32)
            confidence = np.zeros((0, NUM_KEYPOINTS, 1), dtype=np.float32)
            return KeypointResult(
                keypoints=keypoints,
                confidence=confidence,
                num_frames=0,
                num_interpolated=0,
                num_zero_padded=0,
            )

        T = len(raw_kp)
        keypoints = np.stack(raw_kp, axis=0)  # [T, 543, 3]
        frame_detected = np.stack(frame_detected_list, axis=0)  # [T, 4]

        # Confidence: 1.0 where detected, 0.0 initially for missing
        confidence = np.zeros((T, NUM_KEYPOINTS, 1), dtype=np.float32)
        group_order = ["left_hand", "right_hand", "pose", "face"]
        for g_idx, group_name in enumerate(group_order):
            slc = _GROUP_SLICES[group_name]
            detected_frames = frame_detected[:, g_idx]  # [T] bool
            confidence[detected_frames, slc] = 1.0

        # Interpolation pass
        num_interpolated, num_zero_padded = self._apply_interpolation(
            keypoints, confidence, frame_detected
        )

        return KeypointResult(
            keypoints=keypoints,
            confidence=confidence,
            num_frames=T,
            num_interpolated=num_interpolated,
            num_zero_padded=num_zero_padded,
        )

    # ------------------------------------------------------------------
    # Public: batch_extract
    # ------------------------------------------------------------------

    def batch_extract(
        self,
        video_paths: List[Path],
        output_dir: Path,
        num_workers: int = 4,
    ) -> BatchExtractionReport:
        """
        Batch processing with parallelism (ThreadPoolExecutor) and tqdm progress bar.

        For each video:
        - Extract keypoints
        - Save .npy files to output_dir/<video_stem>.npy and <video_stem>_conf.npy

        Requirements: 3.5
        """
        try:
            from tqdm import tqdm
        except ImportError:
            # Fallback: no progress bar
            class tqdm:  # type: ignore[no-redef]
                def __init__(self, iterable=None, total=None, **kwargs):
                    self._iterable = iterable
                    self.total = total

                def __iter__(self):
                    return iter(self._iterable or [])

                def update(self, n=1):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        succeeded = 0
        failed = 0

        def _extract_one(vp: Path):
            result = self.extract_video(vp)
            # Save keypoints
            np.save(output_dir / f"{vp.stem}.npy", result.keypoints)
            np.save(output_dir / f"{vp.stem}_conf.npy", result.confidence)
            return result

        with tqdm(total=len(video_paths), desc="Extracting keypoints") as pbar:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_path = {
                    executor.submit(_extract_one, Path(vp)): Path(vp)
                    for vp in video_paths
                }
                for future in as_completed(future_to_path):
                    vp = future_to_path[future]
                    try:
                        result = future.result()
                        results.append((vp, result))
                        succeeded += 1
                    except Exception as exc:
                        logger.error("Gagal mengekstrak %s: %s", vp, exc)
                        results.append((vp, exc))
                        failed += 1
                    pbar.update(1)

        return BatchExtractionReport(
            total=len(video_paths),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )


_apply_interpolation_standalone = KeypointExtractor._apply_interpolation

