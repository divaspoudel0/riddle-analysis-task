# Analysis instructions

The `analysis` package owns reproducible corpus, evaluation, model, and
riddle-writing summaries. Run commands from the repository root so imports and
shared paths resolve consistently.

## Run the complete analysis

```bash
uv run --project analysis python -m analysis.run_all
```

The runner executes corpus analysis, evaluation analysis, model analysis, and
riddle-writing analysis. It rebuilds the four-tab dashboard after all figures
exist.

## Figure ownership

Every generator writes a review PNG and publication PDF through
`analysis.style.save_figure_pair`. The semantic stem is the filename after the
family prefix. The dashboard catalog in `dashboard/build_static.py` presents
these figures in four tabs.

| Prefix | Figure stem | Generator |
| --- | --- | --- |
| `r_` | `wildcard_theme_distribution` | `riddle_analysis/corpus_data.py` |
| `r_` | `answer_length_by_topic` | `riddle_analysis/corpus_data.py` |
| `r_` | `human_validation_coverage` | `riddle_analysis/corpus_data.py` |
| `r_` | `answer_length_by_region` | `riddle_analysis/corpus_data.py` |
| `m_` | `exact_match_accuracy_leaderboard` | `model_results/leaderboard.py` |
| `m_` | `exact_match_accuracy_by_topic` | `model_results/topic_performance.py` |
| `m_` | `exact_match_accuracy_by_region` | `model_results/group_performance.py` |
| `m_` | `exact_match_accuracy_by_language_group` | `model_results/group_performance.py` |
| `m_` | `exact_match_accuracy_by_language` | `model_results/group_performance.py` |
| `m_` | `reasoning_accuracy_delta_by_topic` | `model_results/thinking_delta.py` |
| `w_` | `topic_writing_difficulty` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `topic_difficulty_vs_model_accuracy` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `specificity_strategy` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `ai_use_functions` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `confidence_distribution` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `time_per_riddle` | `riddle_writing_analysis/survey_analysis.py` |
| `w_` | `resources_used` | `riddle_writing_analysis/survey_analysis.py` |
| `e_` | `accuracy_exact_match_vs_human_correct` | `eval_analysis/accuracy_comparison.py` |
| `e_` | `human_accuracy_distribution_by_community` | `eval_analysis/human_accuracy.py` |
| `e_` | `human_accuracy_heatmap_by_community` | `eval_analysis/human_accuracy.py` |
| `e_` | `human_correct_answers_missed_by_exact_match` | `eval_analysis/human_accuracy.py` |
| `e_` | `community_accuracy_exact_match_vs_human` | `eval_analysis/community_metrics.py` |
| `e_` | `exact_match_agreement_by_community` | `eval_analysis/community_metrics.py` |
| `e_` | `outcome_failure_mode_composition` | `eval_analysis/outcome_failure_modes.py` |
| `e_` | `human_outcomes_and_culture_distribution` | `eval_analysis/outcome_culture_composite.py` |

Do not create a second generator for an existing stem. If a figure changes its
meaning, update the stem, generator, dashboard card, and this table together.

## Artifact conventions

- Store generated figures in `analysis/figures/` through `figure_stem()`.
- Keep PNGs under version control. Publication PDFs remain Git-ignored.
- Store compact aggregate CSVs beside the analysis package that creates them.
- Keep raw model answers, raw human annotations, judge outputs, and credentials
  in Git-ignored `data/` directories.
- The optional LLM-as-a-judge tooling lives in
  `eval_analysis/llm_as_a_judge.py` and `eval_analysis/llm_judge_run.py`.

## Code conventions

Use type annotations for new functions, Google-style docstrings for public
functions, and `pathlib.Path` for paths. Keep each `main()` focused on one
subpackage and safe to call from `analysis.run_all`.
