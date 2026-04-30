"""
ChurnShield SaaS Analytics Dashboard

A portfolio-grade product analytics project demonstrating:
- KPI Overview & MRR tracking
- Conversion Funnel Analysis
- Cohort Retention Analysis
- A/B Test Statistical Testing
- User Segmentation (RFM)

Author: Portfolio Project | Stack: Python, Streamlit, Plotly, Pandas, Scipy, Scikit-learn
"""

import streamlit as st

st.set_page_config(
    page_title="ChurnShield Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
# ChurnShield SaaS Analytics

**A B2B SaaS Product Analytics Portfolio Project**

---

### Business Context

**ChurnShield** is a B2B SaaS platform that helps customer success teams reduce churn.
The company has 3,000 registered users across 10 countries, with 4 subscription tiers
(Free, Starter $29/mo, Professional $99/mo, Enterprise $299/mo).

The product team needs to answer critical questions:

1. **Where do users drop off** in the onboarding funnel?
2. **Which cohorts** have the strongest long-term retention?
3. **Does our new onboarding flow** (A/B test) improve paid conversion?
4. **Which user segments** drive the most revenue — and which are at churn risk?

---

### Dashboard Sections
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **📈 1. Business Overview**

    KPIs, MRR growth, ARR trajectory,
    churn rate trends, plan distribution.
    """)
    st.info("""
    **🔽 2. Funnel Analysis**

    8-step onboarding funnel,
    drop-off analysis, time-to-convert.
    """)

with col2:
    st.info("""
    **🔁 3. Cohort Retention**

    12-month cohort heatmap, retention
    curves by plan tier, survival analysis.
    """)
    st.info("""
    **🧪 4. A/B Test Analysis**

    Two-proportion z-test, statistical
    significance, confidence intervals, power.
    """)

with col3:
    st.info("""
    **👥 5. User Segmentation**

    RFM scoring, K-Means clustering,
    geo/industry breakdown.
    """)
    st.info("""
    **🗄️ SQL Reference**

    All analytical queries in PostgreSQL
    available in `sql/queries.sql`
    """)

st.markdown("""
---

### Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core analysis |
| Pandas | Data manipulation |
| NumPy | Numerical computing |
| Plotly | Interactive charts |
| SciPy | Statistical tests |
| Scikit-learn | K-Means clustering |
| Streamlit | Dashboard |
| PostgreSQL (SQL) | Reference queries |

---

### Dataset

Synthetic dataset generated with realistic distributions modeling a B2B SaaS company:
- **3,000 users** over 18 months (Jan 2023 – Jun 2024)
- **8-step funnel** with realistic drop-off rates
- **A/B experiment** with 50/50 control/treatment split
- **RFM segmentation** across 7 behavioral segments

Navigate the pages in the sidebar to explore the full analysis.
""")

with st.sidebar:
    st.markdown("### ChurnShield Analytics")
    st.markdown("---")
    st.markdown("**Navigate:**")
    st.markdown("Use the pages above to explore each analysis section.")
    st.markdown("---")
    st.caption("Portfolio project for Data/Product Analyst roles")
    st.caption("Stack: Python · Streamlit · Plotly · Scipy")
