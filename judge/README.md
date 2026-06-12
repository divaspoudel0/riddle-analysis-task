# Judges

## Exact-match judge

Scores a framework run's answers by exact match (case- and
whitespace-insensitive) against the reference answer.

```bash
uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
```

It prints a per-riddle ✓/✗ line plus a total, and writes the verdicts to
`<run_dir>/exact_match.jsonl` (next to the input results).

As a library:

```python
from judge import match
match("Donald Trump", "Donald Trump")  # -> True
```

## LLM-as-a-judge

`llm_as_a_judge.py` (library) + `openrouter_smoke_test.py` (runner) score
answers with an LLM via OpenRouter. Needs `OPENROUTER_KEY` in `.env`:

```bash
uv run python -m judge.openrouter_smoke_test
```

> Note: `openrouter_smoke_test.py` hard-codes a German Excel workbook path;
> point it at your own data before running.
