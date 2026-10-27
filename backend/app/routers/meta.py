"""Metadata API router."""

from fastapi import APIRouter

from app.core.config import settings
from app.repositories.data_store import get_data_store
from app.schemas import MetaResponse

router = APIRouter(tags=["metadata"])


@router.get("/meta", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    """Return dataset metadata, available delivery dates, and system defaults."""
    ds = get_data_store()
    meta = ds.metadata
    dates = ds.available_delivery_dates

    return MetaResponse(
        available_dates=dates,
        default_cutoff=settings.DEFAULT_CUTOFF,
        data_freshness=meta.get("generated_at", ""),
        total_forecast_rows=meta.get("total_forecasts", 0),
        total_actual_rows=meta.get("total_actuals_hourly", 0),
        date_range_start=dates[0] if dates else "2026-01-01",
        date_range_end=dates[-1] if dates else "2026-02-01",
    )
