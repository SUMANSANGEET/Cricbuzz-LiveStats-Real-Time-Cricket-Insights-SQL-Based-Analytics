import streamlit as st

from utils.database import get_connection

st.set_page_config(page_title="About · Cricbuzz LiveStats", page_icon="ℹ️", layout="wide")
get_connection()

st.title("ℹ️ About This Project")

st.markdown("""
### 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics
**Author:** P Suman Sangeet · **Track:** LABMENTIX Data Analytics & AI Cohort · **Domain:** Sports Data Analytics

An end-to-end sports-analytics platform that integrates live cricket data from the Cricbuzz API
(RapidAPI), a normalized SQL warehouse, 25 tiered analytics questions, and a transaction-safe CRUD
module — all surfaced through this multi-page Streamlit dashboard.
""")

t1, t2, t3, t4 = st.tabs(["🏗️ Architecture", "🗄️ Database Schema", "🧰 Tech Stack", "🚀 Deployment"])

with t1:
    st.markdown("""
```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT APP LAYER                       │
│   Home · Live Matches · SQL Analytics · Player Explorer · CRUD   │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                 │
        ┌────────▼─────────┐             ┌─────────▼─────────┐
        │   ANALYTICS LAYER  │             │    CRUD LAYER      │
        │ 25 SQL questions   │             │ Insert/Update/     │
        │ (window fns, CTEs) │             │ Delete + rollback  │
        └────────┬─────────┘             └─────────┬─────────┘
                 │                                 │
                 └───────────────┬─────────────────┘
                                 │
                     ┌───────────▼────────────┐
                     │     STORAGE LAYER        │
                     │   SQLite · 3NF schema    │
                     │   7 tables · 7 indexes   │
                     └───────────┬────────────┘
                                 │
                     ┌───────────▼────────────┐
                     │       API LAYER          │
                     │ Cricbuzz REST (RapidAPI) │
                     │ retry/backoff client, OR │
                     │ synthetic-data fallback  │
                     └──────────────────────────┘
```
    """)
    st.markdown("""
    **Data flow:** live matches / scorecards are fetched from the Cricbuzz API (when a key is
    configured) and normalized into the same schema the synthetic generator populates for offline
    demos — so every page, query, and chart works identically in either mode.
    """)

with t2:
    st.markdown("**Entities:** `teams`, `players`, `venues`, `series`, `matches`, "
                 "`batting_scorecards`, `bowling_scorecards` — normalized to 3NF.")
    st.code("""
teams(team_id PK, team_name, region)
players(player_id PK, player_name, team_id FK, role, batting_style, bowling_style, dob)
venues(venue_id PK, venue_name, city, country, capacity)
series(series_id PK, series_name, format, start_date)
matches(match_id PK, series_id FK, format, team1_id FK, team2_id FK, venue_id FK,
        match_date, toss_winner_id FK, toss_decision, winner_team_id FK,
        win_margin, win_margin_type, player_of_match_id FK)
batting_scorecards(scorecard_id PK, match_id FK, player_id FK, team_id FK,
                    runs, balls_faced, fours, sixes, strike_rate, is_out)
bowling_scorecards(bowling_id PK, match_id FK, player_id FK, team_id FK,
                    overs, runs_conceded, wickets, economy, maidens)
    """, language="sql")
    st.caption("Indexes on every foreign key (players.team_id, matches.series_id/venue_id, "
               "batting/bowling .match_id/.player_id) for join performance.")

with t3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **Language & Data**
        - Python 3.11
        - SQLite (embedded, zero-config)
        - Pandas / NumPy

        **API Integration**
        - `requests` with retry/backoff
        - Cricbuzz Cricket API (RapidAPI)
        """)
    with c2:
        st.markdown("""
        **App & Visualization**
        - Streamlit (multi-page app)
        - Plotly Express / Graph Objects

        **Engineering practices**
        - Parameterized queries (SQL-injection safe)
        - Transaction-wrapped CRUD with rollback
        - Secrets-based API key management (no hardcoded keys)
        """)

with t4:
    st.markdown("""
    **Streamlit Community Cloud** (recommended for this project)
    1. Push this folder to a public/private GitHub repo.
    2. On share.streamlit.io, create a new app pointing at `app.py`.
    3. Add `RAPIDAPI_KEY` under the app's **Secrets** manager to enable live data
       (optional — the app runs fully on synthetic data without it).
    4. Deploy — Streamlit installs `requirements.txt` automatically.

    **Alternative targets:** Render, Railway, or a Docker container (see `README.md` for a sample
    `Dockerfile` and `Procfile`-equivalent start command:
    `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`).
    """)

st.divider()
st.markdown("""
#### 💡 Key Insights Baked Into This Dashboard
- Run volume and strike rate don't always move together — the highest-SR players aren't always the
  top accumulators (classic anchor-vs-finisher trade-off), visible in Q1 vs Q7.
- Toss impact on match outcome is measurable but modest — see the live gauge in Q10.
- Career trajectories (Q25) let you flag players trending up or down over time, not just career
  averages — useful for scouting and selection narratives.
""")
