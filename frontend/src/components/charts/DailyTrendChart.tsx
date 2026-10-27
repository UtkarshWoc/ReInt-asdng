import {
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import { DailyAccuracyPoint } from "../../types";

interface DailyTrendChartProps {
  data: DailyAccuracyPoint[];
}

export function DailyTrendChart({ data }: DailyTrendChartProps) {
  const chartData = data.map((d) => ({
    date: d.delivery_date.slice(5), // MM-DD
    fullDate: d.delivery_date,
    mae: d.mae_mw,
    bias: d.bias_mw,
    peakError: d.peak_error_mw,
  }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis
            dataKey="date"
            stroke="#64748b"
            fontSize={11}
            angle={-35}
            textAnchor="end"
            tickLine={false}
          />
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
                    <div className="font-semibold text-white">Date: {item.fullDate}</div>
                    <div className="text-emerald-400">MAE: {item.mae.toLocaleString()} MW</div>
                    <div className={item.bias > 0 ? "text-amber-400" : "text-indigo-400"}>
                      Bias: {item.bias > 0 ? `+${item.bias}` : item.bias} MW
                    </div>
                    <div className="text-rose-400">Peak Error: {item.peakError.toLocaleString()} MW</div>
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
          <Bar dataKey="mae" name="Day MAE (MW)" fill="#10b981" radius={[3, 3, 0, 0]} opacity={0.8} />
          <Line
            type="monotone"
            dataKey="bias"
            name="Mean Bias (MW)"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 2 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
