"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import AppLayout from "./components/AppLayout";
import HeroSection from "./components/home/HeroSection";
import SectionHeader from "./components/home/SectionHeader";
import EventCardLarge from "./components/home/EventCardLarge";
import EventCardCompact from "./components/home/EventCardCompact";
import ArticlesSection from "./components/home/ArticlesSection";
import NewsletterCTA from "./components/home/NewsletterCTA";
import {
  useEventsForDay,
  useEventsForRange,
  useEventsThisWeekCount,
} from "./hooks/useEvents";
import { useWeather } from "./hooks/useWeather";
import { addDays, startOfWeekend, toYmd } from "@/lib/dates";

type EventsState = ReturnType<typeof useEventsForDay>;

function formatWeatherLine(temp: number | null, condition: string) {
  const tempLabel = temp === null ? "—" : `${temp}°`;
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
    return (
      <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-sm text-red-700 dark:text-red-300">
        {state.error}
      </div>
    );
  }

  if (state.loading) {
    return loading;
  }

  if (state.data && state.data.length > 0) {
    return render(state.data);
  }

  return <p className="text-sm text-muted dark:text-white/50">{emptyMessage}</p>;
}

export default function HomePage() {
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
      <div className="relative z-10 mx-auto w-full max-w-7xl px-6">
        <HeroSection
          featuredEvent={featuredEvent}
          eventsThisWeekCount={eventsThisWeek.data}
          weather={weather.data}
          weatherLoading={weather.loading}
          weatherError={weather.error}
        />

        <section className="py-8 border-t border-white/50 dark:border-white/10">
          <SectionHeader
            title="Today"
            subtitle={todaySubtitle}
            icon="✦"
            tone="coral"
          />

          {renderEventsSection(
            todayEvents,
            <div className="grid gap-4 lg:grid-cols-2">
              {[0, 1].map((key) => (
                <div
                  key={key}
                  className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
                />
              ))}
            </div>,
            (events) => (
              <div className="grid gap-4 lg:grid-cols-2">
                {events.map((event, index) => (
                  <EventCardLarge
                    key={event.id}
                    event={event}
                    featured={index === 0}
                    tone="coral"
                  />
                ))}
              </div>
            ),
            "No events found today. Check back soon."
          )}
        </section>

        <section className="py-8 border-t border-white/50 dark:border-white/10">
          <SectionHeader
            title="Tomorrow"
            subtitle={tomorrowSubtitle}
            icon="☀"
            tone="palm"
          />

          {renderEventsSection(
            tomorrowEvents,
            <div className="grid gap-4 lg:grid-cols-2">
              {[0, 1].map((key) => (
                <div
                  key={key}
                  className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
                />
              ))}
            </div>,
            (events) => (
              <div className="grid gap-4 lg:grid-cols-2">
                {events.map((event, index) => (
                  <EventCardLarge
                    key={event.id}
                    event={event}
                    featured={index === 0}
                    tone="palm"
                  />
                ))}
              </div>
            ),
            "No events found tomorrow. Check back soon."
          )}
        </section>

        <section className="py-8 border-t border-white/50 dark:border-white/10">
          <SectionHeader
            title="This Weekend"
            subtitle={weekendSubtitle}
            icon="◈"
            tone="gulf"
            action={
              <Link
                href="/events"
                className="text-sm font-medium text-gulf hover:text-gulf/80 transition flex items-center gap-1 dark:text-purple-300 dark:hover:text-purple-200"
              >
                See all events
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            }
          />

          {renderEventsSection(
            weekendEvents,
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[0, 1, 2, 3].map((key) => (
                <div
                  key={key}
                  className="h-40 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
                />
              ))}
            </div>,
            (events) => (
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {events.slice(0, 4).map((event) => (
                  <EventCardCompact key={event.id} event={event} />
                ))}
              </div>
            ),
            "No weekend events found yet."
          )}
        </section>

        <ArticlesSection />
        <NewsletterCTA />
      </div>
    </AppLayout>
  );
}
