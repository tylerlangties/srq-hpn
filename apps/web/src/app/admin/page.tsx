"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
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

  useEffect(() => {
    loadSources();
  }, []);

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
        `/api/admin/events/search?q=${encodeURIComponent(q.trim())}&limit=20`
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
      await apiPatch<{ event_id: number; hidden: boolean }>(
        `/api/admin/events/${eventId}`,
        { hidden }
      );
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
      const data = await apiGet<SourceOut[]>("/api/admin/sources");
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
        `/api/admin/ingest/source/${selectedSourceId}/feeds`,
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
        "/api/admin/source-feeds/cleanup",
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

  const selectedSource = sources?.find((s) => s.id === selectedSourceId);

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">Admin Panel</h1>

      <div className="space-y-6">
        {/* Ingest Source Feeds Section */}
        <div className="rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Ingest Source Feeds
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
            Fetch and ingest events from iCal feeds for a selected source.
          </p>

          {loadingError ? (
            <div className="rounded-lg border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
              <p className="text-sm font-semibold text-red-900 dark:text-red-300">
                Failed to load sources
              </p>
              <p className="mt-1 text-sm text-red-800 dark:text-red-400">{loadingError}</p>
              <button
                onClick={loadSources}
                className="mt-2 rounded-lg border-2 border-red-300 dark:border-red-600 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : !sources ? (
            <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">
              Loading sources...
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-900 dark:text-gray-200 mb-1">
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
                  className="w-full rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
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
                <div className="rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-3">
                  <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                    <p>
                      <span className="font-semibold text-gray-700 dark:text-gray-300">Type:</span>{" "}
                      {selectedSource.type}
                    </p>
                    <p>
                      <span className="font-semibold text-gray-700 dark:text-gray-300">Feeds:</span>{" "}
                      {selectedSource.feed_count}
                    </p>
                  </div>
                </div>
              )}

              <button
                onClick={handleIngest}
                disabled={!selectedSourceId || ingestStatus === "loading"}
                className="rounded-lg bg-blue-600 dark:bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
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
                <div className="rounded-lg border-2 border-green-300 dark:border-green-600 bg-green-50 dark:bg-green-900/20 p-4">
                  <p className="text-sm font-semibold text-green-900 dark:text-green-300 mb-2">
                    Ingest Complete
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                        {ingestResult.feeds_seen}
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-500 font-medium">
                        Feeds Processed
                      </p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                        {ingestResult.events_ingested}
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-500 font-medium">
                        Events Ingested
                      </p>
                    </div>
                    <div>
                      <p
                        className={`text-2xl font-bold ${
                          ingestResult.errors > 0
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-green-700 dark:text-green-400"
                        }`}
                      >
                        {ingestResult.errors}
                      </p>
                      <p className="text-xs text-green-600 dark:text-green-500 font-medium">
                        Errors
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Result */}
              {ingestStatus === "error" && ingestError && (
                <div className="rounded-lg border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
                  <p className="text-sm font-semibold text-red-900 dark:text-red-300">
                    Ingest Failed
                  </p>
                  <p className="mt-1 text-sm text-red-800 dark:text-red-400">{ingestError}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Clean up source feeds */}
        <div className="rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Clean up source feeds
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
            Remove feeds that haven&apos;t been seen by scrapers in the given
            number of days. Uses <code className="rounded bg-gray-200 dark:bg-gray-700 px-1">last_seen_at</code>{" "}
            (or <code className="rounded bg-gray-200 dark:bg-gray-700 px-1">created_at</code> when
            never seen). Preview shows how many would be removed without deleting.
          </p>

          {!sources ? (
            <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">
              Loading sources...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-900 dark:text-gray-200 mb-1">
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
                    className="w-full rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
                  >
                    <option value={30}>30</option>
                    <option value={60}>60</option>
                    <option value={90}>90</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-900 dark:text-gray-200 mb-1">
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
                    className="w-full rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
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
                  className="rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
                  className="rounded-lg bg-amber-600 dark:bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 dark:hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  Run cleanup
                </button>
              </div>

              {cleanupStatus === "success" && cleanupResult && (
                <div className="rounded-lg border-2 border-green-300 dark:border-green-600 bg-green-50 dark:bg-green-900/20 p-4">
                  <p className="text-sm font-semibold text-green-900 dark:text-green-300 mb-1">
                    {"would_delete" in cleanupResult
                      ? "Preview"
                      : "Cleanup complete"}
                  </p>
                  <p className="text-sm text-green-800 dark:text-green-400">
                    {"would_delete" in cleanupResult
                      ? `${cleanupResult.would_delete} feed(s) would be removed.`
                      : `${cleanupResult.deleted} feed(s) removed.`}
                  </p>
                </div>
              )}

              {cleanupStatus === "error" && cleanupError && (
                <div className="rounded-lg border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4">
                  <p className="text-sm font-semibold text-red-900 dark:text-red-300">
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
        <div className="rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Hide / unhide event
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
            Search by event title or by event ID. Hidden events are excluded from
            the public events list.
          </p>

          <div className="space-y-4">
            <div>
              <label
                htmlFor="event-search"
                className="block text-xs font-semibold text-gray-900 dark:text-gray-200 mb-1"
              >
                Search by title or event ID
              </label>
              <input
                id="event-search"
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="e.g. Jazz Night or 12345"
                className="w-full rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-3 py-2 text-sm focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800"
              />
            </div>

            {searchError && (
              <div className="rounded-lg border-2 border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-3">
                <p className="text-sm text-red-800 dark:text-red-400">
                  {searchError}
                </p>
              </div>
            )}

            {searchStatus === "loading" && searchInput.trim() && (
              <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                Searching…
              </p>
            )}

            {searchStatus === "idle" &&
              searchResults &&
              searchInput.trim() &&
              (searchResults.length === 0 ? (
                <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  No events match &quot;{searchInput.trim()}&quot;
                </p>
              ) : (
                <ul className="space-y-2 max-h-80 overflow-y-auto">
                  {searchResults.map((ev) => (
                    <li
                      key={ev.id}
                      className="flex flex-wrap items-center gap-2 rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-3"
                    >
                      <div className="min-w-0 flex-1">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {ev.title}
                        </span>
                        <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                          #{ev.id} · {ev.source_name}
                          {ev.first_start_utc
                            ? ` · ${formatFirstStart(ev.first_start_utc)}`
                            : ""}
                        </span>
                        {ev.hidden && (
                          <span className="ml-2 inline-flex items-center rounded bg-amber-100 dark:bg-amber-900/40 px-1.5 py-0.5 text-xs font-medium text-amber-800 dark:text-amber-200">
                            Hidden
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleHideUnhide(ev.id, !ev.hidden)}
                        disabled={hidingEventId === ev.id}
                        className={`shrink-0 rounded-lg border-2 px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                          ev.hidden
                            ? "border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900/30"
                            : "border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/30"
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

        {/* Links Section */}
        <Link
          href="/admin/unresolved"
          className="block rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all shadow-sm hover:shadow-md"
        >
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Unresolved Locations
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300">
            Review and resolve event locations that couldn&apos;t be automatically
            matched to venues.
          </p>
        </Link>
      </div>
    </div>
  );
}
