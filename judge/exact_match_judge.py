"""Deterministic exact-match judge for riddle answers.

A non-LLM judge: it normalizes the candidate answer and the reference
answer(s) and checks for an exact (normalized) match. It emits the same
verdict shape as the LLM judge (``verdict`` / ``score`` /
``matched_reference`` / ``reason``) so the two are drop-in interchangeable.

Normalization is intentionally script-agnostic:
  * Unicode NFKC + casefold
  * strip combining marks (Latin accents, Arabic tashkeel, ...)
  * drop punctuation/symbols
  * collapse whitespace
  * optionally strip a small set of leading articles (English)

A reference field may list several acceptable answers separated by
``/ ; | ،`` (incl. the Arabic comma); the candidate matches if it equals
any one of them. Both the original-language and English reference fields
are considered.

Run it over a framework ``results.jsonl``:

    uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

# Verdict shape shared with the LLM judge (see JUDGE_OUTPUT_SCHEMA).
VERDICT_CORRECT = "correct"
VERDICT_INCORRECT = "incorrect"

# Separators that may delimit several acceptable answers in one field.
_REFERENCE_SPLIT_RE = re.compile(r"[/;|،]")

# Leading English articles stripped before comparison ("the X" == "X").
_LEADING_ARTICLES = ("the ", "a ", "an ")


def normalize(text: Any) -> str:
    """Return a script-agnostic normalized form for matching."""
    if text is None:
        return ""
    s = unicodedata.normalize("NFKC", str(text)).casefold()
    # Strip combining marks (accents, Arabic tashkeel, etc.).
    s = "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if unicodedata.category(ch) != "Mn"
    )
    # Drop punctuation and symbols (category P* / S*) -> space.
    s = "".join(
        " " if unicodedata.category(ch)[0] in ("P", "S") else ch
        for ch in s
    )
    s = re.sub(r"\s+", " ", s).strip()
    for article in _LEADING_ARTICLES:
        if s.startswith(article):
            s = s[len(article):]
            break
    return s


def split_reference(reference: Any) -> list[str]:
    """Split a reference field into individual acceptable answers."""
    if reference is None:
        return []
    parts = _REFERENCE_SPLIT_RE.split(str(reference))
    return [p.strip() for p in parts if p and p.strip()]


def reference_variants(*references: Any) -> list[str]:
    """Collect, de-duplicate (by normalized form), and order reference answers."""
    seen: set[str] = set()
    variants: list[str] = []
    for ref in references:
        for part in split_reference(ref):
            norm = normalize(part)
            if norm and norm not in seen:
                seen.add(norm)
                variants.append(part)
    return variants


def judge_exact_match(candidate: Any, *references: Any) -> dict[str, Any]:
    """Judge a single candidate answer against one or more reference fields.

    Returns a verdict dict with the same keys as the LLM judge.
    """
    cand_norm = normalize(candidate)
    variants = reference_variants(*references)
    variant_norms = {normalize(v): v for v in variants}

    if not cand_norm:
        return {
            "verdict": VERDICT_INCORRECT,
            "score": 0,
            "matched_reference": False,
            "reason": "Empty candidate answer.",
        }

    if cand_norm in variant_norms:
        return {
            "verdict": VERDICT_CORRECT,
            "score": 3,
            "matched_reference": True,
            "reason": f"Exact match (normalized) with reference '{variant_norms[cand_norm]}'.",
        }

    return {
        "verdict": VERDICT_INCORRECT,
        "score": 0,
        "matched_reference": False,
        "reason": (
            f"No exact match. Candidate '{candidate}' "
            f"did not equal any of {variants!r}."
        ),
    }


def extract_candidate_answer(row: Mapping[str, Any]) -> str | None:
    """Pull the model's answer out of a framework results row.

    Prefers a parsed ``riddle_answer`` field, falls back to parsing the raw
    JSON response, and finally to the raw text.
    """
    parsed = row.get("parsed_json")
    if isinstance(parsed, Mapping) and parsed.get("riddle_answer") is not None:
        return str(parsed["riddle_answer"])

    raw = row.get("raw_response")
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
            if isinstance(obj, Mapping) and obj.get("riddle_answer") is not None:
                return str(obj["riddle_answer"])
        except (ValueError, TypeError):
            pass
        return raw
    return str(raw)


@dataclass
class JudgedRow:
    riddle_id: str | None
    community: str | None
    candidate: str | None
    reference_original: str | None
    reference_english: str | None
    verdict: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "riddle_id": self.riddle_id,
            "community": self.community,
            "candidate_answer": self.candidate,
            "reference_answer_original": self.reference_original,
            "reference_answer_english": self.reference_english,
            "exact_match_verdict": self.verdict,
        }


def judge_row(row: Mapping[str, Any]) -> JudgedRow:
    candidate = extract_candidate_answer(row)
    ref_orig = row.get("reference_answer_original")
    ref_eng = row.get("reference_answer_english")
    verdict = judge_exact_match(candidate, ref_orig, ref_eng)
    return JudgedRow(
        riddle_id=row.get("riddle_id"),
        community=row.get("instance_community") or row.get("community"),
        candidate=candidate,
        reference_original=ref_orig,
        reference_english=ref_eng,
        verdict=verdict,
    )


def judge_results(rows: Iterable[Mapping[str, Any]]) -> list[JudgedRow]:
    return [judge_row(row) for row in rows]


def summarize(judged: list[JudgedRow]) -> dict[str, Any]:
    total = len(judged)
    correct = sum(1 for j in judged if j.verdict["matched_reference"])
    return {
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic exact-match judge over a results.jsonl"
    )
    parser.add_argument("results", help="Path to a framework run's results.jsonl")
    parser.add_argument(
        "--out",
        default=None,
        help="Where to write per-row verdicts (default: <results_dir>/exact_match_verdicts.jsonl)",
    )
    args = parser.parse_args(argv)

    results_path = Path(args.results)
    if not results_path.exists():
        parser.error(f"results file not found: {results_path}")

    rows = _load_jsonl(results_path)
    judged = judge_results(rows)

    out_path = Path(args.out) if args.out else results_path.parent / "exact_match_verdicts.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for j in judged:
            f.write(json.dumps(j.to_dict(), ensure_ascii=False) + "\n")

    summary = summarize(judged)
    print(f"Exact-match judge over {results_path}")
    print(f"  total={summary['total']}  correct={summary['correct']}  "
          f"incorrect={summary['incorrect']}  accuracy={summary['accuracy']:.2%}")
    print(f"  verdicts written to {out_path}")
    print()
    for j in judged:
        mark = "✓" if j.verdict["matched_reference"] else "✗"
        print(f"  {mark} {j.riddle_id}: cand={j.candidate!r}  ref={j.reference_original!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
