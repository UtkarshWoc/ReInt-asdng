from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="0.1.0", description="Backend service version")
    timestamp: str = Field(description="Current server timestamp in UTC")


class MetaResponse(BaseModel):
    available_dates: list[str] = Field(description="List of available delivery dates (YYYY-MM-DD)")
    default_cutoff: str = Field(default="09:00", description="Default decision cutoff in Europe/London time")
    data_freshness: str = Field(description="Timestamp of the newest record in snapshot")
    total_forecast_rows: int = Field(description="Total forecast records in snapshot")
    total_actual_rows: int = Field(description="Total actual generation records in snapshot")
    date_range_start: str = Field(description="Earliest delivery date available")
    date_range_end: str = Field(description="Latest delivery date available")


class ForecastPeriod(BaseModel):
    target_time: str = Field(description="Target period start time in UTC (ISO-8601)")
    target_time_london: str = Field(description="Target period in Europe/London local time")
    forecast_mw: float | None = Field(None, description="Latest forecast available at cutoff (MW)")
    publish_time: str | None = Field(None, description="Publication timestamp of the selected forecast in UTC")
    horizon_hours: float | None = Field(None, description="Forecast horizon in hours (target_time - publish_time)")
    actual_mw: float | None = Field(None, description="Actual generation (hindsight outturn, MW)")
    error_mw: float | None = Field(None, description="Forecast error in MW (forecast - actual)")
    settlement_period: int | None = Field(None, description="Elexon settlement period index (1-48)")


class DecisionKPIs(BaseModel):
    delivery_date: str = Field(description="Target delivery date (YYYY-MM-DD)")
    cutoff_time: str = Field(description="Cutoff time in London time")
    cutoff_utc: str = Field(description="Cutoff timestamp converted to UTC")
    total_expected_mwh: float = Field(description="Total expected wind energy across the delivery day (MWh)")
    peak_forecast_mw: float = Field(description="Peak expected forecast power (MW)")
    min_forecast_mw: float = Field(description="Minimum expected forecast power (MW)")
    earliest_publish_time: str | None = Field(None, description="Earliest publishTime feeding this decision view")
    latest_publish_time: str | None = Field(None, description="Latest publishTime feeding this decision view")
    missing_periods_count: int = Field(description="Number of delivery periods missing a forecast prior to cutoff")
    actual_total_mwh: float | None = Field(None, description="Total hindsight actual wind generation (MWh)")
    mae_mw: float | None = Field(None, description="Mean absolute error for this delivery day (MW)")


class ForecastAtDecisionResponse(BaseModel):
    kpis: DecisionKPIs
    periods: list[ForecastPeriod]


class RevisionPoint(BaseModel):
    publish_time: str = Field(description="Publication timestamp in UTC")
    generation_mw: float = Field(description="Forecasted generation (MW)")
    horizon_hours: float = Field(description="Forecast horizon hours (target - publish)")
    is_at_or_before_cutoff: bool = Field(description="Whether this forecast was available at or before cutoff")


class ForecastRevisionsResponse(BaseModel):
    target_time: str = Field(description="Target period start time in UTC")
    cutoff_utc: str = Field(description="Decision cutoff timestamp in UTC")
    revisions: list[RevisionPoint] = Field(description="Evolution of forecasts for this target period")
