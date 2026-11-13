"""
trainer.py — Training loop for SignBridge BISINDO (pretraining + fine-tuning).

Task 8.5.
Requirements: 12.4, 13.2, 13.5, 13.6, 20.4, 20.5.

Implements:
  - Differential learning rate (pretrained layers × 0.1, new layers × 1.0)
  - Early stopping (patience=10 epochs without validation improvement)
  - Checkpoint management (max 3, replace lowest performing)
  - Resume from checkpoint (weights, optimizer state, epoch, metric history)
  - Print and save experiment_config.yaml before training starts
"""

from __future__ import annotations

import copy
import shutil
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from torch.optim import Optimizer

from src.exceptions import CheckpointNotFoundError
from src.training.losses import LossFunctions
from src.training.evaluation import Evaluator, EvaluationMetrics


# ---------------------------------------------------------------------------
# TrainerConfig dataclass
# ---------------------------------------------------------------------------

@dataclass
class TrainerConfig:
    """Configuration for the Trainer (maps to the ``training:`` section of YAML)."""
    base_lr: float = 1e-4
    pretrained_lr_factor: float = 0.1
    early_stopping_patience: int = 10
    max_checkpoints: int = 3
    max_epochs: int = 100
    seed: int = 42
    label_smoothing: float = 0.1
    # Lambda weights for phonological losses
    lambda_handshape: float = 0.3
    lambda_lokasi: float = 0.3
    lambda_arah_gerak: float = 0.3
    use_phonological_head: bool = True

    def to_dict(self) -> dict:
        return {
            "base_lr": self.base_lr,
            "pretrained_lr_factor": self.pretrained_lr_factor,
            "early_stopping_patience": self.early_stopping_patience,
            "max_checkpoints": self.max_checkpoints,
            "max_epochs": self.max_epochs,
            "seed": self.seed,
            "label_smoothing": self.label_smoothing,
            "lambda_handshape": self.lambda_handshape,
            "lambda_lokasi": self.lambda_lokasi,
            "lambda_arah_gerak": self.lambda_arah_gerak,
            "use_phonological_head": self.use_phonological_head,
        }


# ---------------------------------------------------------------------------
# Checkpoint metadata
# ---------------------------------------------------------------------------

@dataclass
class CheckpointInfo:
    """Metadata for a saved checkpoint."""
    path: Path
    epoch: int
    metric_value: float          # validation metric (higher is better)


# ---------------------------------------------------------------------------
# Trainer — Task 8.5
# ---------------------------------------------------------------------------

