# Analysis

`analysis` is an importable Python package for reproducible corpus, model, and
contributor-writing analyses. From the repository root:

```bash
uv sync --project analysis
uv run --project analysis python -m analysis.run_all
open analysis/dashboard/index.html
```

The root command runs four suites and then rebuilds the report dashboard:

1. `riddle_analysis/` — corpus structure and validation metadata.
2. `riddle_writing_analysis/` — the contributor riddle-writing process.
3. `model_results/` — full-corpus model results, especially exact-match accuracy.
4. `eval_analysis/` — human comparisons, outcome categories, and optional LLM-as-a-judge analysis.

The writing stage reads the model topic summary produced in the preceding
model stage. The dashboard exposes the analysis suites, paper tables, a
full-width Paper Figures preview, and progress trackers as tabs alongside the
Overview.

## Score model runs

The model-results package includes a deterministic reference-answer scorer for
framework `results.jsonl` files:

```bash
uv run --project analysis python -m analysis.model_results.reference_heuristic_judge \
  framework/runs/<run_id>/results.jsonl
```

The scorer writes `heuristic_match.jsonl` and `heuristic_summary.json` to
`analysis/model_results/data/combined/evals/<run_id>/`. See
[`evals/README.md`](../evals/README.md) for the input schema, matching rules,
and options.

Loading raw model results does not require a scorer. Accuracy figures do
require recorded verdicts from a scorer, and the model-results analysis raises
an explicit error when those verdicts are absent.

## Optional LLM-as-a-judge

The evaluation-analysis package also contains an optional provider-backed
judge for answers that need semantic review. It requires `GEMINI_API_KEY` and
can incur provider charges:

```bash
uv run --project analysis python -m analysis.eval_analysis.llm_judge_run \
  framework/runs/<run_id>/results.jsonl
```

The judge writes raw verdicts beside the run or to the path supplied with
`--out`. Keep those outputs private. See
[`eval_analysis/README.md`](eval_analysis/README.md) for the judge contract.

## Artifact policy

- Use [`style.py`](style.py), [`constants.py`](constants.py), [`corpus.py`](corpus.py),
  and [`corpus_metadata.csv`](corpus_metadata.csv) rather than local copies.
- Write all figures to `analysis/figures/` through `constants.figure_stem()`.
  Prefix names with `r_`, `m_`, `w_`, or `e_` for riddle corpus, model, riddle
  writing, or evaluation analyses.
- Use semantic figure stems that name the measured quantity and grouping. Do
  not add release labels such as `_v2` to figure filenames.
- Every figure has a review PNG and publication PDF. PNGs are version-controlled;
  PDFs are Git-ignored.
- Dashboard cards use stable tab-local IDs: `R1` for riddle analysis, `W1` for
  riddle writing, `M1` for model results, `E1` for evaluation, and `P1` for
  progress trackers.
- Keep source code and compact aggregate CSVs. Survey responses and model
  responses remain private and Git-ignored pending a publication decision.

Focused commands are available as `python -m analysis.<suite>.<module>`. Each
subpackage documents its prefix in its `__init__.py`. See `AGENTS.md` for the
figure ownership map and the recommended run order. Build the dashboard
directly with `python -m analysis.dashboard.build_static` after the figures
exist.
