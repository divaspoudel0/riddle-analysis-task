# RiddlesBenchmarking

RiddlesBenchmarking builds and evaluates a multilingual, culturally grounded
riddle benchmark. This repository contains the dataset build pipeline, model
runner, scoring tools, and publication analysis.

## Start here

Install Python 3.12+ and [uv](https://docs.astral.sh/uv/), then clone the
repository and prepare the analysis environment:

```bash
git clone <repository-url>
cd RiddlesBenchmarking
uv sync --project analysis
```

The current corpus is
[`data_loading/pilot_dataset/pilot_dataset_v1.jsonl`](data_loading/pilot_dataset/pilot_dataset_v1.jsonl):
6,100 valid riddles from 61 communities collected in v0--v2. The frozen v0
corpus remains under `data_loading/v0_dataset/` for reproducibility.

## Repository map

| Path | Purpose |
| --- | --- |
| [`data_loading/`](data_loading/) | Validate submissions and build dataset releases |
| [`framework/`](framework/) | Run a configured model over the benchmark |
| [`evals/`](evals/) | Score model outputs |
| [`analysis/`](analysis/) | Generate reproducible publication tables and figures |

Each component has its own README. A usual workflow is: build or obtain the
dataset, run a model, score its `results.jsonl`, then regenerate analysis.
Provider API keys belong in environment variables, never commits.

## Run the analyses

From the repository root, regenerate everything in dependency order (corpus →
model → writing):

```bash
uv run --project analysis python -m analysis.run_all
```

The individual suite entry points remain useful while developing:

```bash
uv run --project analysis python -m analysis.riddle_analysis.main
uv run --project analysis python -m analysis.model_results.main
uv run --project analysis python -m analysis.riddle_writing_analysis.main
```

Focused scripts are also available, for example:

```bash
uv run --project analysis python -m analysis.riddle_analysis.wildcard_themes
uv run --project analysis python -m analysis.model_results.topic_performance
uv run --project analysis python -m analysis.riddle_writing_analysis.topic_difficulty
```

Each focused script performs one analysis job; the `main` module runs its suite.
Compact CSV summaries remain in each suite's `outputs/` directory. All figures
are written to `analysis/figures/`: `r_` for corpus, `m_` for model, `w_` for
writing, and `j_` for judge analyses. PNGs are committed for review; PDFs are
publication artifacts and ignored by Git. Private survey and model-response
inputs are Git-ignored. The
auditable community-to-region and language-group mapping is
[`analysis/corpus_metadata.csv`](analysis/corpus_metadata.csv); shared paths and
taxonomy constants are in [`analysis/constants.py`](analysis/constants.py).

## Run and score a model

Choose a configuration in `framework/configs/`, set the required provider key,
and run it:

```bash
cd framework
uv sync
uv run python -m riddles_framework.cli --config configs/benchmark_v0/gpt55_high.yaml
```

The run writes `framework/runs/<run_id>/results.jsonl`. Score it from the root:

```bash
python evals/reference_heuristic_judge.py framework/runs/<run_id>/results.jsonl
```

Read [`framework/README.md`](framework/README.md) for configuration and batch
execution, [`evals/README.md`](evals/README.md) for scoring, and
[`analysis/README.md`](analysis/README.md) for analysis conventions.

## Contributing

Keep raw data, derived outputs, and code separate. New analysis code should
have a single responsibility, expose a `main()` entry point, draw shared values
from `analysis/constants.py`, and use `analysis/style.py` for figures. Prefer
auditable CSVs over manual Python mappings.
