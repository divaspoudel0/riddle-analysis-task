from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

EXPECTED_LANGUAGES = {"arz", "zho", "tam", "rus", "eng"}
EXPECTED_ROWS = 25

REQUIRED_FIELDS = [
    "instance_id", "run_id", "riddle_id", "condition_id",
    "model_name", "model_id", "model_provider", "provider_model_name",
    "access_pattern", "prompt_template_id", "prompt_template_version",
    "prompt_language", "riddle_language_presented", "instance_language",
    "generation_status",
]
VALID_STATUSES = {"success", "empty", "refusal", "error"}
OUTPUT_FILES = ("results.jsonl", "run_config.json", "run_metadata.json", "manifest.json")


@dataclass
class Entry:
    label: str
    category: str  # dummy | local | api | aggregator
    config: str    # path relative to framework/


MATRIX = [
    Entry("dummy", "dummy", "configs/campaign/dummy_smoke25.yaml"),
    Entry("local-hf", "local", "configs/local_cpu_smoke.yaml"),
    Entry("cohere-api", "api", "configs/campaign/cohere_smoke25.yaml"),
    Entry("together-aggregator", "aggregator", "configs/campaign/together_smoke25.yaml"),
]


def should_skip(entry: Entry) -> str | None:
    """Return a skip reason if the entry's API key env var is required but unset."""
    cfg = yaml.safe_load(Path(entry.config).read_text(encoding="utf-8"))
    env_var = cfg.get("api_key_env_var")
    if env_var and not os.environ.get(env_var):
        return f"{env_var} not set"
    return None


@dataclass
class RunOutcome:
    returncode: int
    run_dir: Path | None
    stderr_tail: str


def run_entry(entry: Entry, output_root: str) -> RunOutcome:
    """Invoke the real CLI as a subprocess and locate the produced run directory."""
    proc = subprocess.run(
        [sys.executable, "-m", "riddles_framework.cli",
         "--config", entry.config, "--output-root", output_root],
        capture_output=True, text=True,
    )
    run_dir: Path | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("Run complete:"):
            run_id = line.split("Run complete:", 1)[1].strip()
            run_dir = Path(output_root) / run_id
    stderr_tail = "\n".join(proc.stderr.strip().splitlines()[-15:])
    return RunOutcome(returncode=proc.returncode, run_dir=run_dir, stderr_tail=stderr_tail)


@dataclass
class ValidationResult:
    ok: bool
    rows: int
    statuses: dict
    languages: list
    tokens_populated: bool
    problems: list = field(default_factory=list)


def validate_run(run_dir: Path) -> ValidationResult:
    problems: list[str] = []

    for fname in OUTPUT_FILES:
        if not (run_dir / fname).exists():
            problems.append(f"missing output file: {fname}")

    results_path = run_dir / "results.jsonl"
    rows: list[dict] = []
    if results_path.exists():
        rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    if len(rows) != EXPECTED_ROWS:
        problems.append(f"row count {len(rows)} != expected {EXPECTED_ROWS}")

    languages = sorted({r.get("instance_language") for r in rows if r.get("instance_language")})
    if set(languages) != EXPECTED_LANGUAGES:
        problems.append(f"language coverage {languages} != {sorted(EXPECTED_LANGUAGES)}")

    statuses = Counter(r.get("generation_status") for r in rows)
    tokens_populated = False

    for i, r in enumerate(rows):
        for fld in REQUIRED_FIELDS:
            if r.get(fld) in (None, ""):
                problems.append(f"row {i}: missing/empty required field '{fld}'")
        status = r.get("generation_status")
        if status not in VALID_STATUSES:
            problems.append(f"row {i}: invalid generation_status {status!r}")
        if status == "success":
            resp = r.get("raw_response")
            if not isinstance(resp, str) or not resp.strip():
                problems.append(f"row {i}: success row has empty raw_response")
        for tok in ("input_tokens", "output_tokens"):
            val = r.get(tok)
            if val is not None:
                tokens_populated = True
                if not isinstance(val, int):
                    problems.append(f"row {i}: {tok} is {type(val).__name__}, expected int or null")

    if len(problems) > 25:
        extra = len(problems) - 25
        problems = problems[:25] + [f"... and {extra} more problems"]

    return ValidationResult(
        ok=not problems,
        rows=len(rows),
        statuses=dict(statuses),
        languages=languages,
        tokens_populated=tokens_populated,
        problems=problems,
    )
