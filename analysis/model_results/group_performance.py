"""Generate model performance matrices for regions and language groups."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import LANGUAGE_GROUP_ORDER, REGION_ORDER, figure_stem
from analysis.corpus import add_corpus_groups
from analysis.model_results.model_data import load_results, performance_order
from analysis.style import SCORE_CMAP, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"


def plot_group_performance(
    results: pd.DataFrame, column: str, order: tuple[str, ...], name: str, title: str
) -> None:
    """Write one model-by-corpus-group strict-match matrix and summaries."""
    grouped = add_corpus_groups(results, community_column="instance_community")
    rates = (
        grouped.groupby(["model_display", column])["is_correct"]
        .mean()
        .unstack(column)
        .reindex(index=performance_order(results), columns=order)
    )
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.5, 0.31 * len(rates) + 1.65))
    )
    image = ax.imshow(
        rates.to_numpy() * 100, cmap=SCORE_CMAP, vmin=0, vmax=100, aspect="auto"
    )
    ax.set(
        xticks=range(len(order)),
        xticklabels=order,
        yticks=range(len(rates)),
        yticklabels=rates.index,
        title=title,
    )
    plt.setp(ax.get_xticklabels(), rotation=32, ha="right")
    fig.colorbar(image, ax=ax, label="Strict match rate (%)")
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("model_results", name))
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rates.reset_index().to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    pd.DataFrame(
        {
            column: rates.columns,
            "items": grouped.groupby(column).riddle_id.nunique().reindex(order).values,
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
    )
    plot_group_performance(
        results,
        "language_group",
        LANGUAGE_GROUP_ORDER,
        "full_corpus_language_group_performance",
        "Strict match rate across multi-community language groups",
    )


if __name__ == "__main__":
    main()
