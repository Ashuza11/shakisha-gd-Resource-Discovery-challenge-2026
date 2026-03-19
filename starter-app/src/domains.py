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
        "study_count_hint": 19,
    },
    "agriculture": {
        "name": "Agriculture & Food Security",
        "emoji": "🌾",
        "description": "Agricultural household surveys, seasonal crop data, food security assessments.",
        "keywords": [
            "agriculture", "agricultural", "food security",
            "season", "crop", "livestock", "nutrition",
        ],
        "status": "coming_soon",
        "advocacy_context": (
            "Women's role in agricultural production, land rights, "
            "and food security outcomes in rural Rwanda."
        ),
        "study_count_hint": 22,
    },
    "health": {
        "name": "Demographics & Health",
        "emoji": "🏥",
        "description": "DHS surveys, maternal health, reproductive health, and service provision data.",
        "keywords": [
            "demographic", "health", "dhs", "mics",
            "service provision", "maternal", "reproductive",
        ],
        "status": "coming_soon",
        "advocacy_context": (
            "Reproductive health, maternal mortality, and women's access "
            "to healthcare services across Rwanda."
        ),
        "study_count_hint": 9,
    },
    "household": {
        "name": "Household & Living Conditions",
        "emoji": "🏠",
        "description": "EICV integrated household surveys, poverty assessment, living standards data.",
        "keywords": ["household", "eicv", "living conditions", "poverty", "welfare"],
        "status": "planned",
        "advocacy_context": (
            "Gender dimensions of household poverty, asset ownership, "
            "and living standards in Rwanda."
        ),
        "study_count_hint": 13,
    },
    "finance": {
        "name": "Financial Inclusion",
        "emoji": "💰",
        "description": "FinScope surveys measuring access to financial services and products.",
        "keywords": ["finscope", "financial", "finance", "inclusion", "banking"],
        "status": "planned",
        "advocacy_context": (
            "Women's access to formal financial services, savings, credit, "
            "and mobile money in Rwanda."
        ),
        "study_count_hint": 4,
    },
    "population": {
        "name": "Population & Census",
        "emoji": "👥",
        "description": "Population and housing censuses, demographic snapshots.",
        "keywords": ["population", "housing", "census", "recensement", "habitat"],
        "status": "planned",
        "advocacy_context": (
            "Population structure, urbanization, and gender demographic trends across Rwanda."
        ),
        "study_count_hint": 10,
    },
}


def get_active_domains() -> dict[str, DomainConfig]:
    return {k: v for k, v in DOMAINS.items() if v["status"] == "active"}


def get_domain_keywords(domain_key: str) -> list[str]:
    return DOMAINS.get(domain_key, {}).get("keywords", [])


def filter_by_domain(titles: list[str], domain_key: str) -> list[bool]:
    """Return a boolean mask — True if a title belongs to the given domain."""
    keywords = get_domain_keywords(domain_key)
    if not keywords:
        return [True] * len(titles)
    result = []
    for title in titles:
        t = str(title).lower()
        result.append(any(k in t for k in keywords))
    return result
