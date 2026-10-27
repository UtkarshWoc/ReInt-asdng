import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ForecastPeriod } from "../../types";

interface ForecastVsActualChartProps {
  periods: ForecastPeriod[];
}

export function ForecastVsActualChart({ periods }: ForecastVsActualChartProps) {
  const chartData = periods.map((p) => {
    const timeLabel = p.target_time.slice(11, 16);
    return {
      time: timeLabel,
      fullTime: p.target_time,
      londonTime: p.target_time_london,
      forecast: p.forecast_mw,
      actual: p.actual_mw,
      error: p.error_mw,
      publishTime: p.publish_time,
      horizon: p.horizon_hours,
    };
  });

  return (
    <div className="w-full h-80 sm:h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis
            dataKey="time"
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
            unit=" MW"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-3 rounded-lg shadow-xl text-xs space-y-1.5 font-mono">
                    <div className="font-semibold text-sm text-white">
                      {data.time} UTC ({data.londonTime})
                    </div>
                    <div className="flex items-center justify-between space-x-4">
                      <span className="text-emerald-400">Decision Forecast:</span>
                      <span className="font-bold">
                        {data.forecast !== null ? `${data.forecast.toLocaleString()} MW` : "Missing"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between space-x-4">
                      <span className="text-sky-400">Actual Outturn:</span>
                      <span className="font-bold">
                        {data.actual !== null ? `${data.actual.toLocaleString()} MW` : "N/A"}
                      </span>
                    </div>
                    {data.error !== null && (
                      <div className="flex items-center justify-between space-x-4 pt-1 border-t border-slate-800">
                        <span className="text-slate-400">Error (FC - Act):</span>
                        <span
                          className={`font-bold ${
                            data.error > 0 ? "text-amber-400" : "text-indigo-400"
                          }`}
                        >
                          {data.error > 0 ? `+${data.error.toLocaleString()}` : data.error.toLocaleString()} MW
                        </span>
                      </div>
                    )}
                    {data.publishTime && (
                      <div className="text-[10px] text-slate-400 pt-1">
                        Pub: {data.publishTime} ({data.horizon}h lead)
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend
            verticalAlign="top"
            height={36}
            formatter={(value) => (
              <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                {value}
              </span>
            )}
          />
          <Area
            type="monotone"
            dataKey="forecast"
            name="Forecast at Decision"
            stroke="#10b981"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#forecastGradient)"
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Outturn (Hindsight)"
            stroke="#0ea5e9"
            strokeWidth={2.5}
            strokeDasharray="4 4"
            dot={{ r: 3, fill: "#0ea5e9" }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
