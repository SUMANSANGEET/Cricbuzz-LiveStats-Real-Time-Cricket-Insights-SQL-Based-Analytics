"""
Cricbuzz LiveStats — SQL Analytics Question Bank
=================================================
25 questions (Beginner -> Intermediate -> Advanced), each defined as a dict:
    id, tier, title, business_question, sql, chart(df) -> plotly Figure

Kept separate from the Streamlit page so the SQL itself stays reviewable
and testable independent of the UI.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TIERS = ["Beginner", "Intermediate", "Advanced"]

QUESTIONS = []


def q(id, tier, title, business_question, sql, chart, concepts):
    QUESTIONS.append(dict(id=id, tier=tier, title=title, business_question=business_question,
                           sql=sql.strip(), chart=chart, concepts=concepts))


# ---------------------------------------------------------------- Beginner

q(1, "Beginner", "Top 10 all-time run scorers",
  "Who are our highest career run-scorers, and how efficient are they?",
  """
SELECT p.player_name, t.team_name, SUM(b.runs) AS total_runs, COUNT(*) AS innings,
       ROUND(AVG(b.runs),1) AS avg_runs
FROM batting_scorecards b
JOIN players p ON p.player_id = b.player_id
JOIN teams t ON t.team_id = p.team_id
GROUP BY p.player_id
ORDER BY total_runs DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("total_runs"), x="total_runs", y="player_name", color="team_name",
                     orientation="h", title="Top 10 Run Scorers (All Formats)",
                     labels={"total_runs": "Total Runs", "player_name": "Player"}).update_layout(height=450),
  "SELECT, JOIN, GROUP BY, ORDER BY, LIMIT")

