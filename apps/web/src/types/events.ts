export type VenueOut = {
  id: number;
  name: string;
  slug: string;
  area?: string | null;
};

export type EventOut = {
  id: number;
  title: string;
  slug: string;
  is_free: boolean;
  price_text?: string | null;
  status: "scheduled" | "canceled" | string;
};

export type EventOccurrenceOut = {
  id: number;
  start_datetime_utc: string; // ISO
  end_datetime_utc?: string | null;
  event: EventOut;
  venue: VenueOut;
};
