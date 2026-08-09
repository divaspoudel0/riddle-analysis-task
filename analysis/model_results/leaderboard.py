"""Generate the full-corpus model leaderboard."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import figure_stem
from analysis.model_results.metrics import model_summary
from analysis.model_results.model_data import load_results, performance_order
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"


def plot_leaderboard(results: pd.DataFrame) -> None:
    """Write the strict-match leaderboard figure and CSV."""
    summary = model_summary(results).reset_index()
    summary["match_rate"] = summary["model_display"].map(
        results.groupby("model_display")["is_correct"].mean()
    )
    summary = (
        summary.set_index("model_display").loc[performance_order(results)].reset_index()
    )
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.2, 0.34 * len(summary) + 1.25))
    )
    positions = range(len(summary))
    values = summary["match_rate"] * 100
    ax.barh(positions, values, color=PALETTE["blue"], height=0.64)
    ax.set_xlim(0, max(100, values.max() + 8))
    for position, value in zip(positions, values, strict=True):
        ax.text(value + 0.8, position, f"{value:.1f}%", va="center", fontsize=7)
    ax.set(
        yticks=list(positions),
        yticklabels=summary["model_display"],
        xlabel="Strict match rate (%)",
        title="Model performance on the full corpus",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", "leaderboard_v2"))
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "full_corpus_leaderboard.csv", index=False)


def main() -> None:
    """Regenerate the leaderboard figure and table."""
    plot_leaderboard(load_results())


if __name__ == "__main__":
    main()
