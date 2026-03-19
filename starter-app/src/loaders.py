from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import pandas as pd


DEFAULT_DATA_DIR = Path("data/sample")

REQUIRED_STUDY_COLS = {"study_id", "title", "year", "url"}
REQUIRED_RESOURCE_COLS = {"study_id", "type", "url"}
REQUIRED_QUALITY_COLS = {"study_id", "quality_flags", "missing_field_count"}


def get_data_dir() -> Path:
    raw = os.getenv("HACKATHON_DATA_DIR", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_DATA_DIR


def _assert_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {', '.join(missing)}")


def load_all_data(data_dir: Path | None = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = data_dir or get_data_dir()
    studies = pd.read_csv(base / "studies.csv")
    resources = pd.read_csv(base / "study_resources.csv")
    quality = pd.read_csv(base / "quality_report.csv")

    _assert_columns(studies, REQUIRED_STUDY_COLS, "studies.csv")
    _assert_columns(resources, REQUIRED_RESOURCE_COLS, "study_resources.csv")
    _assert_columns(quality, REQUIRED_QUALITY_COLS, "quality_report.csv")
    return studies, resources, quality

