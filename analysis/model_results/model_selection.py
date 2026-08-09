"""Shared, editable model selection for paper-scale result figures.

This is the full set of models with matching v0--v2 outputs in the supplied
Drive archive as of 8 August 2026. Figure scripts preserve the order and omit
an entry only when its complete all-round result files are unavailable.
"""

from __future__ import annotations


PAPER_MODEL_ORDER: tuple[str, ...] = (
    "gemini-3.1-pro-preview",
    "GPT5.5-search",
    "deepseek-v4-pro-thinking",
    "deepseek-v4-pro",
    "Apertus-v1.5-70B",
    "Apertus-v1.5-8B",
    "Apertus-70B-Instruct-2509",
    "Apertus-8B-Instruct-2509",
    "EuroLLM-22B-Instruct-2512",
    "Tiny-Aya water",
    "Tiny-Aya earth",
    "Tiny-Aya fire",
)


def paper_models_available(available_models: set[str]) -> list[str]:
    """Return selected models that are available, in paper display order."""
    return [model for model in PAPER_MODEL_ORDER if model in available_models]
