"""Tests for error metrics, quantiles, and empirical risk buffer calculations."""

from datetime import date

from app.repositories.data_store import DataStore
from app.services.metrics import (
    MetricsService,
    calculate_percentile,
    compute_error_metrics,
)


def test_error_sign_convention():
    """Verify error sign convention: error = forecast - actual (positive = over-forecast)."""
    # Over-forecast: forecast 12000, actual 10000 -> error +2000
    pairs = [(12000.0, 10000.0)]
    summary = compute_error_metrics(pairs)
    assert summary.bias_mw == 2000.0
    assert summary.mae_mw == 2000.0
    assert summary.rmse_mw == 2000.0

    # Under-forecast: forecast 8000, actual 10000 -> error -2000
    pairs_under = [(8000.0, 10000.0)]
    summary_under = compute_error_metrics(pairs_under)
    assert summary_under.bias_mw == -2000.0
    assert summary_under.mae_mw == 2000.0
    assert summary_under.rmse_mw == 2000.0


def test_percentile_calculation():
    """Verify empirical percentile interpolation."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    p50 = calculate_percentile(values, 0.50)
    assert p50 == 30.0

    p90 = calculate_percentile(values, 0.90)
    # k = 4 * 0.9 = 3.6 -> 40 + 0.6*(50-40) = 46.0
    assert p90 == 46.0


def test_safe_mape_near_zero():
    """Verify that MAPE ignores near-zero actuals (<100 MW) to avoid division explosions."""
    pairs = [
        (1100.0, 1000.0),  # 10% error
        (200.0, 10.0),     # near-zero actual, should be excluded from safe MAPE
    ]
    summary = compute_error_metrics(pairs)
    assert summary.mape_percent == 10.0


def test_error_tolerance_shares():
    """Verify share of periods within +/- 500, 1000, 2000 MW."""
    pairs = [
        (10200.0, 10000.0),  # error +200 (within 500)
        (10800.0, 10000.0),  # error +800 (within 1000)
        (11500.0, 10000.0),  # error +1500 (within 2000)
        (13000.0, 10000.0),  # error +3000 (outside 2000)
    ]
    summary = compute_error_metrics(pairs)
    assert summary.sample_count == 4
    assert summary.share_within_500mw == 25.0
    assert summary.share_within_1000mw == 50.0
    assert summary.share_within_2000mw == 75.0


def test_risk_buffer_calculation():
    """Verify empirical risk buffer sizing and conservative wind calculation."""
    mock_data = {
        "metadata": {"available_delivery_dates": ["2026-01-05"]},
        "actuals_hourly": [
            {"startTime": f"2026-01-05T{h:02d}:00:00Z", "generation": 10000.0}
            for h in range(24)
        ],
        "actuals_half_hourly": [],
        "forecasts": [
            # Forecast is 12000 MW -> over-forecast error +2000 MW
            {
                "publishTime": "2026-01-04T07:30:00Z",
                "startTime": f"2026-01-05T{h:02d}:00:00Z",
                "generation": 12000.0,
            }
            for h in range(24)
        ],
    }
    store = DataStore(mock_data)
    svc = MetricsService(store=store)

    rb = svc.get_risk_buffer(date(2026, 1, 5), quantile=0.90, cutoff_str="09:00")
    assert rb.empirical_buffer_mw == 2000.0
    assert len(rb.periods) == 24
    for p in rb.periods:
        assert p.forecast_mw == 12000.0
        assert p.conservative_wind_mw == 10000.0
        assert p.buffer_required_mw == 2000.0
        assert p.was_sufficient is True
