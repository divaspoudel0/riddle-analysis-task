"""Plot country-level language coverage on a flattened world map."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon

from analysis.constants import RIDDLE_ANALYSIS_OUTPUT_DIR, figure_stem
from analysis.corpus import load_corpus_metadata
from analysis.style import (
    COVERAGE_CMAP,
    acl_figure_size,
    apply_style,
    save_figure_pair,
)

TABLE_DIR = RIDDLE_ANALYSIS_OUTPUT_DIR
COUNTRY_GEOMETRY_PATH = (
    Path(__file__).parent / "assets" / "ne_110m_admin_0_countries.geojson"
)

# Natural Earth uses formal map names for a few countries that are shorter in
# corpus_metadata.csv. These aliases are deliberately kept local to the map
# renderer rather than changing the canonical metadata labels.
GEOMETRY_COUNTRY_ALIASES: dict[str, str] = {
    "United States of America": "United States",
    "Republic of Serbia": "Serbia",
}

# Singapore is too small to appear in the 1:110m Natural Earth polygons. Draw
# it as a point so every country represented in the metadata remains visible.
SMALL_COUNTRY_POINTS: dict[str, tuple[float, float]] = {
    "Singapore": (103.82, 1.35),
}


def country_language_coverage(metadata: pd.DataFrame) -> pd.DataFrame:
    """Aggregate distinct languages and communities represented per country.

    Args:
        metadata: Validated rows from ``corpus_metadata.csv``.

    Returns:
        A sorted table with one row per country. ``languages`` is the map
        value; ``communities`` provides a separate audit count.
    """
    coverage = (
        metadata.drop_duplicates(["country", "language_code"])
        .groupby("country", as_index=False)
        .agg(languages=("language_code", "nunique"))
    )
    communities = metadata.groupby("country", as_index=False).agg(
        communities=("community", "nunique")
    )
    return coverage.merge(communities, on="country", validate="one_to_one").sort_values(
        "country"
    )


def _geometry_rings(geometry: dict[str, Any]) -> list[list[list[float]]]:
    """Return exterior rings for Polygon and MultiPolygon GeoJSON geometry."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return [coordinates[0]] if coordinates else []
    if geometry_type == "MultiPolygon":
        return [polygon[0] for polygon in coordinates if polygon]
    return []


def _load_country_features() -> list[dict[str, Any]]:
    """Load the vendored Natural Earth country geometries."""
    if not COUNTRY_GEOMETRY_PATH.exists():
        raise FileNotFoundError(
            f"Country geometry asset is missing: {COUNTRY_GEOMETRY_PATH}"
        )
    payload = json.loads(COUNTRY_GEOMETRY_PATH.read_text(encoding="utf-8"))
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError(f"Invalid country geometry asset: {COUNTRY_GEOMETRY_PATH}")
    return features


def _legend_ticks(maximum: int) -> list[int]:
    """Choose readable integer ticks for a small coverage-count scale."""
    candidates = [0, 1, 3, 5, 7, 10]
    ticks = [tick for tick in candidates if tick <= maximum]
    if maximum not in ticks:
        ticks.append(maximum)
    return sorted(set(ticks))


def plot_languages_by_country(metadata: pd.DataFrame | None = None) -> None:
    """Render and save the global language-coverage choropleth.

    The map shades countries by the number of distinct corpus languages in
    ``corpus_metadata.csv``. Countries absent from the metadata remain a pale
    neutral gray; Singapore is represented by a small colored point because it
    is omitted from the low-resolution boundary source. The map uses a
    flattened equirectangular longitude/latitude layout.
    """
    metadata = load_corpus_metadata() if metadata is None else metadata
    coverage = country_language_coverage(metadata)
    values = dict(zip(coverage["country"], coverage["languages"], strict=True))

    features = _load_country_features()
    geometry_countries = {
        GEOMETRY_COUNTRY_ALIASES.get(
            feature.get("properties", {}).get("ADMIN", ""),
            feature.get("properties", {}).get("ADMIN", ""),
        )
        for feature in features
    }
    missing = set(values) - geometry_countries - set(SMALL_COUNTRY_POINTS)
    if missing:
        raise ValueError(
            f"Map geometry is missing metadata countries: {sorted(missing)}"
        )

    maximum = int(coverage["languages"].max())
    normalizer = Normalize(vmin=0, vmax=maximum)
    patches: list[Polygon] = []
    colors: list[tuple[float, float, float, float]] = []

    for feature in features:
        properties = feature.get("properties", {})
        geometry_country = properties.get("ADMIN", "")
        country = GEOMETRY_COUNTRY_ALIASES.get(geometry_country, geometry_country)
        for ring in _geometry_rings(feature.get("geometry", {})):
            coordinates = np.asarray(ring, dtype=float)
            if coordinates.ndim != 2 or len(coordinates) < 3:
                continue
            patches.append(Polygon(coordinates[:, :2], closed=True))
            value = values.get(country)
            colors.append(
                COVERAGE_CMAP(normalizer(value))
                if value is not None
                else (*plt.cm.Greys(0.12)[:3], 1.0)
            )

    apply_style()
    fig = plt.figure(figsize=acl_figure_size(2, 3.0))
    ax = fig.add_subplot(111)
    ax.set_facecolor("white")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal", adjustable="box")
    ax.add_collection(
        PatchCollection(
            patches,
            facecolor=colors,
            edgecolor="white",
            linewidth=0.28,
            zorder=1,
        )
    )
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_axis_off()

    for country, (longitude, latitude) in SMALL_COUNTRY_POINTS.items():
        if country in values:
            ax.scatter(
                longitude,
                latitude,
                s=12,
                color=COVERAGE_CMAP(normalizer(values[country])),
                edgecolor="white",
                linewidth=0.35,
                zorder=2,
            )

    ax.set_title("Languages represented in the corpus by country", pad=11)
    scalar_mappable = ScalarMappable(norm=normalizer, cmap=COVERAGE_CMAP)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(
        scalar_mappable,
        ax=ax,
        orientation="horizontal",
        fraction=0.045,
        pad=0.06,
        aspect=38,
        ticks=_legend_ticks(maximum),
    )
    colorbar.set_label("Languages per country", fontsize=8, labelpad=3)
    colorbar.ax.tick_params(labelsize=7, length=2, width=0.5)
    colorbar.outline.set_visible(False)
    fig.tight_layout()
    save_figure_pair(fig, figure_stem("riddle_analysis", "languages_by_country"))
    plt.close(fig)

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(TABLE_DIR / "languages_by_country.csv", index=False)


def main() -> None:
    """Generate the country-level language coverage figure and table."""
    plot_languages_by_country()


if __name__ == "__main__":
    main()
