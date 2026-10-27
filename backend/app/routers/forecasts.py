"""Forecast at decision time and revisions API router."""

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.core.time_utils import get_decision_cutoff_utc, parse_iso_utc
from app.repositories.data_store import get_data_store
from app.schemas import (
    ForecastAtDecisionResponse,
    ForecastRevisionsResponse,
)
from app.services.forecast_selection import (
    get_forecast_at_decision,
    get_forecast_revisions,
)

router = APIRouter(prefix="/forecast", tags=["forecasts"])


@router.get("/at-decision", response_model=ForecastAtDecisionResponse)
def get_forecast_at_decision_endpoint(
    delivery_date: str = Query(..., description="Delivery date in YYYY-MM-DD format"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> ForecastAtDecisionResponse:
    """
    Retrieve the latest available wind forecast for each target hour of the delivery day
    published prior to the D-1 decision cutoff (strictly preventing look-ahead leakage).
    """
    try:
        d_obj = date.fromisoformat(delivery_date)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format '{delivery_date}'. Expected YYYY-MM-DD.")

    ds = get_data_store()
    if d_obj.isoformat() not in ds.available_delivery_dates:
        # If date not in range, still compute or inform
        pass

    try:
        return get_forecast_at_decision(d_obj, cutoff_str=cutoff, store=ds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute decision forecast: {e}")


@router.get("/revisions", response_model=ForecastRevisionsResponse)
def get_forecast_revisions_endpoint(
    target_time: str = Query(..., description="Target hour in ISO-8601 UTC (e.g., 2026-01-05T12:00:00Z)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> ForecastRevisionsResponse:
    """Retrieve full evolution of forecasts for a specific target hour across all publication times."""
    try:
        target_dt = parse_iso_utc(target_time)
        delivery_date = target_dt.date()
        cutoff_utc = get_decision_cutoff_utc(delivery_date, cutoff)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid target_time or cutoff parameters: {e}")

    ds = get_data_store()
    return get_forecast_revisions(target_time, cutoff_utc, store=ds)
