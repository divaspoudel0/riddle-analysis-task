"""Load and derive the scored, complete-coverage model-result frame."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from analysis.constants import MODEL_RESULTS_TIDY_CSV, TOPICS
from analysis.model_results.metrics import add_derived_columns
from analysis.model_results.model_selection import paper_models_available

DATA_PATH = MODEL_RESULTS_TIDY_CSV


def load_scored_results(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load selected models with complete current-corpus coverage."""
    results = add_derived_columns(pd.read_csv(path))
    if not results["is_scored"].any():
        raise ValueError(
            "No recorded judge verdicts found. Run a scorer on the raw model "
            "results before generating accuracy figures."
        )
    coverage = results.groupby("model_display")["riddle_id"].nunique()
    if coverage.max() != 6099:
        raise ValueError(f"Expected 6,099 scored riddles; found {coverage.max():,}")
    complete = results[results["model_display"].isin(coverage[coverage == 6099].index)]
    selected = paper_models_available(set(complete["model_display"]))
    return complete[complete["model_display"].isin(selected)].copy()


def canonical_topic(riddle_id: str) -> str:
    """Recover a benchmark topic from an immutable riddle identifier."""
    match = re.search(
        r"_(arts|everyday_life|geography|history|kids_world|national_heritage|politics|sports)_\d+$",
        riddle_id,
    )
    return (
        "Wildcard"
        if match is None
        else match.group(1)
        .replace("_", " ")
        .title()
        .replace("Kids World", "Kid's World")
    )


def performance_order(results: pd.DataFrame) -> list[str]:
    """Order models from highest to lowest strict match rate."""
    return list(
        results.groupby("model_display")["is_correct"]
        .mean()
        .sort_values(ascending=False)
        .index
    )


def match_rates(
    results: pd.DataFrame, group_column: str, group_order: tuple[str, ...]
) -> pd.DataFrame:
    """Return numeric strict-match rates by model and corpus group.

    Pandas 3 may preserve Arrow extension dtypes through ``groupby().mean()``
    and ``unstack()``. Matplotlib expects a real numeric ndarray, so the
    shared aggregation boundary normalizes the result to float64 once for all
    model-performance heatmaps.
    """
    rates = (
        results.groupby(["model_display", group_column])["is_correct"]
        .mean()
        .unstack(group_column)
        .reindex(index=performance_order(results), columns=group_order)
    )
    return rates.astype("float64")


def topic_rates(results: pd.DataFrame) -> pd.DataFrame:
    """Return strict match rates by model and current topic taxonomy."""
    frame = results.assign(topic=results["riddle_id"].map(canonical_topic))
    return match_rates(frame, "topic", TOPICS)
