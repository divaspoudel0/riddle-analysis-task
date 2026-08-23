---
title: Multicultural Riddles — Analysis report
emoji: 🧩
colorFrom: indigo
colorTo: blue
sdk: static
app_file: index.html
pinned: false
---

# Analysis report dashboard

The dashboard is a static report with an Overview tab followed by four analysis areas:

- **Overview** — restored exploratory views for human accuracy by region and country, model accuracy versus hallucination rate, per-community accuracy distributions, and human-evaluation coverage.

- **Riddle analysis** — corpus structure, topics, regions, and validation coverage.
- **Riddle writing** — contributor difficulty, process, resources, and AI use.
- **Model results** — full-corpus exact-match accuracy, including topic, region, and language breakdowns.
- **Evaluation** — human comparison, outcome and failure modes, and the optional LLM-as-a-judge tool.

Each report tab presents the current PNG figures with the figure caption and a
short description. The dashboard has no private data dependency at runtime
because the builder embeds each image and the Overview data in `index.html`.
The Overview charts use Plotly from a CDN, and report figures use Medium Zoom
from a CDN. Click a figure to zoom it; each card also links to the Python
script that generated it.

The Overview is built from the recorded evaluation export and does not run the
removed heuristic judge. Run the builder from a checkout that contains the
private evaluation export at
`analysis/eval_analysis/data/model_riddle_results_flat.csv`.

## Rebuild the dashboard

Run the complete analysis from the repository root:

```bash
uv run --project analysis python -m analysis.run_all
```

To rebuild only the HTML after changing the catalog or CSS:

```bash
uv run --project analysis python -m analysis.dashboard.build_static
```

The source figures live in `analysis/figures/`; the ownership map is in
`analysis/AGENTS.md`. Publication PDFs are generated alongside the PNGs and
remain separate from this review dashboard.
