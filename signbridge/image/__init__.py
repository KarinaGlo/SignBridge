"""Image modality package for BISINDO A-Z Fingerspelling (I1-I3) and hand cropping."""

from __future__ import annotations

from typing import Any

from signbridge.image.crop import compute_hand_crop_box, crop_and_resize_hand, normalize_imagenet

__all__ = [
    "compute_hand_crop_box",
    "crop_and_resize_hand",
    "normalize_imagenet",
    "build_image_model",
    "run_image_training",
    "export_fingerspell_onnx",
]


def __getattr__(name: str) -> Any:
    """Lazy-load PyTorch image training utilities so runtime hand-cropping works without torch."""
    if name in ("build_image_model", "run_image_training", "export_fingerspell_onnx"):
        from signbridge.image import train_image

        return getattr(train_image, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

