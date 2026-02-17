"use client";

import { useEffect, useRef } from "react";
import { trackEvent } from "@/lib/analytics";

type Props = {
  eventId: number;
  eventSlug: string;
  eventTitle: string;
  venueId?: number;
  venueSlug?: string;
  venueName?: string;
};

export default function EventViewedTracker({
  eventId,
  eventSlug,
  eventTitle,
  venueId,
  venueSlug,
  venueName,
}: Props) {
  const hasTrackedRef = useRef(false);

  useEffect(() => {
    if (hasTrackedRef.current) {
      return;
    }

    trackEvent("event_viewed", {
      event_id: eventId,
      event_slug: eventSlug,
      event_title: eventTitle,
      source: "event_detail_page_load",
      source_page: "event_detail",
      source_component: "EventDetailPage",
      venue_id: venueId,
      venue_slug: venueSlug,
      venue_name: venueName,
      is_featured: false,
    });
    hasTrackedRef.current = true;
  }, [eventId, eventSlug, eventTitle, venueId, venueSlug, venueName]);

  return null;
}
