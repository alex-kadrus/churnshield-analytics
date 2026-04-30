"""
Page 2: Funnel Analysis
- 8-step onboarding funnel visualization
- Drop-off analysis
- Time between steps
- Funnel by plan tier
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.data_generator import get_data
from analytics.funnel import compute_funnel, compute_funnel_comparison, compute_time_to_convert

st.set_page_config(page_title="Funnel Analysis | ChurnShield", layout="wide")

st.title("Funnel Analysis")
st.markdown("Conversion funnel from user signup through subscription upgrade — identifying where users drop off.")
st.markdown("---")


@st.cache_data
def load():
    data = get_data()
    funnel_all = compute_funnel(data["events"], data["users"])
    funnel_comparison = compute_funnel_comparison(data["events"], data["users"])
    time_to_convert = compute_time_to_convert(data["events"])
    return data, funnel_all, funnel_comparison, time_to_convert


data, funnel_all, funnel_comparison, time_to_convert = load()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Overall Onboarding Funnel")

    fig_funnel = go.Figure(go.Funnel(
        y=funnel_all["label"],
        x=funnel_all["users"],
        textinfo="value+percent initial",
        marker=dict(
            color=[
                "#4361EE", "#4CC9F0", "#3A0CA3", "#7209B7",
                "#F72585", "#480CA8", "#560BAD", "#E63946"
            ],
        ),
        connector=dict(line=dict(color="royalblue", dash="solid", width=2)),
    ))
    fig_funnel.update_layout(
        height=500,
        margin=dict(t=20, b=20),
        font=dict(size=13),
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

with col2:
    st.subheader("Step-by-Step Conversion Rates")

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=funnel_all["label"],
        y=funnel_all["conversion_from_top"],
        name="Conversion from Top (%)",
        marker_color="#4361EE",
        text=funnel_all["conversion_from_top"].apply(lambda x: f"{x}%"),
        textposition="auto",
    ))
    fig_bar.add_trace(go.Bar(
        x=funnel_all["label"],
        y=funnel_all["drop_off"],
        name="Drop-off from Prev (%)",
        marker_color="#E63946",
        text=funnel_all["drop_off"].apply(lambda x: f"-{x}%"),
        textposition="auto",
    ))
    fig_bar.update_layout(
        barmode="group",
        xaxis_title="Funnel Step",
        yaxis_title="Rate (%)",
        height=500,
        margin=dict(t=20, b=40),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.subheader("Critical Drop-off Points")

drop_sorted = funnel_all[funnel_all["drop_off"] > 0].sort_values("drop_off", ascending=False)
c1, c2, c3 = st.columns(3)

if len(drop_sorted) >= 1:
    row = drop_sorted.iloc[0]
    c1.error(f"**Biggest Drop-off**\n\n{row['label']}\n\n**-{row['drop_off']}%** from previous step")

if len(drop_sorted) >= 2:
    row = drop_sorted.iloc[1]
    c2.warning(f"**2nd Biggest Drop-off**\n\n{row['label']}\n\n**-{row['drop_off']}%** from previous step")

if len(drop_sorted) >= 3:
    row = drop_sorted.iloc[2]
    c3.info(f"**3rd Biggest Drop-off**\n\n{row['label']}\n\n**-{row['drop_off']}%** from previous step")

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Time Between Funnel Steps (Median Hours)")
    fig_time = go.Figure(go.Bar(
        x=time_to_convert["median_hours"],
        y=time_to_convert["to_step"],
        orientation="h",
        marker_color="#7209B7",
        error_x=dict(
            type="data",
            array=(time_to_convert["p75_hours"] - time_to_convert["median_hours"]).tolist(),
            arrayminus=(time_to_convert["median_hours"] - time_to_convert["p25_hours"]).tolist(),
            visible=True,
        ),
        text=time_to_convert["median_hours"].apply(lambda x: f"{x:.1f}h"),
        textposition="auto",
    ))
    fig_time.update_layout(
        xaxis_title="Median Hours to Reach Step",
        height=400,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_time, use_container_width=True)

with col4:
    st.subheader("Funnel Data Table")
    display = funnel_all[["label", "users", "conversion_from_top", "conversion_from_prev", "drop_off"]].copy()
    display.columns = ["Step", "Users", "From Top (%)", "From Prev (%)", "Drop-off (%)"]
    st.dataframe(
        display.style.background_gradient(subset=["From Top (%)"], cmap="Blues")
                     .background_gradient(subset=["Drop-off (%)"], cmap="Reds"),
        use_container_width=True,
        height=380,
    )

st.markdown("---")
st.subheader("Funnel Interpretation & Recommendations")

biggest_drop = funnel_all[funnel_all["drop_off"] > 0].sort_values("drop_off", ascending=False).iloc[0]
top_conversion = funnel_all[funnel_all["label"] == "Subscription Upgraded"]["conversion_from_top"].values[0]

st.markdown(f"""
**Key Findings:**

1. **Top-of-funnel to paid conversion: {top_conversion}%** — only 1 in 7 signups ultimately upgrades to a paid plan.
   Industry benchmark for self-serve B2B SaaS is typically 3-8% (our synthetic model is higher due to email lead quality).

2. **Biggest drop-off: "{biggest_drop['label']}" (-{biggest_drop['drop_off']}%)** — this is the primary optimization lever.
   Users who complete onboarding are {funnel_all[funnel_all['label']=='Onboarding Completed']['conversion_from_prev'].values[0]:.0f}%
   of those who started it.

3. **Team invitation and integrations** have the steepest drop-offs in the mid-funnel,
   suggesting users don't see the collaborative value proposition quickly enough.

4. **Time-to-convert**: The median time from signup to subscription upgrade is
   {time_to_convert['median_hours'].sum():.0f} hours (~{time_to_convert['median_hours'].sum()/24:.1f} days).
   Reducing friction could cut this significantly.

**Recommendations:**

- **Redesign the onboarding completion flow** — add progress bars, celebrate milestones, and show the value of completing.
- **Add in-app nudges for team invitation** — "Invite your team and unlock collaborative features" prompt at the right moment.
- **Integration showcase**: Show integration benefits earlier (e.g., during onboarding, not after) to increase connection rate.
- **Time-based email triggers**: Send targeted emails to users who started but didn't complete onboarding within 24h.
- **A/B test**: See the A/B Test page for analysis of the new onboarding flow experiment.
""")

with st.sidebar:
    st.markdown("### Funnel Analysis")
    st.markdown("8-step onboarding funnel with drop-off analysis.")
