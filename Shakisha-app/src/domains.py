from __future__ import annotations

from typing import TypedDict


class DomainConfig(TypedDict):
    name: str
    emoji: str
    description: str
    keywords: list[str]
    status: str          # "active" | "coming_soon" | "planned"
    advocacy_context: str
    study_count_hint: int


# Domain registry — add new domains here as data is validated.
# Status flow: planned → coming_soon → active
DOMAINS: dict[str, DomainConfig] = {
    "labour": {
        "name": "Labour & Employment",
        "emoji": "👷",
        "description": "Workforce participation, employment surveys, enterprise and establishment census data.",
        "keywords": [
            "labour", "labor", "manpower", "employment",
            "enterprise", "establishment", "workforce", "child labour",
        ],
        "status": "active",
        "advocacy_context": (
            "Women's economic participation and employment equity in Rwanda — "
            "covering formal employment, informal sector, child labour, and enterprise ownership."
        ),
        "study_count_hint": 99,
    },
    "agriculture": {
        "name": "Agriculture & Food Security",
        "emoji": "🌾",
        "description": "Agricultural household surveys, seasonal crop data, food security assessments.",
        "keywords": [
            "agriculture", "agricultural", "food security",
            "season", "crop", "livestock", "nutrition",
        ],
        "status": "active",
        "advocacy_context": (
            "Women's role in agricultural production, land rights, "
            "and food security outcomes in rural Rwanda."
        ),
        "study_count_hint": 297,
    },
    "health": {
        "name": "Demographics & Health",
        "emoji": "🏥",
        "description": "DHS surveys, maternal health, reproductive health, and service provision data.",
        "keywords": [
            "demographic and health", "dhs",
            "mics", "service provision",
            "maternal health", "reproductive health",
        ],
        "status": "active",
        "advocacy_context": (
            "Reproductive health, maternal mortality, and women's access "
            "to healthcare services across Rwanda."
        ),
        "study_count_hint": 112,
    },
    "household": {
        "name": "Household & Living Conditions",
        "emoji": "🏠",
        "description": "EICV integrated household surveys, poverty assessment, living standards data.",
        "keywords": [
            "eicv", "household survey", "living standards",
            "integrated household", "household consumption", "poverty assessment",
        ],
        "status": "active",
        "advocacy_context": (
            "Gender dimensions of household poverty, asset ownership, "
            "and living standards in Rwanda."
        ),
        "study_count_hint": 72,
    },
    "finance": {
        "name": "Financial Inclusion",
        "emoji": "💰",
        "description": "FinScope surveys measuring access to financial services and products.",
        "keywords": [
            "finscope", "financial inclusion",
            "microfinance", "access to finance",
        ],
        "status": "active",
        "advocacy_context": (
            "Women's access to formal financial services, savings, credit, "
            "and mobile money in Rwanda."
        ),
        "study_count_hint": 47,
    },
    "population": {
        "name": "Population & Census",
        "emoji": "👥",
        "description": "Population and housing censuses, demographic snapshots.",
        "keywords": [
            "population and housing census", "recensement général",
            "general census", "demographic projection",
        ],
        "status": "active",
        "advocacy_context": (
            "Population structure, urbanization, and gender demographic trends across Rwanda."
        ),
        "study_count_hint": 8,
    },
}


def get_active_domains() -> dict[str, DomainConfig]:
    return {k: v for k, v in DOMAINS.items() if v["status"] == "active"}


def get_domain_keywords(domain_key: str) -> list[str]:
    return DOMAINS.get(domain_key, {}).get("keywords", [])


def filter_by_domain(
    titles: list[str],
    domain_key: str,
    abstracts: list[str] | None = None,
) -> list[bool]:
    """Return a boolean mask — True if a title or abstract belongs to the given domain."""
    keywords = get_domain_keywords(domain_key)
    if not keywords:
        return [True] * len(titles)
    result = []
    for i, title in enumerate(titles):
        t = str(title).lower()
        in_title = any(k in t for k in keywords)
        in_abstract = False
        if not in_title and abstracts is not None and i < len(abstracts):
            a = str(abstracts[i]).lower()
            in_abstract = any(k in a for k in keywords)
        result.append(in_title or in_abstract)
    return result
