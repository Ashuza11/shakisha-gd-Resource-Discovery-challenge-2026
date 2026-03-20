"""
NISR Rwanda catalog crawler — Shakisha pipeline adapter.

Crawls https://microdata.statistics.gov.rw/index.php/catalog for studies
relevant to gender, labour, agriculture, health, and household welfare in Rwanda.

Key behaviours vs. the original crawler:
  - Skips study IDs already present in data/full/studies.csv (no re-crawl)
  - Gender/domain relevance filter applied at card stage (before hydration)
  - Checkpoint file lets interrupted crawls resume safely
  - Adds ingested_at + source_adapter columns for pipeline provenance
  - Output goes to data/pipeline_sources/nisr_crawl/ (feeds build_dataset.py)

Run:
    python data_pipeline/nisr_crawler.py
    python data_pipeline/nisr_crawler.py --max-pages 5 --max-studies 50
    python data_pipeline/nisr_crawler.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

# ── Paths ───────────────────────────────────────────────────────────────────
_PIPELINE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR     = _PIPELINE_ROOT / "data" / "pipeline_sources" / "nisr_crawl"
EXISTING_DATA  = _PIPELINE_ROOT / "data" / "full" / "studies.csv"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"

# ── Crawler constants ────────────────────────────────────────────────────────
CATALOG_SEED_URL = "https://microdata.statistics.gov.rw/index.php/catalog"
ALLOWED_DOMAIN   = "microdata.statistics.gov.rw"
USER_AGENT       = "ShakishaCrawler/1.0 (+GRB2026-hackathon)"

RESOURCE_EXTENSIONS = (".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx", ".zip")
DETAIL_PATH_RE  = re.compile(r"/index\.php/catalog/(\d+)(?:/)?$")
PAGINATION_RE   = re.compile(r"[/?&]page=(\d+)")

# ── Gender / domain relevance filter ────────────────────────────────────────
# A study card must match at least one keyword from either list to be hydrated.
# This keeps the dataset within the hackathon's gender-in-Rwanda theme while
# still capturing surveys that carry gender-disaggregated data even if "gender"
# isn't in the title (e.g. Labour Force Survey, EICV, DHS).
GENDER_KEYWORDS = [
    "women", "woman", "gender", "female", "girl",
    "maternal", "maternity", "reproductive", "fertility",
    "land rights", "women's", "womens",
]
DOMAIN_KEYWORDS = [
    "labour", "labor", "employment", "workforce", "enterprise", "establishment",
    "manpower", "child labour",
    "agriculture", "agricultural", "food security", "crop", "livestock",
    "season", "nutrition", "smallholder", "farming",
    "household", "poverty", "welfare", "living conditions", "eicv",
    "demographic", "health", "dhs", "mics", "service provision",
    "population", "census", "recensement",
    "financial", "finscope", "inclusion", "banking",
    "education", "child", "youth",
]

ALL_RELEVANCE_KEYWORDS = GENDER_KEYWORDS + DOMAIN_KEYWORDS


def is_gender_relevant(title: str) -> bool:
    """Return True if the study title matches our gender/domain theme."""
    t = title.lower()
    return any(k in t for k in ALL_RELEVANCE_KEYWORDS)


# ── Schema columns ───────────────────────────────────────────────────────────
STUDIES_COLUMNS = [
    "study_id", "title", "year", "organization", "collection",
    "created", "modified", "views", "url", "catalog_page",
    "get_microdata_url", "data_access_type", "country", "study_type",
    "id_number", "production_date", "abstract", "scope_notes", "notes",
    "kind_of_data", "units_of_analysis", "geographic_coverage",
    "geographic_unit", "universe", "producers_and_sponsors",
    "primary_investigator", "other_producers", "funding",
    "overview_summary", "data_description_summary", "documentation_summary",
    "resource_count", "quality_flags", "study_description",
    "data_description", "documentation",
    # provenance columns added by this crawler
    "ingested_at", "source_adapter",
]

RESOURCES_COLUMNS = [
    "study_id", "type", "name", "label", "url", "filename", "quality_flags",
]
QUALITY_REPORT_COLUMNS = [
    "study_id", "title", "quality_flags", "missing_field_count",
    "resource_count", "resource_quality_flags",
]


# ── Config dataclass ─────────────────────────────────────────────────────────
@dataclass
class CrawlConfig:
    seed_url: str
    max_pages: int
    max_studies: int
    delay_seconds: float
    timeout: int
    output_dir: Path
    debug_html: bool
    strict: bool
    dry_run: bool


# ── Checkpoint helpers ────────────────────────────────────────────────────────
def load_checkpoint(path: Path) -> Set[str]:
    """Return set of study_ids already processed in a previous (interrupted) run."""
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("completed_ids", []))
    except Exception:
        return set()


def save_checkpoint(path: Path, completed_ids: Set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"completed_ids": sorted(completed_ids), "updated": str(date.today())}),
        encoding="utf-8",
    )


def clear_checkpoint(path: Path) -> None:
    if path.exists():
        path.unlink()


# ── Existing data helpers ─────────────────────────────────────────────────────
def load_existing_study_ids(csv_path: Path) -> Set[str]:
    """Load study_ids already in data/full/ so we don't re-crawl them."""
    if not csv_path.exists():
        return set()
    try:
        ids: Set[str] = set()
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("study_id", "").strip()
                if sid:
                    ids.add(sid)
        logging.info("Loaded %d existing study IDs to skip", len(ids))
        return ids
    except Exception as exc:
        logging.warning("Could not read existing studies: %s", exc)
        return set()