q(2, "Beginner", "Top 10 wicket-takers",
  "Which bowlers have taken the most wickets, and at what average?",
  """
SELECT p.player_name, t.team_name, SUM(bo.wickets) AS total_wickets,
       ROUND(SUM(bo.runs_conceded)*1.0/NULLIF(SUM(bo.wickets),0),2) AS bowling_avg
FROM bowling_scorecards bo
JOIN players p ON p.player_id = bo.player_id
JOIN teams t ON t.team_id = p.team_id
GROUP BY p.player_id
ORDER BY total_wickets DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("total_wickets"), x="total_wickets", y="player_name", color="team_name",
                     orientation="h", title="Top 10 Wicket Takers",
                     labels={"total_wickets": "Wickets"}).update_layout(height=450),
  "Aggregate functions, NULLIF for safe division")

q(3, "Beginner", "Team-wise win percentage",
  "Which teams win most often across every match they've played (as either side)?",
  """
WITH played AS (
  SELECT team1_id AS team_id, match_id FROM matches
  UNION ALL
  SELECT team2_id AS team_id, match_id FROM matches
)
SELECT t.team_name,
       COUNT(*) AS matches_played,
       SUM(CASE WHEN m.winner_team_id = pl.team_id THEN 1 ELSE 0 END) AS wins,
       ROUND(100.0 * SUM(CASE WHEN m.winner_team_id = pl.team_id THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
FROM played pl
JOIN matches m ON m.match_id = pl.match_id
JOIN teams t ON t.team_id = pl.team_id
GROUP BY t.team_name
ORDER BY win_pct DESC;
""",
  lambda df: px.bar(df, x="team_name", y="win_pct", color="win_pct", color_continuous_scale="Tealgrn",
                     title="Team Win Percentage", labels={"win_pct": "Win %", "team_name": "Team"}, text="win_pct")
      .update_traces(texttemplate='%{text}%', textposition='outside')
      .update_layout(height=450, coloraxis_showscale=False),
  "UNION ALL to unpivot two team columns, conditional aggregation")

q(4, "Beginner", "Highest-scoring venues",
  "Which venues produce the highest average innings totals?",
  """
SELECT v.venue_name, v.city, ROUND(AVG(team_runs),1) AS avg_runs_per_innings
FROM (
  SELECT b.match_id, b.team_id, SUM(b.runs) AS team_runs
  FROM batting_scorecards b GROUP BY b.match_id, b.team_id
) inn
JOIN matches m ON m.match_id = inn.match_id
JOIN venues v ON v.venue_id = m.venue_id
GROUP BY v.venue_id
ORDER BY avg_runs_per_innings DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("avg_runs_per_innings"), x="avg_runs_per_innings", y="venue_name",
                     orientation="h", title="Highest Scoring Venues (avg runs/innings)",
                     color="avg_runs_per_innings", color_continuous_scale="Sunset")
      .update_layout(height=450, coloraxis_showscale=False),
  "Derived table (subquery), multi-level GROUP BY")

q(5, "Beginner", "Match format distribution",
  "What's the split of matches across T20I / ODI / Test?",
  "SELECT format, COUNT(*) AS matches FROM matches GROUP BY format;",
  lambda df: px.pie(df, names="format", values="matches", title="Matches by Format", hole=0.45)
      .update_layout(height=420),
  "GROUP BY, COUNT")

q(6, "Beginner", "Toss decision trend",
  "Do captains prefer batting or fielding first after winning the toss?",
  "SELECT toss_decision, COUNT(*) AS n FROM matches GROUP BY toss_decision;",
  lambda df: px.pie(df, names="toss_decision", values="n", title="Toss Decision Split", hole=0.45,
                     color_discrete_sequence=px.colors.qualitative.Set2).update_layout(height=420),
  "GROUP BY, categorical distribution")

# ------------------------------------------------------------ Intermediate

q(7, "Intermediate", "Strike-rate leaders (min. 300 balls)",
  "Who scores fastest among batters with a meaningful sample size?",
  """
SELECT p.player_name, t.team_name, SUM(b.balls_faced) AS balls, SUM(b.runs) AS runs,
       ROUND(SUM(b.runs)*100.0/SUM(b.balls_faced),1) AS career_strike_rate
FROM batting_scorecards b
JOIN players p ON p.player_id=b.player_id
JOIN teams t ON t.team_id=p.team_id
GROUP BY p.player_id
HAVING balls >= 300
ORDER BY career_strike_rate DESC
LIMIT 10;
""",
  lambda df: px.scatter(df, x="balls", y="career_strike_rate", size="runs", color="team_name",
                         hover_name="player_name", title="Strike Rate vs Balls Faced (bubble = career runs)",
                         labels={"balls": "Balls Faced", "career_strike_rate": "Strike Rate"})
      .update_layout(height=450),
  "HAVING filter on aggregate, derived ratio")

q(8, "Intermediate", "Best economy rates (min. 20 overs)",
  "Which bowlers concede the fewest runs per over over a real workload?",
  """
SELECT p.player_name, t.team_name, ROUND(SUM(bo.overs),1) AS overs,
       ROUND(SUM(bo.runs_conceded)*1.0/SUM(bo.overs),2) AS career_economy
FROM bowling_scorecards bo
JOIN players p ON p.player_id=bo.player_id
JOIN teams t ON t.team_id=p.team_id
GROUP BY p.player_id
HAVING overs >= 20
ORDER BY career_economy ASC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("career_economy", ascending=False), x="career_economy", y="player_name",
                     orientation="h", color="team_name", title="Most Economical Bowlers (min 20 overs)",
                     labels={"career_economy": "Economy Rate"}).update_layout(height=450),
  "HAVING, ratio aggregation")

q(9, "Intermediate", "Top rivalries by matches played",
  "Which head-to-head fixtures have been played most often?",
  """
SELECT t1.team_name AS team_a, t2.team_name AS team_b, COUNT(*) AS matches_played
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
GROUP BY MIN(m.team1_id,m.team2_id), MAX(m.team1_id,m.team2_id)
ORDER BY matches_played DESC
LIMIT 10;
""",
  lambda df: px.bar(df, x="matches_played", y=df.team_a + " vs " + df.team_b, orientation="h",
                     title="Top 10 Rivalries by Matches Played",
                     labels={"y": "Fixture", "matches_played": "Matches"}).update_layout(height=450),
  "Symmetric pair grouping with MIN/MAX")

q(10, "Intermediate", "Toss impact on match outcome",
  "Does winning the toss meaningfully raise your odds of winning the match?",
  """
SELECT
  ROUND(100.0*SUM(CASE WHEN toss_winner_id = winner_team_id THEN 1 ELSE 0 END)
        / SUM(CASE WHEN winner_team_id IS NOT NULL THEN 1 ELSE 0 END), 1) AS toss_winner_win_pct
FROM matches;
""",
  lambda df: go.Figure(go.Indicator(
      mode="gauge+number", value=float(df.toss_winner_win_pct[0]),
      title={'text': "Win % When Team Wins the Toss"},
      gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#2E86AB'}})).update_layout(height=350),
  "Conditional aggregation ratio, gauge KPI")

q(11, "Intermediate", "Player-of-the-Match frequency",
  "Who are the most consistent match-winning performers?",
  """
SELECT p.player_name, t.team_name, COUNT(*) AS pom_awards
FROM matches m
JOIN players p ON p.player_id = m.player_of_match_id
JOIN teams t ON t.team_id = p.team_id
GROUP BY p.player_id
ORDER BY pom_awards DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("pom_awards"), x="pom_awards", y="player_name", color="team_name",
                     orientation="h", title="Most Player-of-the-Match Awards").update_layout(height=450),
  "JOIN on a nullable FK, COUNT")

