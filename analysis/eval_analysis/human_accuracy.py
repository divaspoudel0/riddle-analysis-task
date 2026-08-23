"""Generate human-evaluation accuracy figures."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis import style
from analysis.constants import figure_stem
from analysis.eval_analysis.data import coverage_report, load_human_evaluation


def prepare_frame() -> tuple[pd.DataFrame, set[str], float]:
    """Load the evaluated rows and return the complete-community subset key."""
    frame = load_human_evaluation()
    coverage = coverage_report(frame)
    complete = set(coverage[coverage["status"] == "complete"].index)
    return frame, complete, frame.attrs.get("source_mtime", 0.0)


def _save(fig: plt.Figure, name: str) -> None:
    """Save one evaluation figure under its semantic name."""
    output = figure_stem("eval_analysis", name)
    style.save_figure_pair(fig, output)
    plt.close(fig)
    print(f"Wrote {output}.pdf and {output}.png")


def plot_accuracy_distribution_by_community(
    frame: pd.DataFrame, complete: set[str]
) -> plt.Figure:
    """Plot each model's human-correct accuracy across communities."""
    style.apply_style()
    scored = frame[frame["community"].isin(complete) & ~frame["is_pending"]]
    per_community = (
        scored.groupby(["model_display", "community"])["is_correct"]
        .mean()
        .mul(100)
        .reset_index()
    )
    order = (
        per_community.groupby("model_display")["is_correct"]
        .median()
        .sort_values()
        .index.tolist()
    )
    data = [
        per_community.loc[per_community["model_display"] == model, "is_correct"].values
        for model in order
    ]

    fig, ax = plt.subplots(figsize=(7, 8.5))
    boxes = ax.boxplot(
        data,
        vert=False,
        widths=0.62,
        patch_artist=True,
        showfliers=True,
        medianprops={"color": style.PALETTE["black"], "lw": 1.4},
        flierprops={
            "marker": "o",
            "ms": 3,
            "markerfacecolor": style.PALETTE["grey"],
            "markeredgecolor": "none",
            "alpha": 0.5,
        },
        whiskerprops={"color": style.PALETTE["grey"]},
        capprops={"color": style.PALETTE["grey"]},
    )
    for box in boxes["boxes"]:
        box.set(
            facecolor=style.PALETTE["sky_blue"],
            alpha=0.55,
            edgecolor=style.PALETTE["blue"],
        )
    for position, values in enumerate(data, start=1):
        ax.plot(
            np.min(values),
            position,
            marker="D",
            ms=5,
            color=style.PALETTE["vermillion"],
            zorder=5,
        )
    ax.plot(
        [],
        [],
        "D",
        ms=5,
        color=style.PALETTE["vermillion"],
        label="Lowest-scoring community",
    )
    ax.set(
        yticks=range(1, len(order) + 1),
        yticklabels=order,
        xlim=(0, 100),
        xlabel="Human-correct accuracy in each community (%)",
        title=f"Human Accuracy Distribution Across {len(complete)} Communities",
    )
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig


def plot_accuracy_heatmap_by_community(
    frame: pd.DataFrame, complete: set[str]
) -> plt.Figure:
    """Plot human-correct accuracy for every model and complete community."""
    style.apply_style()
    scored = frame[frame["community"].isin(complete) & ~frame["is_pending"]]
    table = (
        scored.groupby(["model_display", "community"])["is_correct"]
        .mean()
        .mul(100)
        .unstack()
    )
    table = table.loc[table.mean(axis=1).sort_values(ascending=False).index]
    table = table[table.mean(axis=0).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.grid(False)
    image = ax.imshow(table.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set(
        xticks=range(len(table.columns)),
        xticklabels=table.columns,
        yticks=range(len(table.index)),
        yticklabels=table.index,
        title=f"Human-Correct Accuracy by Model and Community ({len(complete)} Communities)",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    plt.setp(ax.get_yticklabels(), fontsize=7.5)
    for row in range(table.shape[0]):
        for column in range(table.shape[1]):
            value = table.iat[row, column]
            ax.text(
                column,
                row,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=6,
                color="white" if value > 55 else style.PALETTE["black"],
            )
    colorbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    colorbar.set_label("Human-correct accuracy (%)", fontsize=9)
    fig.tight_layout()
    return fig


def plot_correct_answers_missed_by_exact_match(
    frame: pd.DataFrame, complete: set[str]
) -> plt.Figure:
    """Plot the share of human-correct answers missed by exact matching."""
    style.apply_style()
    scored = frame[
        frame["is_human"]
        & frame["community"].isin(complete)
        & frame["is_exact_match"].notna()
        & frame["is_correct"]
    ].copy()
    missed = (
        scored.assign(missed=scored["is_exact_match"].eq(False))
        .groupby("model_display")["missed"]
        .mean()
        .mul(100)
        .sort_values()
    )
    positions = range(len(missed))
    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.barh(positions, missed.values, color=style.PALETTE["orange"])
    ax.set(
        yticks=list(positions),
        yticklabels=missed.index,
        xlabel="Human-correct answers missed by exact match (%)",
        title="Human-Correct Answers Missed by Exact Match",
    )
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def main() -> None:
    """Regenerate the human-accuracy distribution, heatmap, and gap figures."""
    frame, complete, mtime = prepare_frame()
    print(
        f"Evaluation source timestamp: {mtime}; complete communities: {len(complete)}"
    )
    _save(
        plot_accuracy_distribution_by_community(frame, complete),
        "human_accuracy_distribution_by_community",
    )
    _save(
        plot_accuracy_heatmap_by_community(frame, complete),
        "human_accuracy_heatmap_by_community",
    )
    _save(
        plot_correct_answers_missed_by_exact_match(frame, complete),
        "human_correct_answers_missed_by_exact_match",
    )


if __name__ == "__main__":
    main()
