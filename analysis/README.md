# Analysis

`analysis` is an importable Python package for reproducible corpus, model, and
contributor-writing analyses. From the repository root:

## Quick links

The following links point to the main local inputs and shared data locations:

### Local inputs

- [Released riddle corpus](../data_loading/pilot_dataset/pilot_dataset_v1.jsonl)
- [Model-response input directory](model_results/data/responses/) (private and
  Git-ignored)
- [Human-evaluation responses](eval_analysis/data/model_riddle_results_flat.csv)
  (private and Git-ignored)

### Shared data

- [Shared Google Drive](https://drive.google.com/drive/u/0/folders/1-HxD2QfqCOqvoHUeYezEMxvo1-CezzrU)
  contains intermediary data from all teams.
- [Riddles from v0 through v2](https://drive.google.com/drive/u/0/folders/11zefNCw2VnECz2CytJVwpG8E4VDiZEvy)
- [Model responses](https://drive.google.com/drive/u/0/folders/1ow1GKXeaOFJJr_59-Qg7erQf046mi2t1)
- Human-evaluation responses are available from the [shared Google Drive](https://drive.google.com/drive/u/0/folders/1-HxD2QfqCOqvoHUeYezEMxvo1-CezzrU).

The local model-response and human-evaluation paths contain private data. Do
not commit raw responses, annotations, or credentials.

## Setup

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

## Analysis status

This status describes the repository's current artifacts and data dependencies.
It supersedes older task-assignment progress columns, which do not reflect the
figures and tables that are already checked in.

| Workstream | Status | Current boundary |
| --- | --- | --- |
| Riddle analysis | Nearly complete | Corpus structure, metadata, language coverage, wildcard themes, English-length summaries, and validation coverage are implemented. The remaining work is data-quality follow-up as missing translations and validation rows are resolved. |
| Riddle-writing analysis | Nearly complete | The descriptive survey outputs cover topic difficulty, writing time, specificity, resources, generative AI use, confidence, and scale relationships. Treat small community samples as exploratory, and do not infer themes from free-text responses without a documented coding protocol. |
| Model results | Awaiting more runs | Ingestion, scoring joins, quality audits, model selection, tables, and figures are implemented. The checked-in snapshot is not the final model comparison because more model results are still being crawled. |
| Evaluation analysis | Awaiting more human evaluations | Human-score loading, coverage reports, exact-match comparisons, outcome categories, and dashboard views are implemented. The checked-in snapshot remains incomplete until the next human-evaluation export is available. |
| LLM as a judge | Scaffolded, not validated | The provider-agnostic contract and a Gemini runner exist. The rubric, calibration set, agreement analysis, multilingual policy, and release criteria remain open. |

The riddle corpus snapshot contains 6,100 riddles from 61 communities and 51
languages. The riddle-writing snapshot contains 76 survey responses from 43
communities. These counts describe the checked-in artifacts, not a promise that
future data refreshes preserve the same coverage.

Use [`TODO.md`](TODO.md) for scoped follow-up tasks. When more model results or
human evaluations arrive, rebuild the private inputs first, then regenerate
the aggregate CSVs, tables, figures, and dashboard together.

## LLM-as-a-judge

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
