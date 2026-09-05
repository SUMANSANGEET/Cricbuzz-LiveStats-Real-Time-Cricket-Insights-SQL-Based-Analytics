import datetime as dt

import streamlit as st

from utils.database import (get_connection, create_match, read_match, update_match,
                             delete_match, lookup_tables, run_sql)

st.set_page_config(page_title="Matches CRUD · Cricbuzz LiveStats", page_icon="🗂️", layout="wide")
get_connection()

st.title("🗂️ Matches CRUD")
st.caption("Transaction-safe Create / Read / Update / Delete against the `matches` table. "
           "Every write commits inside a `with conn:` block, so a failure rolls back cleanly. "
           "For batting/bowling scorecard rows, see **Scores CRUD**.")

lut = lookup_tables()
tab_create, tab_read, tab_update, tab_delete = st.tabs(["➕ Create", "🔎 Read", "✏️ Update", "🗑️ Delete"])

with tab_create:
    st.subheader("Insert a new match")
    with st.form("create_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            series_id = st.selectbox("Series", lut["series"].series_id,
                                      format_func=lambda x: lut["series"].set_index("series_id").loc[x, "series_name"])
            fmt = st.selectbox("Format", ["T20I", "ODI", "Test"])
            match_date = st.date_input("Match date", value=dt.date.today())
        with c2:
            team1_id = st.selectbox("Team 1", lut["teams"].team_id,
                                     format_func=lambda x: lut["teams"].set_index("team_id").loc[x, "team_name"])
            team2_id = st.selectbox("Team 2", lut["teams"].team_id,
                                     format_func=lambda x: lut["teams"].set_index("team_id").loc[x, "team_name"], index=1)
            venue_id = st.selectbox("Venue", lut["venues"].venue_id,
                                     format_func=lambda x: lut["venues"].set_index("venue_id").loc[x, "venue_name"])
        with c3:
            toss_winner_id = st.selectbox("Toss winner", [team1_id, team2_id],
                                           format_func=lambda x: lut["teams"].set_index("team_id").loc[x, "team_name"])
            toss_decision = st.selectbox("Toss decision", ["Bat", "Field"])
            winner_team_id = st.selectbox("Winner (optional)", [None, team1_id, team2_id],
                                           format_func=lambda x: "No result" if x is None
                                           else lut["teams"].set_index("team_id").loc[x, "team_name"])

        c4, c5 = st.columns(2)
        with c4:
            win_margin = st.number_input("Win margin", min_value=0, value=0)
            win_margin_type = st.selectbox("Margin type", ["runs", "wickets"])
        with c5:
            pom_id = st.selectbox("Player of the Match (optional)", [None] + lut["players"].player_id.tolist(),
                                   format_func=lambda x: "—" if x is None
                                   else lut["players"].set_index("player_id").loc[x, "player_name"])

        submitted = st.form_submit_button("Insert match", type="primary")
        if submitted:
            if team1_id == team2_id:
                st.error("Team 1 and Team 2 must be different.")
            else:
                new_id = create_match({
                    "series_id": int(series_id), "format": fmt, "team1_id": int(team1_id),
                    "team2_id": int(team2_id), "venue_id": int(venue_id),
                    "match_date": match_date.isoformat(), "toss_winner_id": int(toss_winner_id),
                    "toss_decision": toss_decision,
                    "winner_team_id": int(winner_team_id) if winner_team_id else None,
                    "win_margin": int(win_margin) if winner_team_id else None,
                    "win_margin_type": win_margin_type if winner_team_id else None,
                    "player_of_match_id": int(pom_id) if pom_id else None,
                })
                st.success(f"Inserted match_id = {new_id}")
                st.dataframe(read_match(new_id), use_container_width=True, hide_index=True)

with tab_read:
    st.subheader("Look up a match")
    max_id = int(run_sql("SELECT MAX(match_id) AS m FROM matches").iloc[0].m)
    mid = st.number_input("Match ID", min_value=1, max_value=max_id, value=1, key="read_id")
    result = read_match(int(mid))
    if result.empty:
        st.warning("No match with that ID.")
    else:
        st.dataframe(result, use_container_width=True, hide_index=True)

with tab_update:
    st.subheader("Update a match's result")
    max_id = int(run_sql("SELECT MAX(match_id) AS m FROM matches").iloc[0].m)
    mid_u = st.number_input("Match ID", min_value=1, max_value=max_id, value=1, key="update_id")
    existing = read_match(int(mid_u))
    if existing.empty:
        st.warning("No match with that ID.")
    else:
        st.dataframe(existing, use_container_width=True, hide_index=True)
        with st.form("update_form"):
            new_margin = st.number_input("New win margin", min_value=0,
                                          value=int(existing.iloc[0].win_margin or 0))
            new_decision = st.selectbox("New toss decision", ["Bat", "Field"],
                                         index=0 if existing.iloc[0].toss_decision == "Bat" else 1)
            if st.form_submit_button("Apply update", type="primary"):
                rows = update_match(int(mid_u), win_margin=int(new_margin), toss_decision=new_decision)
                st.success(f"Updated {rows} row(s).")
                st.dataframe(read_match(int(mid_u)), use_container_width=True, hide_index=True)

with tab_delete:
    st.subheader("Delete a match")
    max_id = int(run_sql("SELECT MAX(match_id) AS m FROM matches").iloc[0].m)
    mid_d = st.number_input("Match ID", min_value=1, max_value=max_id, value=1, key="delete_id")
    existing_d = read_match(int(mid_d))
    if existing_d.empty:
        st.warning("No match with that ID.")
    else:
        st.dataframe(existing_d, use_container_width=True, hide_index=True)
        confirm = st.checkbox("I understand this permanently deletes the match row.")
        if st.button("Delete match", type="secondary", disabled=not confirm):
            rows = delete_match(int(mid_d))
            st.success(f"Deleted {rows} row(s).")
