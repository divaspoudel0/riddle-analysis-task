# Evaluation analysis

This package owns aggregate evaluation evidence: human annotations, coverage,
outcome categories, exact-match comparisons, and optional LLM-as-a-judge
results. Model response loading and full-corpus exact-match performance belong
to `analysis/model_results/`.

## LLM-as-a-judge tooling

The provider-agnostic judge contract and runner now live in this package:

```bash
uv run --project analysis python -m analysis.eval_analysis.llm_judge_run \
  framework/runs/<run_id>/results.jsonl
```

The command may call a paid provider. It writes raw verdicts beside the run or
to the path supplied with `--out`; keep those files private. The OpenRouter
smoke test is available as `analysis.eval_analysis.openrouter_smoke_test`.

Exact-match figures use the canonical model-results exports and the recorded
judge columns available there. This package does not recreate a heuristic
evaluator from answer text.

## Run the evaluation analysis

From the repository root:

```bash
uv run --project analysis python -m analysis.eval_analysis.main
```

The suite writes evaluation tables and `e_` figures to `analysis/figures/`.
The four-tab report dashboard is rebuilt at the end of the full command:

```bash
uv run --project analysis python -m analysis.run_all
```

Raw model answers, human annotations, and judge outputs remain in
Git-ignored data directories. Commit only aggregate tables and review PNGs.
