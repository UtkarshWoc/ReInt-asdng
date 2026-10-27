import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Zap,
  TrendingUp,
  AlertCircle,
  Eye,
  Info,
  CheckCircle2,
} from "lucide-react";
import { api } from "../api/client";
import { Card } from "../components/ui/Card";
import { KpiCard } from "../components/ui/KpiCard";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";
import { DeliveryDatePicker } from "../components/controls/DeliveryDatePicker";
import { CutoffSelector } from "../components/controls/CutoffSelector";
import { ForecastVsActualChart } from "../components/charts/ForecastVsActualChart";
import { RevisionsChart } from "../components/charts/RevisionsChart";

interface ForecastPageProps {
  availableDates: string[];
}

export function ForecastPage({ availableDates }: ForecastPageProps) {
  const [selectedDate, setSelectedDate] = useState<string>(
    () => availableDates[3] || availableDates[0] || "2026-01-05"
  );
  const [cutoff, setCutoff] = useState<string>("09:00");
  const [selectedHour, setSelectedHour] = useState<string>("12:00");

  // Query forecast at decision
  const {
    data: forecastData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["forecastAtDecision", selectedDate, cutoff],
    queryFn: () => api.getForecastAtDecision(selectedDate, cutoff),
    enabled: Boolean(selectedDate),
  });

  // Query revisions for selected hour
  const targetTimeIso = `${selectedDate}T${selectedHour}:00Z`;
  const { data: revisionsData } = useQuery({
    queryKey: ["forecastRevisions", targetTimeIso, cutoff],
    queryFn: () => api.getForecastRevisions(targetTimeIso, cutoff),
    enabled: Boolean(selectedDate && selectedHour),
  });

  if (isError) {
    return (
      <ErrorState
        title="Failed to load forecast data"
        message={error instanceof Error ? error.message : "Unknown error"}
        onRetry={() => refetch()}
      />
    );
  }

  const kpis = forecastData?.kpis;
  const periods = forecastData?.periods || [];

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
            <span>Day-Ahead Decision Window</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Evaluate renewable wind generation available at gate closure on D-1.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <DeliveryDatePicker
            selectedDate={selectedDate}
            availableDates={availableDates}
            onChange={setSelectedDate}
          />
          <CutoffSelector cutoff={cutoff} onChange={setCutoff} />
        </div>
      </div>

      {/* Domain Context Note */}
      <div className="p-4 bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/80 dark:border-blue-900/40 rounded-xl text-xs text-blue-900 dark:text-blue-300 flex items-start space-x-3">
        <Info className="w-5 h-5 flex-shrink-0 text-blue-600 dark:text-blue-400 mt-0.5" />
        <div className="space-y-1">
          <div className="font-semibold">How to read this decision-time view:</div>
          <div>
            The green line reflects the <strong>latest forecast published at or before {cutoff} Europe/London on D-1</strong>.
            Forecasts published after cutoff are strictly excluded to prevent look-ahead leakage. The dotted blue line shows hindsight actual generation
            (FUELHH WIND), allowing quantitative evaluation of forecast errors (<span className="font-mono">Error = Forecast - Actual</span>).
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-24 w-full" />
          ))}
        </div>
      ) : kpis ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <KpiCard
            label="Expected Generation"
            value={(kpis.total_expected_mwh / 1000).toFixed(1)}
            unit="GWh"
            subtitle={`${kpis.total_expected_mwh.toLocaleString()} MWh`}
            tooltip="Total forecasted wind energy for the 24-hour delivery day at cutoff."
            variant="brand"
            icon={<Zap className="w-4 h-4" />}
          />
          <KpiCard
            label="Peak Forecast"
            value={kpis.peak_forecast_mw.toLocaleString()}
            unit="MW"
            subtitle="Maximum hourly capacity"
            tooltip="Highest forecasted generation level among all delivery hours."
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <KpiCard
            label="Minimum Forecast"
            value={kpis.min_forecast_mw.toLocaleString()}
            unit="MW"
            subtitle="Baseload wind support"
            tooltip="Lowest forecasted generation level during the delivery day."
          />
          <KpiCard
            label="Actual Generation"
            value={
              kpis.actual_total_mwh !== null
                ? `${(kpis.actual_total_mwh / 1000).toFixed(1)}`
                : "N/A"
            }
            unit="GWh"
            subtitle="Hindsight outturn"
            tooltip="Total outturn wind energy generated in hindsight (not known at decision time)."
            icon={<Eye className="w-4 h-4" />}
          />
          <KpiCard
            label="Day MAE"
            value={kpis.mae_mw !== null ? `${kpis.mae_mw.toLocaleString()}` : "N/A"}
            unit="MW"
            subtitle="Mean Absolute Error"
            tooltip="Average hourly magnitude of difference between decision forecast and outturn."
            variant={kpis.mae_mw && kpis.mae_mw < 1000 ? "success" : "warning"}
          />
          <KpiCard
            label="Missing Periods"
            value={kpis.missing_periods_count}
            subtitle={kpis.missing_periods_count === 0 ? "Complete 24h coverage" : "Unforecasted intervals"}
            tooltip="Number of delivery hours with zero forecasts published prior to cutoff."
            variant={kpis.missing_periods_count === 0 ? "success" : "danger"}
            icon={
              kpis.missing_periods_count === 0 ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-500" />
              )
            }
          />
        </div>
      ) : null}

      {/* Main Chart */}
      <Card
        title="Day-Ahead Wind Forecast vs Actual Generation"
        subtitle={`Delivery Day: ${selectedDate} • Decision Cutoff: ${cutoff} London Time`}
        badge={
          <span className="px-2 py-0.5 text-[11px] font-mono rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
            24 Hourly Periods
          </span>
        }
      >
        {isLoading ? (
          <Skeleton className="h-80 w-full" />
        ) : (
          <ForecastVsActualChart periods={periods} />
        )}
      </Card>

      {/* Two Column Section: Feed Timeline & Revisions Explorer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revisions Explorer */}
        <Card
          title="Forecast Revisions Explorer"
          subtitle="Inspect how forecasts evolved across successive publication batches"
          action={
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">Target Hour:</span>
              <select
                value={selectedHour}
                onChange={(e) => setSelectedHour(e.target.value)}
                className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold rounded px-2 py-1 text-slate-900 dark:text-slate-100 cursor-pointer"
              >
                {Array.from({ length: 24 }).map((_, h) => {
                  const hStr = `${h.toString().padStart(2, "0")}:00`;
                  return (
                    <option key={hStr} value={hStr}>
                      {hStr} UTC
                    </option>
                  );
                })}
              </select>
            </div>
          }
        >
          {revisionsData ? (
            <div className="space-y-4">
              <RevisionsChart
                revisions={revisionsData.revisions}
                cutoffUtc={revisionsData.cutoff_utc}
              />
              <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                  <span>Eligible (publishTime &le; cutoff)</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
                  <span>Excluded (publishTime &gt; cutoff)</span>
                </span>
              </div>
            </div>
          ) : (
            <Skeleton className="h-64 w-full" />
          )}
        </Card>

        {/* Data Feed & Lead-Times Table */}
        <Card
          title="Publication Lead-Times & Feeds"
          subtitle="Underlying publish times and lead horizons feeding each delivery hour"
        >
          <div className="overflow-x-auto max-h-72">
            <table className="w-full text-xs font-mono text-left">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 sticky top-0">
                <tr>
                  <th className="py-2 px-3">Hour</th>
                  <th className="py-2 px-3">Forecast</th>
                  <th className="py-2 px-3">Publish Time</th>
                  <th className="py-2 px-3">Lead</th>
                  <th className="py-2 px-3">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {periods.map((p) => {
                  const err = p.error_mw;
                  return (
                    <tr
                      key={p.target_time}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                    >
                      <td className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100">
                        {p.target_time.slice(11, 16)}
                      </td>
                      <td className="py-2 px-3 text-emerald-600 dark:text-emerald-400">
                        {p.forecast_mw !== null ? `${p.forecast_mw.toLocaleString()} MW` : "Missing"}
                      </td>
                      <td className="py-2 px-3 text-slate-500 dark:text-slate-400">
                        {p.publish_time ? p.publish_time.slice(5, 16).replace("T", " ") : "-"}
                      </td>
                      <td className="py-2 px-3 text-slate-600 dark:text-slate-300">
                        {p.horizon_hours !== null ? `${p.horizon_hours}h` : "-"}
                      </td>
                      <td
                        className={`py-2 px-3 font-semibold ${
                          err === null
                            ? "text-slate-400"
                            : err > 0
                            ? "text-amber-500"
                            : "text-indigo-500"
                        }`}
                      >
                        {err === null ? "-" : `${err > 0 ? `+${err}` : err} MW`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
