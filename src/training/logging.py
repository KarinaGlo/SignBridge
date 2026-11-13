"""
logging.py — TensorBoard + Weights & Biases logging for SignBridge BISINDO.

Task 8.6.
Requirements: 12.5.

Provides a unified ``TrainingLogger`` that writes to both TensorBoard and W&B
simultaneously.  Both backends are optional — if either is not installed or
not configured, the logger falls back gracefully.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# TrainingLogger — Task 8.6
# ---------------------------------------------------------------------------

class TrainingLogger:
    """
    Unified logger for TensorBoard and Weights & Biases.

    Both backends are optional:
      - If ``tensorboard`` is available, a SummaryWriter is created.
      - If ``wandb`` is available and ``wandb_project`` is given, W&B is initialised.
      - If either is missing, logging continues silently (graceful fallback).

    Usage::

        logger = TrainingLogger(log_dir="logs/bisindo", wandb_project="signbridge")
        logger.log_scalar("train/loss", 0.42, step=1)
        logger.log_metrics({"val/top1": 0.85}, step=10)
        logger.close()
    """

    def __init__(
        self,
        log_dir: str | Path = "logs",
        wandb_project: Optional[str] = None,
        wandb_config: Optional[Dict[str, Any]] = None,
        experiment_name: str = "signbridge",
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_name = experiment_name

        # --- TensorBoard (graceful fallback) ---
        self._tb_writer = None
        try:
            from torch.utils.tensorboard import SummaryWriter
            self._tb_writer = SummaryWriter(log_dir=str(self.log_dir))
        except Exception:
            pass  # TensorBoard not available — continue without it

        # --- Weights & Biases (graceful fallback) ---
        self._wandb_run = None
        if wandb_project is not None:
            try:
                import wandb
                self._wandb_run = wandb.init(
                    project=wandb_project,
                    config=wandb_config or {},
                    name=experiment_name,
                    dir=str(self.log_dir),
                )
            except Exception:
                pass  # W&B not available or not logged in — continue without it

    # ------------------------------------------------------------------
    # Scalar logging
    # ------------------------------------------------------------------

    def log_scalar(self, tag: str, value: float, step: int) -> None:
        """Log a single scalar to both backends."""
        if self._tb_writer is not None:
            self._tb_writer.add_scalar(tag, value, step)
        if self._wandb_run is not None:
            import wandb
            wandb.log({tag: value}, step=step)

    def log_metrics(self, metrics: Dict[str, float], step: int) -> None:
        """Log a dict of scalars to both backends."""
        if self._tb_writer is not None:
            for tag, value in metrics.items():
                self._tb_writer.add_scalar(tag, value, step)
        if self._wandb_run is not None:
            import wandb
            wandb.log(metrics, step=step)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Flush and close both backends."""
        if self._tb_writer is not None:
            self._tb_writer.close()
        if self._wandb_run is not None:
            import wandb
            wandb.finish()

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "TrainingLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Properties for testing
    # ------------------------------------------------------------------

    @property
    def tensorboard_available(self) -> bool:
        return self._tb_writer is not None

    @property
    def wandb_available(self) -> bool:
        return self._wandb_run is not None
