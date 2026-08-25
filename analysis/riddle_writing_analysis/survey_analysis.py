"""Anonymized descriptive analysis of contributor reflection responses."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea

from analysis.constants import (
    REPO_ROOT,
    RIDDLE_WRITING_OUTPUT_DIR,
    SURVEY_TOPICS,
    figure_stem,
)
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

DATA_PATH = (
    Path(__file__).resolve().parent
    / "data/[MCB]_Analysis_MasterSheet - reflection_form.csv"
)
OUTPUT_DIR = RIDDLE_WRITING_OUTPUT_DIR
TOPIC_MATCH_PATH = (
    REPO_ROOT / "analysis/model_results/outputs/topic_match_rate_summary.csv"
)
PII_COLUMNS = {"Timestamp", "Your Discord name", "Your Discord handle or user ID"}
TOPICS = SURVEY_TOPICS
NOT_APPLICABLE_DIFFICULTY_RESPONSE = "0 - N/A"


def _count_percentage_label(value: int, denominator: int) -> HPacker:
    """Return a compact, two-colour count-and-percentage label."""
    return HPacker(
        children=[
            TextArea(str(value), textprops={"fontsize": 7, "color": PALETTE["black"]}),
            TextArea(
                f"({value / denominator:.0%})",
                textprops={"fontsize": 7, "color": PALETTE["grey"]},
            ),
        ],
        align="center",
        pad=0,
        sep=3,
    )


def _add_horizontal_count_label(
    ax: plt.Axes,
    value: int,
    index: int,
    denominator: int,
    *,
    offset: float = 0.35,
) -> None:
    """Annotate a horizontal count bar with dark count and muted percentage."""
    ax.add_artist(
        AnnotationBbox(
            _count_percentage_label(value, denominator),
            (value + offset, index),
            box_alignment=(0, 0.5),
            frameon=False,
            pad=0,
            annotation_clip=False,
        )
    )


def _add_vertical_count_label(
    ax: plt.Axes,
    value: int,
    index: int,
    denominator: int,
    *,
    offset: float = 0.6,
) -> None:
    """Annotate a vertical count bar with a centered count and percentage."""
    label_y = value + max(offset, 1.2)
    ax.add_artist(
        AnnotationBbox(
            _count_percentage_label(value, denominator),
            (index, label_y),
            box_alignment=(0.5, 0.5),
            frameon=False,
            pad=0,
            annotation_clip=False,
        )
    )


def _column_by_prefix(columns: pd.Index, prefix: str) -> str:
    """Return the unique source column beginning with ``prefix``."""
    matches = [column for column in columns if column.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one column beginning {prefix!r}; found {matches}"
        )
    return matches[0]


def load_survey(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load, normalize, and anonymize the reflection survey by default."""
    raw = pd.read_csv(path)
    survey = raw.drop(
        columns=[column for column in PII_COLUMNS if column in raw.columns]
    ).copy()
    rename = {
        _column_by_prefix(
            survey.columns, "Which national-linguistic community"
        ): "community",
        _column_by_prefix(survey.columns, "How confident are you"): "confidence",
        _column_by_prefix(survey.columns, "On average, how long"): "time_per_riddle",
        _column_by_prefix(survey.columns, "How easy was it"): "translation_ease",
        _column_by_prefix(
            survey.columns, "How would you rate the difficulty"
        ): "overall_difficulty",
        _column_by_prefix(
            survey.columns, "What resources did you use"
        ): "resources_used",
        _column_by_prefix(survey.columns, "How locally specific"): "local_specificity",
        _column_by_prefix(
            survey.columns, "How would you rate the clarity"
        ): "instruction_clarity",
    }
    for topic in TOPICS:
        source = _column_by_prefix(
            survey.columns,
            f"How difficult was it to write riddles for each topic, from 0 to 5? [{topic}",
        )
        rename[source] = f"difficulty_{topic.casefold().replace(' ', '_')}"
    survey = survey.rename(columns=rename)
    numeric_columns = [
        "confidence",
        "translation_ease",
        "overall_difficulty",
        "instruction_clarity",
        *[f"difficulty_{topic.casefold().replace(' ', '_')}" for topic in TOPICS],
    ]
    for column in numeric_columns:
        survey[column] = pd.to_numeric(
            survey[column].replace(NOT_APPLICABLE_DIFFICULTY_RESPONSE, pd.NA),
            errors="coerce",
        )
    return survey


