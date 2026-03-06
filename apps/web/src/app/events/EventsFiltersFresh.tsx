"use client";

import { useState } from "react";
import type { CategoryOut, EventRangeSort, VenueOut } from "@/types/events";

type SortOption = { value: EventRangeSort; label: string };

type Props = {
  start: string;
  end: string;
  selectedVenue: string;
  selectedSort: EventRangeSort;
  showFreeOnly: boolean;
  viewMode: "list" | "day";
  selectedCategory: string;
  displayedCategories: CategoryOut[];
  hasMoreCategories: boolean;
  showAllCategories: boolean;
  venues: VenueOut[];
  sortOptions: SortOption[];
  isWeekendPresetActive: boolean;
  onPatch: (patch: Record<string, string | null>) => void;
  onApplyWeekendPreset: () => void;
  onToggleShowAllCategories: () => void;
};

export default function EventsFiltersFresh({
  start,
  end,
  selectedVenue,
  selectedSort,
  showFreeOnly,
  viewMode,
  selectedCategory,
  displayedCategories,
  hasMoreCategories,
  showAllCategories,
  venues,
  sortOptions,
  isWeekendPresetActive,
  onPatch,
  onApplyWeekendPreset,
  onToggleShowAllCategories,
}: Props) {
  const [showDateRange, setShowDateRange] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  const activeGradientButton =
    "bg-gradient-to-r from-coral to-[#ff7b3d] text-white shadow-sm shadow-coral/30 dark:from-purple-600 dark:to-pink-500 dark:shadow-purple-500/20";
  const inactiveButton =
    "border border-charcoal/15 bg-white/85 text-charcoal dark:border-white/25 dark:bg-white/10 dark:text-white";
  const activeCategoryButton =
    "bg-gradient-to-r from-coral/95 to-[#ff7b3d] text-white shadow-sm shadow-coral/30 dark:from-purple-600 dark:to-pink-500 dark:shadow-purple-500/20";

  return (
    <section className="mb-5 rounded-2xl border border-charcoal/10 bg-white/75 px-3 py-3 shadow-sm dark:border-white/15 dark:bg-white/5">
      <div className="mb-2 flex items-center justify-between md:hidden">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted dark:text-white/65">
          Filters
        </p>
        <button
          type="button"
          onClick={() => setShowMobileFilters((value) => !value)}
          className="rounded-full border border-charcoal/15 bg-white px-3 py-1.5 text-xs font-semibold text-charcoal transition dark:border-white/20 dark:bg-white/10 dark:text-white"
          aria-expanded={showMobileFilters}
          aria-controls="fresh-mobile-filters"
        >
          {showMobileFilters ? "Hide" : "Show"} filters
        </button>
      </div>

      <div id="fresh-mobile-filters" className={`${showMobileFilters ? "block" : "hidden"} md:block`}>
        <div className="flex flex-wrap items-end gap-1.5 md:gap-2">
          <button
            type="button"
            onClick={() => onPatch({ view: viewMode === "day" ? null : "day" })}
            className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
              viewMode === "day" ? activeGradientButton : inactiveButton
            }`}
          >
            Group by day
          </button>

          <button
            type="button"
            onClick={() => onPatch({ free: showFreeOnly ? null : "true", page: null })}
            className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
              showFreeOnly ? activeGradientButton : inactiveButton
            }`}
          >
            Free only
          </button>

          <button
            type="button"
            onClick={onApplyWeekendPreset}
            className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
              isWeekendPresetActive ? activeGradientButton : inactiveButton
            }`}
          >
            Weekend Fri-Sun
          </button>

          <button
            type="button"
            onClick={() => setShowDateRange((value) => !value)}
            className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
              showDateRange ? activeGradientButton : inactiveButton
            }`}
            aria-expanded={showDateRange}
            aria-controls="fresh-date-range"
          >
            Date range: {start} - {end}
          </button>

          <label className="min-w-[8rem] flex-1 text-[10px] font-semibold uppercase tracking-wide text-muted dark:text-white/65 md:min-w-[8.5rem]">
            <span className="sr-only md:not-sr-only">Venue</span>
            <select
              value={selectedVenue}
              onChange={(event) => onPatch({ venue: event.target.value || null, page: null })}
              className="mt-1 block h-9 w-full rounded-lg border border-charcoal/15 bg-white/90 px-2.5 text-[13px] font-medium text-charcoal [color-scheme:light] dark:border-white/20 dark:bg-[#14161b] dark:text-white dark:[color-scheme:dark]"
            >
              <option value="" className="bg-cloud text-charcoal dark:bg-[#14161b] dark:text-white">
                All venues
              </option>
              {venues.map((venue) => (
                <option
                  key={venue.id}
                  value={venue.slug}
                  className="bg-cloud text-charcoal dark:bg-[#14161b] dark:text-white"
                >
                  {venue.name}
                </option>
              ))}
            </select>
          </label>

          <label className="min-w-[7.5rem] flex-1 text-[10px] font-semibold uppercase tracking-wide text-muted dark:text-white/65 md:min-w-[8rem]">
            <span className="sr-only md:not-sr-only">Sort</span>
            <select
              value={selectedSort}
              onChange={(event) => onPatch({ sort: event.target.value, page: null })}
              className="mt-1 block h-9 w-full rounded-lg border border-charcoal/15 bg-white/90 px-2.5 text-[13px] font-medium text-charcoal [color-scheme:light] dark:border-white/20 dark:bg-[#14161b] dark:text-white dark:[color-scheme:dark]"
            >
              {sortOptions.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  className="bg-cloud text-charcoal dark:bg-[#14161b] dark:text-white"
                >
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {showDateRange ? (
          <div id="fresh-date-range" className="mt-2 grid gap-2 sm:grid-cols-2">
            <label className="text-[10px] font-semibold uppercase tracking-wide text-muted dark:text-white/65">
              Start
              <input
                type="date"
                value={start}
                onChange={(event) => onPatch({ start: event.target.value, page: null })}
                className="mt-1 block h-9 w-full rounded-lg border border-charcoal/15 bg-white/90 px-2.5 text-[13px] font-medium text-charcoal dark:border-white/20 dark:bg-white/10 dark:text-white"
              />
            </label>
            <label className="text-[10px] font-semibold uppercase tracking-wide text-muted dark:text-white/65">
              End
              <input
                type="date"
                value={end}
                onChange={(event) => onPatch({ end: event.target.value, page: null })}
                className="mt-1 block h-9 w-full rounded-lg border border-charcoal/15 bg-white/90 px-2.5 text-[13px] font-medium text-charcoal dark:border-white/20 dark:bg-white/10 dark:text-white"
              />
            </label>
          </div>
        ) : null}

        <div className="mt-2.5 flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => onPatch({ category: null, page: null })}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              selectedCategory ? inactiveButton : activeCategoryButton
            }`}
          >
            All categories
          </button>

          {displayedCategories.map((category) => (
            <button
              key={category.id}
              type="button"
              onClick={() => onPatch({ category: category.slug, page: null })}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                selectedCategory === category.slug ? activeCategoryButton : inactiveButton
              }`}
            >
              {category.name}
            </button>
          ))}

          {hasMoreCategories ? (
            <button
              type="button"
              onClick={onToggleShowAllCategories}
              className="rounded-full border border-coral/30 bg-white/70 px-3 py-1.5 text-xs font-semibold text-coral transition hover:bg-coral/10 dark:border-purple-400/40 dark:bg-white/5 dark:text-purple-200 dark:hover:bg-purple-500/10"
            >
              {showAllCategories ? "Show fewer" : "Show all"}
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}