q(12, "Intermediate", "Batting milestones (100s & 50s)",
  "Who has the most centuries and half-centuries?",
  """
SELECT p.player_name, t.team_name,
       SUM(CASE WHEN b.runs>=100 THEN 1 ELSE 0 END) AS centuries,
       SUM(CASE WHEN b.runs>=50 AND b.runs<100 THEN 1 ELSE 0 END) AS fifties
FROM batting_scorecards b
JOIN players p ON p.player_id=b.player_id
JOIN teams t ON t.team_id=p.team_id
GROUP BY p.player_id
HAVING centuries + fifties > 0
ORDER BY centuries DESC, fifties DESC
LIMIT 10;
""",
  lambda df: px.bar(df, x="player_name", y=["centuries", "fifties"], barmode="stack",
                     title="Batting Milestones by Player (Top 10)",
                     labels={"value": "Count", "variable": "Milestone"}).update_layout(height=450, xaxis_tickangle=-30),
  "CASE-based bucketing, stacked bars")

# ------------------------------------------------------------------ Advanced (13-18)

q(13, "Advanced", "Leading run-scorer per team",
  "Who is each team's #1 run-scorer?",
  """
WITH team_runs AS (
  SELECT p.team_id, p.player_name, SUM(b.runs) AS total_runs,
         RANK() OVER (PARTITION BY p.team_id ORDER BY SUM(b.runs) DESC) AS team_rank
  FROM batting_scorecards b JOIN players p ON p.player_id=b.player_id
  GROUP BY p.player_id
)
SELECT t.team_name, tr.player_name, tr.total_runs
FROM team_runs tr JOIN teams t ON t.team_id = tr.team_id
WHERE tr.team_rank = 1
ORDER BY tr.total_runs DESC;
""",
  lambda df: px.bar(df.sort_values("total_runs"), x="total_runs", y="team_name", orientation="h",
                     color="total_runs", color_continuous_scale="Viridis", hover_data=["player_name"],
                     title="Leading Run Scorer per Team").update_layout(height=450, coloraxis_showscale=False),
  "RANK() window function, PARTITION BY")

q(14, "Advanced", "Cumulative wins over time",
  "How has each top team's win tally trended across the season?",
  """
WITH results AS (
  SELECT m.match_date, t.team_name
  FROM matches m JOIN teams t ON t.team_id = m.winner_team_id
  WHERE m.winner_team_id IS NOT NULL
)
SELECT match_date, team_name,
       COUNT(*) OVER (PARTITION BY team_name ORDER BY match_date
                       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_wins
FROM results
ORDER BY match_date;
""",
  lambda df: px.line(
      df[df.team_name.isin(df.groupby("team_name").cumulative_wins.max().nlargest(5).index)],
      x="match_date", y="cumulative_wins", color="team_name",
      title="Cumulative Wins Over Time — Top 5 Teams").update_layout(height=450),
  "Running total via window frame (ROWS BETWEEN)")

