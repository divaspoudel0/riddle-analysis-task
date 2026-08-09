"""Generate per-model deterministic-score outcome distributions."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import figure_stem
from analysis.model_results.model_data import load_results, performance_order
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"


def plot_outcomes(results: pd.DataFrame) -> None:
    """Write deterministic judge-score distributions by model."""
    labels = {0: "incorrect", 1: "uncertain", 2: "partial", 3: "correct"}
    shares = (
        results[results.is_completed]
        .assign(outcome=results.loc[results.is_completed, "judge_score"].map(labels))
        .groupby("model_display")["outcome"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        .reindex(
            index=performance_order(results), columns=labels.values(), fill_value=0
        )
    )
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.2, 0.34 * len(shares) + 1.75))
    )
    left = pd.Series(0.0, index=shares.index)
    for label, color in zip(
        labels.values(),
        [
            PALETTE["vermillion"],
            PALETTE["sky_blue"],
            PALETTE["orange"],
            PALETTE["bluish_green"],
        ],
    ):
        ax.barh(
            shares.index, shares[label] * 100, left=left * 100, color=color, label=label
        )
        left += shares[label]
    ax.set(
        xlabel="Completed responses (%)",
    )
    fig.suptitle("Deterministic heuristic-score distribution", y=0.97)
    fig.legend(
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 0.93),
        columnspacing=1.2,
        handlelength=1.2,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure_pair(fig, figure_stem("model_results", "outcomes_v2"))
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shares.reset_index().to_csv(OUTPUT_DIR / "full_corpus_outcomes.csv", index=False)


def main() -> None:
    """Regenerate the outcome-distribution figure and table."""
    plot_outcomes(load_results())


if __name__ == "__main__":
    main()
