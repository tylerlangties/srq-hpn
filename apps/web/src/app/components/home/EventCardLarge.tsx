import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import { toEventRouteSegment } from "@/lib/event-display";
import {
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
  const time = formatEventTime(event);
  const venue = getEventVenueLabel(event);
  const area = getEventAreaLabel(event);
  const priceLabel = getEventPriceLabel(event);
  const href = `/events/${encodeURIComponent(
    toEventRouteSegment({ id: event.event.id, slug: event.event.slug })
  )}`;

  const toneClasses =
    tone === "palm"
      ? "from-palm/10 to-gulf/10 border-palm/30 hover:shadow-palm/10 dark:from-emerald-600/10 dark:to-teal-600/10 dark:border-emerald-500/30"
      : "from-coral/10 to-gulf/10 border-coral/30 hover:shadow-coral/10 dark:from-purple-600/10 dark:to-pink-600/10 dark:border-purple-500/30";

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
            className={`h-12 w-12 rounded-xl grid place-items-center text-white shadow-lg flex-shrink-0 md:h-14 md:w-14 ${
              tone === "palm"
                ? "bg-palm dark:bg-gradient-to-br dark:from-emerald-500 dark:to-teal-500"
                : "bg-coral dark:bg-gradient-to-br dark:from-purple-600 dark:to-pink-500"
            }`}
          >
            <span className="text-xs font-medium">
              {time.includes("AM") ? "AM" : "PM"}
            </span>
            <span className="-mt-1 text-xs font-bold md:text-sm">
              {time.split(":")[0]}
            </span>
          </div>
          <div className="flex h-full min-w-0 flex-1 flex-col">
            <div className="mb-1 flex flex-wrap items-start gap-2">
              <h3 className="min-w-0 flex-1 line-clamp-2 break-words text-base font-[var(--font-heading)] font-bold text-charcoal transition group-hover:text-coral md:text-lg dark:text-white dark:group-hover:text-purple-300">
                {event.event.title}
              </h3>
              {featured ? (
                <span className="shrink-0 rounded-full bg-coral/10 px-2 py-0.5 text-xs font-medium text-coral dark:bg-purple-500/20 dark:text-purple-300">
                  Featured
                </span>
              ) : null}
            </div>
            <p className="mb-2 line-clamp-2 break-words text-sm text-muted dark:text-white/50">
              {event.event.description ?? "Details coming soon."}
            </p>
            <div className="mt-auto flex min-w-0 flex-col items-start gap-1 text-xs text-muted md:flex-row md:flex-wrap md:items-center md:gap-2 dark:text-white/60">
              <span className="block max-w-full min-w-0 truncate">📍 {venue}</span>
              <span className="hidden md:inline">·</span>
              <span className="block max-w-full min-w-0 truncate">{area}</span>
              <span className="hidden md:inline">·</span>
              <span className="rounded-full bg-sand px-2 py-0.5 text-charcoal dark:bg-white/10 dark:text-white/60">
                {priceLabel}
              </span>
            </div>
          </div>
        </div>
        <span className="hidden self-center rounded-full border border-charcoal/10 bg-white/70 px-4 py-2 text-sm font-medium text-charcoal transition hover:bg-white md:inline-flex dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">
          Details →
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
