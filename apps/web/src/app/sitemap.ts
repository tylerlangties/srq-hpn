import type { MetadataRoute } from "next";
import { getArticleSlugs } from "@/lib/articles";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import { toEventRouteSegment } from "@/lib/event-display";
import { buildSiteUrl, getSiteOrigin } from "@/lib/seo";
import type { EventOccurrenceOut, VenueOut } from "@/types/events";

function toYmd(date: Date) {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const url = `${getSiteOrigin()}${path}`;
    const res = await fetch(url, { next: { revalidate: 1800 } });
    if (!res.ok) {
      return null;
    }
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function getVenueEntries(now: Date): Promise<MetadataRoute.Sitemap> {
  const venues = await getJson<VenueOut[]>(API_PATHS.venues.list);
  if (!venues || venues.length === 0) {
    return [];
  }

  return venues.map((venue) => ({
    url: buildSiteUrl(`/venues/${venue.slug}`).toString(),
    lastModified: now,
    changeFrequency: "daily",
    priority: 0.7,
  }));
}

async function getEventEntries(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const start = toYmd(now);
  const endDate = new Date(now);
  endDate.setUTCDate(endDate.getUTCDate() + 365);
  const end = toYmd(endDate);

  const path = withQuery(API_PATHS.events.range, { start, end });
  const occurrences = await getJson<EventOccurrenceOut[]>(path);
  if (!occurrences || occurrences.length === 0) {
    return [];
  }

  const byEvent = new Map<number, EventOccurrenceOut>();
  for (const occurrence of occurrences) {
    if (!byEvent.has(occurrence.event.id)) {
      byEvent.set(occurrence.event.id, occurrence);
    }
  }

  return [...byEvent.values()].map((occurrence) => ({
    url: buildSiteUrl(
      `/events/${toEventRouteSegment({ id: occurrence.event.id, slug: occurrence.event.slug })}`
    ).toString(),
    lastModified: new Date(occurrence.start_datetime_utc),
    changeFrequency: "daily",
    priority: 0.8,
  }));
}

async function getArticleEntries(now: Date): Promise<MetadataRoute.Sitemap> {
  const slugs = await getArticleSlugs();
  return slugs.map((slug) => ({
    url: buildSiteUrl(`/articles/${slug}`).toString(),
    lastModified: now,
    changeFrequency: "weekly",
    priority: 0.6,
  }));
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  const staticEntries: MetadataRoute.Sitemap = [
    {
      url: buildSiteUrl("/").toString(),
      lastModified: now,
      changeFrequency: "hourly",
      priority: 1,
    },
    {
      url: buildSiteUrl("/events").toString(),
      lastModified: now,
      changeFrequency: "hourly",
      priority: 0.95,
    },
    {
      url: buildSiteUrl("/venues").toString(),
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.8,
    },
    {
      url: buildSiteUrl("/articles").toString(),
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.75,
    },
    {
      url: buildSiteUrl("/about").toString(),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.4,
    },
    {
      url: buildSiteUrl("/contact").toString(),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.4,
    },
    {
      url: buildSiteUrl("/submit").toString(),
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.4,
    },
  ];

  const [eventEntries, venueEntries, articleEntries] = await Promise.all([
    getEventEntries(),
    getVenueEntries(now),
    getArticleEntries(now),
  ]);

  return [...staticEntries, ...eventEntries, ...venueEntries, ...articleEntries];
}
