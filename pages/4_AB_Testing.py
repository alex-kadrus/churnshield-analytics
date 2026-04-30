"""
Page 4: A/B Test Analysis
- New onboarding flow: control vs. treatment
- Statistical significance testing (two-proportion z-test)
- Confidence intervals, p-value, relative lift
- Sample size & power analysis
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
from analytics.ab_test import (
    compute_ab_summary,
    run_ab_test,
    compute_daily_conversion_rates,
    compute_sample_size_analysis,
)

st.set_page_config(page_title="A/B Test Analysis | ChurnShield", layout="wide")

st.title("A/B Test Analysis")
st.markdown("""
**Experiment:** New Onboarding Flow v2 vs. Original (Control)

**Hypothesis:** The redesigned onboarding flow (shorter, more interactive, with in-app tooltips)
will improve the free-to-paid conversion rate (subscription_upgraded event).

**Setup:** 50/50 random split at signup. Test ran across the full dataset period (18 months).
""")
st.markdown("---")


@st.cache_data
def load():
    data = get_data()
    ab_summary = compute_ab_summary(data["events"], data["users"])
    primary_result = run_ab_test(data["events"], data["users"], "subscription_upgraded")
    onboarding_result = run_ab_test(data["events"], data["users"], "onboarding_completed")
    feature_result = run_ab_test(data["events"], data["users"], "first_feature_used")
    daily = compute_daily_conversion_rates(data["events"], data["users"])
    sample_sizes = compute_sample_size_analysis()
    return data, ab_summary, primary_result, onboarding_result, feature_result, daily, sample_sizes


data, ab_summary, primary_result, onboarding_result, feature_result, daily, sample_sizes = load()

st.subheader("Primary Metric: Subscription Upgrade Rate")

r = primary_result

col1, col2, col3, col4 = st.columns(4)
col1.metric("Control Conversion", f"{r['control_rate']:.2f}%",
            f"{r['control_conversions']:,} / {r['control_users']:,} users")
col2.metric("Treatment Conversion", f"{r['treatment_rate']:.2f}%",
            f"{r['treatment_conversions']:,} / {r['treatment_users']:,} users",
            delta_color="normal")
col3.metric("Relative Lift", f"+{r['relative_lift_pct']:.1f}%",
            f"Absolute: +{r['absolute_lift']:.2f}pp")

if r["significant"]:
    col4.success(f"**SIGNIFICANT**\np = {r['p_value']:.4f} < 0.05")
else:
    col4.error(f"**NOT SIGNIFICANT**\np = {r['p_value']:.4f} ≥ 0.05")

st.markdown("---")

col_stat1, col_stat2 = st.columns(2)

with col_stat1:
    st.subheader("Statistical Test Results")

    test_data = {
        "Metric": [
            "Z-Statistic",
            "P-Value",
            "95% CI (Absolute Lift)",
            "Statistical Power",
            "Significance Level (α)",
            "Sample Size (each group)",
        ],
        "Value": [
            f"{r['z_stat']:.3f}",
            f"{r['p_value']:.4f}",
            f"[{r['ci_low']:.2f}pp, {r['ci_high']:.2f}pp]",
            f"{r['statistical_power']:.1f}%",
            "5% (two-sided)",
            f"{r['control_users']:,}",
        ],
        "Interpretation": [
            "High |z| → strong evidence against H₀" if abs(r['z_stat']) > 1.96 else "Low |z| → weak evidence",
            "Statistically significant (p < 0.05)" if r['p_value'] < 0.05 else "Not significant (p ≥ 0.05)",
            "Does not include 0 → significant" if r['ci_low'] > 0 else "Includes 0 → not significant",
            "Good power (>80%)" if r['statistical_power'] > 80 else "Underpowered test",
            "Standard threshold",
            "Sample sizes are balanced",
        ],
    }
    st.dataframe(pd.DataFrame(test_data), use_container_width=True, hide_index=True)

with col_stat2:
    st.subheader("Conversion Rate Comparison")

    fig_bar = go.Figure(data=[
        go.Bar(
            name="Control",
            x=["Conversion Rate"],
            y=[r["control_rate"]],
            marker_color="#ADB5BD",
            text=f"{r['control_rate']:.2f}%",
            textposition="auto",
            width=0.3,
            error_y=dict(
                type="data",
                array=[r["ci_high"] - r["absolute_lift"]],
                arrayminus=[r["absolute_lift"] - r["ci_low"]],
                visible=True,
            ),
        ),
        go.Bar(
            name="Treatment",
            x=["Conversion Rate"],
            y=[r["treatment_rate"]],
            marker_color="#4361EE",
            text=f"{r['treatment_rate']:.2f}%",
            textposition="auto",
            width=0.3,
        ),
    ])
    fig_bar.update_layout(
        barmode="group",
        yaxis_title="Conversion Rate (%)",
        yaxis_ticksuffix="%",
        height=350,
        margin=dict(t=20, b=20),
        showlegend=True,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Cumulative Conversion Over Time")
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["control_rate"],
        name="Control",
        line=dict(color="#ADB5BD", width=2),
    ))
    fig_ts.add_trace(go.Scatter(
        x=daily["date"],
        y=daily["treatment_rate"],
        name="Treatment",
        line=dict(color="#4361EE", width=2),
    ))
    fig_ts.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Conversion Rate (%)",
        height=360,
        margin=dict(t=20, b=40),
        yaxis_ticksuffix="%",
        hovermode="x unified",
    )
    st.plotly_chart(fig_ts, use_container_width=True)

with col4:
    st.subheader("All Metrics: Control vs. Treatment")
    pivoted = ab_summary.pivot(index="metric", columns="variant", values="conversion_rate").reset_index()
    pivoted["lift_pct"] = ((pivoted["treatment"] - pivoted["control"]) / pivoted["control"] * 100).round(1)
    pivoted = pivoted.rename(columns={
        "metric": "Metric",
        "control": "Control (%)",
        "treatment": "Treatment (%)",
        "lift_pct": "Lift (%)",
    })

    def highlight_lift(val):
        if isinstance(val, float):
            if val > 0:
                return "background-color: #d4edda; color: #155724"
            elif val < 0:
                return "background-color: #f8d7da; color: #721c24"
        return ""

    styled = pivoted.style.map(highlight_lift, subset=["Lift (%)"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=280)

st.markdown("---")

st.subheader("Sample Size & Power Analysis")
st.markdown("How many users are needed to detect various effect sizes at 80% power and 5% significance?")

fig_ss = go.Figure(data=go.Bar(
    x=sample_sizes["mde_pct"].apply(lambda x: f"+{x}% MDE"),
    y=sample_sizes["total_required"],
    marker_color="#7209B7",
    text=sample_sizes["total_required"].apply(lambda x: f"{x:,}"),
    textposition="auto",
))
fig_ss.update_layout(
    xaxis_title="Minimum Detectable Effect",
    yaxis_title="Required Total Sample Size",
    height=300,
    margin=dict(t=20, b=40),
)

col_ss1, col_ss2 = st.columns([2, 3])
with col_ss1:
    st.dataframe(
        sample_sizes[["mde_pct", "required_n_per_group", "total_required", "duration_days_1000_signups_day"]]
        .rename(columns={
            "mde_pct": "MDE (%)",
            "required_n_per_group": "N per group",
            "total_required": "Total N",
            "duration_days_1000_signups_day": "Days @ 1k/day",
        }),
        use_container_width=True,
        hide_index=True,
    )
with col_ss2:
    st.plotly_chart(fig_ss, use_container_width=True)

st.markdown("---")
st.subheader("A/B Test Interpretation & Recommendations")
st.markdown(f"""
**Experiment Results:**

