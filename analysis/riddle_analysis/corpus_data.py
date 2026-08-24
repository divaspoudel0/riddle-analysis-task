"""Audit and visualize the complete v0--v2 riddle corpus.

This module reads the canonical JSONL release directly rather than a cached
spreadsheet export, so every result reflects the current 6,100-riddle corpus.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import (
    CANONICAL_CORPUS_PATH,
    FIXED_TOPICS,
    REGION_ORDER,
    RIDDLE_ANALYSIS_OUTPUT_DIR,
    RUN_BATCH_ORDER,
    figure_stem,
)
from analysis.corpus import add_corpus_groups
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

DATASET_PATH = CANONICAL_CORPUS_PATH
TABLE_DIR = RIDDLE_ANALYSIS_OUTPUT_DIR

# Exclusive, manual semantic coding of the 85 distinct wildcard labels in the
# released corpus. Ambiguous labels are assigned on their primary referent;
# every observed label must appear exactly once.
WILDCARD_THEME_CODEBOOK = {
    "Food": {
        "Brazilian Cuisine",
        "Cuisine",
        "Food",
        "Food & Coooking",
        "Food & Hawker Culture",
        "Food & Household",
        "Food & Kitchen",
        "Food & Rituals",
        "Food & Street Culture",
        "Food and Agriculture",
        "Food culture",
        "Gasronomy",
        "Gastronomy",
        "National Cuisine",
        "Turkish Cuisine",
        "Wildcard 1 [Food]",
        "Wildcard 2 [Food Is Medicine]",
    },
    "Nature": {
        "Animal",
        "Animal Names",
        "Animals",
        "Animals & Plants",
        "Animals & insects",
        "Nature",
        "Nature, Animals and Science",
        "Plants",
        "Wildcard 2 [animals_naming]",
    },
    "Language": {
        "Cantonese Expressions",
        "Cantonese Sayings",
        "Colloquial phrases",
        "Idiom",
        "Language",
        "Language & Proverbs",
        "Popular Proverbs",
        "Proverbs",
        "Proverbs & Sayings",
        "Puns",
        "Singlish & Slang",
        "Slang",
        "Spoonerism",
        "dialect",
        "idioms and proverbs",
    },
    "Media": {
        "Cinema",
        "Hollywood",
        "Literature",
        "Movies",
        "Music",
        "Popculture",
        "Popular Culture",
        "TV shows",
        "Traditional instruments",
        "Turkish Pop Culture",
        "Wildcard 1 [Tamil Literature]",
    },
    "Religion": {
        "Beliefs",
        "Festivals & Folk Culture",
        "Mythology",
        "Myths & Folklore",
        "Myths and Legends",
        "Religion",
        "Religion & Festivals",
        "Wildcard 2 [Festival]",
    },
    "Society": {
        "Big in Portugal",
        "Clever Hungarians",
        "Culture",
        "Gen-Z ",
        "Humanities",
        "Wildcard 1 [Caste]",
        "Wildcard 2 [Relationships]",
    },
    "Health": {"Anatomy", "Human Anatomy", "Human Body"},
    "Science": {
        "Infrastructure",
        "Science",
        "Science & Technology",
        "Technology",
    },
    "Material Culture": {
        "Clothing",
        "Objects & Things",
        "Wildcard 1 [Konbini Culture]",
        "Wildcard 2 [Sento/Onsen Etiquette]",
    },
    "Economy": {"Economics", "Economy", "Work life"},
    "Places": {"Moscow", "Time, travel & maps"},
    "Heritage": {
        "درياءَ ۽ منڇر جا مهاڻا (Life of the Indus & Manchhar Boat-Folk)",
        "سنڌي شاديءَ جون ننڍڙيون رسمون (Sindhi Wedding Micro-Traditions)",
    },
}


def load_corpus(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load the canonical corpus and validate its identity-level invariants."""
    rows: list[dict[str, Any]] = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    df = pd.DataFrame(rows)
    if df["riddle_id"].duplicated().any():
        raise ValueError("Canonical corpus contains duplicate riddle IDs")
    if set(df["row_status"]) != {"valid"}:
        raise ValueError("Canonical corpus contains non-valid rows")
    if not (df.groupby("community").size() == 100).all():
        raise ValueError("Every community must contribute exactly 100 riddles")
    return add_corpus_groups(df)


def wildcard_theme(topic: str) -> str:
    """Return the exclusive manually coded theme for one wildcard label."""
    matching_themes = [
        theme for theme, labels in WILDCARD_THEME_CODEBOOK.items() if topic in labels
    ]
    if len(matching_themes) != 1:
        raise ValueError(
            f"Wildcard topic must have exactly one manual theme, got "
            f"{matching_themes!r}: {topic!r}"
        )
    return matching_themes[0]