q(15, "Advanced", "Best batting partnerships",
  "Which pairs of batters have combined for the highest partnership totals?",
  """
SELECT b1.match_id, p1.player_name AS batter_1, p2.player_name AS batter_2,
       t.team_name, (b1.runs + b2.runs) AS combined_runs
FROM batting_scorecards b1
JOIN batting_scorecards b2
  ON b1.match_id = b2.match_id AND b1.team_id = b2.team_id AND b1.player_id < b2.player_id
JOIN players p1 ON p1.player_id = b1.player_id
JOIN players p2 ON p2.player_id = b2.player_id
JOIN teams t ON t.team_id = b1.team_id
ORDER BY combined_runs DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("combined_runs"), x="combined_runs",
                     y=df.batter_1 + " & " + df.batter_2, orientation="h", color="team_name",
                     title="Top 10 Batting Partnerships (combined runs)").update_layout(height=450),
  "Self-join with inequality to enumerate unordered pairs")

q(16, "Advanced", "Consistency index (std. dev of runs)",
  "Which established batters (8+ innings) combine high output with low variance?",
  """
SELECT p.player_id, p.player_name, t.team_name, COUNT(*) AS innings, ROUND(AVG(b.runs), 1) AS avg_runs
FROM batting_scorecards b
JOIN players p ON p.player_id = b.player_id
JOIN teams t ON t.team_id = p.team_id
GROUP BY p.player_id, p.player_name, t.team_name
HAVING COUNT(*) >= 8;
-- stdev computed in a second pass per player using SQLite's registered SQRT()
""",
  lambda df: px.scatter(df, x="avg_runs", y="stdev_runs", size="innings", color="team_name",
                         hover_name="player_name",
                         title="Consistency Map — Avg Runs vs Std. Dev (lower-right = elite)",
                         labels={"avg_runs": "Average Runs", "stdev_runs": "Std Dev (lower = more consistent)"})
      .update_layout(height=450),
  "Two-pass aggregation, custom SQRT() UDF for population std. dev.")

q(17, "Advanced", "Best bowling spells (>=3 wickets)",
  "What are the standout single-innings bowling performances, and which are 5-wicket hauls?",
  """
SELECT p.player_name, t.team_name, m.match_date, bo.wickets, bo.runs_conceded, bo.overs,
       CASE WHEN bo.wickets >= 5 THEN 'Yes' ELSE 'No' END AS five_wicket_haul
FROM bowling_scorecards bo
JOIN players p ON p.player_id = bo.player_id
JOIN teams t ON t.team_id = p.team_id
JOIN matches m ON m.match_id = bo.match_id
WHERE bo.wickets >= 3
ORDER BY bo.wickets DESC, bo.runs_conceded ASC
LIMIT 10;
""",
  lambda df: px.scatter(df, x="runs_conceded", y="wickets", color="five_wicket_haul", size="overs",
                         hover_name="player_name", title="Best Bowling Spells (>=3 wickets)",
                         labels={"runs_conceded": "Runs Conceded", "wickets": "Wickets"}).update_layout(height=450),
  "Multi-column ORDER BY, CASE-derived flag")

q(18, "Advanced", "Home vs away win percentage",
  "Do teams perform better at venues in their own country?",
  """
WITH played AS (
  SELECT m.match_id, m.venue_id, m.winner_team_id, t1.team_id, t1.team_name, v.country
  FROM matches m JOIN teams t1 ON t1.team_id = m.team1_id JOIN venues v ON v.venue_id = m.venue_id
  UNION ALL
  SELECT m.match_id, m.venue_id, m.winner_team_id, t2.team_id, t2.team_name, v.country
  FROM matches m JOIN teams t2 ON t2.team_id = m.team2_id JOIN venues v ON v.venue_id = m.venue_id
)
SELECT team_name,
       ROUND(100.0*SUM(CASE WHEN winner_team_id=team_id THEN 1 ELSE 0 END)/COUNT(*),1) AS win_pct,
       COUNT(*) AS matches
FROM played
GROUP BY team_id
ORDER BY win_pct DESC
LIMIT 10;
""",
  lambda df: px.bar(df.sort_values("win_pct"), x="win_pct", y="team_name", orientation="h",
                     color="matches", color_continuous_scale="Blues",
                     title="Overall Win % by Team (weighted by matches)").update_layout(height=450),
  "UNION ALL unpivot + conditional aggregation")

# ------------------------------------------------------------------ Advanced (19-25, official brief tier)

q(19, "Advanced", "Most consistent batsmen (since 2022)",
  "Restricting to recent, meaningful innings — who is the steadiest run-scorer?",
  """
WITH filtered AS (
  SELECT b.player_id, b.runs
  FROM batting_scorecards b
  JOIN matches m ON m.match_id = b.match_id
  WHERE b.balls_faced >= 10 AND m.match_date >= '2022-01-01'
),
stats AS (
  SELECT player_id, COUNT(*) AS innings, AVG(runs) AS avg_runs
  FROM filtered GROUP BY player_id HAVING COUNT(*) >= 10
)
SELECT p.player_name, t.team_name, s.innings, ROUND(s.avg_runs,1) AS avg_runs,
       ROUND(SQRT(AVG((f.runs - s.avg_runs)*(f.runs - s.avg_runs))),1) AS stdev_runs
FROM stats s
JOIN filtered f ON f.player_id = s.player_id
JOIN players p ON p.player_id = s.player_id
JOIN teams t ON t.team_id = p.team_id
GROUP BY s.player_id
ORDER BY stdev_runs ASC
LIMIT 10;
""",
  lambda df: px.scatter(df, x="avg_runs", y="stdev_runs", size="innings", color="team_name",
                         hover_name="player_name",
                         title="Q19 — Most Consistent Batsmen (bottom-right = high scoring + steady)",
                         labels={"avg_runs": "Average Runs", "stdev_runs": "Std. Dev. (lower = more consistent)"})
      .update_layout(height=450),
  "CTE chaining, date filtering, custom SQRT() aggregate")

q(20, "Advanced", "Format-wise workload & average",
  "How does a player's output split across Test / ODI / T20I?",
  """
WITH per_format AS (
  SELECT b.player_id, m.format, COUNT(*) AS innings, SUM(b.runs) AS runs,
         SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END) AS outs
  FROM batting_scorecards b JOIN matches m ON m.match_id=b.match_id
  GROUP BY b.player_id, m.format
),
totals AS (
  SELECT player_id, SUM(innings) AS total_innings FROM per_format GROUP BY player_id HAVING SUM(innings)>=20
)
SELECT p.player_name, t.team_name,
  SUM(CASE WHEN pf.format='Test' THEN pf.innings ELSE 0 END) AS test_innings,
  ROUND(SUM(CASE WHEN pf.format='Test' THEN pf.runs ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN pf.format='Test' THEN pf.outs ELSE 0 END),0),1) AS test_avg,
  SUM(CASE WHEN pf.format='ODI' THEN pf.innings ELSE 0 END) AS odi_innings,
  ROUND(SUM(CASE WHEN pf.format='ODI' THEN pf.runs ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN pf.format='ODI' THEN pf.outs ELSE 0 END),0),1) AS odi_avg,
  SUM(CASE WHEN pf.format='T20I' THEN pf.innings ELSE 0 END) AS t20i_innings,
  ROUND(SUM(CASE WHEN pf.format='T20I' THEN pf.runs ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN pf.format='T20I' THEN pf.outs ELSE 0 END),0),1) AS t20i_avg
