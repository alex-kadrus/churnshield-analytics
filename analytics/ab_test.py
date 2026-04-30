"""
A/B test statistical analysis.

Tests: new onboarding flow (treatment) vs. original (control).
Primary metric: subscription_upgraded conversion rate.
Secondary metrics: onboarding_completed, first_feature_used.
"""

import pandas as pd
import numpy as np
from scipy import stats


def compute_ab_summary(events: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    """
    Summary table of A/B test results for all key metrics.
    """
    metrics = [
        ("email_verified", "Email Verified"),
        ("onboarding_completed", "Onboarding Completed"),
        ("first_feature_used", "First Feature Used"),
        ("team_member_invited", "Team Member Invited"),
        ("subscription_upgraded", "Subscription Upgraded (Primary)"),
    ]

    rows = []
    for variant in ["control", "treatment"]:
        variant_users = users[users["ab_variant"] == variant]["user_id"]
        n_total = len(variant_users)
        variant_events = events[events["user_id"].isin(variant_users)]

        for event, label in metrics:
            converted = variant_events[variant_events["event"] == event]["user_id"].nunique()
            rate = converted / n_total if n_total > 0 else 0
            rows.append({
                "metric": label,
                "variant": variant,
                "n_users": n_total,
                "converted": converted,
                "conversion_rate": round(rate * 100, 2),
            })

    return pd.DataFrame(rows)


def run_ab_test(events: pd.DataFrame, users: pd.DataFrame, metric_event: str = "subscription_upgraded") -> dict:
    """
    Two-proportion z-test for A/B test significance.

    Returns: z-stat, p-value, confidence interval, relative lift, power.
    """
    control_users = users[users["ab_variant"] == "control"]["user_id"]
    treatment_users = users[users["ab_variant"] == "treatment"]["user_id"]

    n_c = len(control_users)
    n_t = len(treatment_users)

    control_events = events[events["user_id"].isin(control_users) & (events["event"] == metric_event)]
    treatment_events = events[events["user_id"].isin(treatment_users) & (events["event"] == metric_event)]

    x_c = control_events["user_id"].nunique()
    x_t = treatment_events["user_id"].nunique()

    p_c = x_c / n_c
    p_t = x_t / n_t

    pooled_p = (x_c + x_t) / (n_c + n_t)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1 / n_c + 1 / n_t))
    z_stat = (p_t - p_c) / se if se > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    se_diff = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    ci_low = (p_t - p_c) - 1.96 * se_diff
    ci_high = (p_t - p_c) + 1.96 * se_diff

    relative_lift = (p_t - p_c) / p_c * 100 if p_c > 0 else 0

    power = 1 - stats.norm.cdf(1.96 - abs(z_stat))

    return {
        "metric": metric_event,
        "control_users": n_c,
        "treatment_users": n_t,
        "control_conversions": x_c,
        "treatment_conversions": x_t,
        "control_rate": round(p_c * 100, 2),
        "treatment_rate": round(p_t * 100, 2),
        "absolute_lift": round((p_t - p_c) * 100, 2),
        "relative_lift_pct": round(relative_lift, 1),
        "z_stat": round(z_stat, 3),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "ci_low": round(ci_low * 100, 2),
        "ci_high": round(ci_high * 100, 2),
        "statistical_power": round(power * 100, 1),
    }


def compute_daily_conversion_rates(events: pd.DataFrame, users: pd.DataFrame, metric_event: str = "subscription_upgraded") -> pd.DataFrame:
    """
    Daily rolling conversion rate by variant (for time-series plot).
    """
    control_ids = set(users[users["ab_variant"] == "control"]["user_id"])
    treatment_ids = set(users[users["ab_variant"] == "treatment"]["user_id"])

    ev = events[events["event"] == metric_event].copy()
    ev["date"] = pd.to_datetime(ev["event_date"]).dt.date

    rows = []
    for date, group in ev.groupby("date"):
        c_count = group[group["user_id"].isin(control_ids)]["user_id"].nunique()
        t_count = group[group["user_id"].isin(treatment_ids)]["user_id"].nunique()
        rows.append({
            "date": date,
            "control": c_count,
            "treatment": t_count,
        })

    df = pd.DataFrame(rows).sort_values("date")
    df["control_cumulative"] = df["control"].cumsum()
    df["treatment_cumulative"] = df["treatment"].cumsum()
    df["control_rate"] = df["control_cumulative"] / len(control_ids) * 100
    df["treatment_rate"] = df["treatment_cumulative"] / len(treatment_ids) * 100
    return df


def compute_sample_size_analysis() -> pd.DataFrame:
    """Minimum detectable effect and required sample size for common MDE levels."""
    rows = []
    baseline = 0.14
    alpha = 0.05
    power = 0.80

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    for mde in [0.05, 0.10, 0.15, 0.20, 0.30]:
        p2 = baseline * (1 + mde)
        p_bar = (baseline + p2) / 2
        n = (z_alpha + z_beta) ** 2 * 2 * p_bar * (1 - p_bar) / (p2 - baseline) ** 2
        rows.append({
            "mde_pct": int(mde * 100),
            "baseline_rate": baseline * 100,
            "target_rate": round(p2 * 100, 2),
            "required_n_per_group": int(np.ceil(n)),
            "total_required": int(np.ceil(n * 2)),
            "duration_days_1000_signups_day": round(np.ceil(n * 2) / 1000, 1),
        })

    return pd.DataFrame(rows)
