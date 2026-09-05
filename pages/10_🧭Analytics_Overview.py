import streamlit as st

from utils.database import get_connection
from utils.kpi import build_kpi_figure, get_kpis
from utils.report import build_summary_pdf

st.set_page_config(page_title="Analytics Overview · Cricbuzz LiveStats", page_icon="🧭", layout="wide")
get_connection()

st.title("🧭 Analytics Overview")
st.caption(
    "The recruiter-facing summary from the notebook, brought to life: a 10-second KPI snapshot, "
    "the batting/bowling performance environment, and the headline insights across all 25 SQL "
    "analytics questions."
)

# --------------------------------------------------------------------- KPI snapshot
st.subheader("📊 Project KPI Snapshot")
st.plotly_chart(build_kpi_figure(height=230), use_container_width=True, config={"displayModeBar": False})

kpis = {label: value for _, label, value, _ in get_kpis()}

st.divider()

# --------------------------------------------------------------------- narrative insights
st.subheader("💡 Key Insights")
st.caption("Straight from the notebook's Section 10 — the takeaways worth leading with.")

insights = [
    ("Scoring patterns", "Q1/Q7 show run volume and strike rate don't always move together; the "
     "highest-SR players aren't always the top accumulators — a classic anchor-vs-finisher split."),
    ("Toss matters, but not decisively", "Q10's gauge typically lands close to 50%, confirming toss "
     "is a marginal, not dominant, factor once enough matches are pooled."),
    ("Venue bias is real", "Q4 shows a clear high/low scoring split across grounds, useful for "
     "pre-match analyst commentary."),
    ("Consistency ≠ average", "Q16's scatter separates 'big scores, big failures' players from truly "
     "reliable accumulators — a distinction raw averages hide."),
    ("Rivalry concentration", "Q9 shows match scheduling clusters around a handful of marquee "
     "fixtures, useful for broadcast/sponsorship analytics framing."),
    ("Composite ranking surfaces multi-skill value", "Q21's weighted score consistently promotes "
     "all-format contributors over one-dimensional specialists — useful for team-balance discussions."),
    ("Form is a leading indicator, not a lagging one", "Q23's last-10-innings view flags players "
     "trending into 'Excellent Form' before their season average catches up — the more actionable "
     "recruiter/selector signal."),
]

for title, body in insights:
    st.markdown(f"**{title}** — {body}")

pdf_bytes = build_summary_pdf(kpis, insights)
st.download_button(
    "📄 Download 1-page PDF summary",
    data=pdf_bytes,
    file_name="cricbuzz_livestats_executive_summary.pdf",
    mime="application/pdf",
    help="A leave-behind summary — KPIs and headline insights — for anyone reviewing this project offline.",
)

st.divider()

# --------------------------------------------------------------------- dataset composition & environment
st.subheader("🏟️ Dataset & Performance Environment")
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.markdown("**Batting environment**")
        st.metric("Average runs / innings", f"{kpis['Avg Runs']:.1f}")
        st.markdown("**Bowling environment**")
        st.metric("Average bowling economy", f"{kpis['Avg Economy']:.2f}")
with c2:
    with st.container(border=True):
        st.markdown("**Coverage**")
        m1, m2 = st.columns(2)
        m1.metric("Matches", f"{kpis['Matches']:,}")
        m1.metric("Teams", f"{kpis['Teams']:,}")
        m2.metric("Players", f"{kpis['Players']:,}")
        m2.metric("Venues", f"{kpis['Venues']:,}")

st.caption(
    "For the full chart gallery behind these numbers, see **Advanced Visualizations**. "
    "For the raw SQL, see **SQL Analytics**."
)

st.divider()

# --------------------------------------------------------------------- roadmap
st.subheader("🛣️ Next Steps")
st.markdown("""
- Set `RAPIDAPI_KEY` in `.streamlit/secrets.toml` to switch **Scores** from synthetic data to live Cricbuzz data — no other code changes required.
- Add a `fielding_stats` table (catches, stumpings) to reinstate the fielding term in Q21's composite ranking formula exactly as specified in the original brief.
- Extend **Scores CRUD** with bulk-import (CSV upload) for faster scorecard entry during live scoring.
""")
