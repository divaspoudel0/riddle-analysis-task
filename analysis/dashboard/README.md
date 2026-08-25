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

The dashboard is a static report with these tabs:

- **Overview** — restored exploratory views for human accuracy by region and country, model accuracy versus hallucination rate, and per-community accuracy distributions.
- **Paper tables** — corpus coverage and model-performance summaries.
- **Paper Figures** — a full-width paper preview assembled from selected figures.

- **Riddle analysis** — corpus structure, topics, and regions.
- **Riddle writing** — contributor difficulty, process, resources, and AI use.
- **Model results** — full-corpus exact-match accuracy, including topic, region, and language breakdowns.
- **Evaluation** — human comparison, outcome and failure modes, and the optional LLM-as-a-judge tool.
- **Progress Trackers** — human-evaluation coverage and validation progress.

Each report tab presents the current PNG figures with the figure caption and a
short description. Figure cards have stable tab-local IDs, such as `R1`, `W1`,
`M1`, `E1`, and `P1`. The dashboard has no private data dependency at runtime
because the builder embeds each image and the Overview data in `index.html`.
The Overview charts use Plotly from a CDN, and report figures use Medium Zoom
from a CDN. Click a figure to zoom it; each card also links to the Python
script that generated it.

To assemble paper figures, click **Add to Paper Figures** on any figure card.
Open the **Paper Figures** tab to review the selected figures in one full-width
column. Figures appear in the order they were selected; use **Move up** and
**Move down** to set the paper order, or **Clear all** to start over. The
selection is held in the current browser page and is not written to disk.

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
