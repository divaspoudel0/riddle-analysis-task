# Analysis TODO

This list is based on the current analysis code, checked-in aggregate outputs,
tables, and figures. It replaces older task-assignment snapshots whose
progress columns are out of date. A task is open when the code or protocol
needs work, even if a preliminary figure or table already exists.

## Current priorities

Complete the data-dependent work before treating model or evaluation figures
as final. The riddle and riddle-writing suites are close to complete as
descriptive analyses. The model-results and evaluation suites are ready for
refreshes, but their results depend on more crawled model runs and human
evaluations.

## Tasks

### Design the LLM-as-a-judge protocol

- **Scope:** large
- **Priority:** high
- **Description:** Turn the existing scaffold into a versioned evaluation
  protocol. Define the rubric, score labels, treatment of synonyms and
  transliteration, cultural specificity rules, multilingual inputs, abstention
  behavior, structured output, prompt versioning, provider/model routes, cost
  limits, and reproducibility metadata. Include a small adjudicated calibration
  set before running the judge over private model outputs.
- **Relevant files to start:** `analysis/eval_analysis/llm_as_a_judge.py`,
  `analysis/eval_analysis/llm_judge_run.py`,
  `analysis/eval_analysis/README.md`, `analysis/constants.py`,
  `framework/runs/examples/5c5b3151-d3a1-4228-9e83-742b4cd2cd58/llm_judge.jsonl`.

### Visualize human evaluation by subscores

- **Scope:** medium
- **Priority:** high
- **Description:** Add figures that break human evaluation into the available
  score components instead of reporting only an aggregate correct rate. Start
  with the current ordinal score distribution and community-by-model slices.
  If the next annotation export adds subscores, extend the schema and show
  correctness, semantic adequacy, cultural specificity, and answer
  completeness separately. Include denominators and uncertainty so small
  communities are not overinterpreted.
- **Relevant files to start:** `analysis/eval_analysis/data.py`,
  `analysis/eval_analysis/human_accuracy.py`,
  `analysis/eval_analysis/community_metrics.py`,
  `analysis/eval_analysis/plot_helpers.py`, `analysis/style.py`,
  `analysis/figures/`.

### Compare LLM-judge and human-evaluation decisions

- **Scope:** large
- **Priority:** high
- **Description:** Join LLM-judge verdicts with human annotations at the
  riddle, model, community, language, and topic levels. Report confusion
  matrices, score calibration, exact agreement, chance-corrected agreement,
  and uncertainty. Cluster disagreement cases by failure mode, then inspect
  whether disagreements concentrate in transliteration, culturally specific
  entities, broad answers, or ambiguous riddles. For multiple human
  annotators, report inter-annotator agreement before using human labels as a
  reference.
- **Relevant files to start:** `analysis/eval_analysis/join_human_eval.py`,
  `analysis/eval_analysis/data.py`, `analysis/eval_analysis/llm_as_a_judge.py`,
  `analysis/eval_analysis/outcome_failure_modes.py`,
  `analysis/eval_analysis/community_metrics.py`,
  `analysis/model_results/load_results.py`.

### Add uncertainty to model and evaluation reports

- **Scope:** medium
- **Priority:** medium
- **Description:** Use the existing bootstrap helpers and coverage metadata to
  add confidence intervals or interval bands to model, community, language,
  and human-comparison summaries. Make the interval unit explicit and avoid
  treating riddles from the same community as independent when the analysis
  requires clustered resampling.
- **Relevant files to start:** `analysis/model_results/metrics.py`,
  `analysis/model_results/leaderboard.py`,
  `analysis/model_results/group_performance.py`,
  `analysis/eval_analysis/model_summary.py`, `analysis/style.py`.

### Select qualitative examples for the paper and blog

- **Scope:** medium
- **Priority:** high
- **Description:** Select 10 to 20 high-signal qualitative examples that
  illustrate strong successes, culturally revealing misses, confident
  fabrications, honest uncertainty, translation-sensitive cases, and why
  native-designed riddles matter. Record the model, riddle, reference answer,
  human and automatic judgments, community, language, and a short rationale
  for each selection. Keep the examples traceable to private row-level data
  while preparing a shareable redacted version for the paper or blog.
- **Relevant files to start:** `analysis/model_results/export_model_answers.py`,
  `analysis/eval_analysis/outcome_failure_modes.py`,
  `analysis/eval_analysis/data.py`, `analysis/figures/`,
  `analysis/model_results/outputs/`, `analysis/eval_analysis/README.md`.

### Pitch a wildcard analysis task

- **Scope:** medium
- **Priority:** medium
- **Description:** Propose an analysis task that is not already represented by
  the existing figures, tables, or tasks. Every proposal must include a task
  name and description, explain what value it adds beyond the existing
  artifacts, and explain how it contributes to the benchmark, paper, blog, or
  analysis workflow. The proposal must identify its data source, expected
  output, and a reproducible starting point in the repository.
- **Relevant files to start:** `analysis/README.md`, `analysis/TODO.md`,
  `analysis/figures/`, `analysis/tables/`, and the module that owns the proposed
  data source.

## Analysis team lead tasks

The analysis team leads own the following maintenance tasks. Contributors can
help with focused subproblems, but the leads coordinate the final refresh and
approval.

### Integrate additional model results

- **Scope:** large
- **Priority:** high
- **Description:** Add the next model-run folders, verify run metadata and
  response coverage, join recorded judge outputs, rerun data-quality audits,
  update the model roster, and regenerate model tables, figures, and dashboard
  assets. Keep incomplete or malformed runs visible in the audit without
  including them in complete-coverage comparisons.
- **Relevant files to start:** `analysis/model_results/load_results.py`,
  `analysis/model_results/data_audit.py`, `analysis/model_results/model_data.py`,
  `analysis/model_results/model_registry.py`,
  `analysis/model_results/model_selection.py`,
  `analysis/model_results/main.py`, `analysis/model_results/README.md`.

### Complete the human-evaluation collection refresh

- **Scope:** large
- **Priority:** high
- **Description:** Ingest the next human-evaluation export, update community
  coverage and completion statuses, verify model-name mappings, and regenerate
  the human-comparison tables and `e_` figures. Record which communities and
  models remain pending so that partial coverage is not mistaken for a final
  ranking.
- **Relevant files to start:** `analysis/eval_analysis/data.py`,
  `analysis/eval_analysis/model_summary.py`,
  `analysis/eval_analysis/human_accuracy.py`,
  `analysis/eval_analysis/community_metrics.py`,
  `analysis/eval_analysis/outcome_failure_modes.py`,
  `analysis/eval_analysis/join_human_eval.py`,
  `analysis/eval_analysis/README.md`.

### Add automated checks for analysis artifacts

- **Scope:** medium
- **Priority:** high
- **Description:** Add focused tests that validate table row counts and totals,
  figure-stem ownership, generated CSV and Markdown agreement, model and
  community coverage invariants, and dashboard references. Add a freshness
  check that fails when checked-in aggregate artifacts do not match the
  builders.
- **Relevant files to start:** `analysis/tables/build.py`,
  `analysis/dashboard/build_static.py`, `analysis/constants.py`,
  `analysis/run_all.py`, `analysis/pyproject.toml`, `analysis/figures/`.
