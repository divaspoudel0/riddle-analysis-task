---
title: Multicultural Riddles — Human Eval
emoji: 🧩
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: 1.40.0
app_file: app.py
pinned: false
---

# Multicultural Riddles Benchmark — Human Evaluation Space

Provisional human-eval leaderboard and coverage tracker for MCB v0, for the
Cohere Labs lead team. Everything is recomputed live from Henry's flat file,
so it stays current as human annotation grows.

## What it shows

- **Leaderboard** — floor→ceiling dumbbell per model on the communities with
  complete human evaluation: heuristic auto-judge (lower bound) vs human
  judgement (upper bound). Strict / lenient toggle. Downloadable CSV.
- **Coverage** — per-community human-eval completion, with a chase list of
  communities not started or thin.

## Source of truth & guarantees

- The only score source is `data/model_riddle_results_flat.csv` (Henry).
- The leaderboard uses only communities with complete human coverage.
- Pending (un-scored) rows are **dropped, never guessed** — every number
  traces to the flat file with zero assumptions.
- Single annotator per riddle (no inter-annotator agreement); provisional and
  labelled N/44 until coverage completes.
- Cuba riddle `spanish_cuba_history_016` excluded (wrong v0 text; redone in v2).

## Refreshing

To refresh, replace `data/model_riddle_results_flat.csv` with Henry's newer
export and push. The app is cached on the file's modified time, so it
recomputes automatically. `data/results_tidy.parquet` is our static
heuristic-judge output (the floor) and rarely changes.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
