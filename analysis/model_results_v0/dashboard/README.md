---
title: Multicultural Riddles Benchmark
emoji: 🧩
colorFrom: indigo
colorTo: blue
sdk: static
app_file: index.html
pinned: false
---

# Multicultural Riddles Benchmark — Human Evaluation Space

Provisional human-eval dashboard for MCB, for the Cohere Labs lead team. This is
the human-evaluation **ceiling** that complements the team's full-corpus
heuristic **floor**. Deployed as a free **Static** Space: `build_static.py`
precomputes every metric from the flat file and bakes the numbers into a
self-contained `index.html` (Plotly from CDN). No server, no Streamlit.

## Views

- **Leaderboard** — floor→ceiling per model on communities with complete human
  eval (heuristic auto-judge vs human). Strict / lenient toggle.
- **How models fail** — per-model error-type breakdown from human eval
  (hallucinated / wrong-entity / too-broad / partial / uncertainty / correct).
- **Community difficulty** — mean accuracy per culture, floor vs ceiling.
- **Judge vs human** — Cohen's κ per community (auto-judge vs human), plus how
  many human-correct answers the auto-judge missed vs over-credited.
- **Coverage** — per-community completion + chase list.

## Source of truth & guarantees

- Only score source is `data/model_riddle_results_flat.csv` (Henry Gagnier).
- Leaderboard and error types use only communities with complete human coverage.
- Pending rows are **dropped, never guessed** — every number traces to the flat
  file. Single annotator per riddle; provisional, labelled N/44.
- Heuristic judge is reference-based string matching (no LLM).
- Cuba riddle `spanish_cuba_history_016` excluded (redone in v2).

## Refreshing

1. Replace `data/model_riddle_results_flat.csv` with Henry's newer export.
2. `pip install pandas pyarrow && python build_static.py`  (regenerates `index.html`).
3. Upload `index.html` to the Space (Files → Add file → Upload) and commit.

The `data/` folder and `build_static.py` are only used to *build* `index.html`;
the deployed Static Space serves just `index.html` (+ this README).
