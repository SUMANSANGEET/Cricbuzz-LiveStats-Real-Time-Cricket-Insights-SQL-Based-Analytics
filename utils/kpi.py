"""
Shared KPI-strip builder — used by both the Home page and Analytics Overview.

Kept in one place so the indicator/subplot wiring (a past source of a rendering bug —
domain must be set via add_trace(row=, col=), never a manual `domain` dict on the
Indicator itself unless a matching layout.grid is also defined) only has to be correct once.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.database import run_sql

ACCENTS = ["#2E86AB", "#0F3057", "#1B998B", "#E28413", "#B23A48", "#5C4D7D"]


def get_kpis() -> list[tuple[str, str, float, str]]:
    kpi = run_sql("""
    SELECT
        (SELECT COUNT(*) FROM matches) AS total_matches,
        (SELECT COUNT(*) FROM players) AS total_players,
        (SELECT COUNT(*) FROM teams) AS total_teams,
        (SELECT COUNT(DISTINCT venue_id) FROM matches) AS venues_used,
        (SELECT ROUND(AVG(runs),1) FROM batting_scorecards) AS avg_runs_per_innings,
        (SELECT ROUND(AVG(economy),2) FROM bowling_scorecards) AS avg_economy
    """).iloc[0]
    return [
        ("🏏", "Matches", int(kpi.total_matches), "Total matches analyzed"),
        ("👤", "Players", int(kpi.total_players), "Unique players covered"),
        ("🏆", "Teams", int(kpi.total_teams), "Teams represented"),
        ("📍", "Venues", int(kpi.venues_used), "Venues used"),
        ("🔥", "Avg Runs", float(kpi.avg_runs_per_innings), "Average runs per innings"),
        ("🎯", "Avg Economy", float(kpi.avg_economy), "Average bowling economy"),
    ]


def build_kpi_figure(kpis=None, height: int = 210) -> go.Figure:
    kpis = kpis or get_kpis()
    fig = make_subplots(rows=1, cols=len(kpis), specs=[[{"type": "indicator"}] * len(kpis)],
                         horizontal_spacing=0.03)
    for i, (icon, label, value, description) in enumerate(kpis, start=1):
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=value,
                number={
                    "font": {"size": 34, "color": ACCENTS[(i - 1) % len(ACCENTS)]},
                    "valueformat": ".1f" if isinstance(value, float) else ",d",
                },
                title={
                    "text": f"<b>{icon} {label}</b><br>"
                            f"<span style='font-size:11px;color:gray'>{description}</span>",
                    "font": {"size": 14},
                },
            ),
            row=1, col=i,
        )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )
    return fig