FROM per_format pf
JOIN totals tt ON tt.player_id=pf.player_id
JOIN players p ON p.player_id=pf.player_id
JOIN teams t ON t.team_id=p.team_id
GROUP BY pf.player_id
ORDER BY (test_innings+odi_innings+t20i_innings) DESC
LIMIT 10;
""",
  lambda df: px.bar(df, x="player_name", y=["test_innings", "odi_innings", "t20i_innings"], barmode="stack",
                     title="Q20 — Innings Workload by Format (Top 10 by total innings)",
                     labels={"value": "Innings", "variable": "Format", "player_name": "Player"})
      .update_layout(height=450, xaxis_tickangle=-30),
  "Pivot-style conditional aggregation across 3 formats")

q(21, "Advanced", "Composite performance ranking",
  "Ranking players within each format using the brief's weighted batting/bowling formula.",
  """
WITH bat AS (
  SELECT b.player_id, m.format, SUM(b.runs) AS runs,
         SUM(b.runs)*1.0/NULLIF(SUM(CASE WHEN b.is_out=1 THEN 1 ELSE 0 END),0) AS batting_avg,
         AVG(b.strike_rate) AS strike_rate
  FROM batting_scorecards b JOIN matches m ON m.match_id=b.match_id
  GROUP BY b.player_id, m.format
),
bowl AS (
  SELECT bo.player_id, m.format, SUM(bo.wickets) AS wickets,
         SUM(bo.runs_conceded)*1.0/NULLIF(SUM(bo.wickets),0) AS bowling_avg,
         SUM(bo.runs_conceded)*1.0/NULLIF(SUM(bo.overs),0) AS economy
  FROM bowling_scorecards bo JOIN matches m ON m.match_id=bo.match_id
  GROUP BY bo.player_id, m.format
),
scored AS (
  SELECT p.player_name, t.team_name, bat.format,
    ROUND(COALESCE(bat.runs,0)*0.01 + COALESCE(bat.batting_avg,0)*0.5 + COALESCE(bat.strike_rate,0)*0.3,1) AS batting_points,
    ROUND(COALESCE(bowl.wickets,0)*2 + (50-COALESCE(bowl.bowling_avg,50))*0.5 + (6-COALESCE(bowl.economy,6))*2,1) AS bowling_points
  FROM bat
  LEFT JOIN bowl ON bowl.player_id=bat.player_id AND bowl.format=bat.format
  JOIN players p ON p.player_id=bat.player_id
  JOIN teams t ON t.team_id=p.team_id
)
SELECT *, ROUND(batting_points+bowling_points,1) AS total_points,
  RANK() OVER (PARTITION BY format ORDER BY (batting_points+bowling_points) DESC) AS format_rank
