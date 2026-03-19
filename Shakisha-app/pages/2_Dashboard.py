from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.domains import DOMAINS, filter_by_domain, get_active_domains
from src.loaders import get_data_dir, load_all_data
from src.quality_badges import quality_level

st.set_page_config(page_title="Shakisha — Analytics", layout="wide")

# ── Load data ──────────────────────────────────────────────────────────────────
studies, resources, quality = load_all_data()
studies["year_num"] = pd.to_numeric(studies.get("year"), errors="coerce")
quality["q_missing"] = quality["missing_field_count"].fillna(0).astype(int)
quality["q_level"] = quality["q_missing"].apply(quality_level)

# ── Sidebar branding + domain selector ────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Shakisha")
    st.caption("Gender Data Discovery · Rwanda")
    st.divider()
    active = get_active_domains()
    selected_domain = st.selectbox(
        "Domain",
        options=list(active.keys()),
        format_func=lambda k: f"{DOMAINS[k]['emoji']} {DOMAINS[k]['name']}",
    )

domain_cfg = DOMAINS[selected_domain]
domain_mask = filter_by_domain(
    studies["title"].tolist(),
    selected_domain,
    abstracts=studies.get("abstract", studies["title"]).fillna("").tolist(),
)
domain_studies = studies[domain_mask].copy()
domain_studies["year_num"] = pd.to_numeric(domain_studies.get("year"), errors="coerce")

# Filter quality to domain studies only
domain_quality = quality[quality["study_id"].isin(domain_studies["study_id"])]

st.markdown(f"## {domain_cfg['emoji']} {domain_cfg['name']} — Analytics")
st.caption(f"Data source: `{get_data_dir()}` · {len(domain_studies)} studies in this domain")

# ── Top metric cards ───────────────────────────────────────────────────────────
# Domain resources
domain_resource_ids = domain_studies["study_id"].tolist()
domain_resources = resources[resources["study_id"].isin(domain_resource_ids)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Studies (this domain)", len(domain_studies))
c2.metric("Resources (this domain)", len(domain_resources))
good_count = (domain_quality["q_level"] == "good").sum()
c3.metric("High Quality Studies", int(good_count))
year_span = (
    f"{int(domain_studies['year_num'].min())} – {int(domain_studies['year_num'].max())}"
    if not domain_studies["year_num"].isna().all() else "—"
)
c4.metric("Year Coverage", year_span)

st.divider()

# ── Row 1: Studies by year + Coverage gap ─────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Studies by year")
    year_counts = (
        domain_studies.dropna(subset=["year_num"])
        .groupby("year_num", as_index=False)["study_id"]
        .count()
        .rename(columns={"study_id": "count", "year_num": "year"})
    )
    fig_year = px.bar(
        year_counts,
        x="year",
        y="count",
        labels={"year": "Year", "count": "Studies"},
        color_discrete_sequence=["#5B8DB8"],
        title=f"{domain_cfg['name']} — studies per year",
    )
    fig_year.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_year, use_container_width=True)

with col_right:
    st.subheader("Coverage gap — missing years")
    if not domain_studies["year_num"].isna().all():
        min_y = int(domain_studies["year_num"].min())
        max_y = int(domain_studies["year_num"].max())
        all_years = set(range(min_y, max_y + 1))
        covered_years = set(domain_studies["year_num"].dropna().astype(int).tolist())
        gap_years = sorted(all_years - covered_years)
        if gap_years:
            gap_df = pd.DataFrame({"year": gap_years, "gap": [1] * len(gap_years)})
            fig_gap = px.bar(
                gap_df,
                x="year",
                y="gap",
                labels={"year": "Year", "gap": "No data"},
                color_discrete_sequence=["#E07B7B"],
                title="Years with no data in this domain",
            )
            fig_gap.update_layout(yaxis=dict(showticklabels=False), margin=dict(t=40, b=20))
            st.plotly_chart(fig_gap, use_container_width=True)
            st.caption(
                f"{len(gap_years)} year(s) with no studies: "
                f"{', '.join(str(y) for y in gap_years[:10])}"
                f"{'…' if len(gap_years) > 10 else ''}"
            )
        else:
            st.success("No year gaps — all years from the range are covered.")
    else:
        st.info("Year data not available.")

st.divider()

# ── Row 2: Resource types + Quality distribution ───────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Resource types")
    type_counts = (
        domain_resources["type"]
        .fillna("unknown")
        .astype(str)
        .str.lower()
        .value_counts()
        .reset_index()
    )
    type_counts.columns = ["type", "count"]
    fig_types = px.pie(
        type_counts,
        names="type",
        values="count",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Resource types in this domain",
    )
    fig_types.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig_types, use_container_width=True)

with col_right2:
    st.subheader("Data quality distribution")
    level_counts = domain_quality["q_level"].value_counts().reset_index()
    level_counts.columns = ["level", "count"]
    COLOR_MAP = {"good": "#4CAF50", "warning": "#FFC107", "critical": "#F44336"}
    fig_quality = go.Figure(
        go.Pie(
            labels=level_counts["level"],
            values=level_counts["count"],
            marker_colors=[COLOR_MAP.get(l, "#999") for l in level_counts["level"]],
            hole=0.45,
            title=dict(text="Quality"),
        )
    )
    fig_quality.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_quality, use_container_width=True)

st.divider()

# ── Organization breakdown ─────────────────────────────────────────────────────
st.subheader("Studies by organization")
if "organization" in domain_studies.columns:
    org_counts = (
        domain_studies["organization"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )
    org_counts.columns = ["organization", "count"]
    org_counts["org_short"] = org_counts["organization"].apply(
        lambda x: x[:50] + "…" if len(x) > 50 else x
    )
    fig_org = px.bar(
        org_counts,
        x="count",
        y="org_short",
        orientation="h",
        labels={"count": "Studies", "org_short": "Organization"},
        color_discrete_sequence=["#7B9E87"],
    )
    fig_org.update_layout(margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_org, use_container_width=True)
else:
    st.info("Organization data not available.")
