"""Generate model performance by benchmark topic."""

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import MODEL_RESULTS_OUTPUT_DIR, figure_stem
from analysis.model_results.model_data import (
    canonical_topic,
    load_scored_results,
    topic_rates,
)
from analysis.style import (
    PALETTE,
    SCORE_CMAP,
    acl_figure_size,
    apply_style,
    save_figure_pair,
)
from analysis.utils import write_csv

OUTPUT_DIR = MODEL_RESULTS_OUTPUT_DIR

TOPIC_LABELS = {
    "National Heritage": "National\nHeritage",
    "Kid's World": "Kid's\nWorld",
    "Everyday Life": "Everyday\nLife",
}


def plot_topic_performance(results: pd.DataFrame) -> None:
    """Write the strict-match topic matrix and its summaries."""
    rates = topic_rates(results)
    frame = results.assign(topic=results["riddle_id"].map(canonical_topic))
    item_counts = frame.groupby("topic")["riddle_id"].nunique().reindex(rates.columns)
    topic_labels = [
        f"{TOPIC_LABELS.get(topic, topic)}\n(n={items})"
        for topic, items in item_counts.items()
    ]
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.5, 0.31 * len(rates) + 1.65))
    )
    image = ax.imshow(
        rates.to_numpy() * 100, cmap=SCORE_CMAP, vmin=0, vmax=100, aspect="auto"
    )
    ax.set(
        xticks=range(len(rates.columns)),
        xticklabels=topic_labels,
        yticks=range(len(rates)),
        yticklabels=rates.index,
        title="Strict match rate by benchmark topic",
    )
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), fontsize=7, ha="center")
    for row in range(rates.shape[0]):
        for column in range(rates.shape[1]):
            ax.text(
                column,
                row,
                f"{rates.iat[row, column] * 100:.1f}",
                ha="center",
                va="center",
                fontsize=7,
                color=PALETTE["black"],
            )
    fig.colorbar(image, ax=ax, label="Strict match rate (%)")
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", "exact_match_accuracy_by_topic"))
    plt.close(fig)
    write_csv(rates.reset_index(), OUTPUT_DIR / "full_corpus_topic_performance.csv")
    write_csv(
        pd.DataFrame(
            {
                "topic": rates.columns,
                "items": item_counts.values,
                "mean_model_match_rate": rates.mean().values,
            }
        ),
        OUTPUT_DIR / "topic_match_rate_summary.csv",
    )


def main() -> None:
    """Regenerate the topic heatmap and summary tables."""
    plot_topic_performance(load_scored_results())


if __name__ == "__main__":
    main()
