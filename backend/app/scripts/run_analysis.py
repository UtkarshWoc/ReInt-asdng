"""Run quantitative accuracy analysis on real January 2026 Elexon data."""

import json
from pathlib import Path

from app.repositories.data_store import DataStore
from app.services.metrics import MetricsService, calculate_percentile


def run_analysis():
    snapshot_path = Path("data/jan_2026_snapshot.json")
    if not snapshot_path.exists():
        snapshot_path = Path("backend/data/jan_2026_snapshot.json")

    store = DataStore.load_from_file(snapshot_path)
    metrics_svc = MetricsService(store=store)

    # 1. Overall Summary
    summary = metrics_svc.get_accuracy_summary(cutoff_str="09:00")
    evaluated_pairs = metrics_svc.get_evaluated_pairs_for_range(cutoff_str="09:00")

    errors = [round(fc - act, 2) for fc, act, _, _ in evaluated_pairs]
    over_forecasts = [e for e in errors if e > 0]
    under_forecasts = [e for e in errors if e < 0]

    # 2. Daily Rankings (Worst & Best Days)
    daily_stats = metrics_svc.get_daily_timeseries(cutoff_str="09:00")
    sorted_by_mae = sorted(daily_stats, key=lambda d: d.mae_mw, reverse=True)
    worst_3_days = sorted_by_mae[:3]
    best_3_days = sorted(daily_stats, key=lambda d: d.mae_mw)[:3]

    # 3. Horizon Degradation
    by_horizon = metrics_svc.get_accuracy_by_horizon(cutoff_str="09:00")

    # 4. Wind Level Buckets (Heteroskedasticity)
    buckets = {"Low (<6 GW)": [], "Medium (6-12 GW)": [], "High (>12 GW)": []}
    for fc, act, _, _ in evaluated_pairs:
        if act < 6000:
            buckets["Low (<6 GW)"].append(abs(fc - act))
        elif act <= 12000:
            buckets["Medium (6-12 GW)"].append(abs(fc - act))
        else:
            buckets["High (>12 GW)"].append(abs(fc - act))

    wind_bucket_summary = {}
    for b_name, errs in buckets.items():
        if errs:
            wind_bucket_summary[b_name] = {
                "count": len(errs),
                "mae_mw": round(sum(errs) / len(errs), 1),
                "p90_mw": round(calculate_percentile(errs, 0.90), 1),
            }

    # 5. Risk Buffer Quantiles (Positive Over-forecasts)
    buffer_quantiles = {}
    for q in [0.75, 0.85, 0.90, 0.95, 0.99]:
        buffer_quantiles[f"P{int(q*100)}"] = round(calculate_percentile(over_forecasts, q), 1)

    results = {
        "overall": {
            "sample_count": summary.sample_count,
            "mae_mw": summary.mae_mw,
            "rmse_mw": summary.rmse_mw,
            "bias_mw": summary.bias_mw,
            "mape_percent": summary.mape_percent,
            "p50_abs_error_mw": summary.p50_abs_error_mw,
            "p90_abs_error_mw": summary.p90_abs_error_mw,
            "p95_abs_error_mw": summary.p95_abs_error_mw,
            "p99_abs_error_mw": summary.p99_abs_error_mw,
            "over_forecast_count": len(over_forecasts),
            "over_forecast_share": round(len(over_forecasts) / len(errors) * 100, 1),
            "under_forecast_count": len(under_forecasts),
            "under_forecast_share": round(len(under_forecasts) / len(errors) * 100, 1),
            "mean_over_forecast_mw": round(sum(over_forecasts) / len(over_forecasts), 1) if over_forecasts else 0,
            "mean_under_forecast_mw": round(sum(under_forecasts) / len(under_forecasts), 1) if under_forecasts else 0,
            "share_within_500mw": summary.share_within_500mw,
            "share_within_1000mw": summary.share_within_1000mw,
            "share_within_2000mw": summary.share_within_2000mw,
        },
        "worst_days": [
            {"date": d.delivery_date, "mae_mw": d.mae_mw, "peak_error_mw": d.peak_error_mw, "bias_mw": d.bias_mw}
            for d in worst_3_days
        ],
        "best_days": [
            {"date": d.delivery_date, "mae_mw": d.mae_mw, "peak_error_mw": d.peak_error_mw, "bias_mw": d.bias_mw}
            for d in best_3_days
        ],
        "by_horizon": [
            {"horizon_bin": h.horizon_bin, "samples": h.sample_count, "mae_mw": h.mae_mw, "p90_mw": h.p90_abs_error_mw}
            for h in by_horizon
        ],
        "wind_level_buckets": wind_bucket_summary,
        "risk_buffer_quantiles": buffer_quantiles,
    }

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    run_analysis()
