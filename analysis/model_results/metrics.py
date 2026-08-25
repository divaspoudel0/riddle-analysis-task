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

# --- search-enabled runs: labelled, not separated ------------------------ #
# Runs with web search enabled (run_config.json: search_enabled) are ranked
# alongside the others and simply labelled, since the benchmark does not
# define an open- vs closed-book split. Web search gives a retrieval
# advantage worth noting, so we flag it in the label and a footnote. The
# eval_category column stays for anyone who wants to filter.
SEARCH_SUFFIX = " (search)"
SEARCH_NOTE = "(search) = web search enabled for this run."


def search_model_set(df: pd.DataFrame) -> set[str]:
    """Model display names whose run is search-enabled."""
    if "eval_category" not in df.columns:
        return set()
    return set(df.loc[df.eval_category == "search_enabled", "model_display"].unique())


def label_with_search(model: str, search_models: set[str]) -> str:
    """Append the search suffix to a model label when applicable."""
    return model + SEARCH_SUFFIX if model in search_models else model


# Literal prompt-template placeholders some models echo back verbatim as the
# answer (they parse as valid JSON, so the extractor accepts them, but they
# carry no answer). These are format failures, not knowledge failures: the
# model never attempted the riddle. Handled here on the analysis side until
# the judge itself rejects placeholder strings. See DATA_QUALITY_v0.md.
TEMPLATE_ECHO_ANSWERS = frozenset(
    {
        "<your_riddle_answer>",
        "<answer>",
        "...",
    }
)


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add completion, scoring, correctness, and format-status columns.

    ``judge_verdict`` is optional at load time. When no recorded scorer output
    is present, ``is_scored`` is false and accuracy remains missing rather than
    being reported as zero.
    """
    df = df.copy()
    if "judge_verdict" not in df:
        df["judge_verdict"] = pd.Series(pd.NA, index=df.index, dtype="string")
    else:
        df["judge_verdict"] = df["judge_verdict"].astype("string")
    df["is_scored"] = df["judge_verdict"].notna()
    df["is_completed"] = (df["generation_status"] == "success") & (
        df["answer_parse_status"] != "empty"
    )
    # Prompt-template echoes: an extractable but empty answer. Treat as a
    # format failure, never correct, even if one coincidentally matched a
    # reference.
    df["is_template_echo"] = (
        df["answer_text"].fillna("").str.strip().isin(TEMPLATE_ECHO_ANSWERS)
    )
    df["is_correct"] = (
        df["is_scored"] & df["judge_verdict"].eq("correct") & ~df["is_template_echo"]
    )
    # judge 'unknown' = explicit "I don't know" style responses
    df["is_abstention"] = df["is_scored"] & df["judge_verdict"].eq("unknown")
    df["is_format_failure"] = df["is_completed"] & (
        df["answer_parse_status"].eq("unparsed") | df["is_template_echo"]
    )
    return df


def model_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-model accuracy over completed responses, plus coverage."""

    def agg(g: pd.DataFrame) -> pd.Series:
        completed = g[g.is_completed]
        scored = completed[completed.is_scored]
        return pd.Series(
            {
                "accuracy": scored.is_correct.mean(),
                "abstention_rate": scored.is_abstention.mean(),
                "format_failure_rate": completed.is_format_failure.mean(),
                "coverage": g.is_completed.mean(),
                "n_completed": len(completed),
                "n_scored": len(scored),
                "n_total": len(g),
                # search-enabled runs are a separate evaluation category,
                # not comparable to closed-book recall (see load_results.py)
                "eval_category": (
                    g["eval_category"].iloc[0]
                    if "eval_category" in g.columns
                    else "closed_book"
                ),
            }
        )

    out = (
        df.groupby("model_display")
        .apply(agg, include_groups=False)
        .sort_values("accuracy", ascending=False)
    )
    return out


