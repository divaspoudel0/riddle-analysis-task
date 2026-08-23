"""Shared paths, labels, and joins for evaluation analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis.constants import ANALYSIS_ROOT

FLAT_CSV = ANALYSIS_ROOT / "eval_analysis" / "data" / "model_riddle_results_flat.csv"
MODEL_RESULTS_TIDY_CSV = (
    ANALYSIS_ROOT
    / "model_results"
    / "data"
    / "combined"
    / "processed"
    / "results_tidy.csv"
)
TOTAL_COMMUNITIES = 44
EXPECTED_MODELS = 24
STRICT_SCORE = 3.0
LENIENT_SCORE = 2.0
THIN_THRESHOLD = 0.20

EXCLUDED_RIDDLES = frozenset({"spanish_cuba_history_016"})

MODEL_NAME_MAP = {
    "Amazon-Nova-Lite": "Amazon Nova Lite v1",
    "Amazon-Nova-Micro": "Amazon Nova Micro v1",
    "Deepseek-v4-flash": "DeepSeek V4 Flash",
    "EuroLLM-Instruct": "EuroLLM-22B-Instruct-2512",
    "GPT5.5-high": "GPT5.5 [high]",
    "GPT5.5-none": "GPT5.5 [none]",
    "Gemini-2.5-Flash": "Gemini 2.5 Flash",
    "Gemini-2.5-Flash-Lite": "Gemini 2.5 Flash Lite",
    "Mistral-Large-3": "Mistral Large 3",
    "Olmo-3-32B-Think": "OLMo-3-32B-Think",
    "Qwen-3.5-0.8B": "Qwen/Qwen3.5-0.8B",
    "Qwen-SEA-LION-v4.5-27B-IT": "Qwen-SEA-LION-v4.5-27B-IT",
    "Qwen3.5-27B": "Qwen3.5 27B",
    "claude-opus-4-7": "claude-opus-4-7 [none]",
    "claude-opus-4-7-thinking": "claude-opus-4-7 [thinking]",
    "command-a-plus-05-2026": "Cohere Command A Plus",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek-v4-pro-thinking": "deepseek-v4-pro-thinking",
    "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
    "gemma-4-31b": "Gemma 4 31B IT",
    "tiny-aya-earth": "Tiny-Aya earth",
    "tiny-aya-fire": "Tiny-Aya fire",
    "tiny-aya-global": "Tiny-Aya global",
    "tiny-aya-water": "Tiny-Aya water",
}


def load_flat_frame(path: Path = FLAT_CSV) -> pd.DataFrame:
    """Load and validate the canonical human-evaluation export.

    Args:
        path: CSV export containing one row per model, community, and riddle.

    Returns:
        The export with the canonical ``model_display`` and score flags.

    Raises:
        ValueError: If the export contains an unmapped model name.
    """
    frame = pd.read_csv(path, low_memory=False)
    frame = frame[~frame["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    frame["model_display"] = frame["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(
        frame.loc[frame["model_display"].isna(), "model_name"].dropna().unique()
    )
    if unmapped:
        raise ValueError(f"Unmapped human-evaluation models: {unmapped}")
    frame["is_human"] = frame["scoring_method"].eq("human_eval")
    frame["is_pending"] = frame["scoring_method"].eq("pending_human_eval")
    frame["is_correct"] = frame["score"].eq(STRICT_SCORE)
    frame["is_correct_lenient"] = frame["score"].ge(LENIENT_SCORE)
    return frame


def coverage_report(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize human-evaluation completion by community.

    Args:
        frame: Output from :func:`load_flat_frame`.

    Returns:
        One row per community with completion counts and a status label.
    """
    unique_rows = frame.drop_duplicates(["community", "riddle_id", "model_display"])
    grouped = unique_rows.groupby("community")
    coverage = pd.DataFrame(
        {
            "human_done": grouped["is_human"].sum().astype(int),
            "pending": grouped["is_pending"].sum().astype(int),
        }
    )
    coverage["human_eligible"] = coverage["human_done"] + coverage["pending"]
    coverage["pct_complete"] = (
        coverage["human_done"]
        / coverage["human_eligible"].where(coverage["human_eligible"] > 0)
        * 100
    ).round(1)

    def status(row: pd.Series) -> str:
        if row["human_done"] == 0:
            return "not_started"
        if row["human_eligible"] == 0 or row["pct_complete"] >= 99:
            return "complete"
        if row["pct_complete"] < THIN_THRESHOLD * 100:
            return "thin"
        return "partial"

    coverage["status"] = coverage.apply(status, axis=1)
    return coverage.sort_values(["status", "pct_complete"])


def load_human_evaluation(
    path: Path = FLAT_CSV,
    tidy_path: Path = MODEL_RESULTS_TIDY_CSV,
) -> pd.DataFrame:
    """Load human scores and attach recorded exact-match judge results.

    The flat export contains the canonical human scores. Exact-match rows are
    already marked by ``scoring_method``. Where the processed model-results
    export contains a recorded judge result for the same riddle and model, it
    is attached to support human-versus-automatic comparisons. Missing judge
    results remain missing; this function never recreates a judge in Python.

    Args:
        path: Canonical human-evaluation export.
        tidy_path: Processed model-results export with recorded judge results.

    Returns:
        The joined evaluation frame with ``is_exact_match``.
    """
    frame = load_flat_frame(path)
    frame.attrs["source_mtime"] = path.stat().st_mtime
    frame["is_exact_match"] = frame["scoring_method"].eq("auto_exact_match")

    if not tidy_path.exists():
        return frame

    tidy = pd.read_csv(tidy_path, low_memory=False)
    required = {"riddle_id", "model_display", "judge_verdict"}
    missing = required.difference(tidy.columns)
    if missing:
        raise ValueError(f"Missing judge columns in {tidy_path}: {sorted(missing)}")
    judge = tidy[["riddle_id", "model_display", "judge_verdict"]].copy()
    if judge.duplicated(["riddle_id", "model_display"]).any():
        raise ValueError(f"Duplicate riddle/model judge rows in {tidy_path}")
    judge["recorded_exact_match"] = judge["judge_verdict"].eq("correct")
    source_mtime = frame.attrs["source_mtime"]
    frame = frame.merge(
        judge[["riddle_id", "model_display", "recorded_exact_match"]],
        on=["riddle_id", "model_display"],
        how="left",
    )
    frame["is_exact_match"] = frame["recorded_exact_match"].combine_first(
        frame["is_exact_match"]
    )
    frame.attrs["source_mtime"] = source_mtime
    return frame.drop(columns="recorded_exact_match")