# ── URL helpers ──────────────────────────────────────────────────────────────
def is_allowed_domain(url: str) -> bool:
    return urlparse(url).netloc.lower() == ALLOWED_DOMAIN


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    scheme = (p.scheme or "https").lower()
    return f"{scheme}://{p.netloc.lower()}{p.path}" + (f"?{p.query}" if p.query else "")


def normalize_catalog_listing_url(url: str) -> str:
    normalized = normalize_url(url)
    p = urlparse(normalized)
    if "/index.php/catalog" not in p.path:
        return normalized
    m = PAGINATION_RE.search(normalized)
    page_no = int(m.group(1)) if m else 1
    if page_no <= 1:
        return f"{p.scheme}://{p.netloc}/index.php/catalog"
    return f"{p.scheme}://{p.netloc}/index.php/catalog?page={page_no}"


# ── HTTP helpers ─────────────────────────────────────────────────────────────
def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_html(session: requests.Session, url: str, timeout: int) -> Optional[str]:
    try:
        r = session.get(url, timeout=timeout)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        if "text/html" not in ct and "application/xhtml" not in ct:
            return None
        return r.text
    except requests.RequestException as exc:
        logging.warning("Request failed %s: %s", url, exc)
        return None


def fetch_soup(session: requests.Session, url: str, timeout: int) -> Optional[BeautifulSoup]:
    html = fetch_html(session, url, timeout)
    return BeautifulSoup(html, "lxml") if html else None


# ── Catalog page discovery ───────────────────────────────────────────────────
def discover_next_catalog_pages(soup: BeautifulSoup, current_url: str) -> List[str]:
    pages: List[Tuple[int, str]] = []
    seen: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(current_url, a["href"])
        if not is_allowed_domain(href) or "/index.php/catalog" not in href:
            continue
        if "/index.php/catalog/" in href and not re.search(r"\?.*page=", href):
            continue
        m = PAGINATION_RE.search(href)
        if not m:
            continue
        page_no = int(m.group(1))
        normalized = normalize_catalog_listing_url(href)
        if normalized not in seen:
            seen.add(normalized)
            pages.append((page_no, normalized))
    pages.sort(key=lambda x: x[0])
    return [u for _, u in pages]


