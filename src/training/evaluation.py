"""
evaluation.py — Evaluation utilities for SignBridge BISINDO.

Task 8.7.
Requirements: 10.5, 11.4, 11.5.

Implements:
  - top_k_accuracy    : compute Top-1 and Top-5 accuracy from logits
  - EvaluationMetrics : per-epoch reporting container
  - Evaluator         : evaluates a model on a DataLoader, returns EvaluationMetrics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import torch


# ---------------------------------------------------------------------------
# Accuracy helpers
# ---------------------------------------------------------------------------

def top_k_accuracy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    k: int,
) -> float:
    """
    Compute Top-k accuracy.

    Parameters
    ----------
    logits : [B, num_classes]
    labels : [B]
    k : int

    Returns
    -------
    float in [0.0, 1.0]
    """
    with torch.no_grad():
        B, num_classes = logits.shape
        k = min(k, num_classes)
        _, topk_indices = logits.topk(k, dim=1)         # [B, k]
        correct = topk_indices.eq(labels.view(-1, 1).expand_as(topk_indices))  # [B, k]
        return correct.any(dim=1).float().mean().item()


def top1_accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Convenience wrapper for Top-1 accuracy."""
    return top_k_accuracy(logits, labels, k=1)


def top5_accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Convenience wrapper for Top-5 accuracy."""
    return top_k_accuracy(logits, labels, k=5)


# ---------------------------------------------------------------------------
# EvaluationMetrics container
# ---------------------------------------------------------------------------

@dataclass
class EvaluationMetrics:
    """Container for per-epoch evaluation results."""
    epoch: int
    loss: float
    top1: float
    top5: Optional[float]       # None when num_classes <= 5
    num_classes: int
    phonological: Optional[Dict[str, float]] = field(default=None)  # head-wise accuracy

    def to_dict(self) -> dict:
        d: dict = {
            "epoch": self.epoch,
            "loss": self.loss,
            "top1": self.top1,
            "num_classes": self.num_classes,
        }
        if self.top5 is not None:
            d["top5"] = self.top5
        if self.phonological:
            d["phonological"] = self.phonological
        return d

    def __str__(self) -> str:
        parts = [f"Epoch {self.epoch} | Loss {self.loss:.4f} | Top-1 {self.top1:.4f}"]
        if self.top5 is not None:
            parts.append(f"Top-5 {self.top5:.4f}")
        if self.phonological:
            for k, v in self.phonological.items():
                parts.append(f"{k} {v:.4f}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Evaluator — Task 8.7
# ---------------------------------------------------------------------------

class Evaluator:
    """
    Evaluates a model on a DataLoader and returns EvaluationMetrics.

    Rules (Requirement 10.5, 11.4, 11.5):
      - Always report Top-1 after each epoch.
      - Only report Top-5 if num_classes > 5.
      - Report phonological head accuracies only if use_phonological_head=True.
      - All metrics are computed after the full epoch (not incremental).
    """

    def __init__(self, num_classes: int, use_phonological_head: bool = True):
        self.num_classes = num_classes
        self.use_phonological_head = use_phonological_head
        self._report_top5 = num_classes > 5

    def compute_metrics(
        self,
        all_logits: torch.Tensor,
        all_labels: torch.Tensor,
        loss: float,
        epoch: int,
        phono_logits_dict: Optional[Dict[str, torch.Tensor]] = None,
        phono_labels_dict: Optional[Dict[str, torch.Tensor]] = None,
    ) -> EvaluationMetrics:
        """
        Compute evaluation metrics from accumulated tensors.

        Parameters
        ----------
        all_logits        : [N, num_classes] accumulated over epoch
        all_labels        : [N] accumulated over epoch
        loss              : average validation loss for the epoch
        epoch             : current epoch index
        phono_logits_dict : dict of {key: [N, num_k]} — accumulated phono logits
        phono_labels_dict : dict of {key: [N]} — accumulated phono labels
        """
        t1 = top1_accuracy(all_logits, all_labels)
        t5 = top5_accuracy(all_logits, all_labels) if self._report_top5 else None

        phono_metrics: Optional[Dict[str, float]] = None
        if (
            self.use_phonological_head
            and phono_logits_dict is not None
            and phono_labels_dict is not None
        ):
            phono_metrics = {}
            for key in phono_logits_dict:
                if key in phono_labels_dict:
                    phono_metrics[key] = top1_accuracy(
                        phono_logits_dict[key],
                        phono_labels_dict[key],
                    )

        return EvaluationMetrics(
            epoch=epoch,
            loss=loss,
            top1=t1,
            top5=t5,
            num_classes=self.num_classes,
            phonological=phono_metrics,
        )

    def report(self, metrics: EvaluationMetrics) -> None:
        """Print a formatted evaluation report."""
        print(str(metrics))
        if metrics.phonological:
            print(
                "  Phonological →",
                ", ".join(f"{k}: {v:.4f}" for k, v in metrics.phonological.items()),
            )
