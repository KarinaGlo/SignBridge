"""
constants.py — Contract 1: 86-node keypoint layout, gloss labels, and manifest columns.

WARNING: Contract interface between Farrel (Data), Jonnathan (Model), and Gloria (Eval/Web).
Do NOT change node ordering or tensor dimensions without team discussion.

86-Node Layout (from MediaPipe Holistic 543 landmarks):
  - Indices [0:9]   (9 nodes)  : Upper-body pose (nose, L/R shoulder, L/R elbow, L/R wrist, L/R hip)
  - Indices [9:30]  (21 nodes) : Left hand landmarks (0..20)
  - Indices [30:51] (21 nodes) : Right hand landmarks (0..20)  <-- Contract: kp[:, 30:51] = right hand
  - Indices [51:86] (35 nodes) : Selective face landmarks (lips, eyebrows, eyes, nose contour)

Total = 9 + 21 + 21 + 35 = 86 nodes, 3 coordinates (x, y, z).
ONNX Video Input:  float32 [1, 64, 86, 3]
ONNX Video Output: float32 [1, 32]
ONNX Image Input:  float32 [1, 3, 224, 224]
ONNX Image Output: float32 [1, 26]
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np

# ---------------------------------------------------------------------------
# Core Tensor Dimensions (Contract 1 & Contract 2)
# ---------------------------------------------------------------------------

NUM_KEYPOINTS: int = 86
NUM_NODES: int = 86
NUM_COORDS: int = 3
T_MAX: int = 64
SEQ_LEN: int = 64
RGB_NUM_FRAMES: int = 16
RGB_NUM_TOKENS: int = 8
RGB_TOKEN_DIM: int = 768
IMAGE_SIZE: int = 224

# ImageNet normalization constants (Contract 5)
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)

# ---------------------------------------------------------------------------
# MediaPipe Holistic Source Indices -> 86 Target Nodes
# ---------------------------------------------------------------------------

# 9 upper-body pose landmarks from MediaPipe Pose (33 landmarks):
# 0: nose, 11: left_shoulder, 12: right_shoulder, 13: left_elbow, 14: right_elbow,
# 15: left_wrist, 16: right_wrist, 23: left_hip, 24: right_hip
MP_POSE_INDICES: List[int] = [0, 11, 12, 13, 14, 15, 16, 23, 24]

# 21 hand landmarks (all 0..20 for both left and right hands)
MP_HAND_INDICES: List[int] = list(range(21))

# 35 selective facial landmarks from MediaPipe FaceMesh (468 landmarks)
# Capturing lips (outer + inner), left/right eyebrows, left/right eye corners/lids, nose tip/bridge
MP_FACE_INDICES: List[int] = [
    # Lips (14 points)
    0, 13, 14, 17, 37, 39, 40, 61, 78, 80, 81, 82, 84, 87,
    # Right lip / mouth corner (4 points)
    88, 91, 95, 146,
    # Left & right mouth corners / upper lip (2 points)
    178, 291,
    # Left eyebrow (4 points)
    70, 63, 105, 66,
    # Right eyebrow (4 points)
    300, 293, 334, 296,
    # Left eye (3 points)
    33, 133, 159,
    # Right eye (3 points)
    362, 263, 386,
    # Nose tip (1 point)
    1,
]
assert len(MP_POSE_INDICES) == 9
assert len(MP_HAND_INDICES) == 21
assert len(MP_FACE_INDICES) == 35
assert len(MP_POSE_INDICES) + 2 * len(MP_HAND_INDICES) + len(MP_FACE_INDICES) == NUM_KEYPOINTS

# ---------------------------------------------------------------------------
# Slice Ranges within the 86-Node Array
# ---------------------------------------------------------------------------

POSE_START: int = 0
POSE_END: int = 9
SLICE_POSE = slice(POSE_START, POSE_END)          # [0:9]   (9 nodes)

LEFT_HAND_START: int = 9
LEFT_HAND_END: int = 30
SLICE_LEFT_HAND = slice(LEFT_HAND_START, LEFT_HAND_END)   # [9:30]  (21 nodes)

RIGHT_HAND_START: int = 30
RIGHT_HAND_END: int = 51
SLICE_RIGHT_HAND = slice(RIGHT_HAND_START, RIGHT_HAND_END) # [30:51] (21 nodes)

FACE_START: int = 51
FACE_END: int = 86
SLICE_FACE = slice(FACE_START, FACE_END)          # [51:86] (35 nodes)

# Key landmark indices in the 86-node array:
NOSE_IDX: int = 0
L_SHOULDER_IDX: int = 1
R_SHOULDER_IDX: int = 2
L_ELBOW_IDX: int = 3
R_ELBOW_IDX: int = 4
L_WRIST_POSE_IDX: int = 5
R_WRIST_POSE_IDX: int = 6
L_HIP_IDX: int = 7
R_HIP_IDX: int = 8

# Left-Right symmetry index pairs for horizontal mirroring (augment.py)
POSE_FLIP_PAIRS: List[Tuple[int, int]] = [
    (L_SHOULDER_IDX, R_SHOULDER_IDX),
    (L_ELBOW_IDX, R_ELBOW_IDX),
    (L_WRIST_POSE_IDX, R_WRIST_POSE_IDX),
    (L_HIP_IDX, R_HIP_IDX),
]

HAND_FLIP_PAIRS: List[Tuple[int, int]] = [
    (LEFT_HAND_START + i, RIGHT_HAND_START + i) for i in range(21)
]

# Symmetric face pairs within [51:86]
FACE_FLIP_PAIRS: List[Tuple[int, int]] = [
    (51 + 7, 51 + 19),   # mouth corners 61 <-> 291
    (51 + 20, 51 + 24),  # eyebrow 70 <-> 300
    (51 + 21, 51 + 25),  # eyebrow 63 <-> 293
    (51 + 22, 51 + 26),  # eyebrow 105 <-> 334
    (51 + 23, 51 + 27),  # eyebrow 66 <-> 296
    (51 + 28, 51 + 31),  # eye outer 33 <-> 362
    (51 + 29, 51 + 32),  # eye inner 133 <-> 263
    (51 + 30, 51 + 33),  # eye upper 159 <-> 386
]

ALL_FLIP_PAIRS: List[Tuple[int, int]] = POSE_FLIP_PAIRS + HAND_FLIP_PAIRS + FACE_FLIP_PAIRS

# ---------------------------------------------------------------------------
# Node Labels (86 nodes)
# ---------------------------------------------------------------------------

NODE_LABELS: List[str] = (
    [
        "pose_nose",
        "pose_left_shoulder",
        "pose_right_shoulder",
        "pose_left_elbow",
        "pose_right_elbow",
        "pose_left_wrist",
        "pose_right_wrist",
        "pose_left_hip",
        "pose_right_hip",
    ]
    + [f"left_hand_{i}" for i in range(21)]
    + [f"right_hand_{i}" for i in range(21)]
    + [f"face_{mp_idx}" for mp_idx in MP_FACE_INDICES]
)

# ---------------------------------------------------------------------------
# 32 BISINDO Gloss Vocabulary (Contract 2: web/model/labels.json)
# ---------------------------------------------------------------------------

BISINDO_32_GLOSSES: List[str] = [
    "HALO",
    "TERIMA_KASIH",
    "MAAF",
    "TOLONG",
    "SAYA",
    "KAMU",
    "GURU",
    "TEMAN",
    "MAU",
    "SUDAH",
    "BELUM",
    "BISA",
    "TIDAK",
    "ADA",
    "BELAJAR",
    "PAHAM",
    "TANYA",
    "BACA",
    "TULIS",
    "JAWAB",
    "BUKU",
    "TUGAS",
    "KELAS",
    "SEKOLAH",
    "APA",
    "SIAPA",
    "DIMANA",
    "KAPAN",
    "BAGAIMANA",
    "BAIK",
    "BENAR",
    "SALAH",
]
assert len(BISINDO_32_GLOSSES) == 32

GLOSS_TO_ID: Dict[str, int] = {g: i for i, g in enumerate(BISINDO_32_GLOSSES)}
ID_TO_GLOSS: Dict[int, str] = {i: g for i, g in enumerate(BISINDO_32_GLOSSES)}

# 26 Fingerspelling Alphabet Labels (Contract 5: web/model/fingerspell.json)
FINGERSPELL_26_LABELS: List[str] = [chr(ord("A") + i) for i in range(26)]
assert len(FINGERSPELL_26_LABELS) == 26

# ---------------------------------------------------------------------------
# Manifest Columns (Contract 1)
# ---------------------------------------------------------------------------

MANIFEST_COLUMNS: List[str] = [
    "video_id",
    "source",
    "gloss",
    "label",
    "signer",
    "kp_path",
    "rgb_path",
    "split_sd",
]

# Phonology feature columns (Modul 03 Langkah 8)
PHONOLOGY_COLUMNS: List[str] = [
    "handshape_dom",
    "handshape_nondom",
    "location",
    "movement",
    "orientation",
    "handedness",
]


# ---------------------------------------------------------------------------
# Helper: Select 86 keypoints from MediaPipe Holistic landmarks
# ---------------------------------------------------------------------------

def _extract_coords(landmarks, indices: Sequence[int]) -> np.ndarray:
    """
    Extract (x, y, z) coordinates for selected landmark indices.
    Returns NaN array of shape [len(indices), 3] if landmarks is None.
    """
    out = np.full((len(indices), 3), np.nan, dtype=np.float32)
    if landmarks is None:
        return out

    # Support both MediaPipe NormalizedLandmarkList (.landmark) and raw sequence/array
    lm_seq = getattr(landmarks, "landmark", landmarks)
    if isinstance(lm_seq, np.ndarray):
        for out_i, src_i in enumerate(indices):
            if src_i < len(lm_seq):
                out[out_i] = lm_seq[src_i, :3]
        return out

    for out_i, src_i in enumerate(indices):
        if src_i < len(lm_seq):
            lm = lm_seq[src_i]
            if hasattr(lm, "x"):
                out[out_i, 0] = float(lm.x)
                out[out_i, 1] = float(lm.y)
                out[out_i, 2] = float(getattr(lm, "z", 0.0))
            else:
                out[out_i, 0] = float(lm[0])
                out[out_i, 1] = float(lm[1])
                out[out_i, 2] = float(lm[2]) if len(lm) > 2 else 0.0
    return out


def select_from_holistic(
    pose_landmarks=None,
    left_hand_landmarks=None,
    right_hand_landmarks=None,
    face_landmarks=None,
) -> np.ndarray:
    """
    Extract the 86 target keypoints from MediaPipe Holistic results for 1 frame.

    Missing landmark groups are filled with NaN (Contract 1: kp [F, 86, 3] float16/float32,
    NaN = missing).

    Returns
    -------
    kp : np.ndarray of shape [86, 3], dtype float32
    """
    pose_arr = _extract_coords(pose_landmarks, MP_POSE_INDICES)          # [9, 3]
    lh_arr = _extract_coords(left_hand_landmarks, MP_HAND_INDICES)       # [21, 3]
    rh_arr = _extract_coords(right_hand_landmarks, MP_HAND_INDICES)      # [21, 3]
    face_arr = _extract_coords(face_landmarks, MP_FACE_INDICES)          # [35, 3]
    return np.concatenate([pose_arr, lh_arr, rh_arr, face_arr], axis=0).astype(np.float32)
