import { Suspense } from "react";
import AppLayout from "../components/AppLayout";
import EventsPageClient from "./EventsPageClient";

function EventsPageFallback() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-6xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-[var(--font-heading)] font-semibold">
            Events in Sarasota
          </h1>
          <p className="mt-2 text-muted dark:text-white/60">
            A curated list of what&apos;s happening over the next 7 days.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {[0, 1, 2, 3].map((key) => (
            <div
              key={key}
              className="h-28 rounded-2xl bg-white/80 dark:bg-white/5 border border-white/60 dark:border-white/10 animate-pulse"
            />
          ))}
        </div>
      </div>
    </AppLayout>
  );
}

export default function EventsPage() {
  return (
    <Suspense fallback={<EventsPageFallback />}>
      <EventsPageClient />
    </Suspense>
  );
}
