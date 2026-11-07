"""
stream_a.py — Stream_A: ST-GCN / Pose-Transformer backbone for keypoint skeleton.

Tasks 6.1, 6.3.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5.

Input:  [B, T_max=64, 86, 3]  + padding_mask [B, T_max]  (True = valid frame)
Output: [B, 512]

Kontrak ONNX (tidak boleh berubah):
  - num_keypoints = 86   (layout: tangan kanan [0:21], kiri [21:42],
                          pose [42:75], wajah selektif [75:86])
  - T_max          = 64  (uniform sampling / zero-pad ke 64 frame)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.exceptions import ConfigValidationError


# ---------------------------------------------------------------------------
# ST-GCN block
# ---------------------------------------------------------------------------

class STGCNBlock(nn.Module):
    """
    One ST-GCN block: spatial graph conv + temporal conv with residual.

    Operates on tensors of shape [B, C, T]:
      - Spatial (pointwise) conv: 1×1 conv across channels  (captures keypoint interactions)
      - Temporal conv: 1D conv over the time dimension with ``kernel_size``
      - Residual connection + BatchNorm + ReLU
    """

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 9, stride: int = 1):
        super().__init__()
        padding = kernel_size // 2  # preserves T

        # Spatial (pointwise) conv — 1×1 across channels
        self.spatial_conv = nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride)

        # Temporal conv — 1D over time
        self.temporal_conv = nn.Conv1d(out_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding)

        self.bn = nn.BatchNorm1d(out_channels)

        # Residual projection when channel dims differ
        if in_channels != out_channels:
            self.residual = nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride)
        else:
            self.residual = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [B, C, T] → [B, C_out, T]."""
        residual = x if self.residual is None else self.residual(x)

        out = self.spatial_conv(x)
        out = self.temporal_conv(out)
        out = out + residual
        out = self.bn(out)
        out = F.relu(out)
        return out


# ---------------------------------------------------------------------------
# Pose-Transformer encoder (alternative Stream_A backbone, Task 6.3)
# ---------------------------------------------------------------------------