def validate_wildcard_theme_codebook(topics: set[str]) -> None:
    """Ensure the manual codebook covers precisely the wildcard labels observed."""
    coded_topics = set().union(*WILDCARD_THEME_CODEBOOK.values())
    missing = topics - coded_topics
    stale = coded_topics - topics
    if missing or stale:
        raise ValueError(
            f"Wildcard theme codebook mismatch; missing={sorted(missing)!r}, "
            f"stale={sorted(stale)!r}"
        )


def save_tables(df: pd.DataFrame) -> None:
    """Write compact, non-sensitive tables that support every figure."""
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    native_english = df["language_code"].eq("eng")
    audit = pd.DataFrame(
        [
            {"metric": "riddles", "value": len(df)},
            {"metric": "communities", "value": df["community"].nunique()},
            {"metric": "languages", "value": df["language_code"].nunique()},
            {
                "metric": "missing English riddles",
                "value": int((df["riddle_english"].isna() & ~native_english).sum()),
            },
            {
                "metric": "missing English answers",
                "value": int(
                    (df["reference_answer_english"].isna() & ~native_english).sum()
                ),
            },
            {
                "metric": "human-validated riddles",
                "value": int(df["human_answer_score"].notna().sum()),
            },
        ]
    )
    audit.to_csv(TABLE_DIR / "corpus_audit.csv", index=False)
    (
        df.groupby("run_batch")
        .agg(
            riddles=("riddle_id", "size"),
            communities=("community", "nunique"),
            languages=("language_code", "nunique"),
        )
        .reindex(RUN_BATCH_ORDER)
        .reset_index()
        .to_csv(TABLE_DIR / "collection_summary.csv", index=False)
    )
    regional_summary = (
        df.assign(
            missing_english_riddle=df["riddle_english"].isna() & ~native_english,
            missing_english_answer=df["reference_answer_english"].isna()
            & ~native_english,
            has_human_score=df["human_answer_score"].notna(),
        )
        .groupby("region")
        .agg(
            riddles=("riddle_id", "size"),
            languages=("language_code", "nunique"),
            missing_english_riddles=("missing_english_riddle", "sum"),
            missing_english_answers=("missing_english_answer", "sum"),
            human_score_coverage=("has_human_score", "mean"),
        )
        .reindex(REGION_ORDER)
    )
    regional_summary[
        [
            "riddles",
            "languages",
            "missing_english_riddles",
            "missing_english_answers",
        ]
    ] = (
        regional_summary[
            [
                "riddles",
                "languages",
                "missing_english_riddles",
                "missing_english_answers",
            ]
        ]
        .fillna(0)
        .astype(int)
    )
    regional_summary["human_score_coverage"] = regional_summary[
        "human_score_coverage"
    ].fillna(0.0)
    regional_summary.reset_index().to_csv(
        TABLE_DIR / "region_corpus_summary.csv", index=False
    )


def plot_wildcard_themes(df: pd.DataFrame) -> None:
    """Plot the exclusive manual coding of community wildcard selections."""
    choices = df.loc[df["is_wildcard"], ["community", "topic"]].drop_duplicates().copy()
    validate_wildcard_theme_codebook(set(choices["topic"]))
    choices["theme"] = choices["topic"].map(wildcard_theme)
    counts = choices["theme"].value_counts().sort_values()
    community_counts = (
        choices.groupby("theme")["community"].nunique().reindex(counts.index)
    )
    colors = [
        PALETTE["vermillion"] if name == "Food" else PALETTE["grey"]
        for name in counts.index
    ]

    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.7))
    ax.barh(counts.index, counts.values, color=colors, height=0.62)
    ax.set_xlim(0, max(counts.values) + 5)
    ax.set_xlabel("Wildcard selections (122 total)")
    ax.set_title("Semantically coded wildcard topics")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for y, value in enumerate(counts.values):
        ax.text(
            value + 0.4,
            y,
            f"{value} ({value / len(choices):.0%})",
            va="center",
            fontsize=7,
        )
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_analysis", "wildcard_theme_distribution"))
    plt.close(fig)
    summary = counts.rename_axis("theme").rename("wildcard_selections").reset_index()
    summary["share_of_wildcard_selections"] = summary["wildcard_selections"] / len(
        choices
    )
    summary["n_communities"] = summary["theme"].map(community_counts)
    summary["share_of_communities"] = (
        summary["n_communities"] / choices["community"].nunique()
    )
    summary.to_csv(TABLE_DIR / "wildcard_themes.csv", index=False)
    choices.sort_values(["theme", "topic", "community"]).to_csv(
        TABLE_DIR / "wildcard_theme_codebook.csv", index=False
    )


