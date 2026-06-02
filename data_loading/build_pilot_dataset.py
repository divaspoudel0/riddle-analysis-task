"""Build the pilot dataset v1 for the framework team.

Consolidates all passing JSONL submissions into a single JSONL file
mapped to the Analysis team's canonical instance schema. Performs a
script-family sanity check to catch obvious language-code
mismatches at build time.

Usage:
    uv run python build_pilot_dataset.py

Inputs:
    reports/passed_jsonl/*.jsonl    (output of validate_submissions.py)

Outputs:
    pilot_dataset/pilot_dataset_v1.jsonl
    pilot_dataset/README.md
"""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pilot_dataset_config import (
    COMPOUND_COMMUNITIES,
    DEFAULT_SCRIPT_FAMILY,
    ISO_TO_SCRIPT_FAMILY,
    LANGUAGE_TO_ISO_639_2,
    SCHEMA_FIELD_ORDER,
    STANDARD_TOPICS,
    TEMPLATE_TO_CANONICAL,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
PASSED_JSONL_DIR = HERE / "reports" / "passed_jsonl"
OUTPUT_DIR = HERE / "pilot_dataset"
OUTPUT_FILE = OUTPUT_DIR / "pilot_dataset_v1.jsonl"
README_FILE = OUTPUT_DIR / "README.md"


# ---------------------------------------------------------------------------
# Unicode script detection (Option A)
# ---------------------------------------------------------------------------
def detect_script_family(text: str) -> str:
    """Return the dominant Unicode script family in a string.

    Looks at character ranges and counts which script appears most often.
    Returns one of: arabic, han, cyrillic, devanagari, bengali, tamil,
    telugu, kannada, malayalam, thai, latin, unknown.
    """
    if not text:
        return "unknown"

    counts: Counter[str] = Counter()
    for ch in text:
        cp = ord(ch)
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
            counts["arabic"] += 1
        elif 0x4E00 <= cp <= 0x9FFF:
            counts["han"] += 1
        elif 0x0400 <= cp <= 0x04FF:
            counts["cyrillic"] += 1
        elif 0x0900 <= cp <= 0x097F:
            counts["devanagari"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["bengali"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["tamil"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["telugu"] += 1
        elif 0x0C80 <= cp <= 0x0CFF:
            counts["kannada"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["malayalam"] += 1
        elif 0x0E00 <= cp <= 0x0E7F:
            counts["thai"] += 1
        elif 0x0041 <= cp <= 0x007A:
            counts["latin"] += 1

    if not counts:
        return "unknown"
    return counts.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    """Lowercase, replace non-alphanumeric runs with underscores."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", text)


def parse_community_from_filename(filename: str) -> str:
    """Extract community token from validator's JSONL filename.

    Files are named like:
        cultural_riddles_benchmark_tamil_india.jsonl
    Returns "tamil_india".
    """
    stem = Path(filename).stem
    return stem.replace("cultural_riddles_benchmark_", "")


def map_language(community: str) -> tuple[str, str | None]:
    """Map community token to (primary_iso, secondary_iso_or_None).

    Looks up COMPOUND_COMMUNITIES first for two-language communities,
    then falls back to matching the first token against
    LANGUAGE_TO_ISO_639_2.
    """
    community_lower = community.lower()

    # Compound community? (e.g. "luganda&lumasaba_uganda")
    for compound_key, (primary, secondary) in COMPOUND_COMMUNITIES.items():
        if community_lower.startswith(compound_key):
            primary_iso = LANGUAGE_TO_ISO_639_2[primary]
            secondary_iso = LANGUAGE_TO_ISO_639_2[secondary] if secondary else None
            return primary_iso, secondary_iso

    # Single-language: first token before underscore is the language
    first_token = community_lower.split("_")[0]
    primary_iso = LANGUAGE_TO_ISO_639_2.get(first_token)
    if primary_iso is None:
        raise ValueError(
            f"Unknown language token {first_token!r} in community "
            f"{community!r}. Add it to LANGUAGE_TO_ISO_639_2."
        )
    return primary_iso, None


def is_wildcard_topic(topic: str | None) -> bool:
    """A topic is a wildcard if it's not in the 8 standard topics."""
    if topic is None:
        return False
    return topic not in STANDARD_TOPICS


def build_riddle_id(community: str, topic: str | None, number: int | None) -> str:
    """Construct stable, sortable riddle ID.

    Format: {community_lower}_{topic_slug}_{number_padded_3}
    Example: tamil_india_history_007
    """
    community_part = community.lower()
    topic_part = slugify(topic) if topic else "unknown"
    number_part = f"{number:03d}" if number is not None else "000"
    return f"{community_part}_{topic_part}_{number_part}"


def transform_record(
    raw: dict,
    community: str,
    primary_iso: str,
    secondary_iso: str | None,
    created_at: str,
) -> dict:
    """Convert one raw JSONL record into a canonical-schema record."""
    # Pull renamed fields
    canonical: dict = {
        TEMPLATE_TO_CANONICAL[k]: v
        for k, v in raw.items()
        if k in TEMPLATE_TO_CANONICAL
    }

    # Preserve everything else (including extra columns like custom scripts)
    raw_template = {
        k: v for k, v in raw.items() if k not in TEMPLATE_TO_CANONICAL
    }

    # Build identifiers
    number = canonical.get("source_row_number")
    try:
        number_int = int(number) if number is not None else None
    except (TypeError, ValueError):
        # Some files use strings like "Tel 042" — strip non-digits
        digits = re.findall(r"\d+", str(number))
        number_int = int(digits[0]) if digits else None

    topic = canonical.get("topic")
    riddle_id = build_riddle_id(community, topic, number_int)

    # Assemble final record in canonical field order
    record = {
        "instance_result_id": str(uuid.uuid4()),
        "riddle_id": riddle_id,
        "created_at": created_at,
        "source_row_number": number_int,
        "language": primary_iso,
        "language_secondary": secondary_iso,
        "community": community,
        "topic": topic,
        "is_wildcard": is_wildcard_topic(topic),
        "riddle_original": canonical.get("riddle_original"),
        "riddle_english": canonical.get("riddle_english"),
        "reference_answer_original": canonical.get("reference_answer_original"),
        "reference_answer_english": canonical.get("reference_answer_english"),
        "riddle_hint": canonical.get("riddle_hint"),
        "riddle_note": canonical.get("riddle_note"),
        "author_credit": canonical.get("author_credit"),
        "human_validator_name": canonical.get("human_validator_name"),
        "human_answer_original": canonical.get("human_answer_original"),
        "human_answer_score": canonical.get("human_answer_score"),
        "human_answer_comment": canonical.get("human_answer_comment"),
        "row_status": "valid",
        "raw_template_fields": raw_template,
    }

    # Re-order according to SCHEMA_FIELD_ORDER (any unlisted fields go last)
    ordered = {k: record[k] for k in SCHEMA_FIELD_ORDER if k in record}
    for k, v in record.items():
        if k not in ordered:
            ordered[k] = v

    return ordered


def script_check(records: list[dict], community: str, primary_iso: str) -> str | None:
    """Sample riddle text and compare detected vs expected script family.

    Returns a warning string if mismatch detected, None if OK.
    """
    sample_text = " ".join(
        str(r.get("riddle_original", "")) for r in records[:20] if r.get("riddle_original")
    )
    if not sample_text.strip():
        return None

    detected = detect_script_family(sample_text)
    expected = ISO_TO_SCRIPT_FAMILY.get(primary_iso, DEFAULT_SCRIPT_FAMILY)

    if detected == expected:
        return None
    if detected == "unknown":
        return None  # short or unusual content; don't false-alarm

    return (
        f"    {community}: expected {expected!r} script for ISO {primary_iso!r}, "
        f"but riddles look like {detected!r}. Verify language code in config."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    if not PASSED_JSONL_DIR.exists():
        raise SystemExit(
            f"Passed JSONL directory not found: {PASSED_JSONL_DIR}\n"
            f"Run `uv run python validate_submissions.py` first."
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    all_records: list[dict] = []
    per_community_counts: dict[str, int] = {}
    warnings: list[str] = []

    jsonl_files = sorted(PASSED_JSONL_DIR.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} passing submissions.\n")

    for jsonl_path in jsonl_files:
        community = parse_community_from_filename(jsonl_path.name)
        try:
            primary_iso, secondary_iso = map_language(community)
        except ValueError as exc:
            warnings.append(f"   {community}: {exc}")
            continue

        # Read raw records
        raw_records = []
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    raw_records.append(json.loads(line))

        # Transform
        transformed = [
            transform_record(r, community, primary_iso, secondary_iso, created_at)
            for r in raw_records
        ]

        # Script-family sanity check
        warning = script_check(raw_records, community, primary_iso)
        if warning:
            warnings.append(warning)

        all_records.extend(transformed)
        per_community_counts[community] = len(transformed)
        secondary_part = f" + {secondary_iso}" if secondary_iso else ""
        print(
            f"  {community:<35} {primary_iso}{secondary_part:<8} "
            f"{len(transformed):>4} riddles"
        )

    # Write output
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Write README
    write_readme(per_community_counts, len(all_records), created_at)

    # Report
    print()
    print(f"Consolidated {len(per_community_counts)} submissions, "
          f"{len(all_records)} riddles.")
    print(f"   Output:  {OUTPUT_FILE.relative_to(HERE)}")
    print(f"   README:  {README_FILE.relative_to(HERE)}")

    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(w)
    else:
        print()
        print("No language-script mismatches detected.")


def write_readme(counts: dict[str, int], total: int, created_at: str) -> None:
    """Document the pilot dataset for downstream consumers."""
    lines = [
        "# Pilot Dataset v1",
        "",
        f"Generated: {created_at}",
        f"Total submissions: {len(counts)}",
        f"Total riddles: {total}",
        "",
        "## Purpose",
        "",
        "First consolidated dataset for the framework team (T2.2.1).",
        "Includes only submissions that passed all validator blocking checks.",
        "Schema follows the Analysis team's canonical instance schema.",
        "",
        "## Schema",
        "",
        "Each line is one riddle as a JSON object. Fields:",
        "",
        "| Field | Type | Description |",
        "|---|---|---|",
        "| `instance_result_id` | string (UUID v4) | Unique per row |",
        "| `riddle_id` | string | Stable structured ID: `{community}_{topic}_{number}` |",
        "| `created_at` | ISO 8601 | When this dataset was built |",
        "| `source_row_number` | int | Original row number in contributor's spreadsheet |",
        "| `language` | string (ISO 639-2/3) | Primary language code |",
        "| `language_secondary` | string or null | For two-language communities (e.g. Luganda&Lumasaba) |",
        "| `community` | string | Community token (e.g. `tamil_india`) |",
        "| `topic` | string | Topic name as submitted |",
        "| `is_wildcard` | bool | True if topic is community-specific, not one of the 8 standard topics |",
        "| `riddle_original` | string | Riddle text in source language |",
        "| `riddle_english` | string | English translation |",
        "| `reference_answer_original` | string | Reference answer in source language |",
        "| `reference_answer_english` | string | Reference answer in English |",
        "| `riddle_hint` | string or null | Optional hint |",
        "| `riddle_note` | string or null | Optional comment about region/generation specificity |",
        "| `author_credit` | string or null | Submitter name |",
        "| `human_validator_name` | string or null | Person who scored the human answer |",
        "| `human_answer_original` | string or null | Human evaluator's answer attempt |",
        "| `human_answer_score` | string or null | 0-2 rating (raw label from spreadsheet) |",
        "| `human_answer_comment` | string or null | Comment on the human answer |",
        "| `row_status` | string | `\"valid\"` for all rows in v1 |",
        "| `raw_template_fields` | object | Original column names → values, for any field not in canonical schema. Dropped in v2. |",
        "",
        "## Coverage",
        "",
        "| Community | Riddles |",
        "|---|---|",
    ]
    for community, count in sorted(counts.items()):
        lines.append(f"| `{community}` | {count} |")

    lines += [
        "",
        "## Design decisions",
        "",
        "- **Anti-corruption layer**: contributors write to the template schema;",
        "  this script transforms once at the boundary to canonical schema. Single",
        "  point of truth, no per-team conversion drift.",
        "- **ISO 639-2/3 language codes**: matches Analysis team's instance schema.",
        "  Arabic dialects use 639-3 codes (`arz`, `apd`, `apc`, `ary`); macro-language",
        "  `ara` would lose dialect information critical to a cultural benchmark.",
        "- **Verified language codes by source inspection**: Egyptian, Sudanese,",
        "  Syrian, Moroccan, Cantonese, Mongondow language codes were confirmed by",
        "  reading actual riddle content rather than guessing from filenames.",
        "  (Sudanese was initially mismapped to Sundanese before verification.)",
        "- **Script-family sanity check**: build runs a Unicode block check against",
        "  the expected script family. Warnings printed but don't block the build.",
        "- **`raw_template_fields` nested object**: preserves any column not in",
        "  the canonical mapping (e.g. custom transliteration columns some",
        "  contributors added). Allows v1 consumers to recover original data if",
        "  needed. Dropped in v2 once mappings are validated.",
        "- **Structured `riddle_id`**: stable across rebuilds, human-readable,",
        "  sortable by community → topic → number.",
        "",
        "## Open questions",
        "",
        "1. **English + hints condition**: hints are written in source language",
        "   only. Should hints be translated for the English condition, or",
        "   fed mixed-language?",
        "2. **`human_answer_score` field**: kept as raw string label (e.g.",
        "   `\"2: correct\"`) for v1 because contributor files use inconsistent",
        "   formats. Should be parsed to int 0/1/2 in v2.",
        "3. **Compound communities**: `Luganda&Lumasaba_Uganda` extends the",
        "   canonical schema with `language_secondary`. Confirm this is the",
        "   right representation with Analysis team.",
        "",
        "## How to rebuild",
        "",
        "```bash",
        "cd data_loading",
        "uv run python validate_submissions.py --no-download   # produce passed_jsonl/",
        "uv run python build_pilot_dataset.py                  # consolidate",
        "```",
        "",
        "## Versioning",
        "",
        "- **v1** (this version): includes `raw_template_fields` for forward",
        "  compatibility. Analysis team consumes canonical fields; data preserved",
        "  for review.",
        "- **v2** (planned): drops `raw_template_fields` after Analysis confirms",
        "  the mapping is complete. May parse `human_answer_score` to int. May",
        "  fold compound-language representation differently.",
    ]

    README_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()