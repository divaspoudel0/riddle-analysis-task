# Analysis

`analysis` is an importable Python package for reproducible corpus, model, and
contributor-writing analyses. From the repository root:

```bash
uv sync --project analysis
uv run --project analysis python -m analysis.run_all
```

The root command runs four suites and then rebuilds the report dashboard:

1. `riddle_analysis/` — corpus structure and validation metadata.
2. `riddle_writing_analysis/` — the contributor riddle-writing process.
3. `model_results/` — full-corpus model results, especially exact-match accuracy.
4. `eval_analysis/` — human comparisons, outcome categories, and optional LLM-as-a-judge analysis.

The writing stage reads the model topic summary produced in the preceding
model stage. The dashboard exposes the four suites as tabs.

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
- Keep source code and compact aggregate CSVs. Survey responses and model
  responses remain private and Git-ignored pending a publication decision.

Focused commands are available as `python -m analysis.<suite>.<module>`. Each
subpackage documents its prefix in its `__init__.py`. See `AGENTS.md` for the
figure ownership map and the recommended run order. Build the dashboard
directly with `python -m analysis.dashboard.build_static` after the figures
exist.
