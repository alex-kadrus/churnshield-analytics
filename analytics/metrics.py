"""
Core SaaS product metrics calculations.

Includes: MRR, ARR, ARPU, Churn Rate, LTV, NRR, conversion rates.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_mrr_over_time(subscriptions: pd.DataFrame) -> pd.DataFrame:
    """Monthly MRR aggregated by month."""
    subs = subscriptions.copy()
    subs["month"] = pd.to_datetime(subs["period_start"]).dt.to_period("M")
    mrr_monthly = (
        subs.groupby("month")["mrr"]
        .sum()
        .reset_index()
        .rename(columns={"mrr": "total_mrr"})
    )
    mrr_monthly["month"] = mrr_monthly["month"].dt.to_timestamp()
    mrr_monthly["arr"] = mrr_monthly["total_mrr"] * 12
    mrr_monthly["mom_growth"] = mrr_monthly["total_mrr"].pct_change() * 100
    return mrr_monthly


def compute_churn_rate(users: pd.DataFrame) -> pd.DataFrame:
    """Monthly churn rate by cohort signup month."""
    df = users[users["plan"] != "free"].copy()
    df["signup_month"] = pd.to_datetime(df["signup_date"]).dt.to_period("M")
    df["churn_month"] = pd.to_datetime(df["churn_date"]).dt.to_period("M")

    monthly = []
    for month in df["signup_month"].unique():
        cohort = df[df["signup_month"] <= month]
        active = len(cohort[cohort["churn_month"].isna() | (cohort["churn_month"] > month)])
        churned_this_month = len(cohort[cohort["churn_month"] == month])
        churn_rate = churned_this_month / len(cohort) if len(cohort) > 0 else 0
        monthly.append({
            "month": month.to_timestamp(),
            "active_users": active,
            "churned": churned_this_month,
            "churn_rate": round(churn_rate * 100, 2),
        })

    return pd.DataFrame(monthly).sort_values("month")


def compute_plan_distribution(users: pd.DataFrame) -> pd.DataFrame:
    """Plan distribution with MRR contribution."""
    dist = (
        users.groupby("plan")
        .agg(
            users=("user_id", "count"),
            total_mrr=("mrr", "sum"),
            churned=("churned", "sum"),
        )
        .reset_index()
    )
    dist["churn_rate_pct"] = (dist["churned"] / dist["users"] * 100).round(1)
    dist["avg_mrr_per_user"] = (dist["total_mrr"] / dist["users"]).round(2)
    plan_order = ["free", "starter", "professional", "enterprise"]
    dist["plan"] = pd.Categorical(dist["plan"], categories=plan_order, ordered=True)
    return dist.sort_values("plan").reset_index(drop=True)


def compute_ltv(users: pd.DataFrame, subscriptions: pd.DataFrame) -> pd.DataFrame:
    """Customer LTV per plan tier."""
    paid = users[users["plan"] != "free"].copy()
    total_rev = subscriptions.groupby("user_id")["mrr"].sum().reset_index()
    total_rev.columns = ["user_id", "total_revenue"]
    merged = paid.merge(total_rev, on="user_id", how="left")
    merged["total_revenue"] = merged["total_revenue"].fillna(0)

    ltv_by_plan = (
        merged.groupby("plan")["total_revenue"]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
    )
    ltv_by_plan.columns = ["plan", "avg_ltv", "median_ltv", "std_ltv", "n_users"]
    return ltv_by_plan


def compute_kpi_summary(users: pd.DataFrame, subscriptions: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Top-level KPI dashboard summary."""
    total_users = len(users)
    paid_users = len(users[users["plan"] != "free"])
    free_to_paid_rate = paid_users / total_users

    total_mrr = users["mrr"].sum()
    total_arr = total_mrr * 12

    churned_paid = len(users[(users["plan"] != "free") & (users["churned"])])
    churn_rate = churned_paid / paid_users if paid_users > 0 else 0

    avg_mrr_per_user = total_mrr / paid_users if paid_users > 0 else 0

    avg_churn_days = (
        (users[users["churned"]]["churn_date"] - users[users["churned"]]["signup_date"])
        .dt.days.mean()
    )
    avg_ltv = avg_mrr_per_user / churn_rate if churn_rate > 0 else 0

    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "free_users": total_users - paid_users,
        "free_to_paid_rate": round(free_to_paid_rate * 100, 1),
        "total_mrr": round(total_mrr, 0),
        "total_arr": round(total_arr, 0),
        "avg_mrr_per_user": round(avg_mrr_per_user, 2),
        "overall_churn_rate": round(churn_rate * 100, 1),
        "avg_days_to_churn": round(avg_churn_days, 0) if not pd.isna(avg_churn_days) else 0,
        "estimated_ltv": round(avg_ltv, 0),
        "total_events": len(events),
    }
