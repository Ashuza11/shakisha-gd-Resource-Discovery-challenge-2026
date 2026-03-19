from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from src.ai import explain_study, interpret_query
from src.domains import DOMAINS, filter_by_domain, get_active_domains
from src.filters import apply_study_filters, filter_resources_by_type
from src.loaders import get_data_dir, load_all_data
from src.quality_badges import parse_quality_flags, quality_level

st.set_page_config(page_title="Shakisha — Discovery", layout="wide")

# ── Load data ──────────────────────────────────────────────────────────────────
studies, resources, quality = load_all_data()
quality_map = (
    quality[["study_id", "quality_flags", "missing_field_count"]]
    .rename(columns={"quality_flags": "q_flags", "missing_field_count": "q_missing"})
)

AI_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/180x50/1a1a2e/ffffff?text=Shakisha", use_column_width=True)
    st.markdown("### 🔍 Shakisha")
    st.caption("Gender Data Discovery · Rwanda")
    st.divider()

    # Domain selector
    st.markdown("#### Domain")

    active = get_active_domains()
    domain_options = list(active.keys())
    domain_labels = {k: f"{v['emoji']} {v['name']}" for k, v in active.items()}

    selected_domain = st.selectbox(
        "Active domain",
        options=domain_options,
        format_func=lambda k: domain_labels.get(k, k),
        help="Domains are added one at a time as data is validated.",
    )

    domain_cfg = DOMAINS[selected_domain]
    st.caption(domain_cfg["description"])

    # Coming soon / planned domains
    other_domains = {k: v for k, v in DOMAINS.items() if v["status"] != "active"}
    if other_domains:
        with st.expander("More domains (coming soon)", expanded=False):
            for key, cfg in other_domains.items():
                status_badge = "🔜" if cfg["status"] == "coming_soon" else "📋"
                st.caption(f"{status_badge} {cfg['emoji']} **{cfg['name']}** — {cfg['study_count_hint']} studies")

    st.divider()
    st.markdown("#### Filters")
    year_min = st.number_input("Year from", value=2000, step=1)
    year_max = st.number_input("Year to", value=2026, step=1)
    resource_type = st.selectbox(
        "Resource type",
        ["all"] + sorted(
            resources["type"].fillna("unknown").astype(str).str.lower().unique().tolist()
        ),
    )
    quality_filter = st.selectbox("Quality level", ["all", "good", "warning", "critical"])
    st.divider()
    ai_status = "✅ Enabled" if AI_AVAILABLE else "⚠️ Disabled — set ANTHROPIC_API_KEY"
    st.caption(f"AI search: {ai_status}")

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown(f"## {domain_cfg['emoji']} {domain_cfg['name']} — Discovery")
st.caption(
    f"Catalog: `{get_data_dir()}` · "
    f"Showing studies in **{domain_cfg['name']}** · "
    f"AI search is {'**enabled**' if AI_AVAILABLE else '**disabled**'}"
)

# Advocacy context callout
st.info(f"**Advocacy focus:** {domain_cfg['advocacy_context']}")

# ── Search bar ─────────────────────────────────────────────────────────────────
query = st.text_input(
    "Search the catalog",
    placeholder="e.g. women's workforce participation after 2019",
    help=(
        "Type a plain-language question or keywords. AI will interpret your intent."
        if AI_AVAILABLE
        else "Keyword search across titles and abstracts."
    ),
)

# ── Domain pre-filter ──────────────────────────────────────────────────────────
domain_mask = filter_by_domain(studies["title"].tolist(), selected_domain)
domain_studies = studies[domain_mask].copy()

# ── AI query interpretation ────────────────────────────────────────────────────
ai_params: dict = {}
if query.strip() and AI_AVAILABLE:
    with st.spinner("Interpreting your query..."):
        try:
            ai_params = interpret_query(query)
            if ai_params.get("explanation"):
                st.info(f"**Search intent:** {ai_params['explanation']}")
        except Exception as e:
            st.warning(f"AI interpretation unavailable: {e}. Falling back to keyword search.")

