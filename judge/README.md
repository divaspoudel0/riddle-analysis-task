# Judges

Both judges score a benchmark **run's `results.jsonl`** (the framework's
output). For a ready-to-use input, use the committed example run:

```
framework/runs/examples/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/results.jsonl
```

## Exact-match judge

Deterministic exact match (case- and whitespace-insensitive) of each answer
against its reference.

```bash
uv run python -m judge.exact_match_judge \
  framework/runs/examples/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/results.jsonl
```

Prints a per-riddle ✓/✗ line plus a total, and writes the verdicts to
`<run_dir>/exact_match.jsonl` (next to the input results).

As a library:

```python
from judge import match
match("Donald Trump", "Donald Trump")  # -> True
```

## LLM-as-a-judge

Scores the same `results.jsonl` with an LLM via OpenRouter, using the judge
prompt + output schema in `llm_as_a_judge.py`. Needs `OPENROUTER_KEY` in
`.env`:

```bash
uv run python -m judge.openrouter_smoke_test \
  framework/runs/examples/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/results.jsonl
```

> Note: `openrouter_smoke_test.py` currently reads a hard-coded Excel workbook
> instead of a run's `results.jsonl`; point it at the run above (or adapt it to
> load `results.jsonl`) before running.
