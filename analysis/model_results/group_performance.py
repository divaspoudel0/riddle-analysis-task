"""Generate model performance matrices for regions and languages."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import LANGUAGE_GROUP_ORDER, REGION_ORDER, figure_stem
from analysis.corpus import add_corpus_groups
from analysis.model_results.model_data import load_results, performance_order
from analysis.style import (
    PALETTE,
    SCORE_CMAP,
    apply_style,
    save_figure_pair,
)

OUTPUT_DIR = Path(__file__).parent / "outputs"

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
LANGUAGE_LABELS = {
    "aeb": "Tunisian Arabic",
    "apc": "Levantine Arabic",
    "apd": "Sudanese Arabic",
    "ary": "Moroccan Arabic",
    "arz": "Egyptian Arabic",
    "asm": "Assamese",
    "bel": "Belarusian",
    "ben": "Bengali",
    "bug": "Buginese",
    "bul": "Bulgarian",
    "cat": "Catalan",
    "deu": "German",
    "eng": "English",
    "fra": "French",
    "gaz": "Oromo",
    "guj": "Gujarati",
    "hun": "Hungarian",
    "ind": "Indonesian",
    "ita": "Italian",
    "jpn": "Japanese",
    "kan": "Kannada",
    "kok": "Konkani",
    "ltz": "Luxembourgish",
    "lug": "Luganda",
    "mal": "Malayalam",
    "mar": "Marathi",
    "mog": "Mongondow",
    "myx": "Lumasaba",
    "nep": "Nepali",
    "nld": "Dutch",
    "pes": "Persian",
    "pol": "Polish",
    "por": "Portuguese",
    "rus": "Russian",
    "sin": "Sinhala",
    "snd": "Sindhi",
    "spa": "Spanish",
    "srp": "Serbian",
    "swa": "Swahili",
    "tam": "Tamil",
    "tel": "Telugu",
    "tha": "Thai",
    "tur": "Turkish",
    "ukr": "Ukrainian",
    "urd": "Urdu",
    "uzb": "Uzbek",
    "vie": "Vietnamese",
    "yor": "Yoruba",
    "yue": "Cantonese",
    "zho": "Chinese",
    "zsm": "Malay",
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
    rates = (
        grouped.groupby(["model_display", column])["is_correct"]
        .mean()
        .unstack(column)
        .reindex(index=performance_order(results), columns=order)
    )
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
        **LANGUAGE_LABELS,
    }
    group_labels = [
        f"{labels.get(group, group)}\n(n={items})"
        for group, items in label_counts.items()
    ]
    x_label_size = 4 if wide else 5 if column == "region" else 7
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
            ax.text(
                column_index,
                row,
                f"{value * 100:.1f}",
                ha="center",
                va="center",
                fontsize=4 if wide else 7,
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