FROM scored
ORDER BY format, format_rank;
-- app narrows this to format_rank <= 5 before charting
""",
  lambda df: px.bar(df[df.format_rank <= 5], x="total_points", y="player_name", color="format", orientation="h",
                     title="Q21 — Composite Performance Ranking — Top 5 per Format",
                     labels={"total_points": "Weighted Score", "player_name": "Player"}, facet_col="format")
      .update_yaxes(matches=None, showticklabels=True).update_layout(height=450),
  "Multi-CTE pipeline, COALESCE, weighted scoring, RANK() per partition")

q(22, "Advanced", "Head-to-head prediction analysis",
  "For rivalries with 5+ meetings, what's the win split and typical margin?",
  """
WITH pairs AS (
  SELECT match_id, win_margin, winner_team_id,
    CASE WHEN team1_id<team2_id THEN team1_id ELSE team2_id END AS team_a,
    CASE WHEN team1_id<team2_id THEN team2_id ELSE team1_id END AS team_b
  FROM matches
)
SELECT ta.team_name AS team_a, tb.team_name AS team_b,
  COUNT(*) AS matches_played,
  SUM(CASE WHEN winner_team_id=team_a THEN 1 ELSE 0 END) AS wins_a,
  SUM(CASE WHEN winner_team_id=team_b THEN 1 ELSE 0 END) AS wins_b,
  ROUND(AVG(win_margin),1) AS avg_margin,
  ROUND(100.0*SUM(CASE WHEN winner_team_id=team_a THEN 1 ELSE 0 END)/COUNT(*),1) AS team_a_win_pct
FROM pairs
JOIN teams ta ON ta.team_id=team_a
JOIN teams tb ON tb.team_id=team_b
GROUP BY team_a, team_b
HAVING COUNT(*) >= 5
ORDER BY matches_played DESC
LIMIT 10;
""",
  lambda df: px.bar(df, x=df.team_a + " vs " + df.team_b, y=["wins_a", "wins_b"], barmode="group",
                     title="Q22 — Head-to-Head Win Split (rivalries with >=5 meetings)",
                     labels={"value": "Wins", "x": "Fixture", "variable": "Side"})
      .update_layout(height=450, xaxis_tickangle=-20),
  "Canonical pair ordering with CASE, HAVING on grouped count")

q(23, "Advanced", "Recent form & momentum",
  "Based on each player's last 10 innings, who's in hot form right now?",
  """
