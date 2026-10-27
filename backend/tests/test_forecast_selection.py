"""Thorough tests for forecast selection engine enforcing leak-free cutoff logic."""

from datetime import UTC, date, datetime

from app.core.time_utils import get_decision_cutoff_utc
from app.repositories.data_store import DataStore
from app.services.forecast_selection import (
    compute_horizon_hours,
    get_forecast_at_decision,
    get_forecast_revisions,
    select_latest_forecast_at_cutoff,
)


def test_select_latest_forecast_at_cutoff_basic():
    """Verify that the latest forecast published at or before cutoff is selected."""
    cutoff = datetime(2026, 1, 4, 9, 0, 0, tzinfo=UTC)
    candidates = [
        {"publishTime": "2026-01-04T04:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 10000},
        {"publishTime": "2026-01-04T07:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 11000},
        {"publishTime": "2026-01-04T11:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 12000},
    ]

    selected = select_latest_forecast_at_cutoff(candidates, cutoff)
    assert selected is not None
    # Must select 07:30 (latest before 09:00 cutoff)
    assert selected["publishTime"] == "2026-01-04T07:30:00Z"
    assert selected["generation"] == 11000


def test_no_lookahead_leakage():
    """Verify that ANY forecast published after cutoff is strictly excluded."""
    cutoff = datetime(2026, 1, 4, 9, 0, 0, tzinfo=UTC)
    # Only forecasts after cutoff
    candidates = [
        {"publishTime": "2026-01-04T09:00:01Z", "startTime": "2026-01-05T00:00:00Z", "generation": 15000},
        {"publishTime": "2026-01-04T10:00:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 16000},
    ]
    selected = select_latest_forecast_at_cutoff(candidates, cutoff)
    assert selected is None, "Look-ahead leakage! A forecast published after cutoff was selected."


def test_exact_cutoff_boundary():
    """A forecast published exactly at the cutoff (boundary moment) MUST be considered eligible."""
    cutoff = datetime(2026, 1, 4, 9, 0, 0, tzinfo=UTC)
    candidates = [
        {"publishTime": "2026-01-04T07:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 9000},
        {"publishTime": "2026-01-04T09:00:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 9500},
        {"publishTime": "2026-01-04T09:00:01Z", "startTime": "2026-01-05T00:00:00Z", "generation": 9999},
    ]
    selected = select_latest_forecast_at_cutoff(candidates, cutoff)
    assert selected is not None
    assert selected["publishTime"] == "2026-01-04T09:00:00Z"
    assert selected["generation"] == 9500


def test_duplicate_publish_times():
    """Handle deterministic selection when multiple forecasts share the latest publishTime."""
    cutoff = datetime(2026, 1, 4, 9, 0, 0, tzinfo=UTC)
    candidates = [
        {"publishTime": "2026-01-04T07:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 10000},
        {"publishTime": "2026-01-04T07:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 10500},
    ]
    selected = select_latest_forecast_at_cutoff(candidates, cutoff)
    assert selected is not None
    assert selected["publishTime"] == "2026-01-04T07:30:00Z"
    assert selected["generation"] in (10000, 10500)


def test_dst_safety():
    """
    Test DST transitions:
    - January (GMT): 09:00 London is 09:00:00 UTC.
    - July (BST): 09:00 London is 08:00:00 UTC.
    """
    # 1. Winter delivery day: 2026-01-15 (D-1 is 2026-01-14)
    cutoff_winter = get_decision_cutoff_utc(date(2026, 1, 15), "09:00")
    assert cutoff_winter == datetime(2026, 1, 14, 9, 0, 0, tzinfo=UTC)

    # 2. Summer delivery day: 2026-07-15 (D-1 is 2026-07-14)
    cutoff_summer = get_decision_cutoff_utc(date(2026, 7, 15), "09:00")
    # In BST (UTC+1), 09:00 BST is 08:00 UTC
    assert cutoff_summer == datetime(2026, 7, 14, 8, 0, 0, tzinfo=UTC)

    # 3. DST transition day (late March 2026)
    # UK clocks go forward on Sunday 29 March 2026 at 01:00 UTC -> 02:00 BST
    cutoff_bst_start = get_decision_cutoff_utc(date(2026, 3, 31), "09:00")
    assert cutoff_bst_start == datetime(2026, 3, 30, 8, 0, 0, tzinfo=UTC)


def test_horizon_calculation():
    """Verify horizon calculation: target_time - publish_time."""
    # Target 2026-01-05 12:00 UTC, published 2026-01-04 07:30 UTC
    # Difference: 28.5 hours
    h = compute_horizon_hours("2026-01-05T12:00:00Z", "2026-01-04T07:30:00Z")
    assert h == 28.5


def test_get_forecast_at_decision_complete_day():
    """Test full 24-hour day-ahead evaluation with KPIs, error calculation, and missing period."""
    target_date = date(2026, 1, 5)
    mock_store_data = {
        "metadata": {"available_delivery_dates": ["2026-01-05"]},
        "actuals_hourly": [
            {"startTime": f"2026-01-05T{h:02d}:00:00Z", "generation": 10000.0}
            for h in range(24)
        ],
        "actuals_half_hourly": [],
        "forecasts": [
            # 23 hours have a forecast before cutoff
            *[
                {
                    "publishTime": "2026-01-04T07:30:00Z",
                    "startTime": f"2026-01-05T{h:02d}:00:00Z",
                    "generation": 11000.0,
                }
                for h in range(23)
            ],
            # Hour 23 only has a forecast published AFTER cutoff
            {
                "publishTime": "2026-01-04T11:30:00Z",
                "startTime": "2026-01-05T23:00:00Z",
                "generation": 14000.0,
            },
        ],
    }
    store = DataStore(mock_store_data)
    resp = get_forecast_at_decision(target_date, cutoff_str="09:00", store=store)

    assert len(resp.periods) == 24
    assert resp.kpis.missing_periods_count == 1
    assert resp.kpis.earliest_publish_time == "2026-01-04T07:30:00Z"
    assert resp.kpis.latest_publish_time == "2026-01-04T07:30:00Z"

    # Periods 0 to 22: forecast 11000, actual 10000 -> error +1000 (over-forecast)
    for p in resp.periods[:23]:
        assert p.forecast_mw == 11000.0
        assert p.actual_mw == 10000.0
        assert p.error_mw == 1000.0

    # Period 23: must be missing (None), NO look-ahead leakage
    assert resp.periods[23].forecast_mw is None
    assert resp.periods[23].error_mw is None
    assert resp.periods[23].actual_mw == 10000.0


def test_forecast_revisions():
    """Verify revision history retrieves all candidate forecasts with eligibility flags."""
    cutoff = datetime(2026, 1, 4, 9, 0, 0, tzinfo=UTC)
    mock_store_data = {
        "metadata": {},
        "actuals_hourly": [],
        "actuals_half_hourly": [],
        "forecasts": [
            {"publishTime": "2026-01-03T14:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 10500.0},
            {"publishTime": "2026-01-04T07:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 11000.0},
            {"publishTime": "2026-01-04T14:30:00Z", "startTime": "2026-01-05T00:00:00Z", "generation": 12000.0},
        ],
    }
    store = DataStore(mock_store_data)
    rev_resp = get_forecast_revisions("2026-01-05T00:00:00Z", cutoff, store=store)

    assert len(rev_resp.revisions) == 3
    # First two are eligible at cutoff
    assert rev_resp.revisions[0].is_at_or_before_cutoff is True
    assert rev_resp.revisions[1].is_at_or_before_cutoff is True
    # Third was published after cutoff (14:30 > 09:00)
    assert rev_resp.revisions[2].is_at_or_before_cutoff is False
    assert rev_resp.revisions[2].generation_mw == 12000.0
