import streamlit as st

from utils.database import (
    get_connection, run_sql, match_player_lookup,
    create_batting_score, read_batting_score, update_batting_score, delete_batting_score,
    create_bowling_score, read_bowling_score, update_bowling_score, delete_bowling_score,
)

st.set_page_config(page_title="Scores CRUD · Cricbuzz LiveStats", page_icon="🧮", layout="wide")
get_connection()

st.title("🧮 Scores CRUD")
st.caption(
    "Transaction-safe Create / Read / Update / Delete against the innings-level score tables — "
    "`batting_scorecards` and `bowling_scorecards`. Same commit-or-rollback pattern as **Matches CRUD**, "
    "scoped to individual player performances within a match."
)

lut = match_player_lookup()
score_type = st.radio("Scorecard type", ["🏏 Batting", "🎯 Bowling"], horizontal=True)

st.divider()

# =====================================================================
# BATTING SCORECARDS
# =====================================================================
if score_type == "🏏 Batting":
    tab_create, tab_read, tab_update, tab_delete = st.tabs(["➕ Create", "🔎 Read", "✏️ Update", "🗑️ Delete"])

    with tab_create:
        st.subheader("Insert a new batting entry")
        with st.form("bat_create_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                match_id = st.selectbox(
                    "Match", lut["matches"].match_id,
                    format_func=lambda x: f"#{x} — " +
                    lut["matches"].set_index("match_id").loc[x, "format"] + " · " +
                    str(lut["matches"].set_index("match_id").loc[x, "match_date"]))
                player_id = st.selectbox(
                    "Player", lut["players"].player_id,
                    format_func=lambda x: lut["players"].set_index("player_id").loc[x, "player_name"])
                team_id = st.selectbox(
                    "Team", lut["teams"].team_id,
                    format_func=lambda x: lut["teams"].set_index("team_id").loc[x, "team_name"])
            with c2:
                runs = st.number_input("Runs", min_value=0, value=0)
                balls_faced = st.number_input("Balls faced", min_value=1, value=1)
                fours = st.number_input("Fours", min_value=0, value=0)
            with c3:
                sixes = st.number_input("Sixes", min_value=0, value=0)
                is_out = st.selectbox("Status", ["Out", "Not Out"])
                strike_rate = round(runs / max(balls_faced, 1) * 100, 2)
                st.metric("Strike rate (auto)", strike_rate)

            submitted = st.form_submit_button("Insert batting score", type="primary")
            if submitted:
                new_id = create_batting_score({
                    "match_id": int(match_id), "player_id": int(player_id), "team_id": int(team_id),
                    "runs": int(runs), "balls_faced": int(balls_faced), "fours": int(fours),
                    "sixes": int(sixes), "strike_rate": strike_rate, "is_out": 1 if is_out == "Out" else 0,
                })
                st.success(f"Inserted scorecard_id = {new_id}")
                st.dataframe(read_batting_score(new_id), use_container_width=True, hide_index=True)

    with tab_read:
        st.subheader("Look up a batting entry")
        max_id = int(run_sql("SELECT MAX(scorecard_id) AS m FROM batting_scorecards").iloc[0].m)
        sid = st.number_input("Scorecard ID", min_value=1, max_value=max_id, value=1, key="bat_read_id")
        result = read_batting_score(int(sid))
        if result.empty:
            st.warning("No batting entry with that ID.")
        else:
            st.dataframe(result, use_container_width=True, hide_index=True)

    with tab_update:
        st.subheader("Update a batting entry")
        max_id = int(run_sql("SELECT MAX(scorecard_id) AS m FROM batting_scorecards").iloc[0].m)
        sid_u = st.number_input("Scorecard ID", min_value=1, max_value=max_id, value=1, key="bat_update_id")
        existing = read_batting_score(int(sid_u))
        if existing.empty:
            st.warning("No batting entry with that ID.")
        else:
            st.dataframe(existing, use_container_width=True, hide_index=True)
            with st.form("bat_update_form"):
                new_runs = st.number_input("New runs", min_value=0, value=int(existing.iloc[0].runs))
                new_balls = st.number_input("New balls faced", min_value=1, value=int(existing.iloc[0].balls_faced))
                new_sr = round(new_runs / max(new_balls, 1) * 100, 2)
                if st.form_submit_button("Apply update", type="primary"):
                    rows = update_batting_score(int(sid_u), runs=int(new_runs),
                                                 balls_faced=int(new_balls), strike_rate=new_sr)
                    st.success(f"Updated {rows} row(s).")
                    st.dataframe(read_batting_score(int(sid_u)), use_container_width=True, hide_index=True)

    with tab_delete:
        st.subheader("Delete a batting entry")
        max_id = int(run_sql("SELECT MAX(scorecard_id) AS m FROM batting_scorecards").iloc[0].m)
        sid_d = st.number_input("Scorecard ID", min_value=1, max_value=max_id, value=1, key="bat_delete_id")
        existing_d = read_batting_score(int(sid_d))
        if existing_d.empty:
            st.warning("No batting entry with that ID.")
        else:
            st.dataframe(existing_d, use_container_width=True, hide_index=True)
            confirm = st.checkbox("I understand this permanently deletes the batting row.", key="bat_confirm")
            if st.button("Delete batting entry", type="secondary", disabled=not confirm):
                rows = delete_batting_score(int(sid_d))
                st.success(f"Deleted {rows} row(s).")

