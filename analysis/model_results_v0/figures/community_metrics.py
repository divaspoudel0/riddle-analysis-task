"""Figures: per-community difficulty and judge-vs-human agreement (v0).

Two paper figures on the COMPLETE-human communities only, from the same
joined frame human_eval.py writes:

  community_difficulty.{png,pdf}  mean accuracy per community, heuristic floor
                                  vs human ceiling (which cultures are hard).
  judge_human_kappa.{png,pdf}     Cohen's kappa (heuristic judge vs human) per
                                  community; low kappa = string-matching is
                                  unreliable there (non-Latin scripts).

Provisional: computed on communities with complete human eval. Rerun after
human_eval.py refreshes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parents[2]))  # analysis/
sys.path.append(str(_HERE.parents[1]))  # model_results_v0/
import style  # noqa: E402

JOINED = Path("data/processed/human_joined.parquet")
COVERAGE_CSV = Path("data/processed/human_eval_coverage.csv")
TOTAL_COMMUNITIES = 44
STRICT_SCORE = 3.0


def _complete(m: pd.DataFrame) -> tuple[pd.DataFrame, set]:
    cov = pd.read_csv(COVERAGE_CSV)
    complete = set(cov.loc[cov.status == "complete", "community"])
    return m[m.community.isin(complete) & ~m.is_pending].copy(), complete


def difficulty_fig(m: pd.DataFrame, strict: bool = True):
    style.apply_style()
    sub, complete = _complete(m)
    col = "is_correct" if strict else "is_correct_lenient"
    human = sub.groupby("community")[col].mean().mul(100)
    floor = (sub.assign(a=sub.judge_verdict.eq("correct"))
             .groupby("community")["a"].mean().mul(100))
    d = pd.DataFrame({"human": human, "floor": floor}).sort_values("human")

    fig, ax = plt.subplots(figsize=(7, 9))
    y = range(len(d))
    ax.hlines(y, d.floor, d.human, color=style.PALETTE["light_grey"], lw=2, zorder=1)
    ax.plot(d.floor, y, "o", color=style.PALETTE["grey"], ms=6, zorder=2,
            label="Heuristic judge (floor)")
    ax.plot(d.human, y, "o", color=style.PALETTE["blue"], ms=6, zorder=3,
            label="Human (ceiling)")
    ax.set_yticks(list(y), d.index, fontsize=8)
    ax.set_ylim(-0.5, len(d) - 0.5)
    ax.set_xlabel(f"Mean accuracy across models (%), "
                  f"{'strict' if strict else 'lenient'}")
    ax.set_title(f"v0 community difficulty, complete communities "
                 f"(N={len(complete)}/{TOTAL_COMMUNITIES}, provisional)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8)
    fig.tight_layout()
    return fig


def kappa_fig(m: pd.DataFrame):
    style.apply_style()
    cov = pd.read_csv(COVERAGE_CSV)
    complete = set(cov.loc[cov.status == "complete", "community"])
    is_human = m.scoring_method.eq("human_eval")
    r = m[is_human & m.community.isin(complete) & m.judge_verdict.notna()].copy()
    r["h"] = r.final_score.eq(STRICT_SCORE)
    r["j"] = r.judge_verdict.eq("correct")

    def kappa(x):
        po = (x.h == x.j).mean()
        ph, pj = x.h.mean(), x.j.mean()
        pe = ph * pj + (1 - ph) * (1 - pj)
        return np.nan if pe == 1 else (po - pe) / (1 - pe)

    per = r.groupby("community").apply(kappa).sort_values()
    overall = kappa(r)

    fig, ax = plt.subplots(figsize=(7, 9))
    y = range(len(per))
    colors = [style.PALETTE["vermillion"] if v < 0.4 else style.PALETTE["blue"]
              for v in per.values]
    ax.barh(list(y), per.values, color=colors)
    ax.axvline(overall, color=style.PALETTE["grey"], ls="--", lw=1.2,
               label=f"overall κ = {overall:.2f}")
    ax.set_yticks(list(y), per.index, fontsize=8)
    ax.set_ylim(-0.5, len(per) - 0.5)
    ax.set_xlabel("Cohen's κ (heuristic judge vs human)")
    ax.set_title(f"v0 judge–human agreement, complete communities "
                 f"(N={len(complete)}/{TOTAL_COMMUNITIES}, provisional)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8)
    fig.text(0.01, 0.005,
             "Red: κ < 0.4 (string-matching unreliable, usually non-Latin "
             "scripts). Provisional; rerun as coverage grows.",
             fontsize=7, color=style.PALETTE["grey"])
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def main() -> None:
    m = pd.read_parquet(JOINED)
    outdir = Path("figures/out")
    for name, fig in [("community_difficulty", difficulty_fig(m, strict=True)),
                      ("judge_human_kappa", kappa_fig(m))]:
        out = outdir / name
        style.save_figure(fig, out.with_suffix(".pdf"))
        fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight")
        print(f"Wrote {out}.pdf and {out}.png")


if __name__ == "__main__":
    main()
