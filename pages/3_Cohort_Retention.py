"""
Page 3: Cohort Retention Analysis
- Monthly cohort retention heatmap
- Average retention curve
- Retention by plan tier
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.data_generator import get_data
from analytics.cohort import (
    compute_cohort_retention,
    compute_cohort_retention_pivot,
    compute_average_retention_curve,
)

st.set_page_config(page_title="Cohort Retention | ChurnShield", layout="wide")

st.title("Cohort Retention Analysis")
st.markdown("Monthly retention rates by signup cohort — tracking how well ChurnShield keeps users over time.")
st.markdown("---")


@st.cache_data
def load():
    data = get_data()
    ret_df = compute_cohort_retention(data["users"], months=12)
    pivot = compute_cohort_retention_pivot(ret_df)
    avg_curve = compute_average_retention_curve(ret_df)
    ret_by_plan = {}
    for plan in ["starter", "professional", "enterprise"]:
        plan_ret = compute_cohort_retention(data["users"][data["users"]["plan"] == plan], months=12)
        ret_by_plan[plan] = compute_average_retention_curve(plan_ret)
    return data, ret_df, pivot, avg_curve, ret_by_plan


data, ret_df, pivot, avg_curve, ret_by_plan = load()

st.subheader("Monthly Cohort Retention Heatmap")
st.markdown("Each row is a signup cohort. Each column is months since signup. Values show % of users still active.")

pivot_clean = pivot.dropna(how="all", axis=1).dropna(how="all", axis=0)
cohort_labels = pivot_clean.index.tolist()
month_labels = [f"M{c}" for c in pivot_clean.columns.tolist()]
z_values = pivot_clean.values.tolist()

fig_heatmap = go.Figure(data=go.Heatmap(
    z=z_values,
    x=month_labels,
    y=cohort_labels,
    colorscale=[
        [0.0, "#FFF3CD"],
        [0.3, "#FFD166"],
        [0.6, "#4361EE"],
        [1.0, "#3A0CA3"],
    ],
    text=[[f"{v:.0f}%" if not np.isnan(v) else "" for v in row] for row in z_values],
    texttemplate="%{text}",
    textfont=dict(size=9),
    colorbar=dict(title="Retention %", ticksuffix="%"),
    zmin=0, zmax=100,
))
fig_heatmap.update_layout(
    xaxis_title="Months Since Signup",
    yaxis_title="Cohort (Signup Month)",
    height=max(400, len(cohort_labels) * 28),
    margin=dict(t=20, b=40),
    font=dict(size=10),
)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.caption("""
**How to read:** Month 0 = 100% (all users active at signup). Month 1 = % still active 1 month later, etc.
Darker blue = better retention. Yellow/orange = lower retention.
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Retention Curve")

    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=avg_curve["month"],
        y=avg_curve["avg_retention_pct"],
        mode="lines+markers",
        name="All Users",
        line=dict(color="#4361EE", width=3),
        fill="tozeroy",
        fillcolor="rgba(67,97,238,0.1)",
        text=avg_curve["avg_retention_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="top center",
    ))
    fig_curve.add_hline(y=40, line_dash="dash", line_color="green",
                         annotation_text="40% benchmark", annotation_position="right")

    fig_curve.update_layout(
        xaxis_title="Months Since Signup",
        yaxis_title="Average Retention (%)",
        yaxis_range=[0, 105],
        height=400,
        margin=dict(t=20, b=40),
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(fig_curve, use_container_width=True)

with col2:
    st.subheader("Retention by Plan Tier")

    fig_plans = go.Figure()
    colors = {"starter": "#4CC9F0", "professional": "#4361EE", "enterprise": "#7209B7"}

    for plan, curve in ret_by_plan.items():
        if len(curve) > 0:
            fig_plans.add_trace(go.Scatter(
                x=curve["month"],
                y=curve["avg_retention_pct"],
                mode="lines+markers",
                name=plan.title(),
                line=dict(color=colors.get(plan, "#888"), width=2.5),
            ))

    fig_plans.update_layout(
        xaxis_title="Months Since Signup",
        yaxis_title="Average Retention (%)",
        yaxis_range=[0, 105],
        height=400,
        margin=dict(t=20, b=40),
        yaxis_ticksuffix="%",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )
    st.plotly_chart(fig_plans, use_container_width=True)

st.markdown("---")

st.subheader("Retention Benchmarks")
bench1, bench2, bench3, bench4 = st.columns(4)

m1_avg = avg_curve[avg_curve["month"] == 1]["avg_retention_pct"].values
m3_avg = avg_curve[avg_curve["month"] == 3]["avg_retention_pct"].values
m6_avg = avg_curve[avg_curve["month"] == 6]["avg_retention_pct"].values
m12_avg = avg_curve[avg_curve["month"] == 12]["avg_retention_pct"].values

bench1.metric("M1 Retention", f"{m1_avg[0]:.1f}%" if len(m1_avg) else "N/A", "Benchmark: 70%")
bench2.metric("M3 Retention", f"{m3_avg[0]:.1f}%" if len(m3_avg) else "N/A", "Benchmark: 55%")
bench3.metric("M6 Retention", f"{m6_avg[0]:.1f}%" if len(m6_avg) else "N/A", "Benchmark: 40%")
bench4.metric("M12 Retention", f"{m12_avg[0]:.1f}%" if len(m12_avg) else "N/A", "Benchmark: 30%")

st.markdown("---")
st.subheader("Cohort Analysis — Interpretation & Recommendations")
st.markdown(f"""
**Key Findings:**

1. **Month-1 retention** is the most critical indicator of long-term retention. Users who complete
   onboarding in the first week have significantly higher M1 retention.

2. **Enterprise cohorts** show the strongest retention curves, plateauing at ~75-80% by month 6.
   Professional tier stabilizes around 65%. Starter tier shows higher early churn (~40% by M3).

3. **2023 Q1 cohorts** (the earliest) showed weaker retention — the product has improved significantly
   since then. Newer cohorts (2023 H2) show measurably better M3 and M6 retention.

4. **Natural retention plateau**: Most SaaS products see retention stabilize after M6-M8.
   Users who stay beyond 6 months have a very high probability of staying long-term.

**Recommendations:**

- **Invest in early activation**: The biggest driver of long-term retention is completing onboarding
  in the first 7 days. Create automated workflows to re-engage users who don't activate quickly.

- **Segment-specific retention campaigns**: Starter users need the most intervention at M2-M3.
  Create proactive check-ins and value-demonstration emails for this segment.

- **Highlight success milestones**: For users approaching 3 months, send "success review" emails
  showing their ROI from the product — proven to reduce churn at this critical drop-off point.

- **Enterprise expansion motion**: High-retention enterprise users are the best candidates for
  upselling additional seats. Their stable long-term usage makes expansion revenue highly reliable.
""")

with st.sidebar:
    st.markdown("### Cohort Retention")
    st.markdown("Monthly retention heatmap and survival curves by plan tier.")
