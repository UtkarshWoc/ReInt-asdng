"""Error metrics and empirical risk buffer computation engine."""

import math
from datetime import date
from typing import Dict, List, Optional, Tuple

from app.core.time_utils import get_decision_cutoff_utc, parse_iso_utc
from app.repositories.data_store import DataStore, get_data_store
from app.schemas.accuracy import (
    AccuracySummaryResponse,
    DailyAccuracyPoint,
    HorizonAccuracyPoint,
    HourAccuracyPoint,
    RiskBufferPeriod,
    RiskBufferResponse,
)
from app.services.forecast_selection import (
    compute_horizon_hours,
    select_latest_forecast_at_cutoff,
)


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate empirical percentile (0.0 to 1.0) using linear interpolation."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    k = (len(sorted_v) - 1) * percentile
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_v[int(k)]
    d0 = sorted_v[int(f)] * (c - k)
    d1 = sorted_v[int(c)] * (k - f)
    return round(d0 + d1, 2)


def compute_error_metrics(
    pairs: List[Tuple[float, float]],
    bins_count: int = 20,
) -> AccuracySummaryResponse:
    """
    Compute comprehensive error metrics over a collection of (forecast, actual) pairs.

    Error Definition: error = forecast - actual (Positive = Over-forecast).
    """
    if not pairs:
        return AccuracySummaryResponse(
            sample_count=0,
            mae_mw=0.0,
            rmse_mw=0.0,
            bias_mw=0.0,
            mape_percent=None,
            p50_abs_error_mw=0.0,
            p90_abs_error_mw=0.0,
            p95_abs_error_mw=0.0,
            p99_abs_error_mw=0.0,
            share_within_500mw=0.0,
            share_within_1000mw=0.0,
            share_within_2000mw=0.0,
            histogram=[],
        )

    errors = [round(fc - act, 2) for fc, act in pairs]
    abs_errors = [abs(e) for e in errors]
    n = len(errors)

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(e ** 2 for e in errors) / n)
    bias = sum(errors) / n

    # Safe MAPE: exclude actuals < 100 MW to avoid division by near-zero distortion
    mape_samples = [abs(fc - act) / act for fc, act in pairs if act >= 100.0]
    mape = (sum(mape_samples) / len(mape_samples) * 100.0) if mape_samples else None

    # Percentiles of absolute error
    p50 = calculate_percentile(abs_errors, 0.50)
    p90 = calculate_percentile(abs_errors, 0.90)
    p95 = calculate_percentile(abs_errors, 0.95)
    p99 = calculate_percentile(abs_errors, 0.99)

    # Share of periods within tolerance
    within_500 = sum(1 for a in abs_errors if a <= 500.0) / n * 100.0
    within_1000 = sum(1 for a in abs_errors if a <= 1000.0) / n * 100.0
    within_2000 = sum(1 for a in abs_errors if a <= 2000.0) / n * 100.0

    # Error Histogram
    min_err = min(errors)
    max_err = max(errors)
    bin_width = (max_err - min_err) / bins_count if max_err > min_err else 100.0
    histogram: List[Dict[str, float]] = []

    for b in range(bins_count):
        bin_start = min_err + b * bin_width
        bin_end = bin_start + bin_width
        count = sum(1 for e in errors if (bin_start <= e < bin_end or (b == bins_count - 1 and e == bin_end)))
        histogram.append({
            "bin_start": round(bin_start, 1),
            "bin_end": round(bin_end, 1),
            "bin_mid": round((bin_start + bin_end) / 2, 1),
            "count": float(count),
            "share_percent": round(count / n * 100.0, 2),
        })

    return AccuracySummaryResponse(
        sample_count=n,
        mae_mw=round(mae, 2),
        rmse_mw=round(rmse, 2),
        bias_mw=round(bias, 2),
        mape_percent=round(mape, 2) if mape is not None else None,
        p50_abs_error_mw=p50,
        p90_abs_error_mw=p90,
        p95_abs_error_mw=p95,
        p99_abs_error_mw=p99,
        share_within_500mw=round(within_500, 2),
        share_within_1000mw=round(within_1000, 2),
        share_within_2000mw=round(within_2000, 2),
        histogram=histogram,
    )


