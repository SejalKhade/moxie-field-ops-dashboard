"""
Moxie Field Ops Intelligence -- API Tests
pytest: tests each endpoint for shape, types, and business-logic invariants.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app as flask_app


@pytest.fixture(scope="session")
def client():
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


# ── /api/summary ─────────────────────────────────────────────────────────────

def test_summary_returns_200(client):
    r = client.get("/api/summary")
    assert r.status_code == 200


def test_summary_required_keys(client):
    d = client.get("/api/summary").get_json()
    required = {"total_jobs", "completion_rate_pct", "total_revenue",
                "active_techs", "zips_served"}
    assert required.issubset(d.keys())


def test_summary_total_jobs_positive(client):
    d = client.get("/api/summary").get_json()
    assert d["total_jobs"] > 0


def test_summary_completion_rate_valid_range(client):
    d = client.get("/api/summary").get_json()
    assert 0.0 <= d["completion_rate_pct"] <= 100.0


def test_summary_revenue_positive(client):
    d = client.get("/api/summary").get_json()
    assert d["total_revenue"] > 0


# ── /api/cancel_by_zip ────────────────────────────────────────────────────────

def test_cancel_by_zip_returns_200(client):
    assert client.get("/api/cancel_by_zip").status_code == 200


def test_cancel_by_zip_is_list(client):
    data = client.get("/api/cancel_by_zip").get_json()
    assert isinstance(data, list) and len(data) > 0


def test_cancel_by_zip_required_fields(client):
    row = client.get("/api/cancel_by_zip").get_json()[0]
    for field in ("zip_code", "total_jobs", "cancelled_jobs",
                  "cancel_rate_pct", "cancel_rank"):
        assert field in row, f"Missing field: {field}"


def test_cancel_by_zip_rate_in_range(client):
    for row in client.get("/api/cancel_by_zip").get_json():
        assert 0.0 <= row["cancel_rate_pct"] <= 100.0


def test_cancel_by_zip_cancelled_lte_total(client):
    for row in client.get("/api/cancel_by_zip").get_json():
        assert row["cancelled_jobs"] <= row["total_jobs"]


def test_cancel_by_zip_rank_sorted(client):
    data = client.get("/api/cancel_by_zip").get_json()
    ranks = [r["cancel_rank"] for r in data]
    assert ranks == sorted(ranks), "cancel_rank not sorted ascending"


# ── /api/tech_efficiency ─────────────────────────────────────────────────────

def test_tech_efficiency_returns_200(client):
    assert client.get("/api/tech_efficiency").status_code == 200


def test_tech_efficiency_is_list(client):
    data = client.get("/api/tech_efficiency").get_json()
    assert isinstance(data, list) and len(data) > 0


def test_tech_efficiency_required_fields(client):
    row = client.get("/api/tech_efficiency").get_json()[0]
    for field in ("tech_id", "tech_name", "region", "completed_jobs",
                  "total_miles", "total_revenue", "revenue_per_mile",
                  "avg_drive_min_per_job", "efficiency_rank"):
        assert field in row, f"Missing field: {field}"


def test_tech_efficiency_revenue_per_mile_positive(client):
    for row in client.get("/api/tech_efficiency").get_json():
        assert row["revenue_per_mile"] > 0


def test_tech_efficiency_rank_sorted(client):
    data = client.get("/api/tech_efficiency").get_json()
    ranks = [r["efficiency_rank"] for r in data]
    assert ranks == sorted(ranks)


# ── /api/cancel_reasons ──────────────────────────────────────────────────────

def test_cancel_reasons_returns_200(client):
    assert client.get("/api/cancel_reasons").status_code == 200


def test_cancel_reasons_is_list(client):
    data = client.get("/api/cancel_reasons").get_json()
    assert isinstance(data, list) and len(data) > 0


def test_cancel_reasons_required_fields(client):
    row = client.get("/api/cancel_reasons").get_json()[0]
    for field in ("cancel_reason", "occurrences", "pct_of_cancels", "zips_affected"):
        assert field in row, f"Missing field: {field}"


def test_cancel_reasons_pct_sums_to_100(client):
    data = client.get("/api/cancel_reasons").get_json()
    total = sum(r["pct_of_cancels"] for r in data)
    assert abs(total - 100.0) < 1.0, f"pct sum = {total}, expected ~100"


def test_cancel_reasons_occurrences_positive(client):
    for row in client.get("/api/cancel_reasons").get_json():
        assert row["occurrences"] > 0


# ── /api/scheduling_gaps ─────────────────────────────────────────────────────

def test_scheduling_gaps_returns_200(client):
    assert client.get("/api/scheduling_gaps").status_code == 200


def test_scheduling_gaps_is_list(client):
    data = client.get("/api/scheduling_gaps").get_json()
    assert isinstance(data, list) and len(data) > 0


def test_scheduling_gaps_required_fields(client):
    row = client.get("/api/scheduling_gaps").get_json()[0]
    for field in ("job_date", "scheduled_jobs", "completed_jobs",
                  "cancelled_jobs", "daily_revenue",
                  "rolling_7day_avg_completed"):
        assert field in row, f"Missing field: {field}"


def test_scheduling_gaps_completed_lte_scheduled(client):
    for row in client.get("/api/scheduling_gaps").get_json():
        assert row["completed_jobs"] <= row["scheduled_jobs"]


def test_scheduling_gaps_dates_ordered(client):
    data = client.get("/api/scheduling_gaps").get_json()
    dates = [r["job_date"] for r in data]
    assert dates == sorted(dates), "dates not in ascending order"


# ── index page ───────────────────────────────────────────────────────────────

def test_index_returns_200(client):
    assert client.get("/").status_code == 200


def test_index_contains_d3(client):
    html = client.get("/").data.decode()
    assert "d3" in html.lower()
