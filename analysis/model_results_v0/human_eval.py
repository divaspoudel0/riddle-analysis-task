"""Human-eval analysis for v0, rerunnable as coverage grows.

Single source of truth for scores: Henry's flat file
(data/human_eval_v0/model_riddle_results_flat.csv). Every non-pending row
already carries a score (human 0/1/2/3, or auto: exact_match=3, empty=0,
placeholder=0, idk=1). Only pending_human_eval rows are blank; those we fill
with the heuristic judge score (Henry's cap policy) for the coverage-filled
views only.

The DEFENSIBLE leaderboard for the paper is computed on COMPLETE communities
only, using Henry's score for every row (no judge-fill, no guessing). It is
provisional until coverage completes; every output is labelled with N/44.

Rerun after each flatfile refresh:  python human_eval.py

Outputs:
  data/processed/human_eval_coverage.csv     per-community completion (chase tracker)
  data/processed/human_leaderboard.csv       defensible leaderboard (complete communities)
  data/processed/human_joined.parquet        full joined frame (feeds figures + the Space)
  HUMAN_EVAL_v0.md                            summary report
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from load_results import EXCLUDED_RIDDLES  # Cuba etc.

FLAT_CSV = Path("data/human_eval_v0/model_riddle_results_flat.csv")
AUTO_PARQUET = Path("data/processed/results_tidy.parquet")
OUT_COVERAGE = Path("data/processed/human_eval_coverage.csv")
OUT_LB = Path("data/processed/human_leaderboard.csv")
OUT_PARQUET = Path("data/processed/human_joined.parquet")
OUT_MD = Path("HUMAN_EVAL_v0.md")

TOTAL_COMMUNITIES = 44          # v0
EXPECTED_MODELS = 24            # human-eval covers the 24 closed-book models
RIDDLES_PER_COMMUNITY = 100
THIN_THRESHOLD = 0.20           # < 20% of human-eligible rows scored
STRICT_SCORE = 3.0             # correct
LENIENT_SCORE = 2.0           # correct or close

# Henry's model_name -> our model_display (verified 24/24).
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


def load_flat() -> pd.DataFrame:
    h = pd.read_csv(FLAT_CSV, low_memory=False)
    h = h[~h["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    h["model_display"] = h["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(h.loc[h["model_display"].isna(), "model_name"].dropna().unique())
    if unmapped:
        raise SystemExit(
            f"Unmapped model_name(s) {unmapped}. Add to MODEL_NAME_MAP before "
            "trusting any number."
        )
    if h["model_display"].nunique() != EXPECTED_MODELS:
        print(f"  NOTE: {h['model_display'].nunique()} models in flatfile "
              f"(expected {EXPECTED_MODELS}).")
    return h


def coverage_report(h: pd.DataFrame) -> pd.DataFrame:
    g = h.assign(
        is_human=h["scoring_method"].eq("human_eval"),
        is_pending=h["scoring_method"].eq("pending_human_eval"),
    ).groupby("community")
    cov = pd.DataFrame({
        "human_done": g["is_human"].sum().astype(int),
        "pending": g["is_pending"].sum().astype(int),
    })
    cov["human_eligible"] = cov["human_done"] + cov["pending"]
    cov["pct_complete"] = (
        cov["human_done"] / cov["human_eligible"].where(cov["human_eligible"] > 0) * 100
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


def build_scored(h: pd.DataFrame, auto: pd.DataFrame) -> pd.DataFrame:
    """Henry's score for every row; fill only pending rows with the judge."""
    judge = auto[["riddle_id", "model_display", "judge_score", "judge_verdict"]]
    m = h.merge(judge, on=["riddle_id", "model_display"], how="left")
    m["is_pending"] = m["scoring_method"].eq("pending_human_eval")
    # final score = Henry's score, or the heuristic judge score where pending.
    m["final_score"] = m["score"].where(~m["is_pending"], m["judge_score"])
    m["is_correct"] = m["final_score"].eq(STRICT_SCORE)
    m["is_correct_lenient"] = m["final_score"].ge(LENIENT_SCORE)
    return m


