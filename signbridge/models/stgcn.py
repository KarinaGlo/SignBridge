"""
stgcn.py — Stream A: Spatio-Temporal Graph Convolutional Network (ST-GCN) with 3-partition
adaptive adjacency and phonological multitask head.

Architecture (Bab 1.4, 1.5, & Bab 5.4-5.5):
  - Input: keypoints [B, 64, 86, 3] -> augmented with frame velocity dx -> [B, 6, 64, 86]
  - GraphConv: Y = sum_{k=1..3} (A_k + B_k) X W_k
  - 6 ST-GCN blocks with temporal kernel 9x1 and strides [1, 1, 2, 1, 2, 1] -> [B, 256, 16, 86]
  - Spatial node average -> [B, 16, 256] temporal pose tokens
  - Pooled pose representation p_bar [B, 256] -> Gloss head + Phonology multitask head
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence
import torch
import torch.nn as nn

from signbridge.constants import NUM_KEYPOINTS, PHONOLOGY_COLUMNS
from signbridge.graph import build_adjacency


class GraphConv(nn.Module):
    """
    Spatial Graph Convolution over K=3 adjacency partitions with learnable adaptive matrix B_k:
        Y = sum_{k=1..K} (A_k + B_k) X W_k
    """

    def __init__(self, in_channels: int, out_channels: int, A: torch.Tensor) -> None:
        super().__init__()
        K, V, _ = A.shape
        self.K = K
        self.register_buffer("A", A.clone())
        # Learnable adaptive adjacency perturbation B_k initialized near zero
        self.B = nn.Parameter(torch.zeros(K, V, V))
        self.conv = nn.Conv2d(in_channels, out_channels * K, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [B, C_in, T, V] -> out: [B, C_out, T, V]
        """
        B_sz, _, T, V = x.shape
        x_proj = self.conv(x)  # [B, C_out * K, T, V]
        C_out = x_proj.shape[1] // self.K
        x_proj = x_proj.view(B_sz, self.K, C_out, T, V)

        A_total = self.A + self.B  # [K, V, V]
        out = torch.einsum("bkctv,kvw->bctw", x_proj, A_total)
        return out


