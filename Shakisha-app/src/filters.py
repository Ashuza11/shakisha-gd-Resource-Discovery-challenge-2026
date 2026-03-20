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
    district: str = "",
) -> pd.DataFrame:
    df = studies.copy()

    if query.strip():
        # Split into individual tokens so "women employment Rwanda" matches
        # studies containing any of those words, not the exact phrase
        STOP = {"and", "or", "the", "in", "of", "for", "to", "a", "an", "on", "at", "by"}
        tokens = [t for t in query.strip().lower().split() if t not in STOP and len(t) > 1]
        if not tokens:
            tokens = query.strip().lower().split()

        title_col      = _normalize_str(df.get("title",              pd.Series(index=df.index)))
        abstract_col   = _normalize_str(df.get("abstract",           pd.Series(index=df.index)))
        geo_col        = _normalize_str(df.get("geographic_coverage", pd.Series(index=df.index)))
        geo_unit_col   = _normalize_str(df.get("geographic_unit",     pd.Series(index=df.index)))

        mask = pd.Series(False, index=df.index)
        for token in tokens:
            mask |= (
                title_col.str.contains(token, regex=False)
                | abstract_col.str.contains(token, regex=False)
                | geo_col.str.contains(token, regex=False)
                | geo_unit_col.str.contains(token, regex=False)
            )
        df = df[mask]

    if district.strip() and district.lower() not in ("all", ""):
        if district == "__district_level__":
            # Special flag: keep only studies that offer district-level disaggregation
            geo_text = (
                _normalize_str(df.get("geographic_coverage", pd.Series(index=df.index)))
                + " "
                + _normalize_str(df.get("geographic_unit", pd.Series(index=df.index)))
                + " "
                + _normalize_str(df.get("abstract", pd.Series(index=df.index)))
            )
            df = df[geo_text.str.contains("district", regex=False)]
        else:
            d = district.strip().lower()
            title_match = _normalize_str(df.get("title", pd.Series(index=df.index))).str.contains(d, regex=False)
            abstract_match = _normalize_str(df.get("abstract", pd.Series(index=df.index))).str.contains(d, regex=False)
            geo_match = _normalize_str(df.get("geographic_coverage", pd.Series(index=df.index))).str.contains(d, regex=False)
            geo_unit_match = _normalize_str(df.get("geographic_unit", pd.Series(index=df.index))).str.contains(d, regex=False)
            df = df[title_match | abstract_match | geo_match | geo_unit_match]

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

