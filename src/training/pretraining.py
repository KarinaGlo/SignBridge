"""
pretraining.py — Pretraining pipeline on WLASL for SignBridge BISINDO.

Task 8.8.
Requirements: 12.1, 12.2, 12.3.

Pipeline:
  1. Load configs/train_wlasl.yaml
  2. Build SignBridgeModel (Teacher) with WLASL config (num_classes=2006,
     use_phonological_head=False)
  3. Train on WLASL with differential LR and early stopping
  4. Save best checkpoint based on Top-1 validation on WLASL
  5. Log warning if Top-1 < 60% on WLASL-100 after all epochs (no halt)

Usage::

    from src.training.pretraining import PretrainingPipeline

    pipeline = PretrainingPipeline(config_path="configs/train_wlasl.yaml")
    pipeline.run(train_loader, val_loader)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.exceptions import ConfigValidationError
from src.training.config_validator import ConfigValidator
from src.training.trainer import Trainer, TrainerConfig
from src.training.logging import TrainingLogger
from src.training.evaluation import Evaluator


# ---------------------------------------------------------------------------
# PretrainingPipeline — Task 8.8
# ---------------------------------------------------------------------------

class PretrainingPipeline:
    """
    Pretraining pipeline on WLASL.

    Loads ``configs/train_wlasl.yaml``, validates all configuration
    parameters, builds the model + trainer, and runs the training loop.
    """

    WLASL100_TOP1_THRESHOLD: float = 0.60  # Requirement 12.2

    def __init__(self, config_path: str | Path = "configs/train_wlasl.yaml"):
        self.config_path = Path(config_path)

        # Load YAML config
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

        # Validate all config parameters (Requirement 7.5, 10.3, etc.)
        ConfigValidator.validate(self.config)

        # Extract training section
        training_cfg = self.config.get("training", {})
        self.trainer_config = TrainerConfig(
            base_lr=training_cfg.get("base_lr", 1e-4),
            pretrained_lr_factor=training_cfg.get("pretrained_lr_factor", 0.1),
            early_stopping_patience=training_cfg.get("early_stopping_patience", 10),
            max_checkpoints=training_cfg.get("max_checkpoints", 3),
            max_epochs=training_cfg.get("max_epochs", 50),
            seed=self.config.get("seed", 42),
            label_smoothing=self.config.get("model", {})
            .get("gloss_head", {})
            .get("label_smoothing", 0.1),
            use_phonological_head=self.config.get("model", {})
            .get("use_phonological_head", False),
        )

        # Paths
        paths = self.config.get("paths", {})
        self.checkpoint_dir = Path(paths.get("checkpoint_dir", "checkpoints/wlasl"))
        self.log_dir = Path(paths.get("log_dir", "logs/wlasl"))

        # Model config
        self.model_config = self.config.get("model", {})
        self.num_classes = self.model_config.get("num_classes", 2006)

    def build_model(self):
        """
        Build the SignBridgeModel (Teacher) from the WLASL config.

        Returns the model instance (not yet trained).
        """
        from src.model.signbridge_model import (
            SignBridgeModel,
            ModelConfig,
            StreamAConfig,
            StreamBConfig,
            FusionConfig,
            GlossHeadConfig,
            PhonologicalHeadConfig,
        )

        m = self.model_config
        sa = m.get("stream_a", {})
        sb = m.get("stream_b", {})
        fus = m.get("fusion", {})
        gh = m.get("gloss_head", {})
        ph = m.get("phonological_head", {})

        model_config = ModelConfig(
            num_classes=self.num_classes,
            use_phonological_head=m.get("use_phonological_head", False),
            stream_a=StreamAConfig(
                arch=sa.get("arch", "stgcn"),
                num_blocks=sa.get("num_blocks", 10),
                hidden_dim=sa.get("hidden_dim", 256),
                num_heads=sa.get("num_heads", 8),
            ),
            stream_b=StreamBConfig(
                arch=sb.get("arch", "videomae"),
                pretrained_url=sb.get("pretrained_url", ""),
                frozen_layers=sb.get("frozen_layers", []),
            ),
            fusion=FusionConfig(
                dim=fus.get("dim", 512),
                num_heads=fus.get("num_heads", 8),
            ),
            gloss_head=GlossHeadConfig(
                in_dim=512,
                label_smoothing=gh.get("label_smoothing", 0.1),
            ),
            phonological_head=PhonologicalHeadConfig(
                in_dim=512,
                num_handshape=ph.get("num_handshape", 20),
                num_lokasi=ph.get("num_lokasi", 10),
                num_arah_gerak=ph.get("num_arah_gerak", 8),
            ),
        )
        return SignBridgeModel(model_config)

    def run(
        self,
        train_loader=None,
        val_loader=None,
        wandb_project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full pretraining pipeline.

        Returns a dict with final metrics and checkpoint paths.

        This is a high-level orchestrator.  When called with real
        DataLoaders it runs the full training loop; when called without
        them it returns the pipeline configuration for inspection.
        """
        model = self.build_model()

        trainer = Trainer(
            model=model,
            config=self.trainer_config,
            checkpoint_dir=self.checkpoint_dir,
            num_classes=self.num_classes,
        )

        # Save experiment config before training (Requirement 20.4)
        trainer.save_experiment_config(
            self.checkpoint_dir / "experiment_config.yaml"
        )

        logger = TrainingLogger(
            log_dir=self.log_dir,
            wandb_project=wandb_project,
            experiment_name="wlasl_pretraining",
        )

        results: Dict[str, Any] = {
            "config_path": str(self.config_path),
            "num_classes": self.num_classes,
            "checkpoint_dir": str(self.checkpoint_dir),
        }

        if train_loader is not None and val_loader is not None:
            history = trainer.train(train_loader, val_loader, logger=logger)
            results["history"] = history

            # Requirement 12.2: log warning if Top-1 < 60% on WLASL-100
            final_top1 = max(
                (h.get("val_top1", 0.0) for h in history),
                default=0.0,
            )
            if final_top1 < self.WLASL100_TOP1_THRESHOLD:
                print(
                    f"[Pretraining] WARNING: Top-1 ({final_top1:.4f}) "
                    f"< {self.WLASL100_TOP1_THRESHOLD:.2f} on WLASL-100. "
                    f"Pretraining mungkin belum konvergen."
                )
                results["warning"] = (
                    f"Top-1 {final_top1:.4f} < threshold "
                    f"{self.WLASL100_TOP1_THRESHOLD:.2f}"
                )
        else:
            results["status"] = "configured (no data loaders provided)"

        logger.close()
        return results
