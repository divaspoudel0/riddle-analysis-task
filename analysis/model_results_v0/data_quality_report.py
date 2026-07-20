"""Generate a data quality report for a results version.

Reads the tidy parquet produced by load_results.py and writes a markdown
report covering response health per model: parse status, empty responses,
token-limit truncations, and judge verdict distribution.

Rerun on each dataset version (v0, v1, ...) to keep a comparable record of
run quality over time.

Usage:
    python data_quality_report.py [parquet_path] [out_md] [version_label]
    defaults: data/processed/results_tidy.parquet  DATA_QUALITY_v0.md  v0
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

TRUNCATION_TOKENS = 4000  # near the shared 4096 max_output_tokens budget


def build_report(df: pd.DataFrame, version: str) -> str:
    lines = [
        f"# Data quality report: {version} model runs",
        "",
        f"Generated {date.today().isoformat()} by data_quality_report.py. "
        "Do not edit by hand; rerun the script.",
        "",
        f"Rows: {len(df)}, models: {df['model_display'].nunique()}, "
        f"communities: {df['instance_community'].nunique()}, "
        f"conditions: {df['condition_id'].nunique()}",
        "",
        "## Per-model response health",
        "",
        "unparsed = response present but no answer extractable "
        "(mostly reasoning that never reaches the JSON answer). "
        f"truncated = unparsed with >= {TRUNCATION_TOKENS} output tokens, "
        "i.e. the model hit the shared token budget before answering.",
        "",
        "| model | rows | empty | unparsed | truncated | judge correct | judge unknown |",
        "|---|---|---|---|---|---|---|",
    ]

    has_judge = "judge_verdict" in df.columns
    for model, g in df.groupby("model_display"):
        empty = (g.answer_parse_status == "empty").sum()
        unparsed = g.answer_parse_status == "unparsed"
        truncated = (
            unparsed & (g.output_tokens.fillna(0) >= TRUNCATION_TOKENS)
        ).sum()
        correct = (g.judge_verdict == "correct").sum() if has_judge else "-"
        unknown = (g.judge_verdict == "unknown").sum() if has_judge else "-"
        lines.append(
            f"| {model} | {len(g)} | {empty} | {unparsed.sum()} | "
            f"{truncated} | {correct} | {unknown} |"
        )

    lines += [
        "",
        "## Notable findings",
        "",
        "Threshold: models with more than 5% of rows empty or unparsed.",
        "",
    ]
    for model, g in df.groupby("model_display"):
        bad = g.answer_parse_status.isin(["empty", "unparsed"]).mean()
        if bad > 0.05:
            unparsed = g.answer_parse_status == "unparsed"
            truncated = (
                unparsed & (g.output_tokens.fillna(0) >= TRUNCATION_TOKENS)
            ).sum()
            lines.append(
                f"- {model}: {bad:.1%} of rows have no extractable answer "
                f"({truncated} of {unparsed.sum()} unparsed rows hit the "
                "token budget)."
            )

    lines += [
        "",
        "## Version notes (hand-maintained context, append per version)",
        "",
        "- v0: Command A+ July 13 rerun fixed earlier empty responses (404s) "
        "but 1,122 of its 1,136 unparsed rows hit the 4,096 token budget "
        "mid-reasoning; kept as-is for v0, scored as format failures, "
        "flagged to leads 15 Jul 2026.",
        "- v0: Amazon Nova Micro emits pseudo-JSON with single-quoted values; "
        "handled in load_results.extract_answer.",
        "- v0: Qwen-SEA-LION and OLMo-3-32B-Think spill reasoning and "
        "truncate before answering on a subset of rows; treated as genuine "
        "no-answers.",
        "- v0: judge abstention detection (NO_ANSWER_PHRASES_RAW) covers ~6 of "
        "30+ benchmark languages; honest-uncertainty rates are lower bounds. "
        "Raised with Abdellah 19 Jul 2026; rerun scoring once the phrase list "
        "is extended.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parquet = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "data/processed/results_tidy.parquet"
    )
    out_md = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("DATA_QUALITY_v0.md")
    version = sys.argv[3] if len(sys.argv) > 3 else "v0"

    df = pd.read_parquet(parquet)
    out_md.write_text(build_report(df, version), encoding="utf-8")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
