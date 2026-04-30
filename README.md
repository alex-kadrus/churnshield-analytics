# ChurnShield SaaS Analytics

**A Portfolio-Grade Product Analytics Project for Data Analyst & Product Analyst Roles**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.20+-purple?logo=plotly)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Business Problem

ChurnShield is a B2B SaaS platform for customer success teams. The company faces a critical challenge:
**users sign up, but many churn before unlocking the platform's full value.**

The product team needs answers to:

1. Where in the onboarding funnel do users drop off?
2. Which signup cohorts have the strongest long-term retention?
3. Does the new onboarding flow (A/B test) improve paid conversion?
4. Which user segments drive the most revenue — and which are at risk?

---

## Project Structure

```
churnshield-analytics/
├── app.py                        # Streamlit dashboard entry point
├── pages/
│   ├── 1_Overview.py             # KPI dashboard: MRR, ARR, churn
│   ├── 2_Funnel_Analysis.py      # 8-step conversion funnel
│   ├── 3_Cohort_Retention.py     # Cohort retention heatmap
│   ├── 4_AB_Testing.py           # A/B test statistical analysis
│   └── 5_Segmentation.py         # RFM user segmentation
├── analytics/
│   ├── data_generator.py         # Synthetic dataset generation
│   ├── metrics.py                # KPI & MRR calculations
│   ├── cohort.py                 # Cohort retention analysis
│   ├── funnel.py                 # Funnel conversion analysis
│   ├── ab_test.py                # Two-proportion z-test
│   └── segmentation.py          # RFM scoring & K-Means
├── sql/
│   └── queries.sql               # PostgreSQL reference queries
├── .streamlit/
│   └── config.toml               # Streamlit theme config
└── requirements.txt
```

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11 | Core analysis |
| Pandas | 2.0+ | Data manipulation & aggregation |
| NumPy | 1.26+ | Numerical computing |
| Plotly | 5.20+ | Interactive visualizations |
| SciPy | 1.12+ | Two-proportion z-test, statistics |
| Scikit-learn | 1.4+ | K-Means clustering, preprocessing |
| Faker | 24.0+ | Synthetic data generation |
| Streamlit | 1.30+ | Interactive dashboard |
| SQL (PostgreSQL) | — | Reference analytical queries |

---

## Dataset

Synthetic dataset generated with realistic distributions:

| Attribute | Details |
|-----------|---------|
| Users | 3,000 |
| Time period | Jan 2023 – Jun 2024 (18 months) |
| Plans | Free, Starter ($29), Professional ($99), Enterprise ($299) |
| Countries | 10 (US, UK, Germany, France, Canada, Australia, NL, India, Brazil, Other) |
| Industries | 7 (SaaS/Tech, E-commerce, Finance, Healthcare, Marketing, Education, Other) |
| Funnel steps | 8 (signup → email_verified → onboarding → first_feature → team → integration → upgrade) |
| A/B experiment | 50/50 split, new onboarding flow vs. control |

---

## Analyses & Metrics

### 1. Business Overview (KPIs)
- **MRR & ARR** growth over 18 months
- **Churn rate** month-over-month trend
- **Plan distribution** and MRR contribution per tier
- **Customer LTV** by plan segment
- Free-to-paid conversion rate

### 2. Funnel Analysis
- **8-step onboarding funnel** with conversion rates at each step
- **Drop-off analysis** — identifying the biggest friction points
- **Time-to-convert** distribution (median hours between steps)

```
Signup → Email Verified → Onboarding Started → Onboarding Completed
       → First Feature Used → Team Invited → Integration Connected → Upgraded
```

### 3. Cohort Retention Analysis
- **12-month cohort retention heatmap** (signup cohort × months since signup)
- **Average retention curve** vs. SaaS benchmark (40% at M6)
- **Retention by plan tier** — enterprise vs. professional vs. starter

