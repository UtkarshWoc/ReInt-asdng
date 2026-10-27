import { useState, useEffect } from "react";
import { Sun, Moon, Wind } from "lucide-react";

export function App() {
  const [activeTab, setActiveTab] = useState<"forecast" | "accuracy">("forecast");
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem("theme") === "dark";
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

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400 rounded-lg">
              <Wind className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">UK Wind Day-Ahead Decision Support</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Elexon BMRS • D-1 09:00 London Gate Closure
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Tabs */}
            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-sm font-medium">
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
              {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {activeTab === "forecast" ? (
          <div className="space-y-6">
            <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Day-Ahead Wind Forecast at Gate Closure</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Evaluating the latest available forecast published prior to the D-1 09:00 London cutoff.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="p-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Historical Accuracy & Risk Buffer Analysis</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Empirical evaluation across January 2026 delivery dates.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-4 text-center text-xs text-slate-500 dark:text-slate-400 font-mono">
        Error Definition: Error = Forecast - Actual (Positive = Over-forecast) • Strictly ISO-8601 UTC & Europe/London
      </footer>
    </div>
  );
}

export default App;
