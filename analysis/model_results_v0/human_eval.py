"""Human-eval analysis for v0, rerunnable as coverage grows.

Reads Henry's flat human-eval file (data/human_eval_v0/model_riddle_results_flat.csv)
and joins it to the automatic tidy frame. Rerun whenever Henry refreshes the
CSV; everything below updates.

Henry's schema (one row per riddle x model):
  score            0/1/2/3 or empty (0 wrong, 3 correct, 2 partial, 1 rare)
  scoring_method   human_eval | pending_human_eval | auto_exact_match |
                   auto_idk | auto_placeholder | auto_empty
  error_type       code (e.g. 0.3 hallucinated); error_type_label is the text
  annotator_name   one annotator per riddle (so no inter-annotator agreement)

Cap handling (Henry's call): fill rows without a human score with the
heuristic judge score, so tiny models are not flattered by reporting over a
thin human-eligible set.

Outputs:
  data/processed/human_eval_coverage.csv   per-community completion (Discord tracker)
  data/processed/human_joined.parquet      joined frame (feeds the leaderboard + dashboard)
  HUMAN_EVAL_v0.md                          summary report
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from load_results import EXCLUDED_RIDDLES  # same exclusions (Cuba)

FLAT_CSV = Path("data/human_eval_v0/model_riddle_results_flat.csv")
AUTO_PARQUET = Path("data/processed/results_tidy.parquet")
OUT_COVERAGE = Path("data/processed/human_eval_coverage.csv")
OUT_PARQUET = Path("data/processed/human_joined.parquet")
OUT_MD = Path("HUMAN_EVAL_v0.md")

# Henry's model_name -> our model_display (24 human-eval models; no search run).
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

# A riddle counts as correct (strict) when the human gave the top score.
HUMAN_CORRECT_SCORE = 3.0
# Communities considered too thin for agreement stats (still shown in coverage).
THIN_THRESHOLD = 0.20  # < 20% of human-eligible rows scored


def load_flat() -> pd.DataFrame:
    h = pd.read_csv(FLAT_CSV, low_memory=False)
    h = h[~h["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    h["model_display"] = h["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(h.loc[h["model_display"].isna(), "model_name"].dropna().unique())
    if unmapped:
        print(f"  WARNING unmapped model_name(s): {unmapped}")
    return h


def coverage_report(h: pd.DataFrame) -> pd.DataFrame:
    """Per-community completion = human / (human + pending). Auto-resolved
    rows don't need human eval, so they are not in the denominator."""
    h = h.assign(
        is_human=h["scoring_method"].eq("human_eval"),
        is_pending=h["scoring_method"].eq("pending_human_eval"),
    )
    g = h.groupby("community")
    cov = pd.DataFrame({
        "human_done": g["is_human"].sum().astype(int),
        "pending": g["is_pending"].sum().astype(int),
    })
    cov["human_eligible"] = cov["human_done"] + cov["pending"]
    cov["pct_complete"] = (
        cov["human_done"] / cov["human_eligible"].where(cov["human_eligible"] > 0)
        * 100
    ).round(1)
    def status(r):
        if r["human_done"] == 0:
            return "not_started"
        if r["human_eligible"] == 0 or r["pct_complete"] >= 99:
            return "complete"
        if r["pct_complete"] < THIN_THRESHOLD * 100:
            return "thin"
        return "partial"
    cov["status"] = cov.apply(status, axis=1)
    return cov.sort_values(["status", "pct_complete"])


