import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { RevisionPoint } from "../../types";

interface RevisionsChartProps {
  revisions: RevisionPoint[];
  cutoffUtc: string;
}

export function RevisionsChart({ revisions, cutoffUtc }: RevisionsChartProps) {
  if (!revisions.length) {
    return (
      <div className="h-64 flex items-center justify-center text-sm text-slate-400">
        No revision history available for this target period.
      </div>
    );
  }

  const chartData = revisions.map((r) => ({
    publishTime: r.publish_time.replace("T", " ").replace("Z", ""),
    shortPub: r.publish_time.slice(5, 16).replace("T", " "),
    generation: r.generation_mw,
    horizon: r.horizon_hours,
    isEligible: r.is_at_or_before_cutoff,
  }));

  const cutoffLabel = cutoffUtc.slice(5, 16).replace("T", " ");

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
          <XAxis
            dataKey="shortPub"
            stroke="#64748b"
            fontSize={11}
            angle={-25}
            textAnchor="end"
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
                  <div className="bg-slate-900/95 backdrop-blur border border-slate-800 text-slate-100 p-2.5 rounded-lg shadow-xl text-xs space-y-1 font-mono">
                    <div className="font-semibold text-white">Pub: {data.publishTime} UTC</div>
                    <div>
                      Forecast: <span className="font-bold text-brand-400">{data.generation.toLocaleString()} MW</span>
                    </div>
                    <div>Horizon: <span className="text-slate-300">{data.horizon}h lead time</span></div>
                    <div className="pt-1">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          data.isEligible
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-rose-950 text-rose-300 border border-rose-800"
                        }`}
                      >
                        {data.isEligible ? "Available at Cutoff" : "Post-Cutoff (Leaked)"}
                      </span>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine
            x={cutoffLabel}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            label={{
              value: "D-1 Cutoff",
              position: "top",
              fill: "#f59e0b",
              fontSize: 11,
            }}
          />
          <Line
            type="stepAfter"
            dataKey="generation"
            name="Forecast Evolution"
            stroke="#10b981"
            strokeWidth={2}
            dot={(props) => {
              const { cx, cy, payload } = props;
              const isEligible = payload.isEligible;
              return (
                <circle
                  key={`${cx}-${cy}`}
                  cx={cx}
                  cy={cy}
                  r={4}
                  fill={isEligible ? "#10b981" : "#f43f5e"}
                  stroke="#ffffff"
                  strokeWidth={1}
                />
              );
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
