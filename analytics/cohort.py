"""
Cohort retention analysis for SaaS users.

Computes monthly cohort retention tables and survival curves.
"""

import pandas as pd
import numpy as np


def compute_cohort_retention(users: pd.DataFrame, months: int = 12) -> pd.DataFrame:
    """
    Build a cohort retention matrix.

    Rows = signup cohort month
    Columns = months since signup (0, 1, 2, ...)
    Values = retention rate (%)
    """
    df = users.copy()
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["churn_date"] = pd.to_datetime(df["churn_date"])
    df["cohort_month"] = df["signup_date"].dt.to_period("M")

    cohorts = sorted(df["cohort_month"].unique())
    retention_rows = []

    for cohort in cohorts:
        cohort_users = df[df["cohort_month"] == cohort]
        n_users = len(cohort_users)
        row = {"cohort": str(cohort), "cohort_size": n_users}

        cohort_start = cohort.to_timestamp()

        for m in range(months + 1):
            check_date = cohort_start + pd.DateOffset(months=m)
            if check_date > pd.Timestamp("2024-06-30"):
                row[f"month_{m}"] = np.nan
                continue

            still_active = cohort_users[
                cohort_users["churn_date"].isna()
                | (cohort_users["churn_date"] > check_date)
            ]
            retention = len(still_active) / n_users if n_users > 0 else 0
            row[f"month_{m}"] = round(retention * 100, 1)

        retention_rows.append(row)

    df_ret = pd.DataFrame(retention_rows)
    return df_ret


def compute_cohort_retention_pivot(retention_df: pd.DataFrame) -> pd.DataFrame:
    """Return a pivot-friendly matrix with cohort as index."""
    cols = ["cohort"] + [c for c in retention_df.columns if c.startswith("month_")]
    pivot = retention_df[cols].set_index("cohort")
    pivot.columns = [int(c.split("_")[1]) for c in pivot.columns]
    return pivot


def compute_average_retention_curve(retention_df: pd.DataFrame) -> pd.DataFrame:
    """Average retention curve across all cohorts."""
    month_cols = [c for c in retention_df.columns if c.startswith("month_")]
    avg = retention_df[month_cols].mean().reset_index()
    avg.columns = ["period", "avg_retention_pct"]
    avg["month"] = avg["period"].str.extract(r"(\d+)").astype(int)
    return avg.sort_values("month")


def compute_plan_retention(users: pd.DataFrame, plan: str, months: int = 12) -> pd.DataFrame:
    """Retention curve for a specific plan tier."""
    plan_users = users[users["plan"] == plan].copy()
    return compute_cohort_retention(plan_users, months=months)
