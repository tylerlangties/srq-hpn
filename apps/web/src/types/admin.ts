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
  description?: string | null;
  hero_image_path?: string | null;
  aliases?: string[] | null;
};

export type AddAliasRequest = {
  alias: string;
};

export type AdminVenueDetailOut = {
  id: number;
  name: string;
  slug: string;
  area?: string | null;
  address?: string | null;
  website?: string | null;
  timezone?: string | null;
  description?: string | null;
  hero_image_path?: string | null;
};

export type UpdateVenueRequest = {
  name: string;
  area?: string | null;
  address?: string | null;
  website?: string | null;
  timezone?: string | null;
  description?: string | null;
  hero_image_path?: string | null;
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
  cf_challenges: number;
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

export type DuplicateGroupOut = {
  title_norm: string;
  start_utc: string;
  occurrences: number;
  event_ids: number[];
};

export type TaskRunOut = {
  id: number;
  task_id: string;
  task_name: string;
  status: string;
  queue: string | null;
  worker_hostname: string | null;
  retries: number | null;
  started_at: string;
  finished_at: string | null;
  runtime_ms: number | null;
  error: string | null;
};

export type TaskRunDayPoint = {
  day: string;
  success: number;
  failure: number;
  other: number;
  total: number;
};

export type TaskRunTaskPoint = {
  task_name: string;
  total: number;
  success: number;
  failure: number;
  last_run_at: string | null;
};

export type TaskRunDashboardOut = {
  generated_at: string;
  window_days: number;
  total_runs: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  recent_runs: TaskRunOut[];
  day_series: TaskRunDayPoint[];
  task_series: TaskRunTaskPoint[];
};
