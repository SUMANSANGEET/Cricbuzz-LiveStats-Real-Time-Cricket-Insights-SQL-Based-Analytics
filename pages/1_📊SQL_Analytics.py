import streamlit as st

from utils.database import get_connection, run_sql
from utils.queries import QUESTIONS, TIERS, postprocess

st.set_page_config(page_title="SQL Analytics · Cricbuzz LiveStats", page_icon="📊", layout="wide")
get_connection()

st.title("📊 SQL Analytics — 25 Business Questions")
st.caption("Beginner → Intermediate → Advanced. Every chart is driven live by the SQL shown beside it.")

tier = st.radio("Tier", TIERS, horizontal=True, label_visibility="collapsed")
tier_questions = [x for x in QUESTIONS if x["tier"] == tier]

for item in tier_questions:
    with st.expander(f"**Q{item['id']}. {item['title']}**", expanded=(item["id"] == tier_questions[0]["id"])):
        st.markdown(f"*{item['business_question']}*")
        left, right = st.columns([1, 1.15])

        with left:
            st.markdown("**SQL query**")
            st.code(item["sql"], language="sql")
            st.caption(f"Concepts: {item['concepts']}")

        with right:
            df = run_sql(item["sql"])
            # a couple of questions need a short post-processing pass identical to the source notebook
            df = postprocess(item["id"], df, run_sql)

            st.markdown("**Result**")
            st.dataframe(df, use_container_width=True, hide_index=True, height=220)
            st.markdown("**Visualization**")
            st.plotly_chart(item["chart"](df), use_container_width=True)

            if item["id"] == 25:
                st.markdown("**Trajectory classification**")
                st.dataframe(trajectories.sort_values("quarters", ascending=False),
                             use_container_width=True, hide_index=True)