WITH ranked AS (
  SELECT b.player_id, b.runs, b.strike_rate, m.match_date,
     ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC) AS rn
  FROM batting_scorecards b JOIN matches m ON m.match_id=b.match_id
),
last10 AS (SELECT * FROM ranked WHERE rn<=10)
SELECT p.player_name, t.team_name,
  ROUND(AVG(CASE WHEN l10.rn<=5 THEN l10.runs END),1) AS avg_last5,
  ROUND(AVG(l10.runs),1) AS avg_last10,
  ROUND(AVG(l10.strike_rate),1) AS sr_last10,
  SUM(CASE WHEN l10.runs>=50 THEN 1 ELSE 0 END) AS scores_50plus,
  COUNT(*) AS innings_counted
FROM last10 l10
JOIN players p ON p.player_id=l10.player_id
JOIN teams t ON t.team_id=p.team_id
GROUP BY l10.player_id
HAVING innings_counted = 10
ORDER BY avg_last10 DESC
LIMIT 15;
-- app adds a derived 'form' label (Excellent/Good/Average/Poor) after this query
""",
  lambda df: px.bar(df.sort_values("avg_last10"), x="avg_last10", y="player_name", color="form",
                     orientation="h", title="Q23 — Recent Form (last 10 innings, colored by form category)",
                     color_discrete_map={"Excellent Form": "#2E7D32", "Good Form": "#66BB6A",
                                         "Average Form": "#FFB300", "Poor Form": "#E53935"},
                     labels={"avg_last10": "Avg Runs (Last 10 Innings)"}).update_layout(height=450),
  "ROW_NUMBER() for a moving window, conditional windowed average")

q(24, "Advanced", "Best partnership combinations (success rate)",
  "Among frequent partnerships (5+ shared innings), which pairs deliver most reliably?",
  """
WITH partnerships AS (
  SELECT b1.match_id, b1.team_id, b1.player_id AS p1, b2.player_id AS p2,
         (b1.runs+b2.runs) AS combined_runs
  FROM batting_scorecards b1
  JOIN batting_scorecards b2 ON b1.match_id=b2.match_id AND b1.team_id=b2.team_id AND b1.player_id<b2.player_id
),
agg AS (
  SELECT p1,p2, COUNT(*) AS partnership_count, AVG(combined_runs) AS avg_runs,
         MAX(combined_runs) AS best_runs,
         SUM(CASE WHEN combined_runs>=50 THEN 1 ELSE 0 END) AS good_partnerships
  FROM partnerships GROUP BY p1,p2 HAVING COUNT(*)>=5
)
SELECT pl1.player_name AS batter_1, pl2.player_name AS batter_2,
  a.partnership_count, ROUND(a.avg_runs,1) AS avg_partnership_runs,
  a.best_runs AS highest_partnership,
  ROUND(100.0*a.good_partnerships/a.partnership_count,1) AS success_rate_pct
FROM agg a
JOIN players pl1 ON pl1.player_id=a.p1
JOIN players pl2 ON pl2.player_id=a.p2
ORDER BY success_rate_pct DESC, avg_partnership_runs DESC
LIMIT 10;
""",
  lambda df: px.scatter(df, x="avg_partnership_runs", y="success_rate_pct", size="partnership_count",
                         hover_name=df.batter_1 + " & " + df.batter_2,
                         title="Q24 — Partnership Success Rate vs Average Partnership Runs",
                         labels={"avg_partnership_runs": "Avg Partnership Runs",
                                 "success_rate_pct": "Success Rate % (50+ runs)"}).update_layout(height=450),
  "Self-join + two-stage CTE aggregation, HAVING on frequency")

q(25, "Advanced", "Career trajectory (quarterly)",
  "Is a player's output trending up, down, or flat over time, by quarter?",
  """
