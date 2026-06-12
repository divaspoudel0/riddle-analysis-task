# Judges

## Exact-match judge

Scores a framework run's answers by exact match (case- and
whitespace-insensitive) against the reference answer.

```bash
uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
```

It prints a per-riddle ✓/✗ line plus a total, and writes the verdicts to
`<run_dir>/exact_match.jsonl`. Actual output over the GPT-5.5 smoke run:

```
✗ arabic_egypt_politics_001: 'ميدان التحرير' vs 'التحرير'
✓ arabic_egypt_politics_002: 'سعد زغلول' vs 'سعد زغلول'
✓ arabic_egypt_politics_003: 'محمد نجيب' vs 'محمد نجيب'
✗ arabic_egypt_politics_004: 'مجلس النواب' vs 'مجلس النواب/مجلس الشعب/البرلمان'
✗ arabic_egypt_politics_005: 'السفير' vs 'السفير/النائب'
...

9/25 exact matches  ->  framework/runs/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/exact_match.jsonl
```

As a library:

```python
from judge import match
match("Donald Trump", "Donald Trump")  # -> True
```

The full verdicts from that run are checked in at
`judge/examples/exact_match_verdicts.sample.jsonl`.

## LLM-as-a-judge

`llm_as_a_judge.py` (library) + `openrouter_smoke_test.py` (runner) score
answers with an LLM via OpenRouter. Needs `OPENROUTER_KEY` in `.env`:

```bash
uv run python -m judge.openrouter_smoke_test
```

> Note: `openrouter_smoke_test.py` hard-codes a German Excel workbook path;
> point it at your own data before running.

## Outputs in git

`judge/*.jsonl` and `framework/runs/` are git-ignored. Curated example
outputs go under `judge/examples/`, which is tracked.
