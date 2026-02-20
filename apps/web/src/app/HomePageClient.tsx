"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import AppLayout from "./components/AppLayout";
import HeroSection from "./components/home/HeroSection";
import SectionHeader from "./components/home/SectionHeader";
import EventCardLarge from "./components/home/EventCardLarge";
import EventCardCompact from "./components/home/EventCardCompact";
import EventLoadError from "./components/home/EventLoadError";
import ArticlesSection from "./components/home/ArticlesSection";
import { useEventsForDay, useEventsForRange, useEventsThisWeekCount } from "./hooks/useEvents";
import { useWeather } from "./hooks/useWeather";
import { addDays, startOfWeekend, toYmd } from "@/lib/dates";
import { SHARED_RESPONSIVE } from "@/lib/responsive";

type EventsState = ReturnType<typeof useEventsForDay>;

function formatWeatherLine(temp: number | null, condition: string) {
  const tempLabel = temp === null ? "-" : `${temp}°`;
  return `${tempLabel} and ${condition}`;
}

function weatherSubtitle(
  label: string,
  temp: number | null,
  condition: string,
  loading: boolean,
  error: string | null
) {
  if (error) {
    return `${label} · Forecast took a beach day`;
  }

  if (loading) {
    return `${label} · Weather loading`;
  }

  return `${label} · ${formatWeatherLine(temp, condition)}`;
}

function renderEventsSection(
  state: EventsState,
  loading: ReactNode,
  render: (events: NonNullable<EventsState["data"]>) => ReactNode,
  emptyMessage: string
) {
  if (state.error) {
    return <EventLoadError message={state.error} />;
  }

  if (state.loading) {
    return loading;
  }

  if (state.data && state.data.length > 0) {
    return render(state.data);
  }

  return <p className="text-sm text-muted dark:text-white/50">{emptyMessage}</p>;
}

export default function HomePageClient() {
  const today = new Date();
  const tomorrow = addDays(today, 1);
  const weekendStart = startOfWeekend(today);
  const weekendEnd = addDays(weekendStart, 1);

  const todayYmd = toYmd(today);
  const tomorrowYmd = toYmd(tomorrow);
  const weekendStartYmd = toYmd(weekendStart);
  const weekendEndYmd = toYmd(weekendEnd);

  const todayEvents = useEventsForDay(todayYmd);
  const tomorrowEvents = useEventsForDay(tomorrowYmd);
  const weekendEvents = useEventsForRange(weekendStartYmd, weekendEndYmd);
  const eventsThisWeek = useEventsThisWeekCount();
  const weather = useWeather();

  const featuredEvent = todayEvents.data?.[0] ?? null;
  const todaySubtitle = weather.data
    ? weatherSubtitle(
        "Today",
        weather.data.today.temp,
        weather.data.today.condition,
        weather.loading,
        weather.error
      )
    : weatherSubtitle("Today", null, "pleasant", weather.loading, weather.error);

  const tomorrowSubtitle = weather.data
    ? weatherSubtitle(
        "Tomorrow",
        weather.data.tomorrow.temp,
        weather.data.tomorrow.condition,
        weather.loading,
        weather.error
      )
    : weatherSubtitle("Tomorrow", null, "pleasant", weather.loading, weather.error);

  const weekendSubtitle = weather.data
    ? weatherSubtitle(
        "Weekend",
        weather.data.weekend.temp,
        weather.data.weekend.condition,
        weather.loading,
        weather.error
      )
    : weatherSubtitle("Weekend", null, "pleasant", weather.loading, weather.error);

  return (
    <AppLayout showAmbient>
      <div className={`relative z-10 mx-auto w-full max-w-7xl ${SHARED_RESPONSIVE.containerInset}`}>
        <HeroSection
          featuredEvent={featuredEvent}
          eventsThisWeekCount={eventsThisWeek.data}
          eventsThisWeekError={eventsThisWeek.error}
          weather={weather.data}
          weatherLoading={weather.loading}
          weatherError={weather.error}
        />

        <section className="border-t border-white/50 py-8 dark:border-white/10">
          <SectionHeader title="Today" subtitle={todaySubtitle} icon="✦" tone="coral" />

          {renderEventsSection(
            todayEvents,
            <div className="grid gap-4 lg:grid-cols-2">
              {[0, 1].map((key) => (
                <div
                  key={key}
                  className="h-28 animate-pulse rounded-2xl border border-white/60 bg-white/80 dark:border-white/10 dark:bg-white/5"
                />
              ))}
            </div>,
            (events) => (
              <div className="grid gap-4 lg:grid-cols-2">
                {events.map((event, index) => (
                  <EventCardLarge key={event.id} event={event} featured={index === 0} tone="coral" />
                ))}
              </div>
            ),
            "No events found today. Check back soon."
          )}
        </section>

        <section className="border-t border-white/50 py-8 dark:border-white/10">
          <SectionHeader title="Tomorrow" subtitle={tomorrowSubtitle} icon="☀" tone="palm" />

          {renderEventsSection(
            tomorrowEvents,
            <div className="grid gap-4 lg:grid-cols-2">
              {[0, 1].map((key) => (
                <div
                  key={key}
                  className="h-28 animate-pulse rounded-2xl border border-white/60 bg-white/80 dark:border-white/10 dark:bg-white/5"
                />
              ))}
            </div>,
            (events) => (
              <div className="grid gap-4 lg:grid-cols-2">
                {events.map((event, index) => (
                  <EventCardLarge key={event.id} event={event} featured={index === 0} tone="palm" />
                ))}
              </div>
            ),
            "No events found tomorrow. Check back soon."
          )}
        </section>

        <section className="border-t border-white/50 py-8 dark:border-white/10">
          <SectionHeader
            title="This Weekend"
            subtitle={weekendSubtitle}
            icon="◈"
            tone="gulf"
            action={
              <Link
                href="/events"
                className="flex items-center gap-1 text-sm font-medium text-gulf transition hover:text-gulf/80 dark:text-purple-300 dark:hover:text-purple-200"
              >
                See all events
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            }
          />

          {renderEventsSection(
            weekendEvents,
            <div className={SHARED_RESPONSIVE.gridTwoThenFour}>
              {[0, 1, 2, 3].map((key) => (
                <div
                  key={key}
                  className="h-40 animate-pulse rounded-2xl border border-white/60 bg-white/80 dark:border-white/10 dark:bg-white/5"
                />
              ))}
            </div>,
            (events) => (
              <div className={SHARED_RESPONSIVE.gridTwoThenFour}>
                {events.slice(0, 4).map((event) => (
                  <EventCardCompact key={event.id} event={event} />
                ))}
              </div>
            ),
            "No weekend events found yet."
          )}
        </section>

        <ArticlesSection />
      </div>
    </AppLayout>
  );
}
