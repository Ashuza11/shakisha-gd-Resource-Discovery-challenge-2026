from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL = "claude-haiku-4-5-20251001"

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "AI features are not available at this time. "
            "Please contact the Shakisha team or try again later."
        )
    # Always create a fresh client — avoids stale key after .env changes
    if _client is None:
        _client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
    return _client


def interpret_query(user_query: str) -> dict[str, Any]:
    """
    Interpret a natural-language search query and return structured filter parameters.

    Returns a dict with keys:
        - keywords: list[str]   — extracted search terms
        - year_min: int | None  — inferred lower year bound
        - year_max: int | None  — inferred upper year bound
        - explanation: str      — one sentence describing what the user is looking for
    """
    if not user_query.strip():
        return {"keywords": [], "year_min": None, "year_max": None, "explanation": ""}

    prompt = f"""You are a data librarian assistant for a gender data discovery platform in Rwanda.
A user typed this search query: "{user_query}"

Extract structured search parameters from this query. Reply ONLY with a valid JSON object — no markdown, no explanation outside the JSON.

JSON format:
{{
  "keywords": ["keyword1", "keyword2"],
  "year_min": null or integer,
  "year_max": null or integer,
  "explanation": "One sentence describing what the user is looking for."
}}

Rules:
- keywords: 2–5 important terms to match against study titles and abstracts
- year_min / year_max: only set if the query implies a time range (e.g. "recent", "after 2018", "2015–2020")
- explanation: plain English, under 20 words, describe the search intent
"""
    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        # Fallback: treat the whole query as a keyword search
        return {
            "keywords": user_query.split(),
            "year_min": None,
            "year_max": None,
            "explanation": f"Searching for: {user_query}",
        }


def explain_study(study_row: dict[str, Any], user_query: str) -> str:
    """
    Return a 2-sentence explanation of why a study is relevant to the user's query.
    """
    title = study_row.get("title", "Untitled")
    year = study_row.get("year", "Unknown year")
    abstract = str(study_row.get("abstract", ""))[:600]
    org = study_row.get("organization", "Unknown organization")

    prompt = f"""You are a gender data assistant. A user searched for: "{user_query}"

This study was returned as a result:
Title: {title}
Year: {year}
Organization: {org}
Abstract excerpt: {abstract}

Write exactly 2 short sentences explaining why this study is relevant to the user's search.
Be specific. Do not repeat the title. Max 40 words total."""

    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def advocacy_brief(study_row: dict[str, Any], resources: list[dict[str, Any]]) -> dict[str, str]:
    """
    Generate a structured advocacy brief for a given study.

    Returns a dict with keys:
        - policy_context
        - key_findings   (3 bullet points as a single string, newline-separated)
        - data_gaps
        - recommended_action
        - citation
    """
    title = study_row.get("title", "Untitled")
    year = study_row.get("year", "Unknown")
    org = study_row.get("organization", "Unknown organization")
    abstract = str(study_row.get("abstract", ""))[:800]
    quality_flags = study_row.get("quality_flags", "")
    missing_count = study_row.get("missing_field_count", 0)
    url = study_row.get("url", "")
    geo = study_row.get("geographic_coverage", "Rwanda")
    resource_types = ", ".join(
        sorted({str(r.get("type", "")).lower() for r in resources if r.get("type")})
    )

    prompt = f"""You are a policy brief writer for a Rwandan gender data advocacy platform.

Rwanda policy context (reference where relevant):
- Vision 2050: targets gender parity in economic participation, education, and leadership by 2050.
- National Strategy for Transformation (NST1, 2017–2024): commits to 30% women in all decision-making bodies and closing gender wage gaps.
- National Gender Policy (2021): mandates gender-responsive budgeting (GRB) and sex-disaggregated data across all ministries.
- SDG 5: gender equality and empowerment of all women and girls.
- Maputo Protocol: Rwanda is a signatory — commits to women's reproductive rights and freedom from GBV.

Study details:
- Title: {title}
- Year: {year}
- Organization: {org}
- Geographic coverage: {geo}
- Available resources: {resource_types or "not specified"}
- Quality flags: {quality_flags or "none"}
- Missing metadata fields: {missing_count}
- Abstract: {abstract}

Write a structured advocacy brief. Reply ONLY with a valid JSON object — no markdown outside the JSON.

JSON format:
{{
  "policy_context": "2–3 sentences on why this data matters for Rwanda gender policy, referencing Vision 2050, NST1, or the National Gender Policy where directly relevant.",
  "key_findings": "• Finding one\\n• Finding two\\n• Finding three",
  "data_gaps": "1–2 sentences on what is missing or limited in this dataset.",
  "recommended_action": "1 concrete advocacy recommendation a CSO can act on, tied to a specific Rwanda policy commitment.",
  "citation": "Proper citation: {org}, {title}, {year}. Available at: {url}"
}}

Be specific, concise, and grounded in the abstract. Do not invent statistics."""

    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Extract JSON from markdown code fences if present (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last resort: find the outermost { ... } in the text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        return {
            "policy_context": "Brief generation encountered a formatting issue. Please try again.",
            "key_findings": "- See abstract for details.",
            "data_gaps": str(quality_flags) if quality_flags and str(quality_flags) != "nan" else "Not specified.",
            "recommended_action": "Review the full study for advocacy opportunities.",
            "citation": f"{org}. ({year}). {title}. Available at: {url}",
        }
