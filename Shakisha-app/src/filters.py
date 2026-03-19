from __future__ import annotations

import pandas as pd


def _normalize_str(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.lower()


def apply_study_filters(
    studies: pd.DataFrame,
    query: str = "",
    year_min: int | None = None,
    year_max: int | None = None,
    organization: str = "",
) -> pd.DataFrame:
    df = studies.copy()

    if query.strip():
        q = query.strip().lower()
        title_match = _normalize_str(df.get("title", pd.Series(index=df.index))).str.contains(q, regex=False)
        abstract_match = _normalize_str(df.get("abstract", pd.Series(index=df.index))).str.contains(q, regex=False)
        df = df[title_match | abstract_match]

    if year_min is not None or year_max is not None:
        years = pd.to_numeric(df.get("year"), errors="coerce")
        if year_min is not None:
            df = df[years >= year_min]
        if year_max is not None:
            df = df[years <= year_max]

    if organization.strip() and organization.lower() != "all":
        df = df[_normalize_str(df.get("organization", pd.Series(index=df.index))) == organization.strip().lower()]

    return df


def filter_resources_by_type(resources: pd.DataFrame, resource_type: str) -> pd.DataFrame:
    if not resource_type or resource_type.lower() == "all":
        return resources
    return resources[_normalize_str(resources.get("type", pd.Series(index=resources.index))) == resource_type.lower()]

