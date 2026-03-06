import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import { toEventRouteSegment } from "@/lib/event-display";
import {
  formatDayLabel,
  formatEventTime,
  getEventAreaLabel,
  getEventPriceLabel,
  getEventVenueLabel,
} from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
  featured?: boolean;
  tone?: "coral" | "palm";
};

export default function EventCardLarge({ event, featured, tone = "coral" }: Props) {
  const startDate = new Date(event.start_datetime_utc);
  const weekdayShort = startDate.toLocaleDateString("en-US", {
    weekday: "short",
    timeZone: "America/New_York",
  });
  const dayOfMonth = startDate.toLocaleDateString("en-US", {
    day: "numeric",
    timeZone: "America/New_York",
  });
  const dayLabel = formatDayLabel(event);
  const time = formatEventTime(event);
  const venue = getEventVenueLabel(event);
  const area = getEventAreaLabel(event);
  const priceLabel = getEventPriceLabel(event);
  const href = `/events/${encodeURIComponent(
    toEventRouteSegment({ id: event.event.id, slug: event.event.slug })
  )}`;

  const toneClasses =
    tone === "palm"
      ? "from-palm/8 to-gulf/8 border-palm/25 hover:shadow-gulf/10 dark:from-emerald-600/10 dark:to-cyan-600/10 dark:border-emerald-500/30"
      : "from-coral/8 to-gulf/8 border-coral/25 hover:shadow-gulf/10 dark:from-coral-500/10 dark:to-cyan-600/10 dark:border-coral-400/30";

  const baseClasses =
    "group flex h-full w-full max-w-full min-h-40 cursor-pointer flex-col overflow-hidden rounded-2xl border p-3 transition-all backdrop-blur-sm md:min-h-44 md:p-4";

  const bgClasses = featured
    ? `bg-gradient-to-r ${toneClasses} border-2 hover:shadow-lg`
    : "bg-white/80 border border-white/60 hover:bg-white hover:shadow-md dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10 dark:hover:border-white/20";

  const card = (
    <article className={`${baseClasses} ${bgClasses}`}>
      <div className="flex flex-1 flex-col gap-3 md:flex-row md:items-stretch">
        <div className="flex min-w-0 flex-1 items-start gap-3 md:gap-4">
          <div
            className={`h-12 w-12 rounded-xl grid place-items-center text-white shadow-sm flex-shrink-0 md:h-14 md:w-14 ${
              tone === "palm"
                ? "bg-gradient-to-br from-palm to-gulf dark:from-emerald-500 dark:to-cyan-500"
                : "bg-gradient-to-br from-coral to-[#ff7b3d] dark:from-purple-600 dark:to-pink-500"
            }`}
          >
            <span className="text-[10px] font-semibold uppercase tracking-wide opacity-90 md:text-xs">
              {weekdayShort}
            </span>
            <span className="-mt-1 text-sm font-bold md:text-base">
              {dayOfMonth}
            </span>
          </div>
          <div className="flex h-full min-w-0 flex-1 flex-col">
            <div className="mb-1 flex flex-wrap items-start gap-2">
              <h3 className="min-w-0 flex-1 line-clamp-2 break-words text-base font-[var(--font-heading)] font-bold text-charcoal transition group-hover:text-gulf md:text-lg dark:text-white dark:group-hover:text-cyan-300">
                {event.event.title}
              </h3>
              {featured ? (
                <span className="shrink-0 rounded-full bg-gulf/10 px-2 py-0.5 text-xs font-medium text-gulf dark:bg-cyan-500/20 dark:text-cyan-300">
                  Featured
                </span>
              ) : null}
            </div>
            <p className="mb-2 text-xs font-medium tracking-wide text-muted dark:text-white/55">
              {dayLabel} · {time}
            </p>
            <p className="mb-2 line-clamp-2 break-words text-sm text-muted dark:text-white/50">
              {event.event.description ?? "Details coming soon."}
            </p>
            <div className="mt-auto flex min-w-0 flex-wrap items-center gap-2 text-xs text-muted dark:text-white/60">
              <span className="max-w-full min-w-0 truncate rounded-full bg-sand/70 px-2.5 py-0.5 text-charcoal dark:bg-white/10 dark:text-white/75">
                {venue}
              </span>
              <span className="max-w-full min-w-0 truncate rounded-full bg-sand/70 px-2.5 py-0.5 text-charcoal dark:bg-white/10 dark:text-white/75">
                {area}
              </span>
              <span className="rounded-full bg-sand px-2.5 py-0.5 text-charcoal dark:bg-white/10 dark:text-white/75">
                {priceLabel}
              </span>
            </div>
          </div>
        </div>
        <span className="hidden self-center rounded-full border border-gulf/25 bg-sand px-4 py-2 text-sm font-semibold text-gulf shadow-sm transition-all duration-200 group-hover:-translate-y-0.5 group-hover:bg-sand/80 group-hover:shadow-md group-hover:shadow-gulf/20 md:inline-flex dark:border-cyan-500/30 dark:bg-white/10 dark:text-cyan-300 dark:group-hover:bg-white/15 dark:group-hover:shadow-cyan-500/20">
          <span>Details</span>
          <span className="ml-1 transition-transform duration-200 group-hover:translate-x-0.5">→</span>
        </span>
      </div>
    </article>
  );

  return (
    <Link href={href} className="block h-full w-full min-w-0">
      {card}
    </Link>
  );
}
