"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { apiGet, apiPatch } from "@/lib/api";
import { API_PATHS } from "@/lib/api-paths";
import { useAdminGuard } from "@/app/hooks/useAdminGuard";
import type { AdminVenueDetailOut, UpdateVenueRequest, VenueOut } from "@/types/admin";

type SaveStatus = "idle" | "saving" | "success" | "error";

type HeroImageValidation = {
  normalizedPath: string | null;
  isValid: boolean;
  message: string | null;
};

function validateHeroImagePath(rawPath: string | null | undefined): HeroImageValidation {
  const value = (rawPath ?? "").trim();
  if (!value) {
    return { normalizedPath: null, isValid: true, message: null };
  }

  const normalizedPath = value.startsWith("/") ? value : `/${value}`;
  const looksLikeUploadPath = normalizedPath.startsWith("/uploads/");
  const hasSupportedExtension = /\.(avif|webp|png|jpe?g|gif)$/i.test(normalizedPath);

  if (!looksLikeUploadPath) {
    return {
      normalizedPath,
      isValid: false,
      message: "Use a local path under /uploads/, for example /uploads/venues/venue-name.webp.",
    };
  }

  if (!hasSupportedExtension) {
    return {
      normalizedPath,
      isValid: false,
      message: "Use an image file extension like .webp, .avif, .jpg, .jpeg, .png, or .gif.",
    };
  }

  return { normalizedPath, isValid: true, message: null };
}

