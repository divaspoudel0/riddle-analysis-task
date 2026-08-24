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

### Reconcile the human-score schema

- **Scope:** medium
- **Priority:** high
- **Description:** Define one canonical representation for human scores. The
  contribution schema stores a raw 0–2 label, while evaluation analysis uses a
  0–3 scale for incorrect, uncertain, partial, and correct outcomes. Preserve
  the raw value, document the mapping, parse it once, and make strict and
  lenient metrics use named constants.
- **Relevant files to start:** `data_loading/pilot_dataset_config.py`,
  `data_loading/build_pilot_dataset.py`, `data_loading/pilot_dataset/README.md`,
  `analysis/eval_analysis/data.py`, `analysis/eval_analysis/README.md`.

### Crawl and integrate additional model results

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

### Close corpus data-quality follow-ups

- **Scope:** medium
- **Priority:** medium
- **Description:** Resolve or explicitly document the remaining missing English
  riddles and answers, review metadata aliases and country geometry coverage,
  and explain incomplete validator coverage by collection round. Keep the
  corpus figures reproducible while distinguishing data limitations from
  modeling results.
- **Relevant files to start:** `analysis/riddle_analysis/corpus_audit.py`,
  `analysis/riddle_analysis/corpus_data.py`,
  `analysis/riddle_analysis/coverage_map.py`,
  `analysis/corpus.py`, `analysis/corpus_metadata.csv`,
  `analysis/riddle_analysis/outputs/corpus_quality_report.md`.

### Extend the cross-task analysis

- **Scope:** medium
- **Priority:** high
- **Description:** Build a topic-level cross-task figure that combines writer
  difficulty, model exact-match rate, human-versus-automatic score gap, and
  human-evaluation coverage. Use a scatter plot with writing difficulty on the
  x-axis, the human-versus-automatic gap on the y-axis, bubble size for the
  number of evaluated riddles, and color for model or topic family. This
  extends the existing writing-difficulty versus model-accuracy figure while
  making coverage and evaluator disagreement visible.
- **Relevant files to start:** `analysis/riddle_writing_analysis/survey_analysis.py`,
  `analysis/model_results/topic_performance.py`,
  `analysis/eval_analysis/model_summary.py`,
  `analysis/eval_analysis/data.py`,
  `analysis/figures/w_topic_difficulty_vs_model_accuracy.png`,
  `analysis/dashboard/build_static.py`.

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

### Complete publication figure and dashboard QA

- **Scope:** small
- **Priority:** medium
- **Description:** Render every figure at publication size and inspect labels,
  legends, font coverage, captions, and accessible descriptions. Fix clipped
  labels and overly dense annotations, then rebuild the dashboard so the PNG,
  PDF, CSV, Markdown, and embedded HTML artifacts come from one documented
  command.
- **Relevant files to start:** `analysis/style.py`,
  `analysis/riddle_analysis/corpus_data.py`,
  `analysis/model_results/leaderboard.py`,
  `analysis/eval_analysis/outcome_failure_modes.py`,
  `analysis/dashboard/build_static.py`, `analysis/dashboard/README.md`,
  `analysis/figures/`.

### Strengthen riddle-writing survey conclusions

- **Scope:** medium
- **Priority:** low
- **Description:** Treat the current descriptive survey as a baseline, then
  add respondents for underrepresented communities and report uncertainty or
  minimum group sizes. If free-text responses become part of the paper,
  define a documented coding guide and inter-coder review rather than folding
  uncoded comments into the existing aggregate figures.
- **Relevant files to start:** `analysis/riddle_writing_analysis/survey_analysis.py`,
  `analysis/riddle_writing_analysis/survey_audit.py`,
  `analysis/riddle_writing_analysis/README.md`,
  `analysis/riddle_writing_analysis/outputs/`.
