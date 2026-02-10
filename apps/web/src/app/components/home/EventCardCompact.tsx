import Link from "next/link";
import type { EventOccurrenceOut } from "@/types/events";
import {
  formatDayLabel,
  formatEventTime,
  getEventVenueLabel,
} from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
};

export default function EventCardCompact({ event }: Props) {
  const time = formatEventTime(event);
  const day = formatDayLabel(event);
  const venue = getEventVenueLabel(event);
  const href = event.event.external_url ?? "/events";
  const isExternal = Boolean(event.event.external_url);

  const card = (
    <article className="group flex h-full min-h-36 cursor-pointer flex-col rounded-2xl border border-white/60 bg-white/80 p-4 transition-all hover:bg-white hover:shadow-lg hover:shadow-charcoal/5 backdrop-blur-sm dark:border-white/10 dark:bg-white/5 dark:hover:border-white/20 dark:hover:bg-white/10 dark:hover:shadow-purple-500/5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-gulf dark:bg-gradient-to-r dark:from-purple-400 dark:to-pink-400"></div>
          <p className="truncate text-xs font-medium text-muted dark:text-white/40">
            {day} · {time}
          </p>
        </div>
        {event.event.is_free ? (
          <span className="text-xs font-medium text-coral dark:text-amber-400">
            Free
          </span>
        ) : null}
      </div>
      <h3 className="mb-2 line-clamp-2 font-[var(--font-heading)] font-bold text-charcoal transition group-hover:text-coral dark:text-white dark:group-hover:text-purple-300">
        {event.event.title}
      </h3>
      <div className="mt-auto flex items-center justify-between gap-3">
        <span className="text-xs text-muted line-clamp-1 dark:text-white/40">{venue}</span>
        <span className="text-xs font-medium text-gulf dark:bg-gradient-to-r dark:from-purple-400 dark:to-pink-400 dark:bg-clip-text dark:text-transparent">
          {event.event.status === "canceled" ? "Canceled" : "Event"}
        </span>
      </div>
    </article>
  );

  if (isExternal) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className="block h-full">
        {card}
      </a>
    );
  }

  return (
    <Link href={href} className="block h-full">
      {card}
    </Link>
  );
}
