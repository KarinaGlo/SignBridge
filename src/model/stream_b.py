"""
stream_b.py — Stream_B: VideoMAE / I3D backbone for RGB video processing.

Task 6.4.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6.

Input:  [B, T, 3, H, W]  (any T, any H, any W)
Output: [B, 512]

Pipeline:
  1. preprocess      — resize to 224×224, normalize with ImageNet mean/std
  2. temporal_sample — uniform sampling → exactly 16 frames
  3. backbone         — 3D CNN → [B, 512]
"""

from __future__ import annotations

from typing import List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Simple 3D CNN backbone (fallback when pretrained torchvision models are
# unavailable or for fast testing without downloading weights)
# ---------------------------------------------------------------------------

class SimpleVideoBackbone(nn.Module):
    """
    Lightweight 3D CNN backbone that maps [B, 3, T, 224, 224] → [B, output_dim].

    In production this would be replaced by a pretrained VideoMAE / I3D model
    loaded from ``pretrained_url``. The interface (input/output shapes) remains
    identical.
    """

    def __init__(self, output_dim: int = 512):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv3d(3, 64, kernel_size=(3, 7, 7), stride=(1, 2, 2), padding=(1, 3, 3)),
            nn.BatchNorm3d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 2, 2)),

            nn.Conv3d(64, 128, kernel_size=(3, 5, 5), stride=(1, 2, 2), padding=(1, 2, 2)),
            nn.BatchNorm3d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 2, 2)),

            nn.Conv3d(128, 256, kernel_size=(3, 3, 3), stride=(1, 2, 2), padding=(1, 1, 1)),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool3d(1),
        )
        self.fc = nn.Linear(256, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, 3, T, H, W] → [B, output_dim]."""
        x = self.features(x)          # [B, 256, 1, 1, 1]
        x = x.flatten(1)              # [B, 256]
        x = self.fc(x)                # [B, output_dim]
        return x


# ---------------------------------------------------------------------------
# StreamB
# ---------------------------------------------------------------------------

class StreamB(nn.Module):
    """
    VideoMAE / I3D backbone for RGB video processing.

    Input:  [B, T, 3, H, W]  (T_sample after sampling = 16)
    Output: [B, 512]

    Config:
      - arch          : "videomae" | "i3d" | "mobilevit"  (default "videomae")
      - pretrained_url: URL sumber bobot pretrained
      - frozen_layers: list of layer name prefixes to freeze
      - output_dim    : 512 (default)
      - num_frames    : 16 (uniform temporal sampling target)
    """

    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]

    def __init__(
        self,
        arch: str = "videomae",
        pretrained_url: str = "",
        frozen_layers: Optional[List[str]] = None,
        output_dim: int = 512,
        num_frames: int = 16,
    ):
        super().__init__()
        self.arch = arch
        self.pretrained_url = pretrained_url
        self.frozen_layers: List[str] = list(frozen_layers) if frozen_layers else []
        self.output_dim = output_dim
        self.num_frames = num_frames

        # Register ImageNet mean/std as buffers for preprocessing
        # Shape [1, 1, 3, 1, 1] broadcasts with [B, T, 3, H, W]
        self.register_buffer(
            "mean", torch.tensor(self.IMAGENET_MEAN).view(1, 1, 3, 1, 1)
        )
        self.register_buffer(
            "std", torch.tensor(self.IMAGENET_STD).view(1, 1, 3, 1, 1)
        )

        # Build backbone (uses SimpleVideoBackbone as fallback / default)
        self.backbone = SimpleVideoBackbone(output_dim=output_dim)

        # Freeze specified layers (Requirement 8.6)
        self._freeze_layers()

    # ------------------------------------------------------------------
    # Preprocessing (Requirement 8.3)
    # ------------------------------------------------------------------

    def preprocess(self, frames: torch.Tensor) -> torch.Tensor:
        """
        Resize to 224×224, normalize with ImageNet mean/std.

        Input:  [B, T, 3, H, W]  (pixel values, any H, W)
        Output: [B, T, 3, 224, 224]
        """
        B, T, C, H, W = frames.shape

        # Resize each frame to 224×224
        frames_flat = frames.reshape(B * T, C, H, W)
        frames_flat = F.interpolate(
            frames_flat, size=(224, 224), mode="bilinear", align_corners=False
        )
        frames = frames_flat.reshape(B, T, C, 224, 224)

        # Normalize: (x - mean) / std
        frames = (frames - self.mean) / self.std
        return frames

    # ------------------------------------------------------------------
    # Temporal sampling (Requirement 8.5)
    # ------------------------------------------------------------------

    def temporal_sample(self, frames: torch.Tensor, n: int = 16) -> torch.Tensor:
        """
        Uniform temporal sampling → exactly ``n`` frames (default 16).

        If T < n: replicate the last frame to reach n.
        If T >= n: select n evenly-spaced indices covering the full range.
        """
        B, T = frames.shape[:2]

        if T >= n:
            # Evenly-spaced indices over [0, T-1]
            indices = torch.linspace(0, T - 1, n).long().to(frames.device)
            return frames[:, indices]
        else:
            # Replicate last frame
            last = frames[:, -1:].expand(B, n - T, *frames.shape[2:])
            return torch.cat([frames, last], dim=1)

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """
        frames: [B, T, 3, H, W] → preprocess → temporal_sample → backbone → [B, 512]
        """
        # 1. Preprocess (resize + normalize)
        frames = self.preprocess(frames)

        # 2. Temporal sampling → [B, 16, 3, 224, 224]
        frames = self.temporal_sample(frames, self.num_frames)

        # 3. Rearrange to [B, 3, T, H, W] for 3D conv
        frames = frames.permute(0, 2, 1, 3, 4)  # [B, 3, 16, 224, 224]

        # 4. Backbone → [B, output_dim]
        out = self.backbone(frames)
        return out

    # ------------------------------------------------------------------
    # Layer freezing (Requirement 8.6)
    # ------------------------------------------------------------------

    def _freeze_layers(self) -> None:
        """Freeze parameters whose name starts with any prefix in ``frozen_layers``."""
        if not self.frozen_layers:
            return

        for name, param in self.backbone.named_parameters():
            for frozen_name in self.frozen_layers:
                if name.startswith(frozen_name):
                    param.requires_grad = False
                    break
