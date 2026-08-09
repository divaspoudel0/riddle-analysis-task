"""Load auditable corpus metadata and attach it to analysis frames."""

from __future__ import annotations

import pandas as pd

from analysis.constants import CORPUS_METADATA_PATH


def load_corpus_metadata() -> pd.DataFrame:
    """Read the community-to-region mapping maintained as a reviewable CSV."""
    metadata = pd.read_csv(CORPUS_METADATA_PATH)
    expected = {"community", "region", "language_group"}
    if set(metadata.columns) != expected or metadata["community"].duplicated().any():
        raise ValueError(f"Invalid corpus metadata file: {CORPUS_METADATA_PATH}")
    return metadata


def add_corpus_groups(
    frame: pd.DataFrame, *, community_column: str = "community"
) -> pd.DataFrame:
    """Attach region and multi-community language group labels to a frame."""
    grouped = frame.drop(columns=["region", "language_group"], errors="ignore").merge(
        load_corpus_metadata(),
        left_on=community_column,
        right_on="community",
        how="left",
    )
    if community_column != "community":
        grouped = grouped.drop(columns="community")
    if grouped["region"].isna().any():
        missing = sorted(
            grouped.loc[grouped["region"].isna(), community_column].unique()
        )
        raise ValueError(f"Missing region assignments for: {missing}")
    return grouped
