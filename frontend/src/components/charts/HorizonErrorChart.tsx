import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { HorizonAccuracyPoint } from "../../types";

interface HorizonErrorChartProps {
  data: HorizonAccuracyPoint[];
}

export function HorizonErrorChart({ data }: HorizonErrorChartProps) {
  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis dataKey="horizon_bin" stroke="#64748b" fontSize={12} tickLine={false} />
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
                const item = payload[0].payload as HorizonAccuracyPoint;
                return (
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-2.5 rounded-lg shadow-xl text-xs space-y-1 font-mono">
                    <div className="font-semibold text-white">Lead Horizon: {item.horizon_bin}</div>
                    <div className="text-emerald-400">MAE: {item.mae_mw.toLocaleString()} MW</div>
                    <div className="text-amber-400">P90 Error: {item.p90_abs_error_mw.toLocaleString()} MW</div>
                    <div className="text-sky-400">RMSE: {item.rmse_mw.toLocaleString()} MW</div>
                    <div className="text-slate-400">Samples: {item.sample_count} periods</div>
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
          <Bar dataKey="mae_mw" name="Mean Absolute Error (MW)" fill="#10b981" radius={[4, 4, 0, 0]} />
          <Bar dataKey="p90_abs_error_mw" name="P90 Absolute Error (MW)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
