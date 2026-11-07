"""
losses.py — Loss functions untuk training SignBridge ID–PH.

Task 8.1.
Requirements: 10.3, 10.4, 11.3, 14.2.

Implements:
  - label_smoothing_ce  : label smoothing cross-entropy (smoothing ∈ [0.0, 1.0))
  - teacher_loss        : ℒ = CE_ls(y) + 0.3*(CE_pose + CE_rgb)
                               + 0.5*(1/|F|)*Σ_f CE(fonologi_f)
  - total_loss          : (alias lama) L_total = L_gloss + λ₁·L_hs + λ₂·L_lok + λ₃·L_gerak
  - distillation_loss   : ℒ = α*CE(y,s) + (1-α)*T²*KL(σ(t/T) ‖ σ(s/T))
                          Kontrak: α=0.5, T=4 (tidak boleh berubah)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.exceptions import ConfigValidationError


# ---------------------------------------------------------------------------
# LossFunctions
# ---------------------------------------------------------------------------

class LossFunctions:
    """Centralised loss functions for gloss + phonological + distillation."""

    # ------------------------------------------------------------------
    # Label smoothing cross-entropy (Requirement 10.3)
    # ------------------------------------------------------------------

    @staticmethod
    def label_smoothing_ce(
        logits: torch.Tensor,
        labels: torch.Tensor,
        smoothing: float = 0.1,
    ) -> torch.Tensor:
        """
        Label smoothing cross-entropy.

        Parameters
        ----------
        logits   : [B, num_classes]
        labels   : [B]  (int64 class indices)
        smoothing: float ∈ [0.0, 1.0)

        Raises
        ------
        ConfigValidationError
            Jika smoothing di luar [0.0, 1.0).
        """
        if not (0.0 <= smoothing < 1.0):
            raise ConfigValidationError("label_smoothing", smoothing, "[0.0, 1.0)")
        return F.cross_entropy(logits, labels, label_smoothing=smoothing)

    # ------------------------------------------------------------------
    # Teacher loss (Requirement 11.3)
    # ℒ = CE_ls(y) + 0.3*(CE_pose + CE_rgb)
    #     + 0.5 * (1/|F|) * Σ_f CE(fonologi_f)
    # ------------------------------------------------------------------

    @staticmethod
    def teacher_loss(
        gloss_logits: torch.Tensor,       # fused head: [B, num_classes]
        pose_logits: torch.Tensor,        # Stream_A aux head: [B, num_classes]
        rgb_logits: torch.Tensor,         # Stream_B aux head: [B, num_classes]
        fonologi_logits: list[torch.Tensor],  # list of [B, num_fonologi_classes_f]
        labels: torch.Tensor,             # [B] int64 gloss labels
        fonologi_labels: list[torch.Tensor],  # list of [B] int64 per fitur fonologis
        smoothing: float = 0.1,
        lambda_aux: float = 0.3,
        lambda_fonologi: float = 0.5,
    ) -> torch.Tensor:
        """
        Teacher loss:
            ℒ = CE_ls(y) + λ_aux*(CE_pose + CE_rgb)
                + λ_fonologi * (1/|F|) * Σ_f CE(fonologi_f)

        Default sesuai spesifikasi: lambda_aux=0.3, lambda_fonologi=0.5.

        Parameters
        ----------
        gloss_logits     : logits dari fused GlossHead [B, C]
        pose_logits      : logits dari Stream_A aux head [B, C]
        rgb_logits       : logits dari Stream_B aux head [B, C]
        fonologi_logits  : list[Tensor] logits tiap fitur fonologis
        labels           : [B] label gloss
        fonologi_labels  : list[Tensor] label tiap fitur fonologis
        smoothing        : label smoothing untuk CE_ls
        lambda_aux       : bobot CE_pose + CE_rgb (default 0.3)
        lambda_fonologi  : bobot rata-rata CE fonologis (default 0.5)

        Returns
        -------
        Scalar tensor — total teacher loss, finite non-negatif.
        """
        if not (0.0 <= smoothing < 1.0):
            raise ConfigValidationError("label_smoothing", smoothing, "[0.0, 1.0)")

        # CE_ls(y) — main gloss loss dengan label smoothing
        ce_main = F.cross_entropy(gloss_logits, labels, label_smoothing=smoothing)

        # CE_pose + CE_rgb — auxiliary stream losses
        ce_pose = F.cross_entropy(pose_logits, labels)
        ce_rgb  = F.cross_entropy(rgb_logits, labels)
        aux_loss = lambda_aux * (ce_pose + ce_rgb)

        # (1/|F|) * Σ_f CE(fonologi_f) — fonologi multi-task losses
        fonologi_loss = torch.tensor(0.0, device=gloss_logits.device)
        if fonologi_logits and fonologi_labels:
            F_count = len(fonologi_logits)
            for f_logits, f_labels in zip(fonologi_logits, fonologi_labels):
                fonologi_loss = fonologi_loss + F.cross_entropy(f_logits, f_labels)
            fonologi_loss = lambda_fonologi * (fonologi_loss / F_count)

        return ce_main + aux_loss + fonologi_loss

    # ------------------------------------------------------------------
    # Total loss — alias lama untuk kompatibilitas (Requirement 11.3)
    # L_total = L_gloss + λ₁·L_handshape + λ₂·L_lokasi + λ₃·L_gerak
    # ------------------------------------------------------------------

    @staticmethod
    def total_loss(
        gloss_loss: torch.Tensor,
        phono_losses: dict,
        lambdas: dict,
    ) -> torch.Tensor:
        """
        L_total = L_gloss + λ₁·L_handshape + λ₂·L_lokasi + λ₃·L_gerak

        Parameters
        ----------
        gloss_loss   : scalar tensor
        phono_losses : dict dengan kunci 'handshape', 'lokasi', 'arah_gerak'
        lambdas      : dict dengan kunci 'handshape', 'lokasi', 'arah_gerak'

        Returns
        -------
        Scalar tensor.
        """
        total = gloss_loss
        for key in ["handshape", "lokasi", "arah_gerak"]:
            if key in phono_losses and key in lambdas:
                total = total + lambdas[key] * phono_losses[key]
        return total

    # ------------------------------------------------------------------
    # Knowledge distillation loss (Requirement 14.2)
    # Kontrak: α=0.5, T=4 (tidak boleh berubah)
    # ℒ = α*CE(y,s) + (1-α)*T²*KL(σ(t/T) ‖ σ(s/T))
    # ------------------------------------------------------------------

    @staticmethod
    def distillation_loss(
        student_logits: torch.Tensor,
        teacher_logits: torch.Tensor,
        hard_labels: torch.Tensor,
        alpha: float = 0.5,       # kontrak: α=0.5 (tidak boleh berubah)
        temperature: float = 4.0, # kontrak: T=4   (tidak boleh berubah)
    ) -> torch.Tensor:
        """
        ℒ = α*CE(y,s) + (1-α)*T²*KL(σ(t/T) ‖ σ(s/T))

        Parameters
        ----------
        student_logits : [B, num_classes]
        teacher_logits : [B, num_classes]
        hard_labels    : [B]  (int64)
        alpha          : float ∈ [0.0, 1.0]  — bobot CE hard labels (default 0.5, kontrak)
        temperature    : float ∈ [1.0, 10.0] — softmax temperature (default 4.0, kontrak)

        Raises
        ------
        ConfigValidationError
            Jika alpha atau temperature di luar rentang valid.
        """
        if not (0.0 <= alpha <= 1.0):
            raise ConfigValidationError("alpha", alpha, "[0.0, 1.0]")
        if not (1.0 <= temperature <= 10.0):
            raise ConfigValidationError("temperature", temperature, "[1.0, 10.0]")

        # Soft loss: T²·KL(σ(t/T) ‖ σ(s/T))
        soft_loss = F.kl_div(
            F.log_softmax(student_logits / temperature, dim=1),
            F.softmax(teacher_logits / temperature, dim=1),
            reduction="batchmean",
        ) * (temperature ** 2)

        # Hard loss: CE(y, s)
        hard_loss = F.cross_entropy(student_logits, hard_labels)

        return alpha * hard_loss + (1.0 - alpha) * soft_loss
