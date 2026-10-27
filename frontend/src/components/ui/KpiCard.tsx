import React from "react";
import { HelpCircle } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  tooltip?: string;
  variant?: "default" | "success" | "warning" | "danger" | "brand";
}

export function KpiCard({
  label,
  value,
  unit,
  subtitle,
  icon,
  tooltip,
  variant = "default",
}: KpiCardProps) {
  const variantStyles = {
    default: "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900",
    success: "border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/30 dark:bg-emerald-950/20",
    warning: "border-amber-200 dark:border-amber-900/50 bg-amber-50/30 dark:bg-amber-950/20",
    danger: "border-rose-200 dark:border-rose-900/50 bg-rose-50/30 dark:bg-rose-950/20",
    brand: "border-brand-200 dark:border-brand-900/50 bg-brand-50/30 dark:bg-brand-950/20",
  };

  return (
    <div
      className={`p-5 rounded-xl border shadow-sm flex flex-col justify-between transition-all hover:shadow-md ${variantStyles[variant]}`}
    >
      <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
        <div className="flex items-center space-x-1.5 group relative">
          <span className="text-xs font-semibold uppercase tracking-wider">
            {label}
          </span>
          {tooltip && (
            <div className="relative flex items-center">
              <HelpCircle className="w-3.5 h-3.5 cursor-pointer text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:flex flex-col items-center z-50 pointer-events-none">
                <div className="bg-slate-900 text-white dark:bg-slate-800 text-[11px] rounded px-2.5 py-1.5 shadow-lg w-48 text-center leading-tight">
                  {tooltip}
                </div>
                <div className="w-2 h-1 bg-slate-900 dark:bg-slate-800 rotate-45 -mt-0.5"></div>
              </div>
            </div>
          )}
        </div>
        {icon && <div className="text-slate-400 dark:text-slate-500">{icon}</div>}
      </div>

      <div className="flex items-baseline space-x-1.5">
        <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
          {value}
        </span>
        {unit && (
          <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
            {unit}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
          {subtitle}
        </div>
      )}
    </div>
  );
}
