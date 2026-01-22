"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { EventOccurrenceOut } from "@/types/events";

type Props = {
  day: string; // YYYY-MM-DD
};

function formatLocalTime(isoUtc: string) {
  const dt = new Date(isoUtc);
  return dt.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function DayEvents({ day }: Props) {
  const [data, setData] = useState<EventOccurrenceOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setError(null);
        const res = await apiGet<EventOccurrenceOut[]>(
          `/api/events/day?day=${encodeURIComponent(day)}`
        );
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }

    // Reset to show loading state when day changes
    setData(null);
    load();

    return () => {
      cancelled = true;
    };
  }, [day]);

  if (error) {
    return (
      <div className="rounded-xl border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-red-900 dark:text-red-300">API error</p>
            <p className="mt-1 text-sm text-red-800 dark:text-red-400">
              Something went wrong while fetching events.
            </p>
          </div>
        </div>

        <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-white/90 dark:bg-gray-800/90 p-3 text-xs text-red-900 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </pre>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="h-4 w-40 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-3 w-24 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>

        <div className="mt-4 space-y-3">
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
        </div>
      </div>
    );
  }

  return (
    <section className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm">
      <header className="flex items-center justify-between gap-3 border-b-2 border-gray-200 dark:border-gray-700 px-4 py-3 bg-gray-50 dark:bg-gray-900">
        <div>
          <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">Events</h2>
          <p className="text-xs text-gray-700 dark:text-gray-400 font-medium">For {day}</p>
        </div>

        <span className="rounded-full border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1 text-xs font-semibold text-gray-900 dark:text-gray-300">
          {data.length} {data.length === 1 ? "event" : "events"}
        </span>
      </header>

      {data.length === 0 ? (
        <div className="px-4 py-6">
          <div className="rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50 p-4">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-200">
              Nothing scheduled yet
            </p>
            <p className="mt-1 text-sm text-gray-700 dark:text-gray-400">
              Try a different day, or check back later.
            </p>
          </div>
        </div>
      ) : (
        <ul className="divide-y-2 divide-gray-100 dark:divide-gray-700">
          {data.map((occ) => {
            const start = formatLocalTime(occ.start_datetime_utc);
            const end = occ.end_datetime_utc
              ? formatLocalTime(occ.end_datetime_utc)
              : null;

            return (
              <li key={occ.id} className="px-4 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {occ.event.title}
                    </p>

                    <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
                      {occ.venue ? (
                        <>
                          <span className="font-semibold text-gray-900 dark:text-gray-200">
                            {occ.venue.name}
                          </span>
                          {occ.venue.area && (
                            <>
                              <span className="text-gray-500 dark:text-gray-500"> • </span>
                              <span className="text-gray-700 dark:text-gray-300">{occ.venue.area}</span>
                            </>
                          )}
                        </>
                      ) : (
                        <span className="font-semibold text-gray-900 dark:text-gray-200">
                          {occ.location_text ?? "Location TBD"}
                        </span>
                      )}
                    </p>

                    <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 font-medium">
                      {start}
                      {end ? ` → ${end}` : ""}
                    </p>
                  </div>

                  <div className="shrink-0 text-right">
                    {occ.event.is_free ? (
                      <span className="inline-flex items-center rounded-full bg-emerald-100 dark:bg-emerald-900/30 px-2 py-1 text-xs font-semibold text-emerald-800 dark:text-emerald-300 border-2 border-emerald-300 dark:border-emerald-700">
                        Free
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-blue-100 dark:bg-blue-900/30 px-2 py-1 text-xs font-semibold text-blue-800 dark:text-blue-300 border-2 border-blue-300 dark:border-blue-700">
                        {occ.event.price_text ?? "Paid"}
                      </span>
                    )}

                    {occ.event.status !== "scheduled" ? (
                      <p className="mt-2 text-xs font-semibold text-red-700 dark:text-red-400">
                        {occ.event.status}
                      </p>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
