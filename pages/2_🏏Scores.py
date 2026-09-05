import pandas as pd
import plotly.express as px
import streamlit as st

from utils.database import (get_connection, live_api_available, run_sql,
                             get_live_matches, get_recent_matches, get_upcoming_matches)

st.set_page_config(page_title="Scores · Cricbuzz LiveStats", page_icon="🏏", layout="wide")
get_connection()

st.title("🏏 Scores")
st.caption("Live/recent/upcoming fixtures (when a live API key is configured), the synthetic match "
           "explorer, and a full batting + bowling scorecard lookup for any match.")

if live_api_available():
    st.success("Live Cricbuzz API connected — showing real-time data.")
    tab_live, tab_recent, tab_upcoming = st.tabs(["🔴 Live", "✅ Recent", "📅 Upcoming"])
    for tab, fetcher, label in [(tab_live, get_live_matches, "live"),
                                 (tab_recent, get_recent_matches, "recent"),
                                 (tab_upcoming, get_upcoming_matches, "upcoming")]:
        with tab:
            try:
                data = fetcher()
                st.json(data, expanded=False)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Couldn't reach the live {label} endpoint: {exc}")
else:
    st.info(
        "Running in **demo mode** on the synthetic dataset (schema-identical to what the live "
        "Cricbuzz API would populate). Add a `RAPIDAPI_KEY` under `.streamlit/secrets.toml` to "
        "switch this page to real-time data — no other code changes needed."
    )

st.divider()
st.subheader("📋 Match Explorer (synthetic warehouse)")

filt_col1, filt_col2, filt_col3 = st.columns(3)
teams = run_sql("SELECT team_id, team_name FROM teams ORDER BY team_name")
formats = run_sql("SELECT DISTINCT format FROM matches")["format"].tolist()

with filt_col1:
    fmt_filter = st.multiselect("Format", formats, default=formats)
with filt_col2:
    team_filter = st.multiselect("Team", teams.team_name.tolist())
with filt_col3:
    limit = st.slider("Rows to show", 10, 120, 25)

matches_df = run_sql("""
SELECT m.match_id, m.match_date, m.format, t1.team_name AS team1, t2.team_name AS team2,
       v.venue_name, v.city, tw.team_name AS toss_winner, m.toss_decision,
       COALESCE(w.team_name, 'No Result') AS winner, m.win_margin, m.win_margin_type,
       pom.player_name AS player_of_match
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
JOIN venues v ON v.venue_id = m.venue_id
LEFT JOIN teams tw ON tw.team_id = m.toss_winner_id
LEFT JOIN teams w ON w.team_id = m.winner_team_id
LEFT JOIN players pom ON pom.player_id = m.player_of_match_id
ORDER BY m.match_date DESC
""")

if fmt_filter:
    matches_df = matches_df[matches_df["format"].isin(fmt_filter)]
if team_filter:
    matches_df = matches_df[matches_df.team1.isin(team_filter) | matches_df.team2.isin(team_filter)]
matches_df = matches_df.head(limit)

st.dataframe(matches_df, use_container_width=True, hide_index=True)

c1, c2 = st.columns(2)
with c1:
    fmt_counts = matches_df["format"].value_counts().reset_index()
    fmt_counts.columns = ["format", "count"]
    st.plotly_chart(px.pie(fmt_counts, names="format", values="count", title="Format Mix (filtered view)", hole=0.45),
                     use_container_width=True)
with c2:
    winner_counts = matches_df["winner"].value_counts().head(10).reset_index()
    winner_counts.columns = ["team", "wins"]
    st.plotly_chart(px.bar(winner_counts, x="wins", y="team", orientation="h",
                            title="Wins in Filtered View"), use_container_width=True)

st.divider()
st.subheader("🔎 Match Scorecard Lookup")
match_id = st.number_input("Match ID", min_value=1, max_value=120, value=1, step=1)
bat = run_sql("""
    SELECT p.player_name, t.team_name, b.runs, b.balls_faced, b.fours, b.sixes, b.strike_rate,
           CASE WHEN b.is_out=1 THEN 'Out' ELSE 'Not Out' END AS status
    FROM batting_scorecards b JOIN players p ON p.player_id=b.player_id
    JOIN teams t ON t.team_id=b.team_id WHERE b.match_id = ? ORDER BY b.team_id, b.runs DESC
""", (int(match_id),))
bowl = run_sql("""
    SELECT p.player_name, t.team_name, bo.overs, bo.runs_conceded, bo.wickets, bo.economy, bo.maidens
    FROM bowling_scorecards bo JOIN players p ON p.player_id=bo.player_id
    JOIN teams t ON t.team_id=bo.team_id WHERE bo.match_id = ? ORDER BY bo.team_id, bo.wickets DESC
""", (int(match_id),))

sc1, sc2 = st.columns(2)
with sc1:
    st.markdown("**Batting scorecard**")
    st.dataframe(bat, use_container_width=True, hide_index=True)
with sc2:
    st.markdown("**Bowling scorecard**")
    st.dataframe(bowl, use_container_width=True, hide_index=True)
