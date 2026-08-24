"""Load auditable corpus metadata and attach it to analysis frames."""

from __future__ import annotations

import pandas as pd

from analysis.constants import CORPUS_METADATA_PATH

METADATA_COLUMNS: tuple[str, ...] = (
    "community",
    "language_code",
    "language_label",
    "country",
    "region",
    "language_group",
)
REQUIRED_METADATA_VALUES: tuple[str, ...] = (
    "language_code",
    "language_label",
    "country",
    "region",
)


def load_corpus_metadata() -> pd.DataFrame:
    """Read and validate the reviewable per-community metadata table."""
    metadata = pd.read_csv(CORPUS_METADATA_PATH)
    if tuple(metadata.columns) != METADATA_COLUMNS:
        raise ValueError(f"Invalid corpus metadata file: {CORPUS_METADATA_PATH}")
    if metadata["community"].duplicated().any() or metadata["community"].isna().any():
        raise ValueError(
            f"Corpus metadata has duplicate or empty communities: {CORPUS_METADATA_PATH}"
        )
    if metadata[list(REQUIRED_METADATA_VALUES)].isna().any().any():
        raise ValueError(
            f"Corpus metadata has empty required values: {CORPUS_METADATA_PATH}"
        )
    conflicting_labels = (
        metadata.groupby("language_code")["language_label"].nunique() > 1
    )
    if conflicting_labels.any():
        languages = sorted(conflicting_labels[conflicting_labels].index)
        raise ValueError(f"Conflicting labels for language codes: {languages}")
    return metadata


def language_label_map() -> dict[str, str]:
    """Return the canonical human-readable label for each ISO language code."""
    metadata = load_corpus_metadata().drop_duplicates(
        ["language_code", "language_label"]
    )
    return dict(
        zip(
            metadata["language_code"],
            metadata["language_label"],
            strict=True,
        )
    )


def country_map() -> dict[str, str]:
    """Return the canonical country for each community identifier."""
    metadata = load_corpus_metadata()
    return dict(zip(metadata["community"], metadata["country"], strict=True))


def add_corpus_groups(
    frame: pd.DataFrame, *, community_column: str = "community"
) -> pd.DataFrame:
    """Attach canonical corpus metadata to an analysis frame."""
    metadata = load_corpus_metadata()
    metadata_columns = [column for column in METADATA_COLUMNS if column != "community"]
    grouped = frame.drop(columns=metadata_columns, errors="ignore").merge(
        metadata,
        left_on=community_column,
        right_on="community",
        how="left",
        validate="many_to_one",
    )
    if community_column != "community":
        grouped = grouped.drop(columns="community")
    if grouped[list(REQUIRED_METADATA_VALUES)].isna().any().any():
        missing = sorted(
            grouped.loc[
                grouped[list(REQUIRED_METADATA_VALUES)].isna().any(axis=1),
                community_column,
            ].unique()
        )
        raise ValueError(f"Missing corpus metadata assignments for: {missing}")
    return grouped
