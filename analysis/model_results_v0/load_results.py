"""Load v0 model run results into one tidy DataFrame.

Walks a directory of run folders (downloaded from the shared Drive folder
RiddleBenchmarking/Responses_v0), extracts the model answer from each row's
raw_response, and produces one row per (riddle_id, model, condition).

Folder quirks are handled here, in code, so the Drive data never needs
hand-fixing:
- some runners prefixed filenames (13_tiny-aya-fire_results.jsonl); files
  are found by glob, not exact name
- manifest.json / run_metadata.json are optional; everything needed lives
  in results.jsonl rows and run_config.json
- two claude-opus-4-7 runs share a model_name and differ only by
  reasoning_mode, so model identity is (model_name, reasoning_mode)

Usage:
    python load_results.py [runs_dir] [out_path]
    defaults: data/responses_v0  ->  data/processed/results_tidy.parquet
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

# Folders excluded from analysis, with reasons. Keep data on disk untouched;
# exclusions are documented here so a fresh Drive download reproduces the
# same analysis set.
EXCLUDED_FOLDERS: dict[str, str] = {
    "28_param-1-2.9B": "removed from benchmarking (config says smoke_test)",
}

# Columns copied through from each results.jsonl row.
ROW_COLUMNS = [
    "riddle_id",
    "condition_id",
    "riddle_language_presented",
    "is_hint_provided",
    "instance_community",
    "instance_topic",
    "instance_language",
    "reference_answer_original",
    "reference_answer_english",
    "model_name",
    "model_id",
    "reasoning_mode",
    "generation_status",
    "raw_response",
]

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_ANSWER_RE = re.compile(r'"riddle_answer"\s*:\s*"((?:[^"\\]|\\.)*)"')


def extract_answer(raw_response: object) -> tuple[str | None, str]:
    """Extract the riddle_answer from a raw model response.

    Returns (answer, parse_status) where parse_status is one of
    'json', 'regex', 'empty', 'unparsed'.
    """
    if raw_response is None:
        return None, "empty"
    text = str(raw_response).strip()
    if not text:
        return None, "empty"
    cleaned = _FENCE_RE.sub("", text).strip()
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "riddle_answer" in obj:
            ans = obj["riddle_answer"]
            ans = None if ans is None else str(ans).strip()
            return (ans or None), "json"
    except (json.JSONDecodeError, ValueError):
        pass
    m = _ANSWER_RE.search(cleaned)
    if m:
        try:
            ans = json.loads(f'"{m.group(1)}"').strip()
        except (json.JSONDecodeError, ValueError):
            ans = m.group(1).strip()
        return (ans or None), "regex"
    return None, "unparsed"


def find_file(folder: Path, pattern: str) -> Path | None:
    matches = sorted(folder.glob(pattern))
    return matches[0] if matches else None


def load_run_folder(folder: Path) -> pd.DataFrame | None:
    """Load one run folder into a DataFrame, or None if unusable."""
    results_path = find_file(folder, "*results*.jsonl")
    if results_path is None:
        print(f"  SKIP {folder.name}: no results jsonl found")
        return None

    rows = []
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            row = {c: r.get(c) for c in ROW_COLUMNS}
            answer, parse_status = extract_answer(r.get("raw_response"))
            row["answer_text"] = answer
            row["answer_parse_status"] = parse_status
            rows.append(row)

    df = pd.DataFrame(rows)
    df["source_folder"] = folder.name
    df = df.drop(columns=["raw_response"])
    return df


def build_frame(runs_dir: Path) -> pd.DataFrame:
    frames = []
    for folder in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        if folder.name in EXCLUDED_FOLDERS:
            print(f"  EXCLUDE {folder.name}: {EXCLUDED_FOLDERS[folder.name]}")
            continue
        df = load_run_folder(folder)
        if df is not None:
            frames.append(df)
            print(f"  OK {folder.name}: {len(df)} rows")
    if not frames:
        raise SystemExit(f"No usable run folders under {runs_dir}")

    full = pd.concat(frames, ignore_index=True)

    # Model identity: (model_name, reasoning_mode). Display name appends the
    # reasoning mode only when needed to disambiguate.
    full["reasoning_mode"] = full["reasoning_mode"].fillna("none")
    key = full["model_name"] + " [" + full["reasoning_mode"] + "]"
    name_modes = full.groupby("model_name")["reasoning_mode"].nunique()
    ambiguous = set(name_modes[name_modes > 1].index)
    full["model_display"] = full["model_name"].where(
        ~full["model_name"].isin(ambiguous), key
    )

    # One run folder per model identity, else two runs would silently mix.
    folders_per_model = full.groupby(key)["source_folder"].nunique()
    dupes = folders_per_model[folders_per_model > 1]
    if not dupes.empty:
        detail = full[full["model_name"].isin(
            {k.split(" [")[0] for k in dupes.index}
        )].groupby(["model_name", "reasoning_mode"])["source_folder"].unique()
        raise SystemExit(
            "Model identity collision, same (model_name, reasoning_mode) in "
            f"multiple folders:\n{detail}"
        )

    return full


def main() -> None:
    runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/responses_v0")
    out_path = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("data/processed/results_tidy.parquet")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading runs from {runs_dir}")
    df = build_frame(runs_dir)

    print("\nSummary")
    print(f"  rows: {len(df)}")
    print(f"  models: {df['model_display'].nunique()}")
    print(f"  communities: {df['instance_community'].nunique()}")
    print(f"  conditions: {df['condition_id'].nunique()}")
    print("\nParse status counts:")
    print(df["answer_parse_status"].value_counts().to_string())
    print("\nRows per model:")
    print(df["model_display"].value_counts().to_string())

    try:
        df.to_parquet(out_path, index=False)
    except ImportError:
        out_path = out_path.with_suffix(".csv")
        df.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
