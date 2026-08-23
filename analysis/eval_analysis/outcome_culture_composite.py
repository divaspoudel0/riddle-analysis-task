"""Build the ACL two-column human-evaluation outcome/culture composite.

The left panel shows the detailed outcome composition and the right panel shows
the same models' across-community human-correct distributions.  The shared row
order lets the two panels be read together without repeating model labels.

Run with::

    uv run --project analysis python -m analysis.eval_analysis.outcome_culture_composite
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from analysis import style
from analysis.constants import figure_stem
from analysis.eval_analysis.data import MODEL_NAME_MAP
from analysis.eval_analysis.human_accuracy import prepare_frame
from analysis.eval_analysis.outcome_failure_modes import (
    OUTCOME_COLORS,
    OUTCOME_HATCHES,
    OUTCOME_ORDER,
    outcome_shares,
)

OUTCOME_LEGEND_LABELS = {
    "Exact match": "Exact",
    "Different valid answer": "Valid answer",
    "Correct, in English": "English",
    "Other correct": "Other correct",
    "Closely related culture": "Culture",
    "Wrong level of detail": "Detail",
    "Surface pattern matching": "Pattern",
    "Other partial": "Other partial",
    "Hallucinated": "Hallucinated",
    "Right category, wrong entity": "Wrong entity",
    "Too broad": "Too broad",
    "Other incorrect": "Other incorrect",
    "Declined to answer": "Declined",
    "Placeholder": "Placeholder",
    "Empty output": "Empty",
}


def plot_outcome_culture_composite():
    """Return the aligned ACL two-column outcome and culture-distribution figure."""
    frame, complete, _ = prepare_frame()
    shares = outcome_shares(frame).rename(index=MODEL_NAME_MAP)
    order = shares.index.tolist()

    scored = frame[frame.community.isin(complete) & ~frame.is_pending]
    by_community = (
        scored.groupby(["model_display", "community"])["is_correct"].mean().mul(100)
    )
    distributions = [by_community.loc[model].to_numpy() for model in order]

    style.apply_style()
    fig, (outcome_ax, culture_ax) = plt.subplots(
        1,
        2,
        figsize=style.acl_figure_size(2, 3.45),
        gridspec_kw={"width_ratios": [1.45, 1]},
    )
    positions = np.arange(len(order))

    left = np.zeros(len(order))
    for outcome in OUTCOME_ORDER:
        values = shares[outcome].to_numpy() * 100
        outcome_ax.barh(
            positions,
            values,
            left=left,
            color=OUTCOME_COLORS[outcome],
            edgecolor="white",
            linewidth=0.3,
            hatch=OUTCOME_HATCHES.get(outcome),
            label=outcome,
        )
        left += values
    outcome_ax.set(
        xlim=(0, 100),
        yticks=positions,
        yticklabels=order,
        xlabel="Scored attempts (%)",
        title="(a) Outcome composition",
    )
    outcome_ax.tick_params(axis="y", labelsize=4.35, pad=1.0)
    outcome_ax.tick_params(axis="x", labelsize=5.3)
    outcome_ax.xaxis.label.set_size(5.9)
    outcome_ax.set_title("")
    outcome_ax.text(
        0.5,
        1.19,
        "(a) Outcome composition",
        transform=outcome_ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=6.7,
        clip_on=False,
    )
    outcome_ax.invert_yaxis()
    outcome_ax.grid(axis="x", alpha=0.3)
    outcome_ax.grid(axis="y", visible=False)

    boxes = culture_ax.boxplot(
        distributions,
        vert=False,
        positions=positions,
        widths=0.62,
        patch_artist=True,
        showfliers=True,
        medianprops={"color": style.PALETTE["black"], "lw": 1.2},
        flierprops={
            "marker": "o",
            "ms": 2.4,
            "markerfacecolor": style.PALETTE["grey"],
            "markeredgecolor": "none",
            "alpha": 0.45,
        },
        whiskerprops={"color": style.PALETTE["grey"], "lw": 0.8},
        capprops={"color": style.PALETTE["grey"], "lw": 0.8},
    )
    for patch in boxes["boxes"]:
        patch.set(
            facecolor=style.PALETTE["sky_blue"],
            alpha=0.55,
            edgecolor=style.PALETTE["blue"],
        )
    minima = [values.min() for values in distributions]
    culture_ax.plot(
        minima,
        positions,
        linestyle="none",
        marker="D",
        ms=2.7,
        color=style.PALETTE["vermillion"],
        label="Lowest-scoring community",
        zorder=5,
    )
    culture_ax.set(
        xlim=(0, 100),
        ylim=(len(order) - 0.5, -0.5),
        yticks=positions,
        yticklabels=[],
        xlabel="Human-correct accuracy (%)",
        title=f"(b) Distribution across {len(complete)} communities",
    )
    culture_ax.tick_params(axis="y", length=0)
    culture_ax.tick_params(axis="x", labelsize=5.3)
    culture_ax.xaxis.label.set_size(5.9)
    culture_ax.set_title("")
    culture_ax.text(
        0.5,
        1.19,
        f"(b) Distribution across {len(complete)} communities",
        transform=culture_ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=6.7,
        clip_on=False,
    )
    culture_ax.grid(axis="x", alpha=0.3)
    culture_ax.grid(axis="y", visible=False)
    culture_ax.legend(loc="lower right", fontsize=4.2, frameon=True, framealpha=0.9)

    handles, labels = outcome_ax.get_legend_handles_labels()
    outcome_ax.legend(
        handles,
        [OUTCOME_LEGEND_LABELS[label] for label in labels],
        ncol=5,
        loc="lower left",
        bbox_to_anchor=(0, 1.015),
        fontsize=3.35,
        columnspacing=0.5,
        handlelength=1.1,
        labelspacing=0.22,
        borderaxespad=0,
    )
    fig.subplots_adjust(left=0.205, right=0.995, bottom=0.12, top=0.76, wspace=0.18)
    return fig


def main() -> None:
    """Write the publication PDF and review PNG for the paired two-column figure."""
    fig = plot_outcome_culture_composite()
    output = figure_stem("eval_analysis", "human_outcomes_and_culture_distribution")
    # Preserve the ACL two-column canvas, rather than style.py's default tight
    # crop, so its panels retain their intended proportions.
    pdf_path, png_path = style.save_figure_pair(
        fig, output, bbox_inches=fig.bbox_inches
    )
    plt.close(fig)
    print(f"Wrote {pdf_path} and {png_path}")


if __name__ == "__main__":
    main()
