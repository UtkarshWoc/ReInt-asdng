"""Integration tests for all FastAPI REST endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_meta_endpoint():
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert "available_dates" in data
    assert len(data["available_dates"]) > 0
    assert data["default_cutoff"] == "09:00"
    assert "total_forecast_rows" in data
    assert "total_actual_rows" in data


def test_forecast_at_decision_endpoint():
    response = client.get("/api/forecast/at-decision?delivery_date=2026-01-05&cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "periods" in data
    assert len(data["periods"]) == 24
    assert data["kpis"]["delivery_date"] == "2026-01-05"
    assert data["kpis"]["cutoff_time"] == "09:00"
    assert data["kpis"]["total_expected_mwh"] > 0
    # First period check
    first = data["periods"][0]
    assert first["target_time"] == "2026-01-05T00:00:00Z"
    assert first["forecast_mw"] is not None
    assert first["publish_time"] <= "2026-01-04T09:00:00Z"


def test_forecast_at_decision_invalid_date():
    response = client.get("/api/forecast/at-decision?delivery_date=not-a-date&cutoff=09:00")
    assert response.status_code == 400


def test_forecast_revisions_endpoint():
    response = client.get("/api/forecast/revisions?target_time=2026-01-05T12:00:00Z&cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert "revisions" in data
    assert len(data["revisions"]) > 0
    for rev in data["revisions"]:
        assert "publish_time" in rev
        assert "generation_mw" in rev
        assert "is_at_or_before_cutoff" in rev


def test_accuracy_summary_endpoint():
    response = client.get("/api/accuracy/summary?cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert data["sample_count"] > 0
    assert "mae_mw" in data
    assert "rmse_mw" in data
    assert "bias_mw" in data
    assert "histogram" in data
    assert len(data["histogram"]) > 0


def test_accuracy_by_horizon_endpoint():
    response = client.get("/api/accuracy/by-horizon?cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert "horizon_bin" in item
        assert "mae_mw" in item


def test_accuracy_by_hour_endpoint():
    response = client.get("/api/accuracy/by-hour?cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 24
    assert data[0]["hour"] == 0
    assert data[-1]["hour"] == 23


def test_accuracy_timeseries_endpoint():
    response = client.get("/api/accuracy/timeseries?cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for day in data:
        assert "delivery_date" in day
        assert "mae_mw" in day


def test_accuracy_risk_buffer_endpoint():
    response = client.get("/api/accuracy/risk-buffer?delivery_date=2026-01-05&quantile=0.90&cutoff=09:00")
    assert response.status_code == 200
    data = response.json()
    assert data["delivery_date"] == "2026-01-05"
    assert data["quantile"] == 0.90
    assert data["empirical_buffer_mw"] > 0
    assert len(data["periods"]) == 24
    assert "explanation" in data
