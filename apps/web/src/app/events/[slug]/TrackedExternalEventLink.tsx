"use client";

import type { ReactNode } from "react";
import { trackEvent } from "@/lib/analytics";

type Props = {
  href: string;
  className: string;
  children: ReactNode;
  eventId: number;
  eventSlug: string;
  eventTitle: string;
  venueId?: number;
  venueSlug?: string;
  venueName?: string;
};

export default function TrackedExternalEventLink({
  href,
  className,
  children,
  eventId,
  eventSlug,
  eventTitle,
  venueId,
  venueSlug,
  venueName,
}: Props) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className={className}
      aria-label={`${eventTitle} (opens in a new tab)`}
      onClick={() => {
        trackEvent("event_link_clicked", {
          event_id: eventId,
          event_slug: eventSlug,
          event_title: eventTitle,
          source: "event_detail_external_link",
          source_page: "event_detail",
          source_component: "EventDetailPage",
          venue_id: venueId,
          venue_slug: venueSlug,
          venue_name: venueName,
          is_featured: false,
        });
      }}
    >
      {children}
    </a>
  );
}
