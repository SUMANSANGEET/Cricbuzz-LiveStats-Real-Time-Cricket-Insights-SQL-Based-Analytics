"""
Shared interactive filter bar
=============================
Renders a Team / Format / Date-range filter row and returns both the
selections and a ready-to-use SQL WHERE clause + params, so any page can
plug live filtering into its own queries with two lines of code.

Usage
-----
    from utils.filters import render_filter_bar

    where_sql, params, choice = render_filter_bar()
    df = run_sql(f\"\"\"
        SELECT ... FROM matches m
        JOIN teams t1 ON t1.team_id = m.team1_id
        JOIN teams t2 ON t2.team_id = m.team2_id
        WHERE {where_sql}
    \"\"\", params)
"""

import streamlit as st

from utils.database import run_sql


def render_filter_bar(key_prefix: str = "flt"):
    """Renders team / format / date-range selectors and returns (where_sql, params, choices)."""
    teams = run_sql("SELECT team_name FROM teams ORDER BY team_name").team_name.tolist()
    date_bounds = run_sql("SELECT MIN(match_date) AS lo, MAX(match_date) AS hi FROM matches").iloc[0]

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        team_choice = st.multiselect(
            "Team", teams, default=[], key=f"{key_prefix}_team",
            placeholder="All teams",
        )
    with c2:
        format_choice = st.selectbox(
            "Format", ["All", "T20I", "ODI", "Test"], key=f"{key_prefix}_format",
        )
    with c3:
        date_range = st.date_input(
            "Match date range", value=(date_bounds.lo, date_bounds.hi),
            min_value=date_bounds.lo, max_value=date_bounds.hi, key=f"{key_prefix}_dates",
        )

    clauses = ["1=1"]
    params: list = []

    if team_choice:
        placeholders = ",".join("?" for _ in team_choice)
        clauses.append(f"(t1.team_name IN ({placeholders}) OR t2.team_name IN ({placeholders}))")
        params.extend(team_choice)
        params.extend(team_choice)

    if format_choice != "All":
        clauses.append("m.format = ?")
        params.append(format_choice)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        clauses.append("m.match_date BETWEEN ? AND ?")
        params.append(str(date_range[0]))
        params.append(str(date_range[1]))

    where_sql = " AND ".join(clauses)
    choice = {"teams": team_choice, "format": format_choice, "date_range": date_range}
    return where_sql, tuple(params), choice
