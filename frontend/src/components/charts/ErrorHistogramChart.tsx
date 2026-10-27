import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { HistogramBin } from "../../types";

interface ErrorHistogramChartProps {
  histogram: HistogramBin[];
}

export function ErrorHistogramChart({ histogram }: ErrorHistogramChartProps) {
  const chartData = histogram.map((b) => ({
    binLabel: `${b.bin_start > 0 ? `+${b.bin_start}` : b.bin_start}`,
    binMid: b.bin_mid,
    count: b.count,
    share: b.share_percent,
    isOverForecast: b.bin_mid > 0,
  }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis
            dataKey="binLabel"
            stroke="#64748b"
            fontSize={10}
            angle={-30}
            textAnchor="end"
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            unit=" hrs"
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-2.5 rounded-lg shadow-xl text-xs space-y-1 font-mono">
                    <div className="font-semibold text-white">Error Bin: ~{data.binMid} MW</div>
                    <div>Periods: <span className="font-bold text-white">{data.count} hours</span></div>
                    <div>Share: <span className="font-bold text-slate-300">{data.share}%</span></div>
                    <div className="text-[10px] text-slate-400">
                      {data.isOverForecast ? "Over-forecast (Shortfall)" : "Under-forecast (Surplus)"}
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine x="0" stroke="#f59e0b" strokeWidth={1.5} />
          <Bar dataKey="count" name="Frequency (Hours)" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isOverForecast ? "#f59e0b" : "#6366f1"}
                opacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