class PoseTransformerEncoder(nn.Module):
    """
    Transformer encoder with positional + temporal embedding.

    Requirement 7.2: minimal 4 encoder layers, positional encoding for keypoint
    position, temporal embedding for frame index, output dim 512.
    """

    def __init__(
        self,
        num_keypoints: int = 86,
        num_coords: int = 3,
        hidden_dim: int = 256,
        num_heads: int = 8,
        num_layers: int = 4,
        max_T: int = 64,              # kontrak T_max=64
        output_dim: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.num_keypoints = num_keypoints
        self.num_coords = num_coords
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.max_T = max_T

        input_dim = num_keypoints * num_coords  # 86 × 3 = 258

        # Input projection: flatten keypoints → hidden_dim
        self.input_proj = nn.Linear(input_dim, hidden_dim)

        # Positional encoding for keypoint position (learnable)
        self.pos_embedding = nn.Parameter(torch.randn(1, max(max_T, 512), hidden_dim) * 0.02)

        # Temporal embedding for frame index (learnable)
        self.temporal_embedding = nn.Parameter(torch.randn(1, max(max_T, 512), hidden_dim) * 0.02)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Output projection to 512
        self.output_proj = nn.Linear(hidden_dim, output_dim)

    def forward(self, keypoints: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
        """
        keypoints:     [B, T_max=64, 86, 3]  (kontrak ONNX)
        padding_mask:  [B, T_max]  True = valid frame, False = padding
        Returns:        [B, 512]
        """
        B, T_max, V, C = keypoints.shape
        if V != self.num_keypoints:
            if V > self.num_keypoints:
                keypoints = keypoints[:, :, : self.num_keypoints, :]
            else:
                pad = torch.zeros(
                    B, T_max, self.num_keypoints - V, C,
                    dtype=keypoints.dtype, device=keypoints.device,
                )
                keypoints = torch.cat([keypoints, pad], dim=2)
            V = self.num_keypoints

        # Flatten keypoints → [B, T_max, V*C]
        x = keypoints.reshape(B, T_max, V * C)
        x = self.input_proj(x)  # [B, T_max, hidden_dim]

        # Add positional + temporal embeddings (sliced to actual T_max)
        x = x + self.pos_embedding[:, :T_max] + self.temporal_embedding[:, :T_max]

        # Transformer expects src_key_padding_mask where True = *padding* (mask out).
        # Our mask: True = valid → invert.
        src_key_padding_mask = ~padding_mask  # [B, T_max], True = padding

        x = self.encoder(x, src_key_padding_mask=src_key_padding_mask)  # [B, T_max, hidden_dim]

        # Masked mean pool over temporal dim
        mask = padding_mask.unsqueeze(-1).float()  # [B, T_max, 1]
        masked_sum = (x * mask).sum(dim=1)          # [B, hidden_dim]
        valid_count = mask.sum(dim=1).clamp(min=1.0) # [B, 1]
        pooled = masked_sum / valid_count            # [B, hidden_dim]

        out = self.output_proj(pooled)  # [B, 512]
        return out


# ---------------------------------------------------------------------------
# StreamA — main class (Task 6.1)
# ---------------------------------------------------------------------------

class StreamA(nn.Module):
    """
    ST-GCN backbone for keypoint skeleton processing.

    Input:  [B, T_max=64, 86, 3]  + padding_mask [B, T_max]  (True = valid)
    Output: [B, 512]

    Kontrak ONNX:
      num_keypoints = 86   (default, tidak boleh diubah untuk ekspor ONNX)
      T_max         = 64   (tidak boleh diubah untuk ekspor ONNX)

    Config (Requirement 7.5):
      - num_blocks : 4–20  (default 10)
      - hidden_dim : 128–512 (default 256)
      - num_heads  : 1–16  (default 8)  — used by Pose-Transformer variant
      - arch       : "stgcn" | "pose_transformer"
    """

    def __init__(
        self,
        num_blocks: int = 10,
        hidden_dim: int = 256,
        num_heads: int = 8,
        num_keypoints: int = 86,   # kontrak: 86 node (bukan 543)
        num_coords: int = 3,
        arch: str = "stgcn",
    ):
        # --- Config validation (Requirement 7.5) ---
        if not isinstance(num_blocks, int) or not (4 <= num_blocks <= 20):
            raise ConfigValidationError("num_blocks", num_blocks, "[4, 20]")
        if not isinstance(hidden_dim, int) or not (128 <= hidden_dim <= 512):
            raise ConfigValidationError("hidden_dim", hidden_dim, "[128, 512]")
        if not isinstance(num_heads, int) or not (1 <= num_heads <= 16):
            raise ConfigValidationError("num_heads", num_heads, "[1, 16]")

        super().__init__()
        self.arch = arch
        self.num_blocks = num_blocks
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_keypoints = num_keypoints
        self.num_coords = num_coords

        input_dim = num_keypoints * num_coords  # 86 × 3 = 258

        if arch == "stgcn":
            # Input projection: 543*3 → hidden_dim
            self.input_proj = nn.Linear(input_dim, hidden_dim)

            # Stack of STGCN blocks
            self.blocks = nn.ModuleList(
                [STGCNBlock(hidden_dim, hidden_dim, kernel_size=9) for _ in range(num_blocks)]
            )

            # Output projection: hidden_dim → 512
            self.output_proj = nn.Linear(hidden_dim, 512)

        elif arch == "pose_transformer":
            self.encoder = PoseTransformerEncoder(
                num_keypoints=num_keypoints,
                num_coords=num_coords,
                hidden_dim=hidden_dim,
                num_heads=num_heads,
                num_layers=num_blocks,  # already validated ≥ 4
                max_T=64,              # kontrak T_max=64
                output_dim=512,
            )
        else:
            raise ValueError(
                f"Unknown arch: {arch!r}. Valid options: 'stgcn', 'pose_transformer'"
            )

    # ------------------------------------------------------------------

    def forward(self, keypoints: torch.Tensor, padding_mask: torch.Tensor) -> torch.Tensor:
        """
        keypoints:     [B, T_max=64, 86, 3]  (kontrak ONNX)
        padding_mask:  [B, T_max]  True = valid frame, False = padding
        Returns:        [B, 512]
        """
        if self.arch == "pose_transformer":
            return self.encoder(keypoints, padding_mask)

        # ---- ST-GCN forward ----
        B, T_max, V, C = keypoints.shape
        if V != self.num_keypoints:
            if V > self.num_keypoints:
                keypoints = keypoints[:, :, : self.num_keypoints, :]
            else:
                pad = torch.zeros(
                    B, T_max, self.num_keypoints - V, C,
                    dtype=keypoints.dtype, device=keypoints.device,
                )
                keypoints = torch.cat([keypoints, pad], dim=2)
            V = self.num_keypoints

        # 1. Flatten last two dims → [B, T_max, V*C]
        x = keypoints.reshape(B, T_max, V * C)

        # 2. Project to hidden_dim → [B, T_max, hidden_dim]
        x = self.input_proj(x)

        # 3. Transpose to [B, hidden_dim, T_max] for temporal conv
        x = x.transpose(1, 2)  # [B, hidden_dim, T_max]

        # 4. Apply STGCN blocks
        for block in self.blocks:
            x = block(x)

        # 5. Transpose back → [B, T_max, hidden_dim]
        x = x.transpose(1, 2)

        # 6. Project to 512 → [B, T_max, 512]
        x = self.output_proj(x)

        # 7. Masked mean pool over temporal dim
        mask = padding_mask.unsqueeze(-1).float()   # [B, T_max, 1]
        masked_sum = (x * mask).sum(dim=1)          # [B, 512]
        valid_count = mask.sum(dim=1).clamp(min=1.0) # [B, 1]
        pooled = masked_sum / valid_count            # [B, 512]

        return pooled
