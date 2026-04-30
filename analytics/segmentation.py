"""
User segmentation analysis for SaaS users.

Implements RFM-style segmentation adapted for SaaS:
- Recency: days since last event
- Frequency: total events (engagement score)
- Monetary: MRR contribution

Also includes: plan-based segments, industry segments, geographic analysis.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


REFERENCE_DATE = pd.Timestamp("2024-06-30")


def compute_rfm(users: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """
    Compute RFM scores for each user.

    R = Recency (days since last event — lower = better)
    F = Frequency (total events — higher = better)
    M = Monetary (MRR — higher = better)
    """
    last_event = (
        events.groupby("user_id")["event_date"]
        .max()
        .reset_index()
        .rename(columns={"event_date": "last_event_date"})
    )
    last_event["last_event_date"] = pd.to_datetime(last_event["last_event_date"])
    last_event["recency_days"] = (REFERENCE_DATE - last_event["last_event_date"]).dt.days

    event_count = events.groupby("user_id").size().reset_index(name="event_frequency")

    rfm = users[["user_id", "mrr", "plan", "churned", "signup_date", "country", "industry", "company_size"]].copy()
    rfm = rfm.merge(last_event[["user_id", "recency_days", "last_event_date"]], on="user_id", how="left")
    rfm = rfm.merge(event_count, on="user_id", how="left")
    rfm["recency_days"] = rfm["recency_days"].fillna(999)
    rfm["event_frequency"] = rfm["event_frequency"].fillna(0)

    rfm["r_score"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop")
    rfm["f_score"] = pd.qcut(rfm["event_frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["m_score"] = pd.cut(
        rfm["mrr"],
        bins=[-1, 0, 29, 99, 299, 10000],
        labels=[1, 2, 3, 4, 5],
    )

    for col in ["r_score", "f_score", "m_score"]:
        rfm[col] = rfm[col].astype(float)

    rfm["rfm_score"] = (rfm["r_score"] + rfm["f_score"] + rfm["m_score"]) / 3

    def segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        rfm = (r + f + m) / 3
        if rfm >= 4.5:
            return "Champions"
        elif rfm >= 3.5:
            return "Loyal Users"
        elif r >= 4 and f <= 2:
            return "Recent Users"
        elif r <= 2 and f >= 4:
            return "At Risk"
        elif r <= 2 and f <= 2:
            return "Churned/Lost"
        elif m >= 4:
            return "High-Value"
        else:
            return "Potential Loyalists"

    rfm["segment"] = rfm.apply(segment, axis=1)
    return rfm


def compute_segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Aggregate statistics per segment."""
    summary = (
        rfm.groupby("segment")
        .agg(
            users=("user_id", "count"),
            avg_mrr=("mrr", "mean"),
            total_mrr=("mrr", "sum"),
            churn_rate=("churned", "mean"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("event_frequency", "mean"),
            avg_rfm_score=("rfm_score", "mean"),
        )
        .reset_index()
    )
    summary["churn_rate"] = (summary["churn_rate"] * 100).round(1)
    summary["avg_mrr"] = summary["avg_mrr"].round(2)
    summary["avg_recency"] = summary["avg_recency"].round(0)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)
    summary["avg_rfm_score"] = summary["avg_rfm_score"].round(2)
    summary["revenue_pct"] = (summary["total_mrr"] / summary["total_mrr"].sum() * 100).round(1)
    return summary.sort_values("avg_rfm_score", ascending=False).reset_index(drop=True)


def compute_kmeans_clusters(rfm: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
    """
    K-Means clustering on RFM features for data-driven segmentation.
    """
    features = rfm[["recency_days", "event_frequency", "mrr"]].copy()
    features = features.fillna(0)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm = rfm.copy()
    rfm["cluster"] = kmeans.fit_predict(scaled)

    centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_info = pd.DataFrame(centers, columns=["avg_recency", "avg_frequency", "avg_mrr"])
    cluster_info["cluster"] = range(n_clusters)

    rfm = rfm.merge(cluster_info, on="cluster")
    return rfm


def compute_geo_distribution(users: pd.DataFrame) -> pd.DataFrame:
    """Geographic distribution with MRR breakdown."""
    geo = (
        users.groupby("country")
        .agg(
            users=("user_id", "count"),
            paid_users=("mrr", lambda x: (x > 0).sum()),
            total_mrr=("mrr", "sum"),
            churn_rate=("churned", "mean"),
        )
        .reset_index()
    )
    geo["churn_rate"] = (geo["churn_rate"] * 100).round(1)
    geo["conversion_rate"] = (geo["paid_users"] / geo["users"] * 100).round(1)
    return geo.sort_values("total_mrr", ascending=False).reset_index(drop=True)


def compute_industry_breakdown(users: pd.DataFrame) -> pd.DataFrame:
    """Industry breakdown with conversion and MRR."""
    ind = (
        users.groupby("industry")
        .agg(
            users=("user_id", "count"),
            paid=("mrr", lambda x: (x > 0).sum()),
            total_mrr=("mrr", "sum"),
            avg_mrr=("mrr", "mean"),
            churn_rate=("churned", "mean"),
        )
        .reset_index()
    )
    ind["conversion_rate"] = (ind["paid"] / ind["users"] * 100).round(1)
    ind["churn_rate"] = (ind["churn_rate"] * 100).round(1)
    return ind.sort_values("total_mrr", ascending=False).reset_index(drop=True)