def bootstrap_ci(
    values: np.ndarray, n_boot: int = 2000, alpha: float = 0.05
) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean of a 0/1 array."""
    if len(values) == 0:
        return (float("nan"), float("nan"))
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
        vals = df[(df.model_display == model) & df.is_completed]["is_correct"].to_numpy(
            dtype=float
        )
        lower, upper = bootstrap_ci(vals, n_boot=n_boot)
        lo.append(lower)
        hi.append(upper)
    out["ci_low"] = lo
    out["ci_high"] = hi
    return out


def clustered_bootstrap_ci(
    values: np.ndarray,
    clusters: np.ndarray,
    n_boot: int = 2000,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile bootstrap CI that resamples clusters (e.g. communities).

    When rows from the same community are not independent, resampling
    individual observations understates variance.  This function resamples
    *communities* (clusters) with replacement and computes the statistic on
    the pooled observations within each bootstrap replicate.

    Args:
        values: Binary 0/1 correctness array.
        clusters: Cluster labels (e.g. community IDs) aligned with *values*.
        n_boot: Number of bootstrap replicates.
        alpha: Significance level for the two-sided interval.

    Returns:
        ``(ci_low, ci_high)`` bounds on the mean.
    """
    if len(values) == 0:
        return (float("nan"), float("nan"))
    unique_clusters = np.unique(clusters)
    rng = np.random.default_rng(RNG_SEED)
    cluster_idx = {
        label: np.where(clusters == label)[0] for label in unique_clusters
    }
    means = np.empty(n_boot)
    for i in range(n_boot):
        sampled = rng.choice(unique_clusters, size=len(unique_clusters), replace=True)
        idx = np.concatenate([cluster_idx[c] for c in sampled])
        means[i] = values[idx].mean()
    return (
        float(np.quantile(means, alpha / 2)),
        float(np.quantile(means, 1 - alpha / 2)),
    )


def group_accuracy_ci(
    df: pd.DataFrame,
    group_col: str,
    *,
    n_boot: int = 2000,
    alpha: float = 0.05,
    use_clustered: bool = True,
) -> pd.DataFrame:
    """Bootstrap accuracy CIs for every (model_display, group) pair.

    Args:
        df: Scored results frame with ``model_display``, ``is_completed``,
            ``is_correct``, and *group_col*.
        group_col: Column name to group by (e.g. ``"topic"``, ``"region"``).
        n_boot: Number of bootstrap replicates.
        alpha: Significance level.
        use_clustered: If True, resample by community within each
            (model, group) cell for variance-aware intervals.

    Returns:
        DataFrame with columns ``model_display``, *group_col*, ``accuracy``,
        ``ci_low``, ``ci_high``, ``n``.
    """
    records: list[dict[str, object]] = []
    scored = df[df.is_completed].copy()
    for (model, group), cell in scored.groupby(["model_display", group_col]):
        vals = cell["is_correct"].to_numpy(dtype=float)
        if use_clustered and "instance_community" in cell.columns:
            clusters = cell["instance_community"].to_numpy()
            lo, hi = clustered_bootstrap_ci(vals, clusters, n_boot=n_boot, alpha=alpha)
        else:
            lo, hi = bootstrap_ci(vals, n_boot=n_boot, alpha=alpha)
        records.append(
            {
                "model_display": model,
                group_col: group,
                "accuracy": float(vals.mean()),
                "ci_low": lo,
                "ci_high": hi,
                "n": len(vals),
            }
        )
    return pd.DataFrame(records)


def topic_ci_rates(
    results: pd.DataFrame,
    *,
    n_boot: int = 2000,
    alpha: float = 0.05,
    use_clustered: bool = True,
) -> pd.DataFrame:
    """Bootstrap CI rates by model and topic, matching ``topic_rates`` layout.

    Returns:
        Long-format DataFrame with model, topic, accuracy, ci_low, ci_high, n.
    """
    from analysis.model_results.model_data import canonical_topic, performance_order

    frame = results.assign(topic=results["riddle_id"].map(canonical_topic))
    ci_df = group_accuracy_ci(
        frame, "topic", n_boot=n_boot, alpha=alpha, use_clustered=use_clustered
    )
    topic_order = list(
        performance_order(results)
    )  # reuse model ordering
    ci_df["model_display"] = pd.Categorical(
        ci_df["model_display"], categories=topic_order, ordered=True
    )
    return ci_df.sort_values(["topic", "model_display"]).reset_index(drop=True)


def group_ci_rates(
    results: pd.DataFrame,
    group_col: str,
    *,
    n_boot: int = 2000,
    alpha: float = 0.05,
    use_clustered: bool = True,
) -> pd.DataFrame:
    """Bootstrap CI rates by model and corpus group, matching ``match_rates`` layout.

    Returns:
        Long-format DataFrame with model, group_col, accuracy, ci_low, ci_high, n.
    """
    return group_accuracy_ci(
        results, group_col, n_boot=n_boot, alpha=alpha, use_clustered=use_clustered
    )
