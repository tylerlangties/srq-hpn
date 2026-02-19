import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import type { WeatherPayload } from "@/lib/weather";
import FeaturedEventCard from "./FeaturedEventCard";
import SurpriseMeButton from "./SurpriseMeButton";
import WeatherWidget from "./WeatherWidget";

type Props = {
  featuredEvent: EventOccurrenceOut | null;
  eventsThisWeekCount: number | null;
  eventsThisWeekError?: string | null;
  weather: WeatherPayload | null;
  weatherLoading?: boolean;
  weatherError?: string | null;
};

export default function HeroSection({
  featuredEvent,
  eventsThisWeekCount,
  eventsThisWeekError,
  weather,
  weatherLoading,
  weatherError,
}: Props) {
  const eventsThisWeekLabel =
    eventsThisWeekCount === null
      ? "Events this week in Sarasota"
      : `${eventsThisWeekCount} ${eventsThisWeekCount === 1 ? "Event" : "Events"} this week in Sarasota`;

  return (
    <section className="py-12 md:py-16">
      <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] items-center">
        <div className="space-y-6 fade-up delay-1">
          {!eventsThisWeekError ? (
            <div className="inline-flex items-center gap-2 rounded-full bg-white/80 dark:bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-muted dark:text-emerald-400 shadow-sm border border-white/60 dark:border-emerald-500/30">
              <span className="h-2 w-2 rounded-full bg-coral dark:bg-emerald-500 animate-pulse"></span>
              {eventsThisWeekLabel}
            </div>
          ) : null}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-[var(--font-heading)] leading-[1.1] text-charcoal dark:text-white">
            Discover what&apos;s{" "}
            <span className="text-coral dark:bg-gradient-to-r dark:from-purple-400 dark:via-pink-400 dark:to-orange-400 dark:bg-clip-text dark:text-transparent">
              happening
            </span>{" "}
            in the Suncoast
          </h1>
          <p className="max-w-xl text-lg text-muted dark:text-white/60 leading-relaxed">
           A curated guide to festivals, live music, art walks, food pop-ups,
            and everything in between.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <Link
              href="/events"
              className="inline-flex w-full items-center justify-center rounded-full bg-coral px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-coral/40 transition-all hover:translate-y-[-2px] hover:shadow-coral/50 sm:w-auto sm:px-7 sm:py-3.5 dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600 dark:shadow-purple-500/30"
            >
              Browse events
            </Link>
            <SurpriseMeButton days={7} />
          </div>
        </div>

        <div className="fade-up delay-2">
          {featuredEvent ? (
            <FeaturedEventCard event={featuredEvent} />
          ) : (
            <WeatherWidget
              weather={weather}
              loading={weatherLoading}
              error={weatherError}
            />
          )}
        </div>
      </div>
    </section>
  );
}
