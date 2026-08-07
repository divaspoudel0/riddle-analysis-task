"""Figure: floor (heuristic) vs ceiling (human) leaderboard, v0.

Dumbbell plot on the COMPLETE-human communities only: for each model, the
heuristic-judge accuracy (floor) and the human accuracy (ceiling), connected,
so the lift from strict auto-matching to human judgement is the story.

Provisional: computed on the communities with complete human eval; the count
is printed in the title. Rerun after human_eval.py refreshes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parents[2]))  # analysis/
sys.path.append(str(_HERE.parents[1]))  # model_results_v0/
import style  # noqa: E402

JOINED = Path("data/processed/human_joined.parquet")
COVERAGE = Path("data/processed/human_eval_coverage.parquet")
COVERAGE_CSV = Path("data/processed/human_eval_coverage.csv")
TOTAL_COMMUNITIES = 44


def make_human_leaderboard(strict: bool = True):
    style.apply_style()
    m = pd.read_parquet(JOINED)
    cov = pd.read_csv(COVERAGE_CSV)
    complete = set(cov.loc[cov.status == "complete", "community"])
    sub = m[m.community.isin(complete)].copy()

    col = "is_correct" if strict else "is_correct_lenient"
    human = sub.groupby("model_display")[col].mean().mul(100)
    # floor = heuristic judge on the same communities/rows
    auto = (
        sub.assign(auto_correct=sub.judge_verdict.eq("correct"))
        .groupby("model_display")["auto_correct"].mean().mul(100)
    )
    lb = pd.DataFrame({"human": human, "auto": auto}).sort_values("human")

    fig, ax = plt.subplots(figsize=(7, 8))
    y = range(len(lb))
    ax.hlines(y, lb.auto, lb.human, color=style.PALETTE["light_grey"],
              lw=2, zorder=1)
    ax.plot(lb.auto, y, "o", color=style.PALETTE["grey"], markersize=6,
            zorder=2, label="Heuristic judge (floor)")
    ax.plot(lb.human, y, "o", color=style.PALETTE["blue"], markersize=6,
            zorder=3, label="Human (ceiling)")
    ax.set_yticks(list(y), lb.index, fontsize=8)
    ax.set_ylim(-0.5, len(lb) - 0.5)
    ax.set_xlabel(f"Accuracy (%), {'strict (top score)' if strict else 'lenient (score >= 2)'}")
    ax.set_title(
        f"v0 human vs heuristic, complete communities "
        f"(N={len(complete)}/{TOTAL_COMMUNITIES}, provisional)"
    )
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8)
    fig.text(0.01, 0.005,
             "Human eval on the communities completed so far; rankings may "
             "shift as coverage grows.",
             fontsize=7, color=style.PALETTE["grey"])
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def main() -> None:
    for strict, tag in [(True, "strict"), (False, "lenient")]:
        fig = make_human_leaderboard(strict=strict)
        out = Path(f"figures/out/human_leaderboard_{tag}")
        style.save_figure(fig, out.with_suffix(".pdf"))
        fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
        print(f"Wrote {out}.pdf and {out}.png")


if __name__ == "__main__":
    main()
