"""Build publication tables and their machine-readable snapshots.

The functions in this module are the shared source for the paper's CSV and
Markdown tables and for the static analysis dashboard. Keep values numeric in
the source DataFrames; presentation strings such as ``65.1%`` are added only
by the display helpers.

Run from the repository root with::

    uv run --project analysis python -m analysis.tables.build
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from analysis.constants import REGION_ORDER
from analysis.corpus import load_corpus_metadata
from analysis.eval_analysis.model_summary import build_summary
from analysis.riddle_analysis.corpus_data import load_corpus
from analysis.utils import write_csv

TABLE_DIR = Path(__file__).parent
OUTPUT_DIR = TABLE_DIR / "outputs"


def build_corpus_coverage() -> pd.DataFrame:
    """Build the corpus-coverage table grouped by region.

    Returns:
        One row per configured region plus a total row. ``cultures`` counts
        communities, ``riddles`` counts corpus rows, ``countries`` counts
        distinct countries, and ``languages`` counts distinct ISO language
        codes.
    """
    corpus = load_corpus()
    grouped = (
        corpus.groupby("region", observed=True)
        .agg(
            cultures=("community", "nunique"),
            riddles=("riddle_id", "size"),
            countries=("country", "nunique"),
            languages=("language_code", "nunique"),
        )
        .reindex(REGION_ORDER, fill_value=0)
        .reset_index(names="region")
    )
    total = pd.DataFrame(
        [
            {
                "region": "Total",
                "cultures": int(corpus["community"].nunique()),
                "riddles": int(corpus["riddle_id"].size),
                "countries": int(corpus["country"].nunique()),
                "languages": int(corpus["language_code"].nunique()),
            }
        ]
    )
    return pd.concat([grouped, total], ignore_index=True).astype(
        {"cultures": int, "riddles": int, "countries": int, "languages": int}
    )


def _community_label(community: str, metadata: pd.DataFrame) -> str:
    """Return a compact language-and-country label for a community ID."""
    row = metadata.loc[community]
    country_abbreviations = {
        "Belarus": "BY",
        "Indonesia": "ID",
        "Italy": "IT",
        "United States": "US",
    }
    country = country_abbreviations.get(row["country"], row["country"])
    return f"{row['language_label']} ({country})"


def build_model_performance() -> pd.DataFrame:
    """Build the paper's model-performance summary table.

    Returns:
        One row per evaluated model with numeric percentage-point values and
        readable labels for the best and worst communities.
    """
    summary = build_summary().copy()
    metadata = load_corpus_metadata().set_index("community")
    missing = (
        set(summary["max_accuracy_community"]) | set(summary["min_accuracy_community"])
    ) - set(metadata.index)
    if missing:
        raise ValueError(
            f"Model summary contains unknown communities: {sorted(missing)}"
        )

    return pd.DataFrame(
        {
            "model": summary["model"],
            "access": summary["is_proprietary"].map(
                {True: "Proprietary", False: "Open"}
            ),
            "exact_match": summary["exact_match"],
            "human_accuracy": summary["human_correct"],
            "difference_pp": (
                summary["human_correct"] - summary["exact_match"].astype(float)
            ).round(1),
            "max_community_accuracy": summary["max_community_accuracy"],
            "max_accuracy_community": summary["max_accuracy_community"].map(
                lambda value: _community_label(value, metadata)
            ),
            "min_community_accuracy": summary["min_community_accuracy"],
            "min_accuracy_community": summary["min_accuracy_community"].map(
                lambda value: _community_label(value, metadata)
            ),
            "n": summary["n"],
            "n_complete_communities": summary["n_complete_communities"],
        }
    )


def corpus_coverage_display(frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the corpus table with paper/dashboard labels and formatting."""
    source = build_corpus_coverage() if frame is None else frame
    return source.rename(
        columns={
            "region": "Region",
            "cultures": "Cultures",
            "riddles": "Riddles",
            "countries": "Countries",
            "languages": "Lang.",
        }
    )


def model_performance_display(frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the model table with compact paper/dashboard formatting."""
    source = build_model_performance() if frame is None else frame
    display = pd.DataFrame(
        {
            "Model": source["model"],
            "Access": source["access"],
            "Exact (%)": source["exact_match"].map(lambda value: f"{value:.1f}"),
            "Human (%)": source["human_accuracy"].map(lambda value: f"{value:.1f}"),
            "Δ (pp)": source["difference_pp"].map(lambda value: f"{value:+.1f}"),
            "Max (%)": source["max_community_accuracy"].map(
                lambda value: f"{value:.1f}"
            ),
            "Max community": source["max_accuracy_community"],
            "Min (%)": source["min_community_accuracy"].map(
                lambda value: f"{value:.1f}"
            ),
            "Min community": source["min_accuracy_community"],
        }
    )
    return display


def _markdown_escape(value: object) -> str:
    """Escape a value for a pipe-delimited Markdown table."""
    return str(value).replace("|", r"\|").replace("\n", " ")


def to_markdown(frame: pd.DataFrame) -> str:
    """Render a DataFrame as a dependency-free GitHub-flavored table."""
    headers = [_markdown_escape(column) for column in frame.columns]
    separator = ["---"] * len(headers)
    rows = [
        [_markdown_escape(value) for value in row]
        for row in frame.itertuples(index=False, name=None)
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def _write_table(
    name: str,
    source_frame: pd.DataFrame,
    display_frame: pd.DataFrame,
    title: str,
) -> None:
    """Write one CSV and one Markdown publication-table snapshot."""
    csv_path = OUTPUT_DIR / f"{name}.csv"
    markdown_path = OUTPUT_DIR / f"{name}.md"
    write_csv(source_frame, csv_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        f"## {title}\n\n{to_markdown(display_frame)}", encoding="utf-8"
    )


TABLES: tuple[
    tuple[str, str, Callable[[], pd.DataFrame], Callable[[pd.DataFrame], pd.DataFrame]],
    ...,
] = (
    (
        "table_01_corpus_coverage",
        "Corpus coverage by region",
        build_corpus_coverage,
        corpus_coverage_display,
    ),
    (
        "table_02_model_performance",
        "Model performance summary",
        build_model_performance,
        model_performance_display,
    ),
)


def main() -> None:
    """Write CSV and Markdown snapshots for all publication tables."""
    for name, title, builder, display_builder in TABLES:
        source = builder()
        _write_table(name, source, display_builder(source), title)
        print(f"Wrote {OUTPUT_DIR / f'{name}.csv'}")
        print(f"Wrote {OUTPUT_DIR / f'{name}.md'}")


if __name__ == "__main__":
    main()
