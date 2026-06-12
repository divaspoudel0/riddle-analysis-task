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

Lenient LLM scoring of the same `results.jsonl` (credits paraphrases /
transliterations that exact match misses). Reuses the judge prompt + output
schema from `llm_as_a_judge.py`; sends via the OpenAI SDK with a gpt-mini
model by default. Needs `OPENAI_API_KEY`:

```bash
python -m judge.llm_judge_run \
  framework/runs/examples/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/results.jsonl \
  --model gpt-5.4-mini
```

Writes verdicts (same shape as exact-match) to `<run_dir>/llm_judge.jsonl`.

> `llm_as_a_judge.py` also has an OpenRouter path used by
> `openrouter_smoke_test.py` (needs `OPENROUTER_KEY`), but that runner is
> hard-coded to a German Excel workbook.
