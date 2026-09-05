"""
Cricbuzz LiveStats — Data Layer
================================
Owns the SQLite schema, synthetic-data generator (offline demo mode),
the optional live Cricbuzz (RapidAPI) client, and the CRUD helpers.

Design notes
------------
* One cached connection per Streamlit session (`get_connection`).
* `USE_LIVE_API` is decided at runtime from `st.secrets` / env vars —
  never hardcode a key in source. If no key is configured the app
  runs entirely on the synthetic dataset, which is schema-identical
  to what the live API would populate.
"""

from __future__ import annotations

import os
import math
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cricbuzz_livestats.db"
DB_PATH.parent.mkdir(exist_ok=True)

RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

TEAMS = ["India", "Australia", "England", "New Zealand", "Pakistan",
         "South Africa", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan"]
FIRST_NAMES = ["Rohit", "Virat", "Steve", "Joe", "Kane", "Babar", "Quinton", "Shai", "Shakib", "Rashid",
               "Jasprit", "Pat", "Trent", "Mitchell", "Fakhar", "David", "Ben", "Marnus", "Rassie", "Mushfiqur",
               "Suryakumar", "Glenn", "Jos", "Devon", "Shaheen", "Kagiso", "Wanindu", "Rishabh", "Travis", "Hardik"]
LAST_NAMES = ["Sharma", "Kohli", "Smith", "Root", "Williamson", "Azam", "de Kock", "Hope", "Al Hasan", "Khan",
              "Bumrah", "Cummins", "Boult", "Starc", "Zaman", "Warner", "Stokes", "Labuschagne", "van der Dussen",
              "Rahim", "Yadav", "Maxwell", "Buttler", "Conway", "Afridi", "Rabada", "Fernando", "Pant", "Head", "Pandya"]
ROLES = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]
FORMATS = ["T20I", "ODI", "Test"]
VENUE_CITIES = ["Mumbai", "Melbourne", "London", "Auckland", "Lahore", "Johannesburg", "Colombo",
                "Bridgetown", "Dhaka", "Kabul", "Chennai", "Sydney", "Manchester", "Wellington", "Karachi"]

