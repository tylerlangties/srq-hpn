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

export function getEventVenueLabel(occ: EventOccurrenceOut): string {
  return occ.venue?.name ?? occ.location_text ?? "Location TBA";
}

export function getEventAreaLabel(occ: EventOccurrenceOut): string {
  return occ.venue?.area ?? "Sarasota";
}

export function getEventPriceLabel(occ: EventOccurrenceOut): string {
  if (occ.event.is_free) {
    return "Free";
  }
  return occ.event.price_text ?? "Event";
}

/** Returns a time-of-day label (This Morning / Afternoon / Evening / Tonight) from a start date. */
export function getTimeOfDayLabel(startDate: Date): "This Morning" | "This Afternoon" | "This Evening" | "Tonight" {
  const hour = startDate.getHours();
  if (hour >= 5 && hour < 12) return "This Morning";
  if (hour >= 12 && hour < 17) return "This Afternoon";
  if (hour >= 17 && hour < 20) return "This Evening";
  return "Tonight"; // 20:00–04:59
}

/** True if the current time falls within the event's start–end window. */
export function isHappeningNow(occ: EventOccurrenceOut): boolean {
  const now = Date.now();
  const start = new Date(occ.start_datetime_utc).getTime();
  if (now < start) return false;
  const end = occ.end_datetime_utc ? new Date(occ.end_datetime_utc).getTime() : null;
  if (end == null) return true; // no end = treat as ongoing once started
  return now <= end;
}
