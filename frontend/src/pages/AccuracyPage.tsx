import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldAlert,
  BarChart2,
  Activity,
  Info,
} from "lucide-react";
import { api } from "../api/client";
import { Card } from "../components/ui/Card";
import { KpiCard } from "../components/ui/KpiCard";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";
import { CutoffSelector } from "../components/controls/CutoffSelector";
import { DeliveryDatePicker } from "../components/controls/DeliveryDatePicker";
import { ErrorHistogramChart } from "../components/charts/ErrorHistogramChart";
import { HorizonErrorChart } from "../components/charts/HorizonErrorChart";
import { HourOfDayChart } from "../components/charts/HourOfDayChart";
import { DailyTrendChart } from "../components/charts/DailyTrendChart";
import { RiskBufferChart } from "../components/charts/RiskBufferChart";

interface AccuracyPageProps {
  availableDates: string[];
}

export function AccuracyPage({ availableDates }: AccuracyPageProps) {
  const [cutoff, setCutoff] = useState<string>("09:00");
  const [bufferDate, setBufferDate] = useState<string>(
    () => availableDates[5] || availableDates[0] || "2026-01-05"
  );
  const [quantile, setQuantile] = useState<number>(0.90);

  // Queries
  const {
    data: summary,
    isLoading: loadingSummary,
    isError: errorSummary,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ["accuracySummary", cutoff],
    queryFn: () => api.getAccuracySummary(undefined, undefined, cutoff),
  });

  const { data: horizonData, isLoading: loadingHorizon } = useQuery({
    queryKey: ["accuracyByHorizon", cutoff],
    queryFn: () => api.getAccuracyByHorizon(undefined, undefined, cutoff),
  });

  const { data: hourData, isLoading: loadingHour } = useQuery({
    queryKey: ["accuracyByHour", cutoff],
    queryFn: () => api.getAccuracyByHour(undefined, undefined, cutoff),
  });

  const { data: timeseriesData, isLoading: loadingTimeseries } = useQuery({
    queryKey: ["accuracyTimeseries", cutoff],
    queryFn: () => api.getAccuracyTimeseries(undefined, undefined, cutoff),
  });

  const { data: riskBufferData, isLoading: loadingBuffer } = useQuery({
    queryKey: ["riskBuffer", bufferDate, quantile, cutoff],
    queryFn: () => api.getRiskBuffer(bufferDate, quantile, cutoff),
    enabled: Boolean(bufferDate),
  });

  if (errorSummary) {
    return (
      <ErrorState
        title="Failed to load accuracy metrics"
        message="An error occurred while evaluating forecast errors."
        onRetry={() => refetchSummary()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Filter */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
            <span>Quantitative Accuracy & Risk Sizing</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Empirical evaluation across all decision-time forecasts in January 2026.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <CutoffSelector cutoff={cutoff} onChange={setCutoff} />
        </div>
      </div>

      {/* Domain Context Note */}
      <div className="p-4 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 rounded-xl text-xs text-amber-900 dark:text-amber-300 flex items-start space-x-3">
        <Info className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold">Sign Convention & Hedging Logic:</div>
          <div>
            <strong>Error = Forecast &minus; Actual</strong>. A positive error indicates an <strong>over-forecast</strong> (wind generation fell short of expectations, leaving the utility with unserved energy that must be procured from thermal or the balancing market at punitive prices). A negative error indicates an <strong>under-forecast</strong> (excess wind generation).
          </div>
        </div>
      </div>

      {/* Headline KPI Cards */}
      {loadingSummary ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-24 w-full" />
          ))}
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <KpiCard
            label="Mean Absolute Error"
            value={summary.mae_mw.toLocaleString()}
            unit="MW"
            subtitle="Overall accuracy"
            tooltip="Average absolute error between decision forecast and actual outturn across all January hours."
            variant={summary.mae_mw < 1000 ? "success" : "warning"}
            icon={<Activity className="w-4 h-4" />}
          />
          <KpiCard
            label="Root Mean Square Error"
            value={summary.rmse_mw.toLocaleString()}
            unit="MW"
            subtitle="Penalizes large errors"
            tooltip="RMSE gives higher weight to large forecast blunders, critical for grid stability."
          />
          <KpiCard
            label="Mean Bias"
            value={`${summary.bias_mw > 0 ? `+${summary.bias_mw}` : summary.bias_mw}`}
            unit="MW"
            subtitle={summary.bias_mw > 0 ? "Net Over-forecast" : "Net Under-forecast"}
            tooltip="Systematic tendency to overestimate (+) or underestimate (-) wind generation."
            variant={summary.bias_mw > 0 ? "warning" : "default"}
          />
          <KpiCard
            label="P90 Absolute Error"
            value={summary.p90_abs_error_mw.toLocaleString()}
            unit="MW"
            subtitle="90% of hours within this error"
            tooltip="90th percentile of absolute error magnitude across evaluated periods."
            variant="brand"
            icon={<ShieldAlert className="w-4 h-4" />}
          />
          <KpiCard
            label="Within &plusmn;1,000 MW"
            value={`${summary.share_within_1000mw}%`}
            subtitle={`${summary.share_within_2000mw}% within &plusmn;2 GW`}
            tooltip="Percentage of hours where the decision forecast was within 1,000 MW of actual outturn."
            icon={<BarChart2 className="w-4 h-4" />}
          />
          <KpiCard
            label="Safe MAPE"
            value={summary.mape_percent !== null ? `${summary.mape_percent}%` : "N/A"}
            subtitle="Excludes near-zero actuals"
            tooltip="Mean Absolute Percentage Error calculated on periods with actual generation >= 100 MW to avoid division by near-zero."
          />
        </div>
      ) : null}

      {/* Row 1: Error Distribution & Horizon Degradation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="Forecast Error Distribution"
          subtitle="Frequency of error magnitude (Negative = Under-forecast, Positive = Over-forecast)"
          badge={
            <span className="px-2 py-0.5 text-[11px] font-mono rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              {summary?.sample_count} Hours Evaluated
            </span>
          }
        >
          {loadingSummary ? (
            <Skeleton className="h-72 w-full" />
          ) : summary ? (
            <ErrorHistogramChart histogram={summary.histogram} />
          ) : null}
        </Card>

        <Card
          title="Error Degradation by Forecast Horizon"
          subtitle="How MAE and P90 error grow as lead time increases prior to delivery"
          badge={
            <span className="px-2 py-0.5 text-[11px] font-mono rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              Lead Time Brackets
            </span>
          }
        >
          {loadingHorizon ? (
            <Skeleton className="h-72 w-full" />
          ) : horizonData ? (
            <HorizonErrorChart data={horizonData} />
          ) : null}
        </Card>
      </div>

      {/* Row 2: Diurnal Patterns & Daily Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="Diurnal Error Profile (Hour of Day)"
          subtitle="Average MAE and Bias across settlement hours (00:00 to 23:00 London time)"
        >
          {loadingHour ? (
            <Skeleton className="h-72 w-full" />
          ) : hourData ? (
            <HourOfDayChart data={hourData} />
          ) : null}
        </Card>

        <Card
          title="Daily Forecast Accuracy Trend"
          subtitle="Day-by-day MAE and Bias tracking volatile wind events across January"
        >
          {loadingTimeseries ? (
            <Skeleton className="h-72 w-full" />
          ) : timeseriesData ? (
            <DailyTrendChart data={timeseriesData} />
          ) : null}
        </Card>
      </div>

      {/* Section: Risk Buffer & Thermal Procurement Sizing */}
      <Card
        title="Empirical Risk Buffer & Thermal Procurement Sizing"
        subtitle="Size an additional thermal reserve to protect against wind shortfall at target confidence"
        action={
          <div className="flex flex-wrap items-center gap-3">
            <DeliveryDatePicker
              selectedDate={bufferDate}
              availableDates={availableDates}
              onChange={setBufferDate}
            />
            <div className="flex items-center space-x-1.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1 text-xs">
              <span className="text-slate-500 font-medium">Confidence:</span>
              <select
                value={quantile}
                onChange={(e) => setQuantile(parseFloat(e.target.value))}
                className="bg-transparent font-bold text-slate-900 dark:text-slate-100 focus:outline-none cursor-pointer"
              >
                <option value={0.75} className="dark:bg-slate-900">75% (Aggressive)</option>
                <option value={0.85} className="dark:bg-slate-900">85% (Moderate)</option>
                <option value={0.90} className="dark:bg-slate-900">90% (Industry Standard)</option>
                <option value={0.95} className="dark:bg-slate-900">95% (Conservative)</option>
                <option value={0.99} className="dark:bg-slate-900">99% (Strict)</option>
              </select>
            </div>
          </div>
        }
      >
        {loadingBuffer ? (
          <Skeleton className="h-80 w-full" />
        ) : riskBufferData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
                  Recommended Thermal Buffer
                </div>
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                  +{riskBufferData.empirical_buffer_mw.toLocaleString()} MW
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Empirical {int(riskBufferData.quantile * 100)}th percentile over-forecast error
                </div>
              </div>

              <div className="p-4 rounded-lg bg-brand-500/10 border border-brand-500/20">
                <div className="text-xs font-semibold text-brand-700 dark:text-brand-400 uppercase tracking-wider">
                  Daily Energy Hedged
                </div>
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                  {(riskBufferData.total_buffer_mwh / 1000).toFixed(1)} GWh
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  {riskBufferData.total_buffer_mwh.toLocaleString()} MWh total buffer across 24h
                </div>
              </div>

              <div className="p-4 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex flex-col justify-center">
                <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                  Risk Sizing Formula
                </div>
                <div className="font-mono text-xs text-slate-700 dark:text-slate-300 mt-1">
                  Wind_conservative = max(0, Forecast &minus; Buffer)
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                  Thermal_procure = Demand &minus; Wind_conservative
                </div>
              </div>
            </div>

            <RiskBufferChart
              periods={riskBufferData.periods}
              bufferMw={riskBufferData.empirical_buffer_mw}
            />

            <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg text-xs text-slate-600 dark:text-slate-300 font-mono leading-relaxed">
              {riskBufferData.explanation}
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

function int(val: number): number {
  return Math.round(val);
}
