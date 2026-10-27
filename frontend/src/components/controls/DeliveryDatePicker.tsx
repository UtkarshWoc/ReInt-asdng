import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";

interface DeliveryDatePickerProps {
  selectedDate: string;
  availableDates: string[];
  onChange: (newDate: string) => void;
}

export function DeliveryDatePicker({
  selectedDate,
  availableDates,
  onChange,
}: DeliveryDatePickerProps) {
  const currentIndex = availableDates.indexOf(selectedDate);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < availableDates.length - 1;

  const handlePrev = () => {
    if (hasPrev) {
      onChange(availableDates[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (hasNext) {
      onChange(availableDates[currentIndex + 1]);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1 shadow-sm">
        <button
          onClick={handlePrev}
          disabled={!hasPrev}
          aria-label="Previous day"
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 disabled:opacity-30 disabled:cursor-not-allowed transition"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center px-3 space-x-2">
          <Calendar className="w-4 h-4 text-brand-600 dark:text-brand-400" />
          <select
            value={selectedDate}
            onChange={(e) => onChange(e.target.value)}
            className="bg-transparent text-sm font-semibold text-slate-900 dark:text-slate-100 focus:outline-none cursor-pointer"
          >
            {availableDates.map((date) => (
              <option key={date} value={date} className="dark:bg-slate-900">
                {date} (Day D)
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleNext}
          disabled={!hasNext}
          aria-label="Next day"
          className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 disabled:opacity-30 disabled:cursor-not-allowed transition"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
