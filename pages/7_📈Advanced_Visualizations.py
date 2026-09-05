import plotly.graph_objects as go
import streamlit as st

from utils.database import get_connection, run_sql
from utils.queries import QUESTIONS, postprocess

st.set_page_config(page_title="Advanced Visualizations · Cricbuzz LiveStats", page_icon="📈", layout="wide")
get_connection()

st.title("📈 Advanced Visualizations")
st.caption(
    "A curated gallery of the project's most analytically rich charts — window functions, "
    "ranking, form/trajectory modelling, and composite scoring — pulled straight from the "
    "notebook's Advanced tier (Q13–Q25), plus two executive-facing summary visuals. "
    "For the SQL behind any chart, see **SQL Analytics**."
)

# One-line, notebook-sourced insight for each Advanced question, so the gallery reads as
# analysis rather than a wall of charts.
INSIGHTS = {
    13: "Surfaces each team's clear top run-scorer — useful for identifying batting reliance risk.",
    14: "Win-total trend lines flag which teams are building form versus plateauing over the sample.",
    15: "Highlights the batting pairs whose combined output most often carries an innings.",
    16: "Separates 'big scores, big failures' players from truly reliable accumulators — a distinction raw averages hide.",
    17: "Five-wicket hauls stand out visually against the broader spread of solid-but-unspectacular spells.",
    18: "Tests whether 'home advantage' actually shows up in the win-percentage numbers, team by team.",
    19: "The tightest cluster (low average, low std. dev.) marks the most dependable batsmen since 2022.",
    20: "Shows how workload splits across formats — some players are two-format specialists, not three.",
    21: "The weighted composite consistently promotes multi-skill, all-format contributors over one-dimensional specialists.",
    22: "Rivalry pairs with lopsided win splits versus genuinely competitive head-to-heads, side by side.",
    23: "Recency-weighted form flags players trending into 'Excellent Form' before their season average catches up — a leading, not lagging, signal.",
    24: "Partnership combinations ranked by success rate, not just raw runs — chemistry over volume.",
    25: "Quarterly batting trajectories classify careers as Ascending / Declining / Stable at a glance.",
}

ADVANCED = [item for item in QUESTIONS if item["tier"] == "Advanced"]

# --------------------------------------------------------------------- gallery
cols = st.columns(2)
for idx, item in enumerate(ADVANCED):
    df = run_sql(item["sql"])
    df = postprocess(item["id"], df, run_sql)
    with cols[idx % 2]:
        with st.container(border=True):
            st.markdown(f"**Q{item['id']}. {item['title']}**")
            st.plotly_chart(item["chart"](df), use_container_width=True, key=f"adv_{item['id']}")
            st.caption(INSIGHTS.get(item["id"], item["business_question"]))

st.divider()

# --------------------------------------------------------------------- bonus executive visuals
st.subheader("🎯 Executive Summary Visuals")
st.caption("Two recruiter-facing views from the notebook's summary dashboard section.")

kpi = run_sql("""
SELECT
    (SELECT COUNT(*) FROM matches) AS total_matches,
    (SELECT COUNT(*) FROM players) AS total_players,
    (SELECT COUNT(*) FROM teams) AS total_teams,
    (SELECT COUNT(DISTINCT venue_id) FROM matches) AS venues_used,
    (SELECT ROUND(AVG(runs),1) FROM batting_scorecards) AS avg_runs_per_innings,
    (SELECT ROUND(AVG(economy),2) FROM bowling_scorecards) AS avg_economy
""").iloc[0]

bonus1, bonus2 = st.columns(2)

with bonus1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Average Runs / Innings"], y=[kpi.avg_runs_per_innings], name="Batting",
        text=[f"{kpi.avg_runs_per_innings:.1f}"], textposition="outside",
        marker_color="#2E86AB",
        hovertemplate="<b>Batting Environment</b><br>Average Runs: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=["Average Bowling Economy"], y=[kpi.avg_economy], name="Bowling",
        text=[f"{kpi.avg_economy:.2f}"], textposition="outside",
        marker_color="#E28413",
        hovertemplate="<b>Bowling Environment</b><br>Average Economy: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(title="⚔️ Batting vs Bowling Performance Environment",
                       yaxis_title="Value", template="plotly_white", height=420, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with bonus2:
    labels = ["Matches", "Players", "Teams", "Venues"]
    values = [int(kpi.total_matches), int(kpi.total_players), int(kpi.total_teams), int(kpi.venues_used)]
    fig2 = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        text=[f"{x:,}" for x in values], textposition="outside",
        marker_color="#1B998B",
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
    ))
    fig2.update_layout(title="📊 Cricket Dataset Composition", xaxis_title="Count",
                        template="plotly_white", height=420)
    st.plotly_chart(fig2, use_container_width=True)
