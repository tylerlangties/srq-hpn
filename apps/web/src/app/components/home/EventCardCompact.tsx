import type { EventOccurrenceOut } from "@/types/events";
import { formatEventTime, formatDayLabel } from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
};

export default function EventCardCompact({ event }: Props) {
  const time = formatEventTime(event);
  const day = formatDayLabel(event);
  const venue = event.venue?.name ?? event.location_text ?? "Location TBA";

  return (
    <article className="group rounded-2xl bg-white/80 border border-white/60 p-4 hover:bg-white hover:shadow-lg hover:shadow-charcoal/5 transition-all cursor-pointer backdrop-blur-sm dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10 dark:hover:border-white/20 dark:hover:shadow-purple-500/5">
      <div className="flex items-center justify-between mb-3">
        <div className="h-3 w-3 rounded-full bg-gulf dark:bg-gradient-to-r dark:from-purple-400 dark:to-pink-400"></div>
        {event.event.is_free ? (
          <span className="text-xs font-medium text-coral dark:text-amber-400">
            Free
          </span>
        ) : null}
      </div>
      <p className="text-xs font-medium text-muted dark:text-white/40 mb-1">
        {day} · {time}
      </p>
      <h3 className="font-[var(--font-heading)] font-bold text-charcoal mb-2 group-hover:text-coral transition dark:text-white dark:group-hover:text-purple-300">
        {event.event.title}
      </h3>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted dark:text-white/40">{venue}</span>
        <span className="text-xs font-medium text-gulf dark:bg-gradient-to-r dark:from-purple-400 dark:to-pink-400 dark:bg-clip-text dark:text-transparent">
          {event.event.status === "canceled" ? "Canceled" : "Event"}
        </span>
      </div>
    </article>
  );
}
