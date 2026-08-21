"""Validate a single riddle submission and surface it for human review.

Phase 1 of the self-serve submission pipeline. Deterministic only: no LLM,
no API, no keys. It takes an uploaded submission (an .xlsx workbook with a
"Riddles" sheet, or a .csv), runs the project's existing validators, prints a
PASS/FAIL report with the exact issues, and surfaces the English translations
so a human moderator can quickly eyeball the riddle types before anything is
accepted (per the leads: format checks are automatic, quality stays human).

Usage:
    python check_submission.py path/to/submission.xlsx
    python check_submission.py path/to/submission.xlsx --json report.json
    python check_submission.py sub.xlsx --reference path/to/updated_template.xlsx

The reference/template is a swappable input: point --reference at Julia's
updated template (or drop it at the default path) and the contract updates with
no code change.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "src"))
from riddles_data_loading.config import ValidationConfig, DEFAULT_SHEET_NAME  # noqa: E402
from riddles_data_loading.validation import (  # noqa: E402
    validate_query_sheet_against_reference,
)

DEFAULT_REFERENCE = _HERE / "data" / "submitted_riddles" / "reference_sheet.xlsx"
ENG_RIDDLE = "Riddle (English Translation)"
ENG_ANSWER = "Reference Answer (English)"


def _read_sheet(path: Path) -> pd.DataFrame:
    """Load the Riddles sheet from an .xlsx, or the whole .csv."""
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        xl = pd.ExcelFile(path)
        sheet = DEFAULT_SHEET_NAME if DEFAULT_SHEET_NAME in xl.sheet_names else xl.sheet_names[0]
        return xl.parse(sheet)
    return pd.read_csv(path)


def _load_reference(reference: Path | None, submission: pd.DataFrame) -> pd.DataFrame:
    """Use the given/default reference sheet; fall back to an empty frame.

    The blocking checks (required columns, answers, Number column, topics) do
    not depend on a real reference, so an empty frame still gives a correct
    pass/fail; the reference only enriches the non-blocking comparison.
    """
    if reference and reference.exists():
        return _read_sheet(reference)
    return submission.iloc[0:0].copy()


def check(submission_path: Path, reference_path: Path | None, samples: int) -> dict:
    submission = _read_sheet(submission_path)
    reference = _load_reference(reference_path, submission)
    result = validate_query_sheet_against_reference(
        reference, submission, config=ValidationConfig()
    )
    result["_submission_rows"] = int(len(submission))
    result["_columns"] = list(submission.columns)
    # collect a review sample of English translations, spread across topics
    review = []
    if ENG_RIDDLE in submission.columns:
        have = submission.dropna(subset=[ENG_RIDDLE])
        picked = (have.groupby("Topic", group_keys=False).head(1)
                  if "Topic" in have.columns else have).head(samples)
        for _, r in picked.iterrows():
            review.append({
                "topic": str(r.get("Topic", "")),
                "riddle_en": str(r.get(ENG_RIDDLE, "")).strip(),
                "answer_en": str(r.get(ENG_ANSWER, "")).strip(),
            })
    result["_review_sample"] = review
    return result


def print_report(name: str, result: dict) -> None:
    ok = result["passed"]
    print(f"{'PASS' if ok else 'FAIL'}  ({name})")
    print(f"  rows: {result['_submission_rows']}")
    if result["blocking_issues"]:
        print("\n  BLOCKING — must be fixed before this can be accepted:")
        for i in result["blocking_issues"]:
            print(f"   - {i}")
    if result["tolerated_issues"]:
        print("\n  Warnings (non-blocking, for awareness):")
        for i in result["tolerated_issues"]:
            print(f"   - {i}")
    if result["_review_sample"]:
        print("\n  English translations for human review (one per topic):")
        for r in result["_review_sample"]:
            print(f"   • [{r['topic']}] {r['riddle_en'][:110]}  ->  {r['answer_en'][:60]}")
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a riddle submission file.")
    ap.add_argument("submission", help="Path to the submission (.xlsx or .csv).")
    ap.add_argument("--reference", default=str(DEFAULT_REFERENCE),
                    help="Reference/template sheet to validate against (swappable).")
    ap.add_argument("--json", help="Write the full result as JSON to this path.")
    ap.add_argument("--samples", type=int, default=10,
                    help="How many English translations to surface for review.")
    args = ap.parse_args(argv)

    sub_path = Path(args.submission)
    if not sub_path.exists():
        ap.error(f"submission not found: {sub_path}")
    ref_path = Path(args.reference) if args.reference else None

    result = check(sub_path, ref_path, args.samples)
    print_report(sub_path.name, result)

    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"  wrote {args.json}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
