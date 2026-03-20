from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from datetime import datetime

from src.link_checker import check_url
from src.loaders import get_data_dir, load_all_data
from src.quality_badges import parse_quality_flags, quality_level

# ── Load data ──────────────────────────────────────────────────────────────────
studies, resources, quality = load_all_data()
quality = quality.copy()
quality["missing_field_count"] = quality["missing_field_count"].fillna(0).astype(int)
quality["q_level"] = quality["missing_field_count"].apply(quality_level)
quality["parsed_flags"] = quality["quality_flags"].fillna("").apply(parse_quality_flags)

st.title("Data Quality")
st.caption(f"Data source: `{get_data_dir()}`")

# ── Summary metrics ────────────────────────────────────────────────────────────
total = len(quality)
good = (quality["q_level"] == "good").sum()
warning = (quality["q_level"] == "warning").sum()
critical = (quality["q_level"] == "critical").sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Studies", total)
c2.metric("🟢 Good", int(good))
c3.metric("🟡 Warning", int(warning))
c4.metric("🔴 Critical", int(critical))

st.divider()

# ── Missing fields bar chart ───────────────────────────────────────────────────
st.subheader("Missing field counts per study")
fig_missing = px.bar(
    quality.sort_values("missing_field_count", ascending=False).head(30),
    x="title",
    y="missing_field_count",
    color="q_level",
    color_discrete_map={"good": "#4CAF50", "warning": "#FFC107", "critical": "#F44336"},
    labels={"title": "Study", "missing_field_count": "Missing fields", "q_level": "Quality"},
)
fig_missing.update_layout(
    xaxis=dict(showticklabels=False),
    margin=dict(t=20, b=20),
)
st.plotly_chart(fig_missing, use_container_width=True)

st.divider()

# ── Quality table with visual badges ──────────────────────────────────────────
st.subheader("Quality overview")

BADGE = {"good": "🟢", "warning": "🟡", "critical": "🔴"}

display = quality[["study_id", "title", "missing_field_count", "q_level", "parsed_flags"]].copy()
display["Quality"] = display["q_level"].map(BADGE) + " " + display["q_level"].str.capitalize()
display["Caveats"] = display["parsed_flags"].apply(
    lambda flags: " · ".join(flags) if flags else "None"
)
display = display.rename(columns={
    "study_id": "ID",
    "title": "Study",
    "missing_field_count": "Missing fields",
}).drop(columns=["q_level", "parsed_flags"])

st.dataframe(
    display[["ID", "Study", "Missing fields", "Quality", "Caveats"]],
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Link checker ───────────────────────────────────────────────────────────────
st.subheader("Source link checker")
st.caption("Validate whether study URLs are currently reachable. Select studies to check.")

study_options = studies[["study_id", "title", "url"]].dropna(subset=["url"])
selected_ids = st.multiselect(
    "Select studies to check",
    options=study_options["study_id"].tolist(),
    format_func=lambda sid: study_options.loc[study_options["study_id"] == sid, "title"].values[0]
    if sid in study_options["study_id"].values else str(sid),
    max_selections=10,
    help="Maximum 10 studies per check to avoid timeouts.",
)

if st.button("Check links", disabled=not selected_ids):
    rows_to_check = study_options[study_options["study_id"].isin(selected_ids)]
    results = []
    progress = st.progress(0)
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, (_, row) in enumerate(rows_to_check.iterrows()):
        status, code = check_url(row["url"])
        STATUS_BADGE = {
            "available": "🟢 Available",
            "error": "🔴 Error",
            "unreachable": "🔴 Unreachable",
            "invalid": "⚪ Invalid URL",
        }
        results.append({
            "Study": row["title"],
            "URL": row["url"],
            "Status": STATUS_BADGE.get(status, status),
            "HTTP code": code if code else "—",
            "Checked at": checked_at,
        })
        progress.progress((i + 1) / len(rows_to_check))
    progress.empty()
    st.caption(f"Last checked: {checked_at}")
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
