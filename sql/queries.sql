-- =============================================================
-- ChurnShield SaaS Analytics — SQL Reference Queries
-- Database: PostgreSQL
-- =============================================================

-- ---------------------------------------------------------------
-- 1. FREE-TO-PAID CONVERSION RATE BY SIGNUP COHORT
-- ---------------------------------------------------------------
SELECT
    DATE_TRUNC('month', u.signup_date) AS cohort_month,
    COUNT(*)                           AS total_signups,
    SUM(CASE WHEN u.plan != 'free' THEN 1 ELSE 0 END) AS paid_users,
    ROUND(
        100.0 * SUM(CASE WHEN u.plan != 'free' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                  AS conversion_rate_pct
FROM users u
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------------
-- 2. MONTHLY CHURN RATE
-- ---------------------------------------------------------------
WITH monthly_base AS (
    SELECT
        DATE_TRUNC('month', signup_date) AS month,
        COUNT(*) FILTER (WHERE plan != 'free') AS paid_at_start
    FROM users
    GROUP BY 1
),
monthly_churned AS (
    SELECT
        DATE_TRUNC('month', churn_date) AS month,
        COUNT(*) AS churned_count
    FROM users
    WHERE churned = TRUE AND plan != 'free'
    GROUP BY 1
)
SELECT
    b.month,
    b.paid_at_start,
    COALESCE(c.churned_count, 0) AS churned,
    ROUND(
        100.0 * COALESCE(c.churned_count, 0) / NULLIF(b.paid_at_start, 0),
        2
    ) AS churn_rate_pct
FROM monthly_base b
LEFT JOIN monthly_churned c ON b.month = c.month
ORDER BY b.month;


-- ---------------------------------------------------------------
-- 3. COHORT RETENTION (12 MONTHS)
-- ---------------------------------------------------------------
WITH cohorts AS (
    SELECT
        user_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM users
),
retention AS (
    SELECT
        c.cohort_month,
        COUNT(DISTINCT c.user_id)               AS cohort_size,
        COUNT(DISTINCT CASE WHEN
            u.churn_date IS NULL OR u.churn_date > c.cohort_month + INTERVAL '1 month'
            THEN c.user_id END)                 AS retained_m1,
        COUNT(DISTINCT CASE WHEN
            u.churn_date IS NULL OR u.churn_date > c.cohort_month + INTERVAL '3 months'
            THEN c.user_id END)                 AS retained_m3,
        COUNT(DISTINCT CASE WHEN
            u.churn_date IS NULL OR u.churn_date > c.cohort_month + INTERVAL '6 months'
            THEN c.user_id END)                 AS retained_m6,
        COUNT(DISTINCT CASE WHEN
            u.churn_date IS NULL OR u.churn_date > c.cohort_month + INTERVAL '12 months'
            THEN c.user_id END)                 AS retained_m12
    FROM cohorts c
    JOIN users u USING (user_id)
    GROUP BY 1
)
SELECT
    cohort_month,
    cohort_size,
    ROUND(100.0 * retained_m1  / cohort_size, 1) AS retention_m1_pct,
    ROUND(100.0 * retained_m3  / cohort_size, 1) AS retention_m3_pct,
    ROUND(100.0 * retained_m6  / cohort_size, 1) AS retention_m6_pct,
    ROUND(100.0 * retained_m12 / cohort_size, 1) AS retention_m12_pct
FROM retention
ORDER BY cohort_month;


-- ---------------------------------------------------------------
-- 4. FUNNEL CONVERSION ANALYSIS
-- ---------------------------------------------------------------
WITH event_counts AS (
    SELECT
        event,
        COUNT(DISTINCT user_id) AS users_reached
    FROM events
    GROUP BY event
),
funnel_ordered AS (
    SELECT
        event,
        users_reached,
        LAG(users_reached) OVER (ORDER BY
            CASE event
                WHEN 'signup'               THEN 1
                WHEN 'email_verified'       THEN 2
                WHEN 'onboarding_started'   THEN 3
                WHEN 'onboarding_completed' THEN 4
                WHEN 'first_feature_used'   THEN 5
                WHEN 'team_member_invited'  THEN 6
                WHEN 'integration_connected' THEN 7
                WHEN 'subscription_upgraded' THEN 8
            END
        ) AS prev_step_users
    FROM event_counts
)
SELECT
    event                                   AS funnel_step,
    users_reached,
    ROUND(100.0 * users_reached / MAX(users_reached) OVER (), 1) AS conversion_from_top_pct,
    ROUND(100.0 * users_reached / NULLIF(prev_step_users, 0), 1) AS conversion_from_prev_pct,
    ROUND(100.0 * (1 - users_reached::FLOAT / NULLIF(prev_step_users, 0)), 1) AS drop_off_pct
FROM funnel_ordered
ORDER BY
    CASE event
        WHEN 'signup'               THEN 1
        WHEN 'email_verified'       THEN 2
        WHEN 'onboarding_started'   THEN 3
        WHEN 'onboarding_completed' THEN 4
        WHEN 'first_feature_used'   THEN 5
        WHEN 'team_member_invited'  THEN 6
        WHEN 'integration_connected' THEN 7
        WHEN 'subscription_upgraded' THEN 8
    END;


-- ---------------------------------------------------------------
-- 5. A/B TEST RESULTS — SUBSCRIPTION CONVERSION
-- ---------------------------------------------------------------
SELECT
    u.ab_variant,
    COUNT(DISTINCT u.user_id)                             AS total_users,
    COUNT(DISTINCT e.user_id)                             AS converted_users,
    ROUND(
        100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id),
        2
    )                                                     AS conversion_rate_pct
FROM users u
LEFT JOIN events e
    ON u.user_id = e.user_id
    AND e.event = 'subscription_upgraded'
GROUP BY u.ab_variant;


-- ---------------------------------------------------------------
-- 6. RFM SEGMENTATION
-- ---------------------------------------------------------------
WITH rfm_raw AS (
    SELECT
        u.user_id,
        u.plan,
        u.mrr,
        u.churned,
        EXTRACT(DAY FROM NOW() - MAX(e.event_date)) AS recency_days,
        COUNT(e.event)                               AS frequency,
        u.mrr                                        AS monetary
    FROM users u
    LEFT JOIN events e ON u.user_id = e.user_id
    GROUP BY u.user_id, u.plan, u.mrr, u.churned
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency)          AS f_score,
        NTILE(5) OVER (ORDER BY monetary)           AS m_score
    FROM rfm_raw
)
SELECT
    user_id,
    plan,
    mrr,
    churned,
    recency_days,
    frequency,
    r_score,
    f_score,
    m_score,
    ROUND((r_score + f_score + m_score) / 3.0, 2) AS rfm_avg_score,
    CASE
        WHEN (r_score + f_score + m_score) / 3.0 >= 4.5 THEN 'Champions'
        WHEN (r_score + f_score + m_score) / 3.0 >= 3.5 THEN 'Loyal Users'
        WHEN r_score >= 4 AND f_score <= 2            THEN 'Recent Users'
        WHEN r_score <= 2 AND f_score >= 4            THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2            THEN 'Churned/Lost'
        WHEN m_score >= 4                             THEN 'High-Value'
        ELSE                                               'Potential Loyalists'
    END AS segment
