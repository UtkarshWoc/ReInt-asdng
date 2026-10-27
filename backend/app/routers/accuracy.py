"""Accuracy analysis and empirical risk buffer API router."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories.data_store import get_data_store
from app.schemas.accuracy import (
    AccuracySummaryResponse,
    DailyAccuracyPoint,
    HorizonAccuracyPoint,
    HourAccuracyPoint,
    RiskBufferResponse,
)
from app.services.metrics import MetricsService

router = APIRouter(prefix="/accuracy", tags=["accuracy"])


@router.get("/summary", response_model=AccuracySummaryResponse)
def get_accuracy_summary_endpoint(
    start: Optional[str] = Query(None, description="Start delivery date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> AccuracySummaryResponse:
    """Retrieve aggregate forecast accuracy metrics and error histogram across a date range."""
    svc = MetricsService(store=get_data_store())
    return svc.get_accuracy_summary(start_date=start, end_date=end, cutoff_str=cutoff)


@router.get("/by-horizon", response_model=List[HorizonAccuracyPoint])
def get_accuracy_by_horizon_endpoint(
    start: Optional[str] = Query(None, description="Start delivery date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> List[HorizonAccuracyPoint]:
    """Retrieve error metrics grouped by forecast lead time (horizon brackets)."""
    svc = MetricsService(store=get_data_store())
    return svc.get_accuracy_by_horizon(start_date=start, end_date=end, cutoff_str=cutoff)


@router.get("/by-hour", response_model=List[HourAccuracyPoint])
def get_accuracy_by_hour_endpoint(
    start: Optional[str] = Query(None, description="Start delivery date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> List[HourAccuracyPoint]:
    """Retrieve error metrics and diurnal patterns grouped by hour of the delivery day."""
    svc = MetricsService(store=get_data_store())
    return svc.get_accuracy_by_hour(start_date=start, end_date=end, cutoff_str=cutoff)


@router.get("/timeseries", response_model=List[DailyAccuracyPoint])
def get_accuracy_timeseries_endpoint(
    start: Optional[str] = Query(None, description="Start delivery date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> List[DailyAccuracyPoint]:
    """Retrieve day-by-day accuracy metrics across January."""
    svc = MetricsService(store=get_data_store())
    return svc.get_daily_timeseries(start_date=start, end_date=end, cutoff_str=cutoff)


@router.get("/risk-buffer", response_model=RiskBufferResponse)
def get_risk_buffer_endpoint(
    delivery_date: str = Query(..., description="Delivery date (YYYY-MM-DD)"),
    quantile: float = Query(0.90, ge=0.50, le=0.99, description="Target confidence quantile (0.50 - 0.99)"),
    cutoff: str = Query("09:00", description="Decision cutoff in Europe/London time (HH:MM)"),
) -> RiskBufferResponse:
    """
    Calculate empirical over-forecast risk buffer and conservative wind scenario
    to support thermal procurement decisions under uncertainty.
    """
    try:
        d_obj = date.fromisoformat(delivery_date)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date format '{delivery_date}'. Expected YYYY-MM-DD.")

    svc = MetricsService(store=get_data_store())
    return svc.get_risk_buffer(delivery_date=d_obj, quantile=quantile, cutoff_str=cutoff)
