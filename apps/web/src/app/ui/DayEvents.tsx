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
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-red-800">API error</p>
            <p className="mt-1 text-sm text-red-700">
              Something went wrong while fetching events.
            </p>
          </div>
        </div>

        <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-white/70 p-3 text-xs text-red-900">
          {error}
        </pre>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="h-4 w-40 animate-pulse rounded bg-zinc-200" />
          <div className="h-3 w-24 animate-pulse rounded bg-zinc-200" />
        </div>

        <div className="mt-4 space-y-3">
          <div className="h-16 animate-pulse rounded-lg bg-zinc-100" />
          <div className="h-16 animate-pulse rounded-lg bg-zinc-100" />
          <div className="h-16 animate-pulse rounded-lg bg-zinc-100" />
        </div>
      </div>
    );
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white">
      <header className="flex items-center justify-between gap-3 border-b border-zinc-200 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">Events</h2>
          <p className="text-xs text-zinc-500">For {day}</p>
        </div>

        <span className="rounded-full border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs text-zinc-600">
          {data.length} {data.length === 1 ? "event" : "events"}
        </span>
      </header>

      {data.length === 0 ? (
        <div className="px-4 py-6">
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-4">
            <p className="text-sm font-medium text-zinc-800">
              Nothing scheduled yet
            </p>
            <p className="mt-1 text-sm text-zinc-600">
              Try a different day, or check back later.
            </p>
          </div>
        </div>
      ) : (
        <ul className="divide-y divide-zinc-100">
          {data.map((occ) => {
            const start = formatLocalTime(occ.start_datetime_utc);
            const end = occ.end_datetime_utc
              ? formatLocalTime(occ.end_datetime_utc)
              : null;

            return (
              <li key={occ.id} className="px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-zinc-900">
                      {occ.event.title}
                    </p>

                    <p className="mt-1 text-sm text-zinc-600">
                      <span className="font-medium text-zinc-700">
                        {occ.venue.name}
                      </span>
                      <span className="text-zinc-400"> • </span>
                      <span>{occ.venue.area ?? "Sarasota"}</span>
                    </p>

                    <p className="mt-2 text-xs text-zinc-500">
                      {start}
                      {end ? ` → ${end}` : ""}
                    </p>
                  </div>

                  <div className="shrink-0 text-right">
                    {occ.event.is_free ? (
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
                        Free
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700 ring-1 ring-inset ring-zinc-200">
                        {occ.event.price_text ?? "Paid"}
                      </span>
                    )}

                    {occ.event.status !== "scheduled" ? (
                      <p className="mt-2 text-xs font-medium text-red-600">
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
