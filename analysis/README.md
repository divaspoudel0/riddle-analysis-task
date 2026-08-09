# Analysis

`analysis` is an importable Python package for reproducible corpus, model, and
contributor-writing analyses. From the repository root:

```bash
uv sync --project analysis
uv run --project analysis python -m analysis.run_all
```

The root command runs corpus analysis, then model analysis, then writing
analysis; the final stage reads the model topic summary produced in the second
stage.

## Artifact policy

- Use [`style.py`](style.py), [`constants.py`](constants.py), [`corpus.py`](corpus.py),
  and [`corpus_metadata.csv`](corpus_metadata.csv) rather than local copies.
- Write all figures to `analysis/figures/` through `constants.figure_stem()`.
  Prefix names with `r_`, `m_`, `w_`, or `j_` for riddle corpus, model, riddle writing, or judge analyses.
- Every figure has a review PNG and publication PDF. PNGs are version-controlled;
  PDFs are Git-ignored.
- Keep source code and compact aggregate CSVs. Survey responses and model
  responses remain private and Git-ignored pending a publication decision.

Focused commands are available as `python -m analysis.<suite>.<module>`. Each
subpackage documents its prefix in its `__init__.py`.
