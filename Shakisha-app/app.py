import hashlib
import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)  # always prefer .env over shell environment

st.set_page_config(
    page_title="Shakisha — Gender Data Discovery",
    page_icon="🔍",
    layout="wide",
)

# ── Logo — defined inline so changes here instantly reload the logo ─────────────
# (SVG file edits are NOT auto-detected by Streamlit; inline definition avoids that)
_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="240" height="52" viewBox="0 0 240 52">
  <circle cx="18" cy="18" r="11" stroke="#000000" stroke-width="3" fill="none"/>
  <line x1="26" y1="26" x2="35" y2="35" stroke="#000000" stroke-width="3.5" stroke-linecap="round"/>
  <text x="44" y="25"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
        font-size="26" font-weight="900" letter-spacing="3" fill="#000000">Shakisha</text>
  <text x="44" y="43"
        font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"
        font-size="11" letter-spacing="0.5" fill="#444444">Gender Data Discovery</text>
</svg>"""

_logo_bytes = _LOGO_SVG.encode("utf-8")
_logo_hash = hashlib.md5(_logo_bytes).hexdigest()[:12]
_logo_path = os.path.join(tempfile.gettempdir(), f"shakisha_logo_{_logo_hash}.svg")
if not os.path.exists(_logo_path):
    with open(_logo_path, "wb") as _f:
        _f.write(_logo_bytes)

st.logo(_logo_path, size="large")

pg = st.navigation([
    st.Page("pages/0_Home.py",           title="Home",           icon="🏠"),
    st.Page("pages/1_Discovery.py",      title="Discovery",      icon="🔍"),
    st.Page("pages/2_Dashboard.py",      title="Analytics",      icon="📊"),
    st.Page("pages/3_Data_Quality.py",   title="Data Quality",   icon="🛡️"),
    st.Page("pages/4_Advocacy_Brief.py", title="Advocacy Brief", icon="📝"),
    st.Page("pages/5_Pipeline.py",       title="Data Pipeline",  icon="🔄"),
])

pg.run()
