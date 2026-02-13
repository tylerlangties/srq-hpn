export const CONTENT_API_PATHS = {
  articles: "/content-api/articles",
} as const;

export const API_PATHS = {
  auth: {
    login: "/api/auth/login",
    logout: "/api/auth/logout",
    me: "/api/auth/me",
  },
  events: {
    day: "/api/events/day",
    range: "/api/events/range",
    count: "/api/events/count",
    detail: (eventId: number) => `/api/events/${eventId}`,
    resolve: (publicSlug: string) => `/api/events/resolve/${encodeURIComponent(publicSlug)}`,
  },
  weather: {
    summary: "/api/weather",
  },
  venues: {
    list: "/api/venues",
    detail: (slug: string) => `/api/venues/${slug}`,
    events: (slug: string) => `/api/venues/${slug}/events`,
  },
  admin: {
    sources: "/api/admin/sources",
    eventsSearch: "/api/admin/events/search",
    event: (eventId: number) => `/api/admin/events/${eventId}`,
    duplicates: "/api/admin/events/duplicates",
    sourceFeedsCleanup: "/api/admin/source-feeds/cleanup",
    ingestSourceFeeds: (sourceId: number) => `/api/admin/ingest/source/${sourceId}/feeds`,
    unresolvedVenues: "/api/admin/venues/unresolved",
    venues: "/api/admin/venues",
    createVenueFromLocation: "/api/admin/venues/create-from-location",
    unresolvedVenueOccurrences: (locationText: string) =>
      `/api/admin/venues/unresolved/${encodeURIComponent(locationText)}/occurrences`,
    linkVenue: "/api/admin/venues/link",
  },
} as const;

export function withQuery(
  path: string,
  params: Record<string, string | number | null | undefined>
): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    searchParams.set(key, String(value));
  }

  const query = searchParams.toString();
  return query ? `${path}?${query}` : path;
}
