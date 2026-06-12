# Judges

How to score model answers produced by the benchmark framework. There are
two judges in this package:

| Judge | File | Type | Needs network / API key |
|-------|------|------|-------------------------|
| **Exact-match** | `exact_match_judge.py` | deterministic, rule-based | no |
| **LLM-as-a-judge** | `llm_as_a_judge.py` + `openrouter_smoke_test.py` | LLM-scored (OpenRouter) | yes (`OPENROUTER_KEY`) |

Start with the exact-match judge — it is fast, free, and reproducible. Use
the LLM judge when you need to credit paraphrases / partially-correct answers
that exact match cannot.

---

## Input: a framework run

Both judges score the answers in a framework run's `results.jsonl`:

```
framework/runs/<run_id>/results.jsonl
```

Each row carries the model's `raw_response` (JSON with `riddle_answer`) plus
the gold `reference_answer_original` / `reference_answer_english`. Produce one
by running the framework, e.g.:

```bash
cd framework
export OPENAI_API_KEY=...
uv run python -m riddles_framework.cli --config configs/openai_gpt55_high_smoke25.yaml
# -> framework/runs/<run_id>/results.jsonl
```

---

## 1. Exact-match judge (recommended first)

Deterministic: it normalizes the candidate and the reference answer(s) and
checks for an exact match. No model, no API key, fully reproducible.

### Run it

From the repo root:

```bash
uv run python -m judge.exact_match_judge framework/runs/<run_id>/results.jsonl
```

Optional: choose where the per-row verdicts are written (defaults to
`<results_dir>/exact_match_verdicts.jsonl`):

```bash
uv run python -m judge.exact_match_judge \
  framework/runs/<run_id>/results.jsonl \
  --out judge/examples/my_verdicts.jsonl
```

It prints a summary plus a per-riddle ✓/✗ table, for example:

```
Exact-match judge over framework/runs/5c5b3151.../results.jsonl
  total=25  correct=12  incorrect=13  accuracy=48.00%
  verdicts written to framework/runs/5c5b3151.../exact_match_verdicts.jsonl

  ✗ arabic_egypt_politics_001: cand='ميدان التحرير'  ref='التحرير'
  ✓ arabic_egypt_politics_002: cand='سعد زغلول'  ref='سعد زغلول'
  ...
```

### As a library

```python
from judge import judge_exact_match, judge_results

judge_exact_match("the First Amendment", "First Amendment")
# -> {"verdict": "correct", "score": 3, "matched_reference": True, "reason": "..."}
```

### How matching works

Normalization is script-agnostic:

- Unicode NFKC + casefold
- strip combining marks (Latin accents, Arabic tashkeel, ...)
- drop punctuation / symbols
- collapse whitespace
- strip leading English articles (`the` / `a` / `an`)

A reference field may list several acceptable answers separated by `/ ; | ،`
(including the Arabic comma); the candidate matches if it equals **any** of
them, and both the original-language and English references are checked.

### Verdict shape

Identical to the LLM judge, so the two are interchangeable downstream:

```json
{"verdict": "correct", "score": 3, "matched_reference": true, "reason": "..."}
```

`verdict` is `correct` / `incorrect`; `score` is `3` (match) or `0` (no match).

### Limitations (it is strict by design)

Exact match marks these as incorrect even though a human might not:

- extra qualifiers: `ميدان التحرير` ("Tahrir **Square**") vs `التحرير`
- reference with a prefix/parenthetical: `George Washington` vs `I am George Washington`
- synonyms / different surface form: `Владимир Ленин` vs `Ленин`
- abstentions (`I don't know`) and wordplay answers

For those, use the LLM judge below.

### Example output (checked into git)

A full 25-row sample over the GPT-5.5 smoke run lives at:

```
judge/examples/exact_match_verdicts.sample.jsonl
```

---

## 2. LLM-as-a-judge (OpenRouter)

`llm_as_a_judge.py` is a library (model registry, judge prompt, output
schema, OpenRouter payload builders). `openrouter_smoke_test.py` is a
runnable smoke test that drives it.

### Prerequisites

- An OpenRouter API key in a `.env` file at the repo root:

  ```
  OPENROUTER_KEY=sk-or-...
  ```

- `pandas` installed (the smoke test reads an Excel workbook).

### Run the smoke test

```bash
uv run python -m judge.openrouter_smoke_test
```

Tunable via environment variables:

| Var | Default | Meaning |
|-----|---------|---------|
| `MODEL_LIMIT` | `20` | how many target models to query |
| `SAMPLE_SIZE` | `20` | riddles sampled from the workbook |
| `SAMPLE_SEED` | `42` | sampling seed |
| `OUTPUT_PATH` | `judge/openrouter_eval_german_20_models_20_examples.jsonl` | where rows are written |

> ⚠️ **Caveat:** `openrouter_smoke_test.py` currently hard-codes an Excel
> workbook path on a specific machine
> (`/Users/.../Cultural Riddles Benchmark [German_Germany].xlsx`) and the
> `german_germany` culture. Point it at your own workbook before running, or
> adapt it to read a framework `results.jsonl` like the exact-match judge does.

### Judge output schema

```json
{
  "verdict": "correct | partially_correct | incorrect | unclear",
  "score": 0,
  "matched_reference": true,
  "reason": "..."
}
```

---

## Notes on git / outputs

- `judge/*.jsonl` and `judge/*.log` are git-ignored (raw run dumps), as is
  `framework/runs/`. Curated example outputs go under `judge/examples/`,
  which **is** tracked — that is where committed sample cases live.
