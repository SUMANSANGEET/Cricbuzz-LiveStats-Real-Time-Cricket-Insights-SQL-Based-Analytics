# 🏏 Cricbuzz LiveStats — Real-Time Cricket Insights & SQL-Based Analytics

A recruiter-friendly, interactive Streamlit dashboard built on top of the Cricbuzz LiveStats
capstone: a REST API integration layer, a normalized SQLite warehouse, 25 tiered SQL analytics
questions, and a transaction-safe CRUD module.

**Author:** P Suman Sangeet · LABMENTIX Data Analytics & AI Cohort

## Pages

| Page | What it shows |
|---|---|
| **Home** | KPI snapshot, project summary, architecture at a glance |
| **SQL Analytics** | All 25 questions (Beginner → Advanced), each with its SQL, result table, and live Plotly chart |
| **Scores** | Fixture explorer + full batting/bowling scorecard lookup; switches to real Cricbuzz data automatically if an API key is configured |
| **Player Explorer** | Search any player's career snapshot, or compare two players head-to-head on a radar chart |
| **Matches CRUD** | Insert / Read / Update / Delete `matches` records, wrapped in commit-or-rollback transactions |
| **Scores CRUD** | Insert / Read / Update / Delete individual `batting_scorecards` / `bowling_scorecards` rows |
| **Advanced Visualizations** | Chart-only gallery of the 13 Advanced-tier SQL questions (Q13–Q25) plus two executive summary visuals |
| **Analytics Overview** | Recruiter-facing executive summary: KPI snapshot, headline insights, dataset/performance-environment cards, and a **1-click downloadable PDF summary** |
| **Interactive Dashboard** | Live team / format / date-range filters that recompute KPIs, a win-trend chart, a toss-impact gauge, and a **world venue map** in real time — the one page where every visual reacts to your selection |
| **About** | Architecture diagram, ER schema, tech stack, deployment notes |

> **Note on the venue map:** it uses Plotly's `scatter_geo`, which loads world boundary data from Plotly's CDN on first render. It needs normal outbound internet access (any regular browser, Streamlit Community Cloud, etc.) — it won't render in a fully air-gapped environment.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The first run creates `data/cricbuzz_livestats.db` and seeds it with a 120-match / 150-player
synthetic dataset — no external API key required.

## Enable live Cricbuzz data (optional)

1. Get a RapidAPI key for the [Cricbuzz Cricket API](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket).
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste your key in.
3. Restart the app — the **Scores** page automatically switches from demo mode to live data.
   Never commit `secrets.toml`; it's already in `.gitignore`.

## Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repo.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py`.
3. Add `RAPIDAPI_KEY` under the app's **Secrets** panel if you want live data.
4. Deploy — dependencies install automatically from `requirements.txt`.

## Deploy with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Project structure

```
cricbuzz_app/
├── app.py                      # Home page (entry point)
├── pages/
│   ├── 1_📊_SQL_Analytics.py
│   ├── 2_🏏_Scores.py
│   ├── 3_🔍_Player_Explorer.py
│   ├── 4_🗂️_Matches_CRUD.py
│   ├── 5_🧮_Scores_CRUD.py
│   ├── 6_📈_Advanced_Visualizations.py
│   ├── 7_🧭_Analytics_Overview.py
│   ├── 8_ℹ️_About.py
│   └── 9_🎛️_Interactive_Dashboard.py
├── utils/
│   ├── database.py             # schema, synthetic data, connection, CRUD, live API client
│   ├── queries.py               # all 25 SQL questions + chart builders + shared postprocess()
│   ├── kpi.py                   # shared KPI-strip figure builder (Home + Analytics Overview)
│   ├── filters.py                # reusable team/format/date-range filter bar → SQL WHERE clause
│   └── report.py                 # builds the 1-page PDF executive summary (reportlab)
├── data/                        # SQLite db (gitignored)
├── .streamlit/
│   ├── config.toml               # theme
│   └── secrets.toml.example
├── requirements.txt
└── README.md
```
