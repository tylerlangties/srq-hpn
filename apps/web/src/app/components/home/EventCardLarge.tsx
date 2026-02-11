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
    "group flex h-full min-h-44 cursor-pointer flex-col rounded-2xl border p-4 transition-all backdrop-blur-sm";

  const bgClasses = featured
    ? `bg-gradient-to-r ${toneClasses} border-2 hover:shadow-lg`
    : "bg-white/80 border border-white/60 hover:bg-white hover:shadow-md dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10 dark:hover:border-white/20";

  const card = (
    <article className={`${baseClasses} ${bgClasses}`}>
      <div className="flex flex-1 flex-col gap-3 md:flex-row md:items-stretch">
        <div className="flex min-w-0 flex-1 items-start gap-4">
          <div
            className={`h-14 w-14 rounded-xl grid place-items-center text-white shadow-lg flex-shrink-0 ${
              tone === "palm"
                ? "bg-palm dark:bg-gradient-to-br dark:from-emerald-500 dark:to-teal-500"
                : "bg-coral dark:bg-gradient-to-br dark:from-purple-600 dark:to-pink-500"
            }`}
          >
            <span className="text-xs font-medium">
              {time.includes("AM") ? "AM" : "PM"}
            </span>
            <span className="text-sm font-bold -mt-1">
              {time.split(":")[0]}
            </span>
          </div>
          <div className="flex h-full min-w-0 flex-1 flex-col">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="line-clamp-2 text-lg font-[var(--font-heading)] font-bold text-charcoal transition group-hover:text-coral dark:text-white dark:group-hover:text-purple-300">
                {event.event.title}
              </h3>
              {featured ? (
                <span className="text-xs font-medium text-coral bg-coral/10 px-2 py-0.5 rounded-full dark:text-purple-300 dark:bg-purple-500/20">
                  Featured
                </span>
              ) : null}
            </div>
            <p className="mb-2 text-sm text-muted line-clamp-2 dark:text-white/50">
              {event.event.description ?? "Details coming soon."}
            </p>
            <div className="mt-auto flex flex-wrap items-center gap-2 text-xs text-muted dark:text-white/40">
              <span className="max-w-full truncate">📍 {venue}</span>
              <span>·</span>
              <span className="truncate">{area}</span>
              <span>·</span>
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
    <Link href={href} className="block h-full">
      {card}
    </Link>
  );
}
