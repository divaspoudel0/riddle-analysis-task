"""Generate model performance by benchmark topic."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import figure_stem
from analysis.model_results.model_data import canonical_topic, load_results, topic_rates
from analysis.style import SCORE_CMAP, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"


def plot_topic_performance(results: pd.DataFrame) -> None:
    """Write the strict-match topic matrix and its summaries."""
    rates = topic_rates(results)
    frame = results.assign(topic=results["riddle_id"].map(canonical_topic))
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.5, 0.31 * len(rates) + 1.65))
    )
    image = ax.imshow(
        rates.to_numpy() * 100, cmap=SCORE_CMAP, vmin=0, vmax=100, aspect="auto"
    )
    ax.set(
        xticks=range(len(rates.columns)),
        xticklabels=rates.columns,
        yticks=range(len(rates)),
        yticklabels=rates.index,
        title="Strict match rate by benchmark topic",
    )
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for row in range(rates.shape[0]):
        for column in range(rates.shape[1]):
            ax.text(
                column,
                row,
                f"{rates.iat[row, column] * 100:.1f}",
                ha="center",
                va="center",
                fontsize=7,
            )
    fig.colorbar(image, ax=ax, label="Strict match rate (%)")
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", "full_corpus_topic_performance"))
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rates.reset_index().to_csv(
        OUTPUT_DIR / "full_corpus_topic_performance.csv", index=False
    )
    pd.DataFrame(
        {
            "topic": rates.columns,
            "items": frame.groupby("topic")["riddle_id"]
            .nunique()
            .reindex(rates.columns)
            .values,
            "mean_model_match_rate": rates.mean().values,
        }
    ).to_csv(OUTPUT_DIR / "topic_match_rate_summary.csv", index=False)


def main() -> None:
    """Regenerate the topic heatmap and summary tables."""
    plot_topic_performance(load_results())


if __name__ == "__main__":
    main()
