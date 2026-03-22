"""
OpenAlex adapter for Shakisha data pipeline.

Fetches research papers relevant to Rwanda gender/labour/agriculture from the
OpenAlex open-access academic API (no API key required).

Output: two CSV files that conform to the Shakisha studies.csv schema.
  - data/pipeline_sources/openalex/studies.csv
  - data/pipeline_sources/openalex/study_resources.csv

Run:
    python data_pipeline/openalex_adapter.py
    python data_pipeline/openalex_adapter.py --max-per-query 200 --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_URL = "https://api.openalex.org/works"
MAILTO = "shakisha@grb2026.rw"          # identifies us to OpenAlex polite pool
PAGE_SIZE = 200                          # max allowed by OpenAlex
OUTPUT_DIR = Path("data/pipeline_sources/openalex")
RATE_LIMIT_DELAY = 0.12                  # seconds between requests (~8 req/s)

# Targeted queries — each maps to a domain tag used in the output.
# Every query is scoped to Rwanda AND a gender lens to stay within the
# hackathon theme.  Domains mirror the six active Shakisha domains.
QUERIES: list[dict] = [
    # ── Labour ──────────────────────────────────────────────────────────────
    {
        "domain": "labour",
        "label": "Rwanda labour force & gender",
        "search": 'Rwanda AND ("labour force" OR "labor force" OR "employment" OR "workforce") AND ("women" OR "gender")',
    },
    {
        "domain": "labour",
        "label": "Rwanda women economic participation",
        "search": 'Rwanda AND ("women" OR "gender") AND ("economic participation" OR "informal sector" OR "enterprise" OR "wage gap")',
    },
    {
        "domain": "labour",
        "label": "Rwanda youth unemployment & gender",
        "search": 'Rwanda AND ("youth unemployment" OR "NEET" OR "skills" OR "vocational training") AND ("women" OR "gender" OR "girls")',
    },
    # ── Agriculture ─────────────────────────────────────────────────────────
    {
        "domain": "agriculture",
        "label": "Rwanda agriculture & gender",
        "search": 'Rwanda AND ("agriculture" OR "food security" OR "smallholder" OR "farming") AND ("women" OR "gender")',
    },
    {
        "domain": "agriculture",
        "label": "Rwanda land rights & women",
        "search": 'Rwanda AND ("land rights" OR "land tenure" OR "land ownership") AND ("women" OR "gender")',
    },
    {
        "domain": "agriculture",
        "label": "Rwanda nutrition & food security women",
        "search": 'Rwanda AND ("nutrition" OR "malnutrition" OR "stunting" OR "food insecurity") AND ("women" OR "gender" OR "maternal")',
    },
    # ── Health / Demographics ────────────────────────────────────────────────
    {
        "domain": "health",
        "label": "Rwanda maternal & reproductive health",
        "search": 'Rwanda AND ("maternal health" OR "reproductive health" OR "maternal mortality" OR "antenatal" OR "postnatal") AND ("women" OR "gender")',
    },
    {
        "domain": "health",
        "label": "Rwanda DHS & demographic health survey",
        "search": 'Rwanda AND ("demographic health survey" OR "DHS" OR "fertility rate" OR "child mortality") AND ("women" OR "gender")',
    },
    {
        "domain": "health",
        "label": "Rwanda gender-based violence & health",
        "search": 'Rwanda AND ("gender-based violence" OR "GBV" OR "intimate partner violence" OR "domestic violence") AND ("women" OR "health")',
    },
    {
        "domain": "health",
        "label": "Rwanda family planning & contraception",
        "search": 'Rwanda AND ("family planning" OR "contraception" OR "contraceptive" OR "birth spacing") AND ("women" OR "gender")',
    },
    # ── Household ───────────────────────────────────────────────────────────
    {
        "domain": "household",
        "label": "Rwanda household welfare & women",
        "search": 'Rwanda AND ("household" OR "living standards" OR "living conditions" OR "welfare") AND ("women" OR "gender")',
    },
    {
        "domain": "household",
        "label": "Rwanda poverty & female-headed households",
        "search": 'Rwanda AND ("poverty" OR "female-headed household" OR "consumption" OR "EICV") AND ("women" OR "gender")',
    },
    {
        "domain": "household",
        "label": "Rwanda unpaid care & domestic work",
        "search": 'Rwanda AND ("unpaid work" OR "care work" OR "domestic work" OR "time use") AND ("women" OR "gender")',
    },
    # ── Finance ─────────────────────────────────────────────────────────────
    {
        "domain": "finance",
        "label": "Rwanda financial inclusion & women",
        "search": 'Rwanda AND ("financial inclusion" OR "mobile money" OR "finscope" OR "savings") AND ("women" OR "gender")',
    },
    {
        "domain": "finance",
        "label": "Rwanda microfinance & women entrepreneurship",
        "search": 'Rwanda AND ("microfinance" OR "credit" OR "women entrepreneurship" OR "SME") AND ("women" OR "gender")',
    },
    # ── Population / Census ─────────────────────────────────────────────────
    {
        "domain": "population",
        "label": "Rwanda population census & gender",
        "search": 'Rwanda AND ("census" OR "population" OR "migration" OR "urbanisation") AND ("women" OR "gender")',
    },
    {
        "domain": "population",
        "label": "Rwanda women empowerment & social protection",
        "search": 'Rwanda AND ("women empowerment" OR "social protection" OR "safety net" OR "VUP") AND ("women" OR "gender")',
    },
    {
        "domain": "population",
        "label": "Rwanda girls education & gender gap",
        "search": 'Rwanda AND ("girls education" OR "school enrollment" OR "gender parity" OR "early marriage") AND ("women" OR "gender")',
    },
    # ── Cross-cutting gender ─────────────────────────────────────────────────
    {
        "domain": "gender",
        "label": "Rwanda gender equality & policy",
        "search": 'Rwanda AND ("gender equality" OR "women empowerment" OR "gender policy" OR "gender mainstreaming")',
    },
    {
        "domain": "gender",
        "label": "Rwanda women political participation",
        "search": 'Rwanda AND ("women" OR "gender") AND ("parliament" OR "political participation" OR "leadership" OR "decision-making")',
    },
    {
        "domain": "gender",
        "label": "Rwanda gender index & SDG",
        "search": 'Rwanda AND ("gender development index" OR "SDG 5" OR "gender gap" OR "women rights" OR "CEDAW")',
    },
]

# Fields to retrieve from OpenAlex
SELECT_FIELDS = ",".join([
    "id", "display_name", "publication_year", "abstract_inverted_index",
    "primary_location", "authorships", "type", "doi", "open_access",
    "concepts", "referenced_works_count", "cited_by_count",
])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct plain-text abstract from OpenAlex's inverted index format."""
    if not inverted_index:
        return ""
    words: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def _get_source_name(work: dict) -> str:
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name", "")


