"""
Interactive Dashboard — live-filtered KPIs, form trend, and a venue map.
Unlike the fixed SQL Analytics / Advanced Visualizations galleries, every
chart on this page re-queries and redraws as the filters change, which is
the single most "real dashboard" moment in the app for a reviewer.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.database import get_connection, run_sql
from utils.filters import render_filter_bar

st.set_page_config(page_title="Interactive Dashboard · Cricbuzz LiveStats", page_icon="🎛️", layout="wide")
get_connection()

st.title("🎛️ Interactive Dashboard")
st.caption(
    "Filter by team, format, and date range — every KPI, chart, and the venue map below "
    "recompute live from SQL against your selection. Leave filters empty to see the full dataset."
)

where_sql, params, choice = render_filter_bar()
st.divider()

# --------------------------------------------------------------------- filtered KPI strip
base_from = """
    FROM matches m
    JOIN teams t1 ON t1.team_id = m.team1_id
    JOIN teams t2 ON t2.team_id = m.team2_id
"""

summary = run_sql(f"""
    SELECT
        COUNT(*) AS matches,
        COUNT(DISTINCT m.venue_id) AS venues,
        (SELECT ROUND(AVG(b.runs),1) FROM batting_scorecards b
            JOIN matches mm ON mm.match_id = b.match_id
            JOIN teams tt1 ON tt1.team_id = mm.team1_id
            JOIN teams tt2 ON tt2.team_id = mm.team2_id
            WHERE {where_sql.replace('m.', 'mm.').replace('t1.', 'tt1.').replace('t2.', 'tt2.')}) AS avg_runs,
        (SELECT ROUND(AVG(bw.economy),2) FROM bowling_scorecards bw
            JOIN matches mm ON mm.match_id = bw.match_id
            JOIN teams tt1 ON tt1.team_id = mm.team1_id
            JOIN teams tt2 ON tt2.team_id = mm.team2_id
            WHERE {where_sql.replace('m.', 'mm.').replace('t1.', 'tt1.').replace('t2.', 'tt2.')}) AS avg_economy
    {base_from}
    WHERE {where_sql}
""", params + params + params).iloc[0]

if summary.matches == 0:
    st.warning("No matches fit this filter combination — widen the date range or team selection.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Matches in selection", int(summary.matches))
k2.metric("Venues involved", int(summary.venues))
k3.metric("Avg runs / innings", f"{summary.avg_runs or 0:.1f}")
k4.metric("Avg bowling economy", f"{summary.avg_economy or 0:.2f}")

st.divider()

c1, c2 = st.columns([3, 2])

# --------------------------------------------------------------------- win trend by team
with c1:
    st.subheader("📈 Wins over time, filtered selection")
    trend = run_sql(f"""
        SELECT strftime('%Y-%m', m.match_date) AS month, tw.team_name AS winner, COUNT(*) AS wins
        {base_from}
        LEFT JOIN teams tw ON tw.team_id = m.winner_team_id
        WHERE {where_sql} AND m.winner_team_id IS NOT NULL
        GROUP BY month, winner ORDER BY month
    """, params)
    if trend.empty:
        st.info("No decided matches in this selection yet.")
    else:
        fig = px.line(trend, x="month", y="wins", color="winner", markers=True,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), legend_title="Team")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------- toss vs win
with c2:
    st.subheader("🪙 Toss → Win, filtered")
    toss = run_sql(f"""
        SELECT SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS toss_and_won,
               COUNT(*) AS decided
        {base_from}
        WHERE {where_sql} AND m.winner_team_id IS NOT NULL
    """, params).iloc[0]
    pct = (toss.toss_and_won / toss.decided * 100) if toss.decided else 0
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=pct,
        number={"suffix": "%"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#2E86AB"},
               "steps": [{"range": [0, 50], "color": "#F4F7FA"}, {"range": [50, 100], "color": "#E4EAF0"}]},
        title={"text": "Toss winner also won match"},
    ))
    gauge.update_layout(height=380, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(gauge, use_container_width=True)

st.divider()

# --------------------------------------------------------------------- venue map
st.subheader("🌍 Venue Map — average runs scored, filtered selection")
st.caption("Bubble size = matches played there under the current filter; color = average first-innings-style run total.")

CITY_COORDS = {
    "Mumbai": (19.0760, 72.8777), "Melbourne": (-37.8136, 144.9631), "London": (51.5072, -0.1276),
    "Auckland": (-36.8485, 174.7633), "Lahore": (31.5497, 74.3436), "Johannesburg": (-26.2041, 28.0473),
    "Colombo": (6.9271, 79.8612), "Bridgetown": (13.0969, -59.6145), "Dhaka": (23.8103, 90.4125),
    "Kabul": (34.5553, 69.2075), "Chennai": (13.0827, 80.2707), "Sydney": (-33.8688, 151.2093),
    "Manchester": (53.4808, -2.2426), "Wellington": (-41.2865, 174.7762), "Karachi": (24.8607, 67.0011),
}

venue_df = run_sql(f"""
    SELECT v.venue_name, v.city, v.country, COUNT(DISTINCT m.match_id) AS matches_played,
           ROUND(AVG(b.runs), 1) AS avg_runs
    {base_from}
    JOIN venues v ON v.venue_id = m.venue_id
    LEFT JOIN batting_scorecards b ON b.match_id = m.match_id
    WHERE {where_sql}
    GROUP BY v.venue_id
""", params)

if venue_df.empty:
    st.info("No venue data for this filter selection.")
else:
    venue_df["lat"] = venue_df["city"].map(lambda c: CITY_COORDS.get(c, (0, 0))[0])
    venue_df["lon"] = venue_df["city"].map(lambda c: CITY_COORDS.get(c, (0, 0))[1])
    map_fig = px.scatter_geo(
        venue_df, lat="lat", lon="lon", size="matches_played", color="avg_runs",
        hover_name="venue_name", hover_data={"city": True, "country": True, "avg_runs": True,
                                              "matches_played": True, "lat": False, "lon": False},
        color_continuous_scale="Tealrose", projection="natural earth",
    )
    map_fig.update_layout(height=460, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(map_fig, use_container_width=True)
