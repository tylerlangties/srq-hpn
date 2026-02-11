import { API_BASE_URL } from "@/lib/api";
import type { EventDetailOut, EventOccurrenceOut } from "@/types/events";

export type EventRouteResolution = {
  eventId: number;
  canonicalSegment: string;
  isUnique: boolean;
};

export type EventDetailData = {
  event: EventOccurrenceOut["event"];
  nextOccurrence: EventOccurrenceOut;
  upcomingOccurrences: EventOccurrenceOut[];
  moreFromVenue: EventOccurrenceOut[];
};

export type EventDetailPresentation = {
  density: "minimal" | "rich";
  hasDescription: boolean;
  hasVenue: boolean;
  hasUpcomingSeries: boolean;
  hasRelatedVenueEvents: boolean;
  showPlanningTips: boolean;
  summaryLine: string;
};

export function formatDateTime(iso: string) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
  }).format(new Date(iso));
}

export function formatTime(iso: string) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
  }).format(new Date(iso));
}

export function formatTimeRange(startIso: string, endIso: string | null | undefined) {
  const startLabel = formatTime(startIso);
  if (!endIso) return startLabel;
  return `${startLabel} - ${formatTime(endIso)}`;
}

export function summarizeDescription(value: string | null | undefined) {
  if (!value) {
    return "Explore this Sarasota event, including schedule details, location, and ticket information.";
  }
  return value.length > 160 ? `${value.slice(0, 157)}...` : value;
}

async function fetchEventDetail(eventId: number): Promise<EventDetailOut | null> {
  try {
    const url = `${API_BASE_URL}/api/events/${eventId}`;
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as EventDetailOut;
  } catch {
    return null;
  }
}

export async function resolveEventRoute(
  publicSlug: string,
  eventId?: number | null
): Promise<EventRouteResolution | null> {
  try {
    const query = eventId ? `?event_id=${encodeURIComponent(String(eventId))}` : "";
    const url = `${API_BASE_URL}/api/events/resolve/${encodeURIComponent(publicSlug)}${query}`;
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }

    const payload = (await response.json()) as {
      event_id: number;
      canonical_segment: string;
      is_unique: boolean;
    };

    return {
      eventId: payload.event_id,
      canonicalSegment: payload.canonical_segment,
      isUnique: payload.is_unique,
    };
  } catch {
    return null;
  }
}

export async function getEventDetailData(eventId: number): Promise<EventDetailData | null> {
  const detail = await fetchEventDetail(eventId);
  if (!detail) {
    return null;
  }

  const nextOccurrence = detail.next_occurrence;
  const upcomingOccurrences = detail.upcoming_occurrences;
  const moreFromVenue = detail.more_from_venue;

  return {
    event: nextOccurrence.event,
    nextOccurrence,
    upcomingOccurrences,
    moreFromVenue,
  };
}

export function getEventPresentation(detail: EventDetailData): EventDetailPresentation {
  const descriptionLength = detail.event.description?.trim().length ?? 0;
  const hasDescription = descriptionLength >= 70;
  const hasVenue = Boolean(detail.nextOccurrence.venue?.name || detail.nextOccurrence.location_text);
  const hasUpcomingSeries = detail.upcomingOccurrences.length > 1;
  const hasRelatedVenueEvents = detail.moreFromVenue.length > 0;
  const richnessScore = [
    hasDescription,
    hasVenue,
    hasUpcomingSeries,
    detail.event.categories.length > 0,
    Boolean(detail.event.external_url),
  ].filter(Boolean).length;
  const density: "minimal" | "rich" = richnessScore >= 4 ? "rich" : "minimal";

  const summaryLine = hasDescription
    ? detail.event.description!.trim()
    : hasVenue
      ? `Plan around ${detail.nextOccurrence.venue?.name ?? detail.nextOccurrence.location_text}. We'll keep this listing updated as more details arrive.`
      : "Core details are confirmed. More context and planning notes will be added as organizers publish updates.";

  return {
    density,
    hasDescription,
    hasVenue,
    hasUpcomingSeries,
    hasRelatedVenueEvents,
    showPlanningTips: density === "rich" && hasVenue,
    summaryLine,
  };
}