def _get_oa_url(work: dict) -> str:
    oa = work.get("open_access") or {}
    return oa.get("oa_url", "") or ""


def _get_doi_url(work: dict) -> str:
    doi = work.get("doi") or ""
    return doi if doi.startswith("http") else (f"https://doi.org/{doi}" if doi else "")


def _make_study_id(openalex_id: str) -> str:
    short = openalex_id.split("/")[-1]   # e.g. W2741809807
    return f"oa_{short}"


def _is_rwanda_focused(title: str, abstract: str) -> bool:
    """Return True only if Rwanda is the primary focus — not a passing mention in a multi-country study.
    Rules (in order of strength):
      1. "Rwanda" in the title → strong signal, always keep
      2. "Rwanda" in the first 300 chars of the abstract → Rwanda is the stated subject
      3. Any Rwanda city/district keyword in the title (e.g. Kigali, Musanze) → keep
    Multi-country studies that only mention Rwanda deep in the abstract are excluded.
    """
    title_lower = title.lower()
    if "rwanda" in title_lower:
        return True
    # Rwanda place names in title (city/district level)
    rwanda_places = {"kigali", "musanze", "huye", "rubavu", "nyagatare", "rwamagana",
                     "butare", "gisenyi", "byumba", "gitarama", "cyangugu"}
    if any(p in title_lower for p in rwanda_places):
        return True
    # Rwanda must appear in the opening of the abstract (first 300 chars)
    if abstract and "rwanda" in abstract[:300].lower():
        return True
    return False


