"""Figures: per-community difficulty and judge-vs-human agreement.

Two paper figures on the COMPLETE-human communities only, from the same
joined frame human_eval.py writes:

  community_accuracy_exact_match_vs_human.{png,pdf}  mean accuracy per
                                  community, exact-match floor vs. human ceiling.
  exact_match_agreement_by_community.{png,pdf}       Cohen's kappa between
                                  exact matching and human evaluation.

"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis import style
from analysis.constants import figure_stem
from analysis.eval_analysis.data import (
    STRICT_SCORE,
    coverage_report,
    load_human_evaluation,
)
from analysis.eval_analysis.plot_helpers import plot_accuracy_dumbbell


def _complete(m: pd.DataFrame) -> tuple[pd.DataFrame, set]:
    complete = set(coverage_report(m).query("status == 'complete'").index)
    return m[m.community.isin(complete) & ~m.is_pending].copy(), complete


def difficulty_fig(m: pd.DataFrame, strict: bool = True):
    style.apply_style()
    sub, complete = _complete(m)
    col = "is_correct" if strict else "is_correct_lenient"
    human = sub.groupby("community")[col].mean().mul(100)
    floor = sub.assign(a=sub.is_exact_match).groupby("community")["a"].mean().mul(100)
    d = pd.DataFrame({"human": human, "floor": floor}).sort_values("human")

    return plot_accuracy_dumbbell(
        d,
        left_column="floor",
        right_column="human",
        left_label="Exact match",
        right_label="Human evaluation",
        x_label="Mean accuracy across models (%)",
        title=f"Community Difficulty: Exact Match and Human Evaluation ({len(complete)} Communities)",
        figsize=(7, 9),
        ytick_fontsize=8,
    )


def kappa_fig(m: pd.DataFrame):
    style.apply_style()
    _, complete = _complete(m)
    is_human = m.scoring_method.eq("human_eval")
    r = m[is_human & m.community.isin(complete) & m.is_exact_match.notna()].copy()
    r["h"] = r.score.eq(STRICT_SCORE)
    r["j"] = r.is_exact_match

    def kappa(x):
        po = (x.h == x.j).mean()
        ph, pj = x.h.mean(), x.j.mean()
        pe = ph * pj + (1 - ph) * (1 - pj)
        return np.nan if pe == 1 else (po - pe) / (1 - pe)

    per = r.groupby("community").apply(kappa).sort_values()
    overall = kappa(r)

    fig, ax = plt.subplots(figsize=(7, 9))
    y = range(len(per))
    colors = [
        style.PALETTE["vermillion"] if v < 0.4 else style.PALETTE["blue"]
        for v in per.values
    ]
    ax.barh(list(y), per.values, color=colors)
    ax.axvline(
        overall,
        color=style.PALETTE["grey"],
        ls="--",
        lw=1.2,
        label=f"overall κ = {overall:.2f}",
    )
    ax.set_yticks(list(y), per.index, fontsize=8)
    ax.set_ylim(-0.5, len(per) - 0.5)
    ax.set_xlabel("Cohen's κ: exact match vs. human evaluation")
    ax.set_title(
        f"Exact-Match Agreement with Human Evaluation ({len(complete)} Communities)"
    )
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8)
    fig.tight_layout()
    return fig


def main() -> None:
    m = load_human_evaluation()
    for name, fig in [
        (
            "community_accuracy_exact_match_vs_human",
            difficulty_fig(m, strict=True),
        ),
        ("exact_match_agreement_by_community", kappa_fig(m)),
    ]:
        out = figure_stem("eval_analysis", name)
        style.save_figure_pair(fig, out)
        print(f"Wrote {out}.pdf and {out}.png")


if __name__ == "__main__":
    main()
