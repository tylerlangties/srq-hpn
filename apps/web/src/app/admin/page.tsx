"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import { useAdminGuard } from "@/app/hooks/useAdminGuard";
import type {
  DuplicateGroupOut,
  EventSearchOut,
  IngestResult,
  SourceFeedCleanupResult,
  SourceOut,
} from "@/types/admin";

type IngestStatus = "idle" | "loading" | "success" | "error";

type CleanupStatus = "idle" | "loading" | "success" | "error";

function formatFirstStart(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function AdminPage() {
  const { checking: authChecking, user } = useAdminGuard();
  const [sources, setSources] = useState<SourceOut[] | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>("idle");
  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const [cleanupOlderThanDays, setCleanupOlderThanDays] = useState(60);
  const [cleanupSourceId, setCleanupSourceId] = useState<number | null>(null);
  const [cleanupStatus, setCleanupStatus] = useState<CleanupStatus>("idle");
  const [cleanupResult, setCleanupResult] =
    useState<SourceFeedCleanupResult | null>(null);
  const [cleanupError, setCleanupError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [searchResults, setSearchResults] = useState<EventSearchOut[] | null>(
    null
  );
  const [searchStatus, setSearchStatus] = useState<"idle" | "loading" | "error">("idle");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hidingEventId, setHidingEventId] = useState<number | null>(null);

  const [dupeSourceId, setDupeSourceId] = useState<number | null>(null);
  const [dupeLimit, setDupeLimit] = useState(100);
  const [dupeStatus, setDupeStatus] = useState<"idle" | "loading" | "error">("idle");
  const [dupeResults, setDupeResults] = useState<DuplicateGroupOut[] | null>(null);
  const [dupeError, setDupeError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "admin") {
      loadSources();
    }
  }, [user]);

  const runSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setSearchResults(null);
      setSearchStatus("idle");
      return;
    }
    setSearchStatus("loading");
    setSearchError(null);
    try {
      const data = await apiGet<EventSearchOut[]>(
        withQuery(API_PATHS.admin.eventsSearch, { q: q.trim(), limit: 20 })
      );
      setSearchResults(data);
      setSearchStatus("idle");
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : String(e));
      setSearchStatus("error");
      setSearchResults(null);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      runSearch(searchInput);
    }, 300);
    return () => clearTimeout(t);
  }, [searchInput, runSearch]);

  async function handleHideUnhide(eventId: number, hidden: boolean) {
    setHidingEventId(eventId);
    setSearchError(null);
    try {
      await apiPatch<{ event_id: number; hidden: boolean }>(API_PATHS.admin.event(eventId), {
        hidden,
      });
      setSearchResults((prev) =>
        prev?.map((e) => (e.id === eventId ? { ...e, hidden } : e)) ?? null
      );
    } catch (e) {
      setSearchError(e instanceof Error ? e.message : String(e));
    } finally {
      setHidingEventId(null);
    }
  }

  async function loadSources() {
    try {
      setLoadingError(null);
      const data = await apiGet<SourceOut[]>(API_PATHS.admin.sources);
      setSources(data);
    } catch (e) {
      setLoadingError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleIngest() {
    if (!selectedSourceId) return;

    setIngestStatus("loading");
    setIngestResult(null);
    setIngestError(null);

    try {
      const result = await apiPost<IngestResult>(
        API_PATHS.admin.ingestSourceFeeds(selectedSourceId),
        {}
      );
      setIngestResult(result);
      setIngestStatus("success");
    } catch (e) {
      setIngestError(e instanceof Error ? e.message : String(e));
      setIngestStatus("error");
    }
  }

  async function handleCleanup(dryRun: boolean) {
    setCleanupStatus("loading");
    setCleanupResult(null);
    setCleanupError(null);

    try {
      const result = await apiPost<SourceFeedCleanupResult>(
        API_PATHS.admin.sourceFeedsCleanup,
        {
          older_than_days: cleanupOlderThanDays,
          source_id: cleanupSourceId ?? undefined,
          dry_run: dryRun,
        }
      );
      setCleanupResult(result);
      setCleanupStatus("success");
      if (!dryRun && (result.deleted ?? 0) > 0) {
        loadSources();
      }
    } catch (e) {
      setCleanupError(e instanceof Error ? e.message : String(e));
      setCleanupStatus("error");
    }
  }

  async function handleLoadDuplicates() {
    if (!dupeSourceId) return;
    setDupeStatus("loading");
    setDupeError(null);
    setDupeResults(null);
    try {
      const data = await apiGet<DuplicateGroupOut[]>(
        withQuery(API_PATHS.admin.duplicates, {
          source_id: dupeSourceId,
          limit: dupeLimit,
        })
      );
      setDupeResults(data);
      setDupeStatus("idle");
    } catch (e) {
      setDupeError(e instanceof Error ? e.message : String(e));
      setDupeStatus("error");
    }
  }

  const selectedSource = sources?.find((s) => s.id === selectedSourceId);

  if (authChecking || !user) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-muted dark:text-white/50 font-medium">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-8">
        Admin Panel
      </h1>

      <div className="space-y-6">
        {/* Ingest Source Feeds Section */}
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm">
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Ingest Source Feeds
          </h2>
          <p className="text-sm text-muted dark:text-white/60 mb-4">
            Fetch and ingest events from iCal feeds for a selected source.
          </p>

          {loadingError ? (
            <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
              <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                Failed to load sources
              </p>
              <p className="mt-1 text-sm text-red-800 dark:text-red-400">{loadingError}</p>
              <button
                onClick={loadSources}
                className="mt-2 rounded-xl border border-red-300 dark:border-red-600 bg-white dark:bg-white/5 px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : !sources ? (
            <div className="text-sm text-muted dark:text-white/50 font-medium">
              Loading sources...
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Select Source
                </label>
                <select
                  value={selectedSourceId ?? ""}
                  onChange={(e) => {
                    setSelectedSourceId(e.target.value ? parseInt(e.target.value) : null);
                    setIngestStatus("idle");
                    setIngestResult(null);
                    setIngestError(null);
                  }}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                >
                  <option value="">-- Select a source --</option>
                  {sources.map((source) => (
                    <option key={source.id} value={source.id}>
                      {source.name} ({source.feed_count} feeds)
                    </option>
                  ))}
                </select>
              </div>

              {selectedSource && (
                <div className="rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-3">
                  <div className="text-xs text-muted dark:text-white/50 space-y-1">
                    <p>
                      <span className="font-semibold text-charcoal dark:text-white/70">Type:</span>{" "}
                      {selectedSource.type}
                    </p>
                    <p>
                      <span className="font-semibold text-charcoal dark:text-white/70">Feeds:</span>{" "}
                      {selectedSource.feed_count}
                    </p>
                  </div>
                </div>
              )}

              <button
                onClick={handleIngest}
                disabled={!selectedSourceId || ingestStatus === "loading"}
                className="rounded-xl bg-gulf px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gulf/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {ingestStatus === "loading" ? (
                  <span className="flex items-center gap-2">
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Ingesting...
                  </span>
                ) : (
                  "Run Ingest"
                )}
              </button>

              {/* Success Result */}
              {ingestStatus === "success" && ingestResult && (
                <div className="rounded-xl border border-palm/30 dark:border-palm/40 bg-palm/10 dark:bg-palm/20 p-4">
                  <p className="text-sm font-semibold text-palm dark:text-palm/90 mb-2">
                    Ingest Complete
                  </p>
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-palm dark:text-palm/90">
                        {ingestResult.feeds_seen}
                      </p>
                      <p className="text-xs text-palm/80 dark:text-palm/70 font-medium">
                        Feeds Processed
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-palm dark:text-palm/90">
                        {ingestResult.events_ingested}
                      </p>
                      <p className="text-xs text-palm/80 dark:text-palm/70 font-medium">
                        Events Ingested
                      </p>
                    </div>
                    <div>
                      <p
                        className={`text-2xl font-bold ${
                          ingestResult.errors > 0
                            ? "text-coral dark:text-coral/90"
                            : "text-palm dark:text-palm/90"
                        }`}
                      >
                        {ingestResult.errors}
                      </p>
                      <p className="text-xs text-palm/80 dark:text-palm/70 font-medium">
                        Errors
                      </p>
                    </div>
                    <div>
                      <p
                        className={`text-2xl font-bold ${
                          ingestResult.cf_challenges > 0
                            ? "text-coral dark:text-coral/90"
                            : "text-palm dark:text-palm/90"
                        }`}
                      >
                        {ingestResult.cf_challenges}
                      </p>
                      <p className="text-xs text-palm/80 dark:text-palm/70 font-medium">
                        CF Blocked
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Result */}
              {ingestStatus === "error" && ingestError && (
                <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
                  <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                    Ingest Failed
                  </p>
                  <p className="mt-1 text-sm text-red-800 dark:text-red-400">{ingestError}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Clean up source feeds */}
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm">
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Clean up source feeds
          </h2>
          <p className="text-sm text-muted dark:text-white/60 mb-4">
            Remove feeds that haven&apos;t been seen by scrapers in the given
            number of days. Uses <code className="rounded bg-charcoal/10 dark:bg-white/10 px-1">last_seen_at</code>{" "}
            (or <code className="rounded bg-charcoal/10 dark:bg-white/10 px-1">created_at</code> when
            never seen). Preview shows how many would be removed without deleting.
          </p>

          {!sources ? (
            <div className="text-sm text-muted dark:text-white/50 font-medium">
              Loading sources...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                    Retention (days)
                  </label>
                  <select
                    value={cleanupOlderThanDays}
                    onChange={(e) => {
                      setCleanupOlderThanDays(parseInt(e.target.value));
                      setCleanupStatus("idle");
                      setCleanupResult(null);
                      setCleanupError(null);
                    }}
                    className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                  >
                    <option value={30}>30</option>
                    <option value={60}>60</option>
                    <option value={90}>90</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                    Source (optional)
                  </label>
                  <select
                    value={cleanupSourceId ?? ""}
                    onChange={(e) => {
                      setCleanupSourceId(
                        e.target.value ? parseInt(e.target.value) : null
                      );
                      setCleanupStatus("idle");
                      setCleanupResult(null);
                      setCleanupError(null);
                    }}
                    className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                  >
                    <option value="">All sources</option>
                    {sources.map((source) => (
                      <option key={source.id} value={source.id}>
                        {source.name} ({source.feed_count} feeds)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleCleanup(true)}
                  disabled={cleanupStatus === "loading"}
                  className="rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {cleanupStatus === "loading" ? (
                    <span className="flex items-center gap-2">
                      <svg
                        className="animate-spin h-4 w-4"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Checking...
                    </span>
                  ) : (
                    "Preview"
                  )}
                </button>
                <button
                  onClick={() => handleCleanup(false)}
                  disabled={cleanupStatus === "loading"}
                  className="rounded-xl bg-coral px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-coral/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Run cleanup
                </button>
              </div>

              {cleanupStatus === "success" && cleanupResult && (
                <div className="rounded-xl border border-palm/30 dark:border-palm/40 bg-palm/10 dark:bg-palm/20 p-4">
                  <p className="text-sm font-semibold text-palm dark:text-palm/90 mb-1">
                    {"would_delete" in cleanupResult
                      ? "Preview"
                      : "Cleanup complete"}
                  </p>
                  <p className="text-sm text-palm/90 dark:text-palm/70">
                    {"would_delete" in cleanupResult
                      ? `${cleanupResult.would_delete} feed(s) would be removed.`
                      : `${cleanupResult.deleted} feed(s) removed.`}
                  </p>
                </div>
              )}

              {cleanupStatus === "error" && cleanupError && (
                <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
                  <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                    Cleanup failed
                  </p>
                  <p className="mt-1 text-sm text-red-800 dark:text-red-400">
                    {cleanupError}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Hide / unhide event */}
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm">
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Hide / unhide event
          </h2>
          <p className="text-sm text-muted dark:text-white/60 mb-4">
            Search by event title or by event ID. Hidden events are excluded from
            the public events list.
          </p>

          <div className="space-y-4">
            <div>
              <label
                htmlFor="event-search"
                className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1"
              >
                Search by title or event ID
              </label>
              <input
                id="event-search"
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="e.g. Jazz Night or 12345"
                className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
              />
            </div>

            {searchError && (
              <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-3">
                <p className="text-sm text-red-800 dark:text-red-400">
                  {searchError}
                </p>
              </div>
            )}

            {searchStatus === "loading" && searchInput.trim() && (
              <p className="text-sm text-muted dark:text-white/50 font-medium">
                Searching…
              </p>
            )}

            {searchStatus === "idle" &&
              searchResults &&
              searchInput.trim() &&
              (searchResults.length === 0 ? (
                <p className="text-sm text-muted dark:text-white/50 font-medium">
                  No events match &quot;{searchInput.trim()}&quot;
                </p>
              ) : (
                <ul className="space-y-2 max-h-80 overflow-y-auto">
                  {searchResults.map((ev) => (
                    <li
                      key={ev.id}
                      className="flex flex-wrap items-center gap-2 rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-3"
                    >
                      <div className="min-w-0 flex-1">
                        <span className="text-sm font-medium text-charcoal dark:text-white">
                          {ev.title}
                        </span>
                        <span className="ml-2 text-xs text-muted dark:text-white/50">
                          #{ev.id} · {ev.source_name}
                          {ev.first_start_utc
                            ? ` · ${formatFirstStart(ev.first_start_utc)}`
                            : ""}
                        </span>
                        {ev.hidden && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-coral/15 px-2 py-0.5 text-xs font-medium text-coral dark:bg-coral/25 dark:text-coral/90">
                            Hidden
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleHideUnhide(ev.id, !ev.hidden)}
                        disabled={hidingEventId === ev.id}
                        className={`shrink-0 rounded-xl border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                          ev.hidden
                            ? "border-palm/30 dark:border-palm/40 bg-palm/10 dark:bg-palm/20 text-palm dark:text-palm/90 hover:bg-palm/15 dark:hover:bg-palm/25"
                            : "border-coral/30 dark:border-coral/40 bg-coral/10 dark:bg-coral/20 text-coral dark:text-coral/90 hover:bg-coral/15 dark:hover:bg-coral/25"
                        }`}
                      >
                        {hidingEventId === ev.id
                          ? "…"
                          : ev.hidden
                            ? "Unhide"
                            : "Hide"}
                      </button>
                    </li>
                  ))}
                </ul>
              ))}
          </div>
        </div>

        {/* Duplicate event preview */}
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm">
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Duplicate event preview
          </h2>
          <p className="text-sm text-muted dark:text-white/60 mb-4">
            Groups duplicates by normalized title and start time for a given source.
          </p>

          {!sources ? (
            <div className="text-sm text-muted dark:text-white/50 font-medium">
              Loading sources...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                    Source
                  </label>
                  <select
                    value={dupeSourceId ?? ""}
                    onChange={(e) => {
                      setDupeSourceId(e.target.value ? parseInt(e.target.value) : null);
                      setDupeResults(null);
                      setDupeError(null);
                      setDupeStatus("idle");
                    }}
                    className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                  >
                    <option value="">-- Select a source --</option>
                    {sources.map((source) => (
                      <option key={source.id} value={source.id}>
                        {source.name} ({source.feed_count} feeds)
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                    Limit
                  </label>
                  <select
                    value={dupeLimit}
                    onChange={(e) => {
                      setDupeLimit(parseInt(e.target.value));
                      setDupeResults(null);
                      setDupeError(null);
                      setDupeStatus("idle");
                    }}
                    className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                  >
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={200}>200</option>
                    <option value={500}>500</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleLoadDuplicates}
                disabled={!dupeSourceId || dupeStatus === "loading"}
                className="rounded-xl bg-gulf px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gulf/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {dupeStatus === "loading" ? "Loading..." : "Preview duplicates"}
              </button>

              {dupeError && (
                <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-3">
                  <p className="text-sm text-red-800 dark:text-red-400">{dupeError}</p>
                </div>
              )}

              {dupeStatus === "idle" && dupeResults && (
                <div className="space-y-2">
                  {dupeResults.length === 0 ? (
                    <p className="text-sm text-muted dark:text-white/50 font-medium">
                      No duplicate groups found.
                    </p>
                  ) : (
                    <ul className="space-y-2 max-h-80 overflow-y-auto">
                      {dupeResults.map((group, idx) => (
                        <li
                          key={`${group.title_norm}-${group.start_utc}-${idx}`}
                          className="rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-3"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-semibold text-charcoal dark:text-white">
                              {group.title_norm}
                            </span>
                            <span className="text-xs text-muted dark:text-white/50">
                              {formatFirstStart(group.start_utc)}
                            </span>
                            <span className="text-xs font-medium text-coral dark:text-coral/90">
                              {group.occurrences} occurrences
                            </span>
                          </div>
                          <div className="mt-2 text-xs text-muted dark:text-white/50">
                            Event IDs: {group.event_ids.join(", ")}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Links Section */}
        <Link
          href="/admin/venues"
          className="block rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm transition-all hover:border-palm/40 dark:hover:border-palm/50 hover:bg-palm/5 dark:hover:bg-palm/10 hover:shadow-md"
        >
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Venue Metadata
          </h2>
          <p className="text-sm text-muted dark:text-white/60">
            Edit venue descriptions, hero image paths, and related SEO metadata.
          </p>
        </Link>

        <Link
          href="/admin/unresolved"
          className="block rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm transition-all hover:border-gulf/40 dark:hover:border-gulf/50 hover:bg-gulf/5 dark:hover:bg-gulf/10 hover:shadow-md"
        >
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Unresolved Locations
          </h2>
          <p className="text-sm text-muted dark:text-white/60">
            Review and resolve event locations that couldn&apos;t be automatically
            matched to venues.
          </p>
        </Link>

        <Link
          href="/admin/tasks"
          className="block rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm transition-all hover:border-gulf/40 dark:hover:border-gulf/50 hover:bg-gulf/5 dark:hover:bg-gulf/10 hover:shadow-md"
        >
          <h2 className="text-lg font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">
            Task Runs Dashboard
          </h2>
          <p className="text-sm text-muted dark:text-white/60">
            Track Celery run health, failure trends, and recent task outcomes.
          </p>
        </Link>
      </div>
    </div>
  );
}
