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

/* =========================================
   GLOBAL DARK BACKGROUND
   ========================================= */

.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(46, 134, 171, 0.18),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #07111F 0%,
            #0B1726 45%,
            #0F1F32 100%
        );

    color: #F1F5F9;
}

/* Main content */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* =========================================
   HIDE STREAMLIT DEFAULT UI
   ========================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* =========================================
   SIDEBAR
   ========================================= */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #050B14 0%,
            #081321 50%,
            #0B1B2E 100%
        );

    border-right: 1px solid #1E3A50;
}

[data-testid="stSidebar"] * {
    color: #E5EEF5 !important;
}

/* =========================================
   HERO SECTION
   ========================================= */

.hero {
    background:
        linear-gradient(
            120deg,
            #081A2C 0%,
            #0F3057 45%,
            #145A78 100%
        );

    padding: 2.2rem 2.5rem;

    border-radius: 18px;

    color: #FFFFFF;

    margin-bottom: 1.5rem;

    border: 1px solid #24506B;

    box-shadow:
        0 10px 35px rgba(0, 0, 0, 0.35);
}

.hero h1 {
    margin: 0;
    font-size: 2.1rem;
    color: #FFFFFF;
}

.hero p {
    margin-top: 0.5rem;
    font-size: 1.02rem;
    color: #D6E5EF;
    opacity: 0.95;
    max-width: 780px;
}

/* =========================================
   BADGES
   ========================================= */

.badge {
    display: inline-block;

    background: rgba(255,255,255,0.10);

    color: #E8F6FF;

    padding: 4px 12px;

    border-radius: 999px;

    font-size: 0.78rem;

    margin-right: 6px;

    margin-top: 10px;

    border: 1px solid rgba(255,255,255,0.20);
}

/* =========================================
   INFORMATION CARDS
   ========================================= */

.card {
    background:
        linear-gradient(
            145deg,
            #111F30,
            #0D1928
        );

    border-radius: 16px;

    padding: 1.2rem 1.4rem;

    border: 1px solid #223B50;

    height: 100%;

    color: #DCE7EF;

    box-shadow:
        0 8px 25px rgba(0, 0, 0, 0.25);

    transition:
        transform 0.25s ease,
        box-shadow 0.25s ease;
}

.card:hover {
    transform: translateY(-4px);

    box-shadow:
        0 14px 35px rgba(0, 0, 0, 0.40);
}

.card h4 {
    margin-top: 0;

    color: #FFFFFF;
}

/* =========================================
   TEXT
   ========================================= */

p, label, span {
    color: #D7E2EA;
}

/* =========================================
   DIVIDERS
   ========================================= */

hr {
    border-color: #24394B !important;
}

/* =========================================
   KPI / METRICS
   ========================================= */

[data-testid="stMetric"] {
    background:
        linear-gradient(
            145deg,
            #111F30,
            #0D1928
        );

    padding: 14px;

    border-radius: 14px;

    border: 1px solid #223B50;

    box-shadow:
        0 6px 20px rgba(0, 0, 0, 0.25);
}

[data-testid="stMetricLabel"] {
    color: #9FB5C5 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

/* =========================================
   BUTTONS
   ========================================= */

.stButton > button {
    background: #12324A;

    color: #FFFFFF;

    border: 1px solid #2E86AB;

    border-radius: 10px;

    font-weight: 600;
}

.stButton > button:hover {
    background: #1B5F7A;

    border-color: #4CA8D1;

    color: #FFFFFF;
}

/* =========================================
   SELECTBOX / INPUTS
   ========================================= */

[data-baseweb="select"] > div {
    background: #111F30;

    color: #FFFFFF;

    border-radius: 10px;

    border: 1px solid #29465B;
}

/* Text input */

input {
    background-color: #111F30 !important;

    color: #FFFFFF !important;
}

/* =========================================
   DATAFRAME
   ========================================= */

[data-testid="stDataFrame"] {
    border-radius: 12px;

    overflow: hidden;

    border: 1px solid #24394B;
}

/* =========================================
   TABS
   ========================================= */

button[data-baseweb="tab"] {
    color: #AFC2D0 !important;

    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #FFFFFF !important;
}

/* =========================================
   EXPANDERS
   ========================================= */

[data-testid="stExpander"] {
    background: #0F1D2C;

    border: 1px solid #24394B;

    border-radius: 12px;
}

/* =========================================
   CAPTIONS
   ========================================= */

.stCaption {
    color: #8FA6B6 !important;
}

/* =========================================
   SUCCESS / WARNING / ERROR BOXES
   ========================================= */

[data-testid="stAlert"] {
    border-radius: 10px;
}

/* =========================================
   SCROLLBAR
   ========================================= */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #07111F;
}

::-webkit-scrollbar-thumb {
    background: #29465B;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #2E86AB;
}

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