def join_and_fill(h: pd.DataFrame, auto: pd.DataFrame) -> pd.DataFrame:
    """Attach the heuristic judge score; fill non-human rows with it."""
    auto_side = auto[["riddle_id", "model_display", "judge_score",
                      "judge_verdict"]].copy()
    m = h.merge(auto_side, on=["riddle_id", "model_display"], how="left")

    m["is_human"] = m["scoring_method"].eq("human_eval") & m["score"].notna()
    m["score_source"] = m["scoring_method"]
    # final_score: human score where present, else the heuristic judge score.
    m["final_score"] = m["score"].where(m["is_human"], m["judge_score"])
    # correctness on a common binary: top human score, or judge 'correct'.
    m["is_correct"] = (
        (m["is_human"] & (m["score"] == HUMAN_CORRECT_SCORE))
        | (~m["is_human"] & m["judge_verdict"].eq("correct"))
    )
    return m


def human_leaderboard(m: pd.DataFrame) -> pd.DataFrame:
    """Per-model hybrid accuracy (human where scored, judge-filled elsewhere)."""
    def agg(g: pd.DataFrame) -> pd.Series:
        human = g[g.is_human]
        return pd.Series({
            "accuracy": g.is_correct.mean(),                    # strict, top score
            "human_graded": human["score"].mean() / 3 if len(human) else float("nan"),
            "human_share": g.is_human.mean(),                   # how much is real human
            "n": len(g),
        })
    return (
        m.groupby("model_display").apply(agg, include_groups=False)
        .sort_values("accuracy", ascending=False)
    )


def main() -> None:
    h = load_flat()
    auto = pd.read_parquet(AUTO_PARQUET)

    cov = coverage_report(h)
    OUT_COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    cov.to_csv(OUT_COVERAGE)
    n_done = (cov.status == "complete").sum()
    print(f"Coverage: {n_done}/{len(cov)} communities complete, "
          f"{(cov.status=='partial').sum()} partial, "
          f"{(cov.status=='thin').sum()} thin, "
          f"{(cov.status=='not_started').sum()} not started")
    print(f"  wrote {OUT_COVERAGE}")

    m = join_and_fill(h, auto)
    m.to_parquet(OUT_PARQUET, index=False)
    lb = human_leaderboard(m)
    print(f"\n  wrote {OUT_PARQUET}")
    print("\nHybrid human leaderboard (top 6, human-where-scored + judge-filled):")
    print((lb.head(6)[["accuracy", "human_graded", "human_share"]] *
           [100, 100, 100]).round(1).to_string())

    write_report(cov, lb, m)
    print(f"\n  wrote {OUT_MD}")


def write_report(cov: pd.DataFrame, lb: pd.DataFrame, m: pd.DataFrame) -> None:
    from datetime import date
    counts = cov.status.value_counts().to_dict()
    lines = [
        "# Human evaluation report: v0",
        "",
        f"Generated {date.today().isoformat()} by human_eval.py from "
        "`model_riddle_results_flat.csv`. Rerun as coverage grows; do not "
        "edit by hand.",
        "",
        "Scores are hybrid: human where a human scored the answer, filled with "
        "the heuristic judge score elsewhere (Henry's cap policy). Accuracy is "
        "the strict top-score rate; human_graded is the mean human score / 3.",
        "",
        "## Coverage",
        "",
        f"complete: {counts.get('complete',0)}, partial: {counts.get('partial',0)}, "
        f"thin: {counts.get('thin',0)}, not started: {counts.get('not_started',0)} "
        f"(of {len(cov)} communities). Full per-community table in "
        "`data/processed/human_eval_coverage.csv`.",
        "",
        "Not started (chase these): "
        + ", ".join(cov[cov.status == "not_started"].index) + ".",
        "",
        "## Hybrid leaderboard",
        "",
        "| model | accuracy (%) | human graded (%) | human share (%) |",
        "|---|---|---|---|",
    ]
    for model, r in lb.iterrows():
        lines.append(
            f"| {model} | {r.accuracy*100:.1f} | {r.human_graded*100:.1f} | "
            f"{r.human_share*100:.1f} |"
        )
    lines += [
        "",
        "> human share = fraction of a model's rows that carry a real human "
        "score; the rest are judge-filled. These numbers move as coverage "
        "grows, so rerun after each refresh.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
