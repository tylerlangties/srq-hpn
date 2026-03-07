import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import AppLayout from "../../components/AppLayout";
import EventCardCompact from "../../components/home/EventCardCompact";
import EventViewedTracker from "./EventViewedTracker";
import TrackedExternalEventLink from "./TrackedExternalEventLink";
import { parseEventRouteSegment, toDisplayEventTitle } from "@/lib/event-display";
import { buildSiteUrl } from "@/lib/seo";
import {
  formatDateTime,
  formatTimeRange,
  getEventDetailData,
  getEventPresentation,
  resolveEventRoute,
  summarizeDescription,
} from "../_lib/detail-data";
import { SHARED_RESPONSIVE } from "@/lib/responsive";

type PageProps = {
  params: Promise<{ slug: string }>;
};

const openGraphImage = "/opengraph-image";
const twitterImage = "/twitter-image";

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
      images: [{ url: openGraphImage }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [twitterImage],
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
  const canonicalPath = `/events/${canonicalSegment}`;
  const eventJsonLd = {
    "@context": "https://schema.org",
    "@type": "Event",
    "@id": buildSiteUrl(canonicalPath).toString(),
    name: displayTitle,
    description: summarizeDescription(detail.event.description),
    inLanguage: "en-US",
    keywords: detail.event.categories.map((category) => category.name).join(", ") || undefined,
    eventStatus: isCanceled
      ? "https://schema.org/EventCancelled"
      : "https://schema.org/EventScheduled",
    eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
    startDate: detail.nextOccurrence.start_datetime_utc,
    endDate: detail.nextOccurrence.end_datetime_utc ?? undefined,
    isAccessibleForFree: detail.event.is_free,
    url: buildSiteUrl(canonicalPath).toString(),
    location: {
      "@type": "Place",
      name: venue?.name ?? "Sarasota",
      address: {
        "@type": "PostalAddress",
        streetAddress: detail.nextOccurrence.location_text ?? undefined,
        addressLocality: venue?.area ?? "Sarasota",
        addressRegion: "FL",
        addressCountry: "US",
      },
    },
    organizer: {
      "@type": "Organization",
      name: "SRQ Happenings",
      url: buildSiteUrl("/").toString(),
    },
    offers: detail.event.external_url
      ? {
          "@type": "Offer",
          url: detail.event.external_url,
          priceCurrency: "USD",
          price: detail.event.is_free ? "0" : undefined,
          availability: isCanceled
            ? "https://schema.org/SoldOut"
            : "https://schema.org/InStock",
        }
      : undefined,
  };

  return (
    <AppLayout showAmbient>
      <EventViewedTracker
        eventId={detail.event.id}
        eventSlug={detail.event.slug}
        eventTitle={detail.event.title}
        venueId={venue?.id}
        venueSlug={venue?.slug}
        venueName={venue?.name}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(eventJsonLd) }}
      />
      <div className={`mx-auto w-full max-w-6xl py-12 ${SHARED_RESPONSIVE.containerInset}`}>
        <section className="mb-10 rounded-3xl bg-white/80 border border-white/60 p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
          <div className="relative mb-6 h-[20rem] overflow-hidden rounded-2xl bg-slate-100 dark:bg-slate-900/40">
            <div className="h-full w-full bg-gradient-to-r from-cyan-200/40 via-sky-100/50 to-amber-100/40 dark:from-cyan-900/30 dark:via-slate-900/40 dark:to-amber-900/20" />
          </div>
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs font-semibold tracking-wide text-muted dark:text-white/50">
            <span className="rounded-full border border-charcoal/15 bg-white px-3 py-1 dark:border-white/20 dark:bg-white/5 dark:text-white/80">
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
              <h1 className="text-3xl font-[var(--font-heading)] font-semibold leading-tight text-charcoal dark:text-white md:text-4xl">
                {displayTitle}
              </h1>
              <p className="mt-4 text-base leading-relaxed text-muted dark:text-white/65 md:text-lg">
                {presentation.summaryLine}
              </p>

              <div className={`mt-6 ${SHARED_RESPONSIVE.buttonGroup}`}>
                {detail.event.external_url ? (
                  <TrackedExternalEventLink
                    href={detail.event.external_url}
                    className={`inline-flex ${SHARED_RESPONSIVE.buttonWidth} items-center justify-center rounded-full bg-coral ${SHARED_RESPONSIVE.buttonPadding} text-sm font-semibold text-white shadow-lg shadow-coral/30 transition hover:translate-y-[-1px] hover:shadow-coral/40`}
                    eventId={detail.event.id}
                    eventSlug={detail.event.slug}
                    eventTitle={detail.event.title}
                    venueId={venue?.id}
                    venueSlug={venue?.slug}
                    venueName={venue?.name}
                  >
                    {detail.event.is_free ? "View event details" : "Get tickets"}
                  </TrackedExternalEventLink>
                ) : null}
                {venue?.slug ? (
                  <Link
                    href={`/venues/${venue.slug}`}
                    className={`inline-flex ${SHARED_RESPONSIVE.buttonWidth} items-center justify-center rounded-full border border-charcoal/15 bg-white ${SHARED_RESPONSIVE.buttonPadding} text-sm font-semibold text-charcoal transition hover:bg-sand dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10`}
                  >
                    More at {venue.name}
                  </Link>
                ) : null}
              </div>
            </div>

            <aside className="rounded-2xl bg-slate-100 p-4 dark:bg-slate-900/40">
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

        <section className="mb-10 rounded-3xl bg-white/80 border border-white/60 p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
          <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
            {presentation.hasUpcomingSeries ? "Upcoming dates" : "Event schedule"}
          </h2>
          <p className="mt-2 text-sm text-muted dark:text-white/55">Times shown in America/New_York.</p>

          <div className="mt-6 space-y-3">
            {detail.upcomingOccurrences.map((occurrence) => (
              <article
                key={occurrence.id}
                className="flex flex-col gap-2 rounded-2xl bg-slate-100 p-4 dark:bg-slate-900/40 md:flex-row md:items-center md:justify-between"
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

        {presentation.hasRelatedVenueEvents ? (
          <div id="more-at-venue" className="mb-6 scroll-mt-24">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-2xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
                  More at this venue
                </h2>
                <p className="mt-2 text-muted dark:text-white/60">Other upcoming events at this location.</p>
              </div>
              {venue?.slug ? (
                <Link
                  href={`/venues/${venue.slug}`}
                  className="text-sm font-medium text-gulf underline-offset-2 hover:underline dark:text-cyan-300"
                >
                  View venue page
                </Link>
              ) : null}
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {detail.moreFromVenue.map((occurrence) => (
                <EventCardCompact key={occurrence.id} event={occurrence} />
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-8">
          <Link
            href="/events"
            className="inline-flex text-sm font-medium text-gulf underline-offset-2 hover:underline dark:text-cyan-300"
          >
            Back to events
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}
