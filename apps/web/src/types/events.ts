export type VenueOut = {
  id: number;
  name: string;
  slug: string;
  area?: string | null;
};

export type VenueDetailOut = {
  id: number;
  name: string;
  slug: string;
  area?: string | null;
  address?: string | null;
  website?: string | null;
  description?: string | null;
  description_markdown?: string | null;
  hero_image_path?: string | null;
  timezone?: string | null;
};

export type CategoryOut = {
  id: number;
  name: string;
  slug: string;
};

export type EventOut = {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  is_free: boolean;
  price_text?: string | null;
  external_url?: string | null;
  status: "scheduled" | "canceled" | string;
  categories: CategoryOut[];
};

export type EventOccurrenceOut = {
  id: number;
  start_datetime_utc: string; // ISO
  end_datetime_utc?: string | null;
  event: EventOut;
  venue: VenueOut | null;
  location_text?: string | null;
};

export type EventDetailOut = {
  event: EventOut;
  next_occurrence: EventOccurrenceOut;
  upcoming_occurrences: EventOccurrenceOut[];
  more_from_venue: EventOccurrenceOut[];
};
