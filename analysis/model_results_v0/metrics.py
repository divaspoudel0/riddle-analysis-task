"""Scoring and aggregation helpers for v0 results analysis.

Central place for metric definitions so the notebook, figure scripts, and
paper all report the same numbers.

Denominator policy
------------------
Accuracy is reported over COMPLETED responses: rows where the model
returned something (generation succeeded and the response is non-empty).
Generation errors and empty responses are excluded from the accuracy
denominator and reported separately as coverage. Rationale: including
API failures would rank provider reliability, not model capability.

Unparsed responses (model produced text but no extractable answer, e.g.
reasoning truncated at the token budget) COUNT as attempts and score as
incorrect: the model consumed its budget and failed to answer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG_SEED = 7


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add is_completed / is_correct / is_abstention columns."""
    df = df.copy()
    df["is_completed"] = (df["generation_status"] == "success") & (
        df["answer_parse_status"] != "empty"
    )
    df["is_correct"] = df["judge_verdict"].eq("correct")
    # judge 'unknown' = explicit "I don't know" style responses
    df["is_abstention"] = df["judge_verdict"].eq("unknown")
    df["is_format_failure"] = df["is_completed"] & df["answer_parse_status"].eq(
        "unparsed"
    )
    return df


def model_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-model accuracy over completed responses, plus coverage."""
    def agg(g: pd.DataFrame) -> pd.Series:
        completed = g[g.is_completed]
        return pd.Series(
            {
                "accuracy": completed.is_correct.mean(),
                "abstention_rate": completed.is_abstention.mean(),
                "format_failure_rate": completed.is_format_failure.mean(),
                "coverage": g.is_completed.mean(),
                "n_completed": len(completed),
                "n_total": len(g),
            }
        )

    out = (
        df.groupby("model_display").apply(agg, include_groups=False)
        .sort_values("accuracy", ascending=False)
    )
    return out


def bootstrap_ci(
    values: np.ndarray, n_boot: int = 2000, alpha: float = 0.05
) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean of a 0/1 array."""
    rng = np.random.default_rng(RNG_SEED)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[idx].mean(axis=1)
    return (
        float(np.quantile(means, alpha / 2)),
        float(np.quantile(means, 1 - alpha / 2)),
    )


def model_summary_with_ci(df: pd.DataFrame, n_boot: int = 2000) -> pd.DataFrame:
    """model_summary plus bootstrap CIs over completed responses."""
    out = model_summary(df)
    lo, hi = [], []
    for model in out.index:
        vals = df[(df.model_display == model) & df.is_completed][
            "is_correct"
        ].to_numpy(dtype=float)
        l, h = bootstrap_ci(vals, n_boot=n_boot)
        lo.append(l)
        hi.append(h)
    out["ci_low"] = lo
    out["ci_high"] = hi
    return out
