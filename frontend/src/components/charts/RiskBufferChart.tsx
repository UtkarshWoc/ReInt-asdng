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
import { RiskBufferPeriod } from "../../types";

interface RiskBufferChartProps {
  periods: RiskBufferPeriod[];
  bufferMw: number;
}

export function RiskBufferChart({ periods, bufferMw }: RiskBufferChartProps) {
  const chartData = periods.map((p) => ({
    time: p.target_time.slice(11, 16),
    forecast: p.forecast_mw,
    conservative: p.conservative_wind_mw,
    buffer: p.buffer_required_mw,
    actual: p.actual_mw,
    wasSufficient: p.was_sufficient,
  }));

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="bufferGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            tickFormatter={(val) => `${(val / 1000).toFixed(1)}k`}
            unit=" MW"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-3 rounded-lg shadow-xl text-xs space-y-1.5 font-mono">
                    <div className="font-semibold text-white">Hour: {item.time} UTC</div>
                    <div className="text-emerald-400">Decision Forecast: {item.forecast.toLocaleString()} MW</div>
                    <div className="text-amber-400 font-bold">
                      Conservative Wind: {item.conservative.toLocaleString()} MW
                    </div>
                    <div className="text-slate-300">
                      Thermal Buffer Required: +{bufferMw.toLocaleString()} MW
                    </div>
                    {item.actual !== null && (
                      <div className="pt-1 border-t border-slate-800 flex items-center justify-between">
                        <span className="text-sky-400">Actual Outturn:</span>
                        <span className="font-bold">{item.actual.toLocaleString()} MW</span>
                      </div>
                    )}
                    {item.wasSufficient !== null && (
                      <div className="text-[10px] pt-1">
                        <span
                          className={`px-1.5 py-0.5 rounded font-semibold ${
                            item.wasSufficient
                              ? "bg-emerald-950 text-emerald-300"
                              : "bg-rose-950 text-rose-300"
                          }`}
                        >
                          {item.wasSufficient ? "Covered: Actual >= Conservative" : "Buffer Breached: Outturn < Conservative"}
                        </span>
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
            formatter={(val) => <span className="text-xs font-medium text-slate-700 dark:text-slate-300">{val}</span>}
          />
          <Area
            type="monotone"
            dataKey="forecast"
            name="Baseline Decision Forecast (MW)"
            stroke="#10b981"
            strokeWidth={2}
            fill="#10b981"
            fillOpacity={0.1}
          />
          <Line
            type="monotone"
            dataKey="conservative"
            name="Conservative Wind Baseline (MW)"
            stroke="#f59e0b"
            strokeWidth={2.5}
            dot={{ r: 2 }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual Outturn (MW, Hindsight)"
            stroke="#0ea5e9"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={{ r: 2 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