SCHEMA_SQL = """
DROP TABLE IF EXISTS bowling_scorecards;
DROP TABLE IF EXISTS batting_scorecards;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE,
    region TEXT
);

CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    role TEXT,
    batting_style TEXT,
    bowling_style TEXT,
    dob DATE,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE venues (
    venue_id INTEGER PRIMARY KEY,
    venue_name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    capacity INTEGER
);

CREATE TABLE series (
    series_id INTEGER PRIMARY KEY,
    series_name TEXT NOT NULL,
    format TEXT CHECK(format IN ('T20I','ODI','Test')),
    start_date DATE
);

CREATE TABLE matches (
    match_id INTEGER PRIMARY KEY,
    series_id INTEGER NOT NULL,
    format TEXT,
    team1_id INTEGER NOT NULL,
    team2_id INTEGER NOT NULL,
    venue_id INTEGER NOT NULL,
    match_date DATE,
    toss_winner_id INTEGER,
    toss_decision TEXT,
    winner_team_id INTEGER,
    win_margin INTEGER,
    win_margin_type TEXT,
    player_of_match_id INTEGER,
    FOREIGN KEY (series_id) REFERENCES series(series_id),
    FOREIGN KEY (team1_id) REFERENCES teams(team_id),
    FOREIGN KEY (team2_id) REFERENCES teams(team_id),
    FOREIGN KEY (venue_id) REFERENCES venues(venue_id),
    FOREIGN KEY (winner_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (player_of_match_id) REFERENCES players(player_id)
);

CREATE TABLE batting_scorecards (
    scorecard_id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    runs INTEGER, balls_faced INTEGER, fours INTEGER, sixes INTEGER,
    strike_rate REAL, is_out INTEGER,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE bowling_scorecards (
    bowling_id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    overs REAL, runs_conceded INTEGER, wickets INTEGER, economy REAL, maidens INTEGER,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_matches_series ON matches(series_id);
CREATE INDEX idx_matches_venue ON matches(venue_id);
CREATE INDEX idx_bat_match ON batting_scorecards(match_id);
CREATE INDEX idx_bat_player ON batting_scorecards(player_id);
CREATE INDEX idx_bowl_match ON bowling_scorecards(match_id);
CREATE INDEX idx_bowl_player ON bowling_scorecards(player_id);
"""


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_connection() -> sqlite3.Connection:
    """One shared, cached SQLite connection for the whole app session."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.create_function("SQRT", 1, math.sqrt)
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0 or _is_empty(conn):
        _build_schema(conn)
        _seed_synthetic_data(conn)
    return conn


def _is_empty(conn: sqlite3.Connection) -> bool:
    try:
        n = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        return n == 0
    except sqlite3.OperationalError:
        return True


def run_sql(query: str, params: tuple | dict | None = None) -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(query, conn, params=params)


def reset_database():
    """Wipe and regenerate the synthetic dataset (used by the sidebar 'Reset demo data' action)."""
    conn = get_connection()
    _build_schema(conn)
    _seed_synthetic_data(conn)


# --------------------------------------------------------------------------
# Schema + synthetic data
# --------------------------------------------------------------------------

def _build_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def _seed_synthetic_data(conn: sqlite3.Connection, n_matches: int = 120, seed: int = 42):
    np.random.seed(seed)
    random.seed(seed)

    teams_df = pd.DataFrame({
        "team_id": range(1, len(TEAMS) + 1),
        "team_name": TEAMS,
        "region": np.random.choice(["Asia", "Oceania", "Europe", "Africa", "Americas"], len(TEAMS)),
    })

    rows, pid = [], 1
    for _, t in teams_df.iterrows():
        for _ in range(15):
            rows.append({
                "player_id": pid,
                "player_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "team_id": t.team_id,
                "role": np.random.choice(ROLES, p=[0.4, 0.3, 0.2, 0.1]),
                "batting_style": np.random.choice(["Right-hand bat", "Left-hand bat"], p=[0.75, 0.25]),
                "bowling_style": np.random.choice(
                    ["Right-arm fast", "Left-arm fast", "Right-arm off-spin", "Left-arm orthodox", "Leg-spin", "None"],
                    p=[0.25, 0.15, 0.2, 0.1, 0.15, 0.15]),
                "dob": (datetime(1988, 1, 1) + timedelta(days=int(np.random.uniform(0, 365 * 15)))).date(),
            })
            pid += 1
    players_df = pd.DataFrame(rows)

    n_venues = 15
    venues_df = pd.DataFrame({
        "venue_id": range(1, n_venues + 1),
        "venue_name": [f"{c} International Stadium" for c in VENUE_CITIES[:n_venues]],
        "city": VENUE_CITIES[:n_venues],
        "country": np.random.choice(
            ["India", "Australia", "England", "NZ", "Pakistan", "SA", "SL", "WI", "Bangladesh", "Afghanistan"],
            n_venues),
        "capacity": np.random.randint(15000, 100000, n_venues),
    })

    n_series = 6
    starts = [datetime(2022, 1, 1) + timedelta(days=int(d)) for d in np.random.uniform(0, 900, n_series)]
    series_df = pd.DataFrame({
        "series_id": range(1, n_series + 1),
        "series_name": [f"{random.choice(TEAMS)} tour of {random.choice(TEAMS)} {s.year}" for s in starts],
        "format": np.random.choice(FORMATS, n_series),
        "start_date": [s.date() for s in starts],
    })

    match_rows = []
    for mid in range(1, n_matches + 1):
        t1, t2 = np.random.choice(teams_df.team_id, 2, replace=False)
        series = series_df.sample(1).iloc[0]
        venue = venues_df.sample(1).iloc[0]
        m_date = series.start_date + timedelta(days=int(np.random.uniform(0, 25)))
        toss_winner = np.random.choice([t1, t2])
        toss_decision = np.random.choice(["Bat", "Field"])
        margin_type = np.random.choice(["runs", "wickets"])
        margin = np.random.randint(1, 120) if margin_type == "runs" else np.random.randint(1, 10)
        winner = np.random.choice([t1, t2, None], p=[0.47, 0.47, 0.06])
        match_rows.append({
            "match_id": mid, "series_id": series.series_id, "format": series.format,
            "team1_id": t1, "team2_id": t2, "venue_id": venue.venue_id, "match_date": m_date,
            "toss_winner_id": toss_winner, "toss_decision": toss_decision,
            "winner_team_id": winner, "win_margin": margin if winner is not None else None,
            "win_margin_type": margin_type if winner is not None else None,
            "player_of_match_id": None,
        })
    matches_df = pd.DataFrame(match_rows)

    bat_rows, bowl_rows = [], []
    bat_id = bowl_id = 1
    pom_by_match = {}
    for _, m in matches_df.iterrows():
        for team_id in [m.team1_id, m.team2_id]:
            squad = players_df[players_df.team_id == team_id].sample(11)
            batters = squad[squad.role != "Bowler"].sample(min(8, len(squad[squad.role != "Bowler"])))
            best_score, best_player = -1, None
            for _, p in batters.iterrows():
                runs = int(np.random.gamma(2.2, 18))
                balls = max(runs, int(runs / np.random.uniform(0.55, 1.3)) + np.random.randint(0, 10))
                fours = int(np.random.poisson(runs / 12))
                sixes = int(np.random.poisson(runs / 30))
                bat_rows.append({
                    "scorecard_id": bat_id, "match_id": m.match_id, "player_id": p.player_id,
                    "team_id": team_id, "runs": runs, "balls_faced": max(balls, 1), "fours": fours,
                    "sixes": sixes, "strike_rate": round(runs / max(balls, 1) * 100, 2),
                    "is_out": bool(np.random.choice([True, False], p=[0.82, 0.18])),
                })
                impact = runs + fours * 1 + sixes * 2
                if impact > best_score:
                    best_score, best_player = impact, p.player_id
                bat_id += 1

            bowlers = squad[squad.role.isin(["Bowler", "All-Rounder"])]
            if len(bowlers) == 0:
                bowlers = squad.sample(3)
            for _, p in bowlers.iterrows():
                overs = round(np.random.uniform(2, 10) * 2) / 2
                economy = round(np.random.uniform(3.5, 10.5), 2)
                runs_conceded = int(overs * economy)
                wkts = int(np.random.choice([0, 1, 2, 3, 4, 5], p=[0.30, 0.28, 0.20, 0.12, 0.07, 0.03]))
                bowl_rows.append({
                    "bowling_id": bowl_id, "match_id": m.match_id, "player_id": p.player_id,
                    "team_id": team_id, "overs": overs, "runs_conceded": runs_conceded,
                    "wickets": wkts, "economy": economy, "maidens": int(np.random.poisson(0.3)),
                })
                bowl_id += 1
            if random.random() < 0.5 and best_player is not None:
                pom_by_match[m.match_id] = best_player
        if m.match_id not in pom_by_match:
            pom_by_match[m.match_id] = players_df[
                players_df.team_id.isin([m.team1_id, m.team2_id])].sample(1).iloc[0].player_id

    matches_df["player_of_match_id"] = matches_df.match_id.map(pom_by_match)
    batting_df = pd.DataFrame(bat_rows)
    bowling_df = pd.DataFrame(bowl_rows)

    teams_df.to_sql("teams", conn, if_exists="append", index=False)
    players_df.to_sql("players", conn, if_exists="append", index=False)
    venues_df.to_sql("venues", conn, if_exists="append", index=False)
    series_df.to_sql("series", conn, if_exists="append", index=False)
    matches_df.to_sql("matches", conn, if_exists="append", index=False)
    batting_df.to_sql("batting_scorecards", conn, if_exists="append", index=False)
    bowling_df.to_sql("bowling_scorecards", conn, if_exists="append", index=False)
    conn.commit()


# --------------------------------------------------------------------------
# Live API client (optional — only used when a key is configured)
# --------------------------------------------------------------------------

def get_api_key() -> str:
    try:
        return st.secrets.get("RAPIDAPI_KEY", "")
    except Exception:
        return os.environ.get("RAPIDAPI_KEY", "")


def live_api_available() -> bool:
    return bool(get_api_key())


def fetch_endpoint(path: str, retries: int = 2, backoff: float = 0.8) -> dict:
    """GET a Cricbuzz RapidAPI endpoint with retry/backoff. Raises on final failure."""
    key = get_api_key()
    headers = {"X-RapidAPI-Key": key, "X-RapidAPI-Host": RAPIDAPI_HOST}
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                import time
                time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"Cricbuzz API request failed after {retries + 1} attempts: {last_exc}")


def get_live_matches() -> dict:
    return fetch_endpoint("/matches/v1/live")


def get_recent_matches() -> dict:
    return fetch_endpoint("/matches/v1/recent")


def get_upcoming_matches() -> dict:
    return fetch_endpoint("/matches/v1/upcoming")


# --------------------------------------------------------------------------
# CRUD (matches table — demonstrates transaction-safe insert/update/delete)
# --------------------------------------------------------------------------

def create_match(record: dict) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""INSERT INTO matches
            (series_id, format, team1_id, team2_id, venue_id, match_date, toss_winner_id,
             toss_decision, winner_team_id, win_margin, win_margin_type, player_of_match_id)
            VALUES (:series_id,:format,:team1_id,:team2_id,:venue_id,:match_date,:toss_winner_id,
                    :toss_decision,:winner_team_id,:win_margin,:win_margin_type,:player_of_match_id)""",
                            record)
        return cur.lastrowid


