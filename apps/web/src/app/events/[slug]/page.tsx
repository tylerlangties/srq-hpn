import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import AppLayout from "../../components/AppLayout";
import EventCardCompact from "../../components/home/EventCardCompact";
import { parseEventRouteSegment, toDisplayEventTitle } from "@/lib/event-display";
import {
  formatDateTime,
  formatTimeRange,
  getEventDetailData,
  getEventPresentation,
  resolveEventRoute,
  summarizeDescription,
} from "../_lib/detail-data";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug: routeSegment } = await params;
  const { eventId, publicSlug } = parseEventRouteSegment(routeSegment);
  if (!publicSlug) {
    return {
      title: "Event not found | SRQ Happenings",
      description: "This event could not be found.",
      robots: { index: false, follow: true },
    };
  }

  const routeResolution = await resolveEventRoute(publicSlug, eventId);
  if (!routeResolution) {
    return {
      title: "Event not found | SRQ Happenings",
      description: "This event could not be found.",
      robots: { index: false, follow: true },
    };
  }

  const detail = await getEventDetailData(routeResolution.eventId);
  if (!detail) {
    return {
      title: "Event not found | SRQ Happenings",
      description: "This event could not be found.",
      robots: { index: false, follow: true },
    };
  }

  const displayTitle = toDisplayEventTitle(detail.event.title, detail.event.slug);
  const description = summarizeDescription(detail.event.description);
  const title = `${displayTitle} | SRQ Happenings`;
  const canonicalPath = `/events/${routeResolution.canonicalSegment}`;

  return {
    title,
    description,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      title,
      description,
      url: canonicalPath,
      type: "article",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
  };
}

