# Corpus analysis

Follow the shared [analysis conventions](../README.md) for setup, artifact
policy, and the root reproducibility command.

The corpus suite reads the released JSONL directly, validates identity-level
invariants, writes compact audit summaries, and generates `r_` figures.

## Reproduce inputs

The source is `data_loading/pilot_dataset/pilot_dataset_v1.jsonl`, produced by
the validation and release workflow documented in `data_loading/pilot_dataset/`.
No cached spreadsheet or private input is required. Region and language-group
labels are loaded from the reviewable `analysis/corpus_metadata.csv`.

Run `uv run --project analysis python -m analysis.riddle_analysis.main`, or run
`corpus_audit`, `wildcard_themes`, or `english_length` individually. The audit
also writes `outputs/corpus_quality_report.md`, including translation,
duplication, validator-coverage, and release-invariant follow-up checks.