class STGCNBlock(nn.Module):
    """
    Single ST-GCN Block (diagram Bab 5.4 p. 25):
      X [B, C, T, V] -> GraphConv -> BN + ReLU -> Temporal Conv 9x1 (stride 1 or 2)
      -> BN + Residual 1x1 -> ReLU
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        A: torch.Tensor,
        stride: int = 1,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.gcn = GraphConv(in_channels, out_channels, A)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        # Temporal 9x1 convolution
        self.tcn = nn.Sequential(
            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=(9, 1),
                stride=(stride, 1),
                padding=(4, 0),
            ),
            nn.BatchNorm2d(out_channels),
            nn.Dropout(dropout, inplace=False),
        )

        if in_channels == out_channels and stride == 1:
            self.residual = nn.Identity()
        else:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=(stride, 1)),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.residual(x)
        out = self.relu(self.bn1(self.gcn(x)))
        out = self.tcn(out)
        return self.relu(out + res)


class STGCNEncoder(nn.Module):
    """
    6-Block ST-GCN Encoder mapping [B, 64, 86, 3] -> 16 temporal tokens of dim 256 ([B, 16, 256]).
    """

    def __init__(
        self,
        hidden_dim: int = 256,
        dropout: float = 0.1,
        num_nodes: int = NUM_KEYPOINTS,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        A_np = build_adjacency(num_nodes)
        A = torch.from_numpy(A_np)

        # Input has 6 channels: (x, y, z, dx, dy, dz)
        in_ch = 6
        c1 = max(64, hidden_dim // 4)
        c2 = max(128, hidden_dim // 2)
        c3 = hidden_dim

        self.data_bn = nn.BatchNorm1d(in_ch * num_nodes)
        self.blocks = nn.ModuleList(
            [
                STGCNBlock(in_ch, c1, A, stride=1, dropout=dropout),
                STGCNBlock(c1, c1, A, stride=1, dropout=dropout),
                STGCNBlock(c1, c2, A, stride=2, dropout=dropout),  # T: 64 -> 32
                STGCNBlock(c2, c2, A, stride=1, dropout=dropout),
                STGCNBlock(c2, c3, A, stride=2, dropout=dropout),  # T: 32 -> 16
                STGCNBlock(c3, c3, A, stride=1, dropout=dropout),
            ]
        )

    def forward_tokens(self, pose: torch.Tensor) -> torch.Tensor:
        """
        pose: [B, T=64, V=86, 3] -> tokens: [B, 16, hidden_dim]
        """
        B, T, V, C = pose.shape
        # Compute frame-to-frame velocity dx_t = x_t - x_{t-1}
        vel = torch.zeros_like(pose)
        vel[:, 1:] = pose[:, 1:] - pose[:, :-1]
        x = torch.cat([pose, vel], dim=-1)  # [B, T, V, 6]

        # Rearrange to [B, C*V, T] for BatchNorm1d, then [B, C, T, V]
        x = x.permute(0, 3, 2, 1).contiguous()  # [B, 6, V, T]
        x = x.view(B, 6 * V, T)
        x = self.data_bn(x)
        x = x.view(B, 6, V, T).permute(0, 1, 3, 2).contiguous()  # [B, 6, T, V]

        for blk in self.blocks:
            x = blk(x)  # [B, hidden_dim, 16, V]

        # Average over spatial nodes V -> [B, 16, hidden_dim]
        tokens = x.mean(dim=-1).transpose(1, 2).contiguous()
        return tokens

    def forward(self, pose: torch.Tensor) -> torch.Tensor:
        """Return temporally pooled feature p_bar [B, hidden_dim]."""
        tokens = self.forward_tokens(pose)
        return tokens.mean(dim=1)


class PhonologyMultitaskHead(nn.Module):
    """
    Multitask classification head for the 6 phonological attributes of BISINDO:
    handshape_dom, handshape_nondom, location, movement, orientation, handedness.
    """

    def __init__(
        self,
        in_dim: int = 256,
        attr_num_classes: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        if attr_num_classes is None:
            attr_num_classes = {col: 8 for col in PHONOLOGY_COLUMNS}
        self.attr_names: List[str] = list(PHONOLOGY_COLUMNS)
        self.heads = nn.ModuleDict(
            {
                col: nn.Linear(in_dim, int(attr_num_classes.get(col, 8)))
                for col in self.attr_names
            }
        )

    def forward(self, feat: torch.Tensor) -> List[torch.Tensor]:
        """Return list of logits tensors, one per phonological attribute."""
        return [self.heads[col](feat) for col in self.attr_names]


class PoseModel(nn.Module):
    """
    M1 (E1/E2/E3) & X1-X3 Pose-Only ST-GCN Classifier with optional Phonology Multitask Head.
    """

    def __init__(
        self,
        num_classes: int = 32,
        hidden_dim: int = 256,
        dropout: float = 0.2,
        use_phonology: bool = False,
        phono_num_classes: Optional[Dict[str, int]] = None,
    ) -> None:
        super().__init__()
        self.encoder = STGCNEncoder(hidden_dim=hidden_dim, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self.use_phonology = bool(use_phonology)
        self.phono_head = (
            PhonologyMultitaskHead(in_dim=hidden_dim, attr_num_classes=phono_num_classes)
            if self.use_phonology
            else None
        )

    def forward(
        self,
        pose: torch.Tensor,
        rgb: Optional[torch.Tensor] = None,
    ) -> Dict[str, Optional[torch.Tensor | List[torch.Tensor]]]:
        tokens = self.encoder.forward_tokens(pose)  # [B, 16, D]
        pooled = self.dropout(tokens.mean(dim=1))   # [B, D]
        logits = self.classifier(pooled)
        phono_logits = self.phono_head(pooled) if self.phono_head is not None else None
        return {
            "logits": logits,
            "pose_logits": logits,
            "rgb_logits": None,
            "phonology_logits": phono_logits,
            "gate": None,
            "features": pooled,
        }