### 4. A/B Test Analysis
- **Two-proportion z-test** on subscription upgrade conversion
- **95% confidence intervals** for absolute lift
- **Statistical power analysis** and sample size requirements
- **Cumulative conversion** time series by variant
- All secondary metrics: onboarding completed, first feature used, team invited

### 5. User Segmentation (RFM)
- **RFM scoring** (Recency, Frequency, Monetary) → 7 behavioral segments
- **K-Means clustering** (5 clusters, normalized features)
- **Geographic distribution** with MRR and conversion breakdowns
- **Industry analysis** — conversion rate vs. churn risk by vertical
- **Actionable playbook** per segment (Champions, At Risk, Churned/Lost, etc.)

---

## Key Findings

| Finding | Impact |
|---------|--------|
| Only 14% of signups upgrade to paid | Biggest revenue unlock is funnel optimization |
| Biggest funnel drop-off: Onboarding Completed → First Feature Used (-8pp) | In-app activation improvements needed |
| New onboarding flow (treatment) increased conversion by ~32% relatively | Statistically significant (p < 0.05) |
| Enterprise users: lowest churn (~10%), highest LTV | High-ROI segment to invest in |
| "At Risk" segment: 28% churn rate, 12% of MRR | Proactive CS outreach is critical |
| M6 retention: ~45% overall (benchmark: 40%) | Slightly above benchmark, room to improve |

---

## Business Recommendations

1. **Ship the new onboarding flow** — A/B test shows +32% lift in paid conversion (p < 0.05)
2. **Focus on the onboarding → first feature gap** — biggest drop-off in the funnel
3. **Invest in enterprise sales** — lowest churn (10%), highest LTV, most stable retention
4. **Build CS playbook for "At Risk" segment** — automated alerts + proactive outreach
5. **Launch upgrade campaign for Starter power users** — LTV gap between Starter→Professional is 3×
6. **Add in-app team invitation nudges** — mid-funnel drop at team invitation step is recoverable

---

## Running Locally

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/churnshield-analytics.git
cd churnshield-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Streamlit dashboard
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## SQL Reference

All analyses are also available as PostgreSQL queries in `sql/queries.sql`:

- Free-to-paid conversion by cohort
- Monthly churn rate calculation
- 12-month cohort retention pivot
- Funnel conversion with step-by-step drop-offs
- A/B test results with conversion rates
- RFM segmentation with NTILE scoring
- MRR growth and LTV by plan tier

---

## How to Publish to GitHub

```bash
# 1. Initialize git repository
git init
git add .
git commit -m "feat: initial SaaS analytics portfolio project"

# 2. Create repository on GitHub (github.com → New repository)
# Name: churnshield-analytics
# Visibility: Public

# 3. Connect and push
git remote add origin https://github.com/yourusername/churnshield-analytics.git
git branch -M main
git push -u origin main
```

**Pro tips for GitHub:**
- Add a description: *"Product analytics portfolio: funnel, cohort retention, A/B testing, RFM segmentation for a B2B SaaS"*
- Add topics: `data-analysis`, `product-analytics`, `python`, `streamlit`, `plotly`, `saas`, `ab-testing`, `cohort-analysis`
- Pin the repository on your GitHub profile
- Include a live Streamlit Cloud demo link in the repository description

---

## Deploying to Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" → select your repository → `app.py`
4. Click "Deploy" — live in ~2 minutes
5. Share the URL in your resume and LinkedIn

---

## Author

Built as a portfolio project demonstrating end-to-end product analytics skills:
- Business problem framing
- Synthetic data generation with realistic distributions
- EDA and data cleaning
- SQL analytical queries (PostgreSQL)
- Product metrics: conversion, retention, cohort analysis, A/B testing, segmentation
- Interactive Streamlit dashboard

**Stack:** Python · Pandas · NumPy · Plotly · SciPy · Scikit-learn · Streamlit · PostgreSQL

---

*If you found this useful, please ⭐ star the repository!*
