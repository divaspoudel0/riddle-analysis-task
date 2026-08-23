"""Prepare the human-eval frame for the tier-3 leaderboard and Figure 5.

Grounded in the real schema of data/human_eval_v0/analysis_model_level.csv
(Henry's model-level file). The 14 Jul copy has auto scores filled and human
scores mostly blank; Henry's 31 Jul refresh fills the human_eval scores.
Rerun this after that refresh.

The model-level file already combines human and automatic scoring, one row
per (riddle_id, model), with:
  - score           numeric score (human or auto, depending on method)
  - scoring_method  human_eval | auto_exact_match | auto_idk | auto_empty
  - is_extras       True if this answer is beyond the human-eval cap
                    (identical answers are clustered; only the cap is scored)
  - answer_cluster_size, error_type (hallucination code), validator_note...

So `scoring_method` IS the score_source, and `is_extras` IS the cap flag.

Two things this script does:
  1. Normalise scoring_method into a tidy `score_source` and apply the cap
     policy (Henry's open question) via `is_extras`.
  2. Join the human-scored rows to the automatic judge score (from the tidy
     frame) so Figure 5 can measure judge-vs-human agreement per community.

Open items to confirm before final numbers:
  - CAP_POLICY: "fill_auto" keeps is_extras rows (auto score stands in) vs
    "eligible_only" drops them. Henry owes the call.
  - MODEL_NAME reconciliation: the human file's model_name (e.g.
    "Amazon-Nova-Lite") may not match the tidy frame's model_name /
    model_display verbatim. build_model_map() reports the overlap so we can
    add a lookup if they differ.

Usage:
    python join_human_eval.py
"""

from __future__ import annotations

import pandas as pd

from analysis.constants import ANALYSIS_ROOT
from analysis.model_results.load_results import EXCLUDED_RIDDLES

DATA_DIR = ANALYSIS_ROOT / "model_results" / "data"
AUTO_PARQUET = DATA_DIR / "processed" / "results_tidy.parquet"
HUMAN_CSV = DATA_DIR / "human_eval_v0" / "analysis_model_level.csv"
OUT_PARQUET = DATA_DIR / "processed" / "human_joined.parquet"

# is_extras handling — Henry's open question:
#   "fill_auto"     capped-out (is_extras) answers keep their auto score
#   "eligible_only" drop is_extras rows; report over human-eligible answers
CAP_POLICY = "fill_auto"  # TODO: set once Henry confirms

# scoring_method -> friendly score_source label
SCORE_SOURCE = {
    "human_eval": "human",
    "auto_exact_match": "auto-3",  # exact match, full credit
    "auto_idk": "auto-1",  # abstention / "I don't know"
    "auto_empty": "auto-0",  # no answer
}

# Human file model_name -> auto frame model_display. Built by matching the
# two model lists; verified 24/24 map to a distinct auto model. (The auto
# frame's GPT5.5-search has no human-eval counterpart, as expected.)
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


def load_human() -> pd.DataFrame:
    if not HUMAN_CSV.exists():
        raise SystemExit(f"Human-eval file not found: {HUMAN_CSV}")
    h = pd.read_csv(HUMAN_CSV, low_memory=False)
    h = h[~h["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    h["score_source"] = h["scoring_method"].map(SCORE_SOURCE).fillna("other")
    # Normalise to the auto frame's model_display so joins line up.
    h["model_display"] = h["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(h.loc[h["model_display"].isna(), "model_name"].dropna().unique())
    if unmapped:
        print(
            f"  WARNING: {len(unmapped)} model_name(s) not in MODEL_NAME_MAP:", unmapped
        )
    if CAP_POLICY == "eligible_only":
        h = h[~h["is_extras"].fillna(False)].copy()
    elif CAP_POLICY != "fill_auto":
        raise ValueError(f"Unknown CAP_POLICY {CAP_POLICY!r}")
    return h


def join_for_agreement(human: pd.DataFrame, auto: pd.DataFrame) -> pd.DataFrame:
    """Human-scored rows joined to the automatic judge score, for Figure 5.

    Keyed on (riddle_id, model_display) after name normalisation.
    """
    human_only = human[human["score_source"] == "human"]
    auto_side = auto[
        [
            "riddle_id",
            "model_display",
            "judge_score",
            "judge_verdict",
            "instance_community",
        ]
    ].rename(columns={"instance_community": "community"})
    agreement = human_only.merge(
        auto_side,
        on=["riddle_id", "model_display"],
        how="left",
        suffixes=("_human", "_auto"),
    )
    return agreement


def main() -> None:
    auto = pd.read_parquet(AUTO_PARQUET)
    auto = auto[~auto["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    human = load_human()

    print(f"human rows (cap_policy={CAP_POLICY}): {len(human):,}")
    print("score_source:", human["score_source"].value_counts().to_dict())

    agreement = join_for_agreement(human, auto)
    matched = agreement["judge_score"].notna().sum()
    print(
        f"human-scored rows joined to an auto judge score: {matched:,} / "
        f"{len(agreement):,}"
    )

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    human.to_parquet(OUT_PARQUET, index=False)
    print(f"Wrote {OUT_PARQUET}")


if __name__ == "__main__":
    main()
