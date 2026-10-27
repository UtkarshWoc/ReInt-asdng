import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sun, Moon, Wind } from "lucide-react";
import { api } from "./api/client";
import { ForecastPage } from "./pages/ForecastPage";
import { AccuracyPage } from "./pages/AccuracyPage";

export function App() {
  const [activeTab, setActiveTab] = useState<"forecast" | "accuracy">("forecast");
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem("theme") === "dark";
  });

  const { data: meta } = useQuery({
    queryKey: ["meta"],
    queryFn: () => api.getMeta(),
    initialData: {
      available_dates: [
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
        "2026-01-06",
      ],
      default_cutoff: "09:00",
      data_freshness: "2026-01-31T23:30:00Z",
      total_forecast_rows: 19856,
      total_actual_rows: 768,
      date_range_start: "2026-01-01",
      date_range_end: "2026-02-01",
    },
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const availableDates = meta?.available_dates || [
    "2026-01-02",
    "2026-01-03",
    "2026-01-04",
    "2026-01-05",
    "2026-01-06",
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400 rounded-lg">
              <Wind className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-50">
                  UK Wind Day-Ahead Decision Support
                </h1>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                  Elexon Verified
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Elexon BMRS • D-1 09:00 London Gate Closure
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Tabs */}
            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs sm:text-sm font-medium">
              <button
                onClick={() => setActiveTab("forecast")}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeTab === "forecast"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Forecast at Decision
              </button>
              <button
                onClick={() => setActiveTab("accuracy")}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeTab === "accuracy"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Forecast Accuracy
              </button>
            </div>

            {/* Dark Mode Toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              aria-label="Toggle dark mode"
              className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            >
              {darkMode ? (
                <Sun className="w-5 h-5 text-amber-400" />
              ) : (
                <Moon className="w-5 h-5 text-slate-600" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {activeTab === "forecast" ? (
          <ForecastPage availableDates={availableDates} />
        ) : (
          <AccuracyPage availableDates={availableDates} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 py-4 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-mono gap-2">
          <div>
            Error Definition: <span className="font-semibold text-slate-700 dark:text-slate-300">Error = Forecast - Actual</span> (Positive = Over-forecast / Wind Shortfall)
          </div>
          <div className="flex items-center space-x-4 text-[11px]">
            <span>UTC &amp; Europe/London DST-Safe</span>
            <span>&bull;</span>
            <span>Elexon FUELHH &amp; WINDFOR</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