# =====================================================================
# BOWLING SCORECARDS
# =====================================================================
else:
    tab_create, tab_read, tab_update, tab_delete = st.tabs(["➕ Create", "🔎 Read", "✏️ Update", "🗑️ Delete"])

    with tab_create:
        st.subheader("Insert a new bowling entry")
        with st.form("bowl_create_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                match_id = st.selectbox(
                    "Match", lut["matches"].match_id,
                    format_func=lambda x: f"#{x} — " +
                    lut["matches"].set_index("match_id").loc[x, "format"] + " · " +
                    str(lut["matches"].set_index("match_id").loc[x, "match_date"]),
                    key="bowl_match")
                player_id = st.selectbox(
                    "Player", lut["players"].player_id,
                    format_func=lambda x: lut["players"].set_index("player_id").loc[x, "player_name"],
                    key="bowl_player")
                team_id = st.selectbox(
                    "Team", lut["teams"].team_id,
                    format_func=lambda x: lut["teams"].set_index("team_id").loc[x, "team_name"],
                    key="bowl_team")
            with c2:
                overs = st.number_input("Overs", min_value=0.0, value=4.0, step=0.1)
                runs_conceded = st.number_input("Runs conceded", min_value=0, value=0)
                wickets = st.number_input("Wickets", min_value=0, max_value=10, value=0)
            with c3:
                maidens = st.number_input("Maidens", min_value=0, value=0)
                economy = round(runs_conceded / max(overs, 0.1), 2)
                st.metric("Economy (auto)", economy)

            submitted = st.form_submit_button("Insert bowling score", type="primary")
            if submitted:
                new_id = create_bowling_score({
                    "match_id": int(match_id), "player_id": int(player_id), "team_id": int(team_id),
                    "overs": float(overs), "runs_conceded": int(runs_conceded), "wickets": int(wickets),
                    "economy": economy, "maidens": int(maidens),
                })
                st.success(f"Inserted bowling_id = {new_id}")
                st.dataframe(read_bowling_score(new_id), use_container_width=True, hide_index=True)

    with tab_read:
        st.subheader("Look up a bowling entry")
        max_id = int(run_sql("SELECT MAX(bowling_id) AS m FROM bowling_scorecards").iloc[0].m)
        bid = st.number_input("Bowling ID", min_value=1, max_value=max_id, value=1, key="bowl_read_id")
        result = read_bowling_score(int(bid))
        if result.empty:
            st.warning("No bowling entry with that ID.")
        else:
            st.dataframe(result, use_container_width=True, hide_index=True)

    with tab_update:
        st.subheader("Update a bowling entry")
        max_id = int(run_sql("SELECT MAX(bowling_id) AS m FROM bowling_scorecards").iloc[0].m)
        bid_u = st.number_input("Bowling ID", min_value=1, max_value=max_id, value=1, key="bowl_update_id")
        existing = read_bowling_score(int(bid_u))
        if existing.empty:
            st.warning("No bowling entry with that ID.")
        else:
            st.dataframe(existing, use_container_width=True, hide_index=True)
            with st.form("bowl_update_form"):
                new_wkts = st.number_input("New wickets", min_value=0, max_value=10,
                                            value=int(existing.iloc[0].wickets))
                new_runs_c = st.number_input("New runs conceded", min_value=0,
                                              value=int(existing.iloc[0].runs_conceded))
                new_econ = round(new_runs_c / max(float(existing.iloc[0].overs), 0.1), 2)
                if st.form_submit_button("Apply update", type="primary"):
                    rows = update_bowling_score(int(bid_u), wickets=int(new_wkts),
                                                 runs_conceded=int(new_runs_c), economy=new_econ)
                    st.success(f"Updated {rows} row(s).")
                    st.dataframe(read_bowling_score(int(bid_u)), use_container_width=True, hide_index=True)

    with tab_delete:
        st.subheader("Delete a bowling entry")
        max_id = int(run_sql("SELECT MAX(bowling_id) AS m FROM bowling_scorecards").iloc[0].m)
        bid_d = st.number_input("Bowling ID", min_value=1, max_value=max_id, value=1, key="bowl_delete_id")
        existing_d = read_bowling_score(int(bid_d))
        if existing_d.empty:
            st.warning("No bowling entry with that ID.")
        else:
            st.dataframe(existing_d, use_container_width=True, hide_index=True)
            confirm = st.checkbox("I understand this permanently deletes the bowling row.", key="bowl_confirm")
            if st.button("Delete bowling entry", type="secondary", disabled=not confirm):
                rows = delete_bowling_score(int(bid_d))
                st.success(f"Deleted {rows} row(s).")
