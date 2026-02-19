"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import AppLayout from "../components/AppLayout";
import EventCardLarge from "../components/home/EventCardLarge";
import EventLoadError from "../components/home/EventLoadError";
import { useCategories, useEventsForRange } from "../hooks/useEvents";
import { addDays, toYmd } from "@/lib/dates";

export default function EventsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const today = new Date();
  const defaultStart = toYmd(today);
  const defaultEnd = toYmd(addDays(today, 6));

  const start = searchParams.get("start") ?? defaultStart;
  const end = searchParams.get("end") ?? defaultEnd;
  const selectedCategory = searchParams.get("category") ?? "";
  const selectedVenue = searchParams.get("venue") ?? "";
  const showFreeOnly = searchParams.get("free") === "true";

  const categories = useCategories();

  const applySearchParamPatch = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(patch)) {
      if (value === null || value === "") {
        next.delete(key);
      } else {
        next.set(key, value);
      }
    }

    const query = next.toString();
    router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
  };

  const events = useEventsForRange(start, end, {
    category: selectedCategory || null,
    freeOnly: showFreeOnly ? true : null,
    venue: selectedVenue || null,
  });

  const displayedCategories = useMemo(() => {
    if (!categories.data || categories.data.length === 0) {
      return [];
    }
    return categories.data.slice(0, 6);
  }, [categories.data]);

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Events in Sarasota
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            A curated list of what&apos;s happening over the next 7 days.
          </p>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          <button className="rounded-full bg-charcoal px-4 py-2 text-sm font-semibold text-white dark:bg-white/10">
            Next 7 days
          </button>
          <button
            type="button"
            onClick={() => applySearchParamPatch({ free: showFreeOnly ? null : "true" })}
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

        {displayedCategories.length > 0 ? (
          <div className="mb-6 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => applySearchParamPatch({ category: null })}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                selectedCategory
                  ? "border border-charcoal/10 text-charcoal dark:border-white/20 dark:text-white"
                  : "bg-charcoal text-white dark:bg-white/10 dark:text-white"
              }`}
            >
              All categories
            </button>
            {displayedCategories.map((category) => (
              <button
                key={category.id}
                type="button"
                onClick={() => applySearchParamPatch({ category: category.slug })}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  selectedCategory === category.slug
                    ? "bg-charcoal text-white dark:bg-white/10 dark:text-white"
                    : "border border-charcoal/10 text-charcoal dark:border-white/20 dark:text-white"
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>
        ) : null}

        {events.error ? (
          <EventLoadError message={events.error} />
        ) : events.loading ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {[0, 1, 2, 3].map((key) => (
              <div
                key={key}
                className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
              />
            ))}
          </div>
        ) : events.data && events.data.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {events.data.map((event) => (
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
