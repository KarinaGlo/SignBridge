"""
student.py — M0 / M5 / X4 Student Pose-Transformer for Real-Time Browser Inference.

Contract 2 (Bab 2.3 & Bab 1.4):
  - Input:  keypoints float32 [B, 64, 86, 3]
  - Output: logits float32 [B, num_classes] (default 32 for BISINDO, 105 for FSL)
  - Architecture:
      * Concatenates frame-to-frame velocity dx -> 86 * 6 = 516 input features per frame
      * Linear projection + LayerNorm -> d_model=160
      * 4-layer Transformer Encoder (nhead=4, dim_feedforward=640, GELU)
      * Temporal average pooling -> Linear classifier
  - Size: ~1.3M parameters (~5 MB FP32, ~1.4 MB INT8 ONNX < 10 MB limit)
"""

from __future__ import annotations

from typing import Dict, Optional
import torch
import torch.nn as nn

from signbridge.constants import NUM_KEYPOINTS, NUM_COORDS, T_MAX


class StudentPoseTransformer(nn.Module):
    """
    Lightweight Pose-Transformer Student Model designed for sub-50ms browser inference via ONNX.

    Can be called directly as `model(keypoints)` returning `logits [B, num_classes]` (for ONNX export)
    or `model.forward_dict(keypoints)` returning the standard training dictionary.
    """

    def __init__(
        self,
        num_classes: int = 32,
        d_model: int = 160,
        nhead: int = 4,
        num_layers: int = 4,
        dim_feedforward: int = 640,
        dropout: float = 0.15,
        max_len: int = T_MAX,
        num_keypoints: int = NUM_KEYPOINTS,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.d_model = d_model
        self.num_keypoints = num_keypoints

        in_features = num_keypoints * NUM_COORDS * 2  # position (3) + velocity (3) = 6 per node
        self.input_proj = nn.Sequential(
            nn.Linear(in_features, d_model),
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
        )
        self.pos_embed = nn.Parameter(torch.randn(1, max_len, d_model) * 0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, num_classes)

    def encode(self, keypoints: torch.Tensor) -> torch.Tensor:
        """
        keypoints: [B, T=64, 86, 3] -> pooled representation [B, d_model]
        """
        B, T, V, C = keypoints.shape
        vel = torch.zeros_like(keypoints)
        vel[:, 1:] = keypoints[:, 1:] - keypoints[:, :-1]
        feat = torch.cat([keypoints, vel], dim=-1).reshape(B, T, V * C * 2)  # [B, T, 516]

        x = self.input_proj(feat)
        x = x + self.pos_embed[:, :T, :]
        x = self.encoder(x)
        x = self.norm(x)
        return x.mean(dim=1)

    def forward(self, keypoints: torch.Tensor) -> torch.Tensor:
        """
        Direct tensor forward for ONNX export:
            keypoints [B, 64, 86, 3] -> logits [B, num_classes]
        """
        pooled = self.encode(keypoints)
        return self.head(pooled)

    def forward_dict(
        self,
        pose: torch.Tensor,
        rgb: Optional[torch.Tensor] = None,
    ) -> Dict[str, Optional[torch.Tensor]]:
        pooled = self.encode(pose)
        logits = self.head(pooled)
        return {
            "logits": logits,
            "pose_logits": logits,
            "rgb_logits": None,
            "phonology_logits": None,
            "gate": None,
            "features": pooled,
        }

