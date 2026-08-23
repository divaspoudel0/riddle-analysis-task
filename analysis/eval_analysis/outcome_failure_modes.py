"""Plot reproducible human-evaluation outcome and failure compositions.

The input is Henry's row-level human-evaluation export. It must provide a
``model_display`` (or ``model_name``) column, numeric ``score`` (0--3), and,
when available, a detailed annotation label such as ``error_type_label``.
Pending annotations are excluded rather than inferred. The detailed taxonomy
is deliberately defined here so a fresh human-evaluation export can regenerate
the paper figure without using a screenshot.

Usage:
    python -m analysis.eval_analysis.outcome_failure_modes [INPUT]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from analysis.constants import figure_stem
from analysis.eval_analysis.data import FLAT_CSV
from analysis.style import PALETTE, apply_style, save_figure_pair

OUTCOME_ORDER: tuple[str, ...] = (
    "Exact match",
    "Different valid answer",
    "Correct, in English",
    "Other correct",
    "Closely related culture",
    "Wrong level of detail",
    "Surface pattern matching",
    "Other partial",
    "Hallucinated",
    "Right category, wrong entity",
    "Too broad",
    "Other incorrect",
    "Declined to answer",
    "Placeholder",
    "Empty output",
)


def _shade(color: str, alpha: float) -> tuple[float, float, float, float]:
    """Return a style-palette colour with a consistent transparency level."""
    return mcolors.to_rgba(color, alpha=alpha)


OUTCOME_COLORS: dict[str, tuple[float, float, float, float]] = {
    "Exact match": _shade(PALETTE["bluish_green"], 1.0),
    "Different valid answer": _shade(PALETTE["bluish_green"], 0.78),
    "Correct, in English": _shade(PALETTE["bluish_green"], 0.56),
    "Other correct": _shade(PALETTE["bluish_green"], 0.34),
    "Closely related culture": _shade(PALETTE["orange"], 1.0),
    "Wrong level of detail": _shade(PALETTE["orange"], 0.76),
    "Surface pattern matching": _shade(PALETTE["orange"], 0.52),
    "Other partial": _shade(PALETTE["orange"], 0.28),
    "Hallucinated": _shade(PALETTE["vermillion"], 1.0),
    "Right category, wrong entity": _shade(PALETTE["vermillion"], 0.76),
    "Too broad": _shade(PALETTE["vermillion"], 0.52),
    "Other incorrect": _shade(PALETTE["vermillion"], 0.24),
    "Declined to answer": _shade(PALETTE["blue"], 0.80),
    "Placeholder": _shade(PALETTE["grey"], 0.70),
    "Empty output": _shade(PALETTE["light_grey"], 1.0),
}

OUTCOME_HATCHES = {"Placeholder": "///", "Empty output": "//"}

OUTCOME_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Correct", OUTCOME_ORDER[:4]),
    ("Partial", OUTCOME_ORDER[4:8]),
    ("Incorrect", OUTCOME_ORDER[8:12]),
    ("Uncertain or no answer", OUTCOME_ORDER[12:]),
)


def _draw_grouped_legend(fig: plt.Figure) -> None:
    """Add the compact grouped outcome key used by the wide paper figure."""
    x_positions = (0.19, 0.39, 0.60, 0.82)
    for (heading, outcomes), x_position in zip(
        OUTCOME_GROUPS, x_positions, strict=True
    ):
        fig.text(
            x_position,
            0.925,
            heading,
            fontsize=7.2,
            fontweight="bold",
            color=PALETTE["black"],
        )
        for row, outcome in enumerate(outcomes):
            y_position = 0.895 - row * 0.027
            fig.add_artist(
                Rectangle(
                    (x_position, y_position - 0.009),
                    0.015,
                    0.015,
                    transform=fig.transFigure,
                    facecolor=OUTCOME_COLORS[outcome],
                    edgecolor="white",
                    linewidth=0.25,
                    hatch=OUTCOME_HATCHES.get(outcome),
                )
            )
            fig.text(x_position + 0.02, y_position, outcome, fontsize=6.5, va="center")


def _annotation_text(frame: pd.DataFrame) -> pd.Series:
    """Combine optional human annotation fields into normalized text."""
    columns = [
        column
        for column in ("error_type_label", "error_type", "outcome_label", "label")
        if column in frame
    ]
    if not columns:
        return pd.Series("", index=frame.index, dtype="string")
    return frame[columns].fillna("").astype(str).agg(" ".join, axis=1).str.lower()


def _response_text(frame: pd.DataFrame) -> pd.Series:
    """Combine optional answer fields used to identify abstentions and blanks."""
    columns = [
        column
        for column in ("model_answer", "answer_text", "answer", "response")
        if column in frame
    ]
    if not columns:
        return pd.Series("", index=frame.index, dtype="string")
    return frame[columns].fillna("").astype(str).agg(" ".join, axis=1).str.lower()


def classify_outcomes(frame: pd.DataFrame) -> pd.Series:
    """Classify human-evaluated responses into the detailed paper taxonomy."""
    if "score" not in frame:
        raise ValueError("Human-evaluation input must contain a 'score' column.")
    score = pd.to_numeric(frame["score"], errors="coerce")
    labels = _annotation_text(frame)
    answers = _response_text(frame)
    methods = frame.get(
        "scoring_method", pd.Series("", index=frame.index, dtype="string")
    ).fillna("")
    outcome = pd.Series("Other incorrect", index=frame.index, dtype="string")

    correct = score.eq(3)
    # A top score without an alternate-answer code is the deterministic exact
    # match bucket.  Human annotation only adds the non-exact 3.1--3.3 detail.
    outcome.loc[correct] = "Exact match"
    outcome.loc[correct & labels.str.contains("english", regex=False)] = (
        "Correct, in English"
    )
    outcome.loc[
        correct
        & labels.str.contains(
            "different|valid|alternative|synonym|translation", regex=True
        )
    ] = "Different valid answer"
    outcome.loc[correct & labels.str.contains(r"3\.3|other correct", regex=True)] = (
        "Other correct"
    )

    partial = score.eq(2)
    outcome.loc[partial] = "Other partial"
    outcome.loc[
        partial & labels.str.contains("related.*culture|culture.*related", regex=True)
    ] = "Closely related culture"
    outcome.loc[partial & labels.str.contains("level.*detail|detail", regex=True)] = (
        "Wrong level of detail"
    )
    outcome.loc[partial & labels.str.contains("surface|pattern", regex=True)] = (
        "Surface pattern matching"
    )

    incorrect = score.eq(0)
    outcome.loc[incorrect & labels.str.contains("hallucin", regex=True)] = (
        "Hallucinated"
    )
    outcome.loc[
        incorrect
        & labels.str.contains("wrong entity|right category|category", regex=True)
    ] = "Right category, wrong entity"
    outcome.loc[incorrect & labels.str.contains("too broad|broad", regex=True)] = (
        "Too broad"
    )

    uncertain = score.eq(1)
    outcome.loc[uncertain] = "Declined to answer"
    placeholder = labels.str.contains(
        "placeholder", regex=False
    ) | answers.str.contains("placeholder", regex=False)
    answer_columns = {"answer_text", "answer", "response"} & set(frame.columns)
    empty = labels.str.contains("empty", regex=False)
    if answer_columns:
        empty |= answers.str.strip().eq("")
    outcome.loc[uncertain & placeholder] = "Placeholder"
    outcome.loc[uncertain & empty & ~placeholder] = "Empty output"

    # The flat-file automatic non-response rules are authoritative.  They
    # arrive as score-0 rows, so applying them only inside score-1 uncertainty
    # would silently misclassify them as ordinary incorrect answers.
    outcome.loc[methods.eq("auto_placeholder")] = "Placeholder"
    outcome.loc[methods.eq("auto_empty")] = "Empty output"
    return outcome


def outcome_shares(frame: pd.DataFrame) -> pd.DataFrame:
    """Return 100%-stacked detailed outcome shares for each model."""
    model_column = "model_display" if "model_display" in frame else "model_name"
    if model_column not in frame:
        raise ValueError(
            "Human-evaluation input needs 'model_display' or 'model_name'."
        )
    scored = frame.copy()
    if "scoring_method" in scored:
        scored = scored[~scored["scoring_method"].eq("pending_human_eval")].copy()
    scored = scored[scored["score"].notna()].copy()
    scored["outcome"] = classify_outcomes(scored)
    shares = (
        scored.groupby(model_column)["outcome"]
        .value_counts(normalize=True)
        .unstack(fill_value=0.0)
        .reindex(columns=OUTCOME_ORDER, fill_value=0.0)
    )
    return shares.loc[shares["Exact match"].sort_values(ascending=False).index]


def plot_outcome_composition(frame: pd.DataFrame):
    """Build the detailed human-evaluation outcome-composition figure."""
    shares = outcome_shares(frame)
    apply_style()
    fig, ax = plt.subplots(figsize=(8, 5.5))
    left = pd.Series(0.0, index=shares.index)
    for outcome in OUTCOME_ORDER:
        values = shares[outcome] * 100
        ax.barh(
            shares.index,
            values,
            left=left * 100,
            color=OUTCOME_COLORS[outcome],
            edgecolor="white",
            linewidth=0.35,
            hatch=OUTCOME_HATCHES.get(outcome),
        )
        left += shares[outcome]
    ax.set(xlim=(0, 100), xlabel="Share of scored attempts (%)")
    fig.text(
        0.19,
        0.975,
        "Outcome and failure mode composition by model",
        fontsize=10,
        fontweight="bold",
    )
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=7.5)
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    _draw_grouped_legend(fig)
    fig.subplots_adjust(left=0.19, right=0.99, bottom=0.095, top=0.80)
    return fig


def load_input(path: Path) -> pd.DataFrame:
    """Load a CSV or Parquet human-evaluation export."""
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    raise ValueError("Input must be a .csv or .parquet human-evaluation export.")


def main(path: Path = FLAT_CSV) -> None:
    """Write the human-evaluation outcome-composition figure."""
    fig = plot_outcome_composition(load_input(path))
    output = figure_stem("eval_analysis", "outcome_failure_mode_composition")
    pdf_path, png_path = save_figure_pair(fig, output, bbox_inches=fig.bbox_inches)
    plt.close(fig)
    print(f"Wrote {pdf_path} and {png_path}")


def cli() -> None:
    """Parse an optional input path for command-line use."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=FLAT_CSV)
    main(parser.parse_args().input)


if __name__ == "__main__":
    cli()