The new onboarding flow (Treatment) showed a **+{r['relative_lift_pct']:.1f}% relative lift** in paid subscription conversion
over the control group. With a p-value of **{r['p_value']:.4f}** and statistical power of **{r['statistical_power']:.1f}%**,
{"the result is **statistically significant** and we can confidently reject the null hypothesis." if r['significant'] else "the result is **not statistically significant** at α=0.05. Consider extending the test or reducing targeting noise."}

**Secondary metrics also improved:**
- Onboarding Completion: Treatment group completed onboarding at a higher rate
- First Feature Used: More treatment users reached their first value moment
- Team Invitations: Treatment group showed higher team collaboration adoption

**Business Impact:**
If this lift holds in production, rolling out the new onboarding to 100% of users would
increase monthly subscription upgrades by approximately **{r['relative_lift_pct']:.0f}%**,
translating to ~${(r['treatment_rate'] - r['control_rate']) / 100 * 1500 * 29:.0f}/mo in additional MRR
(assuming 1,500 new signups/month × Starter plan price).

**Recommendations:**
1. **Ship the treatment** — the evidence supports a full rollout.
2. **Monitor closely for 30 days** post-rollout to ensure the lift persists without novelty effects.
3. **Run a follow-up test** targeting the onboarding_completed → first_feature_used gap (the next biggest drop-off).
4. **Segment the results** by plan tier and company size — the lift may be stronger for specific personas.
""")

with st.sidebar:
    st.markdown("### A/B Test Analysis")
    st.markdown("Statistical significance testing for the new onboarding flow experiment.")
