"use client";

import Link from "next/link";
import AppLayout from "../components/AppLayout";
import { useVenues } from "../hooks/useVenues";

export default function VenuesPage() {
  const venues = useVenues();

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Venues
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            Explore places hosting the best events around Sarasota.
          </p>
        </div>

        {venues.error ? (
          <div className="rounded-2xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-5 text-sm text-red-700 dark:text-red-300">
            {venues.error}
          </div>
        ) : venues.loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2, 3, 4, 5].map((key) => (
              <div
                key={key}
                className="h-24 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
              />
            ))}
          </div>
        ) : venues.data && venues.data.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {venues.data.map((venue) => (
              <Link
                key={venue.id}
                href={`/venues/${venue.slug}`}
                className="group rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 p-5 shadow-sm hover:shadow-md transition"
              >
                <h2 className="font-[var(--font-heading)] text-lg font-semibold text-charcoal group-hover:text-coral transition dark:text-white dark:group-hover:text-purple-300">
                  {venue.name}
                </h2>
                <p className="mt-2 text-sm text-muted dark:text-white/50">
                  {venue.area ?? "Sarasota"}
                </p>
                <span className="mt-3 inline-flex items-center text-sm text-gulf dark:text-purple-300">
                  View venue →
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted dark:text-white/60">
            No venues found yet.
          </p>
        )}
      </div>
    </AppLayout>
  );
}
