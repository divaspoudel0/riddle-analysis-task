"""Generate the human-evaluation exact-match leaderboard."""

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import MODEL_RESULTS_OUTPUT_DIR, figure_stem
from analysis.eval_analysis.data import coverage_report, load_human_evaluation
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair
from analysis.utils import write_csv

OUTPUT_DIR = MODEL_RESULTS_OUTPUT_DIR


def load_human_eval_leaderboard() -> pd.DataFrame:
    """Compute human-evaluation exact-match accuracy on complete communities."""
    frame = load_human_evaluation()
    complete = set(coverage_report(frame).query("status == 'complete'").index)
    scored = frame[frame["community"].isin(complete) & ~frame["is_pending"]]
    summary = (
        scored.groupby("model_display")
        .agg(
            exact_match_accuracy=("is_exact_match", "mean"),
            human_accuracy=("is_correct", "mean"),
            n=("is_correct", "size"),
            human_scored_percent=("is_human", "mean"),
        )
        .assign(
            exact_match_accuracy=lambda data: data["exact_match_accuracy"] * 100,
            human_accuracy=lambda data: data["human_accuracy"] * 100,
            human_scored_percent=lambda data: data["human_scored_percent"] * 100,
        )
        .sort_values("exact_match_accuracy", ascending=False)
        .reset_index()
    )
    return summary


def plot_leaderboard(summary: pd.DataFrame) -> None:
    """Write an exact-match accuracy leaderboard for all evaluated models."""
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.2, 0.34 * len(summary) + 1.25))
    )
    positions = range(len(summary))
    values = summary["exact_match_accuracy"]
    ax.barh(positions, values, color=PALETTE["blue"], height=0.64)
    ax.set_xlim(0, 100)
    for position, value in zip(positions, values, strict=True):
        ax.text(value + 0.8, position, f"{value:.1f}%", va="center", fontsize=7)
    ax.set(
        yticks=list(positions),
        yticklabels=summary["model_display"],
        xlabel="Exact-match accuracy (%)",
        title="Exact-match accuracy across human-evaluated models",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("model_results", "exact_match_accuracy_leaderboard")
    )
    plt.close(fig)
    write_csv(summary, OUTPUT_DIR / "human_eval_exact_match_leaderboard.csv")


def main() -> None:
    """Regenerate the 24-model exact-match leaderboard and table."""
    plot_leaderboard(load_human_eval_leaderboard())


if __name__ == "__main__":
    main()
