export type UnresolvedLocationGroup = {
  location_text: string;
  normalized_location: string;
  occurrence_count: number;
  sample_occurrence_ids: number[];
};

export type UnresolvedOccurrenceOut = {
  id: number;
  start_datetime_utc: string;
  end_datetime_utc?: string | null;
  location_text: string | null;
  event_id: number;
  event_title: string;
};

export type VenueOut = {
  id: number;
  name: string;
  slug: string;
  area?: string | null;
};

export type LinkOccurrenceRequest = {
  occurrence_id: number;
  venue_id: number;
};

export type CreateVenueFromLocationRequest = {
  location_text: string;
  name: string;
  area?: string | null;
  address?: string | null;
};

export type AddAliasRequest = {
  alias: string;
};
