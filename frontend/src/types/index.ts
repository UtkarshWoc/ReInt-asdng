export interface MetaResponse {
  available_dates: string[];
  default_cutoff: string;
  data_freshness: string;
  total_forecast_rows: number;
  total_actual_rows: number;
  date_range_start: string;
  date_range_end: string;
}

export interface ForecastPeriod {
  target_time: string;
  target_time_london: string;
  forecast_mw: number | null;
  publish_time: string | null;
  horizon_hours: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  settlement_period: number | null;
}

export interface DecisionKPIs {
  delivery_date: string;
  cutoff_time: string;
  cutoff_utc: string;
  total_expected_mwh: number;
  peak_forecast_mw: number;
  min_forecast_mw: number;
  earliest_publish_time: string | null;
  latest_publish_time: string | null;
  missing_periods_count: number;
  actual_total_mwh: number | null;
  mae_mw: number | null;
}

export interface ForecastAtDecisionResponse {
  kpis: DecisionKPIs;
  periods: ForecastPeriod[];
}

export interface RevisionPoint {
  publish_time: string;
  generation_mw: number;
  horizon_hours: number;
  is_at_or_before_cutoff: boolean;
}

export interface ForecastRevisionsResponse {
  target_time: string;
  cutoff_utc: string;
  revisions: RevisionPoint[];
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  bin_mid: number;
  count: number;
  share_percent: number;
}

export interface AccuracySummaryResponse {
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  mape_percent: number | null;
  p50_abs_error_mw: number;
  p90_abs_error_mw: number;
  p95_abs_error_mw: number;
  p99_abs_error_mw: number;
  share_within_500mw: number;
  share_within_1000mw: number;
  share_within_2000mw: number;
  histogram: HistogramBin[];
}

export interface HorizonAccuracyPoint {
  horizon_bin: string;
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  p90_abs_error_mw: number;
}

export interface HourAccuracyPoint {
  hour: number;
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  mean_forecast_mw: number;
  mean_actual_mw: number;
}

export interface DailyAccuracyPoint {
  delivery_date: string;
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  peak_error_mw: number;
}

export interface RiskBufferPeriod {
  target_time: string;
  target_time_london: string;
  forecast_mw: number;
  conservative_wind_mw: number;
  buffer_required_mw: number;
  actual_mw: number | null;
  was_sufficient: boolean | null;
}

export interface RiskBufferResponse {
  delivery_date: string;
  quantile: number;
  cutoff_utc: string;
  empirical_buffer_mw: number;
  total_buffer_mwh: number;
  explanation: string;
  periods: RiskBufferPeriod[];
}
