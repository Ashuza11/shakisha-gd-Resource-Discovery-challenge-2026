from __future__ import annotations

import os

import streamlit as st

from src.domains import DOMAINS
from src.loaders import compute_domain_study_counts, load_all_data

# ── Load data for live stats ───────────────────────────────────────────────────
try:
    studies, resources, _ = load_all_data()
    n_studies = len(studies)
    n_resources = len(resources)
    domain_counts = compute_domain_study_counts(studies)
    data_loaded = True
except Exception:
    n_studies = "—"
    n_resources = "—"
    domain_counts = {}
    data_loaded = False

AI_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())

# ── Hero ───────────────────────────────────────────────────────────────────────
col_hero, col_logo = st.columns([3, 1])
with col_hero:
    st.title("🔍 Shakisha")
    st.markdown("##### *Kinyarwanda: \"to search · to discover\"*")
    st.markdown(
        "**AI-powered gender data discovery for Rwanda.** "
        "Find the study you need, understand it instantly, "
        "and turn it into an advocacy brief — in minutes, not hours."
    )
with col_logo:
    st.markdown("")
    st.markdown("")
    st.markdown(
        """
        <div style='text-align:right; color:#888; font-size:0.8em;'>
        Built by<br><strong>Team Shakisha</strong><br>GRB Hackathon 2026<br>Kigali, Rwanda
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Live catalog stats ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Studies in catalog", n_studies)
c2.metric("Total resources", n_resources)
active_count = sum(1 for d in DOMAINS.values() if d["status"] == "active")
c3.metric("Active domains", active_count)
c4.metric("AI search", "✅ On" if AI_AVAILABLE else "⚠️ Off")

st.divider()

# ── Domain roadmap ─────────────────────────────────────────────────────────────
st.subheader("Domain coverage")
st.caption("Domains are validated and added one at a time to ensure data accuracy.")

STATUS_STYLE = {
    "active":      ("🟢", "Active",      "#d4edda", "#155724"),
    "coming_soon": ("🔜", "Coming soon", "#fff3cd", "#856404"),
    "planned":     ("📋", "Planned",     "#f8f9fa", "#6c757d"),
}

cols = st.columns(len(DOMAINS))
for col, (key, cfg) in zip(cols, DOMAINS.items()):
    icon, label, bg, fg = STATUS_STYLE[cfg["status"]]
    count = domain_counts.get(key, cfg["study_count_hint"])
    with col:
        st.markdown(
            f"""
            <div style='background:{bg}; border-radius:8px; padding:12px; text-align:center;'>
                <div style='font-size:1.6em;'>{cfg['emoji']}</div>
                <div style='font-weight:bold; color:{fg}; font-size:0.85em;'>{cfg['name']}</div>
                <div style='color:{fg}; font-size:0.75em;'>{icon} {label}</div>
                <div style='color:#666; font-size:0.7em; margin-top:4px;'>{count} studies</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── How it works ───────────────────────────────────────────────────────────────
st.subheader("How it works")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("### 1️⃣ Choose a domain")
    st.markdown("Select a validated data domain from the sidebar. Each domain contains curated, quality-checked studies from NISR.")
with col2:
    st.markdown("### 2️⃣ Search")
    st.markdown("Type a plain-language question. AI interprets your intent and filters the catalog — no need to guess keywords.")
with col3:
    st.markdown("### 3️⃣ Evaluate")
    st.markdown("Each result shows a **quality badge**, abstract snippet, source link, and an AI explanation of why it's relevant.")
with col4:
    st.markdown("### 4️⃣ Act")
    st.markdown("Click **Generate Brief** to get an AI-written advocacy brief with key findings, data gaps, and a ready-to-cite citation.")

st.divider()

# ── Demo scenario ──────────────────────────────────────────────────────────────
with st.expander("▶ Try this demo scenario", expanded=True):
    st.markdown(
        """
**Scenario:** You are a CSO officer preparing a brief on women's workforce participation for the Ministry of Gender.

1. Open **Discovery** → domain is pre-set to **Labour & Employment**
2. Search: *"women workforce participation Rwanda after 2019"*
3. Review the Rwanda Labour Force Survey results — check quality badge and abstract
4. Click **Generate Brief** → receive a structured advocacy brief in ~10 seconds
5. Download as `.txt` → paste directly into your proposal or policy memo
"""
    )

st.info("👈 Navigate using the sidebar: **Discovery → Analytics → Data Quality → Advocacy Brief**")

if not AI_AVAILABLE:
    st.warning(
        "**AI features are disabled.** "
        "Set `ANTHROPIC_API_KEY` in your environment to enable NLP search and brief generation. "
        "See `.env.example` for setup instructions."
    )

if not data_loaded:
    st.error(
        "**Data failed to load.** "
        "Ensure `data/sample/` (or `data/full/`) contains the required CSV files."
    )

st.divider()
st.caption(
    "Shakisha · GRB Gender Data Resource Discovery Hackathon · March 19–20, 2026, Kigali, Rwanda  \n"
    "Data source: [NISR Microdata Catalog](https://microdata.statistics.gov.rw/)"
)
