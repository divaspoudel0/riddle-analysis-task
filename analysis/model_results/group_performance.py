"""Generate model performance matrices for regions and language groups."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import LANGUAGE_GROUP_ORDER, REGION_ORDER, figure_stem
from analysis.corpus import add_corpus_groups
from analysis.model_results.model_data import load_results, performance_order
from analysis.style import (
    PALETTE,
    SCORE_CMAP,
    acl_figure_size,
    apply_style,
    save_figure_pair,
)

OUTPUT_DIR = Path(__file__).parent / "outputs"

REGION_LABELS = {
    "Sub-Saharan Africa": "Sub-Saharan\nAfrica",
    "North Africa": "North\nAfrica",
    "North America": "North\nAmerica",
    "South America": "South\nAmerica",
    "West Asia": "West\nAsia",
    "Central Asia": "Central\nAsia",
    "South Asia": "South\nAsia",
    "East & Southeast Asia": "East & SE\nAsia",
}
LANGUAGE_GROUP_LABELS = {
    "Arabic varieties": "Arabic\nvarieties",
    "Chinese varieties": "Chinese\nvarieties",
}


def plot_group_performance(
    results: pd.DataFrame,
    column: str,
    order: tuple[str, ...],
    name: str,
    title: str,
    figure_name: str,
) -> None:
    """Write one model-by-corpus-group strict-match matrix and summaries."""
    grouped = add_corpus_groups(results, community_column="instance_community")
    rates = (
        grouped.groupby(["model_display", column])["is_correct"]
        .mean()
        .unstack(column)
        .reindex(index=performance_order(results), columns=order)
    )
    item_counts = grouped.groupby(column).riddle_id.nunique().reindex(order)
    label_counts = (
        grouped.groupby(column).instance_community.nunique().reindex(order)
        if column == "language_group"
        else item_counts
    )
    group_labels = [
        f"{REGION_LABELS.get(group, LANGUAGE_GROUP_LABELS.get(group, group))}\n(n={items})"
        for group, items in label_counts.items()
    ]
    x_label_size = 6 if column == "region" else 7
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.5, 0.31 * len(rates) + 1.65))
    )
    image = ax.imshow(
        rates.to_numpy() * 100, cmap=SCORE_CMAP, vmin=0, vmax=100, aspect="auto"
    )
    ax.set(
        xticks=range(len(order)),
        xticklabels=group_labels,
        yticks=range(len(rates)),
        yticklabels=rates.index,
        title=title,
    )
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), fontsize=x_label_size, ha="center")
    for row in range(rates.shape[0]):
        for column_index in range(rates.shape[1]):
            value = rates.iat[row, column_index]
            if pd.isna(value):
                continue
            ax.text(
                column_index,
                row,
                f"{value * 100:.1f}",
                ha="center",
                va="center",
                fontsize=7,
                color=PALETTE["black"],
            )
    fig.colorbar(image, ax=ax, label="Strict match rate (%)")
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", figure_name))
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rates.reset_index().to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    pd.DataFrame(
        {
            column: rates.columns,
            "items": item_counts.values,
            "mean_model_match_rate": rates.mean().values,
        }
    ).to_csv(OUTPUT_DIR / f"{name}_summary.csv", index=False)


def main() -> None:
    """Regenerate regional and language-group performance outputs."""
    results = load_results()
    plot_group_performance(
        results,
        "region",
        REGION_ORDER,
        "full_corpus_region_performance",
        "Strict match rate by region",
        "region_performance_v2",
    )
    plot_group_performance(
        results,
        "language_group",
        LANGUAGE_GROUP_ORDER,
        "full_corpus_language_group_performance",
        "Strict match rate across multi-community language groups",
        "language_group_performance_v2",
    )


if __name__ == "__main__":
    main()
