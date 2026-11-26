"""
signbridge/image/models/mobilenetv3_p1.py
Official torchvision MobileNetV3-Small with Pretrained ImageNet Weights (P1).

Contract & Specifications:
- Input shape: [batch_size, 3, 224, 224] (Normalized using ImageNet mean & std)
- Output logits: [batch_size, 26] (A-Z classes)
- Weights: torchvision.models.MobileNet_V3_Small_Weights.DEFAULT
- Classifier: Replaces classifier[3] (Linear(1024, 1000) -> Linear(1024, 26))
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import MobileNet_V3_Small_Weights

from signbridge.constants import FINGERSPELL_26_LABELS, IMAGE_SIZE

logger = logging.getLogger("mobilenetv3_p1")


class MobileNetV3SmallPretrainedClassifier(nn.Module):
    """
    MobileNetV3-Small transfer learning classifier using official torchvision architecture
    and ImageNet-1K pretrained weights.
    """

    def __init__(
        self,
        num_classes: int = 26,
        dropout: float = 0.2,
        pretrained: bool = True,
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.dropout_rate = dropout
        self.pretrained = pretrained

        # Load official torchvision model
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        self.backbone = models.mobilenet_v3_small(weights=weights)

        # Update dropout if different from default (0.2)
        if hasattr(self.backbone.classifier[2], "p"):
            self.backbone.classifier[2].p = dropout

        # Replace final classification head: in_features is 1024
        in_features = self.backbone.classifier[3].in_features
        self.backbone.classifier[3] = nn.Linear(in_features, num_classes)

        # Initialize the newly added linear head with He/Kaiming normal
        nn.init.kaiming_normal_(self.backbone.classifier[3].weight, nonlinearity="linear")
        nn.init.zeros_(self.backbone.classifier[3].bias)

        logger.info(
            "MobileNetV3SmallPretrainedClassifier initialized (pretrained=%s, classes=%d, dropout=%.2f)",
            pretrained, num_classes, dropout
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Tensor of shape [batch_size, 3, 224, 224]
        Returns:
            logits: Tensor of shape [batch_size, 26]
        """
        return self.backbone(x)

    def freeze_backbone(self) -> None:
        """
        Stage 1: Freeze all layers in features backbone so only classifier head is trained.
        """
        for param in self.backbone.features.parameters():
            param.requires_grad = False
        # Ensure classifier head is trainable
        for param in self.backbone.classifier.parameters():
            param.requires_grad = True
        logger.info("Backbone frozen. Only classifier head is trainable.")

    def unfreeze_backbone(self, from_layer: int = 9) -> None:
        """
        Stage 2: Unfreeze top layers of the backbone starting from `from_layer` (default 9).
        Layers 0 to from_layer-1 remain frozen to preserve low-level visual feature extractors.
        """
        # First freeze all
        for param in self.backbone.features.parameters():
            param.requires_grad = False

        # Unfreeze from from_layer to end of features
        num_feature_layers = len(self.backbone.features)
        for idx in range(from_layer, num_feature_layers):
            for param in self.backbone.features[idx].parameters():
                param.requires_grad = True

        # Ensure classifier head is trainable
        for param in self.backbone.classifier.parameters():
            param.requires_grad = True

        logger.info(
            "Backbone unfrozen from features[%d] to features[%d].",
            from_layer, num_feature_layers - 1
        )

    def unfreeze_all(self) -> None:
        """Unfreeze all parameters in the model."""
        for param in self.parameters():
            param.requires_grad = True
        logger.info("All parameters unfrozen.")

    def count_parameters(self) -> Dict[str, int]:
        """Returns detailed parameter breakdown."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        backbone_total = sum(p.numel() for p in self.backbone.features.parameters())
        head_total = sum(p.numel() for p in self.backbone.classifier.parameters())
        return {
            "total_params": total,
            "trainable_params": trainable,
            "frozen_params": total - trainable,
            "backbone_params": backbone_total,
            "head_params": head_total,
        }


def build_mobilenetv3_p1(
    num_classes: int = 26,
    dropout: float = 0.2,
    pretrained: bool = True,
) -> MobileNetV3SmallPretrainedClassifier:
    """Factory function to build P1 MobileNetV3-Small pretrained model."""
    return MobileNetV3SmallPretrainedClassifier(
        num_classes=num_classes,
        dropout=dropout,
        pretrained=pretrained,
    )

