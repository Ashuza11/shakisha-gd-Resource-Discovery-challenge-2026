from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.domains import DOMAINS, filter_by_domain, get_active_domains
from src.loaders import get_data_dir, load_all_data
from src.quality_badges import quality_level

# ── Load data ──────────────────────────────────────────────────────────────────
studies, resources, quality = load_all_data()
studies["year_num"] = pd.to_numeric(studies.get("year"), errors="coerce")
quality["q_missing"] = quality["missing_field_count"].fillna(0).astype(int)
quality["q_level"] = quality["q_missing"].apply(quality_level)

# ── Sidebar branding + domain selector ────────────────────────────────────────
with st.sidebar:
    active = get_active_domains()
    domain_options = list(active.keys())

    if st.session_state.get("selected_domain") not in domain_options:
        st.session_state["selected_domain"] = domain_options[0]

    selected_domain = st.selectbox(
        "Domain",
        options=domain_options,
        format_func=lambda k: f"{DOMAINS[k]['emoji']} {DOMAINS[k]['name']}",
        key="selected_domain",
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

st.divider()

# ── Rwanda district coverage map ───────────────────────────────────────────────
st.subheader("Geographic coverage — Rwanda districts")
st.caption("Study coverage mapped across Rwanda's 30 districts and 5 provinces.")

# District centroids (lat, lon, province)
DISTRICT_CENTROIDS = [
    ("Nyarugenge", -1.9441, 30.0619, "Kigali"),
    ("Gasabo",     -1.8667, 30.1167, "Kigali"),
    ("Kicukiro",   -2.0000, 30.1000, "Kigali"),
    ("Burera",     -1.3500, 29.8500, "Northern"),
    ("Gakenke",    -1.7000, 29.7500, "Northern"),
    ("Gicumbi",    -1.5500, 30.0833, "Northern"),
    ("Musanze",    -1.4996, 29.6340, "Northern"),
    ("Rulindo",    -1.7333, 30.1167, "Northern"),
    ("Gisagara",   -2.6000, 29.8167, "Southern"),
    ("Huye",       -2.5953, 29.7396, "Southern"),
    ("Kamonyi",    -2.0167, 29.8833, "Southern"),
    ("Muhanga",    -2.0833, 29.7667, "Southern"),
    ("Nyamagabe",  -2.4667, 29.5500, "Southern"),
    ("Nyanza",     -2.3500, 29.7500, "Southern"),
    ("Nyaruguru",  -2.7167, 29.5833, "Southern"),
    ("Ruhango",    -2.2000, 29.7833, "Southern"),
    ("Bugesera",   -2.2000, 30.2000, "Eastern"),
    ("Gatsibo",    -1.5833, 30.4333, "Eastern"),
    ("Kayonza",    -1.8833, 30.5333, "Eastern"),
    ("Kirehe",     -2.1667, 30.7000, "Eastern"),
    ("Ngoma",      -2.1667, 30.5167, "Eastern"),
    ("Nyagatare",  -1.2833, 30.3167, "Eastern"),
    ("Rwamagana",  -1.9488, 30.4349, "Eastern"),
    ("Karongi",    -2.0833, 29.3667, "Western"),
    ("Ngororero",  -1.8167, 29.5500, "Western"),
    ("Nyabihu",    -1.6167, 29.5000, "Western"),
    ("Nyamasheke", -2.4333, 29.1167, "Western"),
    ("Rubavu",     -1.6823, 29.3609, "Western"),
    ("Rusizi",     -2.4833, 28.9000, "Western"),
    ("Rutsiro",    -1.9167, 29.3167, "Western"),
]

PROVINCE_COLORS = {
    "Kigali":   "#E63946",
    "Northern": "#2A9D8F",
    "Southern": "#E9C46A",
    "Eastern":  "#F4A261",
    "Western":  "#264653",
}


def _parse_province(coverage_text: str) -> str:
    """Return province key from geographic_coverage text, or 'all' for national."""
    if not coverage_text or str(coverage_text).strip().lower() in ("nan", "rwanda", "national", ""):
        return "all"
    t = str(coverage_text).lower()
    if "kigali" in t:
        return "Kigali"
    if "north" in t:
        return "Northern"
    if "south" in t:
        return "Southern"
    if "east" in t:
        return "Eastern"
    if "west" in t:
        return "Western"
    return "all"


# Count studies per province from the domain slice
province_counts: dict[str, int] = {p: 0 for p in PROVINCE_COLORS}
for cov in domain_studies.get("geographic_coverage", pd.Series(dtype=str)).fillna("").astype(str):
    p = _parse_province(cov)
    if p == "all":
        for prov in province_counts:
            province_counts[prov] += 1
    elif p in province_counts:
        province_counts[p] += 1

# Build district dataframe — assign each district its province study count
district_rows = []
for name, lat, lon, province in DISTRICT_CENTROIDS:
    district_rows.append({
        "district": name,
        "lat": lat,
        "lon": lon,
        "province": province,
        "study_count": province_counts.get(province, 0),
    })
district_df = pd.DataFrame(district_rows)

district_df["coverage_label"] = district_df.apply(
    lambda r: f"{r['study_count']} studies cover {r['province']} Province (national surveys include all districts)",
    axis=1,
)

fig_map = px.scatter_mapbox(
    district_df,
    lat="lat",
    lon="lon",
    hover_name="district",
    size="study_count",
    color="province",
    color_discrete_map=PROVINCE_COLORS,
    size_max=28,
    zoom=7.4,
    center={"lat": -1.94, "lon": 29.87},
    hover_data={"lat": False, "lon": False, "study_count": False, "province": True, "coverage_label": True},
    title=f"{domain_cfg['name']} — study coverage by district",
)
fig_map.update_layout(
    mapbox_style="open-street-map",
    height=600,
    margin=dict(t=40, b=10, l=0, r=0),
    legend=dict(title="Province", orientation="v"),
)
st.plotly_chart(fig_map, use_container_width=True)
st.caption(
    "Bubble size = studies covering each province. "
    "Most are national surveys — they cover all 30 districts but are not district-specific. "
    "Use the Discovery page to find studies with district-level disaggregation."
)
