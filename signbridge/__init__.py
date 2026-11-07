"""
SignBridge ID-PH: Real-Time Multimodal BISINDO-FSL Communication Bridge.

Package structure follows the team module specification:
  - signbridge.constants : 86-keypoint layout, 32 BISINDO glosses, 26 A-Z labels, manifest schema
  - signbridge.features  : Keypoint trimming, shoulder normalization, 64-frame resampling (JS parity)
  - signbridge.graph     : 86-node anatomical graph & 3-partition adjacency matrix
  - signbridge.augment   : Spatial & temporal keypoint augmentations (handedness mirror, rotation, etc.)
  - signbridge.data      : SignDataset & manifest loaders (SD 60/10/30 & SI LOSO protocols)
  - signbridge.models    : ST-GCN, StudentPoseTransformer, RGBOnlyModel, TwoStreamFusionModel
  - signbridge.train     : Unified training & knowledge distillation CLI
  - signbridge.export_onnx : PyTorch -> ONNX + INT8 quantization & parity checker (< 1e-4)
  - signbridge.evaluate  : Comprehensive evaluation, LOSO aggregator, error & gate analysis
  - signbridge.image     : Hand crop (JS parity) & Fingerspelling I1-I3 models
  - signbridge.audio     : Whisper ASR A1-A4 training & WER/CER/RTF evaluation
  - signbridge.text      : Pseudo-gloss generator, B0/T1-T3 gloss-to-sentence, MT0-MT3 ID-FIL translation
  - signbridge.bridge    : 3-layer BISINDO <-> FSL communication bridge (L1 concept, L2 NLLB, L3 animation)
"""

from signbridge.constants import (
    NUM_KEYPOINTS,
    NUM_COORDS,
    T_MAX,
    BISINDO_32_GLOSSES,
    FINGERSPELL_26_LABELS,
)

__version__ = "1.0.0"

__all__ = [
    "NUM_KEYPOINTS",
    "NUM_COORDS",
    "T_MAX",
    "BISINDO_32_GLOSSES",
    "FINGERSPELL_26_LABELS",
    "__version__",
]

