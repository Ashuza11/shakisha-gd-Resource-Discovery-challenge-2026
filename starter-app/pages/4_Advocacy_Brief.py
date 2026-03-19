from __future__ import annotations

import os

import streamlit as st

from src.ai import advocacy_brief
from src.loaders import load_all_data
from src.quality_badges import parse_quality_flags, quality_level

st.set_page_config(page_title="Shakisha — Advocacy Brief", layout="wide")

AI_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())

studies, resources, quality = load_all_data()

st.title("Advocacy Brief Generator")
st.caption("Select a study to generate an AI-powered policy brief ready for advocacy use.")

if not AI_AVAILABLE:
    st.warning(
        "AI features require an Anthropic API key. "
        "Set `ANTHROPIC_API_KEY` in your environment to enable brief generation."
    )

# ── Study selector ─────────────────────────────────────────────────────────────
# Pre-select from session_state if user clicked "Generate brief →" on Discovery page
pre_selected = st.session_state.get("selected_study_id", None)

study_options = studies[["study_id", "title"]].copy()
id_to_title = dict(zip(study_options["study_id"], study_options["title"]))

if pre_selected and pre_selected in id_to_title:
    default_index = list(id_to_title.keys()).index(pre_selected)
else:
    default_index = 0

selected_id = st.selectbox(
    "Choose a study",
    options=list(id_to_title.keys()),
    format_func=lambda sid: id_to_title.get(sid, str(sid)),
    index=default_index,
)

# Clear session state after use
if "selected_study_id" in st.session_state:
    del st.session_state["selected_study_id"]

# ── Load selected study data ───────────────────────────────────────────────────
study_row = studies[studies["study_id"] == selected_id].iloc[0].to_dict()
study_resources = resources[resources["study_id"] == selected_id].to_dict("records")
quality_row = quality[quality["study_id"] == selected_id]

# ── Study metadata panel ───────────────────────────────────────────────────────
st.divider()
col_meta, col_quality = st.columns([3, 1])

with col_meta:
    st.subheader(str(study_row.get("title", "Untitled")))
    st.caption(
        f"{study_row.get('organization', '—')} · "
        f"{study_row.get('year', '—')} · "
        f"Coverage: {study_row.get('geographic_coverage', 'Rwanda')}"
    )
    abstract = str(study_row.get("abstract", ""))
    if abstract and abstract != "nan":
        with st.expander("Abstract", expanded=True):
            st.write(abstract[:600] + ("…" if len(abstract) > 600 else ""))

with col_quality:
    if not quality_row.empty:
        missing = int(quality_row.iloc[0]["missing_field_count"])
        level = quality_level(missing)
        BADGE = {"good": "🟢", "warning": "🟡", "critical": "🔴"}
        LABEL = {"good": "Good quality", "warning": "Some missing fields", "critical": "Missing critical fields"}
        st.metric("Quality", f"{BADGE[level]} {LABEL[level]}")
        st.metric("Missing fields", missing)
        flags = parse_quality_flags(str(quality_row.iloc[0].get("quality_flags", "")))
        if flags:
            st.caption("**Caveats:**")
            for f in flags:
                st.caption(f"• {f}")

    # Resources
    st.metric("Resources", len(study_resources))
    if study_resources:
        types = sorted({str(r.get("type", "")).lower() for r in study_resources if r.get("type")})
        st.caption("Types: " + ", ".join(types))

    # Source links
    url = study_row.get("url", "")
    microdata_url = study_row.get("get_microdata_url", "")
    if url:
        st.link_button("View source →", url, use_container_width=True)
    if microdata_url:
        st.link_button("Get microdata →", microdata_url, use_container_width=True)

# ── Brief generation ───────────────────────────────────────────────────────────
st.divider()

if not AI_AVAILABLE:
    st.stop()

if st.button("Generate Advocacy Brief", type="primary", use_container_width=False):
    with st.spinner("Generating policy brief..."):
        try:
            brief = advocacy_brief(study_row, study_resources)
            st.session_state["current_brief"] = brief
            st.session_state["brief_study_id"] = selected_id
        except Exception as e:
            st.error(f"Brief generation failed: {e}")
            st.stop()

# ── Render brief ───────────────────────────────────────────────────────────────
brief = st.session_state.get("current_brief")
brief_study = st.session_state.get("brief_study_id")

if brief and brief_study == selected_id:
    st.subheader("Advocacy Brief")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Policy Context")
        st.write(brief.get("policy_context", "—"))

        st.markdown("#### Key Findings")
        findings = brief.get("key_findings", "")
        st.markdown(findings)

    with col2:
        st.markdown("#### Data Gaps")
        st.write(brief.get("data_gaps", "—"))

        st.markdown("#### Recommended Action")
        st.info(brief.get("recommended_action", "—"))

    st.divider()
    st.markdown("#### Citation")
    citation = brief.get("citation", "")
    st.code(citation, language=None)

    # ── Export ─────────────────────────────────────────────────────────────────
    title = str(study_row.get("title", "study"))
    year = str(study_row.get("year", ""))
    org = str(study_row.get("organization", ""))

    brief_text = f"""ADVOCACY BRIEF
{'=' * 60}
{title} ({year})
{org}

POLICY CONTEXT
{brief.get('policy_context', '')}

KEY FINDINGS
{brief.get('key_findings', '')}

DATA GAPS
{brief.get('data_gaps', '')}

RECOMMENDED ACTION
{brief.get('recommended_action', '')}

CITATION
{brief.get('citation', '')}
{'=' * 60}
Generated by Shakisha — AI-Powered Gender Data Discovery Platform
GRB Hackathon 2026
"""
    st.download_button(
        label="Download brief as .txt",
        data=brief_text,
        file_name=f"shakisha_brief_{selected_id}.txt",
        mime="text/plain",
    )
