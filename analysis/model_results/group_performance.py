"""Generate model performance matrices for regions and languages."""

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import (
    LANGUAGE_GROUP_ORDER,
    MODEL_RESULTS_OUTPUT_DIR,
    REGION_ORDER,
    figure_stem,
)
from analysis.corpus import add_corpus_groups, language_label_map
from analysis.model_results.metrics import group_accuracy_ci
from analysis.model_results.model_data import load_scored_results, match_rates
from analysis.style import (
    PALETTE,
    SCORE_CMAP,
    apply_style,
    save_figure_pair,
)
from analysis.utils import write_csv

OUTPUT_DIR = MODEL_RESULTS_OUTPUT_DIR

REGION_LABELS = {
    "Sub-Saharan Africa": "Sub-Saharan\nAfrica",
    "North Africa": "North\nAfrica",
    "North America": "North\nAmerica",
    "Latin America": "Latin\nAmerica",
    "West Asia": "West\nAsia",
    "Central Asia": "Central\nAsia",
    "South Asia": "South\nAsia",
    "East Asia": "East\nAsia",
    "Southeast Asia": "Southeast\nAsia",
    "Oceania & Pacific": "Oceania &\nPacific",
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
    *,
    wide: bool = False,
) -> None:
    """Write one model-by-corpus-group strict-match matrix and summaries."""
    grouped = add_corpus_groups(results, community_column="instance_community")
    rates = match_rates(grouped, column, order)
    item_counts = (
        grouped.groupby(column).riddle_id.nunique().reindex(order).fillna(0).astype(int)
    )
    label_counts = (
        grouped.groupby(column)
        .instance_community.nunique()
        .reindex(order)
        .fillna(0)
        .astype(int)
        if column == "language_group"
        else item_counts
    )
    labels = {
        **REGION_LABELS,
        **LANGUAGE_GROUP_LABELS,
        **language_label_map(),
    }
    group_labels = [
        f"{labels.get(group, group)}\n(n={items})"
        for group, items in label_counts.items()
    ]
    x_label_size = 4 if wide else 5 if column == "region" else 7

    ci_df = group_accuracy_ci(grouped, column)
    ci_lookup = {}
    for _, row in ci_df.iterrows():
        ci_lookup[(row["model_display"], row[column])] = (
            row["ci_low"],
            row["ci_high"],
        )

    apply_style()
    figure_width = max(6.45, 0.34 * len(order) + 1.65) if wide else 6.45
    fig, ax = plt.subplots(figsize=(figure_width, max(3.5, 0.31 * len(rates) + 1.65)))
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
            model_name = rates.index[row]
            group_name = rates.columns[column_index]
            ci = ci_lookup.get((model_name, group_name))
            if ci is not None:
                ci_width = (ci[1] - ci[0]) / 2 * 100
                text = f"{value * 100:.1f}\n\u00b1{ci_width:.1f}"
                text_size = 3 if wide else 5
            else:
                text = f"{value * 100:.1f}"
                text_size = 4 if wide else 7
            ax.text(
                column_index,
                row,
                text,
                ha="center",
                va="center",
                fontsize=text_size,
                color=PALETTE["black"],
            )
    fig.colorbar(image, ax=ax, label="Strict match rate (%)")
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", figure_name))
    plt.close(fig)
    write_csv(rates.reset_index(), OUTPUT_DIR / f"{name}.csv")
    summary_rows = []
    for group in order:
        if group not in rates.columns:
            continue
        for model in rates.index:
            ci = ci_lookup.get((model, group))
            summary_rows.append(
                {
                    column: group,
                    "items": item_counts.get(group, 0),
                    "model": model,
                    "match_rate": rates.loc[model, group],
                    "ci_low": ci[0] if ci else None,
                    "ci_high": ci[1] if ci else None,
                }
            )
    write_csv(pd.DataFrame(summary_rows), OUTPUT_DIR / f"{name}_summary.csv")


def main() -> None:
    """Regenerate regional and language-group performance outputs."""
    results = load_scored_results()
    plot_group_performance(
        results,
        "region",
        REGION_ORDER,
        "full_corpus_region_performance",
        "Strict match rate by region",
        "exact_match_accuracy_by_region",
    )
    plot_group_performance(
        results,
        "language_group",
        LANGUAGE_GROUP_ORDER,
        "full_corpus_language_group_performance",
        "Strict match rate across multi-community language groups",
        "exact_match_accuracy_by_language_group",
    )
    language_order = tuple(sorted(results["instance_language"].unique()))
    plot_group_performance(
        results,
        "instance_language",
        language_order,
        "full_corpus_language_performance",
        "Strict match rate by language",
        "exact_match_accuracy_by_language",
        wide=True,
    )


if __name__ == "__main__":
    main()