def fetch_catalog_pages(
    session: requests.Session,
    seed_url: str,
    max_pages: int,
    timeout: int,
    delay_seconds: float,
) -> List[Tuple[int, str, BeautifulSoup]]:
    pending = [normalize_catalog_listing_url(seed_url)]
    visited: Set[str] = set()
    pages: List[Tuple[int, str, BeautifulSoup]] = []

    while pending and len(pages) < max_pages:
        current = normalize_catalog_listing_url(pending.pop(0))
        if current in visited:
            continue
        visited.add(current)
        html = fetch_html(session, current, timeout)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        m = PAGINATION_RE.search(current)
        page_no = int(m.group(1)) if m else 1
        pages.append((page_no, current, soup))
        logging.info("Catalog page %d: %s", page_no, current)
        for nxt in discover_next_catalog_pages(soup, current):
            nxt = normalize_catalog_listing_url(nxt)
            if nxt not in visited and nxt not in pending:
                pending.append(nxt)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    pages.sort(key=lambda x: x[0])
    return pages


# ── Card parsing ─────────────────────────────────────────────────────────────
def extract_year(text: str) -> str:
    m = re.search(r"\b(19|20)\d{2}(?:-\d{2,4})?\b", text)
    return m.group(0) if m else ""


def extract_metadata_from_text(text: str) -> Dict[str, str]:
    joined = " ".join(ln.strip() for ln in text.splitlines() if ln.strip())

    def cap(pattern: str) -> str:
        m = re.search(pattern, joined, flags=re.IGNORECASE)
        return m.group(1).strip() if m else ""

    return {
        "year":         extract_year(joined),
        "organization": cap(r"\bBy:\s*(.+?)(?:\s+Created on:|\s+Collection:|$)"),
        "collection":   cap(r"\bCollection:\s*(.+?)(?:\s+Created on:|\s+Views:|$)"),
        "created":      cap(r"\bCreated on:\s*([A-Za-z]{3}\s+\d{2},\s+\d{4}|\d{4}-\d{2}-\d{2})"),
        "modified":     cap(r"\bLast modified:\s*([A-Za-z]{3}\s+\d{2},\s+\d{4}|\d{4}-\d{2}-\d{2})"),
        "views":        cap(r"\bViews:\s*([\d,]+)"),
    }


def parse_study_cards(
    soup: BeautifulSoup,
    base_url: str,
    catalog_page: int,
    skip_ids: Set[str],
) -> List[Dict[str, str]]:
    """Parse listing page cards, filtering by relevance and skipping known IDs."""
    records: List[Dict[str, str]] = []
    seen_urls: Set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = normalize_url(urljoin(base_url, anchor["href"]))
        m = DETAIL_PATH_RE.search(urlparse(href).path)
        if not is_allowed_domain(href) or not m:
            continue
        if href in seen_urls:
            continue

        title = anchor.get_text(" ", strip=True)
        if not title or title.lower() in {"next", "previous"}:
            continue

        study_id = m.group(1)

        # Skip already-ingested studies
        if study_id in skip_ids:
            logging.debug("Skipping existing study %s: %s", study_id, title[:60])
            continue

        # Gender/domain relevance filter — skip off-theme studies
        if not is_gender_relevant(title):
            logging.debug("Skipping off-theme study %s: %s", study_id, title[:60])
            continue

        container = anchor.find_parent(["div", "li", "article", "tr"]) or anchor.parent
        container_text = container.get_text("\n", strip=True) if isinstance(container, Tag) else title
        meta = extract_metadata_from_text(container_text)

        records.append({
            "study_id":    study_id,
            "title":       title,
            "year":        meta["year"],
            "organization": meta["organization"],
            "collection":  meta["collection"],
            "created":     meta["created"],
            "modified":    meta["modified"],
            "views":       meta["views"].replace(",", ""),
            "url":         href,
            "catalog_page": str(catalog_page),
        })
        seen_urls.add(href)

    return records


# ── Text parsing helpers ─────────────────────────────────────────────────────
def clean_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def full_text(text: str) -> str:
    return clean_whitespace(text)


def dedupe_repeated_segments(text: str) -> str:
    cleaned = clean_whitespace(text)
    if not cleaned:
        return ""
    parts = re.split(
        r"(?<=[.!?])\s+|\s+(?=Questionnaires\b|Reports\b|Tables\b|Variables\b)", cleaned
    )
    output: List[str] = []
    seen: Set[str] = set()
    for part in parts:
        norm = clean_whitespace(part)
        if len(norm) < 6 or norm.lower() in seen:
            continue
        seen.add(norm.lower())
        output.append(norm)
    return clean_whitespace(" ".join(output)) if output else cleaned


