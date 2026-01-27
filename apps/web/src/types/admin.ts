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
  aliases?: string[] | null;
};

export type AddAliasRequest = {
  alias: string;
};

export type SourceOut = {
  id: number;
  name: string;
  type: string;
  feed_count: number;
};

export type IngestResult = {
  source_id: number;
  feeds_seen: number;
  events_ingested: number;
  errors: number;
};

export type SourceFeedCleanupRequest = {
  older_than_days: number;
  source_id?: number | null;
  dry_run?: boolean;
};

export type SourceFeedCleanupResult = {
  deleted?: number;
  would_delete?: number;
};

export type EventSearchOut = {
  id: number;
  title: string;
  source_name: string;
  hidden: boolean;
  first_start_utc: string | null;
};
