import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import { formatEventTime, getTimeOfDayLabel, isHappeningNow } from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
};

export default function FeaturedEventCard({ event }: Props) {
  const time = formatEventTime(event);
  const happeningNow = isHappeningNow(event);
  const startDate = new Date(event.start_datetime_utc);
  const timeOfDay = getTimeOfDayLabel(startDate);
  const venue = event.venue?.name ?? event.location_text ?? "Location TBA";
  const href = event.event.external_url ?? "/events";
  const isExternal = Boolean(event.event.external_url);

  const card = (
    <div className="relative rounded-3xl bg-gradient-to-br from-white/90 to-white/70 border border-white/60 p-6 shadow-2xl shadow-coral/10 backdrop-blur-sm dark:bg-gradient-to-br dark:from-white/10 dark:to-white/5 dark:border-white/10 dark:shadow-none">
      <div className="absolute -top-3 -right-3 rounded-full bg-coral px-4 py-1.5 text-xs font-bold text-white shadow-lg dark:bg-gradient-to-r dark:from-purple-500 dark:to-pink-500">
        Featured
      </div>
      <div className="h-44 rounded-2xl bg-gradient-to-br from-coral via-gulf to-palm mb-5 dark:from-purple-600 dark:via-pink-500 dark:to-orange-400"></div>
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted dark:text-white/50 mb-2">
        <span className="h-2 w-2 rounded-full bg-coral dark:bg-purple-400"></span>
        {happeningNow ? "Happening Now" : `${timeOfDay} · ${time}`}
      </div>
      <h2 className="text-2xl font-[var(--font-heading)] font-semibold mb-2 text-charcoal dark:text-white">
        {event.event.title}
      </h2>
      <p className="text-sm text-muted dark:text-white/60 mb-4 line-clamp-5">
        {event.event.description ?? "Live music and coastal vibes to kick off the night."}
      </p>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-sand grid place-items-center dark:bg-white/10">
            <svg className="w-4 h-4 text-muted dark:text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span className="text-sm text-muted dark:text-white/60">{venue}</span>
        </div>
        <span className="rounded-full bg-palm/10 px-3 py-1 text-sm font-semibold text-palm dark:bg-emerald-500/20 dark:text-emerald-400">
          {event.event.is_free ? "Free" : event.event.price_text ?? "Tickets"}
        </span>
      </div>
    </div>
  );

  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className="block">
        {card}
      </a>
    );
  }

  return (
    <Link href={href} className="block">
      {card}
    </Link>
  );
}
