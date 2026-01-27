"use client";

import { useMemo, useState } from "react";
import AppLayout from "../components/AppLayout";
import EventCardLarge from "../components/home/EventCardLarge";
import { useEventsForRange } from "../hooks/useEvents";
import { addDays, toYmd } from "@/lib/dates";

export default function EventsPage() {
  const today = new Date();
  const start = toYmd(today);
  const end = toYmd(addDays(today, 6));

  const events = useEventsForRange(start, end);
  const [showFreeOnly, setShowFreeOnly] = useState(false);

  const filteredEvents = useMemo(() => {
    if (!events.data) return null;
    if (!showFreeOnly) return events.data;
    return events.data.filter((event) => event.event.is_free);
  }, [events.data, showFreeOnly]);

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Events in Sarasota
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            A curated list of what’s happening over the next 7 days.
          </p>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          <button className="rounded-full bg-charcoal px-4 py-2 text-sm font-semibold text-white dark:bg-white/10">
            Next 7 days
          </button>
          <button
            type="button"
            onClick={() => setShowFreeOnly((prev) => !prev)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              showFreeOnly
                ? "bg-charcoal text-white dark:bg-white/10 dark:text-white"
                : "border border-charcoal/10 text-charcoal dark:border-white/20 dark:text-white"
            }`}
          >
            Free events
          </button>
          <button
            type="button"
            disabled
            className="rounded-full border border-charcoal/10 px-4 py-2 text-sm font-semibold text-muted/70 dark:border-white/20 dark:text-white/40 cursor-not-allowed"
          >
            Family-friendly
          </button>
        </div>

        {events.error ? (
          <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-sm text-red-700 dark:text-red-300">
            {events.error}
          </div>
        ) : events.loading ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {[0, 1, 2, 3].map((key) => (
              <div
                key={key}
                className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
              />
            ))}
          </div>
        ) : filteredEvents && filteredEvents.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {filteredEvents.map((event) => (
              <EventCardLarge key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted dark:text-white/60">
            {showFreeOnly
              ? "No free events found for the next week."
              : "No events found for the next week."}
          </p>
        )}
      </div>
    </AppLayout>
  );
}