class MetricsService:
    """Service providing multi-dimensional accuracy analysis and risk buffers."""

    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_data_store()

    def get_evaluated_pairs_for_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cutoff_str: str = "09:00",
    ) -> List[Tuple[float, float, str, float]]:
        """
        Evaluate all decision-time forecasts across a date range.

        Returns list of tuples: (forecast_mw, actual_mw, target_time, horizon_hours).
        """
        all_dates = self.store.available_delivery_dates
        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]

        results: List[Tuple[float, float, str, float]] = []

        for date_str in all_dates:
            d_obj = date.fromisoformat(date_str)
            cutoff_utc = get_decision_cutoff_utc(d_obj, cutoff_str)
            target_times = self.store.get_target_times_for_date(date_str)

            for target_time in target_times:
                actual_mw = self.store.get_actual_hourly(target_time)
                if actual_mw is None:
                    continue

                candidates = self.store.get_forecasts_for_target(target_time)
                selected = select_latest_forecast_at_cutoff(candidates, cutoff_utc)
                if selected is not None:
                    fc_mw = float(selected["generation"])
                    horizon = compute_horizon_hours(target_time, selected["publishTime"])
                    results.append((fc_mw, actual_mw, target_time, horizon))

        return results

    def get_accuracy_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cutoff_str: str = "09:00",
    ) -> AccuracySummaryResponse:
        """Calculate overall accuracy metrics across the specified window."""
        evaluated = self.get_evaluated_pairs_for_range(start_date, end_date, cutoff_str)
        pairs = [(fc, act) for fc, act, _, _ in evaluated]
        return compute_error_metrics(pairs)

    def get_accuracy_by_horizon(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cutoff_str: str = "09:00",
    ) -> List[HorizonAccuracyPoint]:
        """Aggregate accuracy by forecast lead time (horizon brackets)."""
        evaluated = self.get_evaluated_pairs_for_range(start_date, end_date, cutoff_str)

        # Horizon brackets
        bins = [
            ("12-18h", 12.0, 18.0),
            ("18-24h", 18.0, 24.0),
            ("24-30h", 24.0, 30.0),
            ("30-36h", 30.0, 36.0),
            ("36-48h", 36.0, 48.0),
        ]

        results: List[HorizonAccuracyPoint] = []
        for label, h_min, h_max in bins:
            bracket_pairs = [
                (fc, act) for fc, act, _, h in evaluated if (h_min <= h < h_max or (h_max == 48.0 and h >= 36.0))
            ]
            if not bracket_pairs:
                continue

            summary = compute_error_metrics(bracket_pairs)
            results.append(
                HorizonAccuracyPoint(
                    horizon_bin=label,
                    sample_count=summary.sample_count,
                    mae_mw=summary.mae_mw,
                    rmse_mw=summary.rmse_mw,
                    bias_mw=summary.bias_mw,
                    p90_abs_error_mw=summary.p90_abs_error_mw,
                )
            )

        return results

    def get_accuracy_by_hour(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cutoff_str: str = "09:00",
    ) -> List[HourAccuracyPoint]:
        """Aggregate forecast accuracy for each hour of the day (0-23 London time)."""
        evaluated = self.get_evaluated_pairs_for_range(start_date, end_date, cutoff_str)

        by_hour: Dict[int, List[Tuple[float, float]]] = {h: [] for h in range(24)}
        for fc, act, target_time, _ in evaluated:
            dt_utc = parse_iso_utc(target_time)
            # In January, UTC hour == London hour
            hour = dt_utc.hour
            by_hour[hour].append((fc, act))

        results: List[HourAccuracyPoint] = []
        for h in range(24):
            pairs = by_hour[h]
            if not pairs:
                continue
            summary = compute_error_metrics(pairs)
            mean_fc = sum(fc for fc, _ in pairs) / len(pairs)
            mean_act = sum(act for _, act in pairs) / len(pairs)

            results.append(
                HourAccuracyPoint(
                    hour=h,
                    sample_count=summary.sample_count,
                    mae_mw=summary.mae_mw,
                    rmse_mw=summary.rmse_mw,
                    bias_mw=summary.bias_mw,
                    mean_forecast_mw=round(mean_fc, 2),
                    mean_actual_mw=round(mean_act, 2),
                )
            )

        return results

    def get_daily_timeseries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        cutoff_str: str = "09:00",
    ) -> List[DailyAccuracyPoint]:
        """Compute day-by-day accuracy metrics across January."""
        all_dates = self.store.available_delivery_dates
        if start_date:
            all_dates = [d for d in all_dates if d >= start_date]
        if end_date:
            all_dates = [d for d in all_dates if d <= end_date]

        results: List[DailyAccuracyPoint] = []
        for date_str in all_dates:
            evaluated = self.get_evaluated_pairs_for_range(date_str, date_str, cutoff_str)
            pairs = [(fc, act) for fc, act, _, _ in evaluated]
            if not pairs:
                continue

            summary = compute_error_metrics(pairs)
            peak_err = max(abs(fc - act) for fc, act in pairs)

            results.append(
                DailyAccuracyPoint(
                    delivery_date=date_str,
                    sample_count=summary.sample_count,
                    mae_mw=summary.mae_mw,
                    rmse_mw=summary.rmse_mw,
                    bias_mw=summary.bias_mw,
                    peak_error_mw=round(peak_err, 2),
                )
            )

        return results

    def get_risk_buffer(
        self,
        delivery_date: date,
        quantile: float = 0.90,
        cutoff_str: str = "09:00",
    ) -> RiskBufferResponse:
        """
        Calculate empirical risk-buffer procurement recommendations for delivery day D.

        Empirical over-forecast buffer: sizes the extra MW to buy from thermal plants
        such that the probability of a wind shortfall exceeding the buffer is <= (1 - quantile).
        """
        cutoff_utc = get_decision_cutoff_utc(delivery_date, cutoff_str)
        date_str = delivery_date.isoformat()

        # 1. Compute empirical over-forecast quantile across all historical January data
        all_evaluated = self.get_evaluated_pairs_for_range(cutoff_str=cutoff_str)
        # Over-forecast error = forecast - actual (where forecast > actual)
        positive_errors = [round(fc - act, 2) for fc, act, _, _ in all_evaluated if (fc - act) > 0]

        if positive_errors:
            empirical_buffer = calculate_percentile(positive_errors, quantile)
        else:
            empirical_buffer = 1500.0  # Fallback default if no positive errors

        # 2. Apply empirical buffer to the target delivery day
        target_times = self.store.get_target_times_for_date(date_str)
        periods: List[RiskBufferPeriod] = []
        total_buffer_mwh = 0.0

        for target_time in target_times:
            candidates = self.store.get_forecasts_for_target(target_time)
            selected = select_latest_forecast_at_cutoff(candidates, cutoff_utc)
            actual_mw = self.store.get_actual_hourly(target_time)

            if selected is not None:
                fc_mw = float(selected["generation"])
                conservative_mw = max(0.0, round(fc_mw - empirical_buffer, 2))
                buffer_req = round(fc_mw - conservative_mw, 2)
                total_buffer_mwh += buffer_req

                was_suff = (actual_mw >= conservative_mw) if actual_mw is not None else None
                periods.append(
                    RiskBufferPeriod(
                        target_time=target_time,
                        target_time_london=target_time[11:16],
                        forecast_mw=fc_mw,
                        conservative_wind_mw=conservative_mw,
                        buffer_required_mw=buffer_req,
                        actual_mw=actual_mw,
                        was_sufficient=was_suff,
                    )
                )

        explanation = (
            f"Based on empirical January 2026 forecast performance, the {int(quantile * 100)}th "
            f"percentile of over-forecast errors is {empirical_buffer:.0f} MW. Procuring this "
            f"additional thermal capacity provides a {int(quantile * 100)}% empirical confidence "
            f"that wind delivery shortfalls will be fully covered. Note: Empirical risk buffers "
            f"represent historical statistical distributions and do not guarantee future actuals."
        )

        return RiskBufferResponse(
            delivery_date=date_str,
            quantile=quantile,
            cutoff_utc=cutoff_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            empirical_buffer_mw=round(empirical_buffer, 2),
            total_buffer_mwh=round(total_buffer_mwh, 2),
            explanation=explanation,
            periods=periods,
        )
