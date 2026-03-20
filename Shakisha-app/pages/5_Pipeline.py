from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Paths ────────────────────────────────────────────────────────────────────
_APP_ROOT = Path(__file__).resolve().parent.parent
_FULL_DIR = _APP_ROOT / "data" / "full"

SOURCES = [
    {
        "key":     "nisr_base",
        "name":    "NISR Microdata Catalog",
        "dir":     None,          # lives directly in data/full/ — it IS the base
        "adapter": None,
        "description": (
            "Authoritative base: Rwanda's national statistical microdata catalog "
            "from the National Institute of Statistics Rwanda (NISR). "
            "Covers Labour, Agriculture, Household, Health, Population, and Finance surveys."
        ),
        "run_cmd": "# NISR base is the authoritative seed — no adapter needed",
        "badge":   "🟢 Authoritative base",
    },
    {
        "key":     "nisr_crawl",
        "name":    "NISR Crawler (incremental)",
        "dir":     _APP_ROOT / "data" / "pipeline_sources" / "nisr_crawl",
        "adapter": "data_pipeline/nisr_crawler.py",
        "description": (
            "Crawls the live NISR catalog for new gender-relevant studies added since the "
            "last run. Skips any study already in the base catalog. "
            "Filters by gender, labour, agriculture, and household keywords."
        ),
        "run_cmd": "python data_pipeline/nisr_crawler.py",
        "badge":   "🔄 Incremental crawler",
    },
    {
        "key":     "openalex",
        "name":    "OpenAlex Research Papers",
        "dir":     _APP_ROOT / "data" / "pipeline_sources" / "openalex",
        "adapter": "data_pipeline/openalex_adapter.py",
        "description": (
            "Open-access academic papers on Rwanda gender, labour, agriculture, and land "
            "rights from OpenAlex (no API key required). "
            "Adds peer-reviewed research alongside official survey microdata."
        ),
        "run_cmd": "python data_pipeline/openalex_adapter.py",
        "badge":   "📖 Academic papers",
    },
    {
        "key":     "worldbank",
        "name":    "World Bank Open Data",
        "dir":     _APP_ROOT / "data" / "pipeline_sources" / "worldbank",
        "adapter": "data_pipeline/worldbank_adapter.py",
        "description": (
            "Rwanda gender indicators from the World Bank Open Data API — "
            "female labour force participation, gender parity in education, "
            "women in business and law indexes."
        ),
        "run_cmd": "python data_pipeline/worldbank_adapter.py",
        "badge":   "🏦 Coming soon",
    },
    {
        "key":     "ilo",
        "name":    "ILO ILOSTAT",
        "dir":     _APP_ROOT / "data" / "pipeline_sources" / "ilo",
        "adapter": "data_pipeline/ilo_adapter.py",
        "description": (
            "Rwanda labour statistics from the ILO ILOSTAT database — "
            "employment by sex, wages, child labour, and decent work indicators."
        ),
        "run_cmd": "python data_pipeline/ilo_adapter.py",
        "badge":   "⚙️ Coming soon",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _read_source_csv(directory: Path | None, filename: str) -> pd.DataFrame:
    if directory is None or not directory.exists():
        return pd.DataFrame()
    path = directory / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str)
    except Exception:
        return pd.DataFrame()


def _last_ingested(df: pd.DataFrame) -> str:
    if df.empty or "ingested_at" not in df.columns:
        return "—"
    dates = df["ingested_at"].dropna()
    return dates.max() if not dates.empty else "—"


def _source_stats(src: dict) -> dict:
    """Return study count, resource count, and last ingested date for a source."""
    if src["key"] == "nisr_base":
        studies = _read_source_csv(_FULL_DIR, "studies.csv")
        # Base = rows WITHOUT source_adapter set (original NISR rows)
        if "source_adapter" in studies.columns:
            base = studies[studies["source_adapter"].fillna("") == ""]
        else:
            base = studies
        return {
            "study_count":    len(base),
            "resource_count": "—",
            "last_ingested":  "Built-in",
            "active":         True,
        }

    studies   = _read_source_csv(src["dir"], "studies.csv")
    resources = _read_source_csv(src["dir"], "study_resources.csv")
    return {
        "study_count":    len(studies) if not studies.empty else 0,
        "resource_count": len(resources) if not resources.empty else 0,
        "last_ingested":  _last_ingested(studies),
        "active":         not studies.empty,
    }


def _merged_stats() -> dict:
    studies   = _read_source_csv(_FULL_DIR, "studies.csv")
    resources = _read_source_csv(_FULL_DIR, "study_resources.csv")
    new_today = 0
    if not studies.empty and "ingested_at" in studies.columns:
        new_today = (studies["ingested_at"].fillna("") == str(date.today())).sum()
    return {
        "total_studies":   len(studies),
        "total_resources": len(resources),
        "new_today":       new_today,
    }


# ── Page ──────────────────────────────────────────────────────────────────────
st.markdown("## 🔄 Data Pipeline")
st.caption(
    "Shakisha ships with the NISR microdata catalog as the authoritative base. "
    "The pipeline layer ingests OpenAlex, World Bank, ILO, and FAO on demand — "
    "keeping the catalog current without manual data entry."
)

# ── Top metrics ───────────────────────────────────────────────────────────────
merged = _merged_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total studies", f"{merged['total_studies']:,}")
c2.metric("Total resources", f"{merged['total_resources']:,}")
c3.metric("Active sources", sum(1 for s in SOURCES if _source_stats(s)["active"]))
c4.metric("Added today", merged["new_today"])

st.divider()

# ── Source cards ──────────────────────────────────────────────────────────────
st.subheader("Data sources")

for src in SOURCES:
    stats = _source_stats(src)
    active = stats["active"]

    with st.container(border=True):
        col_info, col_stats = st.columns([3, 1])

        with col_info:
            st.markdown(f"**{src['name']}** &nbsp; `{src['badge']}`")
            st.caption(src["description"])
            if src["adapter"]:
                st.code(src["run_cmd"], language="bash")

        with col_stats:
            if active:
                st.metric("Studies", f"{stats['study_count']:,}")
                if stats["resource_count"] != "—":
                    st.metric("Resources", f"{stats['resource_count']:,}")
                st.caption(f"Last run: {stats['last_ingested']}")
            else:
                st.markdown("&nbsp;")
                st.info("Not yet run" if src["key"] not in ("worldbank", "ilo") else "Coming soon")

st.divider()

# ── How to refresh ────────────────────────────────────────────────────────────
st.subheader("How to refresh the catalog")
st.markdown(
    "Run the adapters for whichever sources have new data, then merge into the app catalog. "
    "The NISR crawler automatically skips studies already in the catalog."
)
st.code(
    """\
# 1. Crawl new NISR studies (skips existing ones automatically)
python data_pipeline/nisr_crawler.py

# 2. Fetch latest OpenAlex research papers
python data_pipeline/openalex_adapter.py

# 3. Merge all sources into the live catalog
python data_pipeline/build_dataset.py

# Restart the app to reflect the updated catalog
""",
    language="bash",
)

st.divider()

# ── Recently added studies ────────────────────────────────────────────────────
st.subheader("Recently added studies")
studies_df = _read_source_csv(_FULL_DIR, "studies.csv")

if not studies_df.empty and "ingested_at" in studies_df.columns:
    recent = (
        studies_df[studies_df["ingested_at"].notna() & (studies_df["ingested_at"] != "")]
        .sort_values("ingested_at", ascending=False)
        .head(20)
    )
    if recent.empty:
        st.caption("No pipeline-ingested studies yet — base NISR catalog studies predate the ingested_at column.")
    else:
        for _, row in recent.iterrows():
            col_title, col_meta = st.columns([4, 1])
            with col_title:
                st.markdown(f"**{row.get('title', 'Untitled')}**")
                st.caption(
                    f"{row.get('organization', '—')} · "
                    f"{row.get('year', '—')} · "
                    f"Source: {row.get('source_adapter', '—')}"
                )
            with col_meta:
                st.caption(f"Added {row.get('ingested_at', '—')}")
else:
    st.caption("Run the pipeline to see recently added studies here.")
