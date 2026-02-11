export function toPublicEventSlug(rawSlug: string): string {
  if (!rawSlug) return rawSlug;

  const trimmed = rawSlug.trim().toLowerCase();
  const withoutIdSuffix = trimmed
    .replace(/-\d+-[a-z]{2,6}-[a-z0-9]{10,}$/i, "")
    .replace(/-[a-z]{2,6}-[a-z0-9]{10,}$/i, "")
    .replace(/-[a-z0-9]{10,}$/i, "");

  return withoutIdSuffix.length > 0 ? withoutIdSuffix : trimmed;
}

export function normalizeEventSlugForMatch(value: string): string {
  return toPublicEventSlug(value);
}

export function toEventRouteSegment(event: { id: number; slug: string }): string {
  const publicSlug = toPublicEventSlug(event.slug);
  return `${publicSlug}--e${event.id}`;
}

export function parseEventRouteSegment(segment: string): {
  eventId: number | null;
  publicSlug: string;
} {
  const decoded = decodeURIComponent(segment).trim().toLowerCase();
  const match = decoded.match(/^(.*)--e(\d+)$/);
  if (!match) {
    return { eventId: null, publicSlug: decoded };
  }

  const maybeId = Number.parseInt(match[2], 10);
  if (!Number.isFinite(maybeId) || maybeId <= 0) {
    return { eventId: null, publicSlug: decoded };
  }

  return {
    eventId: maybeId,
    publicSlug: match[1],
  };
}

export function toDisplayEventTitle(rawTitle: string, rawSlug: string): string {
  const title = rawTitle.trim();
  if (!title) return rawTitle;

  const slugParts = rawSlug.split("-").filter(Boolean);
  const tail = slugParts.at(-1) ?? "";
  const maybeIdTail = /^[a-z0-9]{10,}$/i.test(tail) ? tail : "";
  const maybePrefix = slugParts.at(-2) ?? "";
  const maybeNumber = slugParts.at(-3) ?? "";

  if (!maybeIdTail) {
    return title;
  }

  const hashPattern = new RegExp(`\\s+${maybeIdTail}$`, "i");
  let cleaned = title.replace(hashPattern, "").trim();

  if (cleaned !== title && /^[a-z0-9]{1,4}$/i.test(maybePrefix)) {
    const prefixPattern = new RegExp(`\\s+${maybePrefix}$`, "i");
    cleaned = cleaned.replace(prefixPattern, "").trim();

    if (/^\d{1,4}$/.test(maybeNumber)) {
      const numberPattern = new RegExp(`\\s+${maybeNumber}$`, "i");
      cleaned = cleaned.replace(numberPattern, "").trim();
    }
  }

  return cleaned.length > 0 ? cleaned : title;
}