def plot_english_length_by_topic(df: pd.DataFrame) -> None:
    """Show topic medians and IQRs without overstating skewed word counts."""
    usable = df.dropna(subset=["riddle_english"]).copy()
    usable["word_count"] = usable["riddle_english"].str.split().str.len()
    usable["analysis_topic"] = usable["topic"].where(~usable["is_wildcard"], "Wildcard")
    order = (*FIXED_TOPICS, "Wildcard")
    stats = (
        usable.groupby("analysis_topic")["word_count"]
        .agg(
            q1=lambda x: x.quantile(0.25),
            median="median",
            q3=lambda x: x.quantile(0.75),
            n="size",
        )
        .reindex(order)
    )
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 3.15))
    positions = range(len(stats))
    ax.hlines(positions, stats["q1"], stats["q3"], color=PALETTE["grey"], lw=2)
    ax.plot(stats["median"], positions, "o", color=PALETTE["blue"], ms=5)
    ax.set_yticks(list(positions), stats.index)
    ax.invert_yaxis()
    ax.set_xlabel("English riddle length (words): median and IQR")
    ax.set_title("English riddle length by topic")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for y, row in enumerate(stats.itertuples()):
        ax.text(
            row.q3 + 0.4,
            y,
            f"n={row.n}",
            va="center",
            fontsize=7,
            color=PALETTE["grey"],
        )
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_analysis", "answer_length_by_topic"))
    plt.close(fig)
    stats.reset_index(names="topic").to_csv(
        TABLE_DIR / "english_length_by_topic.csv", index=False
    )


def plot_validation_coverage(df: pd.DataFrame) -> None:
    """Separate validator-name coverage from recorded answer-score coverage."""
    summary = (
        df.assign(
            has_validator=df["human_validator_name"].notna(),
            has_score=df["human_answer_score"].notna(),
        )
        .groupby("run_batch")[["has_validator", "has_score"]]
        .mean()
        .reindex(RUN_BATCH_ORDER)
        .mul(100)
    )
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.35))
    x = range(len(summary))
    ax.plot(
        x,
        summary["has_validator"],
        marker="o",
        color=PALETTE["blue"],
        label="Named validator",
    )
    ax.plot(
        x,
        summary["has_score"],
        marker="o",
        color=PALETTE["vermillion"],
        label="Recorded human answer score",
    )
    ax.set_xticks(list(x), summary.index)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Riddles (%)")
    ax.set_title("Human-validation metadata coverage")
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(axis="y", alpha=0.35)
    ax.grid(axis="x", visible=False)
    for column, offset in (("has_validator", 2), ("has_score", -7)):
        for index, value in enumerate(summary[column]):
            ax.text(index, value + offset, f"{value:.0f}", ha="center", fontsize=7)
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_analysis", "human_validation_coverage"))
    plt.close(fig)
    summary.reset_index(names="run_batch").to_csv(
        TABLE_DIR / "human_validation_coverage.csv", index=False
    )


def plot_english_length_by_region(df: pd.DataFrame) -> None:
    """Compare English riddle lengths across explicit macro-regions."""
    usable = df.dropna(subset=["riddle_english"]).copy()
    usable["word_count"] = usable["riddle_english"].str.split().str.len()
    stats = (
        usable.groupby("region")["word_count"]
        .agg(
            q1=lambda x: x.quantile(0.25),
            median="median",
            q3=lambda x: x.quantile(0.75),
            n="size",
        )
        .reindex(REGION_ORDER)
    )
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.5))
    positions = range(len(stats))
    ax.hlines(positions, stats["q1"], stats["q3"], color=PALETTE["grey"], lw=2)
    ax.plot(stats["median"], positions, "o", color=PALETTE["blue"], ms=5)
    ax.set_yticks(list(positions), stats.index)
    ax.invert_yaxis()
    ax.set_xlabel("English riddle length (words): median and IQR")
    ax.set_title("Regional variation in English riddle length")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for y, row in enumerate(stats.itertuples()):
        ax.text(row.q3 + 0.4, y, f"n={row.n}", va="center", fontsize=7)
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_analysis", "answer_length_by_region"))
    plt.close(fig)
    stats.reset_index(names="region").to_csv(
        TABLE_DIR / "english_length_by_region.csv", index=False
    )
