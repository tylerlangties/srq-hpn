import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import { toEventRouteSegment } from "@/lib/event-display";
import {
  formatEventTime,
  getEventPriceLabel,
  getEventVenueLabel,
  getTimeOfDayLabel,
  isHappeningNow,
} from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
};

export default function FeaturedEventCard({ event }: Props) {
  const time = formatEventTime(event);
  const happeningNow = isHappeningNow(event);
  const startDate = new Date(event.start_datetime_utc);
  const timeOfDay = getTimeOfDayLabel(startDate);
  const venue = getEventVenueLabel(event);
  const priceLabel = getEventPriceLabel(event);
  const href = `/events/${encodeURIComponent(
    toEventRouteSegment({ id: event.event.id, slug: event.event.slug })
  )}`;

  const card = (
    <div className="relative flex min-h-[24rem] flex-col rounded-3xl border border-white/60 bg-gradient-to-br from-white/90 to-white/70 p-5 shadow-2xl shadow-coral/10 backdrop-blur-sm dark:border-white/10 dark:bg-gradient-to-br dark:from-white/10 dark:to-white/5 dark:shadow-none">
      <div className="absolute -top-3 -right-3 rounded-full bg-coral px-4 py-1.5 text-xs font-bold text-white shadow-lg dark:bg-gradient-to-r dark:from-purple-500 dark:to-pink-500">
        Featured
      </div>
      <div className="mb-4 h-36 rounded-2xl bg-gradient-to-br from-coral via-gulf to-palm dark:from-purple-600 dark:via-pink-500 dark:to-orange-400"></div>
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted dark:text-white/50 mb-2">
        <span className="h-2 w-2 rounded-full bg-coral dark:bg-purple-400"></span>
        {happeningNow ? "Happening Now" : `${timeOfDay} · ${time}`}
      </div>
      <h2 className="mb-2 line-clamp-2 text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
        {event.event.title}
      </h2>
      <p className="mb-3 text-sm text-muted line-clamp-3 dark:text-white/60">
        {event.event.description ?? "Live music and coastal vibes to kick off the night."}
      </p>
      <div className="mt-auto flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-sand grid place-items-center dark:bg-white/10">
            <svg className="w-4 h-4 text-muted dark:text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span className="text-sm text-muted line-clamp-1 dark:text-white/60">{venue}</span>
        </div>
        <span className="rounded-full bg-palm/10 px-3 py-1 text-sm font-semibold text-palm dark:bg-emerald-500/20 dark:text-emerald-400">
          {priceLabel === "Event" ? "Tickets" : priceLabel}
        </span>
      </div>
    </div>
  );

  return (
    <Link href={href} className="block">
      {card}
    </Link>
  );
}
