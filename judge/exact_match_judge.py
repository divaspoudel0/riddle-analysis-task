"""Simplest exact-match judge for riddle answers.

    uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def match(candidate, reference) -> bool:
    """Case- and whitespace-insensitive exact match."""
    c = str(candidate or "").strip().casefold()
    return bool(c) and c == str(reference or "").strip().casefold()


def candidate_answer(row) -> str:
    """Pull `riddle_answer` out of a framework results row."""
    raw = row.get("raw_response") or ""
    try:
        return str(json.loads(raw).get("riddle_answer", "") or "")
    except Exception:
        return str(raw)


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m judge.exact_match_judge <results.jsonl>")
        return 1

    path = Path(argv[0])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    out = path.parent / "exact_match.jsonl"
    correct = 0
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            cand = candidate_answer(row)
            ref = row.get("reference_answer_original")
            ok = match(cand, ref)
            correct += ok
            f.write(json.dumps(
                {"riddle_id": row.get("riddle_id"), "candidate": cand, "reference": ref, "match": ok},
                ensure_ascii=False,
            ) + "\n")
            print(f"{'✓' if ok else '✗'} {row.get('riddle_id')}: {cand!r} vs {ref!r}")

    print(f"\n{correct}/{len(rows)} exact matches  ->  {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