export default async function EventDetailPage({ params }: PageProps) {
  const { slug: routeSegment } = await params;
  const { eventId, publicSlug } = parseEventRouteSegment(routeSegment);
  if (!publicSlug) {
    notFound();
  }

  const routeResolution = await resolveEventRoute(publicSlug, eventId);
  if (!routeResolution) {
    notFound();
  }

  const detail = await getEventDetailData(routeResolution.eventId);
  if (!detail) {
    notFound();
  }

  const canonicalSegment = routeResolution.canonicalSegment;
  if (routeSegment !== canonicalSegment) {
    redirect(`/events/${encodeURIComponent(canonicalSegment)}`);
  }

  const presentation = getEventPresentation(detail);
  const venue = detail.nextOccurrence.venue;
  const isCanceled = detail.event.status === "canceled";
  const displayTitle = toDisplayEventTitle(detail.event.title, detail.event.slug);

  return (
    <AppLayout showAmbient>
      <div className="relative z-10 mx-auto w-full max-w-6xl px-6 py-12 md:py-16">
        <section className="rounded-3xl border border-white/60 bg-white/80 p-6 shadow-xl shadow-charcoal/5 backdrop-blur-sm dark:border-white/10 dark:bg-white/5 md:p-8">
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold tracking-wide text-muted dark:text-white/50">
            <span className="rounded-full border border-charcoal/10 bg-sand px-3 py-1 dark:border-white/20 dark:bg-white/10 dark:text-white/80">
              Event Details
            </span>
            {detail.event.categories.map((category) => (
              <span
                key={category.slug}
                className="rounded-full bg-gulf/10 px-3 py-1 text-gulf dark:bg-cyan-500/20 dark:text-cyan-300"
              >
                {category.name}
              </span>
            ))}
          </div>

          <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
            <div>
              <h1 className="text-3xl font-[var(--font-heading)] font-semibold leading-tight text-charcoal dark:text-white md:text-5xl">
                {displayTitle}
              </h1>
              <p className="mt-4 text-base leading-relaxed text-muted dark:text-white/65 md:text-lg">
                {presentation.summaryLine}
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                {detail.event.external_url ? (
                  <a
                    href={detail.event.external_url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full bg-coral px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-coral/30 transition hover:translate-y-[-1px] hover:shadow-coral/40"
                  >
                    {detail.event.is_free ? "View event details" : "Get tickets"}
                  </a>
                ) : null}
                {venue?.slug ? (
                  <Link
                    href={`/venues/${venue.slug}`}
                    className="rounded-full border border-charcoal/10 bg-white/70 px-6 py-3 text-sm font-semibold text-charcoal transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
                  >
                    More at {venue.name}
                  </Link>
                ) : null}
              </div>
            </div>

            <aside className="rounded-2xl border border-charcoal/10 bg-sand/70 p-4 dark:border-white/15 dark:bg-white/5">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted dark:text-white/50">
                {presentation.hasUpcomingSeries ? "Next date" : "Schedule"}
              </p>
              <p className="mt-2 text-lg font-semibold text-charcoal dark:text-white">
                {formatDateTime(detail.nextOccurrence.start_datetime_utc)}
              </p>
              <p className="mt-1 text-sm text-muted dark:text-white/60">
                {formatTimeRange(
                  detail.nextOccurrence.start_datetime_utc,
                  detail.nextOccurrence.end_datetime_utc
                )}
              </p>
              <p className="mt-4 text-sm text-muted dark:text-white/60">
                {venue?.name ?? detail.nextOccurrence.location_text ?? "Location to be announced"}
              </p>
              <p className="mt-1 text-sm text-muted dark:text-white/55">{venue?.area ?? "Sarasota"}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-palm/15 px-3 py-1 text-xs font-semibold text-palm dark:bg-emerald-500/25 dark:text-emerald-300">
                  {detail.event.is_free ? "Free" : detail.event.price_text ?? "Ticketed"}
                </span>
                {isCanceled ? (
                  <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-500/20 dark:text-red-300">
                    Canceled
                  </span>
                ) : null}
              </div>
            </aside>
          </div>
        </section>

        <section className="mt-10 rounded-3xl border border-white/60 bg-white/80 p-6 backdrop-blur-sm dark:border-white/10 dark:bg-white/5 md:p-8">
          <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
            {presentation.hasUpcomingSeries ? "Upcoming dates" : "Event schedule"}
          </h2>
          <p className="mt-2 text-sm text-muted dark:text-white/55">Times shown in America/New_York.</p>

          <div className="mt-6 space-y-3">
            {detail.upcomingOccurrences.map((occurrence) => (
              <article
                key={occurrence.id}
                className="flex flex-col gap-2 rounded-2xl border border-charcoal/10 bg-sand/60 p-4 dark:border-white/15 dark:bg-white/5 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <p className="text-sm font-semibold text-charcoal dark:text-white">
                    {formatDateTime(occurrence.start_datetime_utc)}
                  </p>
                  <p className="text-sm text-muted dark:text-white/55">
                    {formatTimeRange(occurrence.start_datetime_utc, occurrence.end_datetime_utc)}
                  </p>
                </div>
                <p className="text-sm text-muted dark:text-white/60">
                  {occurrence.venue?.name ?? occurrence.location_text ?? "Location to be announced"}
                </p>
              </article>
            ))}
          </div>
        </section>

        {presentation.showPlanningTips ? (
          <section className="mt-10 rounded-3xl border border-white/60 bg-white/80 p-6 backdrop-blur-sm dark:border-white/10 dark:bg-white/5 md:p-8">
            <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
              Plan ahead
            </h2>
            <div className="mt-5 space-y-3 text-sm text-muted dark:text-white/65">
              <p className="rounded-2xl border border-charcoal/10 bg-sand/70 p-4 dark:border-white/15 dark:bg-white/5">
                Parking and arrival details can shift by date. Check the official link on the day of the event.
              </p>
              <p className="rounded-2xl border border-charcoal/10 bg-sand/70 p-4 dark:border-white/15 dark:bg-white/5">
                If this listing has limited details, we still show verified time and location as soon as we have them.
              </p>
            </div>
          </section>
        ) : null}

        {presentation.hasRelatedVenueEvents ? (
          <section className="mt-10">
            <div className="mb-5 flex items-center justify-between gap-3">
              <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
                More at this venue
              </h2>
              {venue?.slug ? (
                <Link
                  href={`/venues/${venue.slug}`}
                  className="text-sm font-medium text-gulf transition hover:text-gulf/80 dark:text-cyan-300 dark:hover:text-cyan-200"
                >
                  View venue page
                </Link>
              ) : null}
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {detail.moreFromVenue.map((occurrence) => (
                <EventCardCompact key={occurrence.id} event={occurrence} />
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </AppLayout>
  );
}
