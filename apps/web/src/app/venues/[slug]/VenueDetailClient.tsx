"use client";

import Image from "next/image";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import EventCardLarge from "../../components/home/EventCardLarge";
import { SHARED_RESPONSIVE } from "@/lib/responsive";
import type { EventOccurrenceOut, VenueDetailOut } from "@/types/events";

type Props = {
  venue: VenueDetailOut;
  events: EventOccurrenceOut[];
};

function normalizeVenueImagePath(path: string | null | undefined): string | null {
  if (!path) {
    return null;
  }

  const trimmed = path.trim();
  if (!trimmed) {
    return null;
  }

  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}

export default function VenueDetailClient({ venue, events }: Props) {
  const heroImagePath = normalizeVenueImagePath(venue.hero_image_path);

  return (
    <div className={`mx-auto w-full max-w-6xl py-12 ${SHARED_RESPONSIVE.containerInset}`}>
      <a
        href="#venue-upcoming-events"
        className="fixed bottom-5 right-4 z-40 inline-flex items-center justify-center rounded-full border border-charcoal/15 bg-white/95 px-4 py-2 text-sm font-semibold text-charcoal shadow-lg backdrop-blur transition hover:bg-sand dark:border-white/20 dark:bg-slate-900/90 dark:text-white dark:hover:bg-slate-800 md:hidden"
      >
        Jump to events ↓
      </a>
      <div className="mb-10 rounded-3xl bg-white/80 border border-white/60 p-6 shadow-sm dark:border-white/10 dark:bg-white/5">
        <div className="relative mb-6 h-56 overflow-hidden rounded-2xl bg-slate-100 dark:bg-slate-900/40">
          {heroImagePath ? (
            <Image
              src={heroImagePath}
              alt={`${venue.name} venue photo`}
              fill
              sizes="(max-width: 768px) 100vw, 1152px"
              className="object-cover"
              priority
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-r from-cyan-200/40 via-sky-100/50 to-amber-100/40 dark:from-cyan-900/30 dark:via-slate-900/40 dark:to-amber-900/20" />
          )}
        </div>
        <h1 className="text-3xl font-[var(--font-heading)] font-semibold md:text-4xl">{venue.name}</h1>
        <p className="mt-2 text-muted dark:text-white/60">
          {venue.area ?? "Sarasota"} · {venue.timezone ?? "America/New_York"}
        </p>
        <a
          href="#venue-upcoming-events"
          className="mt-4 inline-flex items-center justify-center rounded-full border border-charcoal/15 bg-white px-4 py-2 text-sm font-semibold text-charcoal transition hover:bg-sand dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
        >
          Jump to events ↓
        </a>
        {venue.description ? (
          <p className="mt-4 max-w-3xl text-sm leading-6 text-muted dark:text-white/70">{venue.description}</p>
        ) : null}
        {venue.description_markdown ? (
          <section className="mt-7 w-full">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-muted dark:text-white/50">
              About this venue
            </p>
            <div className="prose prose-sm md:prose-base max-w-none prose-headings:font-[var(--font-heading)] prose-headings:font-semibold prose-headings:text-charcoal prose-h2:mt-6 prose-h2:text-xl md:prose-h2:text-2xl prose-h3:mt-5 prose-h3:text-lg md:prose-h3:text-xl prose-p:leading-7 prose-p:text-charcoal/80 prose-ul:my-4 prose-ul:list-disc prose-ul:pl-6 prose-ol:my-4 prose-ol:list-decimal prose-ol:pl-6 prose-li:my-1 prose-li:marker:text-gulf prose-a:font-semibold prose-a:text-gulf prose-a:no-underline hover:prose-a:underline prose-strong:text-charcoal prose-blockquote:border-l-4 prose-blockquote:border-gulf/30 prose-blockquote:pl-4 prose-blockquote:text-charcoal/80 dark:prose-invert dark:prose-headings:text-white dark:prose-p:text-white/80 dark:prose-strong:text-white dark:prose-li:marker:text-cyan-300 dark:prose-a:text-cyan-300 dark:prose-blockquote:border-cyan-300/30 dark:prose-blockquote:text-white/80">
              <ReactMarkdown
                components={{
                  img: ({ src, alt }) => {
                    if (!src || typeof src !== "string") {
                      return null;
                    }

                    const normalizedSrc = src.startsWith("/") ? src : `/${src}`;
                    return (
                      <span className="block overflow-hidden rounded-xl">
                        <Image
                          src={normalizedSrc}
                          alt={alt ?? `${venue.name} image`}
                          width={1200}
                          height={700}
                          className="h-auto w-full"
                        />
                      </span>
                    );
                  },
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noreferrer noopener">
                      {children}
                    </a>
                  ),
                }}
              >
                {venue.description_markdown}
              </ReactMarkdown>
            </div>
          </section>
        ) : null}
        {venue.address ? <p className="mt-2 text-sm text-muted dark:text-white/50">{venue.address}</p> : null}
        {venue.website ? (
          <a
            href={venue.website}
            className="mt-3 inline-flex items-center justify-center rounded-full border border-gulf/20 bg-gulf/10 px-4 py-2 text-sm font-semibold text-gulf transition hover:bg-gulf/15 dark:border-cyan-300/30 dark:bg-cyan-300/10 dark:text-cyan-300 dark:hover:bg-cyan-300/20"
            target="_blank"
            rel="noreferrer"
          >
            Visit website →
          </a>
        ) : null}
      </div>

      <div id="venue-upcoming-events" className="mb-6 scroll-mt-24">
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
