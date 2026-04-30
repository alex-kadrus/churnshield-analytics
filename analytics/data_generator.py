"""
Synthetic SaaS dataset generator for ChurnShield Analytics.

Generates realistic user, event, subscription, and experiment data
for a B2B SaaS platform with ~3,000 users over 18 months.

Funnel design: FUNNEL_CUMULATIVE_RATES defines cumulative (from-top) conversion
rates for each step. Step-by-step conditional rates are derived automatically.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 6, 30)
N_USERS = 3_000

PLANS = {
    "free": {"price": 0, "weight": 0.55},
    "starter": {"price": 29, "weight": 0.25},
    "professional": {"price": 99, "weight": 0.13},
    "enterprise": {"price": 299, "weight": 0.07},
}

COUNTRIES = {
    "United States": 0.38,
    "United Kingdom": 0.12,
    "Germany": 0.09,
    "France": 0.07,
    "Canada": 0.07,
    "Australia": 0.06,
    "Netherlands": 0.05,
    "India": 0.08,
    "Brazil": 0.05,
    "Other": 0.03,
}

INDUSTRIES = {
    "SaaS/Tech": 0.30,
    "E-commerce": 0.18,
    "Finance": 0.14,
    "Healthcare": 0.10,
    "Marketing": 0.12,
    "Education": 0.08,
    "Other": 0.08,
}

COMPANY_SIZES = {
    "1-10": 0.28,
    "11-50": 0.32,
    "51-200": 0.22,
    "201-1000": 0.12,
    "1000+": 0.06,
}

FUNNEL_STEPS = [
    "signup",
    "email_verified",
    "onboarding_started",
    "onboarding_completed",
    "first_feature_used",
    "team_member_invited",
    "integration_connected",
    "subscription_upgraded",
]

# Cumulative (from-top) conversion rates — what % of all signups reach this step
FUNNEL_CUMULATIVE_CONTROL = {
    "signup": 1.00,
    "email_verified": 0.87,
    "onboarding_started": 0.74,
    "onboarding_completed": 0.52,
    "first_feature_used": 0.44,
    "team_member_invited": 0.31,
    "integration_connected": 0.22,
    "subscription_upgraded": 0.14,
}

# Treatment group (new onboarding flow) — ~32% lift in final conversion
FUNNEL_CUMULATIVE_TREATMENT = {
    "signup": 1.00,
    "email_verified": 0.89,
    "onboarding_started": 0.81,
    "onboarding_completed": 0.63,
    "first_feature_used": 0.55,
    "team_member_invited": 0.39,
    "integration_connected": 0.28,
    "subscription_upgraded": 0.185,
}


def _cumulative_to_conditional(cumulative: dict) -> dict:
    """Convert cumulative-from-top rates to conditional step-by-step rates."""
    steps = list(cumulative.keys())
    conditional = {}
    for i, step in enumerate(steps):
        if i == 0:
            conditional[step] = 1.0
        else:
            prev_rate = cumulative[steps[i - 1]]
            curr_rate = cumulative[step]
            conditional[step] = curr_rate / prev_rate if prev_rate > 0 else 0.0
    return conditional


FUNNEL_CONDITIONAL_CONTROL = _cumulative_to_conditional(FUNNEL_CUMULATIVE_CONTROL)
FUNNEL_CONDITIONAL_TREATMENT = _cumulative_to_conditional(FUNNEL_CUMULATIVE_TREATMENT)


def _weighted_choice(choices: dict) -> str:
    keys = list(choices.keys())
    weights = list(choices.values())
    return np.random.choice(keys, p=weights)


def generate_users() -> pd.DataFrame:
    users = []
    for i in range(N_USERS):
        signup_date = START_DATE + timedelta(
            days=int(np.random.exponential(scale=300) % (END_DATE - START_DATE).days)
        )
        signup_date = min(signup_date, END_DATE - timedelta(days=1))

        plan = _weighted_choice({k: v["weight"] for k, v in PLANS.items()})
        country = _weighted_choice(COUNTRIES)
        industry = _weighted_choice(INDUSTRIES)
        company_size = _weighted_choice(COMPANY_SIZES)

        variant = "treatment" if i % 2 == 0 else "control"

        base_churn_prob = {
            "free": 0.65,
            "starter": 0.35,
            "professional": 0.20,
            "enterprise": 0.10,
        }[plan]
        churned = np.random.random() < base_churn_prob

        if churned:
            days_to_churn = int(np.random.exponential(scale=60)) + 7
            churn_date = signup_date + timedelta(days=days_to_churn)
            churn_date = min(churn_date, END_DATE)
        else:
            churn_date = None

        users.append({
            "user_id": f"usr_{i+1:05d}",
            "signup_date": signup_date,
            "plan": plan,
            "country": country,
            "industry": industry,
            "company_size": company_size,
            "ab_variant": variant,
            "churned": churned,
            "churn_date": churn_date,
            "mrr": PLANS[plan]["price"],
            "age_group": np.random.choice(
                ["18-24", "25-34", "35-44", "45-54", "55+"],
                p=[0.08, 0.35, 0.32, 0.18, 0.07],
            ),
        })

    return pd.DataFrame(users)


def generate_events(users: pd.DataFrame) -> pd.DataFrame:
    events = []
    for _, user in users.iterrows():
        conversions = (
            FUNNEL_CONDITIONAL_TREATMENT
            if user["ab_variant"] == "treatment"
            else FUNNEL_CONDITIONAL_CONTROL
        )

        current_date = user["signup_date"]
        for step in FUNNEL_STEPS:
            prob = conversions[step]
            if np.random.random() < prob:
                delay_hours = int(np.random.exponential(scale=12))
                current_date = current_date + timedelta(hours=delay_hours)
                if current_date > END_DATE:
                    break
                if user["churn_date"] and current_date > user["churn_date"]:
                    break
                events.append({
                    "user_id": user["user_id"],
                    "event": step,
                    "event_date": current_date,
                    "ab_variant": user["ab_variant"],
                })
            else:
                break  # user dropped off here

    df = pd.DataFrame(events)
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df.sort_values(["user_id", "event_date"]).reset_index(drop=True)


def generate_subscriptions(users: pd.DataFrame) -> pd.DataFrame:
    subs = []
    paid_users = users[users["plan"] != "free"].copy()

    for _, user in paid_users.iterrows():
        start = user["signup_date"]
        end = user["churn_date"] if user["churned"] else END_DATE

        current = start
        while current < end:
            next_month = current + timedelta(days=30)
            mrr = user["mrr"]
            mrr_jitter = mrr * np.random.normal(1, 0.02)
            subs.append({
                "user_id": user["user_id"],
                "plan": user["plan"],
                "period_start": current,
                "period_end": min(next_month, end),
                "mrr": round(max(mrr_jitter, 0), 2),
                "status": "active",
            })
            current = next_month

    return pd.DataFrame(subs)


def generate_all() -> dict[str, pd.DataFrame]:
    users = generate_users()
    events = generate_events(users)
    subscriptions = generate_subscriptions(users)

    users["signup_date"] = pd.to_datetime(users["signup_date"])
    users["churn_date"] = pd.to_datetime(users["churn_date"])

    return {
        "users": users,
        "events": events,
        "subscriptions": subscriptions,
    }


_cache: dict | None = None


def get_data() -> dict[str, pd.DataFrame]:
    global _cache
    if _cache is None:
        _cache = generate_all()
    return _cache
