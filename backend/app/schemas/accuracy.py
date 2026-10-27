"""Pydantic schemas for accuracy and risk-buffer endpoints."""


from pydantic import BaseModel, Field


class AccuracySummaryResponse(BaseModel):
    sample_count: int = Field(description="Number of evaluated hourly forecast-actual pairs")
    mae_mw: float = Field(description="Mean Absolute Error (MW)")
    rmse_mw: float = Field(description="Root Mean Square Error (MW)")
    bias_mw: float = Field(description="Mean Bias Error (MW, forecast - actual)")
    mape_percent: float | None = Field(None, description="Mean Absolute Percentage Error (%)")
    p50_abs_error_mw: float = Field(description="50th percentile of absolute error (MW)")
    p90_abs_error_mw: float = Field(description="90th percentile of absolute error (MW)")
    p95_abs_error_mw: float = Field(description="95th percentile of absolute error (MW)")
    p99_abs_error_mw: float = Field(description="99th percentile of absolute error (MW)")
    share_within_500mw: float = Field(description="Percentage of periods with error within +/- 500 MW")
    share_within_1000mw: float = Field(description="Percentage of periods with error within +/- 1000 MW")
    share_within_2000mw: float = Field(description="Percentage of periods with error within +/- 2000 MW")
    histogram: list[dict[str, float]] = Field(description="Binned error distribution counts")


class HorizonAccuracyPoint(BaseModel):
    horizon_bin: str = Field(description="Horizon bracket (e.g., '12-18h', '18-24h')")
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    p90_abs_error_mw: float


class HourAccuracyPoint(BaseModel):
    hour: int = Field(description="Hour of day (0-23 in Europe/London)")
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    mean_forecast_mw: float
    mean_actual_mw: float


class DailyAccuracyPoint(BaseModel):
    delivery_date: str = Field(description="Delivery date (YYYY-MM-DD)")
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    peak_error_mw: float


class RiskBufferPeriod(BaseModel):
    target_time: str
    target_time_london: str
    forecast_mw: float
    conservative_wind_mw: float
    buffer_required_mw: float
    actual_mw: float | None = None
    was_sufficient: bool | None = None


class RiskBufferResponse(BaseModel):
    delivery_date: str
    quantile: float = Field(description="Target empirical confidence level (e.g. 0.90 for P90)")
    cutoff_utc: str
    empirical_buffer_mw: float = Field(description="Empirical over-forecast buffer size (MW)")
    total_buffer_mwh: float = Field(description="Total additional energy buffer required across the day (MWh)")
    explanation: str = Field(description="Plain-English explanation of the buffer calculation")
    periods: list[RiskBufferPeriod]
