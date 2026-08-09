# Riddle-writing reflection analysis

Follow the shared [analysis conventions](../README.md) for setup, artifact
policy, and the root reproducibility command.

Regenerate the descriptive survey analysis from the repository root:

```bash
uv run --project analysis python -m analysis.riddle_writing_analysis.main
```

The script reads the current reflection form, removes direct identifiers before
analysis, and writes aggregate figures to `analysis/figures/` with matching CSV summaries
in `outputs/`. Focused modules are `survey_audit`, `topic_difficulty`,
`specificity`, `ai_usage`, `confidence`, `writing_time`, and `resources`.

The analysis intentionally reports only closed-form survey responses and
explicitly selected resources. It does not make claims based on an undocumented
manual coding of free-text answers.

## Reproduce inputs

The private reflection-form export belongs at
`analysis/riddle_writing_analysis/data/[MCB]_Analysis_MasterSheet - reflection_form.csv`.
It is a direct CSV export from the contributor form and is Git-ignored because
it contains identifiers. `survey_analysis.load_survey()` removes timestamp and
Discord identifier columns before producing aggregates. The topic-difficulty
comparison also requires `analysis/model_results/outputs/topic_match_rate_summary.csv`,
which `python -m analysis.model_results.main` generates first. Run the root
pipeline to reproduce that dependency automatically.
