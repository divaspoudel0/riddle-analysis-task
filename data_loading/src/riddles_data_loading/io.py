"""File discovery and workbook loading utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from riddles_data_loading.config import DEFAULT_REFERENCE_FILENAME, DEFAULT_SHEET_NAME


@dataclass(frozen=True)
class SheetLoadResult:
    """A loaded sheet plus metadata about how it was selected."""

    dataframe: pd.DataFrame
    sheet_name: str
    used_fallback: bool = False


def read_riddle_sheet(path: Path, *, sheet_name: str = DEFAULT_SHEET_NAME) -> pd.DataFrame:
    """Read a workbook's riddle sheet into a DataFrame."""

    return load_riddle_sheet(path, sheet_name=sheet_name).dataframe


def load_riddle_sheet(
    path: Path,
    *,
    sheet_name: str = DEFAULT_SHEET_NAME,
    fallback_to_first_sheet: bool = False,
) -> SheetLoadResult:
    """Read a workbook sheet and optionally fall back to its first worksheet."""

    try:
        return SheetLoadResult(
            dataframe=pd.read_excel(path, sheet_name=sheet_name),
            sheet_name=sheet_name,
        )
    except ValueError as exc:
        if not fallback_to_first_sheet or "Worksheet named" not in str(exc):
            raise

    workbook = pd.ExcelFile(path)
    first_sheet = workbook.sheet_names[0]
    return SheetLoadResult(
        dataframe=pd.read_excel(workbook, sheet_name=first_sheet),
        sheet_name=first_sheet,
        used_fallback=True,
    )


def discover_submission_workbooks(
    data_dir: Path,
    *,
    reference_filename: str = DEFAULT_REFERENCE_FILENAME,
) -> list[Path]:
    """Find submitted XLSX files, excluding the downloaded reference sheet."""

    files = []
    for path in data_dir.rglob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        if path.name == reference_filename:
            continue
        files.append(path)

    return sorted(files)
