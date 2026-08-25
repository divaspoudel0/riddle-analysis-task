"""Generate the human-evaluation exact-match leaderboard."""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import MODEL_RESULTS_OUTPUT_DIR, figure_stem
from analysis.eval_analysis.data import coverage_report, load_human_evaluation
from analysis.model_results.metrics import bootstrap_ci, clustered_bootstrap_ci
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair
from analysis.utils import write_csv

OUTPUT_DIR = MODEL_RESULTS_OUTPUT_DIR


def load_human_eval_leaderboard(
    *, n_boot: int = 2000, alpha: float = 0.05
) -> pd.DataFrame:
    """Compute human-evaluation exact-match accuracy on complete communities.

    Includes bootstrap 95 % confidence intervals for exact-match and human
    accuracy.  CI computation uses community-clustered resampling so that
    riddles within the same community are not treated as independent.
    """
    frame = load_human_evaluation()
    complete = set(coverage_report(frame).query("status == 'complete'").index)
    scored = frame[frame["community"].isin(complete) & ~frame["is_pending"]]

    rows: list[dict[str, object]] = []
    for model, grp in scored.groupby("model_display"):
        em_vals = grp["is_exact_match"].to_numpy(dtype=float)
        hu_vals = grp["is_correct"].to_numpy(dtype=float)
        clusters = grp["community"].to_numpy() if "community" in grp.columns else None

        if clusters is not None and len(np.unique(clusters)) > 1:
            em_lo, em_hi = clustered_bootstrap_ci(
                em_vals, clusters, n_boot=n_boot, alpha=alpha
            )
            hu_lo, hu_hi = clustered_bootstrap_ci(
                hu_vals, clusters, n_boot=n_boot, alpha=alpha
            )
        else:
            em_lo, em_hi = bootstrap_ci(em_vals, n_boot=n_boot, alpha=alpha)
            hu_lo, hu_hi = bootstrap_ci(hu_vals, n_boot=n_boot, alpha=alpha)

        rows.append(
            {
                "model_display": model,
                "exact_match_accuracy": em_vals.mean() * 100,
                "em_ci_low": em_lo * 100,
                "em_ci_high": em_hi * 100,
                "human_accuracy": hu_vals.mean() * 100,
                "hu_ci_low": hu_lo * 100,
                "hu_ci_high": hu_hi * 100,
                "n": len(grp),
                "human_scored_percent": grp["is_human"].mean() * 100,
            }
        )

    summary = pd.DataFrame(rows).sort_values(
        "exact_match_accuracy", ascending=False
    ).reset_index(drop=True)
    return summary


def plot_leaderboard(summary: pd.DataFrame) -> None:
    """Write an exact-match accuracy leaderboard for all evaluated models."""
    apply_style()
    fig, ax = plt.subplots(
        figsize=acl_figure_size(2, max(3.2, 0.34 * len(summary) + 1.25))
    )
    positions = range(len(summary))
    values = summary["exact_match_accuracy"]
    ci_lo = summary["em_ci_low"]
    ci_hi = summary["em_ci_high"]
    errors_lo = values - ci_lo
    errors_hi = ci_hi - values
    ax.barh(
        positions,
        values,
        xerr=[errors_lo, errors_hi],
        color=PALETTE["blue"],
        height=0.64,
        capsize=2,
        error_kw={"linewidth": 0.7, "color": PALETTE["grey"]},
    )
    ax.set_xlim(0, 100)
    for position, value, lo, hi in zip(
        positions, values, ci_lo, ci_hi, strict=True
    ):
        ax.text(
            hi + 1.0,
            position,
            f"{value:.1f}% [{lo:.1f}, {hi:.1f}]",
            va="center",
            fontsize=6,
        )
    ax.set(
        yticks=list(positions),
        yticklabels=summary["model_display"],
        xlabel="Exact-match accuracy (%)",
        title="Exact-match accuracy across human-evaluated models",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.35)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("model_results", "exact_match_accuracy_leaderboard")
    )
    plt.close(fig)
    write_csv(summary, OUTPUT_DIR / "human_eval_exact_match_leaderboard.csv")


def main() -> None:
    """Regenerate the 24-model exact-match leaderboard and table."""
    plot_leaderboard(load_human_eval_leaderboard())


if __name__ == "__main__":
    main()