def plot_topic_difficulty(survey: pd.DataFrame) -> pd.DataFrame:
    """Plot 1--5 topic-writing difficulty and model-accuracy correlation."""
    rows = []
    for topic in TOPICS:
        values = survey[f"difficulty_{topic.casefold().replace(' ', '_')}"]
        rows.append(
            {
                "topic": topic,
                "mean_difficulty": values.mean(),
                "responses": values.notna().sum(),
            }
        )
    summary = pd.DataFrame(rows).sort_values("mean_difficulty")
    if not TOPIC_MATCH_PATH.exists():
        raise FileNotFoundError(
            "Run `python -m analysis.model_results.main` before the writing analysis."
        )
    model_summary = pd.read_csv(TOPIC_MATCH_PATH)
    model_summary["topic"] = model_summary["topic"].replace({"Wildcard": "Wild Card"})
    comparison = summary.merge(model_summary, on="topic", how="inner")
    topic_accuracy_comparison = comparison.loc[
        comparison["topic"] != "Wild Card"
    ].copy()
    correlation = (
        topic_accuracy_comparison["mean_difficulty"]
        .rank()
        .corr(topic_accuracy_comparison["mean_model_match_rate"].rank())
    )

    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 3.15))
    colors = [
        PALETTE["vermillion"] if topic == summary.iloc[-1].topic else PALETTE["grey"]
        for topic in summary.topic
    ]
    ax.hlines(
        y=summary.topic,
        xmin=1,
        xmax=summary.mean_difficulty,
        color=colors,
        linewidth=2,
        zorder=2,
    )
    ax.scatter(
        summary.mean_difficulty,
        summary.topic,
        color=colors,
        s=32,
        zorder=3,
    )
    ax.set_xlim(1, 5)
    ax.set_xticks(range(1, 6))
    ax.set_xlabel("Mean reported writing difficulty (1--5)")
    ax.set_title("Writing difficulty by benchmark topic")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for index, row in enumerate(summary.itertuples()):
        ax.text(
            row.mean_difficulty + 0.08,
            index,
            f"{row.mean_difficulty:.2f}",
            va="center",
            fontsize=7,
        )
        ax.annotate(
            f"; n={row.responses} ({row.responses / len(survey):.0%})",
            xy=(row.mean_difficulty + 0.08, index),
            xytext=(12, 0),
            textcoords="offset points",
            va="center",
            fontsize=7,
            color=PALETTE["grey"],
        )
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("riddle_writing_analysis", "topic_writing_difficulty")
    )
    plt.close(fig)

    # This is descriptive because it contains only eight topic aggregates.
    fig, correlation_ax = plt.subplots(figsize=acl_figure_size(1, 3.25))
    label_offsets = {
        "Everyday Life": (-8, 7),
        "Kid's World": (-8, -9),
        "National Heritage": (-8, -9),
        "Geography": (-8, 7),
        "History": (7, 5),
        "Sports": (7, 5),
        "Arts": (7, -8),
        "Politics": (7, -5),
    }
    for row in topic_accuracy_comparison.itertuples():
        correlation_ax.scatter(
            row.mean_difficulty,
            row.mean_model_match_rate * 100,
            color=PALETTE["vermillion"],
            s=32,
            zorder=3,
        )
        correlation_ax.annotate(
            row.topic,
            (row.mean_difficulty, row.mean_model_match_rate * 100),
            xytext=label_offsets[row.topic],
            textcoords="offset points",
            ha="right" if label_offsets[row.topic][0] < 0 else "left",
            va="center",
            fontsize=7,
        )

    correlation_ax.set_xlim(1, 5)
    correlation_ax.set_xticks(range(1, 6))
    correlation_ax.set_ylim(18, 30)
    correlation_ax.set_yticks(range(18, 31, 3))
    correlation_ax.set_xlabel("Mean reported writing difficulty (1--5)")
    correlation_ax.set_ylabel("Mean strict model match rate (%)")
    correlation_ax.set_title(
        f"Topic-level correlation (Spearman $\\rho$={correlation:.2f})"
    )
    correlation_ax.grid(alpha=0.35)
    fig.tight_layout()
    save_figure_pair(
        fig,
        figure_stem("riddle_writing_analysis", "topic_difficulty_vs_model_accuracy"),
    )
    plt.close(fig)
    topic_accuracy_comparison["spearman_rho"] = correlation
    topic_accuracy_comparison.to_csv(
        OUTPUT_DIR / "topic_difficulty_model_accuracy_comparison.csv", index=False
    )
    return summary


