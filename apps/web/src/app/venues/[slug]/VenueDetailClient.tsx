"use client";

import Link from "next/link";
import EventCardLarge from "../../components/home/EventCardLarge";
import type { EventOccurrenceOut, VenueDetailOut } from "@/types/events";

type Props = {
  venue: VenueDetailOut;
  events: EventOccurrenceOut[];
};

export default function VenueDetailClient({ venue, events }: Props) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-12">
      <div className="mb-10 rounded-3xl bg-white/80 border border-white/60 p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
        <h1 className="text-3xl font-[var(--font-heading)] font-semibold md:text-4xl">{venue.name}</h1>
        <p className="mt-2 text-muted dark:text-white/60">
          {venue.area ?? "Sarasota"} · {venue.timezone ?? "America/New_York"}
        </p>
        {venue.address ? <p className="mt-2 text-sm text-muted dark:text-white/50">{venue.address}</p> : null}
        {venue.website ? (
          <a
            href={venue.website}
            className="mt-3 inline-flex text-sm text-gulf dark:text-cyan-300"
            target="_blank"
            rel="noreferrer"
          >
            Visit website →
          </a>
        ) : null}
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-[var(--font-heading)] font-semibold">Upcoming events</h2>
        <p className="mt-2 text-muted dark:text-white/60">Next two weeks at this venue.</p>
      </div>

      {events.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {events.map((event) => (
            <EventCardLarge key={event.id} event={event} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted dark:text-white/60">No upcoming events listed for this venue.</p>
      )}

      <div className="mt-8">
        <Link
          href="/venues"
          className="inline-flex text-sm font-medium text-gulf underline-offset-2 hover:underline dark:text-cyan-300"
        >
          Back to venues
        </Link>
      </div>
    </div>
  );
}
