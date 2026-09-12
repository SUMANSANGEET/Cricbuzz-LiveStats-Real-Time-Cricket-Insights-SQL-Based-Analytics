import streamlit as st

from utils.database import get_connection, run_sql
from utils.queries import QUESTIONS, TIERS, postprocess

st.set_page_config(
    page_title="SQL Analytics · Cricbuzz LiveStats",
    page_icon="📊",
    layout="wide"
)

get_connection()

st.title("📊 SQL Analytics — 25 Business Questions")
st.caption(
    "Beginner → Intermediate → Advanced. "
    "Every chart is driven live by the SQL shown beside it."
)

# Unique key prevents StreamlitDuplicateElementId errors
tier = st.radio(
    "Tier",
    TIERS,
    horizontal=True,
    label_visibility="collapsed",
    key="sql_analytics_tier"
)

tier_questions = [x for x in QUESTIONS if x["tier"] == tier]

for item in tier_questions:

    with st.expander(
        f"**Q{item['id']}. {item['title']}**",
        expanded=(item["id"] == tier_questions[0]["id"])
    ):

        st.markdown(f"*{item['business_question']}*")

        left, right = st.columns([1, 1.15])

        # =========================================================
        # LEFT — SQL
        # =========================================================
        with left:
            st.markdown("**SQL query**")

            st.code(
                item["sql"],
                language="sql"
            )

            st.caption(
                f"Concepts: {item['concepts']}"
            )

        # =========================================================
        # RIGHT — RESULT + VISUALIZATION
        # =========================================================
        with right:

            df = run_sql(item["sql"])

            # Post-processing used by selected questions
            df = postprocess(
                item["id"],
                df,
                run_sql
            )

            st.markdown("**Result**")

            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                height=220
            )

            st.markdown("**Visualization**")

            fig = item["chart"](df)

            st.plotly_chart(
                fig,
                width="stretch"
            )

            # =====================================================
            # Q25 — TRAJECTORY CLASSIFICATION
            # =====================================================
            if item["id"] == 25:

                st.markdown("**Trajectory classification**")

                # Q25 SQL result is the trajectory dataset.
                # Use df instead of undefined 'trajectories'.
                trajectories = df.copy()

                # Sort only when the expected column exists
                if "quarters" in trajectories.columns:

                    trajectories = trajectories.sort_values(
                        "quarters",
                        ascending=False
                    )

                st.dataframe(
                    trajectories,
                    width="stretch",
                    hide_index=True
                )
