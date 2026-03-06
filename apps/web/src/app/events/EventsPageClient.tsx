"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import AppLayout from "../components/AppLayout";
import EventCardLarge from "../components/home/EventCardLarge";
import EventLoadError from "../components/home/EventLoadError";
import { useCategories, useEventsForRange } from "../hooks/useEvents";
import { useVenues } from "../hooks/useVenues";
import EventsFiltersFresh from "./EventsFiltersFresh";
import { addDays, toYmd } from "@/lib/dates";
import type { EventOccurrenceOut, EventRangeSort } from "@/types/events";

const SORT_OPTIONS: Array<{ value: EventRangeSort; label: string }> = [
  { value: "date_asc", label: "Soonest" },
  { value: "date_desc", label: "Latest" },
  { value: "title_asc", label: "Title A-Z" },
  { value: "title_desc", label: "Title Z-A" },
];

function groupEventsByDay(events: EventOccurrenceOut[]) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
    timeZone: "America/New_York",
  });
  const grouped = new Map<string, { label: string; items: EventOccurrenceOut[] }>();
  for (const event of events) {
    const date = new Date(event.start_datetime_utc);
    const key = date.toLocaleDateString("en-CA", { timeZone: "America/New_York" });
    const existing = grouped.get(key);
    if (existing) {
      existing.items.push(event);
      continue;
    }
    grouped.set(key, { label: formatter.format(date), items: [event] });
  }
  return [...grouped.entries()].map(([key, value]) => ({ key, ...value }));
}

