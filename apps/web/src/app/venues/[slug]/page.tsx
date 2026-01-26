"use client";

import AppLayout from "../../components/AppLayout";
import EventCardLarge from "../../components/home/EventCardLarge";
import { useVenueDetail, useVenueEvents } from "../../hooks/useVenues";
import { addDays, toYmd } from "@/lib/dates";

type Props = {
  params: { slug: string };
};

export default function VenueDetailPage({ params }: Props) {
  const { slug } = params;
  const venue = useVenueDetail(slug);

  const start = toYmd(new Date());
  const end = toYmd(addDays(new Date(), 14));
  const events = useVenueEvents(slug, start, end);

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        {venue.error ? (
          <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-sm text-red-700 dark:text-red-300">
            {venue.error}
          </div>
        ) : venue.loading ? (
          <div className="h-32 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse" />
        ) : venue.data ? (
          <div className="mb-10 rounded-3xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-6 shadow-sm">
            <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
              {venue.data.name}
            </h1>
            <p className="mt-2 text-muted dark:text-white/60">
              {venue.data.area ?? "Sarasota"} · {venue.data.timezone ?? "America/New_York"}
            </p>
            {venue.data.address ? (
              <p className="mt-2 text-sm text-muted dark:text-white/50">
                {venue.data.address}
              </p>
            ) : null}
            {venue.data.website ? (
              <a
                href={venue.data.website}
                className="mt-3 inline-flex text-sm text-gulf dark:text-purple-300"
                target="_blank"
                rel="noreferrer"
              >
                Visit website →
              </a>
            ) : null}
          </div>
        ) : null}

        <div className="mb-6">
          <h2 className="text-2xl font-[var(--font-heading)] font-semibold">
            Upcoming events
          </h2>
          <p className="mt-2 text-muted dark:text-white/60">
            Next two weeks at this venue.
          </p>
        </div>

        {events.error ? (
          <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-sm text-red-700 dark:text-red-300">
            {events.error}
          </div>
        ) : events.loading ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {[0, 1].map((key) => (
              <div
                key={key}
                className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
              />
            ))}
          </div>
        ) : events.data && events.data.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {events.data.map((event) => (
              <EventCardLarge key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted dark:text-white/60">
            No upcoming events listed for this venue.
          </p>
        )}
      </div>
    </AppLayout>
  );
}
