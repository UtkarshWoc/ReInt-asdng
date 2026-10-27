"""Forecast selection engine enforcing leak-free gate closure cutoffs."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.core.time_utils import (
    format_iso_utc,
    get_decision_cutoff_utc,
    parse_iso_utc,
    to_london_display,
)
from app.repositories.data_store import DataStore, get_data_store
from app.schemas import (
    DecisionKPIs,
    ForecastAtDecisionResponse,
    ForecastPeriod,
    ForecastRevisionsResponse,
    RevisionPoint,
)


def select_latest_forecast_at_cutoff(
    forecasts: List[Dict[str, Any]],
    cutoff_utc: datetime,
) -> Optional[Dict[str, Any]]:
    """
    Select the single latest forecast published at or before cutoff_utc.

    Rules:
    - Only consider forecasts where publishTime <= cutoff_utc.
    - Never include forecasts where publishTime > cutoff_utc (strictly prevents look-ahead leakage).
    - If multiple forecasts share the latest publishTime, select deterministically (last item).
    - If no forecast was published at or before cutoff, return None.
    """
    cutoff_iso = format_iso_utc(cutoff_utc)

    # Filter to eligible forecasts published at or before the cutoff
    eligible = [fc for fc in forecasts if fc.get("publishTime") and fc["publishTime"] <= cutoff_iso]

    if not eligible:
        return None

    # Return the forecast with the greatest publishTime
    eligible.sort(key=lambda x: x["publishTime"])
    return eligible[-1]


def compute_horizon_hours(target_time_iso: str, publish_time_iso: str) -> float:
    """Calculate the forecast lead-time (horizon) in hours: target_time - publish_time."""
    target_dt = parse_iso_utc(target_time_iso)
    publish_dt = parse_iso_utc(publish_time_iso)
    delta_seconds = (target_dt - publish_dt).total_seconds()
    return round(delta_seconds / 3600.0, 2)


def get_forecast_at_decision(
    delivery_date: date,
    cutoff_str: str = "09:00",
    store: Optional[DataStore] = None,
) -> ForecastAtDecisionResponse:
    """
    Build the complete decision-time forecast view for all 24 hours of delivery day D.

    Evaluates the cutoff at D-1 09:00 Europe/London (converted safely to UTC).
    """
    ds = store or get_data_store()
    cutoff_utc = get_decision_cutoff_utc(delivery_date, cutoff_str)
    cutoff_iso = format_iso_utc(cutoff_utc)
    date_str = delivery_date.isoformat()

    periods: List[ForecastPeriod] = []
    selected_pub_times: List[str] = []
    forecast_values: List[float] = []
    actual_values: List[float] = []
    abs_errors: List[float] = []
    missing_count = 0

    # 24 hourly periods (00:00 to 23:00 UTC)
    target_times = ds.get_target_times_for_date(date_str)

    for hour_idx, target_time in enumerate(target_times):
        target_dt = parse_iso_utc(target_time)
        target_london = to_london_display(target_dt)

        # Retrieve all candidate forecasts for this target hour
        candidates = ds.get_forecasts_for_target(target_time)
        selected = select_latest_forecast_at_cutoff(candidates, cutoff_utc)

        actual_mw = ds.get_actual_hourly(target_time)

        if selected is not None:
            fc_mw = float(selected["generation"])
            pub_time = selected["publishTime"]
            horizon = compute_horizon_hours(target_time, pub_time)
            error_mw = round(fc_mw - actual_mw, 2) if actual_mw is not None else None

            selected_pub_times.append(pub_time)
            forecast_values.append(fc_mw)
            if actual_mw is not None:
                actual_values.append(actual_mw)
                abs_errors.append(abs(fc_mw - actual_mw))

            periods.append(
                ForecastPeriod(
                    target_time=target_time,
                    target_time_london=target_london,
                    forecast_mw=fc_mw,
                    publish_time=pub_time,
                    horizon_hours=horizon,
                    actual_mw=actual_mw,
                    error_mw=error_mw,
                    settlement_period=hour_idx * 2 + 1,
                )
            )
        else:
            missing_count += 1
            if actual_mw is not None:
                actual_values.append(actual_mw)

            periods.append(
                ForecastPeriod(
                    target_time=target_time,
                    target_time_london=target_london,
                    forecast_mw=None,
                    publish_time=None,
                    horizon_hours=None,
                    actual_mw=actual_mw,
                    error_mw=None,
                    settlement_period=hour_idx * 2 + 1,
                )
            )

    # Compute Day-Ahead KPIs
    total_expected_mwh = sum(forecast_values) if forecast_values else 0.0
    peak_forecast_mw = max(forecast_values) if forecast_values else 0.0
    min_forecast_mw = min(forecast_values) if forecast_values else 0.0
    earliest_pub = min(selected_pub_times) if selected_pub_times else None
    latest_pub = max(selected_pub_times) if selected_pub_times else None
    actual_total_mwh = sum(actual_values) if actual_values else None
    mae_mw = round(sum(abs_errors) / len(abs_errors), 2) if abs_errors else None

    kpis = DecisionKPIs(
        delivery_date=date_str,
        cutoff_time=cutoff_str,
        cutoff_utc=cutoff_iso,
        total_expected_mwh=round(total_expected_mwh, 2),
        peak_forecast_mw=round(peak_forecast_mw, 2),
        min_forecast_mw=round(min_forecast_mw, 2),
        earliest_publish_time=earliest_pub,
        latest_publish_time=latest_pub,
        missing_periods_count=missing_count,
        actual_total_mwh=round(actual_total_mwh, 2) if actual_total_mwh is not None else None,
        mae_mw=mae_mw,
    )

    return ForecastAtDecisionResponse(kpis=kpis, periods=periods)


def get_forecast_revisions(
    target_time: str,
    cutoff_utc: datetime,
    store: Optional[DataStore] = None,
) -> ForecastRevisionsResponse:
    """Retrieve all revisions published for a specific target time, marked by cutoff eligibility."""
    ds = store or get_data_store()
    cutoff_iso = format_iso_utc(cutoff_utc)

    all_forecasts = ds.get_forecasts_for_target(target_time)
    revisions: List[RevisionPoint] = []

    for fc in all_forecasts:
        pub_iso = fc["publishTime"]
        gen_mw = float(fc["generation"])
        horizon = compute_horizon_hours(target_time, pub_iso)
        is_eligible = pub_iso <= cutoff_iso

        revisions.append(
            RevisionPoint(
                publish_time=pub_iso,
                generation_mw=gen_mw,
                horizon_hours=horizon,
                is_at_or_before_cutoff=is_eligible,
            )
        )

    # Sort chronologically by publish_time
    revisions.sort(key=lambda x: x.publish_time)

    return ForecastRevisionsResponse(
        target_time=target_time,
        cutoff_utc=cutoff_iso,
        revisions=revisions,
    )