def plot_specificity(survey: pd.DataFrame) -> pd.DataFrame:
    """Plot contributors' self-reported local-specificity strategies."""
    labels = {
        "Mostly known across the whole national-linguistic community": "Mostly national",
        "Many require regional or local knowledge": "Mostly regional/local",
        "Some are broadly known, some are region-specific": "Mixed",
        "Many require specialized, older, or niche knowledge": "Niche/specialized",
    }
    counts = (
        survey["local_specificity"]
        .map(labels)
        .value_counts()
        .reindex(labels.values(), fill_value=0)
        .sort_values()
    )
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.4))
    ax.barh(counts.index, counts.values, color=PALETTE["blue"], height=0.62)
    ax.set_xlabel("Respondents")
    ax.set_title("Self-reported specificity strategy")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for index, value in enumerate(counts.values):
        _add_horizontal_count_label(ax, value, index, int(counts.sum()))
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("riddle_writing_analysis", "specificity_strategy")
    )
    plt.close(fig)
    return counts.rename_axis("strategy").rename("respondents").reset_index()


def plot_ai_uses(survey: pd.DataFrame) -> pd.DataFrame:
    """Count explicitly selected AI-use functions in the resource responses."""
    resources = survey["resources_used"].fillna("").str.casefold()
    summary = pd.DataFrame(
        {
            "use": ["Testing difficulty", "Brainstorming", "Paraphrasing/co-writing"],
            "respondents": [
                resources.str.contains("testing difficulty").sum(),
                resources.str.contains("brainstorming").sum(),
                resources.str.contains("paraphras").sum(),
            ],
        }
    ).sort_values("respondents")
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.1))
    colors = [
        PALETTE["blue"] if use == "Testing difficulty" else PALETTE["grey"]
        for use in summary["use"]
    ]
    ax.barh(summary["use"], summary["respondents"], color=colors, height=0.62)
    ax.set_xlabel("Respondents selecting the use")
    ax.set_title("How contributors report using generative AI")
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    for index, row in enumerate(summary.itertuples()):
        _add_horizontal_count_label(ax, row.respondents, index, len(survey))
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_writing_analysis", "ai_use_functions"))
    plt.close(fig)
    return summary


def _plot_count_bars(
    labels: Sequence[str],
    counts: Sequence[int],
    *,
    filename: str,
    title: str,
    xlabel: str = "Respondents",
    highlight: str | None = None,
    height: float = 2.4,
    denominator: int | None = None,
) -> None:
    """Save a consistently styled horizontal count plot.

    This small helper keeps every descriptive survey figure on the same scale,
    typography, and export path while leaving the underlying summaries easy to
    inspect as CSV files.
    """
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, height))
    colors = [
        PALETTE["blue"] if label == highlight else PALETTE["grey"] for label in labels
    ]
    ax.barh(labels, counts, color=colors, height=0.62)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    denominator = denominator or sum(counts)
    for index, value in enumerate(counts):
        _add_horizontal_count_label(ax, value, index, denominator)
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_writing_analysis", filename))
    plt.close(fig)