def join_flags(flags: List[str]) -> str:
    seen: Set[str] = set()
    out = []
    for f in flags:
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return ";".join(out)


def parse_labeled_value(text: str, label: str, next_labels: Sequence[str]) -> str:
    escaped_next = "|".join(
        rf"(?<!\w){re.escape(item)}(?!\w)" for item in next_labels
    )
    pattern = rf"(?<!\w){re.escape(label)}(?!\w)\s*(.+?)(?=(?:{escaped_next})|$)"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return clean_whitespace(m.group(1)) if m else ""


def parse_block_between(text: str, start_label: str, end_labels: Sequence[str]) -> str:
    escaped_next = "|".join(
        rf"(?<!\w){re.escape(item)}(?!\w)" for item in end_labels
    )
    pattern = rf"(?<!\w){re.escape(start_label)}(?!\w)\s*(.+?)(?=(?:{escaped_next})|$)"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return clean_whitespace(m.group(1)) if m else ""


def trim_trailing_markers(value: str, markers: Sequence[str]) -> str:
    cleaned = clean_whitespace(value)
    for marker in markers:
        cleaned = re.sub(rf"\s*{re.escape(marker)}\s*$", "", cleaned, flags=re.IGNORECASE)
    return clean_whitespace(cleaned)


def extract_tab_text(soup: BeautifulSoup) -> str:
    node = soup.select_one("div#tabs-1")
    if not node:
        node = soup.select_one("div.page-body-full") or soup.select_one("div#content")
    if not node:
        return ""
    for noisy in node.select("script, style, noscript"):
        noisy.decompose()
    return node.get_text(" ", strip=True)


def extract_section_by_heading(soup: BeautifulSoup, keywords: Sequence[str]) -> str:
    lowered = [k.lower() for k in keywords]
    heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"]
    for tag in soup.find_all(heading_tags):
        heading = tag.get_text(" ", strip=True).lower()
        if not any(k in heading for k in lowered):
            continue
        fragments: List[str] = []
        for sib in tag.find_all_next():
            if sib.name in heading_tags and sib.get_text(" ", strip=True).lower() != heading:
                break
            text = sib.get_text(" ", strip=True)
            if text and text not in fragments:
                fragments.append(text)
            if len(" ".join(fragments)) > 2000:
                break
        if fragments:
            return " ".join(fragments).strip()
    return ""


