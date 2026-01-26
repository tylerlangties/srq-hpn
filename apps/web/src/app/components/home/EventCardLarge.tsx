import type { EventOccurrenceOut } from "@/types/events";
import { formatEventTime } from "./event-utils";

type Props = {
  event: EventOccurrenceOut;
  featured?: boolean;
  tone?: "coral" | "palm";
};

export default function EventCardLarge({ event, featured, tone = "coral" }: Props) {
  const time = formatEventTime(event);
  const venue = event.venue?.name ?? event.location_text ?? "Location TBA";
  const area = event.venue?.area ?? "Sarasota";

  const toneClasses =
    tone === "palm"
      ? "from-palm/10 to-gulf/10 border-palm/30 hover:shadow-palm/10 dark:from-emerald-600/10 dark:to-teal-600/10 dark:border-emerald-500/30"
      : "from-coral/10 to-gulf/10 border-coral/30 hover:shadow-coral/10 dark:from-purple-600/10 dark:to-pink-600/10 dark:border-purple-500/30";

  const baseClasses =
    "group rounded-2xl p-5 transition-all cursor-pointer backdrop-blur-sm";

  const bgClasses = featured
    ? `bg-gradient-to-r ${toneClasses} border-2 hover:shadow-lg`
    : "bg-white/80 border border-white/60 hover:bg-white hover:shadow-md dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10 dark:hover:border-white/20";

  return (
    <article className={`${baseClasses} ${bgClasses}`}>
      <div className="flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex items-center gap-4 flex-1">
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
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-[var(--font-heading)] font-bold text-charcoal group-hover:text-coral transition dark:text-white dark:group-hover:text-purple-300">
                {event.event.title}
              </h3>
              {featured ? (
                <span className="text-xs font-medium text-coral bg-coral/10 px-2 py-0.5 rounded-full dark:text-purple-300 dark:bg-purple-500/20">
                  Featured
                </span>
              ) : null}
            </div>
            <p className="text-sm text-muted dark:text-white/50 mb-2">
              {event.event.description ?? "Details coming soon."}
            </p>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted dark:text-white/40">
              <span className="flex items-center gap-1">📍 {venue}</span>
              <span>·</span>
              <span>{area}</span>
              <span>·</span>
              <span className="rounded-full bg-sand px-2 py-0.5 text-charcoal dark:bg-white/10 dark:text-white/60">
                {event.event.is_free ? "Free" : event.event.price_text ?? "Event"}
              </span>
            </div>
          </div>
        </div>
        <button className="rounded-full border border-charcoal/10 bg-white/70 px-4 py-2 text-sm font-medium text-charcoal hover:bg-white transition md:self-center dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10">
          Details →
        </button>
      </div>
    </article>
  );
}
