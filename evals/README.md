# Reference-answer heuristic judge

The benchmark framework writes model responses to `results.jsonl`. The
reference-answer heuristic judge scores those responses without making an API
call. It is the deterministic exact-match floor used by the model-results
analysis.

## Run the judge

From the repository root, run the scorer on a framework run:

```bash
uv run --project analysis python -m analysis.model_results.reference_heuristic_judge \
  framework/runs/<run_id>/results.jsonl
```

By default, the scorer writes the following files to
`analysis/model_results/data/combined/evals/<run_id>/`:

- `heuristic_match.jsonl` — one verdict per result row.
- `heuristic_summary.json` — aggregate counts and the match rate.

Use the options below to select another output directory or process a subset:

```bash
uv run --project analysis python -m analysis.model_results.reference_heuristic_judge \
  framework/runs/<run_id>/results.jsonl \
  --out-dir /tmp/riddle-eval \
  --limit 100
```

The scorer also accepts additional abstention phrases:

```bash
uv run --project analysis python -m analysis.model_results.reference_heuristic_judge \
  framework/runs/<run_id>/results.jsonl \
  --additional-no-answer-phrases "I give up" "No clue"
```

## Input schema

The input must be a JSONL file with one object per model response. Each row
must contain:

- `raw_response` — the model's raw answer.
- `reference_answer_original` — the correct answer in the source language.

The following fields are optional but help trace output rows:

- `riddle_id` — the riddle identifier.
- `run_id` — the framework run identifier.
- `parsed_json` — a previously parsed response object.

The model prompt must contain the riddle, but it must not contain the reference
answer. The model response can be a JSON object with `riddle_answer`, plain
text, or a response that contains a recoverable JSON answer.

## Scoring rules

The judge applies the same conservative normalization to every language and
script:

- Unicode-normalize with `NFKC`.
- Case-fold the text.
- Remove whitespace, punctuation, symbols, separators, and control
  characters.

It also expands simple reference alternatives separated by parentheses,
slashes, commas, semicolons, or spaced hyphens. It does not translate,
transliterate, infer synonyms, or use language-specific cleanup.

The output score uses the following values:

- `3` — the candidate matches a normalized reference form.
- `1` — the candidate explicitly says that it does not know.
- `0` — the candidate does not match or cannot be parsed.

Rows include the candidate, reference, verdict, score, match type, parse status,
and a reason so that the deterministic result is auditable.