# ── Core field extraction ────────────────────────────────────────────────────
def extract_study_core_fields(study_description_text: str) -> Dict[str, str]:
    text = clean_whitespace(study_description_text)
    labels = [
        "Country", "Title", "Translated Title", "Study Type", "Type of Study",
        "ID Number", "Version", "Production Date", "Production Date(s)",
        "Production date(s)", "Notes", "Abstract", "Kind of Data", "Type of Data",
        "Units of Analysis", "Unit of Analysis", "Scope Notes", "Scope",
        "Geographic Coverage", "Geographic coverage", "Geographical Coverage",
        "Universe", "Primary Investigator(s)", "Other Producer(s)", "Funding",
    ]
    values: Dict[str, str] = {}
    for i, label in enumerate(labels):
        next_labels = labels[i + 1:] if i + 1 < len(labels) else ["Metadata Production"]
        values[label] = parse_labeled_value(text, label, next_labels)

    values["Production Date"] = trim_trailing_markers(
        values.get("Production Date", ""), ["Overview"]
    )
    values["Scope Notes"] = trim_trailing_markers(
        values.get("Scope Notes", ""), ["Coverage"]
    )
    values["Units of Analysis"] = trim_trailing_markers(
        values.get("Units of Analysis", ""), ["Coverage"]
    )
    values["Universe"] = trim_trailing_markers(
        values.get("Universe", ""), ["Producers and Sponsors"]
    )

    producers_block = parse_block_between(
        text, "Producers and Sponsors",
        ["Metadata Production", "Date of Metadata Production", "DDI Document Version"],
    )
    primary_investigator = parse_block_between(
        producers_block or text, "Primary Investigator(s)",
        ["Other Producer(s)", "Funding", "Metadata Production"],
    )
    other_producers = parse_block_between(
        producers_block or text, "Other Producer(s)",
        ["Funding", "Metadata Production"],
    )
    funding = parse_block_between(
        producers_block or text, "Funding",
        ["Metadata Production", "Date of Metadata Production", "DDI Document Version"],
    )

    def pick(*keys: str) -> str:
        for k in keys:
            v = values.get(k, "")
            if v:
                return v
        return ""

    abstract = pick("Abstract")
    geographic_coverage = pick(
        "Geographic Coverage", "Geographic coverage", "Geographical Coverage"
    )
    geographic_unit = parse_labeled_value(
        text, "Geographic Unit",
        ["Universe", "Producers and Sponsors", "Primary Investigator(s)"],
    )
    if not geographic_unit:
        split = re.split(r"\bGeographic\s+Unit\b", geographic_coverage, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2:
            geographic_coverage = clean_whitespace(split[0])
            geographic_unit = clean_whitespace(split[1])
    geographic_coverage = re.sub(
        r"\bGeographic\s+Unit\b.*$", "", geographic_coverage, flags=re.IGNORECASE
    ).strip()

    return {
        "country":              pick("Country"),
        "study_type":           pick("Study Type", "Type of Study"),
        "id_number":            pick("ID Number"),
        "production_date":      pick("Production Date", "Production Date(s)", "Production date(s)"),
        "abstract":             abstract,
        "scope_notes":          pick("Scope Notes", "Scope"),
        "notes":                pick("Notes"),
        "kind_of_data":         pick("Kind of Data", "Type of Data"),
        "units_of_analysis":    pick("Units of Analysis", "Unit of Analysis"),
        "geographic_coverage":  geographic_coverage,
        "geographic_unit":      geographic_unit,
        "universe":             pick("Universe"),
        "producers_and_sponsors":  producers_block,
        "primary_investigator": trim_trailing_markers(primary_investigator, ["Other Producer(s)", "Funding"]),
        "other_producers":      trim_trailing_markers(other_producers, ["Funding"]),
        "funding":              funding,
        "overview_summary":     full_text(abstract if abstract else text),
    }


def extract_abstract_from_description(study_description_text: str) -> str:
    return parse_labeled_value(
        clean_whitespace(study_description_text), "Abstract",
        ["Kind of Data", "Units of Analysis", "Scope Notes", "Geographic Coverage",
         "Universe", "Producers and Sponsors"],
    )


def apply_strict_row_quality_fixes(study_row: Dict[str, str]) -> None:
    abstract = clean_whitespace(study_row.get("abstract", ""))
    if len(abstract) < 60:
        repaired = extract_abstract_from_description(study_row.get("study_description", ""))
        if repaired:
            abstract = repaired
    if abstract and not re.search(r"[.!?]$|[\]\)]$", abstract):
        abstract += "."
    study_row["abstract"] = abstract
    for field in ["overview_summary", "data_description_summary", "documentation_summary"]:
        v = clean_whitespace(study_row.get(field, ""))
        study_row[field] = v.rstrip("...").rstrip() if v.endswith("...") else v


def build_documentation_summary(
    documentation_text: str, resources: List[Dict[str, str]]
) -> str:
    m = re.search(r"(Download the [^.]+(?:\.)?)", documentation_text, flags=re.IGNORECASE)
    intro = clean_whitespace(m.group(1)) if m else ""
    names: List[str] = []
    seen: Set[str] = set()
    for r in resources:
        name = (r.get("name") or r.get("label") or "").strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    if names:
        files_text = "; ".join(names)
        return f"{intro} Files ({len(names)}): {files_text}" if intro else f"Files ({len(names)}): {files_text}"
    return intro or full_text(documentation_text)


# ── Resource extraction ──────────────────────────────────────────────────────
def detect_resource_type(url: str, label: str) -> str:
    for ext in RESOURCE_EXTENSIONS:
        if url.lower().endswith(ext) or label.lower().endswith(ext):
            return ext.lstrip(".")
    ll = label.lower()
    if "questionnaire" in ll or "report" in ll:
        return "pdf"
    return "file"


def is_resource_link(url: str) -> bool:
    lower = url.lower()
    if "/get_microdata" in lower:
        return False
    return lower.endswith(RESOURCE_EXTENSIONS) or "/download/" in lower


def extract_microdata_fields(soup: BeautifulSoup, base_url: str) -> Tuple[str, str]:
    link = soup.select_one('a[href*="/get_microdata"]')
    if not link or not link.get("href"):
        return "", ""
    url = normalize_url(urljoin(base_url, link["href"]))
    access_type = (link.get("title") or link.get_text(" ", strip=True) or "").strip()
    return url, access_type


# ── Study detail hydration ───────────────────────────────────────────────────
def parse_study_detail(
    session: requests.Session,
    study_row: Dict[str, str],
    timeout: int,
    strict: bool = False,
    debug_html_dir: Optional[Path] = None,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    url = study_row["url"]
    main_soup = fetch_soup(session, url, timeout)
    if not main_soup:
        return study_row, []

    if debug_html_dir:
        debug_html_dir.mkdir(parents=True, exist_ok=True)
        (debug_html_dir / f"{study_row['study_id']}_main.html").write_text(
            str(main_soup), encoding="utf-8"
        )

    get_microdata_url, data_access_type = extract_microdata_fields(main_soup, url)
    base = url.rstrip("/")
    study_desc_soup = fetch_soup(session, f"{base}/study-description", timeout)
    data_dict_soup  = fetch_soup(session, f"{base}/data_dictionary", timeout)
    related_soup    = fetch_soup(session, f"{base}/related_materials", timeout)

    study_row["get_microdata_url"] = get_microdata_url
    study_row["data_access_type"]  = data_access_type

    study_row["study_description"] = dedupe_repeated_segments(
        extract_tab_text(study_desc_soup) if study_desc_soup
        else extract_section_by_heading(main_soup, ["study description"])
    )
    study_row["data_description"] = dedupe_repeated_segments(
        extract_tab_text(data_dict_soup) if data_dict_soup
        else extract_section_by_heading(main_soup, ["data description"])
    )
    study_row["documentation"] = dedupe_repeated_segments(
        extract_tab_text(related_soup) if related_soup
        else extract_section_by_heading(main_soup, ["documentation", "documents", "resources"])
    )

    core = extract_study_core_fields(study_row["study_description"])

    # Fallback: try main page text for any missing core fields
    main_text = extract_tab_text(main_soup)
    fallback = extract_study_core_fields(main_text)
    for key, val in fallback.items():
        if not core.get(key) and val:
            core[key] = val

    for key, val in core.items():
        study_row[key] = val

    study_row["data_description_summary"] = full_text(study_row["data_description"])
    study_row["documentation_summary"] = ""

    # Resources
    resources: List[Dict[str, str]] = []
    best: Dict[str, Dict[str, str]] = {}
    for anchor in (related_soup or main_soup).find_all("a", href=True):
        abs_url = normalize_url(urljoin(url, anchor["href"]))
        if not is_allowed_domain(abs_url) or not is_resource_link(abs_url):
            continue
        text_label  = anchor.get_text(" ", strip=True)
        title_label = (anchor.get("title") or "").strip()
        label = title_label if title_label else text_label
        score = (3 if "." in label else 0) + (3 if label.lower().endswith(".pdf") else 0) + (1 if label else 0)
        cur = best.get(abs_url)
        if cur is None or score > int(cur["score"]):
            best[abs_url] = {
                "score": str(score),
                "label": label,
                "filename": title_label or urlparse(abs_url).path.split("/")[-1] or "",
            }

    for abs_url, info in best.items():
        rtype = detect_resource_type(abs_url, info["label"] or info["filename"])
        flags = join_flags(
            (["missing_label"] if not info["label"] else [])
            + (["missing_filename"] if not info["filename"] else [])
            + (["generic_resource_type"] if rtype == "file" else [])
        )
        resources.append({
            "study_id": study_row["study_id"],
            "type":     rtype,
            "name":     info["filename"] or info["label"],
            "label":    info["label"],
            "url":      abs_url,
            "filename": info["filename"],
            "quality_flags": flags,
        })

    study_row["documentation_summary"] = build_documentation_summary(
        study_row["documentation"], resources
    )

    if strict:
        apply_strict_row_quality_fixes(study_row)

    study_row["resource_count"] = str(len(resources))

    # Study quality flags
    required = {
        "country": "missing_country",
        "study_type": "missing_study_type",
        "abstract": "missing_abstract",
        "geographic_coverage": "missing_geographic_coverage",
        "production_date": "missing_production_date",
        "get_microdata_url": "missing_get_microdata_url",
        "data_access_type": "missing_data_access_type",
        "data_description_summary": "missing_data_description_summary",
    }
    study_flags = [flag for field, flag in required.items() if not (study_row.get(field) or "").strip()]
    if not resources:
        study_flags.append("no_resources_found")
    study_row["quality_flags"] = join_flags(study_flags)

    # Provenance
    study_row["ingested_at"]    = str(date.today())
    study_row["source_adapter"] = "nisr_crawl"

    return study_row, resources


# ── Quality report ───────────────────────────────────────────────────────────
def build_quality_report_rows(
    studies: List[Dict[str, str]],
    resources: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    res_flags_by_study: Dict[str, Set[str]] = {}
    for r in resources:
        sid = r.get("study_id", "")
        res_flags_by_study.setdefault(sid, set())
        for f in filter(None, (r.get("quality_flags") or "").split(";")):
            res_flags_by_study[sid].add(f)

    rows = []
    for s in studies:
        study_flags = [f for f in (s.get("quality_flags") or "").split(";") if f]
        extra: List[str] = []
        abstract = clean_whitespace(s.get("abstract", ""))
        if abstract and len(abstract) < 60:
            extra.append("short_abstract")
        if abstract and not re.search(r"[.!?]$", abstract):
            extra.append("abstract_no_terminal_punctuation")
        for field in ["overview_summary", "data_description_summary", "documentation_summary"]:
            if "..." in (s.get(field) or ""):
                extra.append(f"{field}_contains_ellipsis")
        sid = s.get("study_id", "")
        rows.append({
            "study_id":             sid,
            "title":                s.get("title", ""),
            "quality_flags":        join_flags(study_flags + extra),
            "missing_field_count":  str(len(study_flags) + len(extra)),
            "resource_count":       s.get("resource_count", "0"),
            "resource_quality_flags": ";".join(sorted(res_flags_by_study.get(sid, set()))),
        })
    return rows


# ── CSV writer ───────────────────────────────────────────────────────────────
def write_csv(
    path: Path,
    columns: Sequence[str],
    rows: Iterable[Dict[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(columns),
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in columns})


# ── Main crawl loop ──────────────────────────────────────────────────────────
def crawl(config: CrawlConfig) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    session = build_session()

    # IDs to skip: existing catalog + checkpoint from previous interrupted run
    existing_ids  = load_existing_study_ids(EXISTING_DATA)
    checkpoint_ids = load_checkpoint(CHECKPOINT_FILE)
    skip_ids = existing_ids | checkpoint_ids
    logging.info("Will skip %d study IDs (existing + checkpoint)", len(skip_ids))

    catalog_pages = fetch_catalog_pages(
        session=session,
        seed_url=config.seed_url,
        max_pages=config.max_pages,
        timeout=config.timeout,
        delay_seconds=config.delay_seconds,
    )

    # Collect cards — filtered and deduplicated
    all_cards: List[Dict[str, str]] = []
    seen_ids: Set[str] = set(skip_ids)
    for page_no, page_url, soup in catalog_pages:
        cards = parse_study_cards(soup, page_url, page_no, skip_ids=seen_ids)
        for card in cards:
            if card["study_id"] not in seen_ids:
                seen_ids.add(card["study_id"])
                all_cards.append(card)
                if len(all_cards) >= config.max_studies:
                    break
        if len(all_cards) >= config.max_studies:
            break

    logging.info(
        "Found %d new gender-relevant study cards to hydrate (filtered from NISR catalog)",
        len(all_cards),
    )

    if config.dry_run:
        for c in all_cards:
            print(f"  [{c['study_id']}] {c['title'][:80]}")
        print(f"\n[dry-run] Would hydrate {len(all_cards)} studies. No files written.")
        return [], []

    debug_dir = config.output_dir / "debug-html" if config.debug_html else None
    hydrated: List[Dict[str, str]] = []
    all_resources: List[Dict[str, str]] = []
    completed_ids: Set[str] = set(checkpoint_ids)

    for i, study in enumerate(all_cards, start=1):
        parsed, resources = parse_study_detail(
            session=session,
            study_row=study,
            timeout=config.timeout,
            strict=config.strict,
            debug_html_dir=debug_dir,
        )
        hydrated.append(parsed)
        all_resources.extend(resources)
        completed_ids.add(study["study_id"])

        logging.info(
            "[%d/%d] %s resources | %s",
            i, len(all_cards), len(resources), study["url"],
        )

        # Save checkpoint every 10 studies so a crash loses minimal work
        if i % 10 == 0:
            save_checkpoint(CHECKPOINT_FILE, completed_ids)

        if config.delay_seconds > 0:
            time.sleep(config.delay_seconds)

    # Final checkpoint save then clear (clean run finished)
    save_checkpoint(CHECKPOINT_FILE, completed_ids)

    return hydrated, all_resources


# ── Entry point ──────────────────────────────────────────────────────────────
def parse_args() -> CrawlConfig:
    parser = argparse.ArgumentParser(
        description="Crawl NISR Rwanda catalog for gender-relevant studies."
    )
    parser.add_argument("--seed-url",     default=CATALOG_SEED_URL)
    parser.add_argument("--max-pages",    type=int,   default=20,
                        help="Max catalog listing pages to visit (default: 20 = full catalog)")
    parser.add_argument("--max-studies",  type=int,   default=2000,
                        help="Max new studies to hydrate per run")
    parser.add_argument("--delay-seconds", type=float, default=0.5,
                        help="Polite delay between requests (default: 0.5s)")
    parser.add_argument("--timeout",      type=int,   default=20)
    parser.add_argument("--output-dir",   type=Path,  default=OUTPUT_DIR)
    parser.add_argument("--debug-html",   action="store_true",
                        help="Save raw HTML for each study (debugging)")
    parser.add_argument("--strict",       action="store_true",
                        help="Apply strict quality fixes to abstracts and summaries")
    parser.add_argument("--dry-run",      action="store_true",
                        help="List matching studies without fetching or writing")
    args = parser.parse_args()
    return CrawlConfig(
        seed_url=args.seed_url,
        max_pages=max(1, args.max_pages),
        max_studies=max(1, args.max_studies),
        delay_seconds=max(0.0, args.delay_seconds),
        timeout=max(1, args.timeout),
        output_dir=args.output_dir,
        debug_html=args.debug_html,
        strict=args.strict,
        dry_run=args.dry_run,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = parse_args()

    studies, resources = crawl(config)
    if not studies:
        return

    write_csv(config.output_dir / "studies.csv",          STUDIES_COLUMNS,       studies)
    write_csv(config.output_dir / "study_resources.csv",  RESOURCES_COLUMNS,     resources)
    write_csv(config.output_dir / "quality_report.csv",   QUALITY_REPORT_COLUMNS,
              build_quality_report_rows(studies, resources))

    logging.info("Wrote %d studies  → %s", len(studies),   config.output_dir / "studies.csv")
    logging.info("Wrote %d resources → %s", len(resources), config.output_dir / "study_resources.csv")
    logging.info("Next step: python data_pipeline/build_dataset.py")

    # Clear checkpoint — successful full run
    clear_checkpoint(CHECKPOINT_FILE)


if __name__ == "__main__":
    main()
