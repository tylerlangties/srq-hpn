"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { API_PATHS } from "@/lib/api-paths";
import { useAdminGuard } from "@/app/hooks/useAdminGuard";
import type {
  UnresolvedLocationGroup,
  UnresolvedOccurrenceOut,
  VenueOut,
  CreateVenueFromLocationRequest,
  LinkOccurrenceRequest,
} from "@/types/admin";

export default function UnresolvedLocationsPage() {
  const { checking: authChecking, user } = useAdminGuard();
  const [groups, setGroups] = useState<UnresolvedLocationGroup[] | null>(null);
  const [venues, setVenues] = useState<VenueOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingVenue, setCreatingVenue] = useState<string | null>(null);
  const [linkingVenue, setLinkingVenue] = useState<string | null>(null);
  const [newVenueName, setNewVenueName] = useState("");
  const [newVenueArea, setNewVenueArea] = useState("");
  const [newVenueDescription, setNewVenueDescription] = useState("");
  const [newVenueHeroImagePath, setNewVenueHeroImagePath] = useState("");
  const [newVenueAliases, setNewVenueAliases] = useState<string[]>([]);
  const [selectedVenueId, setSelectedVenueId] = useState<number | null>(null);

  useEffect(() => {
    if (user?.role === "admin") {
      loadData();
    }
  }, [user]);

  if (authChecking || !user) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-muted dark:text-white/50 font-medium">Loading...</div>
      </div>
    );
  }

  async function loadData() {
    try {
      setError(null);
      setLoading(true);
      const [groupsData, venuesData] = await Promise.all([
        apiGet<UnresolvedLocationGroup[]>(API_PATHS.admin.unresolvedVenues),
        apiGet<VenueOut[]>(API_PATHS.admin.venues),
      ]);
      setGroups(groupsData);
      setVenues(venuesData);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateVenue(locationText: string) {
    if (!newVenueName.trim()) {
      alert("Please enter a venue name");
      return;
    }

    try {
      setError(null);
      const request: CreateVenueFromLocationRequest = {
        location_text: locationText,
        name: newVenueName.trim(),
        area: newVenueArea.trim() || null,
        description: newVenueDescription.trim() || null,
        hero_image_path: newVenueHeroImagePath.trim() || null,
        aliases: newVenueAliases.filter((a) => a.trim()).length > 0
          ? newVenueAliases.filter((a) => a.trim())
          : null,
      };

      await apiPost(API_PATHS.admin.createVenueFromLocation, request);
      setCreatingVenue(null);
      setNewVenueName("");
      setNewVenueArea("");
      setNewVenueDescription("");
      setNewVenueHeroImagePath("");
      setNewVenueAliases([]);
      await loadData(); // Refresh list
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleLinkToVenue(locationText: string) {
    if (!selectedVenueId) {
      alert("Please select a venue");
      return;
    }

    try {
      setError(null);
      // Get all occurrences for this location
      const occurrences = await apiGet<UnresolvedOccurrenceOut[]>(
        API_PATHS.admin.unresolvedVenueOccurrences(locationText)
      );

      // Link all occurrences to the selected venue
      for (const occ of occurrences) {
        const request: LinkOccurrenceRequest = {
          occurrence_id: occ.id,
          venue_id: selectedVenueId,
        };
        await apiPost(API_PATHS.admin.linkVenue, request);
      }

      setLinkingVenue(null);
      setSelectedVenueId(null);
      await loadData(); // Refresh list
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-muted dark:text-white/50 font-medium">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4 shadow-sm">
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">Error</p>
          <p className="mt-1 text-sm text-red-800 dark:text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
            Unresolved Locations
          </h1>
          <p className="mt-1 text-sm text-muted dark:text-white/60 font-medium">
            {groups?.length ?? 0} location groups need resolution
          </p>
        </div>
        <button
          onClick={loadData}
          className="rounded-lg border-2 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500 transition-colors shadow-sm"
        >
          Refresh
        </button>
      </div>

      {!groups || groups.length === 0 ? (
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-charcoal dark:text-white/80">
            All locations are resolved!
          </p>
          <p className="mt-1 text-sm text-muted dark:text-white/50">
            No unresolved locations found.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((group) => (
            <div
              key={group.location_text}
              className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h3 className="text-base font-semibold text-charcoal dark:text-white">
                    {group.location_text}
                  </h3>
                  <p className="mt-1 text-xs text-muted dark:text-white/50 font-medium">
                    {group.occurrence_count} occurrence
                    {group.occurrence_count !== 1 ? "s" : ""}
                  </p>
                </div>

                <div className="flex shrink-0 gap-2">
                  <button
                    onClick={() => {
                      setLinkingVenue(
                        linkingVenue === group.location_text
                          ? null
                          : group.location_text
                      );
                      setCreatingVenue(null);
                      setSelectedVenueId(null);
                    }}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition-colors ${
                      linkingVenue === group.location_text
                        ? "border-gulf bg-gulf/10 dark:bg-gulf/20 text-gulf dark:text-gulf/90"
                        : "border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10"
                    }`}
                  >
                    Link to Existing
                  </button>
                  <button
                    onClick={() => {
                      setCreatingVenue(
                        creatingVenue === group.location_text
                          ? null
                          : group.location_text
                      );
                      setLinkingVenue(null);
                      setNewVenueName(group.location_text);
                      setNewVenueArea("");
                      setNewVenueDescription("");
                      setNewVenueHeroImagePath("");
                      setNewVenueAliases([]);
                    }}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition-colors ${
                      creatingVenue === group.location_text
                        ? "border-gulf bg-gulf/10 dark:bg-gulf/20 text-gulf dark:text-gulf/90"
                        : "border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10"
                    }`}
                  >
                    Create Venue
                  </button>
                </div>
              </div>

              {creatingVenue === group.location_text && (
                <div className="mt-4 rounded-xl border border-gulf/30 dark:border-gulf/40 bg-gulf/5 dark:bg-gulf/10 p-4 shadow-sm">
                  <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-3">
                    Create New Venue
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Venue Name *
                      </label>
                      <input
                        type="text"
                        value={newVenueName}
                        onChange={(e) => setNewVenueName(e.target.value)}
                        className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                        placeholder="Enter venue name"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Area (optional)
                      </label>
                      <input
                        type="text"
                        value={newVenueArea}
                        onChange={(e) => setNewVenueArea(e.target.value)}
                        className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                        placeholder="e.g., Sarasota, Downtown"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Description (optional)
                      </label>
                      <textarea
                        value={newVenueDescription}
                        onChange={(e) => setNewVenueDescription(e.target.value)}
                        className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                        placeholder="Write a short venue description for SEO and users"
                        rows={4}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Hero Image Path (optional)
                      </label>
                      <input
                        type="text"
                        value={newVenueHeroImagePath}
                        onChange={(e) => setNewVenueHeroImagePath(e.target.value)}
                        className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                        placeholder="/uploads/venues/your-venue.webp"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Aliases (optional)
                      </label>
                      <p className="text-xs text-muted dark:text-white/50 mb-2">
                        Add alternative names for this venue to help with matching
                      </p>
                      <div className="space-y-2">
                        {newVenueAliases.map((alias, index) => (
                          <div key={index} className="flex gap-2">
                            <input
                              type="text"
                              value={alias}
                              onChange={(e) => {
                                const updated = [...newVenueAliases];
                                updated[index] = e.target.value;
                                setNewVenueAliases(updated);
                              }}
                              className="flex-1 rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                              placeholder="Enter alias"
                            />
                            <button
                              type="button"
                              onClick={() => {
                                const updated = newVenueAliases.filter(
                                  (_, i) => i !== index
                                );
                                setNewVenueAliases(updated);
                              }}
                              className="rounded-xl border border-red-300 dark:border-red-600 bg-white dark:bg-white/5 px-3 py-2 text-sm font-medium text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            >
                              Remove
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => {
                            setNewVenueAliases([...newVenueAliases, ""]);
                          }}
                          className="w-full rounded-xl border border-dashed border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-3 py-2 text-sm font-medium text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10 transition-colors"
                        >
                          + Add Alias
                        </button>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCreateVenue(group.location_text)}
                        className="rounded-xl bg-gulf px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gulf/90 transition-colors"
                      >
                        Create
                      </button>
                      <button
                        onClick={() => {
                          setCreatingVenue(null);
                          setNewVenueName("");
                          setNewVenueArea("");
                          setNewVenueDescription("");
                          setNewVenueHeroImagePath("");
                          setNewVenueAliases([]);
                        }}
                        className="rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {linkingVenue === group.location_text && (
                <div className="mt-4 rounded-xl border border-gulf/30 dark:border-gulf/40 bg-gulf/5 dark:bg-gulf/10 p-4 shadow-sm">
                  <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-3">
                    Link to Existing Venue
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                        Select Venue *
                      </label>
                      <select
                        value={selectedVenueId ?? ""}
                        onChange={(e) =>
                          setSelectedVenueId(
                            e.target.value ? parseInt(e.target.value) : null
                          )
                        }
                        className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                      >
                        <option value="">-- Select a venue --</option>
                        {venues?.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.name} {v.area ? `(${v.area})` : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleLinkToVenue(group.location_text)}
                        disabled={!selectedVenueId}
                        className="rounded-lg bg-blue-600 dark:bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                      >
                        Link All Occurrences
                      </button>
                      <button
                        onClick={() => {
                          setLinkingVenue(null);
                          setSelectedVenueId(null);
                        }}
                        className="rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white hover:bg-sand/80 dark:hover:bg-white/10 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
