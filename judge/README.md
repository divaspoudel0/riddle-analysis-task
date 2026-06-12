# Judges

## Exact-match judge

Scores a framework run's answers by exact match (case- and
whitespace-insensitive) against the reference answer.

```bash
uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
```

It prints a per-riddle ✓/✗ line plus a total, and writes the verdicts to
`<run_dir>/exact_match.jsonl`:

```
✓ arabic_egypt_politics_002: 'سعد زغلول' vs 'سعد زغلول'
✗ arabic_egypt_politics_001: 'ميدان التحرير' vs 'التحرير'

12/25 exact matches
```

As a library:

```python
from judge import match
match("Donald Trump", "Donald Trump")  # -> True
```

A sample output is checked in at
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
