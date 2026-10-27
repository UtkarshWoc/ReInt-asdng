import { Clock } from "lucide-react";

interface CutoffSelectorProps {
  cutoff: string;
  onChange: (newCutoff: string) => void;
}

const COMMON_CUTOFFS = [
  { value: "06:00", label: "06:00 (Early)" },
  { value: "07:30", label: "07:30 (Pre-auction)" },
  { value: "09:00", label: "09:00 (Default Gate Closure)" },
  { value: "11:00", label: "11:00 (Late)" },
];

export function CutoffSelector({ cutoff, onChange }: CutoffSelectorProps) {
  return (
    <div className="flex items-center space-x-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3 py-1.5 shadow-sm">
      <Clock className="w-4 h-4 text-slate-500 dark:text-slate-400" />
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
        D-1 Cutoff:
      </span>
      <select
        value={cutoff}
        onChange={(e) => onChange(e.target.value)}
        className="bg-transparent text-sm font-semibold text-slate-900 dark:text-slate-100 focus:outline-none cursor-pointer"
      >
        {COMMON_CUTOFFS.map((opt) => (
          <option key={opt.value} value={opt.value} className="dark:bg-slate-900">
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
