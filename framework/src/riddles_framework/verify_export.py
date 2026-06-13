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
