---
title: Multicultural Riddles — Human Eval
emoji: 🧩
colorFrom: indigo
colorTo: blue
sdk: static
app_file: index.html
pinned: false
---

# Multicultural Riddles Benchmark — Human Evaluation Space

Provisional human-eval leaderboard and coverage tracker for MCB v0, for the
Cohere Labs lead team. Deployed as a free **Static** Space: `build_static.py`
precomputes every metric from Henry's flat file and bakes the numbers into a
self-contained `index.html` (Plotly from CDN). Same views as the Streamlit
app, no server compute required.

## Views

- **Leaderboard** — floor→ceiling per model on communities with complete human
  eval (heuristic auto-judge vs human). Strict / lenient toggle.
- **Community difficulty** — mean accuracy per culture, floor vs ceiling.
- **Judge vs human** — Cohen's κ per community, plus how many human-correct
  answers the auto-judge missed vs over-credited.
- **Coverage** — per-community completion + chase list.
- **Coverage map** — placeholder crediting Pouya Sadeghi; add the image later.

## Source of truth & guarantees

- Only score source is `data/model_riddle_results_flat.csv` (Henry).
- Leaderboard uses only communities with complete human coverage.
- Pending rows are **dropped, never guessed** — every number traces to the flat
  file. Single annotator per riddle; provisional, labelled N/44.
- Cuba riddle `spanish_cuba_history_016` excluded (redone in v2).

## Refreshing

1. Replace `data/model_riddle_results_flat.csv` with Henry's newer export.
2. `python build_static.py`  (regenerates `index.html`).
3. Commit `index.html` and push to the Space.

The `data/` folder and Python files are used only to *build* `index.html`; the
deployed Static Space needs just `index.html` (+ this README).

## Two SDK options

- `app.py` / `requirements.txt` are the Streamlit version, for if the org ever
  moves to a paid plan (Streamlit needs compute).
- `index.html` is the free Static version and is what this README deploys.