export default function AdminVenuesPage() {
  const { checking: authChecking, user } = useAdminGuard();
  const [venues, setVenues] = useState<VenueOut[] | null>(null);
  const [selectedVenueId, setSelectedVenueId] = useState<number | null>(null);
  const [venue, setVenue] = useState<AdminVenueDetailOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  const loadVenueDetail = useCallback(async (venueId: number) => {
    try {
      setError(null);
      const data = await apiGet<AdminVenueDetailOut>(API_PATHS.admin.venueDetail(venueId));
      setVenue(data);
      setSaveStatus("idle");
      setSaveError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const loadVenues = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiGet<VenueOut[]>(API_PATHS.admin.venues);
      setVenues(data);
      if (data.length > 0) {
        const firstId = data[0].id;
        setSelectedVenueId(firstId);
        await loadVenueDetail(firstId);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loadVenueDetail]);

  useEffect(() => {
    if (user?.role === "admin") {
      void loadVenues();
    }
  }, [loadVenues, user]);

  async function handleSave() {
    if (!selectedVenueId || !venue) {
      return;
    }

    const heroPathValidation = validateHeroImagePath(venue.hero_image_path);
    if (!heroPathValidation.isValid) {
      setSaveStatus("error");
      setSaveError(heroPathValidation.message ?? "Hero image path is invalid.");
      return;
    }

    try {
      setSaveStatus("saving");
      setSaveError(null);
      const payload: UpdateVenueRequest = {
        name: venue.name.trim(),
        area: venue.area?.trim() || null,
        address: venue.address?.trim() || null,
        website: venue.website?.trim() || null,
        timezone: venue.timezone?.trim() || "America/New_York",
        description: venue.description?.trim() || null,
        description_markdown: venue.description_markdown?.trim() || null,
        hero_image_path: heroPathValidation.normalizedPath,
      };

      const updated = await apiPatch<AdminVenueDetailOut>(
        API_PATHS.admin.updateVenue(selectedVenueId),
        payload
      );
      setVenue(updated);
      setSaveStatus("success");
    } catch (e) {
      setSaveStatus("error");
      setSaveError(e instanceof Error ? e.message : String(e));
    }
  }

  if (authChecking || !user) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-muted dark:text-white/50 font-medium">Loading...</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <div className="text-sm text-muted dark:text-white/50 font-medium">Loading venues...</div>
      </div>
    );
  }

  const heroImageValidation = validateHeroImagePath(venue?.hero_image_path);

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-3xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white mb-2">Venue Metadata</h1>
      <p className="text-sm text-muted dark:text-white/60 mb-6">
        Edit venue details used for SEO and venue page presentation.
      </p>

      {error ? (
        <div className="rounded-xl border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-4 shadow-sm mb-6">
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">Error</p>
          <p className="mt-1 text-sm text-red-800 dark:text-red-400">{error}</p>
        </div>
      ) : null}

      {!venues || venues.length === 0 ? (
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5 p-8 text-center shadow-sm">
          <p className="text-sm font-semibold text-charcoal dark:text-white/80">No venues available.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-charcoal/10 dark:border-white/20 bg-white/80 dark:bg-white/5 p-6 shadow-sm space-y-4">
          <div>
            <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
              Select Venue
            </label>
            <select
              value={selectedVenueId ?? ""}
              onChange={async (e) => {
                const nextId = e.target.value ? Number.parseInt(e.target.value, 10) : null;
                setSelectedVenueId(nextId);
                if (nextId) {
                  await loadVenueDetail(nextId);
                } else {
                  setVenue(null);
                }
              }}
              className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
            >
              {venues.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>

          {venue ? (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Slug
                </label>
                <input
                  type="text"
                  value={venue.slug}
                  disabled
                  className="w-full rounded-xl border border-charcoal/10 dark:border-white/20 bg-sand/80 dark:bg-white/5 text-muted dark:text-white/50 px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={venue.name}
                  onChange={(e) => setVenue({ ...venue, name: e.target.value })}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Area
                </label>
                <input
                  type="text"
                  value={venue.area ?? ""}
                  onChange={(e) => setVenue({ ...venue, area: e.target.value })}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={venue.address ?? ""}
                  onChange={(e) => setVenue({ ...venue, address: e.target.value })}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Website URL
                </label>
                <input
                  type="url"
                  value={venue.website ?? ""}
                  onChange={(e) => setVenue({ ...venue, website: e.target.value })}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Timezone
                </label>
                <input
                  type="text"
                  value={venue.timezone ?? "America/New_York"}
                  onChange={(e) => setVenue({ ...venue, timezone: e.target.value })}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Description
                </label>
                <textarea
                  value={venue.description ?? ""}
                  onChange={(e) => setVenue({ ...venue, description: e.target.value })}
                  rows={5}
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Rich Description (Markdown)
                </label>
                <textarea
                  value={venue.description_markdown ?? ""}
                  onChange={(e) => setVenue({ ...venue, description_markdown: e.target.value })}
                  rows={10}
                  placeholder="# About this venue\n\nAdd lists, headers, links, and image markdown."
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
                <p className="mt-1 text-xs text-muted dark:text-white/50">
                  Supports markdown for headings, lists, links, and images. Use local image paths like
                  {" "}
                  <code>/uploads/venues/venue-name.webp</code>.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal dark:text-white/80 mb-1">
                  Hero Image Path
                </label>
                <input
                  type="text"
                  value={venue.hero_image_path ?? ""}
                  onChange={(e) => setVenue({ ...venue, hero_image_path: e.target.value })}
                  placeholder="/uploads/venues/venue-name.webp"
                  className="w-full rounded-xl border border-charcoal/15 dark:border-white/20 bg-white/90 dark:bg-white/5 text-charcoal dark:text-white px-3 py-2 text-sm focus:border-gulf focus:outline-none focus:ring-2 focus:ring-gulf/30 dark:focus:ring-purple-400/30"
                />
                {heroImageValidation.message ? (
                  <p className="mt-2 text-xs font-medium text-coral dark:text-coral/90">
                    {heroImageValidation.message}
                  </p>
                ) : null}
                {heroImageValidation.normalizedPath && heroImageValidation.isValid ? (
                  <div className="mt-3 overflow-hidden rounded-2xl border border-charcoal/10 dark:border-white/20 bg-sand/50 dark:bg-white/5">
                    <div className="relative h-[36rem] w-full">
                      <Image
                        src={heroImageValidation.normalizedPath}
                        alt={`${venue.name || "Venue"} hero preview`}
                        fill
                        sizes="(max-width: 768px) 100vw, 768px"
                        className="object-cover"
                      />
                    </div>
                    <p className="px-3 py-2 text-xs text-muted dark:text-white/50">
                      Preview: {heroImageValidation.normalizedPath}
                    </p>
                  </div>
                ) : null}
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleSave}
                  disabled={saveStatus === "saving" || !venue.name.trim() || !heroImageValidation.isValid}
                  className="rounded-xl bg-gulf px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gulf/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                >
                  {saveStatus === "saving" ? "Saving..." : "Save Venue"}
                </button>
                {saveStatus === "success" ? (
                  <span className="text-sm font-medium text-palm dark:text-palm/90">
                    Saved and revalidation requested.
                  </span>
                ) : null}
              </div>

              {saveStatus === "error" && saveError ? (
                <div className="rounded-lg border border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/20 p-3">
                  <p className="text-sm text-red-800 dark:text-red-400">{saveError}</p>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
