"""
Page 5: User Segmentation
- RFM scoring (Recency, Frequency, Monetary)
- K-Means behavioral clusters
- Geographic & industry breakdown
- Actionable segment profiles
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.data_generator import get_data
from analytics.segmentation import (
    compute_rfm,
    compute_segment_summary,
    compute_kmeans_clusters,
    compute_geo_distribution,
    compute_industry_breakdown,
)

st.set_page_config(page_title="Segmentation | ChurnShield", layout="wide")

st.title("User Segmentation")
st.markdown("RFM-based segmentation to identify high-value users, at-risk accounts, and growth opportunities.")
st.markdown("---")


@st.cache_data
def load():
    data = get_data()
    rfm = compute_rfm(data["users"], data["events"])
    seg_summary = compute_segment_summary(rfm)
    geo = compute_geo_distribution(data["users"])
    industry = compute_industry_breakdown(data["users"])
    clusters = compute_kmeans_clusters(rfm, n_clusters=5)
    return data, rfm, seg_summary, geo, industry, clusters


data, rfm, seg_summary, geo, industry, clusters = load()

st.subheader("RFM Segment Distribution")

SEGMENT_COLORS = {
    "Champions": "#3A0CA3",
    "Loyal Users": "#4361EE",
    "High-Value": "#7209B7",
    "Potential Loyalists": "#4CC9F0",
    "Recent Users": "#06D6A0",
    "At Risk": "#FFD166",
    "Churned/Lost": "#E63946",
}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Segments by User Count")
    fig_pie = px.pie(
        seg_summary,
        values="users",
        names="segment",
        color="segment",
        color_discrete_map=SEGMENT_COLORS,
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(height=380, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Segment Summary Table")
    display = seg_summary[[
        "segment", "users", "revenue_pct", "avg_mrr",
        "churn_rate", "avg_recency", "avg_frequency", "avg_rfm_score"
    ]].copy()
    display.columns = [
        "Segment", "Users", "Revenue %", "Avg MRR ($)",
        "Churn Rate (%)", "Avg Recency (d)", "Avg Events", "RFM Score"
    ]

    def color_segment(val):
        colors_bg = {
            "Champions": "#e8d5f5",
            "Loyal Users": "#d4e0fc",
            "High-Value": "#f0d9fb",
            "At Risk": "#fff3cd",
            "Churned/Lost": "#f8d7da",
        }
        if val in colors_bg:
            return f"background-color: {colors_bg[val]}"
        return ""

    styled = display.style.map(color_segment, subset=["Segment"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=350)

st.markdown("---")
col3, col4 = st.columns(2)

with col3:
    st.subheader("MRR Contribution by Segment")
    fig_mrr_seg = go.Figure(go.Bar(
        x=seg_summary["segment"],
        y=seg_summary["revenue_pct"],
        marker_color=[SEGMENT_COLORS.get(s, "#888") for s in seg_summary["segment"]],
        text=seg_summary["revenue_pct"].apply(lambda x: f"{x}%"),
        textposition="auto",
    ))
    fig_mrr_seg.update_layout(
        xaxis_title="Segment",
        yaxis_title="% of Total MRR",
        height=350,
        margin=dict(t=20, b=40),
        xaxis_tickangle=-25,
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(fig_mrr_seg, use_container_width=True)

with col4:
    st.subheader("Churn Risk by Segment")
    fig_churn_seg = go.Figure(go.Bar(
        x=seg_summary["segment"],
        y=seg_summary["churn_rate"],
        marker_color=[SEGMENT_COLORS.get(s, "#888") for s in seg_summary["segment"]],
        text=seg_summary["churn_rate"].apply(lambda x: f"{x}%"),
        textposition="auto",
    ))
    fig_churn_seg.add_hline(y=seg_summary["churn_rate"].mean(), line_dash="dash",
                             line_color="red", annotation_text="Average")
    fig_churn_seg.update_layout(
        xaxis_title="Segment",
        yaxis_title="Churn Rate (%)",
        height=350,
        margin=dict(t=20, b=40),
        xaxis_tickangle=-25,
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(fig_churn_seg, use_container_width=True)

st.markdown("---")

st.subheader("RFM Score Distribution (All Users)")
fig_scatter = px.scatter(
    rfm.sample(min(1000, len(rfm)), random_state=42),
    x="recency_days",
    y="event_frequency",
    color="segment",
    size="mrr",
    size_max=20,
    color_discrete_map=SEGMENT_COLORS,
    hover_data=["user_id", "plan", "mrr", "churned"],
    labels={
        "recency_days": "Recency (Days Since Last Event)",
        "event_frequency": "Frequency (Total Events)",
        "segment": "Segment",
    },
    opacity=0.7,
)
fig_scatter.update_layout(height=450, margin=dict(t=20, b=40))
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("Point size = MRR ($). Bottom-left = churned/inactive users. Top-right = highly engaged Champions.")

st.markdown("---")
col5, col6 = st.columns(2)

with col5:
    st.subheader("Geographic Distribution")
    fig_geo = px.bar(
        geo,
        x="total_mrr",
        y="country",
        orientation="h",
        color="conversion_rate",
        color_continuous_scale="Blues",
        text=geo["total_mrr"].apply(lambda x: f"${x:,.0f}"),
        hover_data=["users", "paid_users", "churn_rate"],
    )
    fig_geo.update_layout(
        xaxis_title="Total MRR ($)",
        yaxis_title="Country",
        height=380,
        margin=dict(t=20, b=40),
        coloraxis_colorbar=dict(title="Conv. Rate %"),
    )
    st.plotly_chart(fig_geo, use_container_width=True)

with col6:
    st.subheader("Industry Breakdown")
    fig_ind = px.scatter(
        industry,
        x="conversion_rate",
        y="churn_rate",
        size="users",
        color="avg_mrr",
        text="industry",
        color_continuous_scale="Viridis",
        labels={
            "conversion_rate": "Free-to-Paid Conversion (%)",
            "churn_rate": "Churn Rate (%)",
            "avg_mrr": "Avg MRR ($)",
        },
        size_max=40,
    )
    fig_ind.update_traces(textposition="top center")
    fig_ind.update_layout(
        height=380,
        margin=dict(t=20, b=40),
    )
    st.plotly_chart(fig_ind, use_container_width=True)

st.markdown("---")

st.subheader("Segment Action Playbook")

playbook = {
    "Champions": {
        "icon": "🏆",
        "description": "Most engaged, highest MRR, lowest churn. Product evangelists.",
        "action": "Invite to beta programs, ask for reviews/case studies, introduce to enterprise tier.",
        "priority": "High",
    },
    "At Risk": {
        "icon": "⚠️",
        "description": "Previously active, now disengaging. High churn probability.",
        "action": "Trigger proactive CS outreach, offer personalized health check call, consider discount retention offer.",
        "priority": "Urgent",
    },
    "Loyal Users": {
        "icon": "💙",
        "description": "Consistently active, good MRR, moderate churn risk.",
        "action": "Nurture toward Champions with feature education. Identify expansion opportunities.",
        "priority": "Medium",
    },
    "High-Value": {
        "icon": "💰",
        "description": "High MRR but variable engagement. Economically important.",
        "action": "Assign dedicated CSM, quarterly business reviews, expansion conversations.",
        "priority": "High",
    },
    "Churned/Lost": {
        "icon": "😴",
        "description": "Low recency and frequency. Likely churned or dormant.",
        "action": "Win-back campaign with new feature announcements. Do not over-invest in recovery.",
        "priority": "Low",
    },
}

for segment, info in playbook.items():
    with st.expander(f"{info['icon']} {segment} — Priority: {info['priority']}"):
        st.markdown(f"**Who they are:** {info['description']}")
        st.markdown(f"**Action:** {info['action']}")
        seg_data = seg_summary[seg_summary["segment"] == segment]
        if not seg_data.empty:
            row = seg_data.iloc[0]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Users", f"{row['users']:,}")
            m2.metric("Revenue %", f"{row['revenue_pct']}%")
            m3.metric("Avg MRR", f"${row['avg_mrr']:.0f}")
            m4.metric("Churn Rate", f"{row['churn_rate']}%")

with st.sidebar:
    st.markdown("### User Segmentation")
    st.markdown("RFM scoring, K-Means clusters, and actionable segment playbooks.")
