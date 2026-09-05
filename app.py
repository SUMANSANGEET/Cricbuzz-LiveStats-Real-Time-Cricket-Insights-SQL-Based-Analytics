"""
Cricbuzz LiveStats — Real-Time Cricket Insights & SQL-Based Analytics
======================================================================
Recruiter-facing entry point. Run with:  streamlit run app.py
"""

import streamlit as st

from utils.database import get_connection, live_api_available, reset_database
from utils.kpi import build_kpi_figure

st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.hero {
    background: linear-gradient(120deg, #0F3057 0%, #2E86AB 100%);
    padding: 2.2rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
}
.hero h1 {margin: 0; font-size: 2.1rem;}
.hero p {margin-top: 0.5rem; font-size: 1.02rem; opacity: 0.92; max-width: 780px;}
.badge {
    display: inline-block; background: rgba(255,255,255,0.16); color: white;
    padding: 3px 12px; border-radius: 999px; font-size: 0.78rem; margin-right: 6px;
    margin-top: 10px; border: 1px solid rgba(255,255,255,0.35);
}
.card {
    background: #F4F7FA; border-radius: 14px; padding: 1.1rem 1.3rem;
    border: 1px solid #E4EAF0; height: 100%;
}
.card h4 {margin-top: 0;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------- init
get_connection()  # builds schema + seeds synthetic data on first run

# --------------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🏏 Cricbuzz LiveStats")
    st.caption("Real-Time Cricket Insights & SQL-Based Analytics")
    st.divider()
    mode = "🟢 Live API connected" if live_api_available() else "🟡 Demo mode (synthetic dataset)"
    st.markdown(f"**Data source:** {mode}")
    if not live_api_available():
        st.caption("Add `RAPIDAPI_KEY` to `.streamlit/secrets.toml` to switch to live Cricbuzz data — "
                   "every page works unchanged either way.")
    st.divider()
    if st.button("🔄 Reset demo dataset", use_container_width=True):
        reset_database()
        st.success("Synthetic dataset regenerated.")
        st.rerun()
    st.divider()
    st.caption("**P Suman Sangeet** · LABMENTIX Data Analytics & AI cohort")
    st.caption("Built with Python · SQLite · Streamlit · Plotly")

# --------------------------------------------------------------------- hero
st.markdown("""
<div class="hero">
  <h1>🏏 Cricbuzz LiveStats</h1>
  <p>An end-to-end sports-data-analytics platform: a live API integration layer, a normalized
  8-table SQL warehouse, 25 tiered SQL analytics questions, and transaction-safe CRUD —
  all surfaced through this interactive dashboard.</p>
  <span class="badge">Python</span>
  <span class="badge">SQL / SQLite</span>
  <span class="badge">REST API Integration</span>
  <span class="badge">Streamlit</span>
  <span class="badge">Plotly</span>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------- KPI strip
st.plotly_chart(build_kpi_figure(), use_container_width=True, config={"displayModeBar": False})

st.divider()

# --------------------------------------------------------------------- overview cards
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    <div class="card">
    <h4>💼 Business Problem</h4>
    Cricket generates continuous data across matches, players, teams, venues and series —
    but raw feeds and disconnected spreadsheets don't answer real questions like "who's in form"
    or "which venue favors batting." This project pipelines that data into a queryable warehouse
    and a dashboard analysts, coaches, and fans can actually use.
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="card">
    <h4>🏗️ Architecture</h4>
    <b>API Layer</b> → Cricbuzz REST (RapidAPI), retry/backoff client<br>
    <b>Storage Layer</b> → SQLite, 3NF, 7 FK indexes<br>
    <b>Analytics Layer</b> → 25 SQL questions (window fns, CTEs, ranking)<br>
    <b>App Layer</b> → this multi-page Streamlit dashboard
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="card">
    <h4>🧭 Explore</h4>
    Use the sidebar to navigate:<br>
    • <b>SQL Analytics</b> — all 25 questions, live charts<br>
    • <b>Scores</b> — fixtures & full scorecards<br>
    • <b>Player Explorer</b> — search any player's profile<br>
    • <b>Matches CRUD</b> / <b>Scores CRUD</b> — manage records<br>
    • <b>Advanced Visualizations</b> — the analytics highlight reel<br>
    • <b>Analytics Overview</b> — executive summary & key insights<br>
    • <b>About</b> — schema, tech stack, roadmap
    </div>""", unsafe_allow_html=True)

st.divider()
st.caption(
    "Dataset note: when no RapidAPI key is configured, the app runs on a schema-identical "
    "synthetic dataset (120 matches, 150 players) so every query and chart is fully demoable offline."
)
