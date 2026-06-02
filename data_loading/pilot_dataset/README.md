# Pilot Dataset v1

Generated: 2026-06-02T16:46:52.650181+00:00
Total submissions: 26
Total riddles: 2600

## Purpose

First consolidated dataset for the framework team (T2.2.1).
Includes only submissions that passed all validator blocking checks.
Schema follows the Analysis team's canonical instance schema.

## Schema

Each line is one riddle as a JSON object. Fields:

| Field | Type | Description |
|---|---|---|
| `instance_result_id` | string (UUID v4) | Unique per row |
| `riddle_id` | string | Stable structured ID: `{community}_{topic}_{number}` |
| `created_at` | ISO 8601 | When this dataset was built |
| `source_row_number` | int | Original row number in contributor's spreadsheet |
| `language` | string (ISO 639-2/3) | Language code, per project metadata spec |
| `community` | string | Community token (e.g. `tamil_india`) |
| `topic` | string | Topic name as submitted |
| `is_wildcard` | bool | True if topic is community-specific, not one of the 8 standard topics |
| `riddle_original` | string | Riddle text in source language |
| `riddle_english` | string | English translation |
| `reference_answer_original` | string | Reference answer in source language |
| `reference_answer_english` | string | Reference answer in English |
| `riddle_hint` | string or null | Optional hint |
| `riddle_note` | string or null | Optional comment about region/generation specificity |
| `author_credit` | string or null | Submitter name |
| `human_validator_name` | string or null | Person who scored the human answer |
| `human_answer_original` | string or null | Human evaluator's answer attempt |
| `human_answer_score` | string or null | 0-2 rating (raw label from spreadsheet) |
| `human_answer_comment` | string or null | Comment on the human answer |
| `row_status` | string | `"valid"` for all rows in v1 |
| `raw_template_fields` | object | Original column names → values, for any field not in canonical schema. Dropped in v2. |

## Coverage

| Community | Riddles |
|---|---|
| `belarusian_belarus` | 100 |
| `bengali_bangladesh` | 100 |
| `bengali_india` | 100 |
| `bugisnese_indonesia` | 100 |
| `bulgarian_bulgaria` | 100 |
| `chinese_china` | 100 |
| `dutch_netherlands` | 100 |
| `egyptian_egypt` | 100 |
| `english_usa` | 100 |
| `french_france` | 100 |
| `german_germany` | 100 |
| `hungarian_hungary` | 100 |
| `indonesian_indonesia` | 100 |
| `italian_italy` | 100 |
| `malayalam_india` | 100 |
| `mongondow_mongondownese` | 100 |
| `moroccan_morocco` | 100 |
| `nepali_nepal` | 100 |
| `polish_poland` | 100 |
| `russian_russia` | 100 |
| `sudanese_sudan` | 100 |
| `syrian_syria` | 100 |
| `tamil_india` | 100 |
| `thai_thailand` | 100 |
| `urdu_pakistan` | 100 |
| `uzbek_uzbekistan` | 100 |

## Design decisions

- **Anti-corruption layer**: contributors write to the template schema;
  this script transforms once at the boundary to canonical schema. Single
  point of truth, no per-team conversion drift.
- **ISO 639-2/3 language codes**: matches Analysis team's instance schema.
  Arabic dialects use 639-3 codes (`arz`, `apd`, `apc`, `ary`); macro-language
  `ara` would lose dialect information critical to a cultural benchmark.
- **Verified language codes by source inspection**: Egyptian, Sudanese,
  Syrian, Moroccan, Cantonese, Mongondow language codes were confirmed by
  reading actual riddle content rather than guessing from filenames.
  (Sudanese was initially mismapped to Sundanese before verification.)
- **Script-family sanity check**: build runs a Unicode block check against
  the expected script family. Warnings printed but don't block the build.
- **`raw_template_fields` nested object**: preserves any column not in
  the canonical mapping (e.g. custom transliteration columns some
  contributors added). Allows v1 consumers to recover original data if
  needed. Dropped in v2 once mappings are validated.
- **Structured `riddle_id`**: stable across rebuilds, human-readable,
  sortable by community → topic → number.

## Open questions

1. **English + hints condition**: hints are written in source language
   only. Should hints be translated for the English condition, or
   fed mixed-language?
2. **`human_answer_score` field**: kept as raw string label (e.g.
   `"2: correct"`) for v1 because contributor files use inconsistent
   formats. Should be parsed to int 0/1/2 in v2.
3. **Scoring scale mismatch**: contributor template uses a 0-2 scale
   for `Rating of Human Answer`, while the project metadata schema
   and aggregate metrics use a 0-3 scale (0=hallucination, 1=honest
   uncertainty, 2=partial, 3=correct). Needs reconciliation before
   benchmarking starts.

## How to rebuild

```bash
cd data_loading
uv run python validate_submissions.py --no-download   # produce passed_jsonl/
uv run python build_pilot_dataset.py                  # consolidate
```

## Versioning

- **v1** (this version): includes `raw_template_fields` for forward
  compatibility. Analysis team consumes canonical fields; data preserved
  for review.
- **v2** (planned): drops `raw_template_fields` after Analysis confirms
  the mapping is complete. May parse `human_answer_score` to int and
  reconcile the 0-2 vs 0-3 scoring scale mismatch.