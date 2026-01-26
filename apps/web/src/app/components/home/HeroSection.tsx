import type { EventOccurrenceOut } from "@/types/events";
import type { WeatherPayload } from "@/lib/weather";
import FeaturedEventCard from "./FeaturedEventCard";
import WeatherWidget from "./WeatherWidget";

type Props = {
  featuredEvent: EventOccurrenceOut | null;
  weather: WeatherPayload | null;
  weatherLoading?: boolean;
  weatherError?: string | null;
};

export default function HeroSection({
  featuredEvent,
  weather,
  weatherLoading,
  weatherError,
}: Props) {
  return (
    <section className="py-12 md:py-16">
      <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] items-center">
        <div className="space-y-6 fade-up delay-1">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/80 dark:bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-muted dark:text-emerald-400 shadow-sm border border-white/60 dark:border-emerald-500/30">
            <span className="h-2 w-2 rounded-full bg-coral dark:bg-emerald-500 animate-pulse"></span>
            42 events this week in Sarasota
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-[var(--font-heading)] leading-[1.1] text-charcoal dark:text-white">
            Discover what&apos;s{" "}
            <span className="text-coral dark:bg-gradient-to-r dark:from-purple-400 dark:via-pink-400 dark:to-orange-400 dark:bg-clip-text dark:text-transparent">
              happening
            </span>{" "}
            in the Suncoast
          </h1>
          <p className="max-w-xl text-lg text-muted dark:text-white/60 leading-relaxed">
            Your curated guide to festivals, live music, art walks, food pop-ups,
            and everything in between. Find your next adventure.
          </p>
          <div className="flex flex-wrap gap-3">
            <button className="rounded-full bg-coral px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-coral/40 hover:shadow-coral/50 hover:translate-y-[-2px] transition-all dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600 dark:shadow-purple-500/30">
              Browse events
            </button>
            <button className="rounded-full border border-charcoal/10 bg-white/80 px-7 py-3.5 text-sm font-semibold text-charcoal shadow-sm hover:bg-white transition dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">
              Surprise me
            </button>
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