class Trainer:
    """
    Training loop with differential learning rate, early stopping, and
    checkpoint management.

    The full training loop requires real data and is intended to be called
    from pretraining.py / finetuning.py.  The individual components
    (optimizer setup, checkpoint save/load, early-stopping logic) are
    independently testable.
    """

    def __init__(
        self,
        model: nn.Module,
        config: TrainerConfig,
        checkpoint_dir: str | Path = "checkpoints",
        num_classes: int = 32,
        pretrained_layer_prefixes: Optional[List[str]] = None,
    ):
        """
        Parameters
        ----------
        model : nn.Module
            The SignBridgeModel (Teacher) or StudentModel.
        config : TrainerConfig
            Training hyperparameters.
        checkpoint_dir : path-like
            Directory to store checkpoints.
        num_classes : int
            Number of gloss classes (for evaluator).
        pretrained_layer_prefixes : list[str] | None
            Parameter name prefixes that belong to pretrained layers.
            Defaults to ["stream_b"] (VideoMAE / I3D backbone).
        """
        self.model = model
        self.config = config
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.num_classes = num_classes

        self.pretrained_layer_prefixes = pretrained_layer_prefixes or ["stream_b"]

        # Early-stopping state
        self._best_metric: float = -1.0
        self._patience_counter: int = 0
        self._should_stop: bool = False

        # Checkpoint registry
        self._checkpoints: List[CheckpointInfo] = []

        # Training history
        self.history: List[Dict[str, float]] = []
        self.current_epoch: int = 0

        # Build optimizer with differential LR
        self.optimizer = self._build_optimizer()

        # Evaluator
        self.evaluator = Evaluator(
            num_classes=num_classes,
            use_phonological_head=config.use_phonological_head,
        )

        # Loss function reference
        self.loss_fn = LossFunctions

    # ------------------------------------------------------------------
    # Differential learning rate (Requirement 13.2)
    # ------------------------------------------------------------------

    def _build_optimizer(self) -> Optimizer:
        """
        Build optimizer with differential learning rate.

        Pretrained layers (matching ``pretrained_layer_prefixes``) use
        ``base_lr × pretrained_lr_factor``, all other (new) layers use
        ``base_lr × 1.0``.
        """
        base_lr = self.config.base_lr
        pretrained_lr = base_lr * self.config.pretrained_lr_factor

        pretrained_params: List[torch.nn.Parameter] = []
        new_params: List[torch.nn.Parameter] = []

        for name, param in self.model.named_parameters():
            if not param.requires_grad:
                continue
            if any(name.startswith(prefix) for prefix in self.pretrained_layer_prefixes):
                pretrained_params.append(param)
            else:
                new_params.append(param)

        param_groups = [
            {"params": pretrained_params, "lr": pretrained_lr, "name": "pretrained"},
            {"params": new_params, "lr": base_lr, "name": "new"},
        ]

        return torch.optim.Adam(param_groups, lr=base_lr)

    def get_param_group_lrs(self) -> Dict[str, float]:
        """Return the learning rate for each parameter group (for testing)."""
        return {
            group["name"]: group["lr"]
            for group in self.optimizer.param_groups
            if "name" in group
        }

    # ------------------------------------------------------------------
    # Checkpoint management (Requirement 13.5, 13.6)
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        epoch: int,
        metric_value: float,
        optimizer: Optional[Optimizer] = None,
        extra: Optional[dict] = None,
    ) -> Path:
        """
        Save a checkpoint and manage the max-3 policy.

        If the number of checkpoints exceeds ``max_checkpoints``, the one
        with the lowest metric value is removed.
        """
        opt = optimizer if optimizer is not None else self.optimizer
        ckpt_path = self.checkpoint_dir / f"checkpoint_epoch{epoch:04d}.pth"

        state = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": opt.state_dict(),
            "metric_value": metric_value,
            "history": self.history,
            "config": self.config.to_dict(),
        }
        if extra:
            state.update(extra)

        torch.save(state, ckpt_path)

        info = CheckpointInfo(path=ckpt_path, epoch=epoch, metric_value=metric_value)
        self._checkpoints.append(info)

        # Enforce max_checkpoints — remove lowest performing
        if len(self._checkpoints) > self.config.max_checkpoints:
            # Find the checkpoint with the lowest metric value
            worst = min(self._checkpoints, key=lambda c: c.metric_value)
            self._checkpoints.remove(worst)
            if worst.path.exists():
                worst.path.unlink()

        return ckpt_path

    def load_checkpoint(self, path: str | Path) -> dict:
        """
        Resume from a checkpoint.

        Restores: model weights, optimizer state, epoch number, metric history.

        Raises
        ------
        CheckpointNotFoundError
            If the checkpoint path does not exist.
        """
        ckpt_path = Path(path)
        if not ckpt_path.exists():
            raise CheckpointNotFoundError(
                f"Checkpoint tidak ditemukan: {ckpt_path}"
            )

        state = torch.load(ckpt_path, map_location="cpu", weights_only=False)

        self.model.load_state_dict(state["model_state_dict"])
        self.optimizer.load_state_dict(state["optimizer_state_dict"])
        self.current_epoch = state.get("epoch", 0)
        self.history = state.get("history", [])
        self._best_metric = state.get("metric_value", -1.0)

        return state

    def list_checkpoints(self) -> List[CheckpointInfo]:
        """Return list of currently saved checkpoints."""
        return list(self._checkpoints)

    # ------------------------------------------------------------------
    # Early stopping (Requirement 12.4)
    # ------------------------------------------------------------------

    def check_early_stopping(self, current_metric: float) -> bool:
        """
        Check if training should stop early.

        Returns True if patience has been exceeded (no improvement for
        ``early_stopping_patience`` consecutive epochs).

        Parameters
        ----------
        current_metric : float
            The validation metric for the current epoch (higher is better).

        Returns
        -------
        bool : True if training should stop.
        """
        if current_metric > self._best_metric:
            self._best_metric = current_metric
            self._patience_counter = 0
            self._should_stop = False
        else:
            self._patience_counter += 1
            if self._patience_counter >= self.config.early_stopping_patience:
                self._should_stop = True

        return self._should_stop

    def reset_early_stopping(self) -> None:
        """Reset early-stopping state (for fresh training runs)."""
        self._best_metric = -1.0
        self._patience_counter = 0
        self._should_stop = False

    @property
    def best_metric(self) -> float:
        return self._best_metric

    @property
    def patience_counter(self) -> int:
        return self._patience_counter

    @property
    def should_stop(self) -> bool:
        return self._should_stop

    # ------------------------------------------------------------------
    # Experiment config (Requirement 20.4, 20.5)
    # ------------------------------------------------------------------

    def save_experiment_config(self, output_path: str | Path) -> Path:
        """
        Print and save the experiment configuration as YAML.

        This is called before training starts so the full config is recorded.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            "trainer": self.config.to_dict(),
            "num_classes": self.num_classes,
            "pretrained_layer_prefixes": self.pretrained_layer_prefixes,
            "checkpoint_dir": str(self.checkpoint_dir),
        }

        with open(out, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        print(f"[Trainer] Experiment config saved to {out}")
        return out

    # ------------------------------------------------------------------
    # Single training step (used by train loop)
    # ------------------------------------------------------------------

    def train_step(
        self,
        keypoints: torch.Tensor,
        frames: torch.Tensor,
        padding_mask: torch.Tensor,
        gloss_labels: torch.Tensor,
        phono_labels: Optional[Dict[str, torch.Tensor]] = None,
    ) -> float:
        """
        Execute a single training step (forward, loss, backward, optimizer step).

        Returns the total loss as a float.
        """
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(keypoints, frames, padding_mask)

        gloss_loss = self.loss_fn.label_smoothing_ce(
            output.gloss_logits,
            gloss_labels,
            smoothing=self.config.label_smoothing,
        )

        total = gloss_loss

        if self.config.use_phonological_head and output.phono is not None and phono_labels is not None:
            phono_losses = {
                "handshape": self.loss_fn.label_smoothing_ce(
                    output.phono["handshape_logits"],
                    phono_labels["handshape"],
                    smoothing=self.config.label_smoothing,
                ),
                "lokasi": self.loss_fn.label_smoothing_ce(
                    output.phono["lokasi_logits"],
                    phono_labels["lokasi"],
                    smoothing=self.config.label_smoothing,
                ),
                "arah_gerak": self.loss_fn.label_smoothing_ce(
                    output.phono["arah_gerak_logits"],
                    phono_labels["arah_gerak"],
                    smoothing=self.config.label_smoothing,
                ),
            }
            lambdas = {
                "handshape": self.config.lambda_handshape,
                "lokasi": self.config.lambda_lokasi,
                "arah_gerak": self.config.lambda_arah_gerak,
            }
            total = self.loss_fn.total_loss(gloss_loss, phono_losses, lambdas)

        total.backward()
        self.optimizer.step()

        return total.item()

    # ------------------------------------------------------------------
    # Full training loop (stub — requires real DataLoader)
    # ------------------------------------------------------------------

    def train(
        self,
        train_loader,
        val_loader,
        logger=None,
    ) -> List[Dict[str, float]]:
        """
        Full training loop.

        This is a stub that outlines the training flow.  In production it
        iterates over the DataLoaders, but for testing the individual
        components (optimizer, checkpoints, early stopping) are used directly.

        Returns the training history list.
        """
        self.save_experiment_config(self.checkpoint_dir / "experiment_config.yaml")

        for epoch in range(self.current_epoch, self.config.max_epochs):
            self.current_epoch = epoch

            # --- Training phase ---
            epoch_losses = []
            for batch in train_loader:
                loss = self.train_step(*batch)
                epoch_losses.append(loss)

            avg_loss = sum(epoch_losses) / max(len(epoch_losses), 1)

            # --- Validation phase (stub) ---
            # In production: iterate val_loader, accumulate logits, compute metrics
            val_top1 = 0.0  # placeholder

            # --- Early stopping check ---
            self.history.append({
                "epoch": epoch,
                "train_loss": avg_loss,
                "val_top1": val_top1,
            })

            if self.check_early_stopping(val_top1):
                print(f"[Trainer] Early stopping at epoch {epoch}")
                break

            # --- Checkpoint ---
            self.save_checkpoint(epoch, val_top1)

            if logger is not None:
                logger.log_metrics({
                    "train/loss": avg_loss,
                    "val/top1": val_top1,
                }, step=epoch)

        return self.history
