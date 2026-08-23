"""Generate the exact-match versus human-correct accuracy figure."""

import matplotlib.pyplot as plt

from analysis.constants import figure_stem
from analysis.model_results.leaderboard import load_human_eval_leaderboard
from analysis.style import PALETTE, apply_style, save_figure_pair


def plot_exact_match_vs_human_correct():
    """Return the exact-match versus human-correct dumbbell chart."""
    results = load_human_eval_leaderboard().sort_values("human_accuracy")
    apply_style()
    fig, ax = plt.subplots(figsize=(7.2, 8.0))
    positions = range(len(results))
    floor = results["exact_match_accuracy"]
    ceiling = results["human_accuracy"]
    ax.hlines(positions, floor, ceiling, color=PALETTE["light_grey"], lw=2, zorder=1)
    ax.plot(
        floor,
        positions,
        "o",
        ms=5,
        color=PALETTE["grey"],
        zorder=2,
        label="Exact match",
    )
    ax.plot(
        ceiling,
        positions,
        "o",
        ms=5,
        color=PALETTE["blue"],
        zorder=3,
        label="Human evaluation",
    )
    for y, floor_value, ceiling_value in zip(positions, floor, ceiling, strict=True):
        delta = ceiling_value - floor_value
        delta_midpoint = (floor_value + ceiling_value) / 2
        # Keep each score on the outside of its dot.  This remains readable
        # even for the small gaps at the bottom of the chart, unlike putting
        # both labels to the right of the nearly coincident dots.
        near_left_edge = min(floor_value, ceiling_value) < 2
        floor_offset = (4, -6) if near_left_edge else (-4, 0)
        ceiling_offset = (4, 6) if near_left_edge else (4, 0)
        ax.annotate(
            f"{floor_value:.1f}",
            (floor_value, y),
            xytext=floor_offset,
            textcoords="offset points",
            ha="left" if near_left_edge else "right",
            va="top" if near_left_edge else "center",
            fontsize=6.5,
            color=PALETTE["grey"],
        )
        ax.annotate(
            f"{ceiling_value:.1f}",
            (ceiling_value, y),
            xytext=ceiling_offset,
            textcoords="offset points",
            ha="left",
            va="bottom" if near_left_edge else "center",
            fontsize=6.5,
            color=PALETTE["blue"],
        )
        # The delta belongs to the connecting segment, not to either dot.
        # A small vertical offset clears the markers while keeping it close
        # enough to read as the gap between the two scores.
        ax.annotate(
            f"{delta:+.1f}pp",
            (delta_midpoint, y),
            xytext=(16, 0) if near_left_edge else (0, 4),
            textcoords="offset points",
            ha="left" if near_left_edge else "center",
            va="center" if near_left_edge else "bottom",
            fontsize=5.5,
            color=PALETTE["black"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 0.1},
            zorder=4,
        )
    ax.set(
        yticks=list(positions),
        yticklabels=results["model_display"],
        xlim=(0, 100),
        xlabel="Accuracy (%)",
        title=f"Exact-Match and Human-Evaluated Accuracy ({len(results)} Models)",
    )
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=7.5, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig


def main() -> None:
    """Write the exact-match versus human-correct PNG/PDF pair."""
    fig = plot_exact_match_vs_human_correct()
    output = figure_stem("eval_analysis", "accuracy_exact_match_vs_human_correct")
    pdf_path, png_path = save_figure_pair(fig, output)
    plt.close(fig)
    print(f"Wrote {pdf_path} and {png_path}")


if __name__ == "__main__":
    main()