def _normalize_title(title: str) -> str:
    """Convert ALL-CAPS titles to Title Case; leave normally-cased titles alone."""
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


def _get_authors(work: dict) -> str:
    authors = work.get("authorships") or []
    names = [a["author"]["display_name"] for a in authors[:5] if a.get("author")]
    return "; ".join(names)


def _fetch_page(search: str, cursor: str, dry_run: bool = False) -> dict:
    params = urllib.parse.urlencode({
        "search": search,
        "filter": "has_abstract:true,publication_year:>1995",
        "per-page": PAGE_SIZE,
        "select": SELECT_FIELDS,
        "cursor": cursor,
        "mailto": MAILTO,
    })
    url = f"{BASE_URL}?{params}"
    if dry_run:
        print(f"    [dry-run] GET {url[:100]}...")
        return {"results": [], "meta": {"count": 0, "next_cursor": None}}
    req = urllib.request.Request(url, headers={"User-Agent": "Shakisha-Pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


# ── Core fetch loop ─────────────────────────────────────────────────────────────

def fetch_query(query: dict, max_results: int, dry_run: bool) -> list[dict]:
    """Fetch all pages for one query, up to max_results works."""
    search = query["search"]
    domain = query["domain"]
    label = query["label"]

    print(f"\n  Fetching: {label}")
    works: list[dict] = []
    cursor = "*"
    page = 0

    while len(works) < max_results:
        try:
            data = _fetch_page(search, cursor, dry_run)
        except Exception as e:
            print(f"    Error on page {page + 1}: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        if page == 0:
            total = data.get("meta", {}).get("count", 0)
            print(f"    Total available: {total:,} — fetching up to {max_results}")

        works.extend(results)
        cursor = (data.get("meta") or {}).get("next_cursor")
        page += 1

        if not cursor:
            break

        time.sleep(RATE_LIMIT_DELAY)

    print(f"    Fetched {len(works)} works")
    return works


def normalize_work(work: dict, domain: str) -> tuple[dict, list[dict]] | None:
    """Convert an OpenAlex work to (study_row, resource_rows) matching Shakisha schema.
    Returns None if the paper is not Rwanda-focused."""
    oa_id = work.get("id", "")
    study_id = _make_study_id(oa_id)
    title = _normalize_title(work.get("display_name") or "Untitled")
    year = work.get("publication_year")
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    # Drop papers that don't actually discuss Rwanda
    if not _is_rwanda_focused(title, abstract):
        return None

    source = _get_source_name(work)
    doi_url = _get_doi_url(work)
    oa_url = _get_oa_url(work)
    url = doi_url or oa_url
    authors = _get_authors(work)
    work_type = work.get("type", "article")
    cited_by = work.get("cited_by_count", 0)

    study_row = {
        "study_id": study_id,
        "title": title,
        "year": year,
        "organization": source,
        "collection": f"OpenAlex — {domain.title()}",
        "created": "",
        "modified": "",
        "views": cited_by,
        "url": url,
        "catalog_page": "",
        "get_microdata_url": "",
        "data_access_type": "Open Access" if oa_url else "Restricted",
        "country": "Rwanda",
        "study_type": work_type.replace("-", " ").title(),
        "id_number": oa_id,
        "production_date": str(year) if year else "",
        "abstract": abstract,
        "scope_notes": "",
        "notes": f"Source: OpenAlex | Domain: {domain} | Authors: {authors}",
        "kind_of_data": "Research article [article]",
        "units_of_analysis": "",
        "geographic_coverage": "Rwanda",
        "geographic_unit": "",
        "universe": "",
        "producers_and_sponsors": authors,
        "primary_investigator": authors.split(";")[0].strip() if authors else "",
        "other_producers": "",
        "funding": "",
        "overview_summary": abstract[:500] if abstract else "",
        "data_description_summary": "",
        "documentation_summary": "",
        "resource_count": 1 if oa_url else 0,
        "quality_flags": _compute_quality_flags(title, abstract, url, year),
        "study_description": abstract,
        "data_description": "",
        "documentation": doi_url,
        "source_adapter": "openalex",
        "ingested_at": "",
    }

    resources = []
    if oa_url:
        resources.append({
            "study_id": study_id,
            "type": "pdf" if oa_url.endswith(".pdf") else "url",
            "name": f"Open Access — {title[:60]}",
            "label": "Full text (open access)",
            "url": oa_url,
            "filename": "",
            "quality_flags": "",
        })
    if doi_url and doi_url != oa_url:
        resources.append({
            "study_id": study_id,
            "type": "url",
            "name": f"DOI — {title[:60]}",
            "label": "DOI link",
            "url": doi_url,
            "filename": "",
            "quality_flags": "",
        })

    return study_row, resources


def _compute_quality_flags(title: str, abstract: str, url: str, year) -> str:
    flags = []
    if not abstract:
        flags.append("missing_abstract")
    if not url:
        flags.append("missing_url")
    if not year:
        flags.append("missing_year")
    if not title or title == "Untitled":
        flags.append("missing_title")
    return ";".join(flags)


def build_quality_report(studies: list[dict]) -> list[dict]:
    rows = []
    for s in studies:
        flags = s.get("quality_flags", "")
        count = len([f for f in flags.split(";") if f.strip()])
        rows.append({
            "study_id": s["study_id"],
            "title": s["title"],
            "quality_flags": flags,
            "missing_field_count": count,
            "resource_count": s["resource_count"],
            "resource_quality_flags": "",
        })
    return rows


# ── Writer ─────────────────────────────────────────────────────────────────────

def write_csvs(studies: list[dict], resources: list[dict], quality: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _write(path: Path, rows: list[dict]) -> None:
        if not rows:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Wrote {len(rows):,} rows → {path}")

    _write(OUTPUT_DIR / "studies.csv", studies)
    _write(OUTPUT_DIR / "study_resources.csv", resources)
    _write(OUTPUT_DIR / "quality_report.csv", quality)


# ── Main ───────────────────────────────────────────────────────────────────────

def _load_existing_ids() -> set[str]:
    """Load study IDs already in data/full/studies.csv so we skip them during fetch."""
    existing = Path("data/full/studies.csv")
    if not existing.exists():
        return set()
    ids: set[str] = set()
    with open(existing, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("study_id", "").strip()
            if sid:
                ids.add(sid)
    print(f"  Loaded {len(ids):,} existing study IDs from data/full/ (will skip duplicates)")
    return ids


def run(max_per_query: int = 500, dry_run: bool = False) -> None:
    print("=" * 60)
    print("Shakisha — OpenAlex Adapter")
    print(f"Max results per query: {max_per_query} | Dry run: {dry_run}")
    print("=" * 60)

    # Pre-load all IDs already in the dataset so we never re-add them
    seen_ids: set[str] = _load_existing_ids()
    all_studies: list[dict] = []
    all_resources: list[dict] = []

    for query in QUERIES:
        works = fetch_query(query, max_per_query, dry_run)
        for work in works:
            study_id = _make_study_id(work.get("id", ""))
            if study_id in seen_ids:
                continue
            seen_ids.add(study_id)
            result = normalize_work(work, query["domain"])
            if result is None:
                continue  # not Rwanda-focused — skip
            study_row, resource_rows = result
            all_studies.append(study_row)
            all_resources.extend(resource_rows)

    quality_rows = build_quality_report(all_studies)

    print(f"\nTotal unique studies: {len(all_studies):,}")
    print(f"Total resources: {len(all_resources):,}")

    if not dry_run:
        write_csvs(all_studies, all_resources, quality_rows)
        print("\nDone. Next step: run  python data_pipeline/build_dataset.py")
    else:
        print("\n[dry-run] No files written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Rwanda gender/labour/agriculture papers from OpenAlex")
    parser.add_argument("--max-per-query", type=int, default=500, help="Max results per query (default 500)")
    parser.add_argument("--dry-run", action="store_true", help="Print API calls without fetching")
    args = parser.parse_args()
    run(max_per_query=args.max_per_query, dry_run=args.dry_run)
