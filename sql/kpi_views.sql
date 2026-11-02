-- =============================================================
-- Moxie Field Ops Intelligence -- Analytical SQL Layer
-- DuckDB: CTEs, window functions, dimensional joins
-- =============================================================

-- 1. Cancellation rate by ZIP code (ranked worst-first)
CREATE OR REPLACE VIEW vw_cancel_by_zip AS
WITH job_counts AS (
    SELECT
        zip_code,
        COUNT(*)                                            AS total_jobs,
        SUM(CASE WHEN NOT is_completed THEN 1 ELSE 0 END)  AS cancelled_jobs,
        SUM(job_revenue)                                    AS total_revenue,
        ROUND(100.0 * SUM(CASE WHEN NOT is_completed THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                            AS cancel_rate_pct
    FROM moxie.fact_jobs
    GROUP BY zip_code
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY cancel_rate_pct DESC) AS cancel_rank
    FROM job_counts
)
SELECT * FROM ranked ORDER BY cancel_rank;

-- 2. Revenue per mile by technician (efficiency score)
CREATE OR REPLACE VIEW vw_tech_efficiency AS
WITH tech_stats AS (
    SELECT
        r.tech_id,
        t.tech_name,
        t.region,
        COUNT(r.job_id)                         AS completed_jobs,
        ROUND(SUM(r.miles_driven), 1)           AS total_miles,
        ROUND(SUM(r.fuel_cost), 2)              AS total_fuel_cost,
        ROUND(SUM(r.drive_minutes) / 60.0, 1)  AS total_drive_hours,
        ROUND(SUM(j.job_revenue), 2)            AS total_revenue,
        ROUND(SUM(j.job_revenue) / NULLIF(SUM(r.miles_driven), 0), 2)
                                                AS revenue_per_mile,
        ROUND(SUM(r.drive_minutes) / NULLIF(COUNT(r.job_id), 0), 1)
                                                AS avg_drive_min_per_job
    FROM moxie.fact_routes r
    JOIN moxie.fact_jobs j     ON r.job_id  = j.job_id
    JOIN moxie.dim_technician t ON r.tech_id = t.tech_id
    GROUP BY r.tech_id, t.tech_name, t.region
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY revenue_per_mile DESC) AS efficiency_rank
    FROM tech_stats
)
SELECT * FROM ranked ORDER BY efficiency_rank;

-- 3. Scheduling gap analysis -- jobs per day vs capacity
CREATE OR REPLACE VIEW vw_scheduling_gaps AS
WITH daily AS (
    SELECT
        CAST(scheduled_at AS DATE)              AS job_date,
        COUNT(*)                                AS scheduled_jobs,
        SUM(CASE WHEN is_completed THEN 1 ELSE 0 END)   AS completed_jobs,
        SUM(CASE WHEN NOT is_completed THEN 1 ELSE 0 END) AS cancelled_jobs,
        ROUND(SUM(job_revenue), 2)              AS daily_revenue,
        COUNT(DISTINCT tech_id)                 AS active_techs
    FROM moxie.fact_jobs
    GROUP BY CAST(scheduled_at AS DATE)
),
with_rolling AS (
    SELECT *,
        ROUND(AVG(completed_jobs) OVER (
            ORDER BY job_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 1) AS rolling_7day_avg_completed,
        ROUND(AVG(daily_revenue) OVER (
            ORDER BY job_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2) AS rolling_7day_avg_revenue
    FROM daily
)
SELECT * FROM with_rolling ORDER BY job_date;

-- 4. Cancellation reason breakdown
CREATE OR REPLACE VIEW vw_cancel_reasons AS
SELECT
    cancel_reason,
    COUNT(*)                                            AS occurrences,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_cancels,
    COUNT(DISTINCT zip_code)                            AS zips_affected
FROM moxie.fact_jobs
WHERE NOT is_completed AND cancel_reason IS NOT NULL
GROUP BY cancel_reason
ORDER BY occurrences DESC;