def read_match(match_id: int) -> pd.DataFrame:
    return run_sql("SELECT * FROM matches WHERE match_id = ?", (match_id,))


def update_match(match_id: int, **fields) -> int:
    conn = get_connection()
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["match_id"] = match_id
    with conn:
        cur = conn.execute(f"UPDATE matches SET {set_clause} WHERE match_id = :match_id", fields)
        return cur.rowcount


def delete_match(match_id: int) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
        return cur.rowcount


# --------------------------------------------------------------------------
# CRUD (batting_scorecards / bowling_scorecards — "Scores" tables)
# --------------------------------------------------------------------------

def create_batting_score(record: dict) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""INSERT INTO batting_scorecards
            (match_id, player_id, team_id, runs, balls_faced, fours, sixes, strike_rate, is_out)
            VALUES (:match_id,:player_id,:team_id,:runs,:balls_faced,:fours,:sixes,:strike_rate,:is_out)""",
                            record)
        return cur.lastrowid


def read_batting_score(scorecard_id: int) -> pd.DataFrame:
    return run_sql("""
        SELECT bs.*, p.player_name, t.team_name
        FROM batting_scorecards bs
        JOIN players p ON p.player_id = bs.player_id
        JOIN teams t ON t.team_id = bs.team_id
        WHERE bs.scorecard_id = ?""", (scorecard_id,))


def update_batting_score(scorecard_id: int, **fields) -> int:
    conn = get_connection()
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["scorecard_id"] = scorecard_id
    with conn:
        cur = conn.execute(f"UPDATE batting_scorecards SET {set_clause} WHERE scorecard_id = :scorecard_id", fields)
        return cur.rowcount


def delete_batting_score(scorecard_id: int) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("DELETE FROM batting_scorecards WHERE scorecard_id = ?", (scorecard_id,))
        return cur.rowcount


def create_bowling_score(record: dict) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""INSERT INTO bowling_scorecards
            (match_id, player_id, team_id, overs, runs_conceded, wickets, economy, maidens)
            VALUES (:match_id,:player_id,:team_id,:overs,:runs_conceded,:wickets,:economy,:maidens)""",
                            record)
        return cur.lastrowid


