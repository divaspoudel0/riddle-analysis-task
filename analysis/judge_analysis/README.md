# Judge analysis

Follow the shared [analysis conventions](../README.md) for setup, artifact
policy, and the root reproducibility command. This package owns aggregate
analysis of evaluation evidence produced by [`evals/`](../../evals/), not model
response loading or benchmark performance figures.

## What belongs here

- **Heuristic judge**: deterministic reference-answer matching outputs from
  `evals/reference_heuristic_judge.py`.
- **LLM judge**: lenient semantic verdicts from `python -m evals.llm_judge_run`.
- **Human evaluation**: reviewer annotations and coverage summaries.
- **Inter-annotator agreement**: agreement between human annotators and, where
  appropriate, agreement between human, heuristic, and LLM verdicts.

Raw answers, individual human annotations, and evaluator outputs can be
private. This package should only commit non-identifying aggregate CSV summaries
and `j_`-prefixed PNG figures in `analysis/figures/`; matching PDFs are generated
for publication and ignored by Git.

## Reproduce judge inputs

Run evaluators against a model `results.jsonl` from the repository root:

```bash
python evals/reference_heuristic_judge.py framework/runs/<run_id>/results.jsonl
python -m evals.llm_judge_run framework/runs/<run_id>/results.jsonl
```

These write evaluator artifacts under `evals/outputs/` or beside the run,
depending on the evaluator. Place any private human-evaluation export in a
Git-ignored `analysis/judge_analysis/data/` directory, document its schema, and
derive only aggregate audits and agreement tables here.
