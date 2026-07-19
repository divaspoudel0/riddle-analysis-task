"""Figure 1: v0 automatic-evaluation leaderboard (Cleveland dot plot).

Pure function `make_leaderboard(df) -> fig`, plus a CLI that saves PDF (paper)
and PNG (slides/blog). Import the function in the notebook to render inline.

    from figures.leaderboard import make_leaderboard
    fig = make_leaderboard(df)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Put analysis/ (for style.py) and model_results_v0/ (for metrics.py) on path.
_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parents[2]))  # analysis/
sys.path.append(str(_HERE.parents[1]))  # analysis/model_results_v0/
import style  # noqa: E402
from metrics import add_derived_columns, model_summary_with_ci  # noqa: E402

FULL_N = 4400  # complete run size (44 communities x 100 riddles)
FLOOR_THRESHOLD = 0.05  # format-failure rate above which a score is a floor


def make_leaderboard(df: pd.DataFrame, n_boot: int = 2000):
    """Cleveland dot plot of accuracy over completed responses, with 95% CIs.

    Annotates reduced denominators (n=...) and marks token-truncation floors (*).
    """
    style.apply_style()
    if "is_completed" not in df.columns:
        df = add_derived_columns(df)

    lb = model_summary_with_ci(df, n_boot=n_boot).iloc[::-1]  # worst at bottom

    labels = []
    for model, n, ffr in zip(lb.index, lb.n_completed, lb.format_failure_rate):
        label = model if n >= FULL_N else f"{model} (n={int(n):,})"
        if ffr >= FLOOR_THRESHOLD:
            label += " *"
        labels.append(label)

    fig, ax = plt.subplots(figsize=(7.5, 8))
    y = list(range(len(lb)))
    ax.hlines(y, lb.ci_low * 100, lb.ci_high * 100,
              color=style.PALETTE["grey"], lw=1.5, zorder=1)
    ax.plot(lb.accuracy * 100, y, "o", color=style.PALETTE["blue"],
            markersize=6, zorder=2)

    ax.set_yticks(y, labels)
    ax.set_ylim(-0.5, len(lb) - 0.5)
    ax.set_xlabel("Accuracy over completed responses (%), heuristic judge")
    ax.set_title("v0 leaderboard, automatic evaluation")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)

    fig.text(
        0.01, 0.005,
        "(n=...) = completed responses, shown where below 4,400.   "
        "* = floor: >=5% of responses hit the token budget before answering.",
        fontsize=7, color=style.PALETTE["grey"],
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def main() -> None:
    parquet = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "data/processed/results_tidy.parquet"
    )
    df = pd.read_parquet(parquet)
    fig = make_leaderboard(df)
    out = Path("figures/out/leaderboard")
    style.save_figure(fig, out.with_suffix(".pdf"))
    fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
    print(f"Wrote {out}.pdf and {out}.png")


if __name__ == "__main__":
    main()