WITH quarterly AS (
  SELECT b.player_id,
    (CAST(strftime('%Y', m.match_date) AS INT)*4 + (CAST(strftime('%m', m.match_date) AS INT)-1)/3) AS q_index,
    strftime('%Y', m.match_date) || '-Q' || ((CAST(strftime('%m', m.match_date) AS INT)-1)/3 + 1) AS quarter_label,
    b.runs, b.strike_rate
  FROM batting_scorecards b JOIN matches m ON m.match_id=b.match_id
),
qagg AS (
  SELECT player_id, q_index, quarter_label, COUNT(*) AS matches_in_q, AVG(runs) AS avg_runs, AVG(strike_rate) AS avg_sr
  FROM quarterly GROUP BY player_id, q_index HAVING COUNT(*)>=2
),
qualified AS (
  SELECT player_id FROM qagg GROUP BY player_id HAVING COUNT(*)>=4
)
SELECT p.player_name, t.team_name, q.q_index, q.quarter_label, ROUND(q.avg_runs,1) AS avg_runs, ROUND(q.avg_sr,1) AS avg_sr
FROM qagg q
JOIN qualified ql ON ql.player_id=q.player_id
JOIN players p ON p.player_id=q.player_id
JOIN teams t ON t.team_id=p.team_id
ORDER BY p.player_name, q.q_index;
-- app fits a per-player linear trend (slope) to classify Ascending/Declining/Stable
""",
  lambda df: px.line(df, x="quarter_label", y="avg_runs", color="player_name", markers=True,
                      title="Q25 — Quarterly Batting Trajectory (top-coverage players)",
                      labels={"quarter_label": "Quarter", "avg_runs": "Avg Runs"}).update_layout(height=450),
  "Date-bucketing via strftime, nested HAVING qualification, time-series")


def get_question(qid: int) -> dict:
    return next(item for item in QUESTIONS if item["id"] == qid)


def form_label(row) -> str:
    if row.avg_last10 >= 40 and row.avg_last5 >= row.avg_last10:
        return "Excellent Form"
    if row.avg_last10 >= 30:
        return "Good Form"
    if row.avg_last10 >= 18:
        return "Average Form"
    return "Poor Form"


def classify_trajectory(group: pd.DataFrame) -> str:
    x = np.arange(len(group))
    slope = np.polyfit(x, group["avg_runs"], 1)[0] if len(group) >= 2 else 0
    if slope > 1.5:
        return "Career Ascending"
    if slope < -1.5:
        return "Career Declining"
    return "Career Stable"


def postprocess(item_id: int, df: pd.DataFrame, run_sql):
    """Shared per-question post-processing, identical to the source notebook.

    Kept here (rather than duplicated in every page that renders QUESTIONS)
    so the SQL Analytics page and the Advanced Visualizations gallery stay
    in sync. `run_sql` is passed in to avoid a circular import on utils.database.
    """
    if item_id == 16:
        df["stdev_runs"] = df.apply(
            lambda row: (
                run_sql(
                    "SELECT AVG((runs - ?) * (runs - ?)) AS variance FROM batting_scorecards WHERE player_id = ?",
                    (row["avg_runs"], row["avg_runs"], int(row["player_id"])),
                ).iloc[0]["variance"]
            ) ** 0.5,
            axis=1,
        ).round(1)
        df = df[["player_name", "team_name", "innings", "avg_runs", "stdev_runs"]] \
            .sort_values("stdev_runs").head(10).reset_index(drop=True)
    elif item_id == 21:
        df = df[df.format_rank <= 5].reset_index(drop=True)
    elif item_id == 23:
        df["form"] = df.apply(form_label, axis=1)
    elif item_id == 25:
        trajectories = (
            df.groupby("player_name", group_keys=False)
            .apply(lambda g: pd.Series({
                "team_name": g.team_name.iloc[0],
                "quarters": len(g),
                "trajectory": classify_trajectory(g),
            }))
            .reset_index()
        )
        sample_players = trajectories.sort_values("quarters", ascending=False).player_name.head(5).tolist()
        df = df[df.player_name.isin(sample_players)]
    return df
