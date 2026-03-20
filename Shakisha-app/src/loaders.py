from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import pandas as pd


_FULL_DATA_DIR = Path("data/full")
_SAMPLE_DATA_DIR = Path("data/sample")
DEFAULT_DATA_DIR = _FULL_DATA_DIR if _FULL_DATA_DIR.exists() else _SAMPLE_DATA_DIR

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


def compute_domain_study_counts(studies: pd.DataFrame) -> dict[str, int]:
    """Return actual study counts per domain key, computed from the loaded catalog."""
    # Import here to avoid circular dependency at module level
    from src.domains import DOMAINS, get_domain_keywords

    counts: dict[str, int] = {}
    titles = studies["title"].fillna("").astype(str).str.lower().tolist()
    abstracts = studies.get("abstract", pd.Series([""] * len(studies))).fillna("").astype(str).str.lower().tolist()
    for domain_key in DOMAINS:
        keywords = get_domain_keywords(domain_key)
        if not keywords:
            counts[domain_key] = len(studies)
            continue
        n = sum(
            any(k in t for k in keywords) or any(k in a for k in keywords)
            for t, a in zip(titles, abstracts)
        )
        counts[domain_key] = n
    return counts


def get_catalog_mtime() -> str:
    """Return last-modified timestamp of the studies.csv file as a human-readable string."""
    import time
    base = get_data_dir()
    csv_path = base / "studies.csv"
    try:
        mtime = csv_path.stat().st_mtime
        return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(mtime))
    except OSError:
        return "unknown"