export default function EventsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [showAllCategories, setShowAllCategories] = useState(false);
  const resultsTopRef = useRef<HTMLDivElement | null>(null);
  const paginationScrollPendingRef = useRef(false);

  const today = new Date();
  const defaultStart = toYmd(today);
  const defaultEnd = toYmd(addDays(today, 6));
  const daysUntilFriday = (5 - today.getDay() + 7) % 7;
  const upcomingFriday = addDays(today, daysUntilFriday);
  const weekendStart = toYmd(upcomingFriday);
  const weekendEnd = toYmd(addDays(upcomingFriday, 2));

  const start = searchParams.get("start") ?? defaultStart;
  const end = searchParams.get("end") ?? defaultEnd;
  const selectedCategory = searchParams.get("category") ?? "";
  const selectedVenue = searchParams.get("venue") ?? "";
  const showFreeOnly = searchParams.get("free") === "true";
  const sortParam = searchParams.get("sort");
  const selectedSort = SORT_OPTIONS.some((option) => option.value === sortParam)
    ? (sortParam as EventRangeSort)
    : "date_asc";
  const pageParam = Number(searchParams.get("page") ?? "1");
  const currentPage = Number.isFinite(pageParam) && pageParam > 0 ? Math.floor(pageParam) : 1;
  const viewMode = searchParams.get("view") === "day" ? "day" : "list";
  const hasActiveFilters =
    showFreeOnly ||
    selectedCategory.length > 0 ||
    selectedVenue.length > 0 ||
    start !== defaultStart ||
    end !== defaultEnd ||
    selectedSort !== "date_asc";
  const isWeekendPresetActive =
    start === weekendStart && end === weekendEnd && viewMode === "day";

  const categories = useCategories();
  const venues = useVenues();

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

  const applyPagination = (nextPage: number) => {
    paginationScrollPendingRef.current = true;
    applySearchParamPatch({ page: String(nextPage) });
  };

  useEffect(() => {
    if (!paginationScrollPendingRef.current) {
      return;
    }
    paginationScrollPendingRef.current = false;
    resultsTopRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [currentPage]);

  const applyWeekendPreset = () => {
    if (isWeekendPresetActive) {
      applySearchParamPatch({
        start: null,
        end: null,
        page: null,
      });
      return;
    }

    applySearchParamPatch({
      start: weekendStart,
      end: weekendEnd,
      view: "day",
      page: null,
    });
  };

  const events = useEventsForRange(start, end, {
    category: selectedCategory || null,
    freeOnly: showFreeOnly ? true : null,
    venue: selectedVenue || null,
    sort: selectedSort,
    page: currentPage,
    pageSize: 20,
  });

  const displayedCategories = useMemo(() => {
    if (!categories.data || categories.data.length === 0) {
      return [];
    }
    if (showAllCategories) {
      return categories.data;
    }
    return categories.data.slice(0, 6);
  }, [categories.data, showAllCategories]);

  const groupedEvents = useMemo(() => {
    if (!events.data || events.data.length === 0) {
      return [];
    }
    return groupEventsByDay(events.data);
  }, [events.data]);

  const totalPages = events.totalPages ?? 0;
  const isFirstPage = currentPage <= 1;
  const isLastPage = totalPages > 0 && currentPage >= totalPages;
  const hasMoreCategories = (categories.data?.length ?? 0) > 6;

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

        <EventsFiltersFresh
          start={start}
          end={end}
          selectedVenue={selectedVenue}
          selectedSort={selectedSort}
          showFreeOnly={showFreeOnly}
          viewMode={viewMode}
          selectedCategory={selectedCategory}
          displayedCategories={displayedCategories}
          hasMoreCategories={hasMoreCategories}
          showAllCategories={showAllCategories}
          venues={venues.data ?? []}
          sortOptions={SORT_OPTIONS}
          isWeekendPresetActive={isWeekendPresetActive}
          onPatch={applySearchParamPatch}
          onApplyWeekendPreset={applyWeekendPreset}
          onToggleShowAllCategories={() => setShowAllCategories((value) => !value)}
        />

        {events.data && events.data.length > 0 ? (
          <p className="mb-4 text-sm text-muted dark:text-white/60">
            Showing {(currentPage - 1) * 20 + 1}-{(currentPage - 1) * 20 + events.data.length} of {events.total ?? events.data.length} events
          </p>
        ) : null}

        <div ref={resultsTopRef} className="scroll-mt-24" />

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
          viewMode === "day" ? (
            <div className="space-y-8">
              {groupedEvents.map((group) => (
                <section key={group.key}>
                  <h2 className="mb-3 text-xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
                    {group.label}
                  </h2>
                  <div className="grid gap-4 lg:grid-cols-2">
                    {group.items.map((event) => (
                      <EventCardLarge key={event.id} event={event} />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {events.data.map((event) => (
                <EventCardLarge key={event.id} event={event} />
              ))}
            </div>
          )
        ) : (
          <div className="rounded-2xl border border-charcoal/10 bg-white/75 p-5 dark:border-white/15 dark:bg-white/5">
            <p className="text-base font-semibold text-charcoal dark:text-white">
              {showFreeOnly
                ? "No free events in this range yet"
                : "No events found in this range"}
            </p>
            <p className="mt-1 text-sm text-muted dark:text-white/60">
              Try broadening your filters or switching your date range to discover more options.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {hasActiveFilters ? (
                <button
                  type="button"
                  onClick={() =>
                    applySearchParamPatch({
                      free: null,
                      category: null,
                      venue: null,
                      start: null,
                      end: null,
                      sort: null,
                      page: null,
                    })
                  }
                  className="rounded-full bg-charcoal px-4 py-2 text-sm font-semibold text-white transition hover:bg-charcoal/90 dark:bg-white/10 dark:hover:bg-white/15"
                >
                  Reset filters
                </button>
              ) : null}
              <Link
                href="/venues"
                className="rounded-full border border-charcoal/10 bg-white/70 px-4 py-2 text-sm font-semibold text-charcoal transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
              >
                Browse venues
              </Link>
            </div>
          </div>
        )}

        {events.data && events.data.length > 0 && totalPages > 1 ? (
          <div className="mt-8 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-charcoal/10 bg-white/70 p-4 dark:border-white/15 dark:bg-white/5">
            <p className="text-sm text-muted dark:text-white/60">
              Page {currentPage} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={isFirstPage}
                onClick={() => applyPagination(currentPage - 1)}
                className="rounded-full border border-charcoal/15 px-4 py-2 text-sm font-semibold text-charcoal transition enabled:hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/20 dark:text-white dark:enabled:hover:bg-white/10"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={isLastPage}
                onClick={() => applyPagination(currentPage + 1)}
                className="rounded-full border border-charcoal/15 px-4 py-2 text-sm font-semibold text-charcoal transition enabled:hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/20 dark:text-white dark:enabled:hover:bg-white/10"
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </AppLayout>
  );
}
