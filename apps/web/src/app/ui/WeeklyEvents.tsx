"use client";

import { useEffect, useMemo, useState } from "react";
import type { EventOccurrenceOut } from "@/types/events";
import { apiGet } from "@/lib/api";

type Props = {
  start: string; // YYYY-MM-DD (local SRQ date)
  end: string;   // YYYY-MM-DD (local SRQ date, inclusive)
  title?: string;
};

const SRQ_TZ = "America/New_York";

function dayKeyInSarasota(isoUtc: string) {
  const dt = new Date(isoUtc);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: SRQ_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(dt);
  const y = parts.find((p) => p.type === "year")?.value ?? "0000";
  const m = parts.find((p) => p.type === "month")?.value ?? "00";
  const d = parts.find((p) => p.type === "day")?.value ?? "00";
  return `${y}-${m}-${d}`; // YYYY-MM-DD
}

function formatDayLabel(day: string) {
  // day = YYYY-MM-DD (local)
  const [y, m, d] = day.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d)); // stable date container
  return new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(dt);
}

function formatTimeRange(startIsoUtc: string, endIsoUtc: string | null) {
  const start = new Date(startIsoUtc);
  const end = endIsoUtc ? new Date(endIsoUtc) : null;

  // "All day" heuristic: if duration ~24h and starts at midnight local
  // (MustDo events may show as midnight->midnight in America/New_York)
  const startParts = new Intl.DateTimeFormat("en-US", {
    timeZone: SRQ_TZ,
    hour: "numeric",
    minute: "2-digit",
  }).formatToParts(start);

  const startHour = startParts.find((p) => p.type === "hour")?.value;
  const startMinute = startParts.find((p) => p.type === "minute")?.value;

  const startsAtMidnightLocal = startHour === "12" && startMinute === "00"; // 12:00 AM
  const isAllDay =
    end &&
    startsAtMidnightLocal &&
    Math.abs(end.getTime() - start.getTime() - 24 * 60 * 60 * 1000) < 60 * 1000;

  if (isAllDay) return "All day";

  const fmt = new Intl.DateTimeFormat(undefined, {
    timeZone: SRQ_TZ,
    hour: "numeric",
    minute: "2-digit",
  });

  const startText = fmt.format(start);
  if (!end) return startText;

  const endText = fmt.format(end);
  return `${startText} – ${endText}`;
}

function priceLabel(isFree: boolean, priceText: string | null) {
  if (isFree) return "Free";
  if (priceText) return priceText;
  return null;
}

export default function WeeklyEvents({ start, end, title = "This week" }: Props) {
  const [data, setData] = useState<EventOccurrenceOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setError(null);
        setData(null);
        const res = await apiGet<EventOccurrenceOut[]>(
          `/api/events/range?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
        );
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [start, end]);

  const grouped = useMemo(() => {
    const map = new Map<string, EventOccurrenceOut[]>();
    for (const occ of data ?? []) {
      const key = dayKeyInSarasota(occ.start_datetime_utc);
      const arr = map.get(key) ?? [];
      arr.push(occ);
      map.set(key, arr);
    }
    // ensure each day sorted by start time
    for (const [k, arr] of map) {
      arr.sort((a, b) => a.start_datetime_utc.localeCompare(b.start_datetime_utc));
      map.set(k, arr);
    }
    // return sorted day keys
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [data]);

  if (error) {
    return (
      <div className="rounded-xl border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4 shadow-sm">
        <div className="text-sm font-semibold text-red-900 dark:text-red-300">API error</div>
        <pre className="mt-2 whitespace-pre-wrap text-sm text-red-800 dark:text-red-400">{error}</pre>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 shadow-sm">
        <div className="h-4 w-40 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="mt-4 space-y-3">
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
          <div className="h-16 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-700" />
        </div>
      </div>
    );
  }

  return (
    <section className="rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 shadow-sm">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{title}</h2>
        <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">
          {start} → {end}
        </div>
      </div>

      {data.length === 0 ? (
        <div className="mt-4 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900/50 p-4 text-sm text-gray-700 dark:text-gray-300 font-medium">
          No events found for this range.
        </div>
      ) : (
        <div className="mt-4 space-y-6">
          {grouped.map(([day, occs]) => (
            <div key={day}>
              <div className="sticky top-0 z-10 -mx-4 px-4 py-2 backdrop-blur-sm bg-white/80 dark:bg-gray-800/80">
                <div className="text-base font-bold text-gray-900 dark:text-gray-100">
                  {formatDayLabel(day)}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 font-medium">{occs.length} event{occs.length === 1 ? "" : "s"}</div>
              </div>

              <ul className="mt-3 space-y-2">
                {occs.map((occ) => {
                  const price = priceLabel(occ.event.is_free, occ.event.price_text);
                  const timeLabel = formatTimeRange(
                    occ.start_datetime_utc,
                    occ.end_datetime_utc
                  );

                  return (
                    <li
                      key={occ.id}
                      className="rounded-lg border-2 border-gray-200 dark:border-gray-700 p-3 transition hover:bg-gray-50 dark:hover:bg-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600 shadow-sm"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
                            {occ.event.title}
                          </div>
                          <div className="mt-0.5 text-sm text-gray-700 dark:text-gray-300">
                            {occ.venue ? (
                              <>
                                {occ.venue.name}
                                {occ.venue.area ? (
                                  <>
                                    <span className="text-gray-500 dark:text-gray-500"> • </span>
                                    <span className="text-gray-700 dark:text-gray-300">{occ.venue.area}</span>
                                  </>
                                ) : null}
                              </>
                            ) : (
                              <span className="text-gray-700 dark:text-gray-300">
                                {occ.location_text ?? "Location TBD"}
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="shrink-0 text-right">
                          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">{timeLabel}</div>
                          {price ? (
                            <div className="mt-0.5 inline-flex rounded-full bg-blue-100 dark:bg-blue-900/30 px-2 py-0.5 text-xs font-semibold text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-700">
                              {price}
                            </div>
                          ) : (
                            <div className="mt-0.5 text-xs text-gray-600 dark:text-gray-400">Price unknown</div>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
