# Model-results analysis

Follow the shared [analysis conventions](../README.md) for setup, artifact
policy, and the root reproducibility command.

This suite turns private raw model runs into a reproducible, compact tidy table,
then audits and plots the complete-coverage subset.

## Rebuild inputs end to end

1. Download each model-run folder (containing `results.jsonl` and
   `run_config.json`) from the [shared results archive](https://drive.google.com/drive/folders/1ow1GKXeaOFJJr_59-Qg7erQf046mi2t1) into
   `analysis/model_results/data/responses/`. Keep folder names unchanged.
2. Scoring is optional for loading raw results. To generate accuracy figures,
   score each run with the deterministic reference-answer scorer:

   ```bash
   uv run --project analysis python -m analysis.model_results.reference_heuristic_judge \
     analysis/model_results/data/responses/<run_folder>/results.jsonl
   ```

   The scorer writes `heuristic_match.jsonl` and
   `heuristic_summary.json` under the private
   `analysis/model_results/data/combined/evals/<run_id>/` directory.
3. Build the private tidy input. This command also works when the evaluation
   directory is absent; it writes raw extracted answers without verdicts:

   ```bash
   uv run --project analysis python -m analysis.model_results.load_results \
     analysis/model_results/data/responses \
     analysis/model_results/data/combined/processed/results_tidy.csv \
     analysis/model_results/data/combined/evals
   ```

   The `load_results.py` ingestion command extracts answers, applies documented
   run/riddle exclusions, assigns canonical collection rounds from the released
   corpus, and joins judge outputs. Raw runs and the tidy CSV are Git-ignored.

4. Audit and produce figures:

   ```bash
   uv run --project analysis python -m analysis.model_results.data_audit
   uv run --project analysis python -m analysis.model_results.main
   ```

The ingestion command produces the raw tidy table. The analysis modules use
`model_data.load_scored_results()` to add derived metrics, require recorded
verdicts, enforce complete coverage, and select the analysis roster.

`model_data_quality.csv` and `model_data_quality_report.md` document parse,
coverage, judge-join, and token-limit follow-up checks. Performance figures use
only models with all 6,099 evaluable riddles and write PNG/PDF pairs under
`analysis/figures/` using the `m_` prefix. Figure stems name the measured
quantity, such as `m_exact_match_accuracy_by_topic`.

`outputs/five_worst_communities_by_model.csv` lists each model's five
lowest-performing communities, with the completed-response exact-match accuracy
and denominator for every entry.
