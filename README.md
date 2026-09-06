<div align="center">

# 🏏 Cricbuzz LiveStats
### Real-Time Cricket Insights & SQL-Based Analytics

**An end-to-end sports-data-analytics platform** — REST API integration, a normalized SQL warehouse, 25 tiered SQL analytics questions, transaction-safe CRUD, and an interactive multi-page dashboard.

[![Live App](https://img.shields.io/badge/🚀_Live_App-Streamlit_Cloud-FF4B4B?style=for-the-badge)](https://dvhypq3fq8gunazckoz8wt.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)

**[🔗 Try the live app →](https://dvhypq3fq8gunazckoz8wt.streamlit.app/)**

</div>

---

## 📖 Overview

Cricket generates a continuous stream of data — matches, players, teams, venues, series, batting and bowling scorecards — but raw feeds and disconnected spreadsheets can't answer the questions that actually matter: *Who's in form right now? Which venue favors batting? Does winning the toss really matter?*

**Cricbuzz LiveStats** turns that raw data into a queryable warehouse and a recruiter-facing interactive dashboard, built to demonstrate a complete data-engineering-to-BI pipeline:

```
Cricbuzz REST API  →  Normalized SQLite Warehouse  →  25-Question SQL Analytics Layer  →  Streamlit Dashboard
   (RapidAPI)             (3NF, 7 FK indexes)         (window fns, CTEs, ranking)         (Plotly visuals)
```

When no API key is configured, the app runs seamlessly on a **schema-identical synthetic dataset** (120 matches, 150 players) — every page, query, and chart works exactly the same way, so the project is fully demoable offline.

---

## ✨ Features

| Page | What it does |
|---|---|
| 🏠 **Home** | Recruiter-facing KPI dashboard (matches, players, teams, venues, avg runs, avg economy), business problem & architecture summary |
| 📊 **SQL Analytics** | All **25 SQL questions** — Beginner → Intermediate → Advanced — each with its query, live result table, and a matching Plotly visualization |
| 🏏 **Scores** | Fixture explorer with full batting/bowling scorecards; automatically switches from synthetic data to live Cricbuzz data when an API key is present |
| 🔍 **Player Explorer** | Search any player's career batting/bowling snapshot, or compare two players head-to-head on a radar chart |
| 🛠️ **Matches CRUD** / **Scores CRUD** | Transaction-safe Create / Read / Update / Delete on match and scorecard records, with commit-or-rollback safety |
| 📈 **Advanced Visualizations** | A curated highlight reel of the project's most insightful charts |
| 🧾 **Analytics Overview** | Executive summary of key findings and dataset-wide insights |
| ℹ️ **About** | Architecture diagram, ER schema, tech stack, and deployment notes |

---

## 🧠 The 25 SQL Analytics Questions

<details>
<summary><b>🟢 Beginner (Q1–Q6)</b> — aggregation, filtering, sorting</summary>

1. Top 10 all-time run scorers
2. Top 10 wicket-takers
3. Team-wise match win percentage
4. Highest-scoring venues (avg runs/innings)
5. Match format distribution (T20I / ODI / Test)
6. Toss decision trend (bat vs field first)

</details>

<details>
<summary><b>🟡 Intermediate (Q7–Q12)</b> — joins, subqueries, ratios</summary>

7. Strike-rate leaders (min. 300 balls faced)
8. Best economy rates (min. 20 overs)
9. Top rivalries by matches played
10. Toss impact on match outcome
11. Player-of-the-Match frequency
12. Century & half-century count per player

</details>

<details>
<summary><b>🔴 Advanced (Q13–Q25)</b> — window functions, CTEs, ranking, time series</summary>

13. Leading run-scorer per team (`RANK()` window function)
14. Cumulative team wins over time
15. Best batting partnerships
16. Consistency index (standard deviation of runs)
17. Best bowling spells (5-wicket-haul flag)
18. Home vs away win percentage
19. Most consistent batsmen since 2022
20. Format-wise workload & batting average (Test/ODI/T20I split)
21. Composite performance ranking (weighted batting + bowling formula)
22. Head-to-head prediction analysis (rivalries with 5+ meetings)
23. Recent form & momentum (last-10-innings trend)
24. Best partnership combinations by success rate
25. Career trajectory classification (Ascending / Declining / Stable)

</details>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT APP LAYER                       │
│  Home · SQL Analytics · Scores · Player Explorer · CRUD · About  │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                 │
        ┌────────▼─────────┐             ┌─────────▼─────────┐
        │  ANALYTICS LAYER   │             │    CRUD LAYER      │
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

### Database schema (3NF, 7 tables)

```sql
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
```

Indexes on every foreign key for join performance.

---

## 🧰 Tech Stack

| Category | Tools |
|---|---|
| **Language** | Python 3.11 |
| **Database** | SQLite (embedded, zero-config, 3NF) |
| **Data processing** | Pandas, NumPy |
| **API integration** | `requests` with retry/backoff · Cricbuzz Cricket API (RapidAPI) |
| **App framework** | Streamlit (multi-page) |
| **Visualization** | Plotly Express / Graph Objects |
| **Engineering practices** | Parameterized queries (SQL-injection safe), transaction-wrapped CRUD, secrets-based key management (no hardcoded credentials) |

---

## 🚀 Getting Started

### Run locally

```bash
git clone <your-repo-url>
cd cricbuzz-livestats
pip install -r requirements.txt
streamlit run app.py
```

The first run builds the SQLite warehouse and seeds it with a 120-match / 150-player synthetic dataset — **no API key required.**

### Enable live Cricbuzz data (optional)

1. Get a RapidAPI key for the [Cricbuzz Cricket API](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket).
2. Create `.streamlit/secrets.toml`:
   ```toml
   RAPIDAPI_KEY = "your-key-here"
   ```
3. Restart the app — it automatically switches from demo mode to live data. `secrets.toml` is git-ignored; never commit real keys.

### Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py`.
3. (Optional) add `RAPIDAPI_KEY` under the app's **Secrets** panel for live data.
4. Deploy — dependencies install automatically from `requirements.txt`.

---

## 💡 Key Insights

- Run volume and strike rate don't always move together — the highest-strike-rate players aren't always the top accumulators, a classic anchor-vs-finisher trade-off.
- Toss impact on match outcome is measurable but modest, not decisive.
- Career-trajectory analysis flags players trending up or down over time — more actionable for scouting than a flat career average.

---

## 👤 Author

**P Suman Sangeet**
Data Science & AI Intern · LABMENTIX Data Analytics and AI 

---

<div align="center">

**[🔗 View the live dashboard](https://dvhypq3fq8gunazckoz8wt.streamlit.app/)**

</div>
