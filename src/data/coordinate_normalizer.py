"""
coordinate_normalizer.py — Normalize keypoint coordinates to [-1, 1].
Requirements: 4.4
"""
from typing import Optional
import numpy as np

# Pose keypoints are at indices [42:75] in the 543-keypoint array
POSE_SLICE = slice(42, 75)


class CoordinateNormalizer:
    """
    Normalize keypoint coordinates to [-1, 1] relative to body bounding box.
    Requirements: 4.4
    """

    def normalize_frame(
        self,
        keypoints: np.ndarray,          # [N, 3] float32, raw coords ∈ [0,1] from MediaPipe
        prev_bbox: Optional[tuple] = None,  # fallback (x_min, y_min, x_max, y_max)
    ) -> tuple[np.ndarray, tuple]:
        """
        Normalize a single frame's keypoints using the body bounding box.

        Bounding box computed from pose keypoints (indices 42:75).
        x coords = keypoints[42:75, 0], y coords = keypoints[42:75, 1]

        If bbox is degenerate (width==0 or height==0): use prev_bbox.
        If prev_bbox is also None/degenerate: use full image [0,1]→[-1,1] mapping.

        Output coords = (input - center) / half_extent → maps bbox to [-1, 1].

        Returns: (normalized_array [N, 3], used_bbox)
        """
        keypoints = keypoints.astype(np.float32)
        pose_kp = keypoints[POSE_SLICE]  # [33, 3]

        x_min = float(pose_kp[:, 0].min())
        x_max = float(pose_kp[:, 0].max())
        y_min = float(pose_kp[:, 1].min())
        y_max = float(pose_kp[:, 1].max())

        half_w = (x_max - x_min) / 2.0
        half_h = (y_max - y_min) / 2.0

        # Check if current bbox is degenerate
        current_bbox = (x_min, y_min, x_max, y_max)
        bbox_degenerate = (half_w == 0.0 or half_h == 0.0)

        if bbox_degenerate:
            # Try to use prev_bbox
            if prev_bbox is not None:
                pb_x_min, pb_y_min, pb_x_max, pb_y_max = prev_bbox
                pb_half_w = (pb_x_max - pb_x_min) / 2.0
                pb_half_h = (pb_y_max - pb_y_min) / 2.0
                if pb_half_w > 0.0 and pb_half_h > 0.0:
                    x_min, y_min, x_max, y_max = pb_x_min, pb_y_min, pb_x_max, pb_y_max
                    half_w = pb_half_w
                    half_h = pb_half_h
                    current_bbox = prev_bbox
                else:
                    # Both degenerate → use full image [0,1]
                    x_min, y_min, x_max, y_max = 0.0, 0.0, 1.0, 1.0
                    half_w, half_h = 0.5, 0.5
                    current_bbox = (0.0, 0.0, 1.0, 1.0)
            else:
                # No prev_bbox → use full image [0,1]
                x_min, y_min, x_max, y_max = 0.0, 0.0, 1.0, 1.0
                half_w, half_h = 0.5, 0.5
                current_bbox = (0.0, 0.0, 1.0, 1.0)

        cx = (x_min + x_max) / 2.0
        cy = (y_min + y_max) / 2.0

        normalized = keypoints.copy()
        # x: (kp_x - cx) / half_w
        normalized[:, 0] = (keypoints[:, 0] - cx) / half_w
        # y: (kp_y - cy) / half_h
        normalized[:, 1] = (keypoints[:, 1] - cy) / half_h
        # z: keep as-is

        # Clip to [-1, 1] for robustness
        normalized[:, 0] = np.clip(normalized[:, 0], -1.0, 1.0)
        normalized[:, 1] = np.clip(normalized[:, 1], -1.0, 1.0)

        return normalized, current_bbox

    def normalize_sequence(self, keypoints: np.ndarray) -> np.ndarray:
        """
        Normalize all frames in [T, N, 3], using previous valid bbox as fallback.
        Returns [T, N, 3] float32.
        """
        T = keypoints.shape[0]
        result = np.empty_like(keypoints, dtype=np.float32)
        prev_bbox: Optional[tuple] = None

        for t in range(T):
            frame = keypoints[t]  # [N, 3]
            normalized_frame, used_bbox = self.normalize_frame(frame, prev_bbox=prev_bbox)
            result[t] = normalized_frame
            # Update prev_bbox only if not a degenerate fallback
            pose_kp = frame[POSE_SLICE]
            half_w = (pose_kp[:, 0].max() - pose_kp[:, 0].min()) / 2.0
            half_h = (pose_kp[:, 1].max() - pose_kp[:, 1].min()) / 2.0
            if half_w > 0.0 and half_h > 0.0:
                prev_bbox = used_bbox

        return result
