from __future__ import annotations

import json
from pathlib import Path

from .exceptions import DatasetValidationError
from .schemas import BenchmarkInstance


def load_benchmark_instances(jsonl_path: str | Path) -> list[BenchmarkInstance]:
    path = Path(jsonl_path)
    if not path.exists():
        raise DatasetValidationError(f"Dataset file not found: {path}")

    instances: list[BenchmarkInstance] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                inst = BenchmarkInstance.from_dict(data)
                inst.validate()
            except Exception as exc:
                raise DatasetValidationError(
                    f"Invalid dataset row at line {line_no}: {exc}"
                ) from exc

            if inst.riddle_id in seen_ids:
                raise DatasetValidationError(f"Duplicate riddle_id: {inst.riddle_id}")
            seen_ids.add(inst.riddle_id)
            instances.append(inst)

    instances.sort(
        key=lambda x: (
            x.community or "",
            x.topic or "",
            x.source_row_number if x.source_row_number is not None else 10**9,
            x.riddle_id,
        )
    )
    return instances
