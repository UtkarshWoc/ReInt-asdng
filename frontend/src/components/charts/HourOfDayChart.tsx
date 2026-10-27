import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { HourAccuracyPoint } from "../../types";

interface HourOfDayChartProps {
  data: HourAccuracyPoint[];
}

export function HourOfDayChart({ data }: HourOfDayChartProps) {
  const chartData = data.map((d) => ({
    hourLabel: `${d.hour.toString().padStart(2, "0")}:00`,
    mae: d.mae_mw,
    bias: d.bias_mw,
    forecast: d.mean_forecast_mw,
    actual: d.mean_actual_mw,
  }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis dataKey="hourLabel" stroke="#64748b" fontSize={11} tickLine={false} />
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
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-2.5 rounded-lg shadow-xl text-xs space-y-1 font-mono">
                    <div className="font-semibold text-white">Hour: {item.hourLabel} London</div>
                    <div className="text-emerald-400">Mean MAE: {item.mae.toLocaleString()} MW</div>
                    <div className={item.bias > 0 ? "text-amber-400" : "text-indigo-400"}>
                      Mean Bias: {item.bias > 0 ? `+${item.bias}` : item.bias} MW
                    </div>
                    <div className="text-slate-400">Mean Forecast: {item.forecast.toLocaleString()} MW</div>
                    <div className="text-slate-400">Mean Outturn: {item.actual.toLocaleString()} MW</div>
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
          <Line
            type="monotone"
            dataKey="mae"
            name="MAE (MW)"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 2 }}
          />
          <Line
            type="monotone"
            dataKey="bias"
            name="Bias Error (MW)"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="3 3"
            dot={{ r: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
