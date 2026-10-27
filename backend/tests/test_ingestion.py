"""Tests for Elexon ingestion service and DataStore repository."""

from app.repositories.data_store import DataStore
from app.services.ingestion import IngestionService


def test_clean_fuelhh_record():
    valid_raw = {
        "startTime": "2026-01-01T00:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": 13756,
    }
    cleaned = IngestionService.clean_fuelhh_record(valid_raw)
    assert cleaned is not None
    assert cleaned["startTime"] == "2026-01-01T00:00:00Z"
    assert cleaned["settlementPeriod"] == 1
    assert cleaned["generation"] == 13756.0

    # Negative generation rejected
    negative_raw = {**valid_raw, "generation": -100}
    assert IngestionService.clean_fuelhh_record(negative_raw) is None

    # Missing fields rejected
    assert IngestionService.clean_fuelhh_record({}) is None


def test_clean_windfor_record():
    valid_raw = {
        "publishTime": "2026-01-01T02:30:00Z",
        "startTime": "2026-01-01T05:00:00Z",
        "generation": 19636,
    }
    cleaned = IngestionService.clean_windfor_record(valid_raw)
    assert cleaned is not None
    assert cleaned["publishTime"] == "2026-01-01T02:30:00Z"
    assert cleaned["startTime"] == "2026-01-01T05:00:00Z"
    assert cleaned["generation"] == 19636.0

    # Negative generation rejected
    negative_raw = {**valid_raw, "generation": -50}
    assert IngestionService.clean_windfor_record(negative_raw) is None


def test_aggregate_hourly_actuals():
    half_hourly = [
        {"startTime": "2026-01-01T00:00:00Z", "generation": 10000.0, "settlementPeriod": 1},
        {"startTime": "2026-01-01T00:30:00Z", "generation": 12000.0, "settlementPeriod": 2},
        {"startTime": "2026-01-01T01:00:00Z", "generation": 15000.0, "settlementPeriod": 3},
        {"startTime": "2026-01-01T01:30:00Z", "generation": 15000.0, "settlementPeriod": 4},
    ]
    hourly = IngestionService.aggregate_hourly_actuals(half_hourly)
    assert len(hourly) == 2

    # Hour 00:00:00Z mean of 10000 and 12000 = 11000
    assert hourly[0]["startTime"] == "2026-01-01T00:00:00Z"
    assert hourly[0]["generation"] == 11000.0
    assert hourly[0]["period_00"] == 10000.0
    assert hourly[0]["period_30"] == 12000.0
    assert hourly[0]["half_hour_samples"] == 2

    # Hour 01:00:00Z mean of 15000 and 15000 = 15000
    assert hourly[1]["startTime"] == "2026-01-01T01:00:00Z"
    assert hourly[1]["generation"] == 15000.0


def test_datastore_indexing_and_lookups():
    sample_data = {
        "metadata": {
            "total_forecasts": 2,
            "total_actuals_hourly": 1,
            "available_delivery_dates": ["2026-01-01"],
        },
        "actuals_hourly": [
            {"startTime": "2026-01-01T00:00:00Z", "generation": 12500.0}
        ],
        "actuals_half_hourly": [
            {"startTime": "2026-01-01T00:00:00Z", "settlementDate": "2026-01-01", "settlementPeriod": 1, "generation": 12000.0},
            {"startTime": "2026-01-01T00:30:00Z", "settlementDate": "2026-01-01", "settlementPeriod": 2, "generation": 13000.0},
        ],
        "forecasts": [
            {"publishTime": "2025-12-31T05:00:00Z", "startTime": "2026-01-01T00:00:00Z", "generation": 11000.0},
            {"publishTime": "2025-12-31T07:30:00Z", "startTime": "2026-01-01T00:00:00Z", "generation": 11500.0},
        ],
    }
    store = DataStore(sample_data)
    assert store.get_actual_hourly("2026-01-01T00:00:00Z") == 12500.0
    assert store.available_delivery_dates == ["2026-01-01"]

    fc_list = store.get_forecasts_for_target("2026-01-01T00:00:00Z")
    assert len(fc_list) == 2
    # Ensure sorted by publishTime
    assert fc_list[0]["publishTime"] == "2025-12-31T05:00:00Z"
    assert fc_list[1]["publishTime"] == "2025-12-31T07:30:00Z"
