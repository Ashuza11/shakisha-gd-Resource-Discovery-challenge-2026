"""
Shakisha FastAPI backend.
Thin wrapper over the existing src/ Python modules — no logic lives here.
Run from the Shakisha-app/ directory:
    uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ is importable when running from Shakisha-app/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from src.ai import advocacy_brief, explain_study, interpret_query
from src.domains import DOMAINS, get_active_domains
from src.filters import apply_study_filters, filter_resources_by_type
from src.link_checker import check_url
from src.loaders import compute_domain_study_counts, get_catalog_mtime, get_data_dir, load_all_data
from src.quality_badges import parse_quality_flags, quality_level

app = FastAPI(title="Shakisha API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data once at startup ──────────────────────────────────────────────────
try:
    _studies, _resources, _quality = load_all_data()
    _domain_counts = compute_domain_study_counts(_studies)
    _data_ok = True
except Exception as e:
    print(f"WARNING: Could not load data: {e}")
    _data_ok = False


def _require_data():
    if not _data_ok:
        raise HTTPException(status_code=503, detail="Data not loaded. Check data/ directory.")


# ── Request / Response models ──────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = ""
    domain: str = "labour"
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    organization: str = ""
    district: str = ""
    resource_type: str = "all"
    quality_filter: str = "all"
    sort_order: str = "Newest first"
    use_ai: bool = True


class BriefRequest(BaseModel):
    study_id: str


class LinkCheckRequest(BaseModel):
    study_ids: list[str]


class ExplainRequest(BaseModel):
    study_id: str
    query: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _quality_order(level: str) -> int:
    return {"good": 0, "warning": 1, "critical": 2}.get(level, 1)


def _normalize_title(title: str) -> str:
    """Convert ALL-CAPS titles to Title Case; leave normally-cased titles unchanged."""
    if not title:
        return title
    letters = [c for c in title if c.isalpha()]
    if not letters:
        return title
    if sum(1 for c in letters if c.isupper()) / len(letters) > 0.70:
        LOWER_WORDS = {"a", "an", "the", "and", "but", "or", "nor", "for",
                       "in", "on", "at", "to", "of", "up", "by", "with"}
        words = title.lower().split()
        result = []
        for i, word in enumerate(words):
            result.append(word if (i > 0 and word in LOWER_WORDS) else word.capitalize())
        return " ".join(result)
    return title


def _is_nisr(row: dict) -> bool:
    """True for NISR base and NISR crawler studies; False for OpenAlex and other pipeline sources.
    Uses study_id prefix as the primary signal — 'oa_' prefix = OpenAlex."""
    study_id = str(row.get("study_id", "") or "")
    if study_id.startswith("oa_"):
        return False
    adapter = str(row.get("source_adapter", "") or "").strip()
    if adapter in ("openalex", "worldbank", "ilo"):
        return False
    return True


def _relevance_score(title: str, abstract: str, tokens: list) -> float:
    """Count keyword hits: title matches count 3×, abstract matches count 1×."""
    if not tokens:
        return 0.0
    t = title.lower()
    a = abstract.lower()
    return float(
        sum(3 for tok in tokens if tok in t) +
        sum(1 for tok in tokens if tok in a)
    )


def _serialise_study(row: dict, resources_df=None) -> dict:
    """Convert a study row + quality info into a JSON-safe dict."""
    import pandas as pd

    study_id = str(row.get("study_id", ""))

    # Quality
    q_row = _quality[_quality["study_id"].astype(str) == study_id]
    missing = int(q_row.iloc[0]["missing_field_count"]) if not q_row.empty else 0
    flags_raw = str(q_row.iloc[0].get("quality_flags", "")) if not q_row.empty else ""
    level = quality_level(missing)
    flags = parse_quality_flags(flags_raw)

    # Resources
    res_df = resources_df if resources_df is not None else _resources
    study_resources = res_df[res_df["study_id"].astype(str) == study_id].to_dict("records")
    resource_count = len(study_resources)

    def clean(val):
        s = str(val or "").strip()
        return "" if s in ("nan", "None") else s

    nisr = _is_nisr(row)

    return {
        "study_id": study_id,
        "title": _normalize_title(clean(row.get("title", ""))),
        "is_nisr": nisr,
        "year": clean(row.get("year", "")),
        "organization": clean(row.get("organization", "")),
        "abstract": clean(row.get("abstract", "")),
        "url": clean(row.get("url", "")),
        "get_microdata_url": clean(row.get("get_microdata_url", "")),
        "geographic_coverage": clean(row.get("geographic_coverage", "")),
        "geographic_unit": clean(row.get("geographic_unit", "")),
        "quality_level": level,
        "quality_flags": flags,
        "missing_field_count": missing,
        "resource_count": resource_count,
        "resources": [
            {
                "type": clean(r.get("type", "")),
                "url": clean(r.get("url", "")),
                "title": clean(r.get("title", "")),
            }
            for r in study_resources
        ],
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "data_loaded": _data_ok, "catalog": str(get_data_dir())}


@app.get("/api/domains")
def domains():
    result = {}
    for key, cfg in DOMAINS.items():
        result[key] = {
            "name": cfg["name"],
            "emoji": cfg["emoji"],
            "description": cfg["description"],
            "status": cfg["status"],
            "advocacy_context": cfg["advocacy_context"],
            "study_count": _domain_counts.get(key, cfg["study_count_hint"]) if _data_ok else cfg["study_count_hint"],
        }
    return result


@app.get("/api/stats")
def stats():
    _require_data()
    active_domains = sum(1 for d in DOMAINS.values() if d["status"] == "active")
    ai_available = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return {
        "study_count": len(_studies),
        "resource_count": len(_resources),
        "active_domains": active_domains,
        "ai_available": ai_available,
        "catalog_updated": get_catalog_mtime(),
    }


@app.post("/api/search")
def search(req: SearchRequest):
    _require_data()
    import pandas as pd
    from src.domains import filter_by_domain

    # Domain pre-filter
    domain_mask = filter_by_domain(
        _studies["title"].tolist(),
        req.domain,
        abstracts=_studies.get("abstract", _studies["title"]).fillna("").tolist(),
    )
    domain_studies = _studies[domain_mask].copy()
    total_in_domain = len(domain_studies)

    # AI query interpretation
    effective_query = req.query
    effective_year_min = req.year_min
    effective_year_max = req.year_max
    ai_explanation = ""

    if req.query.strip() and req.use_ai and os.getenv("ANTHROPIC_API_KEY", "").strip():
        try:
            ai_params = interpret_query(req.query)
            if ai_params.get("keywords"):
                effective_query = " ".join(ai_params["keywords"])
            effective_year_min = ai_params.get("year_min") or req.year_min
            effective_year_max = ai_params.get("year_max") or req.year_max
            ai_explanation = ai_params.get("explanation", "")
        except Exception:
            pass

    # Apply filters
    district_param = (
        "__district_level__" if req.district == "Has district-level data"
        else "" if req.district in ("All Rwanda", "") else req.district
    )

    filtered = apply_study_filters(
        domain_studies,
        query=effective_query,
        year_min=effective_year_min,
        year_max=effective_year_max,
        organization="" if req.organization in ("All", "") else req.organization,
        district=district_param,
    )

    res_filtered = filter_resources_by_type(_resources, req.resource_type)

    # Merge quality
    quality_map = _quality[["study_id", "missing_field_count"]].copy()
    quality_map["study_id"] = quality_map["study_id"].astype(str)
    filtered = filtered.copy()
    filtered["study_id"] = filtered["study_id"].astype(str)
    merged = filtered.merge(quality_map, on="study_id", how="left")
    merged["missing_field_count"] = merged["missing_field_count"].fillna(0).astype(int)
    merged["q_level"] = merged["missing_field_count"].apply(quality_level)

    # Quality filter
    if req.quality_filter != "all":
        merged = merged[merged["q_level"] == req.quality_filter]

    # ── Ranking ───────────────────────────────────────────────────────────────
    STOP = {"and", "or", "the", "in", "of", "for", "to", "a", "an", "on", "at", "by"}
    search_tokens = [
        t for t in (effective_query or "").lower().split()
        if t not in STOP and len(t) > 2
    ]

    if search_tokens:
        # Composite ranking: relevance + NISR priority + quality
        merged["_rel"] = merged.apply(
            lambda r: _relevance_score(
                str(r.get("title", "")), str(r.get("abstract", "")), search_tokens
            ), axis=1
        )
        merged["_nisr"] = merged.apply(
            lambda r: 3 if _is_nisr(r.to_dict()) else 0, axis=1
        )
        merged["_qual"] = merged["q_level"].map(
            lambda l: {"good": 2, "warning": 1, "critical": 0}.get(l, 1)
        )
        merged["_score"] = merged["_rel"] + merged["_nisr"] + merged["_qual"]
        merged = (
            merged.sort_values(["_score", "_nisr"], ascending=[False, False])
            .drop(columns=["_rel", "_nisr", "_qual", "_score"])
        )
    else:
        # No query: NISR sources first, then apply the chosen sort
        merged["_nisr"] = merged.apply(
            lambda r: 0 if _is_nisr(r.to_dict()) else 1, axis=1
        )
        if req.sort_order == "Newest first":
            year_col = pd.to_numeric(merged["year"], errors="coerce").fillna(0)
            merged["_year"] = year_col
            merged = merged.sort_values(["_nisr", "_year"], ascending=[True, False]).drop(columns=["_nisr", "_year"])
        elif req.sort_order == "Oldest first":
            year_col = pd.to_numeric(merged["year"], errors="coerce").fillna(9999)
            merged["_year"] = year_col
            merged = merged.sort_values(["_nisr", "_year"], ascending=[True, True]).drop(columns=["_nisr", "_year"])
        elif req.sort_order == "By quality":
            merged["_qs"] = merged["q_level"].map(_quality_order)
            merged = merged.sort_values(["_nisr", "_qs"]).drop(columns=["_nisr", "_qs"])
        else:
            merged = merged.sort_values(["_nisr"], ascending=True).drop(columns=["_nisr"])

    studies_out = [_serialise_study(row, res_filtered) for _, row in merged.iterrows()]

    return {
        "results": studies_out,
        "total": len(studies_out),
        "total_in_domain": total_in_domain,
        "ai_explanation": ai_explanation,
    }


@app.get("/api/studies/{study_id}")
def get_study(study_id: str):
    _require_data()
    row = _studies[_studies["study_id"].astype(str) == study_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Study not found")
    return _serialise_study(row.iloc[0].to_dict())


@app.get("/api/quality")
def quality_report(domain: str = "all"):
    _require_data()
    from src.domains import filter_by_domain

    # Build domain-filtered set of study IDs
    if domain != "all":
        titles    = _studies["title"].tolist()
        abstracts = _studies.get("abstract", _studies["title"]).fillna("").tolist()
        mask      = filter_by_domain(titles, domain, abstracts=abstracts)
        allowed   = set(_studies[mask]["study_id"].astype(str).tolist())
    else:
        allowed = None  # no restriction

    out = []
    for _, row in _quality.iterrows():
        study_id = str(row.get("study_id", ""))
        if allowed is not None and study_id not in allowed:
            continue
        missing   = int(row.get("missing_field_count", 0) or 0)
        flags_raw = str(row.get("quality_flags", "") or "")
        study_row = _studies[_studies["study_id"].astype(str) == study_id]
        title     = str(study_row.iloc[0]["title"]) if not study_row.empty else study_id
        out.append({
            "study_id":           study_id,
            "title":              title,
            "missing_field_count": missing,
            "quality_level":      quality_level(missing),
            "quality_flags":      parse_quality_flags(flags_raw),
        })
    return {"items": out, "catalog_updated": get_catalog_mtime()}


@app.post("/api/brief")
def generate_brief(req: BriefRequest):
    _require_data()
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI brief generation requires an Anthropic API key. "
                "Add ANTHROPIC_API_KEY to your .env file or environment to enable this feature. "
                "All discovery, quality, and analytics features work without a key."
            ),
        )

    row = _studies[_studies["study_id"].astype(str) == req.study_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Study not found")

    study_row = row.iloc[0].to_dict()
    resources = _resources[_resources["study_id"].astype(str) == req.study_id].to_dict("records")

    # Attach quality info
    q_row = _quality[_quality["study_id"].astype(str) == req.study_id]
    if not q_row.empty:
        study_row["missing_field_count"] = int(q_row.iloc[0]["missing_field_count"] or 0)
        study_row["quality_flags"] = str(q_row.iloc[0].get("quality_flags", "") or "")

    try:
        brief = advocacy_brief(study_row, resources)
        return {"brief": brief, "study": _serialise_study(study_row)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain")
def explain(req: ExplainRequest):
    _require_data()
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail=(
                "AI explanations require an Anthropic API key. "
                "Add ANTHROPIC_API_KEY to your .env file or environment to enable this feature."
            ),
        )

    row = _studies[_studies["study_id"].astype(str) == req.study_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Study not found")

    try:
        explanation = explain_study(row.iloc[0].to_dict(), req.query)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/link-check")
def link_check(req: LinkCheckRequest):
    _require_data()
    results = []
    study_rows = _studies[_studies["study_id"].astype(str).isin(req.study_ids)]
    for _, row in study_rows.iterrows():
        url = str(row.get("url", "") or "").strip()
        if url and url not in ("nan", "None"):
            status, code = check_url(url)
        else:
            status, code = "invalid", None
        results.append({
            "study_id": str(row["study_id"]),
            "title": str(row.get("title", "")),
            "url": url,
            "status": status,
            "http_code": code,
        })
    return {"results": results}


@app.get("/api/organizations")
def organizations():
    _require_data()
    orgs = sorted(
        _studies["organization"].fillna("Unknown").astype(str).str.strip().unique().tolist()
    )
    return {"organizations": orgs}


@app.get("/api/resource-types")
def resource_types():
    _require_data()
    types = sorted(
        t for t in _resources["type"].fillna("").astype(str).str.strip().unique().tolist()
        if t and t.lower() not in ("", "nan")
    )
    return {"resource_types": types}


_RWANDA_DISTRICTS = [
    "All Rwanda", "Has district-level data",
    "Gasabo", "Kicukiro", "Nyarugenge",
    "Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana",
    "Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo",
    "Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango",
    "Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rutsiro", "Rusizi",
]


@app.get("/api/districts")
def districts():
    return {"districts": _RWANDA_DISTRICTS}


# ── Geographic coverage analysis ───────────────────────────────────────────────

_PROVINCE_KEYWORDS: dict[str, list[str]] = {
    "northern": ["northern province", "northern", "nord", "musanze", "burera", "gakenke", "gicumbi", "rulindo"],
    "eastern":  ["eastern province",  "eastern",  "est",  "nyagatare", "gatsibo", "kayonza", "kirehe", "ngoma", "rwamagana", "bugesera"],
    "southern": ["southern province", "southern", "sud",  "huye", "gisagara", "nyaruguru", "nyamagabe", "muhanga", "ruhango", "kamonyi"],
    "western":  ["western province",  "western",  "ouest","rubavu", "nyabihu", "rutsiro", "karongi", "rusizi", "ngororero", "nyamasheke", "gisenyi"],
    "kigali":   ["kigali"],
}

_PROVINCE_NAMES = {
    "northern": "Northern Province",
    "eastern":  "Eastern Province",
    "southern": "Southern Province",
    "western":  "Western Province",
    "kigali":   "Kigali City",
}

_DISTRICT_TO_PROVINCE: dict[str, str] = {
    "musanze": "northern", "burera": "northern", "gakenke": "northern", "gicumbi": "northern", "rulindo": "northern",
    "nyagatare": "eastern", "gatsibo": "eastern", "kayonza": "eastern", "kirehe": "eastern",
    "ngoma": "eastern", "rwamagana": "eastern", "bugesera": "eastern",
    "huye": "southern", "gisagara": "southern", "nyaruguru": "southern", "nyamagabe": "southern",
    "muhanga": "southern", "ruhango": "southern", "kamonyi": "southern", "nyanza": "southern",
    "rubavu": "western", "nyabihu": "western", "rutsiro": "western", "karongi": "western",
    "rusizi": "western", "ngororero": "western", "nyamasheke": "western",
    "gasabo": "kigali", "kicukiro": "kigali", "nyarugenge": "kigali",
}


@app.get("/api/geographic")
def geographic():
    """Geographic coverage analysis — province-specific vs. national studies."""
    _require_data()
    from src.domains import filter_by_domain, DOMAINS as _DOMAINS

    # Domain masks (index-aligned with _studies)
    studies_list = _studies.reset_index(drop=True)
    titles    = studies_list["title"].tolist()
    abstracts = studies_list.get("abstract", studies_list["title"]).fillna("").tolist()
    domain_masks: dict[str, list[bool]] = {
        dk: filter_by_domain(titles, dk, abstracts=abstracts)
        for dk in _DOMAINS
    }

    specific_count:  dict[str, int] = {k: 0 for k in _PROVINCE_KEYWORDS}
    national_count   = 0
    province_domains: dict[str, dict[str, int]] = {k: {} for k in _PROVINCE_KEYWORDS}
    national_domains: dict[str, int] = {}
    district_counts:  dict[str, int] = {}

    geo_resolution = {"sub_district": 0, "district": 0, "province": 0, "national": 0, "unspecified": 0}

    for i, row in studies_list.iterrows():
        geo_cov  = str(row.get("geographic_coverage", "") or "").lower()
        geo_unit = str(row.get("geographic_unit", "") or "").lower()
        combined = geo_cov + " " + geo_unit

        # Geographic resolution
        if any(w in combined for w in ["cell level", "sector level", "village level", "au niveau de la cellule"]):
            geo_resolution["sub_district"] += 1
        elif any(w in combined for w in ["district level", "district-level", "disaggregated up to the district", "district level as well"]):
            geo_resolution["district"] += 1
        elif any(w in combined for w in ["province", "provincial", "regional level"]):
            geo_resolution["province"] += 1
        elif any(w in combined for w in ["national", "nationwide", "nation-wide", "tout le pays", "whole country", "couverture national"]):
            geo_resolution["national"] += 1
        else:
            geo_resolution["unspecified"] += 1

        # Province assignment
        matched: set[str] = set()
        for prov, keywords in _PROVINCE_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                matched.add(prov)

        # District counts
        for dist in _DISTRICT_TO_PROVINCE:
            if dist in combined:
                district_counts[dist] = district_counts.get(dist, 0) + 1

        if matched:
            for prov in matched:
                specific_count[prov] += 1
                for dk, mask in domain_masks.items():
                    if mask[i]:
                        province_domains[prov][dk] = province_domains[prov].get(dk, 0) + 1
        else:
            national_count += 1
            for dk, mask in domain_masks.items():
                if mask[i]:
                    national_domains[dk] = national_domains.get(dk, 0) + 1

    # Build output
    provinces_out = []
    for prov_key in _PROVINCE_KEYWORDS:
        provinces_out.append({
            "key":            prov_key,
            "name":           _PROVINCE_NAMES[prov_key],
            "specific_count": specific_count[prov_key],
            "total_count":    specific_count[prov_key] + national_count,
            "domain_counts":  province_domains[prov_key],
        })

    districts_out = [
        {"name": d.capitalize(), "province": p, "study_count": district_counts.get(d, 0)}
        for d, p in _DISTRICT_TO_PROVINCE.items()
    ]

    return {
        "provinces":       provinces_out,
        "districts":       districts_out,
        "national_count":  national_count,
        "national_domains": national_domains,
        "total_studies":   len(_studies),
        "geo_resolution":  geo_resolution,
    }


# ── Pipeline status ────────────────────────────────────────────────────────────

_APP_ROOT = Path(__file__).resolve().parent.parent
_FULL_DIR = _APP_ROOT / "data" / "full"
_PIPELINE_SOURCES_DIR = _APP_ROOT / "data" / "pipeline_sources"

_PIPELINE_SOURCES = [
    {
        "key":         "nisr_base",
        "name":        "NISR Microdata Catalog",
        "badge":       "Authoritative base",
        "badge_type":  "active",
        "description": (
            "Rwanda's national statistical microdata catalog from NISR. "
            "Covers Labour, Agriculture, Household, Health, Population, and Finance surveys. "
            "This is the authoritative seed — all other sources extend it."
        ),
        "adapter":     None,
        "run_cmd":     None,
        "dir":         None,
    },
    {
        "key":         "nisr_crawl",
        "name":        "NISR Crawler (incremental)",
        "badge":       "Incremental crawler",
        "badge_type":  "crawler",
        "description": (
            "Crawls the live NISR catalog for new gender-relevant studies added since the "
            "last run. Skips any study already in the base catalog."
        ),
        "adapter":     "data_pipeline/nisr_crawler.py",
        "run_cmd":     "python data_pipeline/nisr_crawler.py",
        "dir":         "nisr_crawl",
    },
    {
        "key":         "openalex",
        "name":        "OpenAlex Research Papers",
        "badge":       "Academic papers",
        "badge_type":  "academic",
        "description": (
            "Open-access academic papers on Rwanda gender, labour, agriculture, and land rights "
            "from OpenAlex (no API key required)."
        ),
        "adapter":     "data_pipeline/openalex_adapter.py",
        "run_cmd":     "python data_pipeline/openalex_adapter.py",
        "dir":         "openalex",
    },
    {
        "key":         "worldbank",
        "name":        "World Bank Open Data",
        "badge":       "Coming soon",
        "badge_type":  "planned",
        "description": (
            "Rwanda gender indicators from the World Bank Open Data API — "
            "female labour force participation, gender parity in education, women in business."
        ),
        "adapter":     "data_pipeline/worldbank_adapter.py",
        "run_cmd":     "python data_pipeline/worldbank_adapter.py",
        "dir":         "worldbank",
    },
    {
        "key":         "ilo",
        "name":        "ILO ILOSTAT",
        "badge":       "Coming soon",
        "badge_type":  "planned",
        "description": (
            "Rwanda labour statistics from ILO ILOSTAT — employment by sex, wages, "
            "child labour, and decent work indicators."
        ),
        "adapter":     "data_pipeline/ilo_adapter.py",
        "run_cmd":     "python data_pipeline/ilo_adapter.py",
        "dir":         "ilo",
    },
]


def _read_source_csv(directory, filename: str):
    import pandas as pd
    if directory is None or not directory.exists():
        return pd.DataFrame()
    path = directory / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str)
    except Exception:
        return pd.DataFrame()


def _source_stats(src: dict) -> dict:
    import pandas as pd
    if src["key"] == "nisr_base":
        studies = _read_source_csv(_FULL_DIR, "studies.csv")
        if "source_adapter" in studies.columns:
            base = studies[studies["source_adapter"].fillna("") == ""]
        else:
            base = studies
        return {
            "study_count":    len(base),
            "resource_count": None,
            "last_ingested":  "Built-in",
            "active":         True,
        }
    src_dir = _PIPELINE_SOURCES_DIR / src["dir"] if src["dir"] else None
    studies   = _read_source_csv(src_dir, "studies.csv")
    resources = _read_source_csv(src_dir, "study_resources.csv")
    last = "—"
    if not studies.empty and "ingested_at" in studies.columns:
        dates = studies["ingested_at"].dropna()
        last = str(dates.max()) if not dates.empty else "—"
    return {
        "study_count":    len(studies) if not studies.empty else 0,
        "resource_count": len(resources) if not resources.empty else 0,
        "last_ingested":  last,
        "active":         not studies.empty,
    }


@app.get("/api/pipeline")
def pipeline_status():
    """Return status of all data pipeline sources and recently added studies."""
    import pandas as pd
    from datetime import date as _date

    sources_out = []
    for src in _PIPELINE_SOURCES:
        stats = _source_stats(src)
        sources_out.append({
            "key":          src["key"],
            "name":         src["name"],
            "badge":        src["badge"],
            "badge_type":   src["badge_type"],
            "description":  src["description"],
            "adapter":      src["adapter"],
            "run_cmd":      src["run_cmd"],
            "study_count":  stats["study_count"],
            "resource_count": stats["resource_count"],
            "last_ingested":  stats["last_ingested"],
            "active":         stats["active"],
        })

    # Overall merged stats
    studies_df = _read_source_csv(_FULL_DIR, "studies.csv")
    resources_df = _read_source_csv(_FULL_DIR, "study_resources.csv")
    total_studies   = len(studies_df)
    total_resources = len(resources_df)
    new_today = 0
    if not studies_df.empty and "ingested_at" in studies_df.columns:
        new_today = int((studies_df["ingested_at"].fillna("") == str(_date.today())).sum())

    # Recently added (pipeline-ingested rows, sorted by ingested_at)
    recent = []
    if not studies_df.empty and "ingested_at" in studies_df.columns:
        recent_df = (
            studies_df[studies_df["ingested_at"].notna() & (studies_df["ingested_at"] != "")]
            .sort_values("ingested_at", ascending=False)
            .head(20)
        )
        for _, row in recent_df.iterrows():
            recent.append({
                "study_id":       str(row.get("study_id", "")),
                "title":          str(row.get("title", "Untitled")),
                "organization":   str(row.get("organization", "—")),
                "year":           str(row.get("year", "—")),
                "source_adapter": str(row.get("source_adapter", "—")),
                "ingested_at":    str(row.get("ingested_at", "—")),
            })

    return {
        "sources":          sources_out,
        "total_studies":    total_studies,
        "total_resources":  total_resources,
        "active_sources":   sum(1 for s in sources_out if s["active"]),
        "new_today":        new_today,
        "recently_added":   recent,
    }
