# Model-results analysis

Follow the shared [analysis conventions](../README.md) for setup, artifact
policy, and the root reproducibility command.

This suite turns private raw model runs into a reproducible, compact tidy table,
then audits and plots the complete-coverage subset.

## Rebuild inputs end to end

1. Download each model-run folder (containing `results.jsonl` and
   `run_config.json`) from the [shared results archive](https://drive.google.com/drive/folders/1ow1GKXeaOFJJr_59-Qg7erQf046mi2t1) into
   `analysis/model_results/data/responses/`. Keep folder names unchanged.
2. Score every raw result with the deterministic evaluator from the repository
   root: `python evals/reference_heuristic_judge.py <results.jsonl>`. This writes
   `evals/outputs/<run_id>/heuristic_match.jsonl`.
3. Build the private tidy input:

   ```bash
   uv run --project analysis python -m analysis.model_results.load_results \
     analysis/model_results/data/responses \
     analysis/model_results/data/combined/processed/results_tidy.csv \
     evals/outputs
   ```

   `load_results` extracts answers, applies documented run/riddle exclusions,
   assigns canonical collection rounds from the released corpus, and joins judge
   outputs. Raw runs and the tidy CSV are Git-ignored.

4. Audit and produce figures:

   ```bash
   uv run --project analysis python -m analysis.model_results.data_audit
   uv run --project analysis python -m analysis.model_results.main
   ```

`model_data_quality.csv` and `model_data_quality_report.md` document parse,
coverage, judge-join, and token-limit follow-up checks. Performance figures use
only models with all 6,099 evaluable riddles and write PNG/PDF pairs under
`analysis/figures/` using the `m_` prefix.