def read_bowling_score(bowling_id: int) -> pd.DataFrame:
    return run_sql("""
        SELECT bo.*, p.player_name, t.team_name
        FROM bowling_scorecards bo
        JOIN players p ON p.player_id = bo.player_id
        JOIN teams t ON t.team_id = bo.team_id
        WHERE bo.bowling_id = ?""", (bowling_id,))


def update_bowling_score(bowling_id: int, **fields) -> int:
    conn = get_connection()
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["bowling_id"] = bowling_id
    with conn:
        cur = conn.execute(f"UPDATE bowling_scorecards SET {set_clause} WHERE bowling_id = :bowling_id", fields)
        return cur.rowcount


def delete_bowling_score(bowling_id: int) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("DELETE FROM bowling_scorecards WHERE bowling_id = ?", (bowling_id,))
        return cur.rowcount


def match_player_lookup() -> dict:
    """Small lookups used to populate the Scores CRUD dropdowns."""
    conn = get_connection()
    return {
        "matches": pd.read_sql("SELECT match_id, match_date, format FROM matches ORDER BY match_id DESC", conn),
        "players": pd.read_sql(
            "SELECT player_id, player_name, team_id FROM players ORDER BY player_name", conn),
        "teams": pd.read_sql("SELECT team_id, team_name FROM teams ORDER BY team_name", conn),
    }


def lookup_tables() -> dict:
    """Small dimension tables used to populate CRUD dropdowns."""
    conn = get_connection()
    return {
        "teams": pd.read_sql("SELECT team_id, team_name FROM teams ORDER BY team_name", conn),
        "venues": pd.read_sql("SELECT venue_id, venue_name FROM venues ORDER BY venue_name", conn),
        "series": pd.read_sql("SELECT series_id, series_name FROM series ORDER BY series_name", conn),
        "players": pd.read_sql("SELECT player_id, player_name FROM players ORDER BY player_name", conn),
    }