def leaderboard(m: pd.DataFrame, communities: set[str]) -> pd.DataFrame:
    """Leaderboard over the given communities, using ONLY Henry's scores.

    Pending rows (no Henry score) are dropped, not judge-filled, so every
    number here traces to the flatfile with zero assumptions on our side.
    """
    sub = m[m["community"].isin(communities) & ~m["is_pending"]]
    lb = sub.groupby("model_display").agg(
        strict=("is_correct", "mean"),
        lenient=("is_correct_lenient", "mean"),
        n=("is_correct", "size"),
        human_share=("scoring_method", lambda s: (s == "human_eval").mean()),
    ).sort_values("strict", ascending=False)
    return lb


def main() -> None:
    h = load_flat()
    auto = pd.read_parquet(AUTO_PARQUET)
    m = build_scored(h, auto)

    cov = coverage_report(h)
    complete = set(cov[cov.status == "complete"].index)

    # --- sanity checks: fail loudly rather than ship a wrong number ---
    cm = m[m["community"].isin(complete)]
    per_model = cm.groupby("model_display").size()
    expected = len(complete) * RIDDLES_PER_COMMUNITY
    off = per_model[per_model != expected]
    if len(complete) and not off.empty:
        print(f"  WARN: some models != {expected} rows on complete communities:\n"
              f"{off.to_string()}")
    stray_pending = int(cm["is_pending"].sum())
    if stray_pending:
        print(f"  NOTE: {stray_pending} stray pending rows inside 'complete' "
              "communities (counted via judge fill).")

    OUT_COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    cov.to_csv(OUT_COVERAGE)
    counts = cov.status.value_counts().to_dict()
    print(f"Coverage: complete {counts.get('complete',0)}, partial "
          f"{counts.get('partial',0)}, thin {counts.get('thin',0)}, "
          f"not started {counts.get('not_started',0)} (of {len(cov)}).")

    lb = leaderboard(m, complete)
    lb.to_csv(OUT_LB)
    m.to_parquet(OUT_PARQUET, index=False)

    print(f"\nDEFENSIBLE human leaderboard  (complete communities only, "
          f"N={len(complete)}/{TOTAL_COMMUNITIES}, provisional):")
    print((lb.head(8)[["strict", "lenient"]] * 100).round(1).to_string())

    write_report(cov, lb, complete)
    print(f"\n  wrote {OUT_LB}, {OUT_COVERAGE}, {OUT_PARQUET}, {OUT_MD}")


def write_report(cov: pd.DataFrame, lb: pd.DataFrame, complete: set[str]) -> None:
    counts = cov.status.value_counts().to_dict()
    lines = [
        "# Human evaluation report: v0",
        "",
        f"Generated {date.today().isoformat()} by human_eval.py from "
        "`model_riddle_results_flat.csv`. Rerun as coverage grows; do not edit "
        "by hand. Every score traces to Henry's flatfile.",
        "",
        f"**Provisional: {len(complete)}/{TOTAL_COMMUNITIES} communities have "
        "complete human evaluation.** The leaderboard below is computed on those "
        "communities only, using the human score for every row (auto-resolved "
        "rows keep their auto score; no judge-fill). Strict = top score (3); "
        "lenient = score >= 2. Rankings can still change as coverage completes.",
        "",
        "## Coverage",
        "",
        f"complete: {counts.get('complete',0)}, partial: {counts.get('partial',0)}, "
        f"thin: {counts.get('thin',0)}, not started: {counts.get('not_started',0)}. "
        "Per-community table in `data/processed/human_eval_coverage.csv`.",
        "",
        "Not started (chase): "
        + (", ".join(cov[cov.status == "not_started"].index) or "none") + ".",
        "Thin: " + (", ".join(cov[cov.status == "thin"].index) or "none") + ".",
        "",
        f"## Human leaderboard (complete communities, N={len(complete)}/"
        f"{TOTAL_COMMUNITIES})",
        "",
        "| model | strict (%) | lenient (%) |",
        "|---|---|---|",
    ]
    for model, r in lb.iterrows():
        lines.append(f"| {model} | {r.strict*100:.1f} | {r.lenient*100:.1f} |")
    lines += ["", "> Provisional until coverage completes. Rerun to refresh.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
