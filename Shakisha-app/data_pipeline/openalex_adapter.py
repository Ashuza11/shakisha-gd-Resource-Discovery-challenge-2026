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

# Targeted queries — each maps to a domain tag used in the output
QUERIES: list[dict] = [
    {
        "domain": "labour",
        "label": "Rwanda labour & gender",
        "search": 'Rwanda AND ("labour force" OR "labor force" OR "employment" OR "workforce") AND ("women" OR "gender")',
    },
    {
        "domain": "labour",
        "label": "Rwanda women economic participation",
        "search": 'Rwanda AND ("women" OR "gender") AND ("economic participation" OR "informal sector" OR "enterprise" OR "wage gap")',
    },
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
        "domain": "gender",
        "label": "Rwanda gender equality & policy",
        "search": 'Rwanda AND ("gender equality" OR "women empowerment" OR "gender policy" OR "gender-based violence")',
    },
    {
        "domain": "gender",
        "label": "Rwanda women political participation",
        "search": 'Rwanda AND ("women" OR "gender") AND ("parliament" OR "political participation" OR "leadership" OR "decision-making")',
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


def normalize_work(work: dict, domain: str) -> tuple[dict, list[dict]]:
    """Convert an OpenAlex work to (study_row, resource_rows) matching Shakisha schema."""
    oa_id = work.get("id", "")
    study_id = _make_study_id(oa_id)
    title = work.get("display_name") or "Untitled"
    year = work.get("publication_year")
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
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

def run(max_per_query: int = 500, dry_run: bool = False) -> None:
    print("=" * 60)
    print("Shakisha — OpenAlex Adapter")
    print(f"Max results per query: {max_per_query} | Dry run: {dry_run}")
    print("=" * 60)

    all_studies: list[dict] = []
    all_resources: list[dict] = []
    seen_ids: set[str] = set()

    for query in QUERIES:
        works = fetch_query(query, max_per_query, dry_run)
        for work in works:
            study_id = _make_study_id(work.get("id", ""))
            if study_id in seen_ids:
                continue
            seen_ids.add(study_id)
            study_row, resource_rows = normalize_work(work, query["domain"])
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
