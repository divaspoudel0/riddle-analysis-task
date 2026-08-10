"""Human-evaluation paper figures (Appendix E + Julia's box plot).

Renders the human-eval layer of the benchmark as styled paper figures (PDF for
the manuscript, PNG for slides/Discord), reusing the *exact* verified compute
functions from the dashboard so numbers never diverge.

Figures (in figures/out/):
  human_boxplot_cultures   per-model distribution of human accuracy across the
                           fully-evaluated cultures, models on the y-axis, with
                           the minimum marked (Julia's request).
  human_error_types        how models fail: per-model outcome/error-type
                           breakdown (hallucination, wrong-entity, ...).
  human_floor_ceiling      heuristic floor vs human ceiling per model.
  human_semantic_broadening of the answers humans accepted, the share the
                           exact-match heuristic missed (what auto-eval loses).

Provisional: computed on communities with complete human evaluation. Rerun
after a newer flat file is dropped into dashboard/data/.

    python human_eval_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parents[1]))          # analysis/  (style.py)
sys.path.append(str(_HERE.parent / "dashboard"))  # reuse verified compute
import style  # noqa: E402
import build_static as bs  # noqa: E402  (load/leaderboard/fail_modes/coverage)

OUT = _HERE.parent / "figures" / "out"
TOTAL = bs.TOTAL_COMMUNITIES


def prep():
    m, mtime = bs.load()
    cov = bs.coverage(m.drop_duplicates(["community", "riddle_id", "model_display"]))
    complete = set(cov[cov.status == "complete"].index)
    return m, complete, mtime


def _save(fig, stem):
    style.save_figure(fig, (OUT / stem).with_suffix(".pdf"))
    fig.savefig((OUT / stem).with_suffix(".png"), dpi=300, bbox_inches="tight")
    print(f"wrote figures/out/{stem}.pdf / .png")


def fig_boxplot(m, complete):
    """Per-model human accuracy across cultures (box plot, minimum marked)."""
    style.apply_style()
    sub = m[m.community.isin(complete) & ~m.is_pending]
    per = (sub.groupby(["model_display", "community"])["is_correct"]
           .mean().mul(100).reset_index())
    order = (per.groupby("model_display")["is_correct"].median()
             .sort_values().index.tolist())
    data = [per.loc[per.model_display == mdl, "is_correct"].values for mdl in order]

    fig, ax = plt.subplots(figsize=(7, 8.5))
    bp = ax.boxplot(data, vert=False, widths=0.62, patch_artist=True, showfliers=True,
                    medianprops=dict(color=style.PALETTE["black"], lw=1.4),
                    flierprops=dict(marker="o", ms=3,
                                    markerfacecolor=style.PALETTE["grey"],
                                    markeredgecolor="none", alpha=0.5),
                    whiskerprops=dict(color=style.PALETTE["grey"]),
                    capprops=dict(color=style.PALETTE["grey"]))
    for patch in bp["boxes"]:
        patch.set(facecolor=style.PALETTE["sky_blue"], alpha=0.55,
                  edgecolor=style.PALETTE["blue"])
    # explicit minimum marker per model
    for i, d in enumerate(data, start=1):
        ax.plot(np.min(d), i, marker="D", ms=5, color=style.PALETTE["vermillion"],
                zorder=5)
    ax.plot([], [], "D", ms=5, color=style.PALETTE["vermillion"],
            label="minimum across cultures")
    ax.set_yticks(range(1, len(order) + 1))
    ax.set_yticklabels(order, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Human-eval accuracy per culture (%)")
    ax.set_title(f"Model performance across cultures (human eval)\n"
                 f"(N={len(complete)}/{TOTAL} complete cultures, provisional)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig


def fig_culture_heatmap(m, complete):
    """Per-culture human accuracy for every model (the 'rank per culture' view)."""
    style.apply_style()
    sub = m[m.community.isin(complete) & ~m.is_pending]
    piv = (sub.groupby(["model_display", "community"])["is_correct"]
           .mean().mul(100).unstack())
    piv = piv.loc[piv.mean(axis=1).sort_values(ascending=False).index]   # best model top
    piv = piv[piv.mean(axis=0).sort_values(ascending=False).index]       # easiest culture left

    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.grid(False)  # style.py enables gridlines; unwanted over a heatmap
    im = ax.imshow(piv.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=7.5)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                    color="white" if v > 55 else style.PALETTE["black"])
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Human-eval accuracy (%)", fontsize=9)
    ax.set_title(f"How models rank per culture (human eval)\n"
                 f"(N={len(complete)}/{TOTAL} complete cultures, provisional)")
    fig.tight_layout()
    return fig


def fig_error_types(m, complete):
    """How models fail: stacked outcome/error-type breakdown."""
    style.apply_style()
    fm = pd.DataFrame(bs.fail_modes(m, complete)).set_index("model")
    fm = fm[bs.FAIL_ORDER].loc[fm["Correct"].sort_values().index]  # worst at bottom
    fig, ax = plt.subplots(figsize=(8, 8))
    left = np.zeros(len(fm))
    for cat in bs.FAIL_ORDER:
        ax.barh(fm.index, fm[cat], left=left, color=bs.FAIL_COLORS[cat],
                label=cat, edgecolor="white", lw=0.4)
        left += fm[cat].values
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of human-scored responses (%)")
    ax.set_yticklabels(fm.index, fontsize=8)
    ax.set_title(f"How models fail: human error types\n"
                 f"(N={len(complete)}/{TOTAL} complete cultures, provisional)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=4, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, -0.13),
              frameon=False)
    fig.tight_layout()
    return fig


def fig_floor_ceiling(m, complete):
    """Heuristic floor vs human ceiling per model (dumbbell)."""
    style.apply_style()
    lb = bs.leaderboard(m, complete, strict=True).sort_values("Human (ceiling) %")
    y = range(len(lb))
    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.hlines(y, lb["Heuristic (floor) %"], lb["Human (ceiling) %"],
              color=style.PALETTE["light_grey"], lw=2, zorder=1)
    ax.plot(lb["Heuristic (floor) %"], y, "o", ms=6, color=style.PALETTE["grey"],
            zorder=2, label="Heuristic exact-match (floor)")
    ax.plot(lb["Human (ceiling) %"], y, "o", ms=6, color=style.PALETTE["blue"],
            zorder=3, label="Human judgement (ceiling)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(lb.index, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Accuracy (%)")
    ax.set_title(f"Heuristic floor vs human ceiling\n"
                 f"(N={len(complete)}/{TOTAL} complete cultures, provisional)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig


def fig_semantic_broadening(m, complete):
    """Of answers humans accepted, the share exact-match missed (per model)."""
    style.apply_style()
    r = m[m.is_human & m.community.isin(complete) & m.judge_verdict.notna()].copy()
    r["h"] = r.score.eq(3.0)
    r["j"] = r.judge_verdict.eq("correct")
    hc = r[r.h]
    miss = (hc.assign(missed=~hc.j).groupby("model_display")["missed"].mean()
            .mul(100).sort_values())
    fig, ax = plt.subplots(figsize=(7, 7.5))
    ax.barh(miss.index, miss.values, color=style.PALETTE["orange"])
    ax.set_xlabel("Human-correct answers missed by exact-match (%)")
    ax.set_yticklabels(miss.index, fontsize=8)
    ax.set_title("Correct answers missed by the exact-match heuristic\n"
                 "(share of human-accepted answers the heuristic rejected)")
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m, complete, mtime = prep()
    print(f"flat file {mtime} | {len(complete)}/{TOTAL} complete cultures")
    _save(fig_boxplot(m, complete), "human_boxplot_cultures")
    _save(fig_culture_heatmap(m, complete), "human_culture_heatmap")
    _save(fig_error_types(m, complete), "human_error_types")
    _save(fig_floor_ceiling(m, complete), "human_floor_ceiling")
    _save(fig_semantic_broadening(m, complete), "human_semantic_broadening")


if __name__ == "__main__":
    main()