FROM rfm_scored
ORDER BY rfm_avg_score DESC;


-- ---------------------------------------------------------------
-- 7. MRR GROWTH & REVENUE BREAKDOWN BY PLAN
-- ---------------------------------------------------------------
SELECT
    DATE_TRUNC('month', s.period_start) AS month,
    s.plan,
    COUNT(DISTINCT s.user_id)           AS active_subscribers,
    SUM(s.mrr)                          AS total_mrr,
    ROUND(AVG(s.mrr), 2)               AS avg_mrr_per_user
FROM subscriptions s
GROUP BY 1, 2
ORDER BY 1, 2;


-- ---------------------------------------------------------------
-- 8. CUSTOMER LIFETIME VALUE BY PLAN
-- ---------------------------------------------------------------
SELECT
    u.plan,
    COUNT(DISTINCT u.user_id)                    AS total_users,
    ROUND(AVG(total_rev.revenue), 2)             AS avg_ltv,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY total_rev.revenue), 2)         AS median_ltv,
    ROUND(AVG(u.mrr), 2)                        AS avg_mrr
FROM users u
JOIN (
    SELECT user_id, SUM(mrr) AS revenue
    FROM subscriptions
    GROUP BY user_id
) total_rev ON u.user_id = total_rev.user_id
WHERE u.plan != 'free'
GROUP BY u.plan
ORDER BY avg_ltv DESC;