# ── Build effective filter params ──────────────────────────────────────────────
effective_query = " ".join(ai_params.get("keywords", [])) if ai_params else query
effective_year_min = ai_params.get("year_min") or int(year_min)
effective_year_max = ai_params.get("year_max") or int(year_max)

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = apply_study_filters(
    domain_studies,
    query=effective_query,
    year_min=effective_year_min,
    year_max=effective_year_max,
)
res_filtered = filter_resources_by_type(resources, resource_type)

# Merge quality info
merged = filtered.merge(quality_map, on="study_id", how="left")
merged["q_missing"] = merged["q_missing"].fillna(0).astype(int)
merged["q_level"] = merged["q_missing"].apply(quality_level)

# Quality level filter
if quality_filter != "all":
    merged = merged[merged["q_level"] == quality_filter]

# Resource count per study
res_count = (
    res_filtered.groupby("study_id", as_index=False)["url"]
    .count()
    .rename(columns={"url": "resource_count"})
)
merged = merged.merge(res_count, on="study_id", how="left")
merged["resource_count"] = merged["resource_count"].fillna(0).astype(int)

# ── Results header ─────────────────────────────────────────────────────────────
total_in_domain = len(domain_studies)
st.subheader(
    f"Results — {len(merged)} of {total_in_domain} "
    f"stud{'y' if total_in_domain == 1 else 'ies'} in {domain_cfg['name']}"
)

if merged.empty:
    st.info("No studies match your search. Try broadening the year range or changing keywords.")
    st.stop()

# ── Quality badge helpers ──────────────────────────────────────────────────────
BADGE = {"good": "🟢", "warning": "🟡", "critical": "🔴"}
LABEL = {"good": "Good quality", "warning": "Some missing fields", "critical": "Missing critical fields"}


def render_card(row: dict, study_resources: list[dict]) -> None:
    level = row.get("q_level", "warning")
    badge = BADGE.get(level, "⚪")
    label = LABEL.get(level, "Unknown")
    flags = parse_quality_flags(str(row.get("q_flags", "")))
    study_url = row.get("url", "")
    microdata_url = row.get("get_microdata_url", "")
    org = row.get("organization", "Unknown organization")
    year = row.get("year", "—")
    title = row.get("title", "Untitled")
    resource_count = row.get("resource_count", 0)
    geo = row.get("geographic_coverage", "")

    with st.container(border=True):
        col_title, col_badge = st.columns([5, 1])

        with col_title:
            st.markdown(f"**{title}**")
            meta_parts = [str(org), str(year)]
            if geo and geo != "nan":
                meta_parts.append(str(geo))
            meta_parts.append(f"{resource_count} resource{'s' if resource_count != 1 else ''}")
            st.caption(" · ".join(meta_parts))

        with col_badge:
            st.markdown(f"{badge} **{label}**")
            if flags:
                with st.expander("Caveats", expanded=False):
                    for f in flags:
                        st.caption(f"• {f}")

        # AI relevance explanation (lazy — only on demand)
        if query.strip() and AI_AVAILABLE:
            with st.expander("Why is this relevant?", expanded=False):
                with st.spinner("Generating explanation..."):
                    try:
                        explanation = explain_study(dict(row), query)
                        st.write(explanation)
                    except Exception:
                        st.caption("AI explanation unavailable.")

        # Abstract snippet
        abstract = str(row.get("abstract", ""))
        if abstract and abstract not in ("", "nan"):
            st.caption(abstract[:280] + ("…" if len(abstract) > 280 else ""))

        # Action row
        btn_col1, btn_col2, btn_col3, _ = st.columns([2, 2, 2, 2])
        with btn_col1:
            if study_url:
                st.link_button("View source", study_url, use_container_width=True)
        with btn_col2:
            if microdata_url:
                st.link_button("Get microdata", microdata_url, use_container_width=True)
        with btn_col3:
            if st.button("Generate brief →", key=f"brief_{row['study_id']}", use_container_width=True):
                st.session_state["selected_study_id"] = row["study_id"]
                st.switch_page("pages/4_Advocacy_Brief.py")


# ── Render cards ───────────────────────────────────────────────────────────────
for _, row in merged.iterrows():
    study_res = res_filtered[res_filtered["study_id"] == row["study_id"]].to_dict("records")
    render_card(row.to_dict(), study_res)
