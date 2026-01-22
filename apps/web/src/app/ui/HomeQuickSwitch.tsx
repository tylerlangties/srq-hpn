"use client";

import { useMemo, useState } from "react";
import DayEvents from "./DayEvents";
import { addDays, startOfWeekend, toYmd } from "@/lib/dates";

type View = "today" | "tomorrow" | "weekend";

export default function HomeQuickSwitch() {
  const [view, setView] = useState<View>("today");

  const day = useMemo(() => {
    const now = new Date();
    if (view === "today") return toYmd(now);
    if (view === "tomorrow") return toYmd(addDays(now, 1));
    return toYmd(startOfWeekend(now));
  }, [view]);

  return (
    <section>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setView("today")}
          aria-pressed={view === "today"}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "today"
              ? "bg-blue-600 dark:bg-blue-500 text-white shadow-md"
              : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500 shadow-sm"
          }`}
        >
          Today
        </button>
        <button
          onClick={() => setView("tomorrow")}
          aria-pressed={view === "tomorrow"}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "tomorrow"
              ? "bg-blue-600 dark:bg-blue-500 text-white shadow-md"
              : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500 shadow-sm"
          }`}
        >
          Tomorrow
        </button>
        <button
          onClick={() => setView("weekend")}
          aria-pressed={view === "weekend"}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            view === "weekend"
              ? "bg-blue-600 dark:bg-blue-500 text-white shadow-md"
              : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-300 border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500 shadow-sm"
          }`}
        >
          Weekend
        </button>
      </div>

      <DayEvents day={day} />
    </section>
  );
}
