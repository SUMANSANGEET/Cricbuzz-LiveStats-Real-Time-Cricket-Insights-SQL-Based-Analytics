import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.database import get_connection, run_sql

st.set_page_config(page_title="Player Explorer · Cricbuzz LiveStats", page_icon="🔍", layout="wide")
get_connection()

st.title("🔍 Player Explorer")
st.caption("Search any player for a career batting/bowling snapshot, or compare two players head-to-head.")

players = run_sql("""
    SELECT p.player_id, p.player_name, t.team_name, p.role, p.batting_style, p.bowling_style
    FROM players p JOIN teams t ON t.team_id = p.team_id ORDER BY p.player_name
""")

tab_profile, tab_compare = st.tabs(["👤 Player Profile", "⚔️ Head-to-Head Comparison"])


def player_summary(player_id: int):
    bat = run_sql("""
        SELECT COUNT(*) AS innings, SUM(runs) AS runs, ROUND(AVG(runs),1) AS avg_runs,
               ROUND(SUM(runs)*100.0/NULLIF(SUM(balls_faced),0),1) AS strike_rate,
               SUM(fours) AS fours, SUM(sixes) AS sixes,
               SUM(CASE WHEN runs>=100 THEN 1 ELSE 0 END) AS centuries,
               SUM(CASE WHEN runs>=50 AND runs<100 THEN 1 ELSE 0 END) AS fifties
        FROM batting_scorecards WHERE player_id = ?
    """, (player_id,)).iloc[0]
    bowl = run_sql("""
        SELECT COUNT(*) AS spells, SUM(wickets) AS wickets, ROUND(SUM(overs),1) AS overs,
               ROUND(SUM(runs_conceded)*1.0/NULLIF(SUM(wickets),0),2) AS bowling_avg,
               ROUND(SUM(runs_conceded)*1.0/NULLIF(SUM(overs),0),2) AS economy
        FROM bowling_scorecards WHERE player_id = ?
    """, (player_id,)).iloc[0]
    return bat, bowl


with tab_profile:
    name = st.selectbox("Search player", players.player_name.tolist())
    row = players[players.player_name == name].iloc[0]

    st.markdown(f"### {row.player_name} — {row.team_name}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Role", row.role)
    m2.metric("Batting style", row.batting_style)
    m3.metric("Bowling style", row.bowling_style)

    bat, bowl = player_summary(int(row.player_id))
    st.markdown("#### Batting")
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Innings", int(bat.innings or 0))
    b2.metric("Runs", int(bat.runs or 0))
    b3.metric("Average", bat.avg_runs or 0)
    b4.metric("Strike Rate", bat.strike_rate or 0)
    b5.metric("100s / 50s", f"{int(bat.centuries or 0)} / {int(bat.fifties or 0)}")

    st.markdown("#### Bowling")
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Spells bowled", int(bowl.spells or 0))
    w2.metric("Wickets", int(bowl.wickets or 0))
    w3.metric("Bowling Average", bowl.bowling_avg if bowl.bowling_avg is not None else "—")
    w4.metric("Economy", bowl.economy if bowl.economy is not None else "—")

    trend = run_sql("""
        SELECT m.match_date, b.runs
        FROM batting_scorecards b JOIN matches m ON m.match_id=b.match_id
        WHERE b.player_id = ? ORDER BY m.match_date
    """, (int(row.player_id),))
    if not trend.empty:
        st.plotly_chart(
            px.line(trend, x="match_date", y="runs", markers=True, title=f"{row.player_name} — Runs per Innings Over Time"),
            use_container_width=True)

with tab_compare:
    c1, c2 = st.columns(2)
    with c1:
        p1 = st.selectbox("Player A", players.player_name.tolist(), key="p1")
    with c2:
        remaining = [p for p in players.player_name.tolist() if p != p1]
        p2 = st.selectbox("Player B", remaining, key="p2")

    id1 = int(players[players.player_name == p1].iloc[0].player_id)
    id2 = int(players[players.player_name == p2].iloc[0].player_id)
    bat1, bowl1 = player_summary(id1)
    bat2, bowl2 = player_summary(id2)

    categories = ["Runs", "Avg", "Strike Rate", "Wickets", "Economy (inv.)"]
    econ1 = bowl1.economy if bowl1.economy else 0
    econ2 = bowl2.economy if bowl2.economy else 0
    max_econ = max(econ1, econ2, 1)

    fig = go.Figure()
    for label, bat, bowl, econ in [(p1, bat1, bowl1, econ1), (p2, bat2, bowl2, econ2)]:
        fig.add_trace(go.Scatterpolar(
            r=[bat.runs or 0, bat.avg_runs or 0, bat.strike_rate or 0, bowl.wickets or 0,
               (max_econ - econ) if econ else 0],
            theta=categories, fill="toself", name=label))
    fig.update_layout(title="Head-to-Head Radar (career totals)", height=500,
                       polar=dict(radialaxis=dict(visible=True)))
    st.plotly_chart(fig, use_container_width=True)

    comp_df = players[players.player_name.isin([p1, p2])][["player_name", "team_name", "role"]]
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
