"""
Funnel analysis for SaaS onboarding flow.

Computes step-by-step conversion rates, drop-off points,
and time-to-convert distributions.
"""

import pandas as pd
import numpy as np

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

STEP_LABELS = {
    "signup": "Signup",
    "email_verified": "Email Verified",
    "onboarding_started": "Onboarding Started",
    "onboarding_completed": "Onboarding Completed",
    "first_feature_used": "First Feature Used",
    "team_member_invited": "Team Member Invited",
    "integration_connected": "Integration Connected",
    "subscription_upgraded": "Subscription Upgraded",
}


def compute_funnel(events: pd.DataFrame, users: pd.DataFrame, variant: str = "all") -> pd.DataFrame:
    """
    Compute funnel conversion rates.

    variant: 'all', 'control', or 'treatment'
    """
    if variant != "all":
        user_ids = users[users["ab_variant"] == variant]["user_id"]
        ev = events[events["user_id"].isin(user_ids)]
    else:
        ev = events.copy()

    total_users = ev["user_id"].nunique() if len(ev) > 0 else 1
    rows = []

    for step in FUNNEL_STEPS:
        step_events = ev[ev["event"] == step]
        users_at_step = step_events["user_id"].nunique()
        rows.append({
            "step": step,
            "label": STEP_LABELS[step],
            "users": users_at_step,
            "conversion_from_top": round(users_at_step / total_users * 100, 1) if total_users else 0,
        })

    df = pd.DataFrame(rows)
    df["conversion_from_prev"] = df["users"] / df["users"].shift(1).replace(0, np.nan) * 100
    df["conversion_from_prev"] = df["conversion_from_prev"].round(1)
    df.loc[0, "conversion_from_prev"] = 100.0
    df["drop_off"] = (100 - df["conversion_from_prev"]).round(1)
    df.loc[0, "drop_off"] = 0.0
    return df


def compute_funnel_comparison(events: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """Side-by-side funnel comparison: control vs treatment."""
    control = compute_funnel(events, users, variant="control").add_suffix("_control")
    treatment = compute_funnel(events, users, variant="treatment").add_suffix("_treatment")

    control = control.rename(columns={"step_control": "step", "label_control": "label"})
    treatment = treatment.drop(columns=["step_treatment", "label_treatment"])

    merged = pd.concat([control, treatment], axis=1)
    merged["lift_pct"] = (
        (merged["conversion_from_top_treatment"] - merged["conversion_from_top_control"])
        / merged["conversion_from_top_control"] * 100
    ).round(1)
    return merged


def compute_time_to_convert(events: pd.DataFrame) -> pd.DataFrame:
    """
    Compute median hours between funnel steps.
    """
    ev = events.copy()
    ev["event_date"] = pd.to_datetime(ev["event_date"])

    user_funnels = ev.pivot_table(
        index="user_id", columns="event", values="event_date", aggfunc="min"
    ).reset_index()

    rows = []
    for i in range(1, len(FUNNEL_STEPS)):
        prev = FUNNEL_STEPS[i - 1]
        curr = FUNNEL_STEPS[i]
        if prev in user_funnels.columns and curr in user_funnels.columns:
            diff = (user_funnels[curr] - user_funnels[prev]).dt.total_seconds() / 3600
            diff = diff.dropna()
            rows.append({
                "from_step": STEP_LABELS[prev],
                "to_step": STEP_LABELS[curr],
                "median_hours": round(diff.median(), 1),
                "p25_hours": round(diff.quantile(0.25), 1),
                "p75_hours": round(diff.quantile(0.75), 1),
                "n_users": len(diff),
            })

    return pd.DataFrame(rows)
