"""
config_validator.py — Centralised configuration validation for SignBridge ID–PH.

Task 8.4.
Requirements: 7.5, 10.3, 10.4, 11.3, 12.1, 14.2.

Validates ALL configuration parameters at load time:
  - num_blocks      ∈ [4, 20]
  - hidden_dim      ∈ [128, 512]
  - num_heads       ∈ [1, 16]
  - label_smoothing ∈ [0.0, 1.0)
  - lambda values   ∈ [0.0, 1.0]
  - base_lr         ∈ [1e-5, 1e-2]
  - alpha           ∈ [0.0, 1.0]  — default kontrak: 0.5 (tidak boleh berubah)
  - temperature     ∈ [1.0, 10.0] — default kontrak: 4.0 (tidak boleh berubah)
  - num_keypoints   harus == 86   (kontrak ONNX)
  - t_max           harus == 64   (kontrak ONNX)

Raises ConfigValidationError with the parameter name and valid range.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.exceptions import ConfigValidationError


# ---------------------------------------------------------------------------
# Range definitions (single source of truth)
# ---------------------------------------------------------------------------

VALID_RANGES: Dict[str, tuple] = {
    "num_blocks": (4, 20),          # inclusive both ends
    "hidden_dim": (128, 512),       # inclusive both ends
    "num_heads": (1, 16),            # inclusive both ends
    "label_smoothing": (0.0, 1.0),  # [0.0, 1.0) — upper exclusive
    "base_lr": (1e-5, 1e-2),         # inclusive both ends
    "alpha": (0.0, 1.0),             # inclusive both ends
    "temperature": (1.0, 10.0),     # inclusive both ends
}

# Lambda values: [0.0, 1.0] inclusive both ends
LAMBDA_KEYS = ["lambda_handshape", "lambda_lokasi", "lambda_arah_gerak"]


# ---------------------------------------------------------------------------
# ConfigValidator — Task 8.4
# ---------------------------------------------------------------------------

class ConfigValidator:
    """
    Centralised configuration validator.

    Usage:
        config = yaml.safe_load(open("configs/train_bisindo.yaml"))
        ConfigValidator.validate(config)  # raises on first invalid param
    """

    # ------------------------------------------------------------------
    # Individual validators
    # ------------------------------------------------------------------

    @staticmethod
    def validate_num_blocks(value: Any) -> None:
        """num_blocks ∈ [4, 20]."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError("num_blocks", value, "[4, 20]")
        if not (4 <= value <= 20):
            raise ConfigValidationError("num_blocks", value, "[4, 20]")

    @staticmethod
    def validate_hidden_dim(value: Any) -> None:
        """hidden_dim ∈ [128, 512]."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError("hidden_dim", value, "[128, 512]")
        if not (128 <= value <= 512):
            raise ConfigValidationError("hidden_dim", value, "[128, 512]")

    @staticmethod
    def validate_num_heads(value: Any) -> None:
        """num_heads ∈ [1, 16]."""
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigValidationError("num_heads", value, "[1, 16]")
        if not (1 <= value <= 16):
            raise ConfigValidationError("num_heads", value, "[1, 16]")

    @staticmethod
    def validate_label_smoothing(value: Any) -> None:
        """label_smoothing ∈ [0.0, 1.0)."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError("label_smoothing", value, "[0.0, 1.0)")
        if not (0.0 <= float(value) < 1.0):
            raise ConfigValidationError("label_smoothing", value, "[0.0, 1.0)")

    @staticmethod
    def validate_lambda(key: str, value: Any) -> None:
        """Lambda values ∈ [0.0, 1.0]."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError(key, value, "[0.0, 1.0]")
        if not (0.0 <= float(value) <= 1.0):
            raise ConfigValidationError(key, value, "[0.0, 1.0]")

    @staticmethod
    def validate_base_lr(value: Any) -> None:
        """base_lr ∈ [1e-5, 1e-2]."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError("base_lr", value, "[1e-5, 1e-2]")
        if not (1e-5 <= float(value) <= 1e-2):
            raise ConfigValidationError("base_lr", value, "[1e-5, 1e-2]")

    @staticmethod
    def validate_alpha(value: Any) -> None:
        """alpha (distillation) ∈ [0.0, 1.0]."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError("alpha", value, "[0.0, 1.0]")
        if not (0.0 <= float(value) <= 1.0):
            raise ConfigValidationError("alpha", value, "[0.0, 1.0]")

    @staticmethod
    def validate_temperature(value: Any) -> None:
        """temperature ∈ [1.0, 10.0]."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigValidationError("temperature", value, "[1.0, 10.0]")
        if not (1.0 <= float(value) <= 10.0):
            raise ConfigValidationError("temperature", value, "[1.0, 10.0]")

    # ------------------------------------------------------------------
    # Full config validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate(config: dict) -> None:
        """
        Validate an entire configuration dict (as loaded from YAML).

        Checks all model + training + distillation parameters.
        Raises ConfigValidationError on the first invalid parameter found.
        """
        # --- Model section ---
        model = config.get("model", {})

        # Stream_A
        stream_a = model.get("stream_a", {})
        if "num_blocks" in stream_a:
            ConfigValidator.validate_num_blocks(stream_a["num_blocks"])
        if "hidden_dim" in stream_a:
            ConfigValidator.validate_hidden_dim(stream_a["hidden_dim"])
        if "num_heads" in stream_a:
            ConfigValidator.validate_num_heads(stream_a["num_heads"])

        # Gloss head
        gloss_head = model.get("gloss_head", {})
        if "label_smoothing" in gloss_head:
            ConfigValidator.validate_label_smoothing(gloss_head["label_smoothing"])

        # Phonological head lambdas (mendukung kunci lama dan baru)
        phono = model.get("phonological_head", model.get("fonologi_head", {}))
        for lk in LAMBDA_KEYS:
            if lk in phono:
                ConfigValidator.validate_lambda(lk, phono[lk])

        # --- Training section ---
        training = config.get("training", {})
        if "base_lr" in training:
            ConfigValidator.validate_base_lr(training["base_lr"])

        # --- Distillation section ---
        distillation = config.get("distillation", {})
        if "alpha" in distillation:
            ConfigValidator.validate_alpha(distillation["alpha"])
        if "temperature" in distillation:
            ConfigValidator.validate_temperature(distillation["temperature"])

        # --- Kontrak ONNX: num_keypoints harus 86, t_max harus 64 ---
        stream_a_check = model.get("stream_a", {})
        if "num_keypoints" in stream_a_check:
            if stream_a_check["num_keypoints"] != 86:
                raise ConfigValidationError(
                    "num_keypoints",
                    stream_a_check["num_keypoints"],
                    "86 (kontrak ONNX tidak boleh berubah)"
                )
        if "t_max" in model:
            if model["t_max"] != 64:
                raise ConfigValidationError(
                    "t_max",
                    model["t_max"],
                    "64 (kontrak ONNX tidak boleh berubah)"
                )
