import React from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function Card({
  title,
  subtitle,
  badge,
  action,
  children,
  className = "",
}: CardProps) {
  return (
    <div
      className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden transition-colors ${className}`}
    >
      {(title || subtitle || action || badge) && (
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800/60 flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="flex items-center space-x-2">
              {title && (
                <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  {title}
                </h3>
              )}
              {badge}
            </div>
            {subtitle && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="flex items-center space-x-2">{action}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
