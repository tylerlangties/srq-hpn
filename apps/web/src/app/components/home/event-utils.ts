import type { EventOccurrenceOut } from "@/types/events";

export function formatEventTime(occ: EventOccurrenceOut): string {
  const start = new Date(occ.start_datetime_utc);
  const end = occ.end_datetime_utc ? new Date(occ.end_datetime_utc) : null;

  const startLabel = start.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });

  if (!end) {
    return startLabel;
  }

  const endLabel = end.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });

  return `${startLabel} – ${endLabel}`;
}

export function formatDayLabel(occ: EventOccurrenceOut): string {
  const start = new Date(occ.start_datetime_utc);
  return start.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}
