"""Shared plotting primitives for evaluation figures."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from analysis import style


def plot_accuracy_dumbbell(
    table: pd.DataFrame,
    *,
    left_column: str,
    right_column: str,
    left_label: str,
    right_label: str,
    x_label: str,
    title: str,
    figsize: tuple[float, float],
    ytick_fontsize: float = 8,
) -> plt.Figure:
    """Plot two accuracy series connected by a labelled dumbbell.

    Values must be percentages on a 0--100 scale. The table index supplies
    the y-axis labels; callers are responsible for sorting it meaningfully.
    """
    values = table[[left_column, right_column]].dropna()
    if values.empty:
        raise ValueError("Cannot draw an accuracy dumbbell with no values")

    style.apply_style()
    positions = range(len(values))
    left = values[left_column]
    right = values[right_column]
    fig, ax = plt.subplots(figsize=figsize)
    ax.hlines(
        positions,
        left,
        right,
        color=style.PALETTE["light_grey"],
        lw=2,
        zorder=1,
    )
    ax.plot(
        left,
        positions,
        "o",
        ms=5,
        color=style.PALETTE["grey"],
        zorder=2,
        label=left_label,
    )
    ax.plot(
        right,
        positions,
        "o",
        ms=5,
        color=style.PALETTE["blue"],
        zorder=3,
        label=right_label,
    )
    for position, left_value, right_value in zip(positions, left, right, strict=True):
        near_left_edge = min(left_value, right_value) < 2
        left_offset = (4, -6) if near_left_edge else (-4, 0)
        right_offset = (4, 6) if near_left_edge else (4, 0)
        ax.annotate(
            f"{left_value:.1f}",
            (left_value, position),
            xytext=left_offset,
            textcoords="offset points",
            ha="left" if near_left_edge else "right",
            va="top" if near_left_edge else "center",
            fontsize=6.5,
            color=style.PALETTE["grey"],
        )
        ax.annotate(
            f"{right_value:.1f}",
            (right_value, position),
            xytext=right_offset,
            textcoords="offset points",
            ha="left",
            va="bottom" if near_left_edge else "center",
            fontsize=6.5,
            color=style.PALETTE["blue"],
        )
        midpoint = (left_value + right_value) / 2
        ax.annotate(
            f"{right_value - left_value:+.1f}pp",
            (midpoint, position),
            xytext=(16, 0) if near_left_edge else (0, 4),
            textcoords="offset points",
            ha="left" if near_left_edge else "center",
            va="center" if near_left_edge else "bottom",
            fontsize=5.5,
            color=style.PALETTE["black"],
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.8,
                "pad": 0.1,
            },
            zorder=4,
        )
    ax.set(
        yticks=list(positions),
        yticklabels=[str(label) for label in values.index],
        ylim=(-0.5, len(values) - 0.5),
        xlim=(0, 100),
        xlabel=x_label,
        title=title,
    )
    plt.setp(ax.get_yticklabels(), fontsize=ytick_fontsize)
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=7.5, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig
