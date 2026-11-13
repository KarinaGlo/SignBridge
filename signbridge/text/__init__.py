"""Text modality package: BISINDO pseudo-gloss rules, B0/T1-T3 gloss-to-sentence, and MT0-MT3 ID-FIL translation."""

from __future__ import annotations

from typing import Any

from signbridge.text.pseudo_gloss import (
    gloss_to_sentence_rules,
    sentence_to_pseudo_gloss,
)

__all__ = [
    "sentence_to_pseudo_gloss",
    "gloss_to_sentence_rules",
    "compute_bleu",
    "compute_chrf",
    "GRUAttentionSeq2Seq",
    "run_text_experiment",
    "run_translation_eval",
]


def __getattr__(name: str) -> Any:
    """Lazy-load training and evaluation symbols so runtime inference does not require PyTorch."""
    if name in ("compute_bleu", "compute_chrf", "GRUAttentionSeq2Seq", "run_text_experiment"):
        from signbridge.text import train_text

        return getattr(train_text, name)
    if name == "run_translation_eval":
        from signbridge.text.eval_translate import run_translation_eval

        return run_translation_eval
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