def plot_confidence_distribution(survey: pd.DataFrame) -> pd.DataFrame:
    """Plot the distribution of self-reported community-representation confidence."""
    summary = (
        survey["confidence"]
        .value_counts()
        .reindex(range(1, 6), fill_value=0)
        .rename_axis("confidence")
        .rename("respondents")
        .reset_index()
    )
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 2.35))
    ax.bar(
        summary["confidence"].astype(str),
        summary["respondents"],
        color=PALETTE["blue"],
        width=0.62,
    )
    ax.set_xlabel("Confidence (1 = low, 5 = high)")
    ax.set_ylabel("Respondents")
    ax.set_title("Confidence in community representation")
    ax.set_ylim(0, max(summary["respondents"]) + 6)
    for index, value in enumerate(summary["respondents"]):
        _add_vertical_count_label(ax, value, index, len(survey))
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("riddle_writing_analysis", "confidence_distribution")
    )
    plt.close(fig)
    return summary


def plot_time_per_riddle(survey: pd.DataFrame) -> pd.DataFrame:
    """Plot respondents' estimated time to write a complete riddle."""
    order = [
        "Less than 5 minutes",
        "5-10 minutes",
        "10-15 minutes",
        "More than 15 minutes",
        "More than 30 minutes",
        "It varied too much to estimate",
    ]
    labels = {
        "Less than 5 minutes": "Less than 5 min",
        "5-10 minutes": "5--10 min",
        "10-15 minutes": "10--15 min",
        "More than 15 minutes": "More than 15 min",
        "More than 30 minutes": "More than 30 min",
        "It varied too much to estimate": "Varied / no estimate",
    }
    summary = pd.DataFrame(
        {
            "time": order,
            "respondents": [
                survey["time_per_riddle"].eq(value).sum() for value in order
            ],
        }
    )
    _plot_count_bars(
        [labels[value] for value in order],
        summary["respondents"].tolist(),
        filename="time_per_riddle",
        title="Estimated time to write one riddle",
        highlight="5--10 min",
        height=2.85,
        denominator=len(survey),
    )
    return summary


def plot_resources_used(survey: pd.DataFrame) -> pd.DataFrame:
    """Count selected resources without parsing free-text additions as options."""
    resources = survey["resources_used"].fillna("")
    options = [
        ("Personal knowledge/experience", "Personal knowledge/Experience"),
        ("Online encyclopedia/general search", "Online encyclopedia/General search"),
        (
            "Native speaker/community member",
            "Consulting a native speaker/Community member",
        ),
        (
            "Books, articles, or other references",
            "Books, articles, websites, or other reference materials",
        ),
        ("AI: testing difficulty", "AI tools for testing difficulty"),
        ("AI: brainstorming", "AI tools for brainstorming"),
    ]
    summary = pd.DataFrame(
        {
            "resource": [label for label, _ in options],
            "respondents": [
                resources.str.contains(pattern, regex=False).sum()
                for _, pattern in options
            ],
        }
    ).sort_values("respondents")
    _plot_count_bars(
        summary["resource"].tolist(),
        summary["respondents"].tolist(),
        filename="resources_used",
        title="Resources used while writing riddles",
        xlabel="Respondents selecting the resource",
        highlight="Personal knowledge/experience",
        height=2.85,
        denominator=len(survey),
    )
    return summary


def summarize_scale_relationships(survey: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregate correlations without retaining person-level responses."""
    metrics = survey[
        ["confidence", "translation_ease", "overall_difficulty", "instruction_clarity"]
    ]
    # Ranking first implements Spearman correlation without requiring SciPy.
    return metrics.rank().corr().reset_index(names="metric")
