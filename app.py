"""
Moxie Field Ops Intelligence Dashboard
Flask + DuckDB + D3.js

Surfaces three KPIs Moxie's current stack leaves unconnected:
  1. Cancellation rate by ZIP (FieldRoutes job data)
  2. Revenue-per-mile efficiency by technician (Geotab route data)
  3. Scheduling gap trend (daily completed vs capacity)
"""

from flask import Flask, jsonify, render_template
import duckdb
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "moxie_ops.db")


def get_db():
    # In-memory DuckDB session: attach the on-disk DB read-only, then create
    # session-scoped views against it. CREATE VIEW is allowed in-memory.
    con = duckdb.connect(":memory:")
    con.execute(f"ATTACH '{DB_PATH}' AS moxie (READ_ONLY)")
    # Stay on in-memory default db so CREATE VIEW is allowed;
    # SQL views reference tables as moxie.fact_jobs etc.
    sql_path = os.path.join(os.path.dirname(__file__), "sql", "kpi_views.sql")
    with open(sql_path) as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)
    return con


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cancel_by_zip")
def cancel_by_zip():
    con = get_db()
    rows = con.execute("""
        SELECT zip_code, total_jobs, cancelled_jobs,
               cancel_rate_pct, total_revenue, cancel_rank
        FROM vw_cancel_by_zip
        ORDER BY cancel_rank
        LIMIT 20
    """).fetchdf()
    con.close()
    return jsonify(rows.to_dict(orient="records"))


@app.route("/api/tech_efficiency")
def tech_efficiency():
    con = get_db()
    rows = con.execute("""
        SELECT tech_id, tech_name, region, completed_jobs,
               total_miles, total_revenue, revenue_per_mile,
               avg_drive_min_per_job, efficiency_rank
        FROM vw_tech_efficiency
        ORDER BY efficiency_rank
        LIMIT 20
    """).fetchdf()
    con.close()
    return jsonify(rows.to_dict(orient="records"))


@app.route("/api/scheduling_gaps")
def scheduling_gaps():
    con = get_db()
    rows = con.execute("""
        SELECT job_date::VARCHAR AS job_date,
               scheduled_jobs, completed_jobs, cancelled_jobs,
               daily_revenue, active_techs,
               rolling_7day_avg_completed, rolling_7day_avg_revenue
        FROM vw_scheduling_gaps
        ORDER BY job_date
    """).fetchdf()
    con.close()
    return jsonify(rows.to_dict(orient="records"))


@app.route("/api/cancel_reasons")
def cancel_reasons():
    con = get_db()
    rows = con.execute("""
        SELECT cancel_reason, occurrences, pct_of_cancels, zips_affected
        FROM vw_cancel_reasons
    """).fetchdf()
    con.close()
    return jsonify(rows.to_dict(orient="records"))


@app.route("/api/summary")
def summary():
    con = get_db()
    row = con.execute("""
        SELECT
            COUNT(*)                                                AS total_jobs,
            ROUND(100.0 * SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                    AS completion_rate_pct,
            ROUND(SUM(job_revenue), 2)                              AS total_revenue,
            COUNT(DISTINCT tech_id)                                 AS active_techs,
            COUNT(DISTINCT zip_code)                                AS zips_served
        FROM moxie.fact_jobs
    """).fetchone()
    con.close()
    return jsonify({
        "total_jobs": row[0],
        "completion_rate_pct": row[1],
        "total_revenue": row[2],
        "active_techs": row[3],
        "zips_served": row[4]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5050, use_reloader=False)
