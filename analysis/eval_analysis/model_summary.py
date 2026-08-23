"""Summarize the 24-model human-evaluation snapshot by model and community.

The human-correct values and community extremes come directly from the local
``model_riddle_results_flat.csv``.  Exact-match values are read from the
versioned dashboard snapshot because the flat file intentionally stores only
the human adjudication for manually reviewed rows; its companion automatic
judge verdict is not part of this export.

Run after replacing the flat file::

    uv run --project analysis python -m analysis.eval_analysis.model_summary
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis.constants import CORPUS_METADATA_PATH, FIGURES_DIR
from analysis.eval_analysis.data import (
    EXCLUDED_RIDDLES,
    FLAT_CSV,
    MODEL_NAME_MAP,
)
from analysis.model_results.leaderboard import load_human_eval_leaderboard

OUTPUT_CSV = FIGURES_DIR / "e_human_eval_model_summary.csv"
STRICT_SCORE = 3.0
COMPLETE_THRESHOLD = 99.0

# These are API-only models in the evaluated closed-book roster.  The remaining
# models have publicly available weights.  Keep this explicit: licensing is a
# model attribute, not something inferred from a model name at runtime.
PROPRIETARY_MODELS = {
    "Amazon Nova Lite v1",
    "Amazon Nova Micro v1",
    "GPT5.5 [high]",
    "GPT5.5 [none]",
    "Gemini 2.5 Flash",
    "Gemini 2.5 Flash Lite",
    "claude-opus-4-7 [none]",
    "claude-opus-4-7 [thinking]",
    "gemini-3.1-pro-preview",
}


def complete_communities(frame: pd.DataFrame) -> set[str]:
    """Return communities whose eligible human evaluation is at least 99% done."""
    coverage = (
        frame.assign(
            human_done=frame["scoring_method"].eq("human_eval"),
            pending=frame["scoring_method"].eq("pending_human_eval"),
        )
        .groupby("community")[["human_done", "pending"]]
        .sum()
    )
    eligible = coverage["human_done"] + coverage["pending"]
    percent_complete = coverage["human_done"].div(eligible.where(eligible > 0)) * 100
    return set(percent_complete[percent_complete >= COMPLETE_THRESHOLD].index)


def build_summary(flat_csv: Path = FLAT_CSV) -> pd.DataFrame:
    """Build the 24-row human-evaluation model summary.

    Args:
        flat_csv: Human-evaluation export with the canonical model and
            community identifiers.

    Returns:
        One row per evaluated model. Percentage columns are on a 0--100 scale.
    """
    frame = pd.read_csv(flat_csv, low_memory=False)
    frame = frame[~frame["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    frame["model"] = frame["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(frame.loc[frame["model"].isna(), "model_name"].unique())
    if unmapped:
        raise ValueError(f"Unmapped human-evaluation models: {unmapped}")

    canonical_communities = set(pd.read_csv(CORPUS_METADATA_PATH)["community"])
    unknown_communities = set(frame["community"]) - canonical_communities
    if unknown_communities:
        raise ValueError(
            f"Communities missing from corpus_metadata.csv: {unknown_communities}"
        )

    complete = complete_communities(frame)
    scored = frame[
        frame["community"].isin(complete)
        & ~frame["scoring_method"].eq("pending_human_eval")
    ].copy()
    scored["human_correct"] = scored["score"].eq(STRICT_SCORE)

    per_model = scored.groupby("model", as_index=False).agg(
        human_correct=("human_correct", "mean"),
        n=("human_correct", "size"),
    )
    per_model["human_correct"] *= 100

    per_community = scored.groupby(["model", "community"], as_index=False).agg(
        human_correct=("human_correct", "mean"),
    )
    per_community["human_correct"] *= 100
    best = (
        per_community.sort_values(
            ["model", "human_correct", "community"], ascending=[True, False, True]
        )
        .drop_duplicates("model")
        .rename(
            columns={
                "community": "community_with_highest_accuracy",
                "human_correct": "highest_community_human_correct",
            }
        )
    )
    worst = (
        per_community.sort_values(["model", "human_correct", "community"])
        .drop_duplicates("model")
        .rename(
            columns={
                "community": "community_with_lowest_accuracy",
                "human_correct": "lowest_community_human_correct",
            }
        )
    )

    exact = load_human_eval_leaderboard()[["model_display", "exact_match_accuracy"]]
    exact = exact.rename(
        columns={"model_display": "model", "exact_match_accuracy": "exact_match"}
    )
    summary = per_model.merge(exact, on="model", validate="one_to_one")
    summary = summary.merge(
        best[
            [
                "model",
                "community_with_highest_accuracy",
                "highest_community_human_correct",
            ]
        ],
        on="model",
        validate="one_to_one",
    ).merge(
        worst[
            [
                "model",
                "community_with_lowest_accuracy",
                "lowest_community_human_correct",
            ]
        ],
        on="model",
        validate="one_to_one",
    )
    summary.insert(1, "setting", "closed book")
    summary.insert(2, "is_proprietary", summary["model"].isin(PROPRIETARY_MODELS))
    summary["diff"] = (summary["human_correct"] - summary["exact_match"]).map(
        lambda value: f"{value:+.1f}pp"
    )
    summary["n_complete_communities"] = len(complete)
    summary["exact_match"] = summary["exact_match"].round(1)
    summary["human_correct"] = summary["human_correct"].round(1)
    summary["highest_community_human_correct"] = summary[
        "highest_community_human_correct"
    ].round(1)
    summary["lowest_community_human_correct"] = summary[
        "lowest_community_human_correct"
    ].round(1)
    return (
        summary[
            [
                "model",
                "setting",
                "is_proprietary",
                "exact_match",
                "human_correct",
                "diff",
                "highest_community_human_correct",
                "community_with_highest_accuracy",
                "lowest_community_human_correct",
                "community_with_lowest_accuracy",
                "n",
                "n_complete_communities",
            ]
        ]
        .rename(
            columns={
                "highest_community_human_correct": "max_community_accuracy",
                "community_with_highest_accuracy": "max_accuracy_community",
                "lowest_community_human_correct": "min_community_accuracy",
                "community_with_lowest_accuracy": "min_accuracy_community",
            }
        )
        .sort_values(
            ["human_correct", "model"], ascending=[False, True], ignore_index=True
        )
    )


def main() -> None:
    """Write the compact model-level human-evaluation CSV."""
    summary = build_summary()
    if len(summary) != 24:
        raise ValueError(f"Expected 24 human-evaluated models, found {len(summary)}.")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_CSV} ({len(summary)} models).")


if __name__ == "__main__":
    main()
